import time
import ctypes
import threading
from typing import Optional, Any, Union
from pynput import keyboard

import config
from core.api import declencher_action_micro

XINPUT_GAMEPAD_RIGHT_THUMB    = 0x0080
XINPUT_GAMEPAD_LEFT_THUMB     = 0x0040
XINPUT_GAMEPAD_LEFT_SHOULDER  = 0x0100
XINPUT_GAMEPAD_RIGHT_SHOULDER = 0x0200
XINPUT_GAMEPAD_BACK           = 0x0020
XINPUT_GAMEPAD_START          = 0x0010
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

xinput_dll = None
import sys
if sys.platform == "win32":
    for dll_name in ["xinput1_4.dll", "xinput1_3.dll", "xinput9_1_0.dll"]:
        try:
            xinput_dll = ctypes.windll.LoadLibrary(dll_name)
            break
        except Exception:
            continue

def get_pressed_gamepad_button() -> Optional[str]:
    if not xinput_dll:
        return None
    state = XINPUT_STATE()
    res = xinput_dll.XInputGetState(0, ctypes.byref(state))
    if res != 0:
        return None
    buttons = state.Gamepad.wButtons
    if buttons & XINPUT_GAMEPAD_LEFT_SHOULDER:
        return "lb"
    if buttons & XINPUT_GAMEPAD_RIGHT_SHOULDER:
        return "rb"
    if state.Gamepad.bLeftTrigger > 128:
        return "lt"
    if state.Gamepad.bRightTrigger > 128:
        return "rt"
    if buttons & XINPUT_GAMEPAD_RIGHT_THUMB:
        return "rs"
    if buttons & XINPUT_GAMEPAD_LEFT_THUMB:
        return "ls"
    if buttons & XINPUT_GAMEPAD_BACK:
        return "back"
    if buttons & XINPUT_GAMEPAD_START:
        return "start"
    if buttons & XINPUT_GAMEPAD_A:
        return "a"
    if buttons & XINPUT_GAMEPAD_B:
        return "b"
    if buttons & XINPUT_GAMEPAD_X:
        return "x"
    if buttons & XINPUT_GAMEPAD_Y:
        return "y"
    return None

def is_gamepad_button_pressed() -> bool:
    if not xinput_dll or config.GAMEPAD_BUTTON == "none":
        return False
    state = XINPUT_STATE()
    res = xinput_dll.XInputGetState(0, ctypes.byref(state))
    if res != 0:
        return False
    buttons = state.Gamepad.wButtons

    btn = config.GAMEPAD_BUTTON.lower()
    if btn in ("r_thumb", "rs", "r3"):
        return bool(buttons & XINPUT_GAMEPAD_RIGHT_THUMB)
    elif btn in ("l_thumb", "ls", "l3"):
        return bool(buttons & XINPUT_GAMEPAD_LEFT_THUMB)
    elif btn in ("lb", "l_shoulder"):
        return bool(buttons & XINPUT_GAMEPAD_LEFT_SHOULDER)
    elif btn in ("rb", "r_shoulder"):
        return bool(buttons & XINPUT_GAMEPAD_RIGHT_SHOULDER)
    elif btn == "lt":
        return state.Gamepad.bLeftTrigger > 128
    elif btn == "rt":
        return state.Gamepad.bRightTrigger > 128
    elif btn in ("back", "view", "select"):
        return bool(buttons & XINPUT_GAMEPAD_BACK)
    elif btn in ("start", "menu"):
        return bool(buttons & XINPUT_GAMEPAD_START)
    elif btn == "a":
        return bool(buttons & XINPUT_GAMEPAD_A)
    elif btn == "b":
        return bool(buttons & XINPUT_GAMEPAD_B)
    elif btn == "x":
        return bool(buttons & XINPUT_GAMEPAD_X)
    elif btn == "y":
        return bool(buttons & XINPUT_GAMEPAD_Y)
    return False

def get_key_name(key) -> str:
    try:
        if hasattr(key, 'char') and key.char:
            return key.char.lower()
        if hasattr(key, 'name') and key.name:
            return key.name.lower()
    except Exception:
        pass
    return str(key).lower().replace("key.", "")

def is_input_active() -> bool:
    return config.key_pressed_state or is_gamepad_button_pressed()

def on_press(key):
    if getattr(config, "IS_MUTED", False):
        return
    k_name = get_key_name(key)
    if k_name == config.HOTKEY_STR:
        if config.RECORD_MODE == "toggle":
            if config.is_action_in_progress:
                config.stop_toggle_recording.set()
            else:
                threading.Thread(target=declencher_action_micro, daemon=True).start()
        else:
            if not config.key_pressed_state:
                config.key_pressed_state = True
                threading.Thread(target=declencher_action_micro, daemon=True).start()

def on_release(key):
    k_name = get_key_name(key)
    if k_name == config.HOTKEY_STR:
        if config.RECORD_MODE != "toggle":
            config.key_pressed_state = False

_background_thread_running = False
_keyboard_listener = None
_gamepad_thread = None

def gamepad_poller_thread():
    was_pressed = False
    global _background_thread_running
    while _background_thread_running:
        try:
            is_capturing = False
            if config.hud_window:
                if getattr(config.hud_window, 'is_capturing_gamepad', False):
                    is_capturing = True
                elif getattr(config.hud_window, 'settings_dialog', None) and getattr(config.hud_window.settings_dialog, 'is_capturing_gamepad', False):
                    is_capturing = True
            if is_capturing or getattr(config, "IS_MUTED", False):
                time.sleep(0.05)
                continue

            pressed = is_gamepad_button_pressed()
            if config.RECORD_MODE == "toggle":
                if pressed and not was_pressed:
                    if config.is_action_in_progress:
                        config.stop_toggle_recording.set()
                    else:
                        threading.Thread(target=declencher_action_micro, daemon=True).start()
            else:
                if pressed and not was_pressed:
                    threading.Thread(target=declencher_action_micro, daemon=True).start()
            was_pressed = pressed
        except Exception:
            pass
        time.sleep(0.02)

def start_background_listeners():
    global _background_thread_running, _keyboard_listener, _gamepad_thread
    _background_thread_running = True

    _gamepad_thread = threading.Thread(target=gamepad_poller_thread, daemon=True)
    _gamepad_thread.start()

    _keyboard_listener = keyboard.Listener(on_press=on_press, on_release=on_release)
    _keyboard_listener.daemon = True
    _keyboard_listener.start()

def stop_background_listeners():
    global _background_thread_running, _keyboard_listener
    _background_thread_running = False
    if _keyboard_listener:
        try:
            _keyboard_listener.stop()
        except Exception:
            pass
