# Configuration Proxmox pour Infrastructure Manager MCP

Ce guide vous explique comment configurer Proxmox pour utiliser le serveur MCP.

## 1. Créer un Token API Proxmox

### Via l'interface web Proxmox

1. Connectez-vous à votre interface Proxmox (https://votre-proxmox:8006)
2. Allez dans **Datacenter > Permissions > API Tokens**
3. Cliquez sur **Add**
4. Remplissez les informations :
   - **User**: `root@pam` (ou un autre utilisateur avec permissions)
   - **Token ID**: `mytoken` (choisissez un nom)
   - **Privilege Separation**: Décochez si vous voulez que le token ait les mêmes permissions que l'utilisateur
5. Cliquez sur **Add**
6. **IMPORTANT**: Copiez le **Token Secret** affiché - il ne sera plus visible après !

Votre `token_id` sera : `root@pam!mytoken`
Votre `token_secret` sera la valeur affichée (ex: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`)

### Via la ligne de commande (sur le serveur Proxmox)

```bash
pveum user token add root@pam mytoken --privsep 0
```

## 2. Configuration des permissions

Si vous avez créé un utilisateur dédié (recommandé pour la production), donnez-lui les permissions nécessaires :

```bash
# Créer un utilisateur dédié
pveum user add automation@pam

# Créer un rôle personnalisé avec les permissions nécessaires
pveum role add AutomationRole \
  -privs "VM.Audit VM.Monitor VM.PowerMgmt VM.Console VM.Config.Disk VM.Config.Memory VM.Config.CPU VM.Config.Network Sys.Audit Sys.Console Datastore.Audit"

# Assigner le rôle à l'utilisateur sur tout le datacenter
pveum acl modify / -user automation@pam -role AutomationRole

# Créer le token pour cet utilisateur
pveum user token add automation@pam mytoken --privsep 0
```

## 3. Installer qemu-guest-agent dans vos VMs

Pour pouvoir exécuter des commandes via l'API Proxmox, vous devez installer `qemu-guest-agent` dans vos VMs :

### Ubuntu/Debian

```bash
apt update
apt install qemu-guest-agent
systemctl start qemu-guest-agent
systemctl enable qemu-guest-agent
```

### CentOS/RHEL/Rocky

```bash
yum install qemu-guest-agent
systemctl start qemu-guest-agent
systemctl enable qemu-guest-agent
```

### Dans Proxmox, activez l'agent pour la VM

Via l'interface web :
1. Sélectionnez votre VM
2. Options > QEMU Guest Agent
3. Cochez "Use QEMU Guest Agent"
4. Redémarrez la VM

Via CLI :
```bash
qm set <VMID> --agent enabled=1
```

## 4. Configuration du MCP

Éditez votre `config.yaml` :

```yaml
proxmox:
  host: "proxmox.example.com"  # Adresse de votre Proxmox
  port: 8006
  token_id: "root@pam!mytoken"  # Votre token ID
  token_secret: "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"  # Votre token secret
  verify_ssl: false  # Mettez true si vous avez un certificat SSL valide
  timeout: 30
```

## 5. Tester la connexion

Une fois le MCP lancé, testez la connexion :

```bash
# Via Claude Desktop ou votre client MCP, demandez :
"Liste-moi tous mes serveurs Proxmox"
```

Ou testez directement avec Python :

```python
from proxmoxer import ProxmoxAPI

proxmox = ProxmoxAPI(
    'proxmox.example.com',
    port=8006,
    token_name='mytoken',
    token_value='xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx',
    verify_ssl=False
)

# Tester
print(proxmox.nodes.get())
print(proxmox.cluster.resources.get())
```

## Troubleshooting

### Erreur d'authentification

- Vérifiez que le token_id est au format `user@realm!tokenname`
- Vérifiez que le token_secret est correct
- Vérifiez que l'utilisateur a les permissions nécessaires

### Impossible d'exécuter des commandes

- Vérifiez que qemu-guest-agent est installé et actif dans la VM
- Vérifiez que l'agent est activé dans la configuration Proxmox de la VM
- Redémarrez la VM après avoir activé l'agent

### Certificat SSL invalide

Si vous utilisez un certificat auto-signé :
```yaml
proxmox:
  verify_ssl: false
```

Pour une meilleure sécurité, installez un certificat valide ou importez le certificat auto-signé.

## Sécurité

### Production

Pour la production, il est recommandé de :
1. Créer un utilisateur dédié (pas root)
2. Donner uniquement les permissions nécessaires
3. Utiliser un certificat SSL valide
4. Restreindre l'accès réseau au serveur MCP
5. Utiliser des secrets management (pas de tokens en clair)

### Renouvellement des tokens

Les tokens Proxmox n'expirent pas par défaut, mais vous pouvez les régénérer régulièrement :

```bash
pveum user token remove root@pam mytoken
pveum user token add root@pam mytoken --privsep 0
```

N'oubliez pas de mettre à jour votre `config.yaml` !
