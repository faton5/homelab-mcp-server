FROM python:3.11-slim

# Installer les dépendances système
RUN apt-get update && apt-get install -y \
    openssh-client \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Créer le répertoire de travail
WORKDIR /app

# Copier les fichiers de dépendances et README
COPY requirements.txt pyproject.toml README.md ./

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code source AVANT d'installer le package
COPY src/ ./src/

# Installer le package en mode éditable
RUN pip install --no-cache-dir -e .

# Créer les répertoires nécessaires
RUN mkdir -p /app/ssh_keys /var/log

# Définir les variables d'environnement
ENV PYTHONUNBUFFERED=1
ENV CONFIG_PATH=/app/config.yaml

# Exposer le port (si nécessaire pour SSE)
EXPOSE 8080

# Point d'entrée : garder le container actif
# Le serveur MCP sera lancé par Claude Desktop via docker exec
CMD ["tail", "-f", "/dev/null"]
