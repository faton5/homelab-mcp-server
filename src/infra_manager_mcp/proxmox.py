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
