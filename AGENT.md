# Directives de l'Agent

## 1. Règle principale : Pas de serveur ni d'éléments de preview web
- **Ne pas créer ni tenter de réparer de serveur de preview web** (Node.js, Vite, serveurs HTTP, etc.).
- L'utilisateur n'utilise pas la preview AI Studio / Cloud Run. Il est inutile de dépenser des ressources pour démarrer ou maintenir un serveur de développement pour la preview.
- Ce projet est une application de bureau locale / script Python pour Windows (**Speech to Translate — Traducteur & Dictée Vocale IA**).

## 2. Interdiction d'exécution d'I/O Matériel & GUI en Sandbox (Anti-Freeze)
- **Validation statique uniquement :** Ne JAMAIS tenter d'exécuter dynamiquement des scripts Python qui ouvrent une interface graphique (`QApplication.exec()`) ou qui attendent un périphérique physique (microphone, clavier, manette X-Input).
- L'environnement de build cloud est *headless* et sans périphérique attaché : l'exécution d'une boucle d'attente matérielle provoque un gel du conteneur et un timeout.
- Valider le code exclusivement par analyse syntaxique statique (`python -m py_compile main.py`).

## 3. Règles d'Architecture du Code
- **Écoute matérielle non-bloquante :** L'interception des touches de clavier ou boutons manette ne doit JAMAIS utiliser de boucle synchrone `while`. Utiliser exclusivement des mécanismes asynchrones ou récurrents (ex: `QTimer` sous PyQt6).
- **Garde-fou Temporal UI :** Tout mode d'écoute active (ex: capture d'un bouton manette dans les réglages) doit intégrer une temporisation automatique (ex: 8 secondes max). Sans action dans ce délai, l'écoute se désactive seule.
- **Gestion du Focus Windows :** La vérification du champ texte actif doit être non-bloquante pour l'interface graphique.

## 4. Portée et priorités
- Se concentrer exclusivement sur la structure applicative locale :
  - Script principal Python (`main.py`, modules GUI PyQt6)
  - Fichiers de configuration (`config.json`, `.env`)
  - Fichiers de directives et documentation (`AGENT.md`, `README.md`)
  - Dépendances Python (`requirements.txt`)
- Respecter scrupuleusement la charte graphique dark/cyan (#22d3ee) et le fonctionnement minimaliste type `Win + H`.