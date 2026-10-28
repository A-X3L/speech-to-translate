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

def get_input_devices_list() -> List[Tuple[Optional[int], str]]:
    """Retourne la liste des périphériques d'enregistrement disponibles sous forme de tuples (index, label)."""
    devices: List[Tuple[Optional[int], str]] = [(None, config.get_msg("settings_input_default") or "Microphone par défaut")]
    try:
        all_devs = sd.query_devices()
        host_apis = sd.query_hostapis()
        for idx, dev in enumerate(all_devs):
            if dev.get("max_input_channels", 0) > 0:
                name = dev.get("name", f"Périphérique #{idx}")
                api_idx = dev.get("hostapi", 0)
                api_name = host_apis[api_idx]["name"] if api_idx < len(host_apis) else ""
                label = f"{name} ({api_name})" if api_name else name
                devices.append((idx, label))
    except Exception as e:
        pass
    return devices

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

    raw_dev = config.CONFIG.get("INPUT_DEVICE")
    input_dev = None
    if raw_dev is not None and str(raw_dev).strip() != "" and str(raw_dev).lower() != "none":
        try:
            input_dev = int(raw_dev)
        except (ValueError, TypeError):
            input_dev = str(raw_dev).strip()

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
        print(f"[MICROPHONE] Erreur d'enregistrement sur périphérique {input_dev} : {e}")

    return frames
