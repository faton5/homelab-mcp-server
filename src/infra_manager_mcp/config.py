"""
Configuration management for Infrastructure Manager MCP
"""

import os
from pathlib import Path
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
import yaml


class ProxmoxConfig(BaseModel):
    """Configuration Proxmox"""
    host: str
    port: int = 8006
    token_id: str
    token_secret: str
    verify_ssl: bool = False
    timeout: int = 30


class SSHConfig(BaseModel):
    """Configuration SSH"""
    enabled: bool = True
    key_path: Optional[str] = None
    default_user: str = "root"
    timeout: int = 30
    port: int = 22


class RestrictionsConfig(BaseModel):
    """Configuration des restrictions de sécurité"""
    require_confirmation: List[str] = Field(default_factory=list)
    blocked_commands: List[str] = Field(default_factory=list)
    protected_paths: List[str] = Field(default_factory=list)


class ServerConfig(BaseModel):
    """Configuration d'un serveur"""
    name: str
    type: str  # proxmox-vm, proxmox-lxc, ssh-only
    vmid: Optional[int] = None
    node: Optional[str] = None
    ssh_enabled: bool = True
    ssh_host: Optional[str] = None
    ssh_user: Optional[str] = None
    ssh_port: Optional[int] = None


class MCPConfig(BaseModel):
    """Configuration du serveur MCP"""
    name: str = "infra-manager"
    version: str = "1.0.0"
    log_level: str = "INFO"
    log_file: str = "/var/log/infra-manager-mcp.log"


class FeaturesConfig(BaseModel):
    """Configuration des fonctionnalités"""
    auto_detect_vms: bool = True
    allow_vm_control: bool = True
    allow_package_management: bool = True
    allow_user_management: bool = True
    allow_service_management: bool = True
    allow_file_operations: bool = True


class Config(BaseModel):
    """Configuration complète"""
    proxmox: ProxmoxConfig
    ssh: SSHConfig = Field(default_factory=SSHConfig)
    restrictions: RestrictionsConfig = Field(default_factory=RestrictionsConfig)
    servers: List[ServerConfig] = Field(default_factory=list)
    mcp: MCPConfig = Field(default_factory=MCPConfig)
    features: FeaturesConfig = Field(default_factory=FeaturesConfig)

    @classmethod
    def load_from_env(cls) -> "Config":
        """
        Charge la configuration depuis les variables d'environnement

        Returns:
            Instance de Config
        """
        # Configuration Proxmox depuis ENV
        proxmox_config = ProxmoxConfig(
            host=os.getenv("PROXMOX_HOST", ""),
            port=int(os.getenv("PROXMOX_PORT", "8006")),
            token_id=os.getenv("PROXMOX_TOKEN_ID", ""),
            token_secret=os.getenv("PROXMOX_TOKEN_SECRET", ""),
            verify_ssl=os.getenv("PROXMOX_VERIFY_SSL", "false").lower() == "true",
            timeout=int(os.getenv("PROXMOX_TIMEOUT", "30")),
        )

        # Configuration SSH depuis ENV
        ssh_config = SSHConfig(
            enabled=os.getenv("SSH_ENABLED", "true").lower() == "true",
            key_path=os.getenv("SSH_KEY_PATH"),
            default_user=os.getenv("SSH_DEFAULT_USER", "root"),
            timeout=int(os.getenv("SSH_TIMEOUT", "30")),
            port=int(os.getenv("SSH_PORT", "22")),
        )

        # Configuration MCP depuis ENV
        mcp_config = MCPConfig(
            name=os.getenv("MCP_NAME", "infra-manager"),
            version=os.getenv("MCP_VERSION", "1.0.0"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            log_file=os.getenv("MCP_LOG_FILE", "/var/log/infra-manager-mcp.log"),
        )

        return cls(
            proxmox=proxmox_config,
            ssh=ssh_config,
            mcp=mcp_config,
            restrictions=RestrictionsConfig(),  # Defaults
            servers=[],  # Auto-détection depuis Proxmox
            features=FeaturesConfig(),  # Defaults
        )

    @classmethod
    def load_from_file(cls, config_path: Optional[str] = None) -> "Config":
        """
        Charge la configuration depuis un fichier YAML

        Args:
            config_path: Chemin vers le fichier de config (ou None pour utiliser CONFIG_PATH env)

        Returns:
            Instance de Config
        """
        if config_path is None:
            config_path = os.getenv("CONFIG_PATH", "/app/config.yaml")

        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with open(path, "r") as f:
            data = yaml.safe_load(f)

        return cls(**data)

    @classmethod
    def load(cls) -> "Config":
        """
        Charge la configuration (ENV en priorité, sinon fichier YAML)

        Returns:
            Instance de Config
        """
        # Si les ENV vars Proxmox sont définies, utiliser ENV
        if os.getenv("PROXMOX_HOST") and os.getenv("PROXMOX_TOKEN_ID"):
            return cls.load_from_env()
        # Sinon, charger depuis le fichier YAML
        else:
            return cls.load_from_file()

    def is_command_blocked(self, command: str) -> bool:
        """
        Vérifie si une commande est bloquée

        Args:
            command: La commande à vérifier

        Returns:
            True si la commande est bloquée
        """
        command_lower = command.lower().strip()
        for blocked in self.restrictions.blocked_commands:
            if blocked.lower() in command_lower:
                return True
        return False

    def requires_confirmation(self, command: str) -> bool:
        """
        Vérifie si une commande nécessite une confirmation

        Args:
            command: La commande à vérifier

        Returns:
            True si la commande nécessite confirmation
        """
        command_lower = command.lower().strip()
        for pattern in self.restrictions.require_confirmation:
            if pattern.lower() in command_lower:
                return True
        return False

    def is_path_protected(self, path: str) -> bool:
        """
        Vérifie si un chemin est protégé

        Args:
            path: Le chemin à vérifier

        Returns:
            True si le chemin est protégé
        """
        for protected in self.restrictions.protected_paths:
            if path.startswith(protected):
                return True
        return False

    def get_server_by_name(self, name: str) -> Optional[ServerConfig]:
        """
        Récupère un serveur par son nom

        Args:
            name: Nom du serveur

        Returns:
            ServerConfig ou None si non trouvé
        """
        for server in self.servers:
            if server.name == name:
                return server
        return None


# Instance globale de configuration (sera initialisée au démarrage)
_config: Optional[Config] = None


def get_config() -> Config:
    """
    Récupère l'instance globale de configuration

    Returns:
        Instance de Config

    Raises:
        RuntimeError: Si la config n'a pas été initialisée
    """
    global _config
    if _config is None:
        raise RuntimeError("Configuration not initialized. Call init_config() first.")
    return _config


def init_config(config_path: Optional[str] = None) -> Config:
    """
    Initialise la configuration globale
    (ENV variables en priorité, sinon fichier YAML)

    Args:
        config_path: Chemin vers le fichier de config (optionnel si ENV définies)

    Returns:
        Instance de Config
    """
    global _config
    # Utiliser Config.load() qui choisit automatiquement ENV ou fichier
    if config_path:
        _config = Config.load_from_file(config_path)
    else:
        _config = Config.load()
    return _config
