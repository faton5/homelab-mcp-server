# Démarrage Rapide - Infrastructure Manager MCP

Ce guide vous permet de lancer le serveur MCP en 5 minutes !

## Prérequis

- Docker et Docker Compose installés
- Accès à un serveur Proxmox
- Token API Proxmox (voir [PROXMOX_SETUP.md](PROXMOX_SETUP.md))

## Étape 1 : Configuration (2 min)

```bash
# 1. Copier le fichier de configuration
cp config.example.yaml config.yaml

# 2. Éditer avec vos informations Proxmox
nano config.yaml
# ou
vi config.yaml
```

**Minimum requis dans config.yaml :**

```yaml
proxmox:
  host: "VOTRE-PROXMOX.com"          # 👈 Changez ça
  token_id: "root@pam!mytoken"       # 👈 Votre token
  token_secret: "xxx-xxx-xxx"        # 👈 Votre secret
```

Le reste fonctionne avec les valeurs par défaut !

## Étape 2 : Lancer le serveur (1 min)

```bash
# Construire et démarrer le container
docker-compose up -d

# Vérifier que ça tourne
docker-compose logs -f
```

Vous devriez voir :
```
infra-manager-mcp | INFO - Connected to Proxmox at ...
infra-manager-mcp | INFO - MCP Server created
infra-manager-mcp | INFO - Starting MCP server via stdio...
```

✅ Le serveur MCP est lancé !

## Étape 3 : Connecter Claude Desktop (2 min)

Éditez votre configuration Claude Desktop :

**Sur macOS :**
```bash
nano ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

**Sur Windows :**
```bash
notepad %APPDATA%\Claude\claude_desktop_config.json
```

**Sur Linux :**
```bash
nano ~/.config/Claude/claude_desktop_config.json
```

**Ajoutez :**

```json
{
  "mcpServers": {
    "infra-manager": {
      "command": "docker",
      "args": [
        "exec",
        "-i",
        "infra-manager-mcp",
        "python",
        "-m",
        "infra_manager_mcp"
      ]
    }
  }
}
```

**Redémarrez Claude Desktop.**

## Étape 4 : Tester (1 min)

Ouvrez Claude Desktop et demandez :

```
Liste-moi tous mes serveurs Proxmox
```

Claude devrait vous répondre avec la liste de vos VMs ! 🎉

## Commandes utiles

```bash
# Voir les logs
docker-compose logs -f

# Redémarrer le serveur
docker-compose restart

# Arrêter le serveur
docker-compose down

# Mettre à jour le code
git pull
docker-compose up -d --build

# Entrer dans le container
docker exec -it infra-manager-mcp bash
```

## Exemples de commandes avec Claude

Une fois connecté :

```
Utilisateur : Liste tous mes serveurs et leur statut

Utilisateur : Vérifie s'il y a des mises à jour sur le serveur HLB

Utilisateur : Montre-moi les informations système de Thierry01

Utilisateur : Exécute "df -h" sur tous les serveurs pour voir l'espace disque

Utilisateur : Démarre la VM Affine

Utilisateur : Redémarre le service nginx sur HLB
```

## Problèmes courants

### "Configuration file not found"

```bash
# Vérifiez que config.yaml existe
ls -la config.yaml

# Copiez depuis l'exemple si besoin
cp config.example.yaml config.yaml
```

### "Proxmox authentication failed"

Vérifiez vos credentials dans `config.yaml` :
- Le `token_id` doit être au format `user@realm!tokenname`
- Le `token_secret` doit être correct
- Testez l'accès : https://votre-proxmox:8006

### "SSH connection failed"

SSH est optionnel ! Par défaut, le MCP utilise l'API Proxmox.

Pour activer SSH, voir [SSH_SETUP.md](SSH_SETUP.md).

### Claude Desktop ne voit pas le MCP

1. Vérifiez que le container tourne : `docker ps`
2. Vérifiez la config Claude Desktop (JSON valide ?)
3. Redémarrez Claude Desktop complètement
4. Vérifiez les logs : `docker-compose logs`

## Prochaines étapes

Une fois que ça marche :

1. **Configurez SSH** pour plus de contrôle → [SSH_SETUP.md](SSH_SETUP.md)
2. **Ajoutez vos serveurs** dans `config.yaml` :
   ```yaml
   servers:
     - name: "MonServeur"
       type: "proxmox-vm"
       vmid: 100
   ```
3. **Personnalisez les restrictions** pour plus de sécurité
4. **Explorez les outils** disponibles (voir README.md)

## Sécurité

⚠️ **Important** :
- Ne committez JAMAIS `config.yaml` (il contient vos secrets)
- Utilisez des tokens API dédiés (pas root en production)
- Activez SSL sur Proxmox (`verify_ssl: true`)
- Limitez l'accès réseau au container Docker

## Besoin d'aide ?

- Documentation complète : [README.md](../README.md)
- Configuration Proxmox : [PROXMOX_SETUP.md](PROXMOX_SETUP.md)
- Configuration SSH : [SSH_SETUP.md](SSH_SETUP.md)
- Logs : `docker-compose logs -f`

Bon amusement avec votre infrastructure automatisée ! 🚀
