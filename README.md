
# Plateforme de ..

## Installation

1. **Installer les dépendances**
   ```bash
   composer update
   ```

2. **Mettre à jour le schéma de la base de données**
   ```bash
   php bin/console doctrine:schema:update --force
   ```

3. **Effacer le cache**
   ```bash
   php bin/console cache:clear
   ```

## Technologie

Le projet est développé en **PHP 8.2** avec le framework **Symfony**.

## Conception

La plateforme permet aux administrateurs de gérer l'ensemble des opérations VTC, incluant :

- Gestion des chauffeurs
- Gestion des véhicules
- Gestion des demandeurs de service
## Diagramme de Cas d'Utilisation

