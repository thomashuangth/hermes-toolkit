# Résultats réellement exécutés

- `python3 plugins/run_tests.py` : **13 tests réussis** (5 communs, 8 adaptateur Telegram natif).
- `hermes plugins doctor <dossier> --ci` : **4/4 dossiers acceptés**, HERMES_HOME temporaire à chaque lancement. Ces diagnostics sans réglages valident la découverte/import/registration inerte (0 outil, 0 hook), PAS les patches activés ni la livraison.
- Scan local des 15 fichiers livrés : aucun nom privé de l’original, identifiant réel de chat/topic, chemin hôte privé, Path.home(), dossier Git ou reçu embarqué. Les caches compilés générés par doctor ont été retirés.

## Couverture

Opt-in absent ; imports inertes ; titre explicite avec espaces doubles sans LLM ; plafond de 24 caractères y compris mot unique ; sanitiseur actif seulement sur identité/chat autorisés et restauration à unload ; fournisseur quota absent refusé.

Adaptateur réel : rendu natif et callbacks, HTML/UTF-16 long, absence d’autorisation permanente, autre chat inchangé, opt-in absent, recharge sans empilement, smart deny once/deny, restauration à unload. Le contexte utilisateur et l’envoi réseau sont des doublures ; aucun Telegram réel.

## Non couvert / non livré

- Aucun test live, credential, connexion Telegram, pin ou appel LLM.
- Route exacte de génération de /title et écriture SQLite complètes non exercées ici ; seul le helper apply_title explicite est testé.
- Le raccourcissement dépend de la présence du contexte de session lors du sanitiseur ; contexte absent => comportement original.
- runtime-status-footer est exclusivement une bibliothèque expérimentale de formatage : aucun wrapper runtime, aucun statut épinglé. Le pin original avait un scope privé/home de test non portable ; volontairement exclu.
- Originaux sous le home Hermes uniquement lus, jamais modifiés. Aucun changement du cœur, de Git, du profil actif ou de système distant.

La documentation officielle actuelle confirme `owner/repo/path/to/plugin` pour les installations Git en sous-dossier et le CLI local confirme `--no-enable`. Le dépôt doit encore être publié ; aucune installation distante n’a été testée.
