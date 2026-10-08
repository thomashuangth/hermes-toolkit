---
name: runtime-config-audit
description: "Vérifier la configuration réellement utilisée."
version: 0.1.0
author: "Contributeurs du toolkit, Hermes Agent"
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [portable, audit, safety]
    related_skills: []
---

# runtime-config-audit

Workflow portable à portée explicite ; lecture et validation avant toute modification.

## When to Use
- Vérifier modèle, fournisseur, effort ou surcharge d'une session.
- Ne pas utiliser pour appliquer automatiquement un réglage.

## Prerequisites
Découvrir le profil actif et `HERMES_HOME` sans afficher l'environnement complet. Utiliser `terminal(command="hermes config --help")` et la documentation officielle correspondant à la version installée.

## Procedure
1. Identifier profil, processus et surface ciblés ; distinguer CLI et passerelle vivante.
2. Lire uniquement les clés utiles avec la CLI supportée. Ne pas lire ni afficher fichiers de secrets.
3. Comparer défaut persistant, surcharge de session, route réellement servie et éventuel fallback ; marquer les champs non observables comme inconnus.
4. Vérifier les valeurs dans le processus cible si des reçus existent ; un reçu CLI ne prouve pas l'état du démon.
5. Proposer une commande supportée si nécessaire ; aucune édition manuelle de configuration ni redémarrage sans accord.

## Pitfalls
Mémoire, ancien message, configuration disque et état en mémoire ne sont pas interchangeables. Ne pas modifier un autre profil.

## Verification
Présenter valeur, portée et preuve datée pour chaque clé ; dire explicitement ce qui reste non vérifié.
