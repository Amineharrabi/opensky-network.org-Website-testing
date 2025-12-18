# Introduction et Contexte du Projet

## Présentation du Projet
Ce projet automatise des tests end-to-end (Selenium + Pytest) et des audits non-intrusifs (requests) sur le site public OpenSky Network : https://opensky-network.org/.

Objectif principal : augmenter la capacité à détecter des anomalies réelles (liens cassés, erreurs JavaScript, régressions UI, headers de sécurité absents, etc.) et produire des éléments exploitables pour un ticket Jira (preuves, logs, HTML, captures d'écran).

## Cahier des Charges et Objectifs
- Construire des suites de tests utiles (et non “hollow”) orientées bug hunting.
- Collecter automatiquement des preuves quand un test échoue (screenshot, HTML, console logs, erreurs JS).
- Faciliter la création d’un bug report Jira (automatique optionnel).
- Générer un rapport PDF structuré (ce document) pour la soutenance / livrable.

## Architecture Technique
- `pytest` : orchestration, markers, exécution sélective.
- `selenium` : tests UI (navigation, interactions, map, responsive).
- `requests` : audits rapides (headers sécurité, intégrité des liens).
- `tests/conftest.py` : configuration runtime + collecte d’artifacts en cas d’échec + intégration Jira (optionnelle).
- `reports/` : rapports (PDF/HTML), screenshots et artifacts de bugs.

# Innovations

## Phase 1 : Collecte d’Artifacts Automatique
Lors d’un échec de test, le framework sauvegarde automatiquement :
- `screenshot.png`
- `page.html` (HTML complet)
- `console.json` (logs console navigateur, si disponibles)
- `js_errors.json` (erreurs runtime collectées côté client, si supporté)

## Phase 2 : Intégration Jira (optionnelle)
En activant l’option `--jira-create-on-fail`, un ticket Jira peut être créé automatiquement, avec pièces jointes (captures + logs).

Remarque : l’intégration est volontairement simple et contrôlable par variables d’environnement (pas de secrets dans le code).

# Analyse Détaillée des Suites de Tests

## Suite 1 : Fonctionnel (Navigation, Pages publiques)
Les tests valident les parcours “publics” (home/about/data/feed) et le chargement de la carte publique (map).

## Suite 2 : Performance (Best-effort)
Tests orientés temps de chargement et métriques navigateur (LCP/CLS/TBT) avec throttling (si support CDP).

## Suite 3 : Compatibilité (Cross-browser)
Smoke tests (à exécuter selon le navigateur configuré via `--browser`).

## Suite 4 : Responsive
Matrice de viewports (mobile/tablet/desktop) avec :
- screenshots pour revue visuelle
- détection de scroll horizontal
- heuristiques “tap targets”
- checks sur overflow de code blocks

## Suite 5 : Sécurité (Non-intrusif)
Audit des headers HTTP sur pages publiques (HSTS, nosniff, framing protections, etc.) en mode :
- “audit” (journalise des findings)
- “strict” via `--audit-strict` (échec du test si manque)

## Suite 6 : Intégrité des liens
Extraction des URLs depuis le DOM et vérification HTTP (par défaut interne uniquement, optionnellement externe).

## Suite 7 : Erreurs JavaScript / Console
Détection d’erreurs client-side (console logs + collecteur runtime) sur pages clés.

## Suite 8 : Fuzzing léger des inputs (Map search)
Tests négatifs sur le champ de recherche de la carte (payloads XSS usuels) avec heuristiques non-intrusives (absence d’alert/injection évidente).

# Conclusion et Perspectives

## Points Forts du Projet
- Tests orientés “bug signals” (erreurs console, liens cassés, headers sécurité).
- Artifacts automatiques en cas d’échec => bug report plus rapide.
- Intégration Jira (optionnelle) pour industrialiser la remontée de bugs.

## Améliorations Futures
- Ajout de tests accessibilité (axe-core) si l’outillage est autorisé.
- Exécution planifiée (monitoring) + historique de tendances (performances, erreurs JS).
- Enrichissement du rapport PDF par extraction automatique des suites/markers et statistiques d’exécution.

