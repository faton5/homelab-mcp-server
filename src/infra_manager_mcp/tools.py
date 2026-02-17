"""
MCP Tools definitions for Infrastructure Manager
"""

import json
import logging
from typing import Any, Dict, List, Optional
from mcp.server import Server
from mcp.types import Tool, TextContent

from .proxmox import ProxmoxClient
from .ssh import SSHClient, CommandExecutor
from .restrictions import CommandValidator, PermissionChecker
from .config import get_config

logger = logging.getLogger(__name__)


def register_tools(server: Server) -> None:
    """
    Enregistre tous les outils MCP sur le serveur

    Args:
        server: Instance du serveur MCP
    """
    # Initialiser les clients
    proxmox = ProxmoxClient()
    ssh_client = SSHClient()
    executor = CommandExecutor(proxmox, ssh_client)
    validator = CommandValidator()
    permissions = PermissionChecker()
    config = get_config()

    # ===== OUTILS PROXMOX =====

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        """Liste tous les outils disponibles"""
        return [
            Tool(
                name="list_servers",
                description="Liste tous les serveurs configurés et les VMs/conteneurs Proxmox",
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
            ),
            Tool(
                name="list_nodes",
                description="Liste tous les nodes Proxmox avec leur statut",
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
            ),
            Tool(
                name="list_vms",
                description="Liste toutes les VMs et conteneurs sur Proxmox",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "node": {
                            "type": "string",
                            "description": "Nom du node Proxmox (optionnel, liste tous si absent)",
                        }
                    },
                },
            ),
            Tool(
                name="get_vm_status",
                description="Obtenir le statut détaillé d'une VM ou conteneur",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "server_name": {
                            "type": "string",
                            "description": "Nom du serveur",
                        }
                    },
                    "required": ["server_name"],
                },
            ),
            Tool(
                name="start_vm",
                description="Démarrer une VM ou un conteneur",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "server_name": {
                            "type": "string",
                            "description": "Nom du serveur à démarrer",
                        }
                    },
                    "required": ["server_name"],
                },
            ),
            Tool(
                name="stop_vm",
                description="Arrêter une VM ou un conteneur (NÉCESSITE CONFIRMATION)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "server_name": {
                            "type": "string",
                            "description": "Nom du serveur à arrêter",
                        }
                    },
                    "required": ["server_name"],
                },
            ),
            Tool(
                name="restart_vm",
                description="Redémarrer une VM ou un conteneur (NÉCESSITE CONFIRMATION)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "server_name": {
                            "type": "string",
                            "description": "Nom du serveur à redémarrer",
                        }
                    },
                    "required": ["server_name"],
                },
            ),
            Tool(
                name="execute_command",
                description="Exécuter une commande sur un serveur (SSH ou API Proxmox)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "server_name": {
                            "type": "string",
                            "description": "Nom du serveur",
                        },
                        "command": {
                            "type": "string",
                            "description": "Commande à exécuter",
                        },
                        "sudo": {
                            "type": "boolean",
                            "description": "Exécuter avec sudo",
                            "default": False,
                        },
                    },
                    "required": ["server_name", "command"],
                },
            ),
            Tool(
                name="get_system_info",
                description="Obtenir les informations système (CPU, RAM, disque, load)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "server_name": {
                            "type": "string",
                            "description": "Nom du serveur",
                        }
                    },
                    "required": ["server_name"],
                },
            ),
            Tool(
                name="check_updates",
                description="Vérifier les mises à jour disponibles sur un serveur",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "server_name": {
                            "type": "string",
                            "description": "Nom du serveur",
                        }
                    },
                    "required": ["server_name"],
                },
            ),
            Tool(
                name="install_updates",
                description="Installer les mises à jour système (NÉCESSITE CONFIRMATION)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "server_name": {
                            "type": "string",
                            "description": "Nom du serveur",
                        }
                    },
                    "required": ["server_name"],
                },
            ),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: Any) -> list[TextContent]:
        """Gestionnaire d'appels d'outils"""
        try:
            if name == "list_servers":
                return await handle_list_servers(proxmox, config)

            elif name == "list_nodes":
                return await handle_list_nodes(proxmox)

            elif name == "list_vms":
                node = arguments.get("node")
                return await handle_list_vms(proxmox, node)

            elif name == "get_vm_status":
                server_name = arguments["server_name"]
                return await handle_get_vm_status(proxmox, config, server_name)

            elif name == "start_vm":
                server_name = arguments["server_name"]
                return await handle_start_vm(proxmox, config, permissions, server_name)

            elif name == "stop_vm":
                server_name = arguments["server_name"]
                return await handle_stop_vm(proxmox, config, permissions, server_name)

            elif name == "restart_vm":
                server_name = arguments["server_name"]
                return await handle_restart_vm(proxmox, config, permissions, server_name)

            elif name == "execute_command":
                server_name = arguments["server_name"]
                command = arguments["command"]
                sudo = arguments.get("sudo", False)
                return await handle_execute_command(
                    executor, validator, server_name, command, sudo
                )

            elif name == "get_system_info":
                server_name = arguments["server_name"]
                return await handle_get_system_info(executor, server_name)

            elif name == "check_updates":
                server_name = arguments["server_name"]
                return await handle_check_updates(executor, server_name)

            elif name == "install_updates":
                server_name = arguments["server_name"]
                return await handle_install_updates(executor, server_name)

            else:
                return [TextContent(type="text", text=f"Unknown tool: {name}")]

        except Exception as e:
            logger.error(f"Error executing tool {name}: {e}")
            return [TextContent(type="text", text=f"Error: {str(e)}")]


# ===== HANDLERS D'OUTILS =====


def find_vm_by_name(proxmox: ProxmoxClient, config, vm_name: str) -> Optional[Dict[str, Any]]:
    """
    Cherche une VM par son nom, d'abord dans la config manuelle puis dans Proxmox

    Args:
        proxmox: Client Proxmox
        config: Configuration
        vm_name: Nom de la VM à chercher

    Returns:
        Dict avec les infos de la VM ou None si non trouvée
    """
    # D'abord chercher dans les serveurs configurés manuellement
    server = config.get_server_by_name(vm_name)
    if server:
        return {
            "name": server.name,
            "type": server.type,
            "vmid": server.vmid,
            "node": server.node,
            "ssh_enabled": server.ssh_enabled,
            "ssh_host": server.ssh_host,
            "ssh_user": server.ssh_user,
            "ssh_port": server.ssh_port,
        }

    # Si non trouvé, chercher dans les VMs détectées par Proxmox
    try:
        all_vms = proxmox.list_all_guests()
        for vm in all_vms:
            if vm.get("name") == vm_name:
                # Déterminer le type (qemu = VM, lxc = container)
                vm_type = "proxmox-vm" if vm.get("type") == "qemu" else "proxmox-lxc"
                return {
                    "name": vm.get("name"),
                    "type": vm_type,
                    "vmid": vm.get("vmid"),
                    "node": vm.get("node"),
                    "ssh_enabled": False,  # Pas de config SSH pour VMs auto-détectées
                    "ssh_host": None,
                    "ssh_user": None,
                    "ssh_port": None,
                }
    except Exception as e:
        logger.error(f"Error searching for VM in Proxmox: {e}")

    return None


async def handle_list_servers(proxmox: ProxmoxClient, config) -> list[TextContent]:
    """Liste tous les serveurs"""
    try:
        all_guests = proxmox.list_all_guests()
        configured_servers = config.servers

        result = {
            "configured_servers": [
                {
                    "name": s.name,
                    "type": s.type,
                    "vmid": s.vmid,
                    "node": s.node,
                    "ssh_enabled": s.ssh_enabled,
                }
                for s in configured_servers
            ],
            "detected_vms": [
                {
                    "name": vm.get("name"),
                    "vmid": vm.get("vmid"),
                    "node": vm.get("node"),
                    "status": vm.get("status"),
                    "type": vm.get("type"),
                }
                for vm in all_guests
            ],
        }

        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    except Exception as e:
        return [TextContent(type="text", text=f"Error listing servers: {str(e)}")]


async def handle_list_nodes(proxmox: ProxmoxClient) -> list[TextContent]:
    """Liste les nodes Proxmox"""
    try:
        nodes = proxmox.list_nodes()
        return [TextContent(type="text", text=json.dumps(nodes, indent=2))]
    except Exception as e:
        return [TextContent(type="text", text=f"Error listing nodes: {str(e)}")]


async def handle_list_vms(proxmox: ProxmoxClient, node: Optional[str]) -> list[TextContent]:
    """Liste les VMs"""
    try:
        vms = proxmox.list_all_guests(node)
        return [TextContent(type="text", text=json.dumps(vms, indent=2))]
    except Exception as e:
        return [TextContent(type="text", text=f"Error listing VMs: {str(e)}")]


async def handle_get_vm_status(
    proxmox: ProxmoxClient, config, server_name: str
) -> list[TextContent]:
    """Obtient le statut d'une VM"""
    try:
        server = find_vm_by_name(proxmox, config, server_name)
        if not server or not server.get("vmid") or not server.get("node"):
            return [TextContent(type="text", text=f"Server '{server_name}' not found or misconfigured")]

        if server["type"] == "proxmox-vm":
            status = proxmox.get_vm_status(server["node"], server["vmid"])
        elif server["type"] == "proxmox-lxc":
            status = proxmox.get_container_status(server["node"], server["vmid"])
        else:
            return [TextContent(type="text", text=f"Cannot get status for server type: {server['type']}")]

        return [TextContent(type="text", text=json.dumps(status, indent=2))]
    except Exception as e:
        return [TextContent(type="text", text=f"Error getting VM status: {str(e)}")]


async def handle_start_vm(
    proxmox: ProxmoxClient, config, permissions: PermissionChecker, server_name: str
) -> list[TextContent]:
    """Démarre une VM"""
    try:
        allowed, error = permissions.check_operation_permission("vm_control")
        if not allowed:
            return [TextContent(type="text", text=error)]

        server = find_vm_by_name(proxmox, config, server_name)
        if not server or not server.get("vmid") or not server.get("node"):
            return [TextContent(type="text", text=f"Server '{server_name}' not found")]

        result = proxmox.start_vm(server["node"], server["vmid"])
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    except Exception as e:
        return [TextContent(type="text", text=f"Error starting VM: {str(e)}")]


async def handle_stop_vm(
    proxmox: ProxmoxClient, config, permissions: PermissionChecker, server_name: str
) -> list[TextContent]:
    """Arrête une VM - NÉCESSITE CONFIRMATION"""
    try:
        allowed, error = permissions.check_operation_permission("vm_control")
        if not allowed:
            return [TextContent(type="text", text=error)]

        return [
            TextContent(
                type="text",
                text=f"⚠️ CONFIRMATION REQUISE: Voulez-vous vraiment arrêter le serveur '{server_name}' ? "
                f"Cette action va éteindre la VM. Veuillez confirmer avant que j'exécute cette action.",
            )
        ]
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def handle_restart_vm(
    proxmox: ProxmoxClient, config, permissions: PermissionChecker, server_name: str
) -> list[TextContent]:
    """Redémarre une VM - NÉCESSITE CONFIRMATION"""
    try:
        allowed, error = permissions.check_operation_permission("vm_control")
        if not allowed:
            return [TextContent(type="text", text=error)]

        return [
            TextContent(
                type="text",
                text=f"⚠️ CONFIRMATION REQUISE: Voulez-vous vraiment redémarrer le serveur '{server_name}' ? "
                f"Cette action va redémarrer la VM. Veuillez confirmer avant que j'exécute cette action.",
            )
        ]
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def handle_execute_command(
    executor: CommandExecutor,
    validator: CommandValidator,
    server_name: str,
    command: str,
    sudo: bool,
) -> list[TextContent]:
    """Exécute une commande sur un serveur"""
    try:
        # Valider la commande
        is_allowed, error, requires_confirmation = validator.validate_command(command)

        if not is_allowed:
            return [TextContent(type="text", text=f"❌ Commande bloquée: {error}")]

        if requires_confirmation:
            return [
                TextContent(
                    type="text",
                    text=f"⚠️ CONFIRMATION REQUISE: La commande `{command}` sur le serveur '{server_name}' "
                    f"nécessite une confirmation explicite. Veuillez confirmer avant que j'exécute cette commande.",
                )
            ]

        # Exécuter la commande
        result = executor.execute(server_name, command, sudo=sudo)

        if result["success"]:
            output = f"✅ Commande exécutée avec succès via {result['method']}:\n\n"
            if "stdout" in result:
                output += f"Sortie:\n{result['stdout']}\n"
                if "stderr" in result and result["stderr"]:
                    output += f"\nErreurs/Warnings:\n{result['stderr']}"
            elif "result" in result:
                output += f"Résultat:\n{json.dumps(result['result'], indent=2)}"
            return [TextContent(type="text", text=output)]
        else:
            return [
                TextContent(
                    type="text", text=f"❌ Erreur lors de l'exécution: {result.get('error', 'Unknown error')}"
                )
            ]

    except Exception as e:
        return [TextContent(type="text", text=f"Error executing command: {str(e)}")]


async def handle_get_system_info(executor: CommandExecutor, server_name: str) -> list[TextContent]:
    """Obtient les infos système"""
    try:
        command = """
        echo "=== CPU ===" && \
        nproc && \
        grep "model name" /proc/cpuinfo | head -1 && \
        echo "\n=== RAM ===" && \
        free -h && \
        echo "\n=== DISK ===" && \
        df -h && \
        echo "\n=== LOAD ===" && \
        uptime
        """
        result = executor.execute(server_name, command, sudo=False)

        if result["success"]:
            # Gérer les deux formats de retour (SSH avec stdout, ou Proxmox API avec result)
            if "stdout" in result:
                return [TextContent(type="text", text=f"Informations système de {server_name}:\n\n{result['stdout']}")]
            elif "result" in result:
                return [TextContent(type="text", text=f"Informations système de {server_name}:\n\n{json.dumps(result['result'], indent=2)}")]
            else:
                return [TextContent(type="text", text=f"Commande exécutée avec succès via {result.get('method')}")]
        else:
            return [TextContent(type="text", text=f"Error: {result.get('error', 'Unknown error')}")]

    except Exception as e:
        return [TextContent(type="text", text=f"Error getting system info: {str(e)}")]


async def handle_check_updates(executor: CommandExecutor, server_name: str) -> list[TextContent]:
    """Vérifie les mises à jour"""
    try:
        # Détecter le gestionnaire de paquets
        detect_cmd = "which apt || which yum || which dnf"
        detect_result = executor.execute(server_name, detect_cmd, sudo=False)

        if not detect_result["success"]:
            return [TextContent(type="text", text="Impossible de détecter le gestionnaire de paquets")]

        # Gérer les deux formats de retour
        package_manager = None
        if "stdout" in detect_result:
            package_manager = detect_result["stdout"].strip().split("/")[-1]
        elif "result" in detect_result:
            # Pour Proxmox API, essayer de parser le résultat
            result_str = str(detect_result["result"])
            if "apt" in result_str:
                package_manager = "apt"
            elif "yum" in result_str:
                package_manager = "yum"
            elif "dnf" in result_str:
                package_manager = "dnf"

        if not package_manager:
            return [TextContent(type="text", text="Gestionnaire de paquets non supporté")]

        if package_manager == "apt":
            cmd = "apt update && apt list --upgradable"
        elif package_manager in ["yum", "dnf"]:
            cmd = f"{package_manager} check-update"
        else:
            return [TextContent(type="text", text="Gestionnaire de paquets non supporté")]

        result = executor.execute(server_name, cmd, sudo=True)

        if result["success"]:
            # Gérer les deux formats de retour
            if "stdout" in result:
                return [
                    TextContent(type="text", text=f"Mises à jour disponibles sur {server_name}:\n\n{result['stdout']}")
                ]
            elif "result" in result:
                return [
                    TextContent(type="text", text=f"Mises à jour disponibles sur {server_name}:\n\n{json.dumps(result['result'], indent=2)}")
                ]
            else:
                return [TextContent(type="text", text=f"Commande exécutée avec succès via {result.get('method')}")]
        else:
            return [TextContent(type="text", text=f"Error: {result.get('error', 'Unknown error')}")]

    except Exception as e:
        return [TextContent(type="text", text=f"Error checking updates: {str(e)}")]


async def handle_install_updates(executor: CommandExecutor, server_name: str) -> list[TextContent]:
    """Installe les mises à jour - NÉCESSITE CONFIRMATION"""
    return [
        TextContent(
            type="text",
            text=f"⚠️ CONFIRMATION REQUISE: Voulez-vous vraiment installer les mises à jour sur '{server_name}' ? "
            f"Cette action peut prendre du temps et nécessiter un redémarrage. "
            f"Veuillez confirmer avant que j'exécute cette action.",
        )
    ]
