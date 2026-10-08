# runtime-status-footer

Distribution nettoyée du plugin original ; aucun reçu privé, historique, identifiant réel, credential ou dépôt Git embarqué.

## État et limites

EXPERIMENTAL : bibliothèque de formatage uniquement. `register` ne patche RIEN, même avec opt_in=true. Le statut épinglé demandé est OMIS : le code original contient un scope privé et un contrôle home/profil de test ; il n’est pas universellement portable. Aucun message créé, épinglé, édité ou désépinglé. Le cache est facultatif sous get_hermes_home()/state/provider_usage_cache.json ; aucun cron livré. Fournisseur inconnu ou différent : quota caché. La timezone historique Europe/Paris est conservée dans ce module expérimental, non généralisée. Ne pas présenter ce module comme une implémentation de statut épinglé complète.

Les hooks de rendu/sanitiseur internes et l’accès aux classes privées sont des monkeypatchs non garantis par le SDK public. Revalider après chaque mise à jour Hermes. Cette distribution n’est pas une admission au catalogue. Aucun `/close`.

## Installation volontaire

Après publication du dépôt, remplacer OWNER/REPO par le vrai dépôt (ce n’est pas une adresse publiée) :

```sh
hermes plugins install OWNER/REPO/plugins/runtime-status-footer --no-enable
hermes plugins doctor runtime-status-footer
hermes plugins capabilities runtime-status-footer
```

Le CLI actuel accepte les sous-dossiers Git ; aucun téléchargement ni activation réelle n’a été effectué ici. Choisir son profil/HERMES_HOME avant toute commande. Pour un essai local, copier UNIQUEMENT ce dossier dans le répertoire plugins de son home Hermes isolé, puis utiliser les commandes doctor/enable du CLI. `install ./chemin` n’est pas annoncé comme syntaxe supportée.

## Opt-in par utilisateur

Les trois plugins actifs sont inertes tant que les trois réglages suivants ne sont pas définis. Mettre ses propres identifiants, jamais ceux d’un exemple ; les listes doivent être non vides, numériques. Chaque profil garde ses réglages. Les autorisations natives Telegram restent nécessaires.

```sh
hermes config set plugins.entries.runtime-status-footer.settings.allowed_users '["VOTRE_ID_UTILISATEUR"]'
hermes config set plugins.entries.runtime-status-footer.settings.allowed_chats '["VOTRE_ID_CHAT"]'
hermes config set plugins.entries.runtime-status-footer.settings.opt_in true
hermes plugins enable runtime-status-footer
```

Ne pas exécuter ces listes littérales : leurs marqueurs non numériques sont refusés. L’extension runtime expérimentale ne s’active pas. Aucun pin_enabled opérant n’est proposé : la fonction épinglage est exclue plutôt que faussement configurable.

```sh
hermes plugins disable runtime-status-footer
```

Pas de changement du cœur sur disque, aucune activation automatique ou changement distant. Les chemins de données sont résolus par `get_hermes_home()`.

## Vérification effective

Suite commune : opt-in absent inerte pour les quatre imports, titre explicite, mot unique long, scope du sanitiseur/démontage, quota fournisseur inconnu. Suite approbations : huit tests avec le vrai adaptateur. Lancement avec HERMES_HOME temporaire avant import et avant résolution du runtime ; aucun test live Telegram, pin, livraison LLM ou quota réseau. Commande reproductible : `python3 ../run_tests.py` depuis ce dossier (Hermes installé requis pour la suite adaptateur).

Référence vérifiée : documentation officielle Hermes, pages « Plugins » et « Build a Hermes Plugin » ; CLI local `hermes plugins install --help`, `doctor --help` et PluginContext.get_config.
