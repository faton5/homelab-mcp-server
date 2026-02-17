# Tests du serveur MCP Homelab

## 📊 Résumé des modifications

### ✅ Code vérifié
- **proxmox.py** : 30 méthodes (11 originales + 19 nouvelles)
- **tools.py** : 32 outils MCP avec handlers
- **Syntaxe Python** : ✓ Tous les fichiers compilent sans erreur

### 🆕 Nouveaux outils ajoutés (21)

#### Gestion des VMs
1. `create_vm` - Créer une nouvelle VM
2. `clone_vm` - Cloner une VM existante
3. `delete_vm` - Supprimer une VM (⚠️ confirmation requise)
4. `modify_vm_config` - Modifier la configuration d'une VM

#### Snapshots
5. `create_snapshot` - Créer un snapshot
6. `list_snapshots` - Lister les snapshots
7. `restore_snapshot` - Restaurer un snapshot
8. `delete_snapshot` - Supprimer un snapshot (⚠️ confirmation requise)

#### Backups
9. `list_backups` - Lister les backups disponibles
10. `create_backup` - Créer un backup

#### Stockage & Disques
11. `list_storage` - Lister les storages avec utilisation
12. `add_disk` - Ajouter un disque à une VM
13. `remove_disk` - Retirer un disque d'une VM
14. `resize_disk` - Redimensionner un disque

#### Migration
15. `migrate_vm` - Migrer une VM vers un autre node

#### Services (systemd)
16. `manage_service` - Gérer un service (start/stop/restart/enable/disable/status)
17. `list_services` - Lister tous les services

#### Fichiers
18. `read_file` - Lire un fichier sur une VM
19. `write_file` - Écrire dans un fichier (⚠️ confirmation requise)

#### Processus
20. `list_processes` - Lister les processus (top 20 par RAM)
21. `kill_process` - Tuer un processus (⚠️ confirmation requise)

## 🧪 Plan de test

### 1. Rebuild du conteneur Docker

```bash
cd /path/to/infra-manager-mcp
docker compose down
docker compose build --no-cache
docker compose up -d
```

### 2. Vérifier le démarrage

```bash
docker logs infra-manager-mcp
```

**Résultats attendus :**
```
Loading configuration...
Configuration loaded: infra-manager v1.0.0
MCP Server created
Registering MCP tools...
Tools registered successfully
SSE server listening on 0.0.0.0:10850
```

### 3. Tester la connexion depuis Claude Desktop

Redémarrer Claude Desktop (Ctrl+R / Cmd+R) et vérifier que le serveur MCP "homelab" apparaît dans la liste des outils disponibles.

### 4. Tests basiques recommandés

#### Test 1: Lister les VMs
```
"Liste toutes mes VMs Proxmox"
```

#### Test 2: Status d'une VM
```
"Quel est le status de la VM [NOM_VM] ?"
```

#### Test 3: Lister les snapshots
```
"Liste les snapshots de la VM [NOM_VM]"
```

#### Test 4: Lister les backups
```
"Liste les backups disponibles sur le node [NODE]"
```

#### Test 5: Lister les storages
```
"Montre-moi tous les storages disponibles"
```

#### Test 6: Informations système
```
"Donne-moi les infos système de la VM [NOM_VM]"
```

#### Test 7: Lister les services (nécessite qemu-guest-agent ou SSH)
```
"Liste les services sur la VM [NOM_VM]"
```

#### Test 8: Lire un fichier
```
"Lis le fichier /etc/os-release sur la VM [NOM_VM]"
```

### 5. Tests avancés (optionnels)

#### Créer un snapshot
```
"Crée un snapshot nommé 'test-snapshot' sur la VM [NOM_VM]"
```

#### Cloner une VM
```
"Clone la VM [NOM_VM] vers une nouvelle VM nommée [NOM_CLONE]"
```

#### Migration
```
"Migre la VM [NOM_VM] du node [NODE1] vers [NODE2]"
```

## ⚠️ Sécurité

Les actions suivantes nécessitent une **confirmation explicite** :
- Arrêt/redémarrage de VM
- Suppression de VM
- Suppression de snapshot
- Installation de mises à jour
- Écriture dans un fichier
- Kill d'un processus
- Migration de VM

## 🐛 Dépannage

### Le serveur ne démarre pas
```bash
docker logs infra-manager-mcp --tail 50
```

Vérifier :
- Les variables d'environnement Proxmox dans `docker-compose.yml`
- La connectivité réseau vers Proxmox
- Les permissions du token API

### "Command execution failed"
- **Via API** : Installer `qemu-guest-agent` dans la VM
- **Via SSH** : Configurer l'accès SSH dans `config.yaml`

### Tools MCP non visibles dans Claude
1. Vérifier que le conteneur est running : `docker ps`
2. Vérifier la config : `~/.config/claude/claude_desktop_config.json`
3. Redémarrer Claude Desktop (Ctrl+R)

## 📝 Notes

- **Total : 32 outils MCP** disponibles
- **Mode SSE** : Accès distant via HTTP sur port 10850
- **Auto-détection** : Les VMs sont découvertes automatiquement depuis Proxmox
- **Support multi-plateforme** : Base extensible pour VMware, Docker, etc. (à venir)

## ✅ Checklist avant push

- [x] Code ajouté dans proxmox.py (30 méthodes)
- [x] Tools définis dans tools.py (32 outils)
- [x] Handlers implémentés dans tools.py
- [x] Syntaxe Python validée
- [ ] Docker rebuild et test
- [ ] Test de base (list_vms, get_vm_status)
- [ ] Commit et push vers GitHub

---

**Date de création** : 2026-02-17
**Version** : v1.0.0 avec 32 outils MCP
