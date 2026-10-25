import sys
import threading
from typing import Optional, Any, Dict, List, Tuple
from PyQt6.QtCore import Qt, QPoint, QTimer, QSize
from PyQt6.QtWidgets import (
    QApplication, QWidget, QHBoxLayout, QVBoxLayout, QPushButton,
    QGraphicsDropShadowEffect, QStackedWidget
)
from PyQt6.QtGui import QColor, QPainter, QIcon, QMouseEvent, QBrush

import config
from core.inputs import get_pressed_gamepad_button
from core.api import declencher_action_micro
from ui.settings import SettingsPage
from ui.help import HelpPage

class DragGripWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.setCursor(Qt.CursorShape.SizeAllCursor)
        self.setFixedHeight(18)
        self.setToolTip("Glisser pour déplacer la capsule")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w = self.width()
        h = self.height()
        bar_w = 36
        bar_h = 4
        bar_x = (w - bar_w) // 2
        bar_y = (h - bar_h) // 2
        painter.setBrush(QBrush(QColor(255, 255, 255, 75)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(bar_x, bar_y, bar_w, bar_h, 2, 2)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton and self.parent_window:
            self.parent_window.drag_position = event.globalPosition().toPoint() - self.parent_window.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() == Qt.MouseButton.LeftButton and self.parent_window and not self.parent_window.drag_position.isNull():
            self.parent_window.move(event.globalPosition().toPoint() - self.parent_window.drag_position)
            event.accept()

class HUDWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.drag_position = QPoint()
        self.current_state = "idle"
        self.glow_step = 0
        self.glow_direction = 1

        self.is_capturing_gamepad = False
        self.gamepad_poll_timer = QTimer(self)
        self.gamepad_poll_timer.timeout.connect(self._check_gamepad_capture)
        self.gamepad_timeout_timer = QTimer(self)
        self.gamepad_timeout_timer.setSingleShot(True)
        self.gamepad_timeout_timer.timeout.connect(self._on_gamepad_capture_timeout)

        self.init_ui()
        if config.hud_bridge:
            config.hud_bridge.state_changed.connect(self.on_state_changed)
            config.hud_bridge.volume_level.connect(self.on_volume_level)

        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self.update_glow_animation)
        self.anim_timer.start(50)

    def init_ui(self):
        self.setWindowIcon(QIcon(config.ICON_ICO_PATH))
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool |
            Qt.WindowType.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, False)
        self.setFixedSize(224, 82)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 150))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self.stacked_widget = QStackedWidget(self)
        root_layout.addWidget(self.stacked_widget)

        self.page_main = QWidget(self)
        main_layout = QVBoxLayout(self.page_main)
        main_layout.setContentsMargins(12, 6, 12, 10)
        main_layout.setSpacing(4)

        top_bar_layout = QHBoxLayout()
        top_bar_layout.setContentsMargins(0, 0, 0, 0)
        top_bar_layout.setSpacing(4)
        dummy_spacer = QWidget(self.page_main)
        dummy_spacer.setFixedSize(16, 16)
        top_bar_layout.addWidget(dummy_spacer)
        self.grip_handle = DragGripWidget(self)
        top_bar_layout.addWidget(self.grip_handle, 1)

        self.btn_close = QPushButton("✕", self.page_main)
        self.btn_close.setFixedSize(18, 18)
        self.btn_close.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_close.setToolTip("Quitter Speech to Translate")
        self.btn_close.setStyleSheet("""
            QPushButton { background-color: transparent; color: rgba(255, 255, 255, 0.4); border: none; border-radius: 9px; font-family: 'Segoe UI', sans-serif; font-size: 11px; font-weight: bold; padding-bottom: 2px; }
            QPushButton:hover { background-color: rgba(234, 67, 53, 0.8); color: #ffffff; }
            QPushButton:pressed { background-color: rgba(200, 40, 30, 1.0); color: #ffffff; }
        """)
        self.btn_close.clicked.connect(self.close_application)
        top_bar_layout.addWidget(self.btn_close)
        main_layout.addLayout(top_bar_layout)

        buttons_layout = QHBoxLayout()
        buttons_layout.setContentsMargins(6, 0, 6, 0)
        buttons_layout.setSpacing(14)

        self.btn_settings = QPushButton(self.page_main)
        self.btn_settings.setFixedSize(40, 40)
        self.btn_settings.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.btn_settings.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_settings.setToolTip("Paramètres intégrés")
        self.btn_settings.setStyleSheet(self._button_stylesheet())
        self._load_svg_to_btn(self.btn_settings, config.SVG_SETTING_PATH, size=30)
        self.btn_settings.clicked.connect(self.show_settings_page)
        buttons_layout.addWidget(self.btn_settings)

        self.btn_mic = QPushButton(self.page_main)
        self.btn_mic.setFixedSize(48, 48)
        self.btn_mic.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.btn_mic.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_mic.setToolTip("Speech to Translate (Veille / Parler)")
        self.btn_mic.setStyleSheet(self._mic_button_stylesheet())
        self._load_svg_to_btn(self.btn_mic, config.SVG_MIC_PATH, size=38)
        self.btn_mic.clicked.connect(self.on_mic_clicked)
        buttons_layout.addWidget(self.btn_mic)

        self.btn_help = QPushButton(self.page_main)
        self.btn_help.setFixedSize(40, 40)
        self.btn_help.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.btn_help.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_help.setToolTip("Documentation & Aide (help.html)")
        self.btn_help.setStyleSheet(self._button_stylesheet())
        self._load_svg_to_btn(self.btn_help, config.SVG_HELP_PATH, size=30)
        self.btn_help.clicked.connect(self.show_help_page)
        buttons_layout.addWidget(self.btn_help)

        main_layout.addLayout(buttons_layout)
        self.stacked_widget.addWidget(self.page_main)

        self.page_settings = SettingsPage(self)
        self.stacked_widget.addWidget(self.page_settings)

        self.page_help = HelpPage(self)
        self.stacked_widget.addWidget(self.page_help)

        self.position_default()

        if not str(config.CONFIG.get("GEMINI_API_KEY", "")).strip():
            self.show_help_page()
        else:
            self.show_main_page()

    def start_gamepad_capture(self):
        self.is_capturing_gamepad = True
        self.page_settings.btn_capture_gamepad.setText("Appuyez sur la manette... (8s)")
        self.page_settings.btn_capture_gamepad.setStyleSheet("color: #22d3ee; border: 1px solid #22d3ee; font-weight: bold;")
        self.gamepad_poll_timer.start(50)
        self.gamepad_timeout_timer.start(8000)

    def _check_gamepad_capture(self):
        pressed_btn = get_pressed_gamepad_button()
        if pressed_btn:
            self._finish_gamepad_capture(pressed_btn)

    def _on_gamepad_capture_timeout(self):
        self._finish_gamepad_capture(None)

    def _finish_gamepad_capture(self, button_name: Optional[str]):
        self.gamepad_poll_timer.stop()
        self.gamepad_timeout_timer.stop()
        self.is_capturing_gamepad = False

        if button_name:
            config.GAMEPAD_BUTTON = button_name.lower()
            config.CONFIG["GAMEPAD_BUTTON"] = config.GAMEPAD_BUTTON
            config.save_config(config.CONFIG)

        display_text = config.GAMEPAD_BUTTON.upper() if config.GAMEPAD_BUTTON != "none" else "AUCUN"
        self.page_settings.btn_capture_gamepad.setText(f"Bouton : [{display_text}]")
        self.page_settings.btn_capture_gamepad.setStyleSheet("")
        if hasattr(self.page_help, 'update_shortcuts_display'):
            self.page_help.update_shortcuts_display()

    def clear_gamepad_button(self):
        if self.is_capturing_gamepad:
            self.gamepad_poll_timer.stop()
            self.gamepad_timeout_timer.stop()
            self.is_capturing_gamepad = False
        config.GAMEPAD_BUTTON = "none"
        config.CONFIG["GAMEPAD_BUTTON"] = "none"
        config.save_config(config.CONFIG)
        self.page_settings.btn_capture_gamepad.setText("Bouton : [AUCUN]")
        self.page_settings.btn_capture_gamepad.setStyleSheet("")
        if hasattr(self.page_help, 'update_shortcuts_display'):
            self.page_help.update_shortcuts_display()

    def set_interactive_mode(self, interactive: bool):
        self.setWindowFlag(Qt.WindowType.WindowDoesNotAcceptFocus, not interactive)
        self.show()

    def show_settings_page(self):
        self.set_interactive_mode(True)
        self.stacked_widget.setCurrentIndex(1)
        self.setFixedSize(280, 500)
        self.adjustSize()
        self.update()

    def show_help_page(self):
        if hasattr(self.page_help, 'update_shortcuts_display'):
            self.page_help.update_shortcuts_display()
        self.set_interactive_mode(True)
        self.stacked_widget.setCurrentIndex(2)
        self.setFixedSize(280, 200)
        self.adjustSize()
        self.update()

    def show_main_page(self):
        self.set_interactive_mode(False)
        self.stacked_widget.setCurrentIndex(0)
        self.setFixedSize(224, 82)
        self.adjustSize()
        self.update()

    def update_ducking_level(self, val):
        config.DUCKING_LEVEL = float(val) / 100.0
        config.CONFIG["DUCKING_LEVEL"] = config.DUCKING_LEVEL
        config.save_config(config.CONFIG)

    def update_record_mode(self, index):
        modes = ["hold", "toggle"]
        config.RECORD_MODE = modes[index]
        config.CONFIG["RECORD_MODE"] = config.RECORD_MODE
        config.save_config(config.CONFIG)

    def update_target_lang(self, index):
        lang_codes = ["en", "fr", "es", "de"]
        if 0 <= index < len(lang_codes):
            config.TARGET_LANG = lang_codes[index]
            config.CONFIG["TARGET_LANG"] = config.TARGET_LANG
            config.save_config(config.CONFIG)
            from core.api import init_genai_client
            init_genai_client()

    def update_auto_enter(self, checked):
        config.AUTO_ENTER = checked
        config.CONFIG["AUTO_ENTER"] = config.AUTO_ENTER
        config.save_config(config.CONFIG)

    def update_api_key(self, text):
        config.GEMINI_API_KEY = text.strip()
        config.CONFIG["GEMINI_API_KEY"] = config.GEMINI_API_KEY
        config.save_config(config.CONFIG)
        from core.api import init_genai_client
        init_genai_client()

    def update_hotkey(self, text):
        val = text.strip().lower()
        if val:
            config.HOTKEY_STR = val
            config.CONFIG["HOTKEY"] = config.HOTKEY_STR
            config.save_config(config.CONFIG)

    def _panel_stylesheet(self) -> str:
        return """
            QWidget { background-color: rgba(15, 23, 42, 0.95); color: #f8fafc; font-family: 'Segoe UI', sans-serif; border-radius: 12px; }
            QLabel { font-size: 13px; font-weight: 500; color: #cbd5e1; }
            QPushButton { background-color: rgba(255, 255, 255, 0.1); border: 1px solid rgba(255, 255, 255, 0.2); border-radius: 6px; color: #f8fafc; font-size: 12px; padding: 4px; }
            QPushButton:hover { background-color: rgba(34, 211, 238, 0.2); border: 1px solid #22d3ee; }
            QPushButton:pressed { background-color: rgba(34, 211, 238, 0.4); }
            QLineEdit { background-color: rgba(0, 0, 0, 0.3); border: 1px solid rgba(255, 255, 255, 0.15); border-radius: 6px; padding: 6px; color: #22d3ee; font-weight: bold; font-size: 12px; }
            QLineEdit:focus { border: 1px solid #22d3ee; background-color: rgba(0, 0, 0, 0.5); }
            QComboBox { background-color: rgba(0, 0, 0, 0.3); border: 1px solid rgba(255, 255, 255, 0.15); border-radius: 6px; padding: 3px 8px; }
            QComboBox:hover { border: 1px solid #22d3ee; }
            QComboBox::drop-down { border: none; }
            QSlider::groove:horizontal { border-radius: 2px; height: 4px; background: rgba(255, 255, 255, 0.2); }
            QSlider::handle:horizontal { background: #22d3ee; width: 14px; height: 14px; margin: -5px 0; border-radius: 7px; }
            QSlider::handle:horizontal:hover { background: #ff5e36; }
            QCheckBox { color: #e2e8f0; font-family: 'Segoe UI', sans-serif; font-size: 12px; spacing: 8px; }
            QCheckBox::indicator { width: 16px; height: 16px; border-radius: 3px; border: 1px solid rgba(255, 255, 255, 0.2); background: rgba(15, 23, 42, 0.8); }
            QCheckBox::indicator:hover { border: 1px solid #22d3ee; }
            QCheckBox::indicator:checked { background: #22d3ee; }
        """

    def _button_stylesheet(self) -> str:
        return """
            QPushButton { background-color: transparent; border: none; }
        """

    def _mic_button_stylesheet(self) -> str:
        return """
            QPushButton { background-color: transparent; border: none; }
        """

    def _load_svg_to_btn(self, btn: QPushButton, svg_path: str, size: int = 24):
        import os
        if os.path.exists(svg_path):
            btn.setIcon(QIcon(svg_path))
            btn.setIconSize(QSize(size, size))

    def position_default(self):
        screen = QApplication.primaryScreen()
        if screen:
            screen_geom = screen.geometry()
            x = (screen_geom.width() - self.width()) // 2
            y = int(screen_geom.height() * 0.05)
            self.move(x, y)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
        
        # Effacer l'arrière-plan pour éviter les artefacts de transparence
        painter.fillRect(self.rect(), QColor(0, 0, 0, 0))

        # Glow / Status indicator
        if self.current_state in ("recording", "processing", "error", "focus_error"):
            if self.current_state == "recording":
                base_color = QColor(34, 211, 238, 120)  # Cyan doux plutôt que rouge agressif
            elif self.current_state == "processing":
                base_color = QColor(34, 211, 238, 200)
            else:
                base_color = QColor(255, 60, 60, 160)
            glow_radius = 8 + (self.glow_step / 100.0) * 4
            painter.setBrush(base_color)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), glow_radius, glow_radius)

        # Fond principal
        painter.setBrush(QColor(15, 23, 42, 245))
        painter.setPen(Qt.PenStyle.NoPen)
        rect = self.rect()
        painter.drawRoundedRect(rect.adjusted(2, 2, -2, -2), 12, 12)

    def update_glow_animation(self):
        if self.current_state in ("recording", "processing", "error", "focus_error"):
            self.glow_step += 5 * self.glow_direction
            if self.glow_step >= 100:
                self.glow_direction = -1
                self.glow_step = 100
            elif self.glow_step <= 0:
                self.glow_direction = 1
                self.glow_step = 0
            self.update()

    def on_state_changed(self, state_str: str):
        self.current_state = state_str
        if state_str == "idle":
            self.glow_step = 0
            self._load_svg_to_btn(self.btn_mic, config.SVG_MIC_PATH, size=38)
            self.btn_mic.setStyleSheet(self._mic_button_stylesheet())
        else:
            self._load_svg_to_btn(self.btn_mic, config.SVG_MIC_PATH, size=38)
        self.update()

    def on_volume_level(self, level: float):
        if self.current_state == "recording":
            self.glow_step = int(level * 100)
            self.update()

    def mousePressEvent(self, event: QMouseEvent):
        pass

    def mouseMoveEvent(self, event: QMouseEvent):
        pass

    def close_application(self):
        sys.exit(0)

    def on_settings_clicked(self):
        self.show_settings_page()

    def on_help_clicked(self):
        self.show_help_page()

    def on_mic_clicked(self):
        if self.current_state == "idle":
            threading.Thread(target=declencher_action_micro, daemon=True).start()
        elif self.current_state == "recording" and config.RECORD_MODE == "toggle":
            config.stop_toggle_recording.set()
