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

## 5. État d'avancement & Architecture actuelle
- **Architecture en 2 Entités Distinctes** :
  - **Entité 1 (Le HUD Actif / Micro-Languette Triptyque)** : Micro-fenêtre ultra-légère dédiée exclusivement à l'écoute et au retour visuel. Fond gris anthracite totalement opaque et stable (`#1f1f1f`). Suppression définitive de toute transparence globale (`WA_TranslucentBackground`) et des ombres portées recalculées qui causaient des plantages DWM Windows (`UpdateLayeredWindowIndirect`).
  - **Entité 2 (L'Atelier de Configuration & Aide)** : Fenêtres de dialogue indépendantes (`SettingsDialog`, `HelpDialog`) à fond opaque `#1f1f1f`, ouvertes à la demande depuis le System Tray ou via clic droit sur le HUD sans surcharger la micro-capsule d'écoute ni provoquer de menus hors-champ.
- **Le Triptyque de la Micro-Languette (HUD)** :
  1. **Badge Drapeau Langue Cible (`FlagBadgeWidget`)** : Téléchargement dynamique asynchrone non-bloquant depuis Flagcdn (`https://flagcdn.com/w40/{country}.png`), avec mise en cache locale intelligente dans `cache/flags/` et fallback textuel immédiat sur code pays/langue en mode hors-ligne.
  2. **Égaliseur Vocal Dynamique (`VoiceEqualizerWidget`)** : Remplace définitivement l'ancien logo AI Studio à points colorés et la bulle centrale. 5 barrettes acoustiques réactives au volume sonore (`volume_level`), onde fluide en phase de traitement (`processing`), profil d'alerte en rouge (`error`), et sourdine ardoise si Mute. Déclenche l'écoute instantanément au clic.
  3. **Interrupteur Mute Discret (`MuteButtonWidget`)** : Bouton vectoriel permettant de couper ou d'autoriser l'écoute globale à la volée (`config.toggle_mute()`), bloquant instantanément les entrées F8 et manette.
- **Suppression des Anciens Composants Obsolètes** :
  - Retrait définitif de la roue dentée (⚙) et du point d'interrogation (?) du HUD principal (déportés vers le System Tray et le menu contextuel clic-droit).
  - Élimination de l'ancien logo AI Studio et du bouton circulaire.
- **Intégration Windows System Tray & Clic Droit Unifié** :
  - `QSystemTrayIcon` avec menu contextuel complet (Atelier de Configuration, Atelier d'Aide, Interrupteur Mute, sélection du bord d'ancrage, Quitter).
  - Clic droit direct sur la micro-languette ouvrant le même menu unifié.
- **Ancrage Universel sur les 4 Bords (`top`, `bottom`, `left`, `right`)** :
  - Support natif de l'aimantation sur les 4 bords avec bascule automatique de la disposition (horizontale 126x26 px pour haut/bas, verticale 26x126 px pour gauche/droite).
  - Déplacement libre par glisser-déposer le long du bord actif.
- **Libération Critique du Déclenchement (Micro & Touche F8)** :
  - Suppression du blocage UIA `is_editable_text_field_focused()`. Réactivité 100% immédiate sur F8, clic égaliseur et bouton manette.
- **Sélecteur de Langue au Démarrage & i18n Fiabilisé** :
  - `LanguageSelectionDialog` opaque (#1f1f1f), persistant `UI_LANG` et `SHOW_LANG_SELECTOR` dans `config.json` et rechargeant dynamiquement les dictionnaires (`reload_runtime_config()`) avant l'affichage du HUD.
- **Conditionnalité dynamique Langue Source** : Affichage exclusif du sélecteur de langue source pour Azure Speech ; masqué pour Gemini.
- **Saisie libre Langue Cible (`TARGET_LANG`)** : Champ texte libre sauvegardé instantanément (ex: `en`, `fr`, `ja`, `es-ES`, `de-DE`) avec rafraîchissement immédiat du drapeau sur le HUD.
- **Sélection Microphone** : `QComboBox` dédiée listant les périphériques système (`sd.query_devices()`) avec sauvegarde sous `INPUT_DEVICE`.
- **Thématique Anthracite / Noir Mat** : Fond `#1f1f1f` stable, cartes `#161b22`, bordures et accents cyan `#22d3ee`.