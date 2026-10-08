# `/toolkit` — catalogue Telegram volontaire

Cinq skills du dépôt public `thomashuangth/hermes-toolkit`, boutons de détail, état installé, activation/désactivation du **chargement sur Telegram pour tout le profil**. Ce n'est ni une désinstallation ni une autorisation d'exécuter les scripts. Aucun LLM, cron ou service supplémentaire.

## Bootstrap exact (terminal, profil choisi)

Prérequis : Hermes avec `PluginContext.register_telegram_handler` et `on_unload`, plateforme Telegram déjà configurée et son contrôle d'accès natif actif. Vérifier `hermes plugins --help` et `hermes skills install --help`. Choisir explicitement le `HERMES_HOME` du profil voulu pour toutes les commandes ; ne pas utiliser un profil de production pour les tests.

```sh
# Remplacer les trois valeurs ; IDs Telegram numériques, pas @pseudos.
export HERMES_HOME="/chemin/du/profil-hermes"
export TOOLKIT_USER_ID="123456789"
export TOOLKIT_CHAT_ID="123456789"

git clone https://github.com/thomashuangth/hermes-toolkit.git
cd hermes-toolkit
# Lire __init__.py et plugin.yaml avant de charger du code Python tiers.
# Arrêter si ce plugin existe déjà : ne pas écraser une version locale.
test ! -e "$HERMES_HOME/plugins/toolkit-catalog" || exit 1
mkdir -p "$HERMES_HOME/plugins"
cp -R plugins/toolkit-catalog "$HERMES_HOME/plugins/toolkit-catalog"
hermes plugins doctor "$HERMES_HOME/plugins/toolkit-catalog" --ci
hermes config set plugins.entries.toolkit-catalog.settings.allowed_users "[\"$TOOLKIT_USER_ID\"]"
hermes config set plugins.entries.toolkit-catalog.settings.allowed_chats "[\"$TOOLKIT_CHAT_ID\"]"
hermes config set plugins.entries.toolkit-catalog.settings.opt_in true
hermes plugins enable toolkit-catalog
hermes plugins list
```

Le bootstrap est une copie locale explicite d'un sous-dossier relu, **pas** `hermes plugins install owner/repo` : la racine de ce dépôt multi-plugins n'est pas un plugin unique. La copie n'effectue pas de scan de skills. Les skills ne sont jamais copiés par le plugin. L'activation native peut recharger une passerelle connectée ; si votre version ne câble pas les handlers tardifs, redémarrer la passerelle selon `hermes gateway --help`. Dans Telegram, envoyer `/toolkit`. L'accès exige l'opt-in, les deux listes non vides et l'autorisation native. Pour plusieurs utilisateurs/chats, passer des listes JSON au writer `hermes config set`.

## Installation et consentement

Le bouton **Installer : procédure native** affiche les commandes exactes `hermes skills inspect owner/repo/skills/nom` puis `hermes skills install owner/repo/skills/nom`. Il **n'installe rien dans Telegram**. Exécuter ces commandes au terminal interactif du même profil, lire le scanner natif/quarantaine et accepter ou refuser la confirmation native. Le source installé montre que ce flux est interactif (`hermes_cli.skills_hub._install_skill`) ; le plugin ne simule pas sa réponse et ne passe aucun drapeau de contournement. Si le scanner bloque, arrêter et examiner le rapport. Si un nom existe déjà, ne pas écraser une variante locale. Revenir à `/toolkit` pour relire l'état.

## État et portée

- Détection réelle par le registre natif `_find_all_skills(skip_disabled=True)`, y compris skills désactivés. Un nom détecté prouve sa présence, **pas sa provenance ni son intégrité**. Un skill bundled/local homonyme peut donc être affiché installé.
- Boutons d'activation : `save_disabled_skills(..., platform='telegram')`, avec relecture après écriture. Persistance dans `skills.platform_disabled.telegram` du `config.yaml` du profil ; réglages globaux, autres plateformes et autres noms préservés. Une désactivation globale reste prioritaire : activation refusée, à régler explicitement au terminal via `hermes skills`.
- La portée est **tous les chats et utilisateurs Telegram de ce profil**, pas un topic/utilisateur unique. Réserver les allowlists à des administrateurs de confiance. Les boutons ne changent ni fichiers, ni cron, ni accès SSH. Ils ne retirent pas un skill déjà chargé du contexte ; commencer une nouvelle session pour un résultat prévisible.
- Cartes en mémoire uniquement : jeton aléatoire lié à utilisateur/chat/topic/session Hermes/message, expiration 10 minutes, plafond 512 cartes. Changement de session, déchargement/rechargement ou redémarrage invalide les anciennes cartes. Les boutons d'un autre utilisateur ne sont jamais utilisables, même s'il est autorisé au catalogue.
- Les permissions du plugin sont relues à chaque clic. Les handlers PTB sont enregistrés via le SDK, groupe -20, callback strictement préfixé `tkc:` ; les autres callbacks natifs restent intacts. Rechargement : nouvelle génération et remplacement uniquement des handlers appartenant au catalogue.

## Arrêt / retrait

```sh
hermes config set plugins.entries.toolkit-catalog.settings.opt_in false
hermes plugins disable toolkit-catalog
# Facultatif, après vérification :
hermes plugins remove toolkit-catalog
```

Désactiver le plugin ne restaure pas les réglages de skills déjà choisis. Les rétablir avec `hermes skills`, sélectionner Telegram. Le retrait du plugin ne désinstalle aucun skill.

## Vérification et limites

Depuis la racine du dépôt :

```sh
python3 plugins/run_tests.py
```

Le lanceur utilise le runtime fourni par `hermes --print-runtime-command` et un `HERMES_HOME` temporaire avant tout import. Les tests de ce plugin refusent un lancement direct sans marqueur d'isolation. Tests : vrais registre/config/writer/PluginContext Hermes, handlers et boutons PTB avec mocks de transport, scoping, expiration, révocation et rechargement. Aucun message Telegram réel, installation GitHub distante ou modification du profil actif pendant ces tests.

Les helpers du registre et d'admission/session sont ceux du source installé, mais certains portent `_` et ne constituent pas une garantie ABI. Revalider après mise à jour Hermes. Le plugin utilise le writer natif et sérialise ses propres clics ; éviter les modifications concurrentes du même fichier par d'autres outils. Une erreur après écriture peut laisser le réglage persisté même si l'édition Telegram échoue : relancer `/toolkit` pour relire. Pas d'installation en un clic, d'auto-update, de preuve de provenance, ni de révocation rétroactive des instructions déjà présentes dans le contexte.
