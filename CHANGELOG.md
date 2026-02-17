# Changelog

Toutes les modifications notables de ce projet seront documentées dans ce fichier.

Le format est basé sur [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/),
et ce projet adhère à [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-02-17

### Ajouté
- 🎉 Version initiale du serveur MCP Infrastructure Manager
- Support complet de l'API Proxmox (VMs, conteneurs, nodes)
- Exécution de commandes via SSH et API Proxmox (hybride)
- Système de restrictions et permissions configurables
- Outils MCP pour :
  - Lister les serveurs, nodes, VMs
  - Obtenir le statut des VMs
  - Démarrer/arrêter/redémarrer les VMs
  - Exécuter des commandes sur les serveurs
  - Obtenir les informations système (CPU, RAM, disque, load)
  - Vérifier et installer les mises à jour
- Configuration YAML flexible
- Déploiement Docker avec docker-compose
- Documentation complète (README, guides de configuration)
- Système de validation des commandes dangereuses
- Demande de confirmation pour les actions critiques
- Support multi-serveurs
- Client SSH avec gestion de connexions persistantes
- Client Proxmox API avec authentification par token

### Documentation
- README complet avec exemples
- Guide de configuration Proxmox
- Guide de configuration SSH
- Guide de démarrage rapide
- Exemples de configuration

## [À venir]

### En cours de réflexion pour v1.1.0
- [ ] Support des snapshots Proxmox
- [ ] Gestion des backups
- [ ] Monitoring et alertes
- [ ] Support de Terraform/Ansible
- [ ] Interface web de monitoring (optionnelle)
- [ ] Support de plusieurs clusters Proxmox
- [ ] Gestion des templates et clones
- [ ] Scripts de migration de VMs
- [ ] Intégration avec d'autres outils (Grafana, Prometheus)
- [ ] Support des conteneurs Docker sur les VMs

### Idées pour le futur
- Support d'autres hyperviseurs (VMware, Hyper-V)
- Gestion du réseau (VLANs, firewall)
- Automatisation de déploiements
- Gestion de configurations (Ansible playbooks)
- Interface CLI dédiée
- API REST pour accès externe
- Dashboard web
- Multi-tenant support

---

## Types de changements

- `Ajouté` : Nouvelles fonctionnalités
- `Modifié` : Changements dans les fonctionnalités existantes
- `Déprécié` : Fonctionnalités qui seront supprimées prochainement
- `Supprimé` : Fonctionnalités supprimées
- `Corrigé` : Corrections de bugs
- `Sécurité` : Changements de sécurité
