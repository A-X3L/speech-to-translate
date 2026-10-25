import time
import io
import threading
from typing import Optional, Any, Dict, List
import numpy as np
from scipy.io import wavfile
from google import genai
from google.genai import types

import config
from config import AppNotifier, log_msg, get_msg
from core.injector import is_editable_text_field_focused, inject_text_into_active_window
from core.audio import apply_audio_ducking, restore_audio_volume, record_microphone_audio

genai_client = None
if config.GEMINI_API_KEY:
    try:
        genai_client = genai.Client(api_key=config.GEMINI_API_KEY)
    except Exception as e:
        print(f"[API] Initialisation Client Gemini : {e}")

SYSTEM_INSTRUCTION = (
    f"Tu es un traducteur instantané ultra-précis pour joueur de jeu vidéo multijoueur. "
    f"Identifie la langue parlée et traduis le message vers la langue cible : {config.get_tgt_desc()}. "
    f"Règles strictes et impératives : "
    f"1. Renvoie UNIQUEMENT la traduction brute en {config.get_tgt_desc()} (slang gaming, vocabulaire de jeu). "
    f"2. N'ajoute ABSOLUMENT AUCUNE formule de politesse, AUCUN commentaire, AUCUN préfixe, AUCUN en-tête, AUCUN guillemet, AUCUNE explication. "
    f"3. Si l'audio est vide ou incompréhensible, renvoie une chaîne vide."
)

def init_genai_client():
    global genai_client
    if not genai_client and config.GEMINI_API_KEY:
        try:
            genai_client = genai.Client(api_key=config.GEMINI_API_KEY)
        except Exception:
            pass
    return genai_client

def declencher_action_micro():
    global genai_client
    
    if not config.action_lock.acquire(blocking=False):
        return

    try:
        config.is_action_in_progress = True
        
        if not is_editable_text_field_focused():
            AppNotifier.notify_focus_error()
            return

        AppNotifier.notify_ducking_start()
        vol_interface, orig_vol = apply_audio_ducking(config.DUCKING_LEVEL)
        
        try:
            AppNotifier.notify_recording_start(config.RECORD_MODE, config.HOTKEY_STR.upper())
            recorded_frames = record_microphone_audio()
            AppNotifier.notify_recording_stop()

            if not recorded_frames or len(recorded_frames) == 0:
                AppNotifier.notify_empty_speech()
                return

            audio_data = np.concatenate(recorded_frames, axis=0)
            audio_int16 = (audio_data * 32767).astype(np.int16)
            wav_io = io.BytesIO()
            wavfile.write(wav_io, config.SAMPLE_RATE, audio_int16)
            wav_bytes = wav_io.getvalue()

            client = init_genai_client()
            if not client:
                print(get_msg("err_key_missing"))
                AppNotifier.notify_error("Clé GEMINI_API_KEY absente dans config.json")
                return

            start_time = time.time()
            AppNotifier.notify_api_sending(config.GEMINI_MODEL)
            
            tgt_desc = config.get_tgt_desc()
            user_prompt = f"Identifie la langue parlée et traduis le message vers la langue cible : {tgt_desc}."

            response = client.models.generate_content(
                model=config.GEMINI_MODEL,
                contents=[
                    types.Part.from_bytes(
                        data=wav_bytes,
                        mime_type="audio/wav",
                    ),
                    user_prompt,
                ],
                config=types.GenerateContentConfig(
                    system_instruction=(
                        f"Tu es un traducteur instantané ultra-précis pour joueur de jeu vidéo multijoueur. "
                        f"Identifie la langue parlée et traduis le message vers la langue cible : {tgt_desc}. "
                        f"Règles strictes et impératives : "
                        f"1. Renvoie UNIQUEMENT la traduction brute en {tgt_desc} (slang gaming, vocabulaire de jeu). "
                        f"2. N'ajoute ABSOLUMENT AUCUNE formule de politesse, AUCUN commentaire, AUCUN préfixe, AUCUN en-tête, AUCUN guillemet, AUCUNE explication. "
                        f"3. Si l'audio est vide ou incompréhensible, renvoie une chaîne vide."
                    ),
                    temperature=0.2,
                )
            )

            translated_text = response.text.strip() if response and response.text else ""
            latency = round((time.time() - start_time), 2)

            if translated_text:
                AppNotifier.notify_translation_success(latency, config.GEMINI_MODEL, translated_text)
                inject_text_into_active_window(translated_text, press_enter=config.AUTO_ENTER)
            else:
                AppNotifier.notify_empty_speech()

        except Exception as e:
            AppNotifier.notify_error(e)

        finally:
            AppNotifier.notify_ducking_restore()
            restore_audio_volume(vol_interface, orig_vol)

    finally:
        config.is_action_in_progress = False
        config.action_lock.release()
