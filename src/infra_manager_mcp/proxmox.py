"""
Proxmox API client for Infrastructure Manager MCP
"""

import logging
import urllib3
from typing import List, Dict, Any, Optional
from proxmoxer import ProxmoxAPI
from proxmoxer.core import AuthenticationError
from .config import get_config, ProxmoxConfig

# Désactiver les warnings SSL pour les certificats auto-signés
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)


class ProxmoxClient:
    """Client pour interagir avec l'API Proxmox"""

    def __init__(self):
        config = get_config()
        self.config = config.proxmox
        self._api: Optional[ProxmoxAPI] = None

    def connect(self) -> ProxmoxAPI:
        """
        Se connecte à l'API Proxmox

        Returns:
            Instance ProxmoxAPI

        Raises:
            AuthenticationError: Si l'authentification échoue
        """
        if self._api is not None:
            return self._api

        try:
            # Séparer user et token_name depuis token_id (format: user@pam!tokenname)
            if "!" in self.config.token_id:
                user, token_name = self.config.token_id.split("!", 1)
            else:
                raise ValueError(f"Invalid token_id format: {self.config.token_id}. Expected format: user@pam!tokenname")

            self._api = ProxmoxAPI(
                self.config.host,
                user=user,
                token_name=token_name,
                token_value=self.config.token_secret,
                port=self.config.port,
                verify_ssl=self.config.verify_ssl,
                timeout=self.config.timeout,
            )
            logger.info(f"Connected to Proxmox at {self.config.host}:{self.config.port}")
            return self._api
        except AuthenticationError as e:
            logger.error(f"Proxmox authentication failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to connect to Proxmox: {e}")
            raise

    def list_nodes(self) -> List[Dict[str, Any]]:
        """
        Liste tous les nodes Proxmox

        Returns:
            Liste des nodes avec leurs informations
        """
        api = self.connect()
        try:
            nodes = api.nodes.get()
            logger.debug(f"Found {len(nodes)} Proxmox nodes")
            return nodes
        except Exception as e:
            logger.error(f"Failed to list nodes: {e}")
            raise

    def list_vms(self, node: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Liste toutes les VMs (QEMU) sur un ou tous les nodes

        Args:
            node: Nom du node (optionnel, liste tous les nodes si None)

        Returns:
            Liste des VMs avec leurs informations
        """
        api = self.connect()
        all_vms = []

        try:
            if node:
                nodes = [{"node": node}]
            else:
                nodes = self.list_nodes()

            for n in nodes:
                node_name = n["node"]
                try:
                    vms = api.nodes(node_name).qemu.get()
                    for vm in vms:
                        vm["node"] = node_name
                        vm["type"] = "qemu"
                    all_vms.extend(vms)
                except Exception as e:
                    logger.error(f"Failed to list VMs on node {node_name}: {e}")

            logger.debug(f"Found {len(all_vms)} VMs")
            return all_vms
        except Exception as e:
            logger.error(f"Failed to list VMs: {e}")
            raise

    def list_containers(self, node: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Liste tous les conteneurs LXC sur un ou tous les nodes

        Args:
            node: Nom du node (optionnel)

        Returns:
            Liste des conteneurs avec leurs informations
        """
        api = self.connect()
        all_containers = []

        try:
            if node:
                nodes = [{"node": node}]
            else:
                nodes = self.list_nodes()

            for n in nodes:
                node_name = n["node"]
                try:
                    containers = api.nodes(node_name).lxc.get()
                    for container in containers:
                        container["node"] = node_name
                        container["type"] = "lxc"
                    all_containers.extend(containers)
                except Exception as e:
                    logger.error(f"Failed to list containers on node {node_name}: {e}")

            logger.debug(f"Found {len(all_containers)} containers")
            return all_containers
        except Exception as e:
            logger.error(f"Failed to list containers: {e}")
            raise

    def list_all_guests(self, node: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Liste toutes les VMs et conteneurs

        Args:
            node: Nom du node (optionnel)

        Returns:
            Liste combinée des VMs et conteneurs
        """
        vms = self.list_vms(node)
        containers = self.list_containers(node)
        return vms + containers

    def get_vm_status(self, node: str, vmid: int) -> Dict[str, Any]:
        """
        Récupère le statut détaillé d'une VM

        Args:
            node: Nom du node
            vmid: ID de la VM

        Returns:
            Statut de la VM
        """
        api = self.connect()
        try:
            status = api.nodes(node).qemu(vmid).status.current.get()
            logger.debug(f"VM {vmid} status: {status.get('status')}")
            return status
        except Exception as e:
            logger.error(f"Failed to get status for VM {vmid}: {e}")
            raise

    def get_container_status(self, node: str, vmid: int) -> Dict[str, Any]:
        """
        Récupère le statut détaillé d'un conteneur LXC

        Args:
            node: Nom du node
            vmid: ID du conteneur

        Returns:
            Statut du conteneur
        """
        api = self.connect()
        try:
            status = api.nodes(node).lxc(vmid).status.current.get()
            logger.debug(f"Container {vmid} status: {status.get('status')}")
            return status
        except Exception as e:
            logger.error(f"Failed to get status for container {vmid}: {e}")
            raise

    def start_vm(self, node: str, vmid: int) -> Dict[str, Any]:
        """
        Démarre une VM

        Args:
            node: Nom du node
            vmid: ID de la VM

        Returns:
            Résultat de l'opération
        """
        api = self.connect()
        try:
            result = api.nodes(node).qemu(vmid).status.start.post()
            logger.info(f"Started VM {vmid} on node {node}")
            return {"success": True, "vmid": vmid, "action": "start", "result": result}
        except Exception as e:
            logger.error(f"Failed to start VM {vmid}: {e}")
            return {"success": False, "vmid": vmid, "action": "start", "error": str(e)}

    def stop_vm(self, node: str, vmid: int) -> Dict[str, Any]:
        """
        Arrête une VM

        Args:
            node: Nom du node
            vmid: ID de la VM

        Returns:
            Résultat de l'opération
        """
        api = self.connect()
        try:
            result = api.nodes(node).qemu(vmid).status.stop.post()
            logger.info(f"Stopped VM {vmid} on node {node}")
            return {"success": True, "vmid": vmid, "action": "stop", "result": result}
        except Exception as e:
            logger.error(f"Failed to stop VM {vmid}: {e}")
            return {"success": False, "vmid": vmid, "action": "stop", "error": str(e)}

    def restart_vm(self, node: str, vmid: int) -> Dict[str, Any]:
        """
        Redémarre une VM

        Args:
            node: Nom du node
            vmid: ID de la VM

        Returns:
            Résultat de l'opération
        """
        api = self.connect()
        try:
            result = api.nodes(node).qemu(vmid).status.reboot.post()
            logger.info(f"Restarted VM {vmid} on node {node}")
            return {"success": True, "vmid": vmid, "action": "restart", "result": result}
        except Exception as e:
            logger.error(f"Failed to restart VM {vmid}: {e}")
            return {"success": False, "vmid": vmid, "action": "restart", "error": str(e)}

    def get_vm_config(self, node: str, vmid: int) -> Dict[str, Any]:
        """
        Récupère la configuration d'une VM

        Args:
            node: Nom du node
            vmid: ID de la VM

        Returns:
            Configuration de la VM
        """
        api = self.connect()
        try:
            config = api.nodes(node).qemu(vmid).config.get()
            logger.debug(f"Retrieved config for VM {vmid}")
            return config
        except Exception as e:
            logger.error(f"Failed to get config for VM {vmid}: {e}")
            raise

    def execute_command_via_api(
        self, node: str, vmid: int, command: str, timeout: int = 30
    ) -> Dict[str, Any]:
        """
        Exécute une commande sur une VM via l'API Proxmox (nécessite qemu-guest-agent)

        Args:
            node: Nom du node
            vmid: ID de la VM
            command: Commande à exécuter
            timeout: Timeout en secondes

        Returns:
            Résultat de la commande avec stdout, stderr, exitcode
        """
        import time

        api = self.connect()
        try:
            # Étape 1: Lancer la commande et obtenir le PID
            exec_result = api.nodes(node).qemu(vmid).agent.exec.post(
                command=command
            )
            pid = exec_result.get("pid")
            if not pid:
                raise Exception("No PID returned from agent exec")

            logger.info(f"Executed command on VM {vmid}, PID: {pid}")

            # Étape 2: Polling pour récupérer le résultat
            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    status_result = api.nodes(node).qemu(vmid).agent("exec-status").get(pid=pid)

                    # Vérifier si la commande est terminée
                    if status_result.get("exited"):
                        result = {
                            "exitcode": status_result.get("exitcode", -1),
                            "stdout": status_result.get("out-data", ""),
                            "stderr": status_result.get("err-data", ""),
                            "exited": True,
                        }
                        logger.info(f"Command completed on VM {vmid} with exit code {result['exitcode']}")
                        return result

                    # Attendre un peu avant de réessayer
                    time.sleep(0.5)

                except Exception as e:
                    logger.warning(f"Error polling command status: {e}")
                    time.sleep(0.5)

            # Timeout atteint
            logger.warning(f"Command execution timeout on VM {vmid}")
            return {
                "exitcode": -1,
                "stdout": "",
                "stderr": f"Command timeout after {timeout} seconds",
                "exited": False,
            }

        except Exception as e:
            logger.error(f"Failed to execute command on VM {vmid}: {e}")
            raise

    def get_vm_ip_addresses(self, node: str, vmid: int) -> List[str]:
        """
        Récupère les adresses IP d'une VM (nécessite qemu-guest-agent)

        Args:
            node: Nom du node
            vmid: ID de la VM

        Returns:
            Liste des adresses IP
        """
        api = self.connect()
        try:
            network_info = api.nodes(node).qemu(vmid).agent("network-get-interfaces").get()
            ip_addresses = []

            for interface in network_info.get("result", []):
                if "ip-addresses" in interface:
                    for ip_info in interface["ip-addresses"]:
                        ip = ip_info.get("ip-address")
                        if ip and not ip.startswith("127.") and not ip.startswith("fe80"):
                            ip_addresses.append(ip)

            logger.debug(f"Found {len(ip_addresses)} IP addresses for VM {vmid}")
            return ip_addresses
        except Exception as e:
            logger.warning(f"Failed to get IP addresses for VM {vmid}: {e}")
            return []

    # ===== GESTION AVANCÉE DES VMs =====

    def create_vm(self, node: str, vmid: int, name: str, **config) -> Dict[str, Any]:
        """
        Crée une nouvelle VM

        Args:
            node: Nom du node
            vmid: ID de la nouvelle VM
            name: Nom de la VM
            **config: Configuration de la VM (memory, cores, sockets, etc.)

        Returns:
            Résultat de l'opération
        """
        api = self.connect()
        try:
            params = {"vmid": vmid, "name": name, **config}
            result = api.nodes(node).qemu.post(**params)
            logger.info(f"Created VM {vmid} ({name}) on node {node}")
            return {"success": True, "vmid": vmid, "action": "create", "result": result}
        except Exception as e:
            logger.error(f"Failed to create VM {vmid}: {e}")
            return {"success": False, "vmid": vmid, "action": "create", "error": str(e)}

    def clone_vm(self, node: str, vmid: int, newid: int, name: str, full: bool = True) -> Dict[str, Any]:
        """
        Clone une VM existante

        Args:
            node: Nom du node
            vmid: ID de la VM source
            newid: ID de la nouvelle VM
            name: Nom de la nouvelle VM
            full: Full clone (true) ou linked clone (false)

        Returns:
            Résultat de l'opération
        """
        api = self.connect()
        try:
            params = {"newid": newid, "name": name, "full": 1 if full else 0}
            result = api.nodes(node).qemu(vmid).clone.post(**params)
            logger.info(f"Cloned VM {vmid} to {newid} ({name}) on node {node}")
            return {"success": True, "vmid": newid, "action": "clone", "result": result}
        except Exception as e:
            logger.error(f"Failed to clone VM {vmid}: {e}")
            return {"success": False, "vmid": vmid, "action": "clone", "error": str(e)}

    def delete_vm(self, node: str, vmid: int, purge: bool = False) -> Dict[str, Any]:
        """
        Supprime une VM

        Args:
            node: Nom du node
            vmid: ID de la VM
            purge: Supprimer aussi les disques

        Returns:
            Résultat de l'opération
        """
        api = self.connect()
        try:
            params = {}
            if purge:
                params["purge"] = 1
            result = api.nodes(node).qemu(vmid).delete(**params)
            logger.info(f"Deleted VM {vmid} on node {node}")
            return {"success": True, "vmid": vmid, "action": "delete", "result": result}
        except Exception as e:
            logger.error(f"Failed to delete VM {vmid}: {e}")
            return {"success": False, "vmid": vmid, "action": "delete", "error": str(e)}

    def modify_vm_config(self, node: str, vmid: int, **config) -> Dict[str, Any]:
        """
        Modifie la configuration d'une VM

        Args:
            node: Nom du node
            vmid: ID de la VM
            **config: Paramètres à modifier (memory, cores, sockets, etc.)

        Returns:
            Résultat de l'opération
        """
        api = self.connect()
        try:
            result = api.nodes(node).qemu(vmid).config.put(**config)
            logger.info(f"Modified config for VM {vmid}: {config}")
            return {"success": True, "vmid": vmid, "action": "modify_config", "result": result}
        except Exception as e:
            logger.error(f"Failed to modify VM {vmid} config: {e}")
            return {"success": False, "vmid": vmid, "action": "modify_config", "error": str(e)}

    # ===== SNAPSHOTS =====

    def create_snapshot(self, node: str, vmid: int, snapname: str, description: str = "") -> Dict[str, Any]:
        """
        Crée un snapshot d'une VM

        Args:
            node: Nom du node
            vmid: ID de la VM
            snapname: Nom du snapshot
            description: Description du snapshot

        Returns:
            Résultat de l'opération
        """
        api = self.connect()
        try:
            params = {"snapname": snapname}
            if description:
                params["description"] = description
            result = api.nodes(node).qemu(vmid).snapshot.post(**params)
            logger.info(f"Created snapshot '{snapname}' for VM {vmid}")
            return {"success": True, "vmid": vmid, "snapshot": snapname, "action": "create_snapshot", "result": result}
        except Exception as e:
            logger.error(f"Failed to create snapshot for VM {vmid}: {e}")
            return {"success": False, "vmid": vmid, "action": "create_snapshot", "error": str(e)}

    def list_snapshots(self, node: str, vmid: int) -> List[Dict[str, Any]]:
        """
        Liste les snapshots d'une VM

        Args:
            node: Nom du node
            vmid: ID de la VM

        Returns:
            Liste des snapshots
        """
        api = self.connect()
        try:
            snapshots = api.nodes(node).qemu(vmid).snapshot.get()
            logger.debug(f"Found {len(snapshots)} snapshots for VM {vmid}")
            return snapshots
        except Exception as e:
            logger.error(f"Failed to list snapshots for VM {vmid}: {e}")
            return []

    def restore_snapshot(self, node: str, vmid: int, snapname: str) -> Dict[str, Any]:
        """
        Restaure un snapshot

        Args:
            node: Nom du node
            vmid: ID de la VM
            snapname: Nom du snapshot

        Returns:
            Résultat de l'opération
        """
        api = self.connect()
        try:
            result = api.nodes(node).qemu(vmid).snapshot(snapname).rollback.post()
            logger.info(f"Restored snapshot '{snapname}' for VM {vmid}")
            return {"success": True, "vmid": vmid, "snapshot": snapname, "action": "restore_snapshot", "result": result}
        except Exception as e:
            logger.error(f"Failed to restore snapshot '{snapname}' for VM {vmid}: {e}")
            return {"success": False, "vmid": vmid, "action": "restore_snapshot", "error": str(e)}

    def delete_snapshot(self, node: str, vmid: int, snapname: str) -> Dict[str, Any]:
        """
        Supprime un snapshot

        Args:
            node: Nom du node
            vmid: ID de la VM
            snapname: Nom du snapshot

        Returns:
            Résultat de l'opération
        """
        api = self.connect()
        try:
            result = api.nodes(node).qemu(vmid).snapshot(snapname).delete()
            logger.info(f"Deleted snapshot '{snapname}' for VM {vmid}")
            return {"success": True, "vmid": vmid, "snapshot": snapname, "action": "delete_snapshot", "result": result}
        except Exception as e:
            logger.error(f"Failed to delete snapshot '{snapname}' for VM {vmid}: {e}")
            return {"success": False, "vmid": vmid, "action": "delete_snapshot", "error": str(e)}

    # ===== BACKUPS =====

    def list_backups(self, node: str) -> List[Dict[str, Any]]:
        """
        Liste les backups disponibles sur un node

        Args:
            node: Nom du node

        Returns:
            Liste des backups
        """
        api = self.connect()
        try:
            # Lister tous les storages du node
            storages = api.nodes(node).storage.get()
            all_backups = []

            for storage in storages:
                storage_name = storage.get("storage")
                storage_type = storage.get("type")

                # Seuls certains types de storage supportent les backups
                if storage_type in ["dir", "nfs", "cifs", "pbs"]:
                    try:
                        backups = api.nodes(node).storage(storage_name).content.get(content="backup")
                        for backup in backups:
                            backup["storage"] = storage_name
                        all_backups.extend(backups)
                    except Exception:
                        # Storage ne contient pas de backups ou erreur d'accès
                        pass

            logger.debug(f"Found {len(all_backups)} backups on node {node}")
            return all_backups
        except Exception as e:
            logger.error(f"Failed to list backups on node {node}: {e}")
            return []

    def create_backup(self, node: str, vmid: int, storage: str, mode: str = "snapshot", compress: str = "zstd") -> Dict[str, Any]:
        """
        Crée un backup d'une VM

        Args:
            node: Nom du node
            vmid: ID de la VM
            storage: Storage où sauvegarder
            mode: Mode de backup (snapshot, suspend, stop)
            compress: Compression (0, 1, gzip, lzo, zstd)

        Returns:
            Résultat de l'opération
        """
        api = self.connect()
        try:
            params = {
                "vmid": vmid,
                "storage": storage,
                "mode": mode,
                "compress": compress
            }
            result = api.nodes(node).vzdump.post(**params)
            logger.info(f"Created backup for VM {vmid} to storage {storage}")
            return {"success": True, "vmid": vmid, "action": "create_backup", "result": result}
        except Exception as e:
            logger.error(f"Failed to create backup for VM {vmid}: {e}")
            return {"success": False, "vmid": vmid, "action": "create_backup", "error": str(e)}

    def restore_backup(self, node: str, vmid: int, archive: str, storage: str) -> Dict[str, Any]:
        """
        Restaure un backup

        Args:
            node: Nom du node
            vmid: Nouvel ID pour la VM restaurée
            archive: Nom du fichier de backup
            storage: Storage où restaurer

        Returns:
            Résultat de l'opération
        """
        api = self.connect()
        try:
            params = {
                "vmid": vmid,
                "archive": archive,
                "storage": storage
            }
            result = api.nodes(node).qemu.post(**params)
            logger.info(f"Restored backup {archive} to VM {vmid}")
            return {"success": True, "vmid": vmid, "action": "restore_backup", "result": result}
        except Exception as e:
            logger.error(f"Failed to restore backup {archive}: {e}")
            return {"success": False, "action": "restore_backup", "error": str(e)}

    # ===== STORAGE =====

    def list_storage(self, node: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Liste les storages disponibles

        Args:
            node: Nom du node (optionnel)

        Returns:
            Liste des storages avec leur usage
        """
        api = self.connect()
        try:
            if node:
                nodes_to_check = [{"node": node}]
            else:
                nodes_to_check = self.list_nodes()

            all_storages = []
            for n in nodes_to_check:
                node_name = n["node"]
                try:
                    storages = api.nodes(node_name).storage.get()
                    for storage in storages:
                        storage["node"] = node_name
                    all_storages.extend(storages)
                except Exception as e:
                    logger.warning(f"Failed to list storage on node {node_name}: {e}")

            logger.debug(f"Found {len(all_storages)} storages")
            return all_storages
        except Exception as e:
            logger.error(f"Failed to list storages: {e}")
            return []

    # ===== DISQUES =====

    def add_disk(self, node: str, vmid: int, disk_id: str, size: str, storage: str) -> Dict[str, Any]:
        """
        Ajoute un disque à une VM

        Args:
            node: Nom du node
            vmid: ID de la VM
            disk_id: ID du disque (virtio0, scsi0, etc.)
            size: Taille du disque (ex: "50G")
            storage: Storage où créer le disque

        Returns:
            Résultat de l'opération
        """
        api = self.connect()
        try:
            config = {disk_id: f"{storage}:{size}"}
            result = api.nodes(node).qemu(vmid).config.put(**config)
            logger.info(f"Added disk {disk_id} ({size}) to VM {vmid}")
            return {"success": True, "vmid": vmid, "action": "add_disk", "result": result}
        except Exception as e:
            logger.error(f"Failed to add disk to VM {vmid}: {e}")
            return {"success": False, "vmid": vmid, "action": "add_disk", "error": str(e)}

    def remove_disk(self, node: str, vmid: int, disk_id: str) -> Dict[str, Any]:
        """
        Retire un disque d'une VM

        Args:
            node: Nom du node
            vmid: ID de la VM
            disk_id: ID du disque (virtio0, scsi0, etc.)

        Returns:
            Résultat de l'opération
        """
        api = self.connect()
        try:
            config = {"delete": disk_id}
            result = api.nodes(node).qemu(vmid).config.put(**config)
            logger.info(f"Removed disk {disk_id} from VM {vmid}")
            return {"success": True, "vmid": vmid, "action": "remove_disk", "result": result}
        except Exception as e:
            logger.error(f"Failed to remove disk from VM {vmid}: {e}")
            return {"success": False, "vmid": vmid, "action": "remove_disk", "error": str(e)}

    def resize_disk(self, node: str, vmid: int, disk_id: str, size: str) -> Dict[str, Any]:
        """
        Redimensionne un disque

        Args:
            node: Nom du node
            vmid: ID de la VM
            disk_id: ID du disque (virtio0, scsi0, etc.)
            size: Taille à ajouter (ex: "+10G")

        Returns:
            Résultat de l'opération
        """
        api = self.connect()
        try:
            result = api.nodes(node).qemu(vmid).resize.put(disk=disk_id, size=size)
            logger.info(f"Resized disk {disk_id} on VM {vmid} by {size}")
            return {"success": True, "vmid": vmid, "action": "resize_disk", "result": result}
        except Exception as e:
            logger.error(f"Failed to resize disk on VM {vmid}: {e}")
            return {"success": False, "vmid": vmid, "action": "resize_disk", "error": str(e)}

    # ===== MIGRATION =====

    def migrate_vm(self, node: str, vmid: int, target: str, online: bool = True) -> Dict[str, Any]:
        """
        Migre une VM vers un autre node

        Args:
            node: Node source
            vmid: ID de la VM
            target: Node de destination
            online: Migration à chaud (true) ou à froid (false)

        Returns:
            Résultat de l'opération
        """
        api = self.connect()
        try:
            params = {"target": target, "online": 1 if online else 0}
            result = api.nodes(node).qemu(vmid).migrate.post(**params)
            logger.info(f"Migrated VM {vmid} from {node} to {target}")
            return {"success": True, "vmid": vmid, "action": "migrate", "result": result}
        except Exception as e:
            logger.error(f"Failed to migrate VM {vmid}: {e}")
            return {"success": False, "vmid": vmid, "action": "migrate", "error": str(e)}

    # ===== SERVICES =====

    def manage_service(self, node: str, vmid: int, service_name: str, action: str) -> Dict[str, Any]:
        """
        Gère un service systemd sur une VM

        Args:
            node: Nom du node
            vmid: ID de la VM
            service_name: Nom du service
            action: Action (start, stop, restart, enable, disable, status)

        Returns:
            Résultat de l'opération
        """
        valid_actions = ["start", "stop", "restart", "enable", "disable", "status"]
        if action not in valid_actions:
            return {"success": False, "error": f"Invalid action. Must be one of: {valid_actions}"}

        command = f"systemctl {action} {service_name}"
        result = self.execute_command(node, vmid, command)
        return result

    def list_services(self, node: str, vmid: int) -> Dict[str, Any]:
        """
        Liste les services systemd sur une VM

        Args:
            node: Nom du node
            vmid: ID de la VM

        Returns:
            Liste des services
        """
        command = "systemctl list-units --type=service --all --no-pager"
        result = self.execute_command(node, vmid, command)
        return result

    # ===== FILES =====

    def read_file(self, node: str, vmid: int, file_path: str, lines: int = None) -> Dict[str, Any]:
        """
        Lit le contenu d'un fichier sur une VM

        Args:
            node: Nom du node
            vmid: ID de la VM
            file_path: Chemin du fichier
            lines: Nombre de lignes à lire (optionnel)

        Returns:
            Contenu du fichier
        """
        if lines:
            command = f"head -n {lines} {file_path}"
        else:
            command = f"cat {file_path}"

        result = self.execute_command(node, vmid, command)
        return result

    def write_file(self, node: str, vmid: int, file_path: str, content: str) -> Dict[str, Any]:
        """
        Écrit du contenu dans un fichier sur une VM

        Args:
            node: Nom du node
            vmid: ID de la VM
            file_path: Chemin du fichier
            content: Contenu à écrire

        Returns:
            Résultat de l'opération
        """
        # Échapper les quotes dans le contenu
        escaped_content = content.replace("'", "'\\''")
        command = f"echo '{escaped_content}' > {file_path}"
        result = self.execute_command(node, vmid, command)
        return result

    # ===== PROCESSES =====

    def list_processes(self, node: str, vmid: int) -> Dict[str, Any]:
        """
        Liste les processus sur une VM

        Args:
            node: Nom du node
            vmid: ID de la VM

        Returns:
            Liste des processus
        """
        command = "ps aux --sort=-%mem | head -20"
        result = self.execute_command(node, vmid, command)
        return result

    def kill_process(self, node: str, vmid: int, pid: int, signal: str = "TERM") -> Dict[str, Any]:
        """
        Tue un processus sur une VM

        Args:
            node: Nom du node
            vmid: ID de la VM
            pid: ID du processus
            signal: Signal à envoyer (TERM, KILL, etc.)

        Returns:
            Résultat de l'opération
        """
        valid_signals = ["TERM", "KILL", "HUP", "INT", "QUIT"]
        if signal not in valid_signals:
            return {"success": False, "error": f"Invalid signal. Must be one of: {valid_signals}"}

        command = f"kill -{signal} {pid}"
        result = self.execute_command(node, vmid, command)
        return result
