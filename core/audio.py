import sys
import time
from typing import Optional, Any, List, Tuple
import numpy as np
import sounddevice as sd

import config
from config import log_msg

try:
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    from comtypes import CLSCTX_ALL
    PYCAW_AVAILABLE = True
except ImportError:
    PYCAW_AVAILABLE = False

def get_master_volume_interface():
    if not PYCAW_AVAILABLE or sys.platform != "win32":
        return None
    try:
        from ctypes import cast, POINTER
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        return cast(interface, POINTER(IAudioEndpointVolume))
    except Exception as e:
        log_msg("ducking_err", e)
        return None

def apply_audio_ducking(ducking_level: float = 0.5):
    """Baisse le volume principal proportionnellement au niveau de ducking."""
    try:
        volume = get_master_volume_interface()
        if not volume:
            return None, None
        original_scalar = volume.GetMasterVolumeLevelScalar()
        new_scalar = max(0.0, original_scalar * (1.0 - ducking_level))
        volume.SetMasterVolumeLevelScalar(new_scalar, None)
        return volume, original_scalar
    except Exception as e:
        log_msg("ducking_err", e)
        return None, None

def restore_audio_volume(volume_interface, original_scalar: Optional[float]):
    """Restaure le volume principal à sa valeur initiale."""
    if not volume_interface or original_scalar is None:
        return
    try:
        volume_interface.SetMasterVolumeLevelScalar(original_scalar, None)
    except Exception as e:
        log_msg("ducking_restore_err", e)

# =====================================================================
# AUDIO RECORDING
# =====================================================================
def record_microphone_audio():
    from core.inputs import is_input_active
    frames = []

    def callback(indata, frames_count, time_info, status):
        if status:
            pass
        frames.append(indata.copy())
        if config.hud_bridge and config.PYQT6_AVAILABLE:
            rms = float(np.sqrt(np.mean(indata**2)))
            config.hud_bridge.volume_level.emit(min(1.0, rms * 5.0))

    input_dev = config.CONFIG.get("INPUT_DEVICE")

    try:
        with sd.InputStream(device=input_dev, samplerate=config.SAMPLE_RATE, channels=config.CHANNELS, callback=callback):
            if config.RECORD_MODE == "toggle":
                while not config.stop_toggle_recording.is_set():
                    time.sleep(0.02)
            else:
                time.sleep(0.12)  # Délais initial de maintien
                while is_input_active():
                    time.sleep(0.02)
    except Exception as e:
        print(f"[MICROPHONE] Erreur d'enregistrement : {e}")

    return frames
