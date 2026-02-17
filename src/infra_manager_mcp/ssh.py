"""
SSH client for Infrastructure Manager MCP
"""

import logging
import paramiko
from typing import Optional, Tuple, Dict, Any
from pathlib import Path
from .config import get_config, ServerConfig

logger = logging.getLogger(__name__)


class SSHClient:
    """Client SSH pour exécuter des commandes sur des serveurs distants"""

    def __init__(self):
        config = get_config()
        self.config = config.ssh
        self.connections: Dict[str, paramiko.SSHClient] = {}

    def _get_connection(
        self,
        host: str,
        user: str,
        port: int = 22,
        password: Optional[str] = None,
        key_path: Optional[str] = None,
    ) -> paramiko.SSHClient:
        """
        Crée ou récupère une connexion SSH

        Args:
            host: Adresse du serveur
            user: Nom d'utilisateur
            port: Port SSH
            password: Mot de passe (optionnel)
            key_path: Chemin vers la clé privée (optionnel)

        Returns:
            Client SSH connecté
        """
        connection_key = f"{user}@{host}:{port}"

        # Réutiliser la connexion existante si disponible
        if connection_key in self.connections:
            client = self.connections[connection_key]
            try:
                # Vérifier si la connexion est toujours active
                transport = client.get_transport()
                if transport and transport.is_active():
                    return client
            except Exception:
                pass
            # Connexion morte, la fermer
            try:
                client.close()
            except Exception:
                pass
            del self.connections[connection_key]

        # Créer une nouvelle connexion
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            # Déterminer la méthode d'authentification
            auth_kwargs = {
                "hostname": host,
                "port": port,
                "username": user,
                "timeout": self.config.timeout,
            }

            if password:
                auth_kwargs["password"] = password
            elif key_path or self.config.key_path:
                key_file = key_path or self.config.key_path
                if key_file and Path(key_file).exists():
                    auth_kwargs["key_filename"] = key_file
                else:
                    # Essayer les clés SSH par défaut
                    pass

            client.connect(**auth_kwargs)
            logger.info(f"SSH connected to {connection_key}")
            self.connections[connection_key] = client
            return client

        except paramiko.AuthenticationException as e:
            logger.error(f"SSH authentication failed for {connection_key}: {e}")
            raise
        except paramiko.SSHException as e:
            logger.error(f"SSH connection failed for {connection_key}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error connecting to {connection_key}: {e}")
            raise

    def execute_command(
        self,
        host: str,
        command: str,
        user: Optional[str] = None,
        port: Optional[int] = None,
        password: Optional[str] = None,
        sudo: bool = False,
        timeout: Optional[int] = None,
    ) -> Tuple[int, str, str]:
        """
        Exécute une commande SSH sur un serveur

        Args:
            host: Adresse du serveur
            command: Commande à exécuter
            user: Nom d'utilisateur (optionnel, utilise default_user si None)
            port: Port SSH (optionnel, utilise 22 par défaut)
            password: Mot de passe (optionnel)
            sudo: Exécuter avec sudo
            timeout: Timeout en secondes (optionnel)

        Returns:
            Tuple (exit_code, stdout, stderr)
        """
        user = user or self.config.default_user
        port = port or self.config.port
        timeout = timeout or self.config.timeout

        if sudo and not command.startswith("sudo "):
            command = f"sudo {command}"

        try:
            client = self._get_connection(
                host=host,
                user=user,
                port=port,
                password=password,
            )

            logger.debug(f"Executing command on {host}: {command}")
            stdin, stdout, stderr = client.exec_command(command, timeout=timeout)

            # Lire la sortie
            exit_code = stdout.channel.recv_exit_status()
            stdout_data = stdout.read().decode("utf-8", errors="replace")
            stderr_data = stderr.read().decode("utf-8", errors="replace")

            logger.debug(
                f"Command completed with exit code {exit_code}, "
                f"stdout: {len(stdout_data)} bytes, stderr: {len(stderr_data)} bytes"
            )

            return exit_code, stdout_data, stderr_data

        except paramiko.SSHException as e:
            logger.error(f"SSH error executing command: {e}")
            return -1, "", f"SSH Error: {str(e)}"
        except Exception as e:
            logger.error(f"Error executing command: {e}")
            return -1, "", f"Error: {str(e)}"

    def execute_command_for_server(
        self,
        server: ServerConfig,
        command: str,
        sudo: bool = False,
        timeout: Optional[int] = None,
    ) -> Tuple[int, str, str]:
        """
        Exécute une commande sur un serveur configuré

        Args:
            server: Configuration du serveur
            command: Commande à exécuter
            sudo: Exécuter avec sudo
            timeout: Timeout en secondes

        Returns:
            Tuple (exit_code, stdout, stderr)
        """
        if not server.ssh_enabled:
            return -1, "", "SSH is disabled for this server"

        if not server.ssh_host:
            return -1, "", "SSH host not configured for this server"

        return self.execute_command(
            host=server.ssh_host,
            command=command,
            user=server.ssh_user or self.config.default_user,
            port=server.ssh_port or self.config.port,
            sudo=sudo,
            timeout=timeout,
        )

    def close_connection(self, host: str, user: str, port: int = 22) -> None:
        """
        Ferme une connexion SSH

        Args:
            host: Adresse du serveur
            user: Nom d'utilisateur
            port: Port SSH
        """
        connection_key = f"{user}@{host}:{port}"
        if connection_key in self.connections:
            try:
                self.connections[connection_key].close()
                logger.info(f"Closed SSH connection to {connection_key}")
            except Exception as e:
                logger.error(f"Error closing connection to {connection_key}: {e}")
            finally:
                del self.connections[connection_key]

    def close_all_connections(self) -> None:
        """Ferme toutes les connexions SSH"""
        for connection_key in list(self.connections.keys()):
            try:
                self.connections[connection_key].close()
            except Exception as e:
                logger.error(f"Error closing connection {connection_key}: {e}")
        self.connections.clear()
        logger.info("Closed all SSH connections")

    def __del__(self):
        """Ferme toutes les connexions à la destruction"""
        self.close_all_connections()


class CommandExecutor:
    """Exécuteur de commandes qui choisit automatiquement SSH ou API Proxmox"""

    def __init__(self, proxmox_client, ssh_client: SSHClient):
        self.proxmox = proxmox_client
        self.ssh = ssh_client
        self.config = get_config()

    def _find_server(self, server_name: str) -> Optional[Dict[str, Any]]:
        """
        Cherche un serveur par son nom (config manuelle ou Proxmox)

        Args:
            server_name: Nom du serveur

        Returns:
            Dict avec les infos du serveur ou None
        """
        # Chercher dans la config manuelle
        server_config = self.config.get_server_by_name(server_name)
        if server_config:
            return {
                "name": server_config.name,
                "type": server_config.type,
                "vmid": server_config.vmid,
                "node": server_config.node,
                "ssh_enabled": server_config.ssh_enabled,
                "ssh_host": server_config.ssh_host,
                "ssh_user": server_config.ssh_user,
                "ssh_port": server_config.ssh_port,
            }

        # Chercher dans Proxmox
        try:
            all_vms = self.proxmox.list_all_guests()
            for vm in all_vms:
                if vm.get("name") == server_name:
                    vm_type = "proxmox-vm" if vm.get("type") == "qemu" else "proxmox-lxc"
                    return {
                        "name": vm.get("name"),
                        "type": vm_type,
                        "vmid": vm.get("vmid"),
                        "node": vm.get("node"),
                        "ssh_enabled": False,
                        "ssh_host": None,
                        "ssh_user": None,
                        "ssh_port": None,
                    }
        except Exception as e:
            logger.error(f"Error searching for VM in Proxmox: {e}")

        return None

    def execute(
        self,
        server_name: str,
        command: str,
        sudo: bool = False,
        prefer_ssh: bool = True,
        timeout: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Exécute une commande sur un serveur en choisissant la meilleure méthode

        Args:
            server_name: Nom du serveur
            command: Commande à exécuter
            sudo: Exécuter avec sudo
            prefer_ssh: Préférer SSH à l'API Proxmox si disponible
            timeout: Timeout en secondes

        Returns:
            Dict avec les résultats de l'exécution
        """
        server = self._find_server(server_name)
        if not server:
            return {
                "success": False,
                "error": f"Server '{server_name}' not found in configuration or Proxmox",
                "method": None,
            }

        # Essayer SSH en premier si préféré et disponible
        if prefer_ssh and server.get("ssh_enabled") and server.get("ssh_host"):
            try:
                # Créer un ServerConfig temporaire pour l'appel SSH
                from .config import ServerConfig
                server_config = ServerConfig(**server)
                exit_code, stdout, stderr = self.ssh.execute_command_for_server(
                    server=server_config,
                    command=command,
                    sudo=sudo,
                    timeout=timeout,
                )
                return {
                    "success": exit_code == 0,
                    "exit_code": exit_code,
                    "stdout": stdout,
                    "stderr": stderr,
                    "method": "ssh",
                    "server": server_name,
                }
            except Exception as e:
                logger.warning(f"SSH execution failed, trying Proxmox API: {e}")

        # Fallback vers l'API Proxmox si VM/LXC
        if server.get("type") in ["proxmox-vm", "proxmox-lxc"] and server.get("vmid") and server.get("node"):
            try:
                result = self.proxmox.execute_command_via_api(
                    node=server["node"],
                    vmid=server["vmid"],
                    command=command,
                    timeout=timeout or 30,
                )
                # Le résultat a maintenant le même format que SSH (exitcode, stdout, stderr)
                return {
                    "success": result.get("exitcode") == 0,
                    "exit_code": result.get("exitcode", -1),
                    "stdout": result.get("stdout", ""),
                    "stderr": result.get("stderr", ""),
                    "method": "proxmox_api",
                    "server": server_name,
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e),
                    "method": "proxmox_api",
                    "server": server_name,
                }

        return {
            "success": False,
            "error": "No available execution method for this server",
            "method": None,
            "server": server_name,
        }
