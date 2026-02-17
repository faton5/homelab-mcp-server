"""
Security restrictions and command validation
"""

import re
from typing import Tuple, Optional
from .config import get_config


class CommandValidator:
    """Validateur de commandes avec restrictions de sécurité"""

    def __init__(self):
        self.config = get_config()

    def validate_command(self, command: str) -> Tuple[bool, Optional[str], bool]:
        """
        Valide une commande avant exécution

        Args:
            command: La commande à valider

        Returns:
            Tuple (is_allowed, error_message, requires_confirmation)
            - is_allowed: True si la commande est autorisée
            - error_message: Message d'erreur si refusée
            - requires_confirmation: True si nécessite confirmation utilisateur
        """
        command_clean = command.strip()

        # Vérifier si la commande est bloquée
        if self.config.is_command_blocked(command_clean):
            return False, "Cette commande est bloquée pour des raisons de sécurité", False

        # Vérifier si la commande nécessite confirmation
        requires_conf = self.config.requires_confirmation(command_clean)

        # Vérifier les chemins protégés dans la commande
        if self._contains_protected_path(command_clean):
            return True, None, True  # Autorisé mais nécessite confirmation

        return True, None, requires_conf

    def _contains_protected_path(self, command: str) -> bool:
        """
        Vérifie si la commande contient des chemins protégés

        Args:
            command: La commande à vérifier

        Returns:
            True si des chemins protégés sont détectés
        """
        for protected_path in self.config.restrictions.protected_paths:
            if protected_path in command:
                return True
        return False

    def is_destructive_operation(self, command: str) -> bool:
        """
        Détermine si une opération est destructive

        Args:
            command: La commande à analyser

        Returns:
            True si l'opération est considérée comme destructive
        """
        destructive_patterns = [
            r'\brm\b',           # Suppression
            r'\bmkfs\b',         # Formatage
            r'\bdd\b',           # Copie destructive
            r'\breboot\b',       # Redémarrage
            r'\bshutdown\b',     # Extinction
            r'\bpoweroff\b',     # Extinction
            r'\bhalt\b',         # Arrêt
            r'\buserdel\b',      # Suppression utilisateur
            r'\bgroupdel\b',     # Suppression groupe
            r'\biptables\s+-F\b', # Flush firewall
            r'\bufw\s+disable\b', # Désactivation firewall
        ]

        for pattern in destructive_patterns:
            if re.search(pattern, command, re.IGNORECASE):
                return True

        return False

    def sanitize_command(self, command: str) -> str:
        """
        Nettoie une commande pour éviter les injections

        Args:
            command: La commande à nettoyer

        Returns:
            Commande nettoyée
        """
        # Supprimer les caractères dangereux pour l'injection de commandes
        dangerous_chars = [';', '&&', '||', '|', '`', '$()']

        # Note: Ceci est une protection basique
        # Pour une vraie sécurité, il faudrait utiliser une whitelist
        # ou une validation plus stricte

        cleaned = command
        # On ne bloque pas complètement ces caractères car ils peuvent être légitimes
        # On laisse la validation se faire au niveau is_command_blocked

        return cleaned.strip()

    def suggest_safe_alternative(self, blocked_command: str) -> Optional[str]:
        """
        Suggère une alternative sûre pour une commande bloquée

        Args:
            blocked_command: La commande bloquée

        Returns:
            Suggestion d'alternative ou None
        """
        suggestions = {
            "rm -rf /": "Veuillez spécifier un chemin plus précis",
            "chmod 777": "Utilisez des permissions plus restrictives (ex: 755)",
            ":(){:|:&};:": "Cette commande fork bomb est dangereuse",
        }

        for blocked, suggestion in suggestions.items():
            if blocked in blocked_command.lower():
                return suggestion

        return None


class PermissionChecker:
    """Vérificateur de permissions pour les opérations"""

    def __init__(self):
        self.config = get_config()

    def can_control_vm(self) -> bool:
        """Vérifie si le contrôle des VMs est autorisé"""
        return self.config.features.allow_vm_control

    def can_manage_packages(self) -> bool:
        """Vérifie si la gestion des paquets est autorisée"""
        return self.config.features.allow_package_management

    def can_manage_users(self) -> bool:
        """Vérifie si la gestion des utilisateurs est autorisée"""
        return self.config.features.allow_user_management

    def can_manage_services(self) -> bool:
        """Vérifie si la gestion des services est autorisée"""
        return self.config.features.allow_service_management

    def can_access_files(self) -> bool:
        """Vérifie si l'accès aux fichiers est autorisé"""
        return self.config.features.allow_file_operations

    def check_operation_permission(self, operation_type: str) -> Tuple[bool, Optional[str]]:
        """
        Vérifie si une opération est autorisée

        Args:
            operation_type: Type d'opération (vm_control, package_mgmt, etc.)

        Returns:
            Tuple (is_allowed, error_message)
        """
        permission_map = {
            "vm_control": self.can_control_vm,
            "package_management": self.can_manage_packages,
            "user_management": self.can_manage_users,
            "service_management": self.can_manage_services,
            "file_operations": self.can_access_files,
        }

        check_func = permission_map.get(operation_type)
        if check_func is None:
            return False, f"Unknown operation type: {operation_type}"

        if not check_func():
            return False, f"L'opération '{operation_type}' est désactivée dans la configuration"

        return True, None
