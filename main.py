"""
Xbox Game Bar / Forza Horizon - Traducteur Vocal Push-to-Talk (FR -> EN)
========================================================================
Auteur: Google AI Studio Build Assistant
Description: Intercepte la voix en français dès qu'une touche (ex: F8) est maintenue,
envoie l'audio à Gemini via l'API ultra-rapide, traduit en anglais gamer authentique,
et tape ou colle automatiquement le texte dans le champ de conversation Xbox Game Bar actif.
"""

import os
import io
import sys
import time
import queue
import tempfile
import threading
import ctypes
from dotenv import load_dotenv
import numpy as np
import sounddevice as sd
from scipy.io import wavfile
from pynput import keyboard
import pyperclip
from google import genai
from google.genai import types

# Chargement de la configuration .env
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.7-flash")
SOURCE_LANG = os.getenv("SOURCE_LANG", "fr").strip().lower() # 'fr', 'en', 'es', 'de', 'it', 'pt', 'ja', 'auto'
TARGET_LANG = os.getenv("TARGET_LANG", "en").strip().lower() # 'en', 'fr', 'es', 'de', 'it', 'pt', 'ja'
HOTKEY_STR = os.getenv("HOTKEY", "f8").lower()
GAMEPAD_HOTKEY = os.getenv("GAMEPAD_HOTKEY", "r_thumb").lower() # 'r_thumb', 'l_thumb', 'back', 'start', 'r_shoulder', 'l_shoulder', 'a', 'b', 'x', 'y', 'lb_rs', 'none'
AUTO_ENTER = os.getenv("AUTO_ENTER", "true").lower() in ("true", "1", "yes", "oui")
INJECTION_METHOD = os.getenv("INJECTION_METHOD", "clipboard_paste").lower() # "clipboard_paste" ou "typewriter"
SAMPLE_RATE = int(os.getenv("SAMPLE_RATE", "16000"))
CHANNELS = 1

# =====================================================================
# Support Manette Xbox (XInput Officiel Windows via ctypes - Zéro Anti-Cheat)
# =====================================================================
XINPUT_GAMEPAD_DPAD_UP        = 0x0001
XINPUT_GAMEPAD_DPAD_DOWN      = 0x0002
XINPUT_GAMEPAD_DPAD_LEFT      = 0x0004
XINPUT_GAMEPAD_DPAD_RIGHT     = 0x0008
XINPUT_GAMEPAD_START          = 0x0010
XINPUT_GAMEPAD_BACK           = 0x0020
XINPUT_GAMEPAD_LEFT_THUMB     = 0x0040
XINPUT_GAMEPAD_RIGHT_THUMB    = 0x0080
XINPUT_GAMEPAD_LEFT_SHOULDER  = 0x0100
XINPUT_GAMEPAD_RIGHT_SHOULDER = 0x0200
XINPUT_GAMEPAD_A              = 0x1000
XINPUT_GAMEPAD_B              = 0x2000
XINPUT_GAMEPAD_X              = 0x4000
XINPUT_GAMEPAD_Y              = 0x8000

class XINPUT_GAMEPAD(ctypes.Structure):
    _fields_ = [
        ("wButtons", ctypes.c_ushort),
        ("bLeftTrigger", ctypes.c_ubyte),
        ("bRightTrigger", ctypes.c_ubyte),
        ("sThumbLX", ctypes.c_short),
        ("sThumbLY", ctypes.c_short),
        ("sThumbRX", ctypes.c_short),
        ("sThumbRY", ctypes.c_short),
    ]

class XINPUT_STATE(ctypes.Structure):
    _fields_ = [
        ("dwPacketNumber", ctypes.c_ulong),
        ("Gamepad", XINPUT_GAMEPAD),
    ]

# Chargement de la DLL XInput Windows
xinput_dll = None
for dll_name in ["xinput1_4.dll", "xinput1_3.dll", "xinput9_1_0.dll"]:
    try:
        xinput_dll = ctypes.windll.LoadLibrary(dll_name)
        break
    except Exception:
        continue

def is_gamepad_hotkey_pressed() -> bool:
    """Interroge l'état XInput de la manette sans hook ni injection mémoire."""
    if not xinput_dll or GAMEPAD_HOTKEY == "none":
        return False

    state = XINPUT_STATE()
    # Interroge le joueur 1 (index 0)
    res = xinput_dll.XInputGetState(0, ctypes.byref(state))
    if res != 0: # 0 = ERROR_SUCCESS, non-zéro si manette déconnectée
        return False

    buttons = state.Gamepad.wButtons

    if GAMEPAD_HOTKEY in ("r_thumb", "rs", "r3"):
        return bool(buttons & XINPUT_GAMEPAD_RIGHT_THUMB)
    elif GAMEPAD_HOTKEY in ("l_thumb", "ls", "l3"):
        return bool(buttons & XINPUT_GAMEPAD_LEFT_THUMB)
    elif GAMEPAD_HOTKEY in ("back", "view", "select"):
        return bool(buttons & XINPUT_GAMEPAD_BACK)
    elif GAMEPAD_HOTKEY in ("start", "menu"):
        return bool(buttons & XINPUT_GAMEPAD_START)
    elif GAMEPAD_HOTKEY in ("r_shoulder", "rb"):
        return bool(buttons & XINPUT_GAMEPAD_RIGHT_SHOULDER)
    elif GAMEPAD_HOTKEY in ("l_shoulder", "lb"):
        return bool(buttons & XINPUT_GAMEPAD_LEFT_SHOULDER)
    elif GAMEPAD_HOTKEY in ("lb_rs", "combo_lb_rs"):
        return bool((buttons & XINPUT_GAMEPAD_LEFT_SHOULDER) and (buttons & XINPUT_GAMEPAD_RIGHT_THUMB))
    elif GAMEPAD_HOTKEY in ("view_rb", "combo_view_rb"):
        return bool((buttons & XINPUT_GAMEPAD_BACK) and (buttons & XINPUT_GAMEPAD_RIGHT_SHOULDER))
    elif GAMEPAD_HOTKEY == "a":
        return bool(buttons & XINPUT_GAMEPAD_A)
    elif GAMEPAD_HOTKEY == "b":
        return bool(buttons & XINPUT_GAMEPAD_B)
    elif GAMEPAD_HOTKEY == "x":
        return bool(buttons & XINPUT_GAMEPAD_X)
    elif GAMEPAD_HOTKEY == "y":
        return bool(buttons & XINPUT_GAMEPAD_Y)
    return False

LANG_DESCRIPTIONS = {
    "fr": "French (Français)",
    "en": "American Gaming English (Anglais Gamer US)",
    "es": "Spanish (Español)",
    "de": "German (Deutsch)",
    "it": "Italian (Italiano)",
    "pt": "Portuguese (Português)",
    "ja": "Japanese (日本語)",
    "ko": "Korean (한국어)",
    "auto": "Auto-Detect spoken language",
}

if not GEMINI_API_KEY:
    print("\n[ERREUR] La clé GEMINI_API_KEY n'est pas définie !")
    print("Veuillez renseigner votre clé API dans le fichier .env (GEMINI_API_KEY=AIzaSy...)")
    print("Vous pouvez obtenir une clé gratuite sur https://aistudio.google.com\n")
    input("Appuyez sur Entrée pour quitter...")
    sys.exit(1)

# Initialisation du client Google GenAI
client = genai.Client(api_key=GEMINI_API_KEY)

src_desc = LANG_DESCRIPTIONS.get(SOURCE_LANG, SOURCE_LANG)
tgt_desc = LANG_DESCRIPTIONS.get(TARGET_LANG, TARGET_LANG)

SYSTEM_INSTRUCTION = (
    f"Tu es un traducteur instantané pour joueur de jeu vidéo multijoueur (Forza Horizon 6, Xbox Game Bar). "
    f"Tu reçois un enregistrement audio parlé en {src_desc}. "
    f"Ta seule tâche est de renvoyer le texte traduit directement en {tgt_desc} couramment utilisé dans les jeux vidéo en ligne "
    f"(slang gaming, vocabulaire de course automobile et de chat vocal entre amis). "
    f"Ne réponds JAMAIS à la phrase, ne rajoute aucun commentaire, ne mets aucun guillemet : renvoie uniquement la traduction brute."
)

# Variables globales d'état
is_recording = False
audio_buffer = []
audio_queue = queue.Queue()
kb_controller = keyboard.Controller()

def audio_callback(indata, frames, time_info, status):
    """Callback temps réel de sounddevice pour collecter les échantillons audio."""
    if status:
        pass
    if is_recording:
        audio_buffer.append(indata.copy())

def inject_text_into_active_window(text: str, press_enter: bool = True):
    """Injecte le texte traduit dans le champ actif de l'application Xbox Game Bar."""
    if not text:
        return

    print(f"\n[🚀 INJECTION] Envoi vers la boîte de dialogue Xbox : \"{text}\"")

    if INJECTION_METHOD == "clipboard_paste":
        # Méthode ultra-rapide et fiable (supporte tous les caractères sans décalage de layout clavier)
        prev_clipboard = pyperclip.paste()
        try:
            pyperclip.copy(text)
            time.sleep(0.05)
            # Simule Ctrl+V
            with kb_controller.pressed(keyboard.Key.ctrl):
                kb_controller.press('v')
                kb_controller.release('v')
            time.sleep(0.05)
        finally:
            # Optionnel : restauration du presse-papier après 500ms
            pass
    else:
        # Frappe simulant caractère par caractère
        kb_controller.type(text)

    # Simulation de la touche Entrée pour envoyer directement dans le chat Xbox
    if press_enter:
        time.sleep(0.08)
        kb_controller.press(keyboard.Key.enter)
        kb_controller.release(keyboard.Key.enter)
        print("  -> Touche [Entrée] pressée (Message envoyé !)")

def process_audio_and_translate(recorded_frames):
    """Traite l'audio capturé, l'envoie à Gemini et déclenche l'injection clavier."""
    if not recorded_frames:
        return

    start_time = time.time()
    print("\n[⚡ TRAITEMENT] Traduction en cours via Gemini...")

    try:
        # Concaténation des frames audio
        audio_data = np.concatenate(recorded_frames, axis=0)
        
        # Normalisation si nécessaire et conversion en WAV 16-bit PCM
        audio_int16 = (audio_data * 32767).astype(np.int16)
        
        # Encodage en mémoire WAV
        wav_io = io.BytesIO()
        wavfile.write(wav_io, SAMPLE_RATE, audio_int16)
        wav_bytes = wav_io.getvalue()

        # Appel API Gemini pour la traduction instantanée
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=[
                types.Part.from_bytes(
                    data=wav_bytes,
                    mime_type="audio/wav",
                ),
                f"Translate this spoken {src_desc} into natural, authentic {tgt_desc} for Forza Horizon 6 / Xbox chat. Return ONLY the raw translated text.",
            ],
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=0.2,
            )
        )

        translated_text = response.text.strip() if response and response.text else ""
        latency = round((time.time() - start_time), 2)

        if translated_text:
            print(f"[✅ SUCCÈS ({latency}s | {GEMINI_MODEL})] Traduction reçue : \"{translated_text}\"")
            inject_text_into_active_window(translated_text, press_enter=AUTO_ENTER)
        else:
            print("[⚠️ INFO] Aucune parole détectée ou réponse vide.")

    except Exception as e:
        print(f"[❌ ERREUR API] {e}")

def worker_thread():
    """Thread d'arrière-plan pour traiter les requêtes audio sans bloquer le clavier."""
    while True:
        frames = audio_queue.get()
        if frames is None:
            break
        process_audio_and_translate(frames)
        audio_queue.task_done()

# Démarrage du thread de traitement
worker = threading.Thread(target=worker_thread, daemon=True)
worker.start()

def match_hotkey(key) -> bool:
    """Vérifie si la touche pressée correspond au raccourci configuré."""
    try:
        if HOTKEY_STR == "f8" and key == keyboard.Key.f8:
            return True
        if HOTKEY_STR == "f9" and key == keyboard.Key.f9:
            return True
        if HOTKEY_STR == "f10" and key == keyboard.Key.f10:
            return True
        if HOTKEY_STR == "f7" and key == keyboard.Key.f7:
            return True
        if HOTKEY_STR == "f12" and key == keyboard.Key.f12:
            return True
        if HOTKEY_STR == "space" and key == keyboard.Key.space:
            return True
        if hasattr(key, 'char') and key.char and key.char.lower() == HOTKEY_STR:
            return True
    except Exception:
        pass
    return False

def on_press(key):
    global is_recording, audio_buffer
    if match_hotkey(key):
        if not is_recording:
            is_recording = True
            audio_buffer = []
            print(f"\n[🔴 ENREGISTREMENT EN COURS] Parlez en français... (Maintenez [{HOTKEY_STR.upper()}])", end="", flush=True)

def on_release(key):
    global is_recording, audio_buffer
    if match_hotkey(key):
        if is_recording:
            is_recording = False
            print(f"\n[⏹️ STOP] Touche relâchée. Analyse...")
            if len(audio_buffer) > 0:
                # Transmet une copie du buffer au worker
                audio_queue.put(list(audio_buffer))
                audio_buffer = []

def gamepad_poller_thread():
    """Sonde l'état de la manette Xbox à intervalles rapides (50 Hz) sans saturer le CPU."""
    global is_recording, audio_buffer
    was_pressed = False
    while True:
        try:
            pressed = is_gamepad_hotkey_pressed()
            if pressed and not was_pressed:
                if not is_recording:
                    is_recording = True
                    audio_buffer = []
                    print(f"\n[🔴 MANETTE XBOX - ENREGISTREMENT] Parlez... (Maintenez [{GAMEPAD_HOTKEY.upper()}])", end="", flush=True)
            elif not pressed and was_pressed:
                if is_recording:
                    is_recording = False
                    print(f"\n[⏹️ MANETTE - STOP] Bouton relâché. Analyse...")
                    if len(audio_buffer) > 0:
                        audio_queue.put(list(audio_buffer))
                        audio_buffer = []
            was_pressed = pressed
        except Exception:
            pass
        time.sleep(0.02) # 20 ms polling (50 Hz) - ultra réactif et 0.0% CPU

def main():
    print("=" * 70)
    print("🎮  XBOX GAME BAR / FORZA HORIZON - TRADUCTEUR VOCAL INSTANTANÉ (FR -> EN)")
    print("=" * 70)
    print(f"🎙️  Microphone actif : {sd.query_devices(kind='input')['name']}")
    print(f"⌨️  Raccourci Clavier Push-To-Talk : Touche [{HOTKEY_STR.upper()}] (Maintenir)")
    print(f"🎮  Raccourci Manette Xbox : Bouton [{GAMEPAD_HOTKEY.upper()}] (Maintenir)")
    print(f"⚙️  Envoi automatique [Entrée] : {'Oui' if AUTO_ENTER else 'Non'}")
    print(f"📋  Mode d'injection : {INJECTION_METHOD}")
    print("-" * 70)
    print("💡 INSTRUCTIONS :")
    print("1. Ouvrez Forza Horizon 6 et le widget 'Conversation Xbox' (Win + G).")
    print("2. Cliquez dans le champ d'écriture Xbox pour y placer votre curseur.")
    print(f"3. Maintenez [{HOTKEY_STR.upper()}] au clavier OU le bouton [{GAMEPAD_HOTKEY.upper()}] sur la manette, parlez, puis relâchez.")
    print("4. Le texte est traduit instantanément en anglais gaming et tapé dans le chat !")
    print("-" * 70)
    print("Prêt ! En attente de votre voix... (Appuyez sur Ctrl+C pour quitter)\n")

    # Démarrage du thread d'écoute manette si activé
    if GAMEPAD_HOTKEY != "none":
        gp_thread = threading.Thread(target=gamepad_poller_thread, daemon=True)
        gp_thread.start()

    # Démarrage du flux audio continu et du listener clavier
    with sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS, callback=audio_callback):
        with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
            listener.join()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nArrêt du traducteur. Bonne session de jeu sur Forza !")
        sys.exit(0)
