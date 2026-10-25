import sys
import ctypes
import time
from typing import Optional, Any
import pyperclip
from pynput import keyboard

import config
from config import log_msg

kb_controller = keyboard.Controller()

def is_editable_text_field_focused() -> bool:
    """
    Vérifie via Windows UI Automation et Win32 si l'élément actuellement
    ciblé par le curseur est un champ texte éditable.
    """
    if sys.platform != "win32":
        return True

    try:
        import comtypes
        import comtypes.client
        comtypes.CoInitialize()
        try:
            uia_clsid = "{ff48dba4-60ef-4201-aa87-54103eef594e}"
            uia = comtypes.client.CreateObject(uia_clsid)
            if uia:
                elem = uia.GetFocusedElement()
                if elem:
                    ctrl_type = getattr(elem, "CurrentControlType", None)
                    if ctrl_type in (50004, 50030, 50003):
                        return True
                    try:
                        val_pattern = elem.GetCurrentPattern(10002)
                        if val_pattern:
                            is_readonly = getattr(val_pattern, "CurrentIsReadOnly", False)
                            if not is_readonly:
                                return True
                    except Exception:
                        pass
        finally:
            comtypes.CoUninitialize()
    except Exception:
        pass

    try:
        user32 = ctypes.windll.user32
        class RECT(ctypes.Structure):
            _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long),
                        ("right", ctypes.c_long), ("bottom", ctypes.c_long)]
        class GUITHREADINFO(ctypes.Structure):
            _fields_ = [
                ("cbSize", ctypes.c_ulong), ("flags", ctypes.c_ulong),
                ("hwndActive", ctypes.c_void_p), ("hwndFocus", ctypes.c_void_p),
                ("hwndCapture", ctypes.c_void_p), ("hwndMenuOwner", ctypes.c_void_p),
                ("hwndMoveSize", ctypes.c_void_p), ("hwndCaret", ctypes.c_void_p),
                ("rcCaret", RECT)
            ]
        gti = GUITHREADINFO()
        gti.cbSize = ctypes.sizeof(GUITHREADINFO)
        if user32.GetGUIThreadInfo(0, ctypes.byref(gti)):
            if gti.hwndCaret:
                return True
            if gti.hwndFocus:
                class_buf = ctypes.create_unicode_buffer(256)
                user32.GetClassNameW(gti.hwndFocus, class_buf, 256)
                c_name = class_buf.value.lower()
                if any(x in c_name for x in ["edit", "textbox", "rich", "scintilla", "input"]):
                    return True
    except Exception:
        pass

    return False

def inject_text_into_active_window(text: str, press_enter: bool = True):
    """Injecte le texte traduit dans le champ actif via presse-papiers ou frappe."""
    log_msg("injection_sending", text)

    if config.INJECTION_METHOD == "clipboard_paste":
        try:
            pyperclip.copy(text)
            time.sleep(0.05)
            with kb_controller.pressed(keyboard.Key.ctrl):
                kb_controller.press('v')
                kb_controller.release('v')
            time.sleep(0.05)
        except Exception:
            kb_controller.type(text)
    else:
        kb_controller.type(text)

    if press_enter:
        time.sleep(0.08)
        kb_controller.press(keyboard.Key.enter)
        kb_controller.release(keyboard.Key.enter)
        log_msg("enter_validated")
