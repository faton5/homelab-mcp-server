# Installation sur Windows

Guide spécifique pour installer et utiliser Infrastructure Manager MCP sur Windows.

## Prérequis

### 1. Installer Docker Desktop

1. Téléchargez Docker Desktop : https://www.docker.com/products/docker-desktop
2. Installez-le (il va redémarrer votre PC)
3. Lancez Docker Desktop depuis le menu Démarrer
4. Attendez que Docker soit complètement démarré (icône verte)

### 2. Vérifier l'installation

Ouvrez **PowerShell** (pas CMD) et testez :

```powershell
docker --version
docker compose version
```

Si ça marche, c'est bon ! ✅

Si `docker compose` ne marche pas, essayez :
```powershell
docker-compose --version
```

## Installation rapide (5 minutes)

### Étape 1 : Télécharger le projet

Si vous avez Git :
```powershell
git clone <votre-repo>
cd infra-manager-mcp
```

Sinon, copiez simplement le dossier `infra-manager-mcp` sur votre PC.

### Étape 2 : Installation initiale

**Avec PowerShell (recommandé) :**
```powershell
.\manage.ps1 install
```

**Ou avec CMD :**
```cmd
manage.bat install
```

Cela créera :
- `config.yaml` (à partir du template)
- Les dossiers `ssh_keys/` et `logs/`

### Étape 3 : Configurer Proxmox

Éditez `config.yaml` avec votre éditeur préféré :

```powershell
notepad config.yaml
# ou
code config.yaml  # Si vous avez VS Code
```

**Minimum requis :**

```yaml
proxmox:
  host: "votre-proxmox.com"
  token_id: "root@pam!mytoken"
  token_secret: "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
```

Voir [PROXMOX_SETUP.md](PROXMOX_SETUP.md) pour créer le token.

### Étape 4 : Démarrer le serveur

**Avec PowerShell :**
```powershell
.\manage.ps1 up
```

**Ou avec CMD :**
```cmd
manage.bat up
```

Attendez quelques secondes, puis vérifiez les logs :

```powershell
.\manage.ps1 logs
# ou
manage.bat logs
```

Vous devriez voir :
```
Connected to Proxmox at ...
MCP Server created
Starting MCP server via stdio...
```

✅ Le serveur est lancé !

## Commandes disponibles

### PowerShell (recommandé)

```powershell
.\manage.ps1 help       # Affiche l'aide
.\manage.ps1 install    # Installation initiale
.\manage.ps1 up         # Démarrer
.\manage.ps1 down       # Arrêter
.\manage.ps1 restart    # Redémarrer
.\manage.ps1 logs       # Voir les logs
.\manage.ps1 status     # Statut du serveur
.\manage.ps1 check      # Vérifier Docker
```

### CMD

```cmd
manage.bat help
manage.bat install
manage.bat up
manage.bat down
manage.bat logs
manage.bat status
```

## Configuration Claude Desktop sur Windows

### Localisation du fichier de config

Le fichier de configuration Claude Desktop se trouve ici :
```
%APPDATA%\Claude\claude_desktop_config.json
```

Pour l'ouvrir rapidement :
```powershell
notepad $env:APPDATA\Claude\claude_desktop_config.json
```

### Configuration

Ajoutez cette configuration :

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

**Sauvegardez** et **redémarrez Claude Desktop**.

## Tester

Ouvrez Claude Desktop et dites :

```
Liste-moi tous mes serveurs Proxmox
```

Claude devrait vous répondre avec vos VMs ! 🎉

## Problèmes courants sur Windows

### "docker-compose n'est pas reconnu"

**Solution 1 - Docker Desktop moderne (recommandé) :**
```powershell
# Utilisez "docker compose" (SANS tiret)
docker compose up -d
```

**Solution 2 - Ancienne version :**
```powershell
# Utilisez "docker-compose" (AVEC tiret)
docker-compose up -d
```

**Solution 3 - Utiliser les scripts :**
```powershell
# Ils détectent automatiquement la bonne commande
.\manage.ps1 up
```

### "Cannot connect to Docker daemon"

Docker Desktop n'est pas lancé :
1. Ouvrez le menu Démarrer
2. Cherchez "Docker Desktop"
3. Lancez-le
4. Attendez que l'icône devienne verte
5. Réessayez

### "Permission denied" sur les fichiers

Sur Windows, pas besoin de `chmod`. Les permissions sont gérées différemment.

Si vous avez des problèmes avec les clés SSH :
```powershell
# Créer le dossier ssh_keys
mkdir ssh_keys

# Générer la clé
ssh-keygen -t ed25519 -C "infra-mcp" -f .\ssh_keys\id_rsa
```

### Les chemins avec espaces

Si votre dossier a des espaces dans le nom (ex: `C:\Mes Documents\infra-manager-mcp`), utilisez des guillemets :

```powershell
cd "C:\Mes Documents\infra-manager-mcp"
.\manage.ps1 up
```

### WSL2 vs Hyper-V

Docker Desktop sur Windows utilise soit WSL2, soit Hyper-V.

**WSL2 (recommandé, plus rapide) :**
- Plus performant
- Mieux intégré avec Windows 11

**Hyper-V (ancien) :**
- Fonctionne sur Windows 10 Pro/Enterprise
- Peut avoir des conflits avec VirtualBox

Dans les deux cas, ça marche !

### Firewall Windows

Si vous avez des problèmes de connexion :
1. Ouvrez "Pare-feu Windows"
2. Autorisez Docker Desktop
3. Autorisez les connexions localhost

## SSH sur Windows

Pour utiliser SSH depuis Windows :

### Option 1 : OpenSSH (intégré dans Windows 10/11)

OpenSSH est déjà installé dans Windows 10/11 moderne :

```powershell
# Vérifier
ssh -V

# Si pas installé, installer via Paramètres :
# Paramètres > Applications > Fonctionnalités facultatives
# Ajouter > Client OpenSSH
```

### Option 2 : PuTTY

Si vous préférez PuTTY :
1. Téléchargez : https://www.putty.org
2. Utilisez PuTTYgen pour générer les clés
3. Convertissez au format OpenSSH si nécessaire

### Générer une clé SSH sur Windows

```powershell
# Créer le dossier
mkdir ssh_keys

# Générer la clé
ssh-keygen -t ed25519 -C "infra-mcp" -f .\ssh_keys\id_rsa

# Afficher la clé publique (à copier sur vos serveurs)
Get-Content .\ssh_keys\id_rsa.pub
```

## Éditeurs de texte recommandés

Pour éditer `config.yaml` :

1. **VS Code** (gratuit, puissant) : https://code.visualstudio.com
2. **Notepad++** (léger, gratuit) : https://notepad-plus-plus.org
3. **Notepad** (intégré Windows, basique)

**N'utilisez PAS Word !** Word ajoute du formatage invisible.

## Logs et debugging

### Voir les logs en temps réel

```powershell
.\manage.ps1 logs
# Ctrl+C pour quitter
```

### Logs dans un fichier

Les logs sont aussi sauvegardés dans :
```
logs/infra-manager-mcp.log
```

Vous pouvez les ouvrir avec n'importe quel éditeur de texte.

### Entrer dans le container

Pour débugger directement :

```powershell
docker exec -it infra-manager-mcp bash
```

Cela ouvre un terminal Linux dans le container.

## Mise à jour

Pour mettre à jour le serveur MCP :

```powershell
# Si vous avez Git
git pull

# Reconstruire et redémarrer
.\manage.ps1 down
.\manage.ps1 up
```

## Performance sur Windows

Docker sur Windows est légèrement moins performant que sur Linux, mais ça reste très acceptable pour gérer votre infrastructure.

**Conseils :**
- Utilisez WSL2 plutôt qu'Hyper-V si possible
- Donnez assez de RAM à Docker (dans les paramètres Docker Desktop)
- Placez le projet sur votre disque principal (C:) pour de meilleures perfs

## Désinstallation

Pour tout supprimer :

```powershell
# Arrêter et supprimer
.\manage.ps1 down

# Supprimer les images Docker
docker rmi infra-manager-mcp

# Supprimer le dossier
cd ..
Remove-Item -Recurse -Force infra-manager-mcp
```

## Aide supplémentaire

- Documentation Docker Desktop Windows : https://docs.docker.com/desktop/windows/
- Configuration Proxmox : [PROXMOX_SETUP.md](PROXMOX_SETUP.md)
- Configuration SSH : [SSH_SETUP.md](SSH_SETUP.md)
- Guide rapide : [QUICK_START.md](QUICK_START.md)

Bon courage ! 🚀
