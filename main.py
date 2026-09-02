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

# Support Zone de notification Windows (Systray) via pystray & Pillow
try:
    import pystray
    from PIL import Image as PILImage
    PYSTRAY_AVAILABLE = True
except ImportError:
    PYSTRAY_AVAILABLE = False

# Chargement de la configuration .env
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.7-flash")
SOURCE_LANG = os.getenv("SOURCE_LANG", "fr").strip().lower() # 'fr', 'en', 'es', 'de', 'it', 'pt', 'ja', 'auto'
TARGET_LANG = os.getenv("TARGET_LANG", "en").strip().lower() # 'en', 'fr', 'es', 'de', 'it', 'pt', 'ja'
RECORD_MODE = os.getenv("RECORD_MODE", "hold").strip().lower() # "hold" (Push-To-Talk) ou "toggle" (Appuyer / Réappuyer)
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

if SOURCE_LANG == "auto":
    src_desc = "Détection Automatique"
else:
    src_desc = LANG_DESCRIPTIONS.get(SOURCE_LANG, SOURCE_LANG)
tgt_desc = LANG_DESCRIPTIONS.get(TARGET_LANG, TARGET_LANG)

# Formulations adaptées pour le prompt système Gemini
src_prompt_phrase = "dans une langue parlée automatiquement détectée" if SOURCE_LANG == "auto" else f"parlé en {src_desc}"

SYSTEM_INSTRUCTION = (
    f"Tu es un traducteur instantané pour joueur de jeu vidéo multijoueur (Forza Horizon 6, Xbox Game Bar). "
    f"Tu reçois un enregistrement audio {src_prompt_phrase}. "
    f"Ta seule tâche est de renvoyer le texte traduit directement en {tgt_desc} couramment utilisé dans les jeux vidéo en ligne "
    f"(slang gaming, vocabulaire de course automobile et de chat vocal entre amis). "
    f"Ne réponds JAMAIS à la phrase, ne rajoute aucun commentaire, ne mets aucun guillemet : renvoie uniquement la traduction brute."
)

# =====================================================================
# Gestion de la Fenêtre de Console Windows & Systray (Zone de Notification)
# =====================================================================
console_hwnd = None
is_console_visible = True
tray_icon_instance = None

if sys.platform == "win32":
    try:
        console_hwnd = ctypes.windll.kernel32.GetConsoleWindow()
    except Exception:
        pass

def set_console_icon(icon_rel_path: str = "ICO/dango_translate_icon.ico"):
    """Définit l'icône de la fenêtre de console Windows active via l'API Win32 (ctypes)."""
    if sys.platform != "win32" or not console_hwnd:
        return
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        full_path = os.path.join(base_dir, icon_rel_path)
        if not os.path.exists(full_path):
            for alt in [icon_rel_path, "dango_translate_icon_512.png", "icon.ico", "ICO/icon.ico"]:
                alt_full = os.path.join(base_dir, alt) if not os.path.isabs(alt) else alt
                if os.path.exists(alt_full):
                    full_path = alt_full
                    break

        if not os.path.exists(full_path):
            return

        IMAGE_ICON = 1
        LR_LOADFROMFILE = 0x00000010
        hicon_big = ctypes.windll.user32.LoadImageW(None, full_path, IMAGE_ICON, 32, 32, LR_LOADFROMFILE)
        hicon_small = ctypes.windll.user32.LoadImageW(None, full_path, IMAGE_ICON, 16, 16, LR_LOADFROMFILE)

        WM_SETICON = 0x0080
        ICON_SMALL = 0
        ICON_BIG = 1

        if hicon_small:
            ctypes.windll.user32.SendMessageW(console_hwnd, WM_SETICON, ICON_SMALL, hicon_small)
        if hicon_big:
            ctypes.windll.user32.SendMessageW(console_hwnd, WM_SETICON, ICON_BIG, hicon_big)
    except Exception:
        pass

def toggle_console_window(icon=None, item=None):
    """Masque ou réaffiche la fenêtre de console Windows active."""
    global is_console_visible
    if sys.platform != "win32" or not console_hwnd:
        return
    SW_HIDE = 0
    SW_SHOW = 5
    if is_console_visible:
        ctypes.windll.user32.ShowWindow(console_hwnd, SW_HIDE)
        is_console_visible = False
    else:
        ctypes.windll.user32.ShowWindow(console_hwnd, SW_SHOW)
        ctypes.windll.user32.SetForegroundWindow(console_hwnd)
        is_console_visible = True

def quit_app(icon=None, item=None):
    """Ferme l'application et l'icône de zone de notification."""
    print("\n[SYSTRAY] Arrêt de l'application...")
    if icon:
        try:
            icon.stop()
        except Exception:
            pass
    os._exit(0)

def setup_systray():
    """Initialise l'icône dans la zone de notification Windows avec pystray et Pillow."""
    global tray_icon_instance
    if not PYSTRAY_AVAILABLE or sys.platform != "win32":
        return None

    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        icon_candidates = [
            os.path.join(base_dir, "ICO", "dango_translate_icon.ico"),
            "ICO/dango_translate_icon.ico",
            os.path.join(base_dir, "dango_translate_icon_512.png"),
            "dango_translate_icon_512.png",
            os.path.join(base_dir, "icon.ico"),
            "icon.ico"
        ]
        img = None
        for p in icon_candidates:
            if os.path.exists(p):
                try:
                    img = PILImage.open(p)
                    break
                except Exception:
                    continue
        if img is None:
            img = PILImage.new("RGBA", (64, 64), color=(255, 42, 117, 255))

        menu = pystray.Menu(
            pystray.MenuItem("Afficher / Masquer", toggle_console_window, default=True),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quitter", quit_app)
        )

        tray_icon_instance = pystray.Icon(
            name="XboxVoiceTranslator",
            icon=img,
            title="Xbox Voice Translator (Forza / Game Bar)",
            menu=menu
        )

        tray_thread = threading.Thread(target=tray_icon_instance.run, daemon=True)
        tray_thread.start()
        return tray_icon_instance
    except Exception as e:
        print(f"[⚠️ SYSTRAY] Notification tray non initialisée : {e}")
        return None

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
        prev_clipboard = pyperclip.paste()
        try:
            pyperclip.copy(text)
            time.sleep(0.05)
            with kb_controller.pressed(keyboard.Key.ctrl):
                kb_controller.press('v')
                kb_controller.release('v')
            time.sleep(0.05)
        finally:
            pass
    else:
        kb_controller.type(text)

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
        audio_data = np.concatenate(recorded_frames, axis=0)
        audio_int16 = (audio_data * 32767).astype(np.int16)
        
        wav_io = io.BytesIO()
        wavfile.write(wav_io, SAMPLE_RATE, audio_int16)
        wav_bytes = wav_io.getvalue()

        user_prompt = (
            f"Translate this spoken audio into natural, authentic {tgt_desc} for Forza Horizon 6 / Xbox chat. Return ONLY the raw translated text."
            if SOURCE_LANG == "auto"
            else f"Translate this spoken {src_desc} into natural, authentic {tgt_desc} for Forza Horizon 6 / Xbox chat. Return ONLY the raw translated text."
        )

        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=[
                types.Part.from_bytes(
                    data=wav_bytes,
                    mime_type="audio/wav",
                ),
                user_prompt,
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
        if RECORD_MODE == "toggle":
            if not is_recording:
                is_recording = True
                audio_buffer = []
                print(f"\n[🔴 ENREGISTREMENT - TOGGLE ACTIF] Parlez ({src_desc})... Appuyez à nouveau sur [{HOTKEY_STR.upper()}] pour traduire & envoyer.", flush=True)
            else:
                is_recording = False
                print(f"\n[⏹️ STOP] Touche pressée. Analyse & Traduction...")
                if len(audio_buffer) > 0:
                    audio_queue.put(list(audio_buffer))
                    audio_buffer = []
        else:
            # Mode "hold" (Push-To-Talk standard)
            if not is_recording:
                is_recording = True
                audio_buffer = []
                print(f"\n[🔴 ENREGISTREMENT EN COURS] Parlez ({src_desc})... (Maintenez [{HOTKEY_STR.upper()}])", end="", flush=True)

def on_release(key):
    global is_recording, audio_buffer
    if match_hotkey(key):
        if RECORD_MODE == "toggle":
            # En mode toggle, relâcher la touche ne stoppe pas l'enregistrement
            return
        else:
            # Mode "hold" : relâcher stoppe l'enregistrement
            if is_recording:
                is_recording = False
                print(f"\n[⏹️ STOP] Touche relâchée. Analyse...")
                if len(audio_buffer) > 0:
                    audio_queue.put(list(audio_buffer))
                    audio_buffer = []

def gamepad_poller_thread():
    """Sonde l'état de la manette Xbox à intervalles rapides (50 Hz) sans saturer le CPU."""
    global is_recording, audio_buffer
    was_pressed = False
    while True:
        try:
            pressed = is_gamepad_hotkey_pressed()
            if RECORD_MODE == "toggle":
                if pressed and not was_pressed:
                    if not is_recording:
                        is_recording = True
                        audio_buffer = []
                        print(f"\n[🔴 MANETTE XBOX - TOGGLE ACTIF] Parlez ({src_desc})... Réappuyez sur [{GAMEPAD_HOTKEY.upper()}] pour envoyer.", flush=True)
                    else:
                        is_recording = False
                        print(f"\n[⏹️ MANETTE - STOP] Bouton pressé. Analyse...")
                        if len(audio_buffer) > 0:
                            audio_queue.put(list(audio_buffer))
                            audio_buffer = []
            else:
                # Mode "hold"
                if pressed and not was_pressed:
                    if not is_recording:
                        is_recording = True
                        audio_buffer = []
                        print(f"\n[🔴 MANETTE XBOX - ENREGISTREMENT] Parlez ({src_desc})... (Maintenez [{GAMEPAD_HOTKEY.upper()}])", end="", flush=True)
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
        time.sleep(0.02) # 20 ms polling (50 Hz)

def main():
    # 1. Attribution de l'icône Dango à la fenêtre de console Windows active (ctypes)
    set_console_icon("ICO/dango_translate_icon.ico")

    # 2. Initialisation de l'icône dans la zone de notification (Systray)
    setup_systray()

    mode_label = "Toggle (Appuyer pour démarrer / Réappuyer pour envoyer)" if RECORD_MODE == "toggle" else "Hold (Push-To-Talk - Maintenir pour parler)"

    print("=" * 70)
    print("🎮  XBOX GAME BAR / FORZA HORIZON - TRADUCTEUR VOCAL INSTANTANÉ")
    print(f"🌐  Langues : {src_desc} ➔ {tgt_desc}")
    print("=" * 70)
    print(f"🎙️  Microphone actif : {sd.query_devices(kind='input')['name']}")
    print(f"🔄  Mode d'enregistrement : {mode_label}")
    if RECORD_MODE == "toggle":
        print(f"⌨️  Raccourci Clavier : Touche [{HOTKEY_STR.upper()}] (Appuyer / Réappuyer)")
        if GAMEPAD_HOTKEY != "none":
            print(f"🎮  Raccourci Manette : Bouton [{GAMEPAD_HOTKEY.upper()}] (Appuyer / Réappuyer)")
    else:
        print(f"⌨️  Raccourci Clavier Push-To-Talk : Touche [{HOTKEY_STR.upper()}] (Maintenir)")
        if GAMEPAD_HOTKEY != "none":
            print(f"🎮  Raccourci Manette Xbox : Bouton [{GAMEPAD_HOTKEY.upper()}] (Maintenir)")
    print(f"⚙️  Envoi automatique [Entrée] : {'Oui' if AUTO_ENTER else 'Non'}")
    print(f"📋  Mode d'injection : {INJECTION_METHOD}")
    if PYSTRAY_AVAILABLE and sys.platform == "win32":
        print("📌  Zone de notification : Icône Dango active dans le Systray (Clic droit > Afficher / Masquer)")
    elif not PYSTRAY_AVAILABLE:
        print("💡  Astuce : Installez 'pystray' et 'Pillow' (pip install pystray Pillow) pour activer la réduction dans le systray.")
    print("-" * 70)
    print("💡 INSTRUCTIONS :")
    print("1. Ouvrez Forza Horizon 6 et le widget 'Conversation Xbox' (Win + G).")
    print("2. Cliquez dans le champ d'écriture Xbox pour y placer votre curseur.")
    if RECORD_MODE == "toggle":
        print(f"3. Appuyez une fois sur [{HOTKEY_STR.upper()}] (ou manette [{GAMEPAD_HOTKEY.upper()}]), parlez ({src_desc}), puis réappuyez pour envoyer.")
    else:
        print(f"3. Maintenez [{HOTKEY_STR.upper()}] au clavier OU bouton [{GAMEPAD_HOTKEY.upper()}] sur manette, parlez, puis relâchez.")
    print(f"4. Le texte est traduit instantanément en {tgt_desc} et tapé/collé dans le chat !")
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
