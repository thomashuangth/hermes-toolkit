---
name: session-context-recovery
description: "Retrouver le contexte des réponses brèves."
version: 0.1.0
author: "Contributeurs du toolkit, Hermes Agent"
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [portable, audit, safety]
    related_skills: []
---

# session-context-recovery

Workflow portable à portée explicite ; lecture et validation avant toute modification.

## When to Use
- Réponse brève renvoyant à une option, décision ou alerte absente du fil actuel.
- Ne pas utiliser pour explorer sans motif l'historique privé.

## Prerequisites
Outil `session_search` disponible ; sinon demander l'extrait pertinent. Découvrir son schéma via les outils avant de l'appeler.

## Procedure
1. Chercher quelques sessions récentes avec les mots distinctifs ; conserver les identifiants réellement retournés.
2. Lire une fenêtre autour du message trouvé ; comparer canal, fil et chronologie. La proximité temporelle seule ne suffit pas.
3. Pour une alerte, découvrir les sorties de tâches du profil actif avec `search_files`, puis lire uniquement l'extrait pertinent avec `read_file`.
4. Si plusieurs candidats restent plausibles, poser une question courte avant toute action à effet de bord.
5. Re-mesurer toute affirmation de configuration ou chiffre devenu ancien avant de conclure.

## Pitfalls
Ne pas deviner les IDs ni ouvrir une base avec un schéma supposé. Ne pas publier transcripts, identifiants de messagerie ou erreurs brutes.

## Verification
Citer en interne le message et le fil retrouvés ; expliquer brièvement le référent. Distinguer contexte historique et état actuel vérifié.
