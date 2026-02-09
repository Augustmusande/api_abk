# API ABK - Coopérative ABK

Application Django REST Framework pour la gestion d'une coopérative financière.

## Fonctionnalités principales

- Gestion des membres et clients
- Gestion des crédits et remboursements
- Calcul des intérêts et frais de gestion
- Gestion de la caisse (multi-types de caisse)
- Génération de rapports et reçus
- Système de scoring pour les crédits

## Installation

1. Cloner le dépôt
2. Créer un environnement virtuel : `python -m venv .venv`
3. Activer l'environnement virtuel
4. Installer les dépendances : `pip install -r requirements.txt`
5. Configurer les variables d'environnement (créer un fichier `.env`)
6. Appliquer les migrations : `python manage.py migrate`
7. Créer un superutilisateur : `python manage.py createsuperuser`
8. Lancer le serveur : `python manage.py runserver`

## Technologies utilisées

- Django
- Django REST Framework
- PostgreSQL (recommandé) / SQLite (développement)
- ReportLab (génération de PDF)

## Structure du projet

- `caisse/` : Gestion de la caisse et calculs financiers
- `credits/` : Gestion des crédits et remboursements
- `membres/` : Gestion des membres et clients
- `rapports/` : Génération de rapports et reçus
- `users/` : Gestion des utilisateurs et authentification
