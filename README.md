# Hermes Toolkit — tap portable

Six skills originaux, en français : `toolkit-manager` (bootstrap principal), `session-context-recovery`, `usage-cost-audit`, `runtime-config-audit`, `scheduled-task-watchdog`, `backup-and-recovery`. Python 3.10+ pour les scripts, uniquement bibliothèque standard. Aucun ajout automatique de tâche cron, accès distant ni changement de configuration. Les extensions Telegram séparées sont dans `plugins/` : plugins adaptés, catalogue volontaire `/toolkit` et module de formatage expérimental. **Le statut épinglé portable n’est pas encore implémenté** ; il ne faut pas confondre ce module avec la fonction complète de l’installation d’origine.

## Démarrage principal (après publication du nouveau skill)

Une seule commande au terminal du profil choisi :

```sh
hermes skills install thomashuangth/hermes-toolkit/skills/toolkit-manager
```

Conserver le scanner et la confirmation native. Dans une nouvelle session Telegram, envoyer `/toolkit-manager`, puis « Configure le catalogue toolkit » (ou directement cette phrase). La documentation native Skills System décrit les skills installés comme commandes slash ; leur présence dans le menu Telegram dépend de la version. Le skill guide l'agent : rien ne s'exécute à son installation. Après inspection du profil, IDs réels de la session et approbation du plan, son helper copie uniquement le catalogue public à un commit fixé, lance le doctor natif puis configure les allowlists/opt-in et active le plugin. Dry-run par défaut, refus d'écrasement ; aucun credential lu. Voir `skills/toolkit-manager/SKILL.md`. Le commit plugin par défaut est déjà publié ; ce nouveau skill doit encore être publié.

## Installation sélective

Le dépôt public est `thomashuangth/hermes-toolkit`. Le tap reste facultatif :

```sh
hermes skills tap add thomashuangth/hermes-toolkit
hermes skills tap list
hermes skills inspect thomashuangth/hermes-toolkit/skills/backup-and-recovery
hermes skills install thomashuangth/hermes-toolkit/skills/backup-and-recovery
```

Répéter uniquement la dernière commande avec le nom des skills souhaités. Le tap ajoute une source de recherche, **pas** tous les skills. Ne pas utiliser `--force` pour contourner une alerte ; lire le rapport de sécurité. Le skill `session-context-recovery` peut déjà exister : vérifier les collisions avant installation, ne pas écraser une version personnelle.

Syntaxe vérifiée dans la CLI installée (`hermes skills --help`, `tap add --help`, `install --help`) et son source : `hermes_cli/skills_hub.py::do_tap`, `tools/skills_hub.py::TapsManager.add` (racine par défaut `skills/`), `tools/skills_hub_github.py::GitHubSkillsSource.fetch` (identifiant `owner/repo/path/to/skill-dir`, scripts téléchargés avec le dossier). La publication et l'installation depuis GitHub ne sont pas testées ici. Sur une autre version, relire l'aide avant installation.

## Catalogue Telegram `/toolkit`

Le plugin volontaire `plugins/toolkit-catalog` expose les cinq skills avec détails et état installé, puis active/désactive leur chargement **pour tout Telegram du profil** via les réglages natifs. Par défaut il reste inerte : opt-in et listes d'utilisateurs/chats obligatoires. Le bouton d'installation affiche la procédure interactive native au terminal (scanner et confirmation conservés), **pas une installation Telegram en un clic**. Bootstrap exact, sécurité, persistance et limites : `plugins/toolkit-catalog/README.md`. Vérification isolée : `python3 plugins/run_tests.py`.

## Essai local sans installer dans un profil réel

Depuis la racine du toolkit :

```sh
python3 -m unittest discover -s tests -v
python3 skills/backup-and-recovery/scripts/backup.py --help
python3 skills/scheduled-task-watchdog/scripts/watchdog.py --help
```

Les tests créent leurs fixtures dans des répertoires temporaires isolés et n'importent pas le runtime Hermes. Aucun fichier de production, profil, cron ou configuration n'est modifié. Pour un essai manuel, sélectionner un dossier de fixtures, créer un nom d'archive nouveau puis utiliser `restore-check` ; les commandes détaillées figurent dans chaque `SKILL.md`. `<skill-dir>` désigne le dossier du skill sélectionné, pas un chemin fixé à cette machine.

Pour tester les procédures par conversation, utiliser un profil de test créé selon l'aide de sa version de Hermes, ne jamais le profil personnel. Demander successivement : récupération d'un contexte fictif, audit d'une configuration de test et contrôle d'un export de reçus fictif. Vérifier que l'agent demande une précision si le référent est ambigu et n'applique aucun changement sans autorisation. L'installation d'un skill ne garantit pas sa sélection dans une session déjà ouverte : ouvrir une nouvelle session et vérifier le catalogue.

## Limites et sécurité

- Les audits sont des procédures, pas des adaptateurs figés aux schémas internes. Découvrir colonnes, CLI et profils avant lecture ; ne jamais afficher de secrets ni d'historique brut.
- Watchdog : export normalisé fourni explicitement, contrôle ponctuel, stdout vide si sain ; aucun cron, notification ou état persistant. Codes 0/1/2 : sain/anomalie/entrée invalide.
- Backup : liste de fichiers explicitement approuvée, symlinks et noms de credentials refusés, plafond 64 MiB ; SQLite sauvegardé en ligne. La sélection reste responsable d'exclure les secrets présents dans le contenu.
- Archives NON chiffrées : ne jamais les publier. Permissions POSIX privées ; ACL Windows à contrôler séparément. Pas de cohérence globale entre plusieurs fichiers actifs, restauration applicative, VM, réplication ou preuve hors site.
- `restore-check` contrôle intégrité, hashes et matérialisation temporaire ; il ne restaure jamais une production. Tests exécutés sur Linux ; compatibilité macOS/Windows non exercée ici.

## Provenance et licence

Réécriture originale adaptée de workflows locaux de récupération de contexte, audit de coûts et protections planifiées. Aucun export des sources privées, identifiants, topologie, références locales ou scripts de production. Aucune copie de skills de développement livrés avec Hermes ; les guides d'auteur et d'utilisation ont seulement servi à vérifier conventions et CLI. Ce projet est indépendant, non officiel et non attribué aux auteurs des skills bundled. Contributions du toolkit assistées par Hermes Agent ; licence MIT, voir `LICENSE`. Les noms de contributeurs personnels sont volontairement omis.
