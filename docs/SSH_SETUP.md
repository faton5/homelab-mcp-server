# Configuration SSH pour Infrastructure Manager MCP

Ce guide vous explique comment configurer l'accès SSH pour vos serveurs.

## 1. Générer une paire de clés SSH

Sur votre machine (ou serveur où tourne le MCP) :

```bash
# Générer une nouvelle clé SSH (si vous n'en avez pas)
ssh-keygen -t ed25519 -C "infra-manager-mcp" -f ./ssh_keys/id_rsa

# Ou RSA si ed25519 n'est pas supporté
ssh-keygen -t rsa -b 4096 -C "infra-manager-mcp" -f ./ssh_keys/id_rsa
```

Cela créera deux fichiers :
- `ssh_keys/id_rsa` : Clé privée (à garder secrète)
- `ssh_keys/id_rsa.pub` : Clé publique (à copier sur les serveurs)

## 2. Copier la clé publique sur vos serveurs

### Méthode 1 : Avec ssh-copy-id

```bash
ssh-copy-id -i ./ssh_keys/id_rsa.pub root@votre-serveur
```

### Méthode 2 : Manuellement

Sur chaque serveur cible :

```bash
# Sur le serveur
mkdir -p ~/.ssh
chmod 700 ~/.ssh

# Ajouter votre clé publique
cat >> ~/.ssh/authorized_keys << 'EOF'
<contenu de votre id_rsa.pub>
EOF

chmod 600 ~/.ssh/authorized_keys
```

## 3. Tester la connexion SSH

```bash
ssh -i ./ssh_keys/id_rsa root@votre-serveur
```

Si ça fonctionne sans demander de mot de passe, c'est bon ! 🎉

## 4. Configuration dans le MCP

### Option 1 : Clés SSH dans le container Docker

Montez vos clés SSH dans le container :

```yaml
# docker-compose.yml
volumes:
  - ./ssh_keys:/app/ssh_keys:ro  # :ro = read-only pour sécurité
```

Configuration dans `config.yaml` :

```yaml
ssh:
  enabled: true
  key_path: "/app/ssh_keys/id_rsa"
  default_user: "root"
  timeout: 30
  port: 22
```

### Option 2 : SSH via l'API Proxmox uniquement

Si vous ne voulez pas gérer SSH directement, désactivez-le :

```yaml
ssh:
  enabled: false
```

Le MCP utilisera uniquement l'API Proxmox (nécessite qemu-guest-agent dans les VMs).

## 5. Configuration par serveur

Vous pouvez configurer SSH différemment pour chaque serveur :

```yaml
servers:
  - name: "HLB"
    type: "proxmox-vm"
    vmid: 100
    ssh_enabled: true
    ssh_host: "192.168.1.100"
    ssh_user: "admin"        # Utilisateur spécifique
    ssh_port: 2222           # Port SSH personnalisé

  - name: "Thierry01"
    type: "proxmox-vm"
    vmid: 101
    ssh_enabled: true
    ssh_host: "10.0.0.50"    # IP différente du réseau Proxmox
    ssh_user: "root"

  - name: "External-Server"
    type: "ssh-only"         # Serveur non-Proxmox
    ssh_enabled: true
    ssh_host: "external.example.com"
    ssh_user: "ubuntu"
```

## 6. Sécurité SSH

### Sur vos serveurs

Éditez `/etc/ssh/sshd_config` :

```bash
# Désactiver l'authentification par mot de passe (clés uniquement)
PasswordAuthentication no

# Désactiver root login si vous utilisez un autre utilisateur
PermitRootLogin prohibit-password  # ou "no"

# Désactiver l'authentification keyboard-interactive
ChallengeResponseAuthentication no

# Limiter les utilisateurs autorisés
AllowUsers admin automation

# Changer le port SSH (optionnel mais recommandé)
Port 2222
```

Redémarrez SSH :
```bash
systemctl restart sshd
```

### Permissions des fichiers

Les clés SSH doivent avoir les bonnes permissions :

```bash
chmod 700 ssh_keys/
chmod 600 ssh_keys/id_rsa      # Clé privée
chmod 644 ssh_keys/id_rsa.pub  # Clé publique
```

## 7. Utiliser sudo sans mot de passe

Pour que le MCP puisse exécuter des commandes sudo, configurez sudoers :

```bash
# Sur le serveur cible
visudo
```

Ajoutez :
```
# Pour l'utilisateur root (si vous utilisez root)
root ALL=(ALL) NOPASSWD: ALL

# Ou pour un utilisateur spécifique
automation ALL=(ALL) NOPASSWD: ALL
```

**Attention**: C'est pratique mais réduit la sécurité. Pour plus de sécurité, limitez les commandes autorisées :

```
automation ALL=(ALL) NOPASSWD: /usr/bin/apt, /usr/bin/systemctl, /usr/bin/reboot
```

## 8. Troubleshooting

### Permission denied (publickey)

- Vérifiez que la clé publique est dans `~/.ssh/authorized_keys` du serveur
- Vérifiez les permissions (600 pour authorized_keys, 700 pour .ssh)
- Vérifiez que PasswordAuthentication est bien à "no" ou "yes" selon votre config

### Connection timeout

- Vérifiez que le serveur est accessible (ping)
- Vérifiez le port SSH (22 par défaut)
- Vérifiez le firewall (autoriser le port SSH)

### Host key verification failed

Première connexion ? Ajoutez la clé :
```bash
ssh-keyscan -H votre-serveur >> ~/.ssh/known_hosts
```

Ou dans le container :
```bash
docker exec -it infra-manager-mcp ssh-keyscan -H votre-serveur >> /root/.ssh/known_hosts
```

## 9. Mode hybride (API + SSH)

Le mode recommandé est hybride :

```yaml
ssh:
  enabled: true  # SSH disponible comme fallback

servers:
  - name: "HLB"
    type: "proxmox-vm"
    vmid: 100
    node: "proxmox"
    ssh_enabled: true        # Peut utiliser SSH ou API
    ssh_host: "192.168.1.100"
```

Le MCP essaiera :
1. **SSH en premier** (plus fiable, plus de contrôle)
2. **API Proxmox en fallback** (si SSH échoue et qemu-guest-agent disponible)

Vous pouvez inverser cet ordre dans le code si préféré.

## Bonnes pratiques

1. **Utilisez des clés SSH**, jamais de mots de passe
2. **Un utilisateur dédié** (pas root) avec sudo limité
3. **Port SSH personnalisé** pour réduire les scans automatiques
4. **fail2ban** pour bloquer les tentatives de brute force
5. **Rotation des clés** régulière (tous les 6-12 mois)
6. **Monitoring** des connexions SSH (`/var/log/auth.log`)
