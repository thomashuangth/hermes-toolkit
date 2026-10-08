---
name: usage-cost-audit
description: "Auditer les usages et les estimations de coût."
version: 0.1.0
author: "Contributeurs du toolkit, Hermes Agent"
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [portable, audit, safety]
    related_skills: []
---

# usage-cost-audit

Workflow portable à portée explicite ; lecture et validation avant toute modification.

## When to Use
- Dépenses, tokens, appels auxiliaires ou comparaison de routes.
- Ne pas assimiler estimation locale, facture et quota d'abonnement.

## Prerequisites
Accès autorisé aux relevés du profil actif. Découvrir la CLI avec `terminal(command="hermes usage --help")`. Aucun appel facturable requis pour l'audit.

## Procedure
1. Fixer période, fuseau, monnaie et profil ; collecter les relevés en lecture seule.
2. Pour SQLite, utiliser une sauvegarde en ligne autorisée vers un dossier temporaire, puis découvrir tables et colonnes avant les requêtes.
3. Identifier les sources main/aux ; vérifier si une table inclut déjà l'autre pour éviter tout double comptage.
4. Distinguer input, cache, output et reasoning selon le fournisseur ; ne jamais additionner reasoning à output quand il en est un sous-ensemble.
5. Calculer avec `execute_code` ou `terminal`, jamais mentalement. Comparer à l'estimation enregistrée et expliquer les écarts, données absentes et tarifs datés.
6. Confirmer les tarifs actuels auprès du fournisseur avant une recommandation ; présenter les snapshots locaux comme historiques, pas comme facture.

## Pitfalls
Les schémas évoluent. Pas de tarif mémorisé, solde inventé ou clé copiée en sortie. Ne pas lancer une connexion interactive depuis l'agent.

## Verification
Rapport : période, couverture main/aux, tokens, coût estimé et limites. Recommander un seul changement mesurable, sans l'appliquer sans autorisation.
