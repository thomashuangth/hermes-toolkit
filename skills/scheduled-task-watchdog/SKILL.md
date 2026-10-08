---
name: scheduled-task-watchdog
description: "Détecter les tâches échouées ou devenues anciennes."
version: 0.1.0
author: "Contributeurs du toolkit, Hermes Agent"
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [portable, audit, safety]
    related_skills: []
---

# scheduled-task-watchdog

Workflow portable à portée explicite ; lecture et validation avant toute modification.

## When to Use
- Contrôler des reçus de tâches sans créer de planification.
- Ne pas utiliser comme adaptateur automatique des fichiers internes Hermes.

## Prerequisites
Python 3.10+ ; export normalisé local, sans prompts ni erreurs brutes. Schéma : liste d'objets `id` (alias anonymisé unique), `enabled` (bool), `status`, `last_success` (epoch UTC ou null), `max_age_seconds` (>0).

## How to Run
Via `terminal`, appeler `python3 <skill-dir>/scripts/watchdog.py --input <receipts.json> --self-id <alias>`. Le script [scripts/watchdog.py](scripts/watchdog.py) lit seulement le fichier explicitement fourni.

## Procedure
1. Découvrir les tâches et le schéma de reçus de la version installée en lecture seule.
2. Normaliser les reçus dans un dossier temporaire ; choisir les seuils d'après cadence et marge autorisées.
3. Exécuter le script ; code 0 sain (stdout vide), 1 anomalies JSON, 2 entrée invalide.
4. Écarter soi-même, les tâches désactivées et terminées ; contrôler les horodatages futurs.
5. Rapporter les anomalies sans envoyer de message, réparer, écrire d'état ou installer de cron.

## Pitfalls
Ce script n'observe pas un ordonnanceur directement et ne détecte pas les transitions. Une absence de succès n'est pas une preuve de panne ; vérifier la date de création.

## Verification
Tester données saines, anciennes, jamais exécutées, futures et invalides. Une réparation éventuelle exige autorisation et lecture de contrôle séparées.
