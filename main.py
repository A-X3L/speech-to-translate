import sys, time, threading, ctypes
from typing import Optional, Any
import config
from config import log_msg
from core.inputs import start_background_listeners, stop_background_listeners

def main():
    # Single Instance Lock (Anti-Ghost)
    if sys.platform == "win32":
        mutex = ctypes.windll.kernel32.CreateMutexW(None, False, "SpeechToTranslateSingleInstanceMutex")
        if ctypes.windll.kernel32.GetLastError() == 183: # ERROR_ALREADY_EXISTS
            print("[INFO] Une instance de Speech To Translate est déjà en cours d'exécution.")
            sys.exit(0)

    config.set_console_icon("assets/STT2.ico")
    config.action_lock = threading.Lock()
    config.stop_toggle_recording = threading.Event()
    mode_label = config.get_msg("banner_mode_toggle") if config.RECORD_MODE == "toggle" else config.get_msg("banner_mode_ptt")
    print("=" * 70)
    log_msg("banner_title")
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
        
        hud_window = HUDWidget()
        config.hud_window = hud_window
        hud_window.show()
        
        # Exécution et nettoyage à la fermeture
        exit_code = hud_app.exec()
        stop_background_listeners()
        sys.exit(exit_code)
    else:
        print("[HUD] PyQt6 n'est pas détecté. Mode console pure actif.")
        try:
            while True: time.sleep(1)
        except KeyboardInterrupt:
            log_msg("stop_app")
            stop_background_listeners()
            sys.exit(0)

if __name__ == "__main__":
    try: main()
    except KeyboardInterrupt:
        log_msg("stop_app")
        stop_background_listeners()
        sys.exit(0)
