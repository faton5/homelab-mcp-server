.PHONY: help build up down restart logs shell test clean install dev

help: ## Affiche cette aide
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

build: ## Construit l'image Docker
	docker-compose build

up: ## Démarre le serveur MCP
	docker-compose up -d

down: ## Arrête le serveur MCP
	docker-compose down

restart: ## Redémarre le serveur MCP
	docker-compose restart

logs: ## Affiche les logs en temps réel
	docker-compose logs -f

shell: ## Ouvre un shell dans le container
	docker exec -it infra-manager-mcp bash

test: ## Lance les tests (à implémenter)
	@echo "Tests not implemented yet"

clean: ## Nettoie les containers et volumes
	docker-compose down -v
	rm -rf logs/*.log

install: ## Installation initiale (copie config.example.yaml)
	@if [ ! -f config.yaml ]; then \
		cp config.example.yaml config.yaml; \
		echo "✅ config.yaml créé depuis config.example.yaml"; \
		echo "⚠️  N'oubliez pas de l'éditer avec vos informations Proxmox !"; \
	else \
		echo "⚠️  config.yaml existe déjà, pas de modification"; \
	fi
	@mkdir -p ssh_keys logs
	@chmod 700 ssh_keys
	@echo "✅ Répertoires créés"

dev: ## Mode développement (monte le code source)
	docker-compose up

status: ## Affiche le statut du serveur
	docker-compose ps

stop: ## Arrête le serveur
	docker-compose stop

start: ## Démarre le serveur (si déjà créé)
	docker-compose start

update: ## Met à jour et redémarre
	git pull
	docker-compose up -d --build

backup-config: ## Sauvegarde la configuration
	@mkdir -p backups
	@cp config.yaml backups/config-$(shell date +%Y%m%d-%H%M%S).yaml
	@echo "✅ Configuration sauvegardée dans backups/"

ssh-keygen: ## Génère une paire de clés SSH
	@mkdir -p ssh_keys
	ssh-keygen -t ed25519 -C "infra-manager-mcp" -f ./ssh_keys/id_rsa
	@chmod 600 ssh_keys/id_rsa
	@chmod 644 ssh_keys/id_rsa.pub
	@echo "✅ Clés SSH générées dans ssh_keys/"
	@echo "📋 Clé publique :"
	@cat ssh_keys/id_rsa.pub
