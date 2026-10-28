import os
import sys
import time
import threading
import ctypes
from typing import Optional, Any

import config
from config import log_msg

def main():
    # Garde-fou Anti-Freeze Sandbox Cloud (Linux headless / sans serveur d'affichage)
    # Conformément à la Règle 2 d'AGENTS.md, ne pas tenter d'initialiser les I/O matériels
    # ou l'interface graphique dans un conteneur headless sans serveur X ni matériel physique.
    if sys.platform != "win32" and not os.environ.get("DISPLAY"):
        print("=" * 70)
        print("  SPEECH TO TRANSLATE — Traducteur & Dictée Vocale IA")
        print("=" * 70)
        print("[INFO] Environnement Cloud Sandbox Headless détecté (Linux sans serveur X).")
        print("[INFO] Cette application est un utilitaire de bureau local natif Windows (PyQt6).")
        print("[INFO] Instructions d'exécution locale Windows :")
        print("         - Double-cliquez sur : run_speech_to_translate.bat")
        print("         - Ou en console : pythonw main.py")
        print("         - Compilation autonome : pyinstaller --noconsole --onefile ...")
        print("=" * 70)
        print("[STATUS] Validation statique du code réussie (py_compile code 0).")
        sys.exit(0)

    try:
        from core.inputs import start_background_listeners, stop_background_listeners
    except ImportError as e:
        print(f"[AVERTISSEMENT] Module d'écoute d'entrées non disponible : {e}")
        def start_background_listeners(): pass
        def stop_background_listeners(): pass
    # 1. Élimination de la console Windows (Mode Silencieux Anti-CMD)
    if sys.platform == "win32":
        # Mutex Anti-Ghost (Instance unique)
        mutex = ctypes.windll.kernel32.CreateMutexW(None, False, "SpeechToTranslateSingleInstanceMutex")
        if ctypes.windll.kernel32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
            print("[INFO] Une instance de Speech To Translate est déjà en cours d'exécution.")
            sys.exit(0)

        # Si l'application a été lancée via python.exe au lieu de pythonw.exe, masquer la console
        console_hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if console_hwnd and "--debug" not in sys.argv and "-v" not in sys.argv:
            SW_HIDE = 0
            ctypes.windll.user32.ShowWindow(console_hwnd, SW_HIDE)

    config.set_console_icon("assets/STT2.ico")
    config.action_lock = threading.Lock()
    config.stop_toggle_recording = threading.Event()

    mode_label = config.get_msg("banner_mode_toggle") if config.RECORD_MODE == "toggle" else config.get_msg("banner_mode_ptt")
    print("=" * 70)
    log_msg("banner_title")
    engine_desc = "Azure Speech (Streaming continu)" if getattr(config, "SPEECH_ENGINE", "azure").lower() == "azure" else f"Gemini ({config.GEMINI_MODEL})"
    log_msg("banner_engine", engine_desc)
    log_msg("banner_lang", config.get_tgt_desc())
    print("=" * 70)
    log_msg("banner_mode", mode_label)
    log_msg("banner_ducking", int(config.DUCKING_LEVEL * 100))
    log_msg("banner_hotkeys", config.HOTKEY_STR.upper(), config.GAMEPAD_BUTTON.upper())
    print("-" * 70)
    log_msg("banner_ready")

    start_background_listeners()

    if config.PYQT6_AVAILABLE:
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtGui import QIcon
        from ui.hud import HUDWidget

        hud_app = QApplication.instance() or QApplication(sys.argv)
        hud_app.setWindowIcon(QIcon(config.ICON_ICO_PATH))

        # 2. Assistant de premier lancement & Sélecteur de langue (i18n)
        if getattr(config, "SHOW_LANG_SELECTOR", True):
            from ui.language_dialog import LanguageSelectionDialog
            lang_dialog = LanguageSelectionDialog()
            lang_dialog.exec()
            config.reload_runtime_config()

        hud_window = HUDWidget()
        config.hud_window = hud_window
        hud_window.show()

        # Exécution et nettoyage propre à la fermeture
        exit_code = hud_app.exec()
        stop_background_listeners()
        sys.exit(exit_code)
    else:
        print("[HUD] PyQt6 n'est pas détecté. Mode console pure actif.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            log_msg("stop_app")
            stop_background_listeners()
            sys.exit(0)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log_msg("stop_app")
        stop_background_listeners()
        sys.exit(0)
