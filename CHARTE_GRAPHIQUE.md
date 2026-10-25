# Spécifications UI/UX et Charte Graphique : Speech to Translate (STT)

Ce document décrit l'interface utilisateur (UI), l'expérience utilisateur (UX) et les comportements attendus pour l'application "Speech to Translate" (STT). L'interface s'inspire de l'outil de dictée natif de Windows (`Win + H`) tout en l'adaptant spécifiquement pour une interaction avec les modèles Gemini.

---

## 1. Interface Principale (Fenêtre de Dictée)

### Disposition et Structure

L'interface est une capsule flottante minimaliste (overlay) visible en permanence, sans bordure de fenêtre native Windows (`Qt.FramelessWindowHint`), dotée d'une icône de fenêtre spécifique (`assets/STT2.ico`) et d'une mini-barre de titre supérieure intégrée (inspirée du modèle Windows `Win + H`).

* **Mini-barre de titre supérieure :**
* Une **poignée de déplacement horizontale centrale** permettant le glisser-déposer fluide de la capsule sur le bureau sans conflit avec les clics sur les boutons.
* Une **croix de fermeture (`X`)** explicite (avec effet de survol rouge vif) exécutant la fermeture propre et immédiate de l'application (`QApplication.quit()`).


* **Zone des boutons principaux (en bas) :**
1. **Bouton Gauche :** `assets/setting.svg` (Accès direct au panneau des paramètres).


2. **Bouton Central :** `assets/Google_Ai_vector_Logo.svg` (Icône principale d'enregistrement, composée de cercles colorés formant un hexagone abstrait).


3. **Bouton Droit :** `assets/HelpG.svg` (Accès direct au menu d'aide).





### Comportement au lancement

* **Aucun enregistrement automatique :** Contrairement à `Win + H` (qui enregistre dès l'apparition si un champ texte est ciblé), STT démarre la fenêtre en état de veille (*idle*) sans débuter l'enregistrement automatiquement.


* *Raisonnement :* L'application pouvant être lancée via un exécutable (double-clic), un enregistrement automatique risquerait de s'activer alors que le focus sur le champ de texte désiré a été perdu.



### Animation en cours de dictée (Icône Centrale)

* L'icône centrale (`assets/Google_Ai_vector_Logo.svg`) doit être dynamique et réagir à l'entrée audio en temps réel (volume/intonation).


* **Effet visuel attendu :**
* Les cercles constituant l'icône s'animent pour former une "onde" visuelle via des variations coordonnées de taille et de position.


* Un léger effet de lueur externe (*outer glow*) s'active pour signaler visuellement que le microphone est en écoute active.





---

## 2. Menu des Paramètres (Settings)

Le menu des paramètres s'intègre directement dans l'ergonomie applicative du HUD pour centraliser l'ensemble des configurations.

### Style Visuel

* Un design épuré, lisible et ergonomique, s'inspirant des standards des paramètres Windows modernes.


* **Composants UI requis :**
* Interrupteurs (*toggles*) pour les options booléennes.
* Champs de texte pour les saisies (clés API, configurations).
* Menus déroulants (*selects*) pour les choix de modèles et de langues.
* Curseur progressif (*slider*) pour les réglages de niveau.



### Options à intégrer

1. **Clé GEMINI_API_KEY :** Champ texte sécurisé pour la clé d'authentification.


2. **Modèle IA :** Menu déroulant listant les modèles supportés (ex: `gemini-3.5-flash-lite`).


3. **Langue traduite (Cible) :** Menu déroulant de sélection de la langue de sortie (`TARGET_LANG`).


4. **Mode d'enregistrement (Microphone) :** Menu déroulant (`hold` / `toggle`).


5. **Raccourci Clavier (HOTKEY) :** Champ texte interactif capturant la frappe au clavier.


6. **Bouton Manette (GAMEPAD_BUTTON) :**
* *Comportement UX spécifique :* L'interface intègre un mode d'écoute active pour capturer directement l'appui sur le bouton physique de la manette sans saisie manuelle.


* *Mention obligatoire :* Indiquer explicitement la compatibilité exclusive avec les manettes Microsoft (X-input).




7. **Comportement d'envoi du message :** Option ou interrupteur pour l'envoi automatique avec la touche Entrée après l'injection (`AUTO_ENTER`).
8. **Niveau de Ducking Audio (Atténuation du son Windows) :** Curseur gradué de 0 à 100%.


9. **Filtrer le langage inadapté :** Interrupteur d'activation du filtrage de contenu.


10. **Sélectionner le microphone par défaut :** Menu déroulant énumérant les périphériques audio disponibles sur le système.



---

## 3. Menu d'Aide (Help)

L'accès au menu d'aide (`assets/HelpG.svg`) charge la documentation essentielle de l'application.

### Contenu Requis

* **Obtenir une clé API :** Guide pas à pas et lien direct vers la création d'une clé gratuite sur Google AI Studio.


* **Limites des modèles IA :** Rappel des quotas (requêtes par minute et par jour) et recommandations d'usage.


* **Langues prises en charge :** Liste des langues avec une architecture évolutive.


* **Mode d'emploi rapide :** Résumé synthétique du workflow (sélectionner un champ texte -> maintenir le raccourci -> parler -> relâcher pour traduire et insérer).


* **Liens utiles :** Accès direct au dépôt GitHub du projet et au fichier `README.md`.