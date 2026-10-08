---
name: toolkit-manager
description: "Configurer le catalogue et choisir les skills Toolkit."
version: 0.2.0
author: thomashuangth, Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [toolkit, telegram, bootstrap]
    related_skills: []
---

# Toolkit Manager

Procédure guidée pour installer le seul plugin `toolkit-catalog`, puis choisir les six skills utilitaires via `/toolkit`. Ce skill ne contient **aucun script** et ne charge aucun code automatiquement : il décrit des commandes que l'agent n'exécute qu'après accord explicite. Installer ce skill n'installe ni plugin ni autres skills.

## When to Use

- Demande explicite « Configure le catalogue toolkit » ou `/toolkit-manager` suivie d'une demande de configuration.
- Inspection d'un catalogue existant ou sélection de skills Toolkit.
- Ne pas utiliser pour une mise à jour silencieuse, un autre profil ou un simple affichage de cette documentation. L'invocation sans demande précise doit demander ce que l'utilisateur souhaite, pas installer.

## Prerequisites

CLI Hermes avec `plugins doctor --ci`, `config set`, `plugins enable` et le SDK `register_telegram_handler`/`on_unload`. Telegram et ses autorisations natives doivent déjà fonctionner ; ne jamais lire de credentials pour cette procédure. Outils shell usuels (`curl`, `tar`) pour l'étape de récupération.

## How to Run

Installation native unique au terminal du profil choisi :

```sh
hermes skills install thomashuangth/hermes-toolkit/skills/toolkit-manager
```

Respecter scanner, quarantaine et confirmation native ; **ne jamais passer `--force`**. Nouvelle session Telegram : `/toolkit-manager Configure le catalogue toolkit`, ou simplement « Configure le catalogue toolkit ». Selon la version, un skill installé peut être exposé comme commande slash ; vérifier localement et ne pas promettre sa présence dans le menu Telegram.

## Procedure

1. Avec `terminal`, inspecter `hermes --help`, `hermes plugins --help`, `hermes plugins doctor --help`, `hermes config path` et `hermes plugins list`. Résoudre le profil effectif et `HERMES_HOME` ; à défaut le home natif par défaut est `~/.hermes`. Si le profil actif et le chemin CLI divergent, arrêter et clarifier. Ne pas lire `.env`, auth, vault ou fichiers de credentials ; inspecter uniquement les clés du catalogue par `hermes config get`. Critère : version, profil, destination et présence éventuelle connus.
2. Obtenir les vrais IDs numériques de l'utilisateur ET du chat Telegram depuis les métadonnées fiables de la session courante. Ne jamais utiliser un exemple, un nom, un ancien skill ou sa mémoire personnelle comme ID ; ne pas supposer que user et chat sont égaux. Si l'une des valeurs manque, la demander explicitement et la faire confirmer. Critère : deux valeurs réelles confirmées, profil approuvé.
3. Vérifier le dépôt public fixe `thomashuangth/hermes-toolkit` et le commit complet. Par défaut `9a748ee6b2943b704e5bb65daeefb3fda11abf36` (le catalogue publié depuis `dab1484b3f3c0dffb018b0ecbe67addb34690b0b` y est inchangé) ; changer de commit seulement pour un SHA publié explicitement vérifié. Lire `plugins/toolkit-catalog/plugin.yaml` et `__init__.py` du dépôt avant tout accord. Aucun suivi automatique de branche. Critère : provenance et code relus, commit identifié.
4. Récupérer et préparer **hors du profil**, dans un répertoire de travail jetable : télécharger l'archive du commit en HTTPS (`https://github.com/thomashuangth/hermes-toolkit/archive/<SHA>.tar.gz`), en extraire **uniquement** le sous-dossier `plugins/toolkit-catalog`, puis vérifier la liste des fichiers extraits (aucun chemin absolu, `..`, symlink ni fichier hors de ce sous-dossier). Refuser tout écrasement : si `$HERMES_HOME/plugins/toolkit-catalog` existe déjà, s'arrêter, inspecter sa provenance et sa configuration, proposer une configuration native ciblée — ne rien supprimer ni remplacer.
5. Demander une approbation explicite couvrant : copie de `plugins/toolkit-catalog` vers `$HERMES_HOME/plugins/`, exécution du doctor natif (qui importe du code tiers), allowlists limitées aux deux IDs, opt-in et activation (qui peut recharger la passerelle). L'accord ne couvre aucun autre skill, cron, credential, profil ou changement de permissions. Après accord seulement, copier le sous-dossier, lancer `hermes plugins doctor "$HERMES_HOME/plugins/toolkit-catalog" --ci`, puis configurer par les commandes natives :
   ```sh
   hermes config set plugins.entries.toolkit-catalog.settings.allowed_users '["<ID utilisateur>"]'
   hermes config set plugins.entries.toolkit-catalog.settings.allowed_chats '["<ID chat>"]'
   hermes config set plugins.entries.toolkit-catalog.settings.opt_in true
   hermes plugins enable toolkit-catalog
   ```
   Critère : toutes les commandes réussissent sans contournement ; sinon s'arrêter et expliquer.
6. Relire la cible exacte : `hermes plugins list`, puis `hermes config get` sur `plugins.entries.toolkit-catalog.settings.allowed_users`, `allowed_chats`, `opt_in`. Vérifier le manifeste et les fichiers du plugin installé. Demander `/toolkit` dans la session autorisée : seul son affichage réel prouve le fonctionnement Telegram. Si les handlers tardifs manquent, consulter `hermes gateway --help` et proposer un redémarrage approuvé, jamais un redémarrage automatique.
7. Les boutons du catalogue affichent les détails et la procédure native d'installation ; ils n'installent aucun skill. Pour chaque sélection, conserver `hermes skills inspect <identifiant>` puis `hermes skills install <identifiant>`, avec scanner et confirmation interactifs — aucune réponse simulée, aucun bypass. Les activations/désactivations du chargement concernent **tout Telegram du profil**, pas seulement ce chat, et n'uninstallent rien. Une nouvelle session peut être nécessaire. Critère : état relu après chaque choix ; aucune réussite inventée.

## Mises à jour sur demande

Vérifier d'abord `hermes skills check --help` et `hermes skills update --help` sur le runtime/profil choisi. Syntaxe vérifiée localement : `hermes skills check [name]` (contrôle sans installation) et `hermes skills update [name]`. Préférer un nom explicitement sélectionné ; sans nom, la portée est tous les skills suivis et exige un accord distinct. Faire un contrôle ponctuel borné, rapporter le résultat réel et les erreurs réseau ; ne pas présenter un échec comme « à jour ».

Avant toute mise à jour, demander l'accord pour chaque nom/provenance et lire les changements disponibles. Exécuter la commande native interactive, conserver scanner/quarantaine et confirmations, ne jamais passer `--force` ni simuler un accord. Les variantes éditées localement doivent rester intactes ; si non suivies ou bloquées, s'arrêter et expliquer. Relire l'état natif après mise à jour ; ouvrir une nouvelle session pour les instructions modifiées.

Aucune notification automatique, tâche cron ni bouton de mise à jour n'est installé par ce skill. Un utilisateur peut demander « Vérifie les mises à jour Toolkit » ; une surveillance récurrente requerrait une autorisation et une implémentation séparées. Les **skills** et le **plugin** sont deux mécanismes distincts : `skills update` ne met pas à jour `toolkit-catalog`. Le bootstrap fixe un commit et ne met jamais le plugin à jour automatiquement. Pour un plugin existant, inspecter séparément provenance et `hermes plugins update --help`, convenir d'un plan de migration/rollback explicite ; ne pas réappliquer cette procédure sur une cible existante.

## Pitfalls

- Pas de `--force`, de contournement du scanner, de commande construite avec des valeurs non citées, ni d'installation de la racine multi-plugins comme plugin unique.
- Ne jamais lire de credentials ; ne jamais installer d'autres plugins ni les autres skills. Le doctor n'est pas une preuve d'absence de code malveillant.
- En cas d'échec en cours : nettoyer le répertoire de travail jetable, mais **ne jamais prétendre à une transaction** : un plugin copié ou des réglages natifs partiellement appliqués peuvent subsister. S'arrêter, inspecter, expliquer.
- Retrait approuvé : `hermes config set plugins.entries.toolkit-catalog.settings.opt_in false`, puis `hermes plugins disable toolkit-catalog`. Le retrait ne restaure pas les choix de skills.
- Vérifier les listes d'IDs réellement écrites (`hermes config get`) : une liste vide ou erronée laisse le catalogue inerte par conception.
- Compatibilité macOS/Windows prévue (commandes sans shell, chemins relatifs), non exercée ici.

## Verification

Rapporter séparément : lecture du code publié, copie effectuée, doctor, écritures de configuration relues par `hermes config get`, `hermes plugins list`, et affichage Telegram de `/toolkit` **observé ou non observé**. Aucun test ne doit viser le profil actif.
