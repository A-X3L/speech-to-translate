# 🎙️ Forza Translator — Traducteur & Dictée Vocale IA

Un outil autonome et universel pour Windows permettant de traduire ou dicter du texte à la voix en direct via l'API Gemini, directement dans vos jeux (comme Forza) et vos applications (Discord, WhatsApp, Word, etc.).

---

## 🛠️ Fonctionnalités

* **Dictée & Traduction en direct :** Capture le micro à la volée via un raccourci clavier (*hotkey*) ou les boutons d'une manette Xbox.
* **Modes d'enregistrement :**
  * `hold` (Push-To-Talk) : Maintenez la touche enfoncée pour parler, relâchez pour envoyer.
  * `toggle` : Appuyez une fois pour démarrer l'enregistrement, réappuyez pour l'arrêter et traduire.
* **Langues & Détection automatique :** Traduction multilingue (FR, EN, ES, DE, JA...) ou détection automatique de la langue parlée (`SOURCE_LANG=auto`).
* **Zone de notification Windows (Systray) & Icône Dango :**
  * Attribution automatique de l'icône Dango à la console Windows (`ICO/dango_translate_icon.ico`).
  * Réduction en tâche de fond dans la zone de notification (à côté de l'horloge) avec menu clic droit : *Afficher / Masquer* et *Quitter*.
* **Injection universelle :** Colle le texte directement dans le champ actif (`Ctrl+V`) avec option de validation automatique (`AUTO_ENTER`).
* **Configurateur Web :** Interface dashboard HTML/JS (`configurateur.html`) pour générer facilement votre fichier `.env` en quelques clics.
* **Modèles Gemini supportés :**
  * `gemini-3.5-flash-lite` : **Recommandé** — Quota gratuit généreux (15 req/min, 500 req/jour).
  * `gemini-3.1-flash-lite` : Rapide et économique (15 req/min, 500 req/jour).
  * `gemini-3.7-flash` : Modèle multimodal de pointe pour traduction ultra-rapide.
  * `gemini-2.5-flash` : Haute fidélité audio.
* **Utilitaires d'icônes inclus :**
  * `Recadrage.ps1` : Redimensionne et recadre vos visuels au format carré 512x512.
  * `convert_icon.py` : Convertit vos PNG (`dango_translate_icon_512.png`, `peas_translate_icon_512.png`, etc.) en fichiers Windows `.ico` multi-résolutions.
  * `creer_raccourci_bureau.bat` : Crée automatiquement un raccourci avec icône sur votre Bureau Windows.

---

## 🚀 Installation & Utilisation

### 1. Configuration
1. Ouvrez `configurateur.html` (ou l'application web) dans votre navigateur pour accéder au configurateur.
2. Renseignez votre clé API Gemini ainsi que vos préférences (langues, raccourcis, modèle).
3. Exportez/téléchargez le fichier sous le nom `.env` et placez-le à la racine du dossier.

### 2. Personnalisation des icônes (Optionnel)
1. Placez votre image PNG dans le dossier (par exemple `dango_translate_icon_512.png` ou `peas_translate_icon_512.png`).
2. Démarrez `convert_icon.py` pour générer automatiquement le fichier `icon.ico` multi-résolutions.
3. Lancez `creer_raccourci_bureau.bat` pour créer le raccourci Windows personnalisé sur votre Bureau.

### 3. Lancement
Exécutez simplement `run_xbox_translator.bat` (ou lancez manuellement le script Python) :
```bash
python main.py
```

Maintenez ensuite votre raccourci enfoncé (ex: `F8` ou `LS + RS` sur la manette), parlez en français, et relâchez : la traduction en anglais s'écrit et s'envoie instantanément dans le chat !
