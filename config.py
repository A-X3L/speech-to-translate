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
SVG_HELP_PATH = os.path.join(ASSETS_DIR, "HelpR.svg")

DEFAULT_CONFIG: Dict[str, Any] = {
    "SPEECH_ENGINE": "azure",
    "AZURE_SPEECH_KEY": "",
    "AZURE_SPEECH_REGION": "francecentral",
    "AZURE_SOURCE_LANG": "fr-FR",
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
    "UI_LANG": "fr",
    "HUD_OPACITY": 0.95,
    "SHOW_LANG_SELECTOR": True,
    "ALWAYS_ON_TOP": True,
    "DOCK_EDGE": "top",
    "IS_MUTED": False
}

def load_config() -> Dict[str, Any]:
    if not os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(DEFAULT_CONFIG, f, indent=2, ensure_ascii=False)
            print("[CONFIG] Fichier 'config.json' généré avec les paramètres par défaut.")
        except Exception as e:
            print(f"[CONFIG] Erreur de création de config.json : {e}")
        cfg = DEFAULT_CONFIG.copy()
        cfg["SHOW_LANG_SELECTOR"] = True
        return cfg

    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            merged = DEFAULT_CONFIG.copy()
            merged.update(data)
            if "UI_LANG" not in data:
                merged["SHOW_LANG_SELECTOR"] = True
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

SPEECH_ENGINE = str(CONFIG.get("SPEECH_ENGINE", "azure")).strip().lower()
AZURE_SPEECH_KEY = CONFIG.get("AZURE_SPEECH_KEY") or os.getenv("AZURE_SPEECH_KEY", "")
AZURE_SPEECH_REGION = str(CONFIG.get("AZURE_SPEECH_REGION", "francecentral")).strip()
AZURE_SOURCE_LANG = str(CONFIG.get("AZURE_SOURCE_LANG", "fr-FR")).strip()

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
HUD_OPACITY = float(CONFIG.get("HUD_OPACITY", 0.95))
SHOW_LANG_SELECTOR = bool(CONFIG.get("SHOW_LANG_SELECTOR", True))
ALWAYS_ON_TOP = bool(CONFIG.get("ALWAYS_ON_TOP", True))
DOCK_EDGE = str(CONFIG.get("DOCK_EDGE", "top")).strip().lower()
if DOCK_EDGE not in ("top", "bottom", "left", "right"):
    DOCK_EDGE = "top"
IS_MUTED = bool(CONFIG.get("IS_MUTED", False))
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
    "ru": "Russian (Русский)",
    "zh": "Chinese Simplified (中文)",
    "auto": "Auto-Detect spoken language",
}

def get_tgt_desc() -> str:
    tl_str = str(TARGET_LANG).strip()
    tl_lower = tl_str.lower()
    if tl_lower in LANG_DESCRIPTIONS:
        return LANG_DESCRIPTIONS[tl_lower]
    base = tl_lower.split("-")[0].split("_")[0]
    if base in LANG_DESCRIPTIONS:
        return f"{LANG_DESCRIPTIONS[base]} ({tl_str})"
    return tl_str

def reload_runtime_config():
    """Recharge à chaud toutes les variables globales depuis CONFIG."""
    global SPEECH_ENGINE, AZURE_SPEECH_KEY, AZURE_SPEECH_REGION, AZURE_SOURCE_LANG
    global GEMINI_API_KEY, GEMINI_MODEL, TARGET_LANG, RECORD_MODE, HOTKEY_STR
    global GAMEPAD_BUTTON, AUTO_ENTER, INJECTION_METHOD, SAMPLE_RATE, DUCKING_LEVEL
    global UI_LANG, HUD_OPACITY, SHOW_LANG_SELECTOR, ALWAYS_ON_TOP, DOCK_EDGE, IS_MUTED
    
    SPEECH_ENGINE = str(CONFIG.get("SPEECH_ENGINE", "azure")).strip().lower()
    AZURE_SPEECH_KEY = CONFIG.get("AZURE_SPEECH_KEY") or os.getenv("AZURE_SPEECH_KEY", "")
    AZURE_SPEECH_REGION = str(CONFIG.get("AZURE_SPEECH_REGION", "francecentral")).strip()
    AZURE_SOURCE_LANG = str(CONFIG.get("AZURE_SOURCE_LANG", "fr-FR")).strip()

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
    HUD_OPACITY = float(CONFIG.get("HUD_OPACITY", 0.95))
    SHOW_LANG_SELECTOR = bool(CONFIG.get("SHOW_LANG_SELECTOR", True))
    ALWAYS_ON_TOP = bool(CONFIG.get("ALWAYS_ON_TOP", True))
    DOCK_EDGE = str(CONFIG.get("DOCK_EDGE", "top")).strip().lower()
    if DOCK_EDGE not in ("top", "bottom", "left", "right"):
        DOCK_EDGE = "top"
    IS_MUTED = bool(CONFIG.get("IS_MUTED", False))

def toggle_mute() -> bool:
    """Bascule l'état Mute global du microphone et notifie l'application."""
    global IS_MUTED
    IS_MUTED = not IS_MUTED
    CONFIG["IS_MUTED"] = IS_MUTED
    save_config(CONFIG)
    if hud_bridge and hasattr(hud_bridge, "mute_changed") and hud_bridge.mute_changed:
        hud_bridge.mute_changed.emit(IS_MUTED)
    return IS_MUTED

def set_mute(muted: bool):
    """Définit explicitement l'état Mute global."""
    global IS_MUTED
    IS_MUTED = bool(muted)
    CONFIG["IS_MUTED"] = IS_MUTED
    save_config(CONFIG)
    if hud_bridge and hasattr(hud_bridge, "mute_changed") and hud_bridge.mute_changed:
        hud_bridge.mute_changed.emit(IS_MUTED)

def set_ui_language(lang: str):
    global UI_LANG
    UI_LANG = lang.lower()
    CONFIG["UI_LANG"] = UI_LANG
    save_config(CONFIG)
    reload_runtime_config()

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
        "err_azure_key_missing": "\n[ATTENTION] AZURE_SPEECH_KEY n'est pas configurée dans config.json !\nRenseignez votre clé Azure Speech dans les réglages ou config.json.",
        "err_azure_sdk_missing": "\n[⚠️ MODULE AZURE ABSENT] Le package 'azure-cognitiveservices-speech' n'est pas installé.\nInstallez-le avec : pip install azure-cognitiveservices-speech",
        "pipeline_azure_start": "[⚡ AZURE STREAMING] Écoute continue et traduction temps réel démarrées...",
        "pipeline_azure_segment": "[✅ AZURE SUCCÈS] Traduction validée : \"{}\"",
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
        "banner_engine": "  Moteur : {}",
        "banner_lang": "  Langue Cible (Traduction) : {}",
        "banner_mode": "  Mode : {}",
        "banner_mode_toggle": "Toggle (Appuyer / Réappuyer)",
        "banner_mode_ptt": "Hold / Push-To-Talk (Maintenir)",
        "banner_ducking": "  Ducking Audio Master : {}% d'atténuation",
        "banner_hotkeys": "  Clavier : [{}] | Manette : [{}]",
        "banner_ready": "Prêt ! Actionnez votre raccourci pour parler et traduire... (HUD Win + H actif)\n",
        "lang_dialog_title": "Bienvenue / Welcome",
        "lang_dialog_prompt": "Choisissez la langue de l'interface :",
        "lang_dialog_remember": "Ne plus afficher au prochain démarrage",
        "lang_dialog_confirm": "Valider et Lancer",
        "settings_opacity": "Transparence HUD (Opacité : {}%)",
        "settings_input_device": "Microphone d'entrée :",
        "settings_input_default": "Microphone par défaut du système",
        "settings_dock_edge": "Bord d'ancrage à l'écran :",
        "dock_top": "Bord Haut (Supérieur)",
        "dock_bottom": "Bord Bas (Inférieur)",
        "dock_left": "Bord Gauche",
        "dock_right": "Bord Droit",
        "settings_workshop_title": "Atelier de Configuration",
        "help_workshop_title": "Atelier d'Aide & Guide",
    },
    "en": {
        "err_key_missing": "\n[WARNING] GEMINI_API_KEY is not set in config.json!\nSee help.html to obtain a free API key.",
        "err_azure_key_missing": "\n[WARNING] AZURE_SPEECH_KEY is not set in config.json!\nEnter your Azure Speech key in settings or config.json.",
        "err_azure_sdk_missing": "\n[⚠️ AZURE MODULE MISSING] Package 'azure-cognitiveservices-speech' is not installed.\nInstall it with: pip install azure-cognitiveservices-speech",
        "pipeline_azure_start": "[⚡ AZURE STREAMING] Continuous listening and real-time translation started...",
        "pipeline_azure_segment": "[✅ AZURE SUCCESS] Validated translation: \"{}\"",
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
        "banner_engine": "  Engine: {}",
        "banner_lang": "  Target Language (Translation): {}",
        "banner_mode": "  Mode: {}",
        "banner_mode_toggle": "Toggle (Press / Press again)",
        "banner_mode_ptt": "Hold / Push-To-Talk (Hold)",
        "banner_ducking": "  Master Audio Ducking: {}% attenuation",
        "banner_hotkeys": "  Keyboard: [{}] | Gamepad: [{}]",
        "banner_ready": "Ready! Trigger your hotkey to speak and translate... (Win + H HUD active)\n",
        "lang_dialog_title": "Welcome / Bienvenue",
        "lang_dialog_prompt": "Choose your interface language:",
        "lang_dialog_remember": "Do not show again on next startup",
        "lang_dialog_confirm": "Confirm & Launch",
        "settings_opacity": "HUD Transparency (Opacity: {}%)",
        "settings_input_device": "Input Microphone:",
        "settings_input_default": "System Default Microphone",
        "settings_dock_edge": "Screen Dock Edge:",
        "dock_top": "Top Edge",
        "dock_bottom": "Bottom Edge",
        "dock_left": "Left Edge",
        "dock_right": "Right Edge",
        "settings_workshop_title": "Configuration Workshop",
        "help_workshop_title": "Help & Guide Workshop",
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
        mute_changed = pyqtSignal(bool)
        target_lang_changed = pyqtSignal(str)
    else:
        state_changed = None
        volume_level = None
        mute_changed = None
        target_lang_changed = None

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
    def notify_azure_start():
        log_msg("pipeline_azure_start")
        if hud_bridge and hud_bridge.state_changed:
            hud_bridge.state_changed.emit("recording")

    @staticmethod
    def notify_azure_segment(text: str):
        log_msg("pipeline_azure_segment", text)

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
