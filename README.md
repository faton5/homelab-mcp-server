# Homelab MCP Server

[![Build](https://github.com/faton5/homelab-mcp-server/actions/workflows/docker-build.yml/badge.svg)](https://github.com/faton5/homelab-mcp-server/actions/workflows/docker-build.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docker](https://img.shields.io/badge/ghcr.io-faton5%2Fhomelab--mcp--server-blue)](https://ghcr.io/faton5/homelab-mcp-server)

Serveur MCP extensible pour gérer votre homelab directement depuis Claude AI. Contrôlez vos VMs, snapshots, services et fichiers en langage naturel.

**Proxmox VE** est entièrement supporté · VMware, Docker et d'autres plateformes sont prévus.

---

## ⚡ Installation en 3 étapes

### 1. Téléchargez le docker-compose.yml

```bash
curl -O https://raw.githubusercontent.com/faton5/homelab-mcp-server/master/docker-compose.yml
```

### 2. Remplissez vos 4 valeurs

Ouvrez `docker-compose.yml` et modifiez uniquement les lignes marquées `✏️` :

```yaml
- PROXMOX_HOST=192.168.1.10          # ✏️ IP de votre Proxmox
- PROXMOX_PORT=8006                   # ✏️ Port (8006 par défaut)
- PROXMOX_TOKEN_ID=root@pam!mcp       # ✏️ Token ID
- PROXMOX_TOKEN_SECRET=xxxx-xxxx      # ✏️ Secret du token
```

> **Créer un token Proxmox** : Datacenter → API Tokens → Add

### 3. Lancez le serveur

```bash
docker compose up -d
```

L'image est téléchargée automatiquement depuis GitHub Container Registry. ✅

---

## 🔌 Connecter Claude

Ajoutez ceci à votre config Claude Desktop (`~/.config/claude/claude_desktop_config.json`) :

```json
{
  "mcpServers": {
    "homelab": {
      "url": "http://VOTRE_IP_DOCKER:10850/sse"
    }
  }
}
```

Remplacez `VOTRE_IP_DOCKER` par l'IP du serveur qui fait tourner Docker, puis redémarrez Claude (**Ctrl+R**).

<details>
<summary>Autres clients MCP (Claude Code, Codeium, Gemini…)</summary>

**Claude Code**
```bash
claude mcp add homelab http://VOTRE_IP_DOCKER:10850/sse
```

**Codeium / Gemini / autres**
```
URL SSE : http://VOTRE_IP_DOCKER:10850/sse
```
</details>

---

## 🛠️ Outils disponibles (32)

| Catégorie | Outils |
|-----------|--------|
| **VMs & Conteneurs** | `list_vms`, `list_nodes`, `list_servers`, `get_vm_status`, `start_vm`, `stop_vm`⚠️, `restart_vm`⚠️ |
| **Gestion VMs** | `create_vm`, `clone_vm`, `delete_vm`⚠️, `modify_vm_config` |
| **Snapshots** | `create_snapshot`, `list_snapshots`, `restore_snapshot`, `delete_snapshot`⚠️ |
| **Backups** | `list_backups`, `create_backup` |
| **Stockage & Disques** | `list_storage`, `add_disk`, `remove_disk`⚠️, `resize_disk` |
| **Migration** | `migrate_vm`⚠️ |
| **Système** | `execute_command`, `get_system_info`, `check_updates`, `install_updates`⚠️ |
| **Services** | `manage_service`, `list_services` |
| **Fichiers** | `read_file`, `write_file`⚠️ |
| **Processus** | `list_processes`, `kill_process`⚠️ |

⚠️ = demande une confirmation explicite avant exécution

---

## 💬 Exemples d'utilisation

```
"Liste toutes mes VMs Proxmox"
"Quel est le statut de HLB-VPN-01 ?"
"Crée un snapshot de HLB-NAS-01 nommé avant-migration"
"Augmente la RAM de HLB-DOCKER-01 à 8 Go"
"Montre les 20 processus qui consomment le plus de RAM sur HLB-NC-01"
"Redémarre le service nginx sur HLB-HA-01"
"Liste les backups disponibles sur le node PROXMOX"
```

---

## 🔍 Dépannage

**VMs non détectées** → Vérifiez l'IP Proxmox et les permissions du token API.

**Exécution de commandes impossible** → Installez `qemu-guest-agent` dans vos VMs.

**MCP non visible dans Claude** → Vérifiez que le container tourne (`docker ps`), puis redémarrez Claude (Ctrl+R).

**Logs du serveur** :
```bash
docker logs infra-manager-mcp
```

---

## 🤝 Contribuer

Pull requests et issues bienvenus ! Priorités : support VMware, Docker, équipements réseau.

## 📄 Licence

MIT — voir [LICENSE](LICENSE)

---

*Built with [MCP](https://modelcontextprotocol.io/) · Powered by [proxmoxer](https://github.com/proxmoxer/proxmoxer) · For [Claude AI](https://claude.ai/)*
