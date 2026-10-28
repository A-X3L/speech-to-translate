import time
import sys
import threading
from typing import Optional, Any, Dict

import config
from config import AppNotifier, log_msg, get_msg
from core.injector import is_editable_text_field_focused, inject_text_into_active_window
from core.audio import apply_audio_ducking, restore_audio_volume

try:
    from PyQt6.QtCore import pyqtSignal, QObject
    PYQT6_AVAILABLE = True
except ImportError:
    PYQT6_AVAILABLE = False

try:
    import azure.cognitiveservices.speech as speechsdk
    import azure.cognitiveservices.speech.translation as translation
    AZURE_SPEECH_AVAILABLE = True
except ImportError:
    speechsdk = None
    translation = None
    AZURE_SPEECH_AVAILABLE = False

class AzureSpeechBridge(QObject if PYQT6_AVAILABLE else object):
    if PYQT6_AVAILABLE:
        recognizing = pyqtSignal(str)
        recognized = pyqtSignal(str)
        state_changed = pyqtSignal(str)
        error = pyqtSignal(str)
    else:
        recognizing = None
        recognized = None
        state_changed = None
        error = None

azure_bridge = AzureSpeechBridge() if PYQT6_AVAILABLE else None

def is_azure_available() -> bool:
    """Vérifie si le SDK Azure Speech est installé et importable."""
    return AZURE_SPEECH_AVAILABLE

def _extract_translated_text(result, target_lang: str) -> str:
    """Extrait la traduction pour la langue cible depuis le résultat Azure."""
    translations = getattr(result, "translations", {})
    if not translations:
        return getattr(result, "text", "")
    
    tl_clean = target_lang.strip()
    tl_lower = tl_clean.lower()
    
    # 1. Correspondance exacte
    if tl_clean in translations:
        return translations[tl_clean]
        
    # 2. Correspondance insensible à la casse ou code de base (ex: 'es-ES' -> 'es')
    for k, v in translations.items():
        k_lower = k.lower()
        if k_lower == tl_lower or k_lower == tl_lower.split("-")[0].split("_")[0]:
            return v
            
    # 3. Premier résultat disponible si non trouvé
    return next(iter(translations.values()))

def run_azure_streaming_session():
    """
    Session d'écoute continue et traduction en streaming avec Azure Speech.
    Gère les événements recognizing (temporaire) et recognized (final),
    applique le ducking Windows et injecte le texte traduit dans la fenêtre active.
    """
    if not AZURE_SPEECH_AVAILABLE:
        print(get_msg("err_azure_sdk_missing"))
        AppNotifier.notify_error("SDK Azure Speech non installé (pip install azure-cognitiveservices-speech)")
        return

    if not config.AZURE_SPEECH_KEY or not config.AZURE_SPEECH_KEY.strip():
        print(get_msg("err_azure_key_missing"))
        AppNotifier.notify_error("Clé AZURE_SPEECH_KEY absente dans config.json")
        return

    AppNotifier.notify_ducking_start()
    vol_interface, orig_vol = apply_audio_ducking(config.DUCKING_LEVEL)

    recognizer = None
    try:
        # Configuration de la traduction Azure
        source_language = getattr(config, "AZURE_SOURCE_LANG", "fr-FR")
        target_language = config.TARGET_LANG.lower()

        translation_config = translation.SpeechTranslationConfig(
            subscription=config.AZURE_SPEECH_KEY.strip(),
            region=config.AZURE_SPEECH_REGION.strip()
        )
        translation_config.speech_recognition_language = source_language
        translation_config.add_target_language(target_language)

        # Audio par défaut (microphone actif)
        audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
        recognizer = translation.TranslationRecognizer(
            translation_config=translation_config,
            audio_config=audio_config
        )

        # Callbacks des événements de streaming
        def on_recognizing(evt):
            try:
                partial = _extract_translated_text(evt.result, target_language).strip()
                if partial and azure_bridge and azure_bridge.recognizing:
                    azure_bridge.recognizing.emit(partial)
            except Exception:
                pass

        def on_recognized(evt):
            try:
                if evt.result.reason == speechsdk.ResultReason.TranslatedSpeech:
                    final_text = _extract_translated_text(evt.result, target_language).strip()
                    if final_text:
                        AppNotifier.notify_azure_segment(final_text)
                        if azure_bridge and azure_bridge.recognized:
                            azure_bridge.recognized.emit(final_text)
                        inject_text_into_active_window(final_text, press_enter=config.AUTO_ENTER)
                elif evt.result.reason == speechsdk.ResultReason.NoMatch:
                    pass
            except Exception as e:
                AppNotifier.notify_error(f"Erreur d'injection Azure : {e}")

        def on_canceled(evt):
            try:
                cancellation = evt.cancellation_details
                if cancellation.reason == speechsdk.CancellationReason.Error:
                    err_msg = f"Azure Speech Error ({cancellation.error_code}): {cancellation.error_details}"
                    AppNotifier.notify_error(err_msg)
                    if azure_bridge and azure_bridge.error:
                        azure_bridge.error.emit(err_msg)
            except Exception:
                pass

        recognizer.recognizing.connect(on_recognizing)
        recognizer.recognized.connect(on_recognized)
        recognizer.canceled.connect(on_canceled)

        AppNotifier.notify_azure_start()

        # Démarrage de l'écoute continue asynchrone
        start_future = recognizer.start_continuous_recognition_async()
        start_future.get()

        # Boucle d'écoute selon le mode
        from core.inputs import is_input_active
        if config.RECORD_MODE == "toggle":
            while not config.stop_toggle_recording.is_set():
                time.sleep(0.02)
        else:
            time.sleep(0.12)  # Délai initial de maintien
            while is_input_active():
                time.sleep(0.02)

    except Exception as e:
        AppNotifier.notify_error(e)

    finally:
        # Arrêt propre de l'écoute continue Azure
        if recognizer:
            try:
                stop_future = recognizer.stop_continuous_recognition_async()
                stop_future.get()
            except Exception:
                pass

        AppNotifier.notify_ducking_restore()
        restore_audio_volume(vol_interface, orig_vol)

        if config.hud_bridge and config.hud_bridge.state_changed:
            config.hud_bridge.state_changed.emit("idle")

def declencher_action_azure():
    """Point d'entrée sécurisé pour déclencher la traduction continue Azure."""
    if not config.action_lock.acquire(blocking=False):
        return

    try:
        config.is_action_in_progress = True
        run_azure_streaming_session()
    finally:
        config.is_action_in_progress = False
        config.action_lock.release()
