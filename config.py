import os
import sys
import json
import ctypes
import webbrowser
from typing import Dict, Any, Optional

# =====================================================================
# CENTRALISATION DE LA CONFIGURATION (config.json) & PORTABILITÉ .EXE
# =====================================================================
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
    BUNDLE_DIR = getattr(sys, '_MEIPASS', BASE_DIR)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    BUNDLE_DIR = BASE_DIR

CONFIG_PATH = os.path.join(BASE_DIR, "config.json")

HELP_PATH = os.path.join(BASE_DIR, "help.html")
if not os.path.exists(HELP_PATH) and os.path.exists(os.path.join(BUNDLE_DIR, "help.html")):
    HELP_PATH = os.path.join(BUNDLE_DIR, "help.html")

ASSETS_DIR = os.path.join(BASE_DIR, "assets")
if not os.path.exists(ASSETS_DIR) and os.path.exists(os.path.join(BUNDLE_DIR, "assets")):
    ASSETS_DIR = os.path.join(BUNDLE_DIR, "assets")

ICON_ICO_PATH = os.path.join(ASSETS_DIR, "STT2.ico")
SVG_SETTING_PATH = os.path.join(ASSETS_DIR, "setting.svg")
SVG_MIC_PATH = os.path.join(ASSETS_DIR, "Google_Ai_vector_Logo.svg")
SVG_HELP_PATH = os.path.join(ASSETS_DIR, "HelpG.svg")

DEFAULT_CONFIG: Dict[str, Any] = {
    "GEMINI_API_KEY": "",
    "GEMINI_MODEL": "gemini-3.5-flash-lite",
    "TARGET_LANG": "en",
    "RECORD_MODE": "hold",
    "HOTKEY": "f8",
    "GAMEPAD_BUTTON": "r_thumb",
    "AUTO_ENTER": True,
    "DUCKING_LEVEL": 0.5,
    "INJECTION_METHOD": "clipboard_paste",
    "SAMPLE_RATE": 16000,
    "FILTER_PROFANITY": False,
    "INPUT_DEVICE": None,
    "UI_LANG": "fr"
}

def load_config() -> Dict[str, Any]:
    if not os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(DEFAULT_CONFIG, f, indent=2, ensure_ascii=False)
            print("[CONFIG] Fichier 'config.json' généré avec les paramètres par défaut.")
        except Exception as e:
            print(f"[CONFIG] Erreur de création de config.json : {e}")
        return DEFAULT_CONFIG.copy()

    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            merged = DEFAULT_CONFIG.copy()
            merged.update(data)
            return merged
    except Exception as e:
        print(f"[CONFIG] Erreur de lecture de config.json : {e}. Utilisation des paramètres par défaut.")
        return DEFAULT_CONFIG.copy()

def save_config(cfg: Dict[str, Any]) -> bool:
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"[CONFIG] Erreur d'écriture dans config.json : {e}")
        return False

CONFIG = load_config()

GEMINI_API_KEY = CONFIG.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = CONFIG.get("GEMINI_MODEL", "gemini-3.5-flash-lite")
TARGET_LANG = str(CONFIG.get("TARGET_LANG", "en")).strip().lower()
RECORD_MODE = str(CONFIG.get("RECORD_MODE", "hold")).strip().lower()
HOTKEY_STR = str(CONFIG.get("HOTKEY", "f8")).lower()
GAMEPAD_BUTTON = str(CONFIG.get("GAMEPAD_BUTTON", "r_thumb")).lower()
AUTO_ENTER = bool(CONFIG.get("AUTO_ENTER", True))
INJECTION_METHOD = str(CONFIG.get("INJECTION_METHOD", "clipboard_paste")).lower()
SAMPLE_RATE = int(CONFIG.get("SAMPLE_RATE", 16000))
DUCKING_LEVEL = float(CONFIG.get("DUCKING_LEVEL", 0.5))
UI_LANG = str(CONFIG.get("UI_LANG", "fr")).lower()
CHANNELS = 1

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

def get_tgt_desc():
    return LANG_DESCRIPTIONS.get(TARGET_LANG, TARGET_LANG)

def open_help_documentation():
    target_url = HELP_PATH
    if not os.path.exists(target_url):
        target_url = "help.html"
    try:
        webbrowser.open(f"file://{os.path.abspath(target_url)}")
    except Exception as e:
        print(f"[AIDE] Erreur ouverture navigateur : {e}")

MESSAGES_I18N = {
    "fr": {
        "err_key_missing": "\n[ATTENTION] GEMINI_API_KEY n'est pas configurée dans config.json !\nConsultez l'aide (help.html) pour obtenir une clé gratuite.",
        "press_enter_exit": "Appuyez sur Entrée pour continuer...",
        "ducking_err": "[⚠️ DUCKING] Erreur : {}",
        "ducking_restore_err": "[⚠️ DUCKING] Erreur de restauration : {}",
        "focus_error": "\n[⚠️ FOCUS] Aucun champ texte éditable actif détecté. Action annulée.",
        "injection_sending": "\n[🚀 INJECTION] Envoi vers le champ texte ciblé : \"{}\"",
        "enter_validated": "  -> Touche [Entrée] validée !",
        "pipeline_ducking": "\n[⚡ PIPELINE] 1/6 - Atténuation Master Volume Windows (Ducking)...",
        "pipeline_rec_start": "[⚡ PIPELINE] 2/6 - Enregistrement micro en cours... ({})",
        "pipeline_rec_stop": "[⚡ PIPELINE] 2/6 - Enregistrement terminé. Traitement de l'audio...",
        "pipeline_sending": "[⚡ PIPELINE] 3/6 - Envoi de l'audio à l'API Gemini ({})...",
        "pipeline_injecting": "[⚡ PIPELINE] 4/6 - Injection du texte dans le champ activement ciblé...",
        "pipeline_restoring": "[⚡ PIPELINE] 5/6 - Restauration du volume Master Windows...",
        "success_trans": "[✅ SUCCÈS ({}s | {})] Traduction : \"{}\"",
        "no_speech": "[⚠️ INFO] Aucune parole détectée ou réponse vide.",
        "api_err": "[❌ ERREUR API] {}",
        "rec_toggle_start": "Parlez... Réappuyez sur [{}] pour envoyer.",
        "rec_ptt_start": "Parlez... (Maintenez [{}])",
        "stop_app": "\nArrêt de Speech to Translate.",
        "banner_title": "  SPEECH TO TRANSLATE - TRADUCTEUR VOCAL IA (HUD Win + H)",
        "banner_lang": "  Langue Cible (Traduction) : {}",
        "banner_mode": "  Mode : {}",
        "banner_mode_toggle": "Toggle (Appuyer / Réappuyer)",
        "banner_mode_ptt": "Hold / Push-To-Talk (Maintenir)",
        "banner_ducking": "  Ducking Audio Master : {}% d'atténuation",
        "banner_hotkeys": "  Clavier : [{}] | Manette : [{}]",
        "banner_ready": "Prêt ! Actionnez votre raccourci pour parler et traduire... (HUD Win + H actif)\n",
    },
    "en": {
        "err_key_missing": "\n[WARNING] GEMINI_API_KEY is not set in config.json!\nSee help.html to obtain a free API key.",
        "press_enter_exit": "Press Enter to continue...",
        "ducking_err": "[⚠️ DUCKING] Error: {}",
        "ducking_restore_err": "[⚠️ DUCKING] Restore error: {}",
        "focus_error": "\n[⚠️ FOCUS] No active editable text field detected. Action aborted.",
        "injection_sending": "\n[🚀 INJECTION] Sending to targeted text field: \"{}\"",
        "enter_validated": "  -> [Enter] key pressed!",
        "pipeline_ducking": "\n[⚡ PIPELINE] 1/6 - Windows Master Volume Ducking...",
        "pipeline_rec_start": "[⚡ PIPELINE] 2/6 - Microphone recording... ({})",
        "pipeline_rec_stop": "[⚡ PIPELINE] 2/6 - Recording finished. Audio processing...",
        "pipeline_sending": "[⚡ PIPELINE] 3/6 - Sending audio to Gemini API ({})...",
        "pipeline_injecting": "[⚡ PIPELINE] 4/6 - Injecting text into targeted text field...",
        "pipeline_restoring": "[⚡ PIPELINE] 5/6 - Restoring Windows Master Volume...",
        "success_trans": "[✅ SUCCESS ({}s | {})] Translation: \"{}\"",
        "no_speech": "[⚠️ INFO] No speech detected or empty response.",
        "api_err": "[❌ API ERROR] {}",
        "rec_toggle_start": "Speak... Press [{}] again to send.",
        "rec_ptt_start": "Speak... (Hold [{}])",
        "stop_app": "\nStopping Speech to Translate.",
        "banner_title": "  SPEECH TO TRANSLATE - AI VOICE TRANSLATOR (Win + H HUD)",
        "banner_lang": "  Target Language (Translation): {}",
        "banner_mode": "  Mode: {}",
        "banner_mode_toggle": "Toggle (Press / Press again)",
        "banner_mode_ptt": "Hold / Push-To-Talk (Hold)",
        "banner_ducking": "  Master Audio Ducking: {}% attenuation",
        "banner_hotkeys": "  Keyboard: [{}] | Gamepad: [{}]",
        "banner_ready": "Ready! Trigger your hotkey to speak and translate... (Win + H HUD active)\n",
    }
}

def get_msg(key: str, *args) -> str:
    lang = UI_LANG if UI_LANG in MESSAGES_I18N else "fr"
    msg_template = MESSAGES_I18N[lang].get(key, MESSAGES_I18N["en"].get(key, ""))
    return msg_template.format(*args)

def log_msg(key: str, *args):
    print(get_msg(key, *args))

def set_console_icon(icon_rel_path: str = "assets/STT2.ico"):
    if sys.platform != "win32":
        return
    try:
        console_hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if not console_hwnd:
            return
        full_path = os.path.join(BASE_DIR, icon_rel_path)
        if not os.path.exists(full_path):
            full_path = os.path.join(BUNDLE_DIR, icon_rel_path)
        if not os.path.exists(full_path):
            return
        IMAGE_ICON = 1
        LR_LOADFROMFILE = 0x00000010
        hicon_small = ctypes.windll.user32.LoadImageW(None, full_path, IMAGE_ICON, 16, 16, LR_LOADFROMFILE)
        hicon_big = ctypes.windll.user32.LoadImageW(None, full_path, IMAGE_ICON, 32, 32, LR_LOADFROMFILE)
        if hicon_small:
            ctypes.windll.user32.SendMessageW(console_hwnd, 0x0080, 0, hicon_small)
        if hicon_big:
            ctypes.windll.user32.SendMessageW(console_hwnd, 0x0080, 1, hicon_big)
    except Exception:
        pass

# Global states for actions
is_action_in_progress = False
action_lock = None # Will be initialized as threading.Lock() in main
stop_toggle_recording = None # Will be threading.Event()
key_pressed_state = False
hud_window = None

try:
    from PyQt6.QtCore import pyqtSignal, QObject
    PYQT6_AVAILABLE = True
except ImportError:
    PYQT6_AVAILABLE = False

class HUDBridge(QObject if PYQT6_AVAILABLE else object):
    if PYQT6_AVAILABLE:
        state_changed = pyqtSignal(str)
        volume_level = pyqtSignal(float)
    else:
        state_changed = None
        volume_level = None

hud_bridge = HUDBridge() if PYQT6_AVAILABLE else None

class AppNotifier:
    @staticmethod
    def notify_focus_error():
        log_msg("focus_error")
        if hud_bridge and hud_bridge.state_changed:
            hud_bridge.state_changed.emit("focus_error")

    @staticmethod
    def notify_ducking_start():
        log_msg("pipeline_ducking")

    @staticmethod
    def notify_recording_start(mode: str, hotkey: str):
        sub = get_msg("rec_toggle_start", hotkey) if mode == "toggle" else get_msg("rec_ptt_start", hotkey)
        log_msg("pipeline_rec_start", sub)
        if hud_bridge and hud_bridge.state_changed:
            hud_bridge.state_changed.emit("recording")

    @staticmethod
    def notify_recording_stop():
        log_msg("pipeline_rec_stop")
        if hud_bridge and hud_bridge.state_changed:
            hud_bridge.state_changed.emit("processing")

    @staticmethod
    def notify_api_sending(model_name: str):
        log_msg("pipeline_sending", model_name)

    @staticmethod
    def notify_translation_success(latency: float, model_name: str, text: str):
        log_msg("success_trans", latency, model_name, text)
        if hud_bridge and hud_bridge.state_changed:
            hud_bridge.state_changed.emit("idle")

    @staticmethod
    def notify_injection():
        log_msg("pipeline_injecting")

    @staticmethod
    def notify_ducking_restore():
        log_msg("pipeline_restoring")

    @staticmethod
    def notify_empty_speech():
        log_msg("no_speech")
        if hud_bridge and hud_bridge.state_changed:
            hud_bridge.state_changed.emit("idle")

    @staticmethod
    def notify_error(err):
        log_msg("api_err", err)
        if hud_bridge and hud_bridge.state_changed:
            hud_bridge.state_changed.emit("error")
