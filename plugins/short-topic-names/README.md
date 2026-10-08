# short-topic-names

Distribution nettoyée du plugin original ; aucun reçu privé, historique, identifiant réel, credential ou dépôt Git embarqué.

## État et limites

Sanitiseur déterministe : quatre mots / 24 caractères. Le patch global du prompt original est volontairement retiré car il ne dispose pas de scope utilisateur. Si les variables de session ne sont pas présentes au renommage, aucun raccourcissement : sécurité avant fonctionnalité. Aucun sujet existant n’est parcouru.

Les hooks de rendu/sanitiseur internes et l’accès aux classes privées sont des monkeypatchs non garantis par le SDK public. Revalider après chaque mise à jour Hermes. Cette distribution n’est pas une admission au catalogue. Aucun `/close`.

## Installation volontaire

Après publication du dépôt, remplacer OWNER/REPO par le vrai dépôt (ce n’est pas une adresse publiée) :

```sh
hermes plugins install OWNER/REPO/plugins/short-topic-names --no-enable
hermes plugins doctor short-topic-names
hermes plugins capabilities short-topic-names
```

Le CLI actuel accepte les sous-dossiers Git ; aucun téléchargement ni activation réelle n’a été effectué ici. Choisir son profil/HERMES_HOME avant toute commande. Pour un essai local, copier UNIQUEMENT ce dossier dans le répertoire plugins de son home Hermes isolé, puis utiliser les commandes doctor/enable du CLI. `install ./chemin` n’est pas annoncé comme syntaxe supportée.

## Opt-in par utilisateur

Les trois plugins actifs sont inertes tant que les trois réglages suivants ne sont pas définis. Mettre ses propres identifiants, jamais ceux d’un exemple ; les listes doivent être non vides, numériques. Chaque profil garde ses réglages. Les autorisations natives Telegram restent nécessaires.

```sh
hermes config set plugins.entries.short-topic-names.settings.allowed_users '["VOTRE_ID_UTILISATEUR"]'
hermes config set plugins.entries.short-topic-names.settings.allowed_chats '["VOTRE_ID_CHAT"]'
hermes config set plugins.entries.short-topic-names.settings.opt_in true
hermes plugins enable short-topic-names
```

Ne pas exécuter ces listes littérales : leurs marqueurs non numériques sont refusés. L’extension runtime expérimentale ne s’active pas. Aucun pin_enabled opérant n’est proposé : la fonction épinglage est exclue plutôt que faussement configurable.

```sh
hermes plugins disable short-topic-names
```

Pas de changement du cœur sur disque, aucune activation automatique ou changement distant. Les chemins de données sont résolus par `get_hermes_home()`.

## Vérification effective

Suite commune : opt-in absent inerte pour les quatre imports, titre explicite, mot unique long, scope du sanitiseur/démontage, quota fournisseur inconnu. Suite approbations : huit tests avec le vrai adaptateur. Lancement avec HERMES_HOME temporaire avant import et avant résolution du runtime ; aucun test live Telegram, pin, livraison LLM ou quota réseau. Commande reproductible : `python3 ../run_tests.py` depuis ce dossier (Hermes installé requis pour la suite adaptateur).

Référence vérifiée : documentation officielle Hermes, pages « Plugins » et « Build a Hermes Plugin » ; CLI local `hermes plugins install --help`, `doctor --help` et PluginContext.get_config.
