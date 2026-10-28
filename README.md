# **🎙️ Speech to Translate — AI Voice Translator & Traducteur Vocal**

Un utilitaire Windows autonome et universel fonctionnant en arrière-plan avec un HUD discret (style Windows dictée `Win + H`). Il permet de traduire et dicter votre voix en direct via le service de **streaming continu Azure Speech** (`TranslationRecognizer`) ou via l'API **Google Gemini Flash / Gemma**, directement dans le champ texte actif de vos applications et jeux (Discord, WhatsApp, Word, Notepad, Forza Horizon, etc.).

---

## **📐 Architecture & Principes Fondamentaux**

Le projet repose sur des piliers d'ingénierie stricts pour garantir une exécution ultra-fluide sans ralentir les jeux vidéo :

1. **Architecture Dual-Engine (Azure Speech & Google Gemini) :**
   * **Azure Speech SDK (`TranslationRecognizer`) :** Streaming continu haute fidélité avec latence quasi-nulle. Le flux audio est transmis en temps réel, affiche les segments intermédiaires (`recognizing`) et injecte automatiquement le texte traduit dès validation du segment (`recognized`).
   * **Google Gemini API :** Mode batch audio utilisant les modèles multimodaux de pointe (`gemini-3.5-flash-lite`, `gemma-4-26b`) pour une auto-détection contextuelle globale.
   * Bascule instantanée entre les deux moteurs depuis le volet des **Réglages (⚙️)** du HUD.

2. **Garde-fou de Focus Texte (Windows Focus Check) :**
   * L'application interroge les API Windows (Win32 / UI Automation) dès la sollicitation du raccourci.
   * Si aucun champ de saisie texte éditable n'est actif, la capture s'interrompt immédiatement avec une notification visuelle sur le HUD, évitant tout appel API inutile et toute consommation superflue de quota.

3. **Point d'Entrée Unifié (`declencher_action_micro`) :**
   * Tous les périphériques (raccourcis clavier globaux, boutons de manette Xbox XInput, clic direct sur le microphone du HUD) convergent vers un pipeline unique thread-safe.

4. **Audio Ducking Master Synchrone (`pycaw`) :**
   * Atténuation automatique du volume principal de Windows pendant la durée exacte de la parole.
   * Restauration instantanée et garantie du volume sonore initial via un bloc `finally:`, évitant tout blocage du son en cas d'erreur ou d'interruption.

---

## **🛠️ Fonctionnalités Clés**

* **HUD Flottant & Panneaux Déroulants (Flyout) :**
  * Overlay flottant compact inspiré de l'ergonomie `Win + H` avec animations visuelles douces.
  * Égaliseur vectoriel réactif (5 colonnes de points animées selon l'amplitude réelle du micro).
  * **Roue crantée (⚙️ Réglages) :** Volet déroulant intégré pour ajuster les clés API, le moteur actif, la région Azure, la langue source conditionnelle (Azure), la langue cible en saisie libre (`TARGET_LANG`), le niveau de ducking, l'opacité et les raccourcis.
  * **Bouton Aide (? Aide) :** Affiche le statut du moteur, les raccourcis configurés et le guide d'utilisation directement dans le HUD, avec accès rapide à la documentation locale (`help.html`).
* **Modes d'Enregistrement :**
  * `hold` (Push-To-Talk) : Maintenez le raccourci enfoncé pour dicter, relâchez pour finaliser et traduire.
  * `toggle` (Bascule) : Pressez une fois pour ouvrir le micro, pressez à nouveau pour couper et traduire.
* **Support Manette Xbox (XInput) :**
  * Capture des boutons de manette (`R_THUMB`, `L_THUMB`, `LB`, `RB`, etc.) avec boucle asynchrone non-bloquante (`QTimer`) et garde-fou temporel de sécurité de 8 secondes.
* **Zone de Notification (Systray) :**
  * Réduction discrète dans la barre des tâches à côté de l'horloge avec menu contextuel rapide (*Paramètres*, *Aide*, *Masquer/Afficher*, *Quitter*).
* **Injection Universelle de Texte :**
  * Saisie rapide du texte traduit au curseur actif via presse-papier (`Ctrl+V`) avec option d'envoi automatique (`AUTO_ENTER`).

---

## **🤖 Comparatif des Moteurs Supportés**

| Moteur / Modèle | Type de Traitement | Latence | Quota Gratuit | Usage Recommandé |
| :--- | :--- | :--- | :--- | :--- |
| **Azure Speech Translation** | **Streaming Continu** | **Ultra-faible (~100-300ms)** | 5 heures / mois | **Recommandé** — Idéal pour les jeux multijoueurs et discussions en direct |
| **gemini-3.5-flash-lite** | Batch Audio | Faible (< 1.2s) | 500 req / jour | Alternative puissante avec auto-détection universelle de la langue |
| **gemini-3.1-flash-lite** | Batch Audio | Faible | 500 req / jour | Solution économique et légère |
| **gemma-4-26b** | Batch Audio | Modérée | 14 400 req / jour | Usage intensif et gros volumes |

---

## **🔄 Flux de Traitement Séquentiel**

```text
[ Événement Hotkey Clavier / Bouton Manette ]
                    │
                    ▼
          1. Test Focus Texte Actif ?
             ├── NON ──► [ HUD : Alerte "Champ texte requis" ] ──► Fin
             └── OUI
                    │
                    ▼
          2. Baisse Master Volume (Audio Ducking ON)
                    │
                    ▼
          3. Ouverture Micro & Capture
             ├── [Azure Speech] ──► Streaming continu + affichage temporaire
             └── [Gemini]       ──► Enregistrement du buffer audio
                    │
                    ▼
          4. Traduction vers TARGET_LANG
                    │
                    ▼
          5. Injection Texte (Ctrl+V / Auto-Enter au curseur actif)
                    │
                    ▼
          6. Restauration Master Volume (Ducking OFF) & Reset HUD
```

---

## **⚙️ Paramètres de Configuration (`config.json`)**

Tous les paramètres sont modifiables directement depuis le volet Réglages du HUD ou via `config.json` :

```json
{
  "SPEECH_ENGINE": "azure",
  "AZURE_SPEECH_KEY": "VOTRE_CLE_AZURE",
  "AZURE_SPEECH_REGION": "francecentral",
  "AZURE_SOURCE_LANG": "fr-FR",
  "GEMINI_API_KEY": "",
  "GEMINI_MODEL": "gemini-3.5-flash-lite",
  "TARGET_LANG": "en",
  "RECORD_MODE": "hold",
  "HOTKEY": "f8",
  "GAMEPAD_BUTTON": "r_thumb",
  "AUTO_ENTER": true,
  "DUCKING_LEVEL": 0.5,
  "INJECTION_METHOD": "clipboard_paste",
  "SAMPLE_RATE": 16000,
  "FILTER_PROFANITY": false,
  "INPUT_DEVICE": null,
  "UI_LANG": "fr",
  "HUD_OPACITY": 0.95,
  "ALWAYS_ON_TOP": true,
  "SHOW_LANG_SELECTOR": false
}
```

---

## **🚀 Installation & Lancement Local (Windows)**

### **1. Prérequis**
* Windows 10 ou 11 (64-bit)
* Python 3.10 ou supérieur

### **2. Installation des Dépendances**
Dans une invite de commandes ou un terminal PowerShell :
```cmd
pip install -r requirements.txt
```

### **3. Lancement de l'Application (Mode Silencieux GUI Pur)**
* **Via le lanceur batch silencieux :**
  ```cmd
  run_speech_to_translate.bat
  ```
  *Le script installe les dépendances, génère le raccourci Bureau et démarre l'application via `pythonw.exe` sans aucune invite de commande d'arrière-plan.*
* **Ou directement en Python (Mode silencieux) :**
  ```cmd
  pythonw main.py
  # Pour afficher les logs en console de débogage :
  python main.py --debug
  ```

### **4. Compilation en Exécutable Autonome (.exe sans console)**
Pour générer un fichier `.exe` portable et silencieux via PyInstaller :
```cmd
pip install pyinstaller
pyinstaller --noconsole --onefile --windowed --icon=assets/STT2.ico --add-data "assets;assets" --add-data "help.html;." main.py
```

### **5. Configuration Initiale & Ergonomie**
1. **Assistant Premier Démarrage :** Une fenêtre interactive vous invite à choisir votre langue d'interface (**Français** ou **English**) avec mémorisation automatique.
2. **Réglage Transparence :** Ajustez l'opacité globale du HUD (de 30% à 100%) directement avec le curseur dédié dans les Réglages.
3. **Animation Micro :** L'icône centrale s'illumine d'un halo cyan pulsant en temps réel selon le niveau de votre voix.
4. **Déplacement Universel :** Cliquez et glissez sur la poignée ou n'importe quel espace vide des fenêtres pour repositionner le HUD à votre convenance.
5. Renseignez votre clé Azure Speech (ou Google AI Studio) dans les **Réglages (⚙️)**, puis commencez à dicter !