# **🎙️ Speech to Translate — AI Voice Translator & Traducteur Vocal**

Un utilitaire Windows autonome et universel fonctionnant en arrière-plan avec un HUD discret (style Windows dictée Win \+ H). Il permet de traduire et dicter votre voix en direct via l'API Gemini ou Gemma, directement dans le champ texte actif de vos applications et jeux (Discord, WhatsApp, Word, Notepad, Forza, etc.).

## **📐 Architecture & Principes Fondamentaux**

Le projet repose sur trois piliers d'ingénierie stricts :

1. **Auto-détection intégrale :** Aucune sélection de langue d'entrée. L'IA détecte automatiquement la langue parlée et la traduit vers la **Langue Cible** configurée (TARGET\_LANG).  
2. **Garde-fou de Focus Texte :** L'application vérifie la présence d'un champ de saisie éditable actif sous Windows avant toute capture audio pour éviter les envois "dans le vide" et la consommation inutile de quotas.  
3. **Fonction de déclenchement unifiée :** L'ensemble des événements (raccourcis clavier PTT/Toggle ou boutons de manette Xbox) appellent un point d'entrée unique (declencher\_action\_micro()).

## **🛠️ Fonctionnalités Clés**

* **HUD Flottant & Panneau de Réglages Déroulant (Flyout) :**  
  * Overlay flottant minimaliste (style Win \+ H) affichant l'état en temps réel via un égaliseur vectoriel réactif (5 colonnes de points animées selon l'amplitude du micro).  
  * **Roue crantée (Paramètres) :** Déplie un panneau de configuration intégré au HUD pour modifier les clés API, les langues cibles, l'atténuation sonore et les raccourcis sans ouvrir de navigateur.  
  * **Bouton Aide (?) :** Affiche la documentation et le guide rapide directement dans un volet du HUD.  
* **Détection automatique de la langue parlée :** Dites n'importe quoi (Français, Espagnol, Allemand, Japonais...), l'IA comprend et traduit automatiquement vers la langue cible paramétrée (TARGET\_LANG=en, fr, es...).  
* **Contrôle dynamique du Focus Texte (Focus Check) :**  
  * Interroge l'API Windows (UI Automation / Win32) dès la pression du raccourci.  
  * Si aucun champ de saisie n'est ciblé, le traitement s'arrête immédiatement avec une alerte visuelle sur le HUD.  
* **Audio Ducking Master synchrone :**  
  * Atténuation automatique du volume principal de Windows (Master Volume via pycaw) pendant la durée exacte de l'enregistrement micro.  
  * Restauration instantanée du volume dès la fin de la capture.  
* **Modes d'enregistrement flexibles :**  
  * hold (Push-To-Talk) : Maintenez la touche/bouton enfoncé(e) pour parler, relâchez pour traduire.  
  * toggle : Appuyez une fois pour lancer la capture, réappuyez pour finaliser et traduire.  
* **Zone de notification Windows (Systray) :**  
  * Réduction invisible dans la barre des tâches à côté de l'horloge avec menu rapide (*Paramètres*, *Masquer/Afficher*, *Quitter*).  
* **Injection universelle de texte :** Saisie automatique du texte traduit dans le champ actif (Ctrl+V) avec option de validation automatique (AUTO\_ENTER).

## **🤖 Modèles IA Supportés**

| Modèle | Quota Req/Min (RPM) | Quota Req/Jour (RPD) | Usage Recommandé |
| :---- | :---- | :---- | :---- |
| **gemini-3.5-flash-lite** | 15 | 500 | **Recommandé** — Parfait pour de longues sessions de jeu |
| **gemini-3.1-flash-lite** | 15 | 500 | Très rapide et quotas généreux |
| **gemma-4-26b** | 30 | 14 400 | Usage intensif et haut débit |

## **🔄 Flux de Traitement Séquentiel (Pipeline declencher\_action\_micro)**

Tout déclenchement (Clavier ou Gamepad) exécute strictement la séquence synchrone suivante :

\[ Événement Hotkey / Gamepad \]  
              │  
              ▼  
    1\. Test Focus Texte Actif ? ──► NON ──► \[ HUD : Alerte "Champ texte requis" \] ──► Fin  
              │  
             OUI  
              ▼  
    2\. Baisse Master Volume (Ducking ON)  
              │  
              ▼  
    3\. Ouverture Micro & Capture Audio (HUD : Animation égaliseur 30 FPS)  
              │  
              ▼  
    4\. Envoi Audio à Gemini / Gemma (Auto-détection ──► Traduction TARGET\_LANG)  
              │  
              ▼  
    5\. Injection Texte (\`Ctrl+V\` / Auto-Enter)  
              │  
              ▼  
    6\. Restauration Master Volume (Ducking OFF) & Reset HUD

## **🚀 Lancement & Déploiement**

### **Exécution autonome (.exe)**

Double-cliquez sur SpeechToTranslate.exe. L'application se loge en Systray et affiche le HUD au premier raccourci activé. Tout le paramétrage s'effectue via le menu déroulant de la roue crantée du HUD.