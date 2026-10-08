---
name: toolkit-manager
description: "Configurer le catalogue et choisir les skills Toolkit."
version: 0.1.0
author: thomashuangth, Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [toolkit, telegram, bootstrap]
    related_skills: []
---

# Toolkit Manager

Procédure guidée pour installer le seul plugin `toolkit-catalog`, puis choisir les cinq skills utilitaires via `/toolkit`. Ce skill ne charge aucun code automatiquement : le script reste inerte jusqu'à son exécution explicitement approuvée. Installer ce skill n'installe ni plugin ni autres skills.

## When to Use

- Demande explicite « Configure le catalogue toolkit » ou `/toolkit-manager` suivie d'une demande de configuration.
- Inspection d'un catalogue existant ou sélection de skills Toolkit.
- Ne pas utiliser pour une mise à jour silencieuse, un autre profil ou un simple affichage de cette documentation. L'invocation sans demande précise doit demander ce que l'utilisateur souhaite, pas installer.

## Prerequisites

Python 3.10+, CLI Hermes avec `plugins doctor --ci`, `config set`, `plugins enable` et SDK `register_telegram_handler`/`on_unload`. Telegram et ses autorisations natives doivent déjà fonctionner ; ne jamais lire de credentials pour cette procédure.

## How to Run

Installation native unique au terminal du profil choisi :

```sh
hermes skills install thomashuangth/hermes-toolkit/skills/toolkit-manager
```

Respecter scanner, quarantaine et confirmation native. Nouvelle session Telegram : `/toolkit-manager Configure le catalogue toolkit`, ou simplement « Configure le catalogue toolkit ». Les skills installés ont des commandes slash natives selon la documentation officielle `user-guide/features/skills` ; vérifier sur la version locale, ne pas promettre leur présence dans le menu Telegram.

## Procedure

1. Avec `terminal`, inspecter `hermes --help`, `hermes plugins --help`, `hermes plugins doctor --help`, `hermes config path` et `hermes plugins list`. Résoudre le profil effectif depuis le contexte d'exécution et `HERMES_HOME` ; à défaut le home natif par défaut est `~/.hermes`. Si le profil actif et le chemin CLI divergent, arrêter et clarifier. Ne pas lire `.env`, auth, vault ou fichiers de credentials. Inspecter uniquement les clés du catalogue par `hermes config get`. Critère : version, profil, destination et présence éventuelle connus.
2. Obtenir les vrais IDs numériques de l'utilisateur ET du chat Telegram depuis les métadonnées fiables de la session courante. Ne jamais utiliser un exemple, nom, ancien skill ou mémoire personnelle comme ID ; ne pas déduire que user et chat sont égaux. Si absents, demander les deux valeurs explicitement (par exemple informations `/whoami`), et leur confirmation. Ne pas détourner l'allowlist native ni installer Telegram. Critère : deux valeurs réelles confirmées, profil approuvé.
3. Vérifier le dépôt public fixe `thomashuangth/hermes-toolkit` et le commit complet. Par défaut `dab1484b3f3c0dffb018b0ecbe67addb34690b0b`, contenant déjà le catalogue ; utiliser `--ref` seulement avec un commit publié explicitement vérifié. Lire les fichiers Python et manifeste du sous-dossier public avec les outils de lecture/retrieval avant accord. Aucun suivi automatique de branche. Critère : provenance et code relus, commit identifié.
4. Localiser le dossier réellement installé de ce skill avec `skill_view`/`search_files`, lire `scripts/install_catalog.py`. Avec `terminal`, exécuter Python sur ce chemin (arguments correctement cités), `--user-id <ID réel> --chat-id <ID réel>` ; sans `--install` c'est un dry-run sans réseau ni écriture. Afficher le plan. Si le catalogue existe, le script refuse : inspecter sa provenance et sa configuration, ne pas supprimer/écraser ; proposer une configuration native ciblée après accord séparé.
5. Demander une approbation explicite pour ce plan : téléchargement HTTPS du commit, validation/copie du seul `plugins/toolkit-catalog`, exécution du doctor natif (qui peut importer du code tiers), allowlists limitées aux deux IDs, opt-in et activation pouvant recharger la passerelle. L'accord ne couvre aucun autre skill, cron, credential, profil ou changement de permissions. Après accord seulement, relancer le même script avec `--install` dans le même `HERMES_HOME`. Critère : toutes les commandes réussissent sans contournement.
6. Relire la cible exacte avec `hermes plugins list` et `hermes config get plugins.entries.toolkit-catalog.settings.allowed_users`, puis `allowed_chats`, puis `opt_in`. Vérifier fichiers/manifeste du plugin installé. Demander `/toolkit` dans la session autorisée ; seul son affichage réel prouve le fonctionnement Telegram. Si les handlers tardifs manquent, consulter `hermes gateway --help` et proposer un redémarrage approuvé, pas un restart automatique.
7. Les boutons du catalogue affichent les détails et la procédure native d'installation, ils n'installent aucun skill. Pour chaque sélection, conserver `hermes skills inspect` puis `hermes skills install`, scanner et confirmation interactifs ; aucune réponse simulée, aucun bypass. Les activations/désactivations du chargement concernent **tout Telegram du profil**, pas seulement ce chat. Une nouvelle session peut être nécessaire. Critère : état relu après chaque choix ; aucune réussite inventée.

## Mises à jour sur demande

Avec `terminal`, vérifier d'abord `hermes skills check --help` et `hermes skills update --help` sur le runtime/profil choisi. Syntaxe vérifiée localement : `hermes skills check [name]` (contrôle sans installation) et `hermes skills update [name]`. Préférer un nom explicitement sélectionné ; sans nom, la portée est tous les skills suivis/outdated et exige un accord distinct. Faire un contrôle ponctuel avec timeout borné, rapporter le résultat réel et les erreurs réseau ; ne pas présenter un échec comme « à jour ».

Avant toute mise à jour, demander l'accord pour chaque nom/provenance et lire les changements disponibles. Exécuter la commande native interactive, conserver scanner/quarantaine et confirmations, ne jamais passer `--force` ni simuler un accord. Les variantes éditées localement doivent rester intactes ; si non suivies ou bloquées, arrêter et expliquer. Relire l'état natif après mise à jour ; ouvrir une nouvelle session pour les instructions modifiées.

Aucune notification automatique, tâche cron ou bouton de mise à jour n'est installé par ce skill. Un utilisateur peut demander « Vérifie les mises à jour Toolkit » ; une surveillance récurrente requerrait une autorisation et une implémentation séparées. Les **skills** et le **plugin** sont deux mécanismes distincts : `skills update` ne met pas à jour `toolkit-catalog`. Le bootstrap fixe un commit, ne crée pas de suivi Git/provenance pour les updates natives de plugins et ne met jamais le plugin à jour automatiquement. Pour le plugin existant, inspecter séparément provenance et `hermes plugins update --help`, convenir d'un plan de migration/rollback explicite ; ne pas relancer ce helper sur une cible existante.

## Pitfalls

- Pas de `--force`, contournement de scanner, commandes shell construites avec des valeurs non citées ou installation de la racine multi-plugins.
- Le script ne lit pas de credentials et n'installe jamais les autres plugins ni les skills. Le doctor n'est pas une preuve d'absence de code malveillant.
- Échec : staging nettoyé ; un plugin copié ou des réglages natifs partiellement appliqués peuvent rester. Arrêter, inspecter et expliquer ; ne jamais prétendre à une transaction config ou restauration automatique. Un enable peut réussir même si la vérification ultérieure échoue.
- Retrait approuvé : `hermes config set plugins.entries.toolkit-catalog.settings.opt_in false`, puis `hermes plugins disable toolkit-catalog`. Le retrait ne restaure pas les choix de skills.
- Compatibilité macOS/Windows prévue par stdlib et argv sans shell, non exercée ici. Installation distante de ce nouveau skill exige sa publication ; le commit par défaut du plugin ne contient pas ce nouveau skill.

## Verification

Le dry-run doit afficher `install: false`, le home, le commit et les commandes, sans modifier le profil. Tests fixtures : `terminal(command="python3 -m unittest discover -s tests -p 'test_toolkit_manager.py' -v")` depuis la racine du dépôt. Tests runtime du catalogue : `python3 plugins/run_tests.py`, home temporaire avant imports. Aucun test ne doit viser le profil actif. Rapporter séparément validation locale, installation distante et livraison Telegram observée/non observée.
