---
name: backup-and-recovery
description: "Sauvegarder une liste explicite et tester sa lecture."
version: 0.1.0
author: "Contributeurs du toolkit, Hermes Agent"
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [portable, audit, safety]
    related_skills: []
---

# backup-and-recovery

Workflow portable à portée explicite ; lecture et validation avant toute modification.

## When to Use
- Sauvegarde de fichiers choisis et test de restauration isolé.
- Ne pas utiliser pour restaurer une production, copier des secrets ou valider une machine entière.

## Prerequisites
Python 3.10+ ; dossier source explicitement autorisé, destination nouvelle hors source, espace libre. Le script [scripts/backup.py](scripts/backup.py) est autonome ; aucune dépendance réseau.

## How to Run
Via `terminal` : `python3 <skill-dir>/scripts/backup.py create --source <source> --archive <new-archive.tar.gz> --include <relative-file>` ; répéter `--include` pour chaque fichier.
Puis `python3 <skill-dir>/scripts/backup.py restore-check --archive <archive.tar.gz>`.

## Procedure
1. Inventorier et approuver la liste des fichiers ; exclure secrets, authentification et historique sensible. Ne jamais inclure tout un profil implicitement.
2. Utiliser d'abord des fixtures dans un dossier temporaire. La création refuse les symlinks, chemins dangereux et destinations existantes.
3. Créer l'archive ; SQLite `.db` utilise une sauvegarde en ligne et `integrity_check`. Les fichiers ordinaires peuvent changer pendant la lecture : pas de snapshot global atomique.
4. Vérifier hashes, tailles, membres réguliers et intégrité SQLite ; materialisation dans un nouveau dossier temporaire uniquement, jamais dans la source.
5. Rapporter les fichiers vérifiés. Aucun prune, rotation, upload ou restauration réelle automatique.

## Pitfalls
La liste de noms interdits ne détecte pas un secret dans un contenu : sélection manuelle obligatoire. Archive privée, NON chiffrée ; ne pas la publier. Limite 64 MiB de données, manifeste limité par l'enveloppe ; pas de sauvegarde volumineuse. Les permissions POSIX ne prouvent pas une ACL sûre sous Windows. La lecture d'une archive ne prouve pas le redémarrage applicatif ni une restauration hors site.

## Verification
Le JSON doit porter `verified: true` ; le restore-check indique `production_restored: false`. En cas d'échec, code 2. Tester corruption, traversal, liens, SQLite et refus d'écrasement avant tout usage réel.
