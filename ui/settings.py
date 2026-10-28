import os
import sys
from typing import Optional, Any
from PyQt6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QLineEdit, QSlider, QComboBox, QCheckBox, QScrollArea, QFrame, QApplication
)
from PyQt6.QtCore import Qt, QPoint, QTimer
from PyQt6.QtGui import QIcon, QMouseEvent

import config
from core.inputs import get_pressed_gamepad_button

class SettingsDialog(QDialog):
    """
    Entité 2 : L'Atelier de Configuration.
    Fenêtre de dialogue indépendante, opaque et stable (#1f1f1f),
    dédiée à l'ensemble des réglages applicatifs (Audio, Moteurs, Dock, Raccourcis, i18n).
    """
    def __init__(self, parent_hud=None):
        super().__init__(parent_hud)
        self.hud = parent_hud
        self.drag_position = QPoint()

        # Capture manette avec garde-fou temporel (8 secondes max)
        self.is_capturing_gamepad = False
        self.gamepad_poll_timer = QTimer(self)
        self.gamepad_poll_timer.timeout.connect(self._check_gamepad_capture)
        self.gamepad_timeout_timer = QTimer(self)
        self.gamepad_timeout_timer.setSingleShot(True)
        self.gamepad_timeout_timer.timeout.connect(self._on_gamepad_capture_timeout)

        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Speech to Translate — " + config.get_msg("settings_workshop_title"))
        self.setWindowIcon(QIcon(config.ICON_ICO_PATH))
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Dialog
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setFixedSize(380, 620)
        self.setStyleSheet(self._dialog_stylesheet())

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(8)

        # En-tête avec titre et bouton Fermer ✕
        header = QHBoxLayout()
        header.setContentsMargins(4, 2, 4, 2)
        header.setSpacing(8)

        title_lbl = QLabel(f"⚙ {config.get_msg('settings_workshop_title')}", self)
        title_lbl.setStyleSheet("font-weight: bold; font-size: 14px; color: #22d3ee; background: transparent; border: none;")
        header.addWidget(title_lbl)
        header.addStretch(1)

        self.btn_close_header = QPushButton("✕", self)
        self.btn_close_header.setFixedSize(22, 22)
        self.btn_close_header.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_close_header.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: rgba(255, 255, 255, 0.45);
                font-size: 12px;
                font-weight: bold;
                border-radius: 11px;
            }
            QPushButton:hover { background: rgba(239, 68, 68, 0.85); color: #fff; }
        """)
        self.btn_close_header.clicked.connect(self.accept)
        header.addWidget(self.btn_close_header)
        main_layout.addLayout(header)

        # Zone déroulante (Scroll Area)
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea { background: transparent; border: none; }
            QScrollBar:vertical {
                border: none;
                background: #161b22;
                width: 6px;
                border-radius: 3px;
            }
            QScrollBar::handle:vertical {
                background: rgba(34, 211, 238, 0.4);
                border-radius: 3px;
            }
            QScrollBar::handle:vertical:hover {
                background: #22d3ee;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
        """)

        content_widget = QWidget()
        content_widget.setStyleSheet("background: transparent;")
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(4, 4, 8, 4)
        content_layout.setSpacing(10)

        # 1. BORD D'ANCRAGE DE L'ÉCRAN
        self.lbl_dock = QLabel(config.get_msg("settings_dock_edge"), content_widget)
        content_layout.addWidget(self.lbl_dock)

        self.combo_dock = QComboBox(content_widget)
        self.combo_dock.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.combo_dock.addItem(config.get_msg("dock_top"), "top")
        self.combo_dock.addItem(config.get_msg("dock_bottom"), "bottom")
        self.combo_dock.addItem(config.get_msg("dock_left"), "left")
        self.combo_dock.addItem(config.get_msg("dock_right"), "right")

        cur_dock = str(config.CONFIG.get("DOCK_EDGE", "top")).lower()
        dock_idx = 0
        for i in range(self.combo_dock.count()):
            if self.combo_dock.itemData(i) == cur_dock:
                dock_idx = i
                break
        self.combo_dock.setCurrentIndex(dock_idx)
        self.combo_dock.currentIndexChanged.connect(self.on_dock_edge_changed)
        content_layout.addWidget(self.combo_dock)

        # 2. MICROPHONE D'ENTRÉE
        self.lbl_mic_input = QLabel(config.get_msg("settings_input_device"), content_widget)
        content_layout.addWidget(self.lbl_mic_input)

        self.combo_mic_input = QComboBox(content_widget)
        self.combo_mic_input.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        from core.audio import get_input_devices_list
        self.input_devices_data = get_input_devices_list()
        current_dev = config.CONFIG.get("INPUT_DEVICE")
        cur_selected = 0
        for idx, (dev_val, dev_label) in enumerate(self.input_devices_data):
            self.combo_mic_input.addItem(dev_label, dev_val)
            if dev_val is not None and current_dev is not None:
                if str(dev_val) == str(current_dev):
                    cur_selected = idx
            elif dev_val is None and current_dev is None:
                cur_selected = idx

        self.combo_mic_input.setCurrentIndex(cur_selected)
        self.combo_mic_input.currentIndexChanged.connect(self.on_mic_device_changed)
        content_layout.addWidget(self.combo_mic_input)

        # 3. MOTEUR DE TRADUCTION
        self.lbl_engine = QLabel("Moteur de reconnaissance & traduction :", content_widget)
        content_layout.addWidget(self.lbl_engine)

        self.combo_engine = QComboBox(content_widget)
        self.combo_engine.addItems([
            "Azure Speech (Streaming continu)",
            "Gemini Flash (Appel unitaire)"
        ])
        self.combo_engine.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        cur_engine = getattr(config, "SPEECH_ENGINE", "azure").lower()
        self.combo_engine.setCurrentIndex(0 if cur_engine == "azure" else 1)
        self.combo_engine.currentIndexChanged.connect(self.on_engine_changed)
        content_layout.addWidget(self.combo_engine)

        # --- Conteneur Azure Speech ---
        self.box_azure = QWidget(content_widget)
        self.box_azure.setStyleSheet("""
            QWidget#box_azure {
                background-color: #161b22;
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 8px;
            }
        """)
        self.box_azure.setObjectName("box_azure")
        box_azure_layout = QVBoxLayout(self.box_azure)
        box_azure_layout.setContentsMargins(10, 10, 10, 10)
        box_azure_layout.setSpacing(8)

        self.lbl_azure_key = QLabel("Clé AZURE_SPEECH_KEY :", self.box_azure)
        box_azure_layout.addWidget(self.lbl_azure_key)

        self.edit_azure_key = QLineEdit(self.box_azure)
        self.edit_azure_key.setText(config.CONFIG.get("AZURE_SPEECH_KEY", ""))
        self.edit_azure_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.edit_azure_key.setPlaceholderText("Collez votre clé Azure Speech...")
        self.edit_azure_key.textChanged.connect(self.on_azure_key_changed)
        box_azure_layout.addWidget(self.edit_azure_key)

        self.lbl_azure_region = QLabel("Région Azure Speech :", self.box_azure)
        box_azure_layout.addWidget(self.lbl_azure_region)

        self.edit_azure_region = QLineEdit(self.box_azure)
        self.edit_azure_region.setText(config.CONFIG.get("AZURE_SPEECH_REGION", "francecentral"))
        self.edit_azure_region.setPlaceholderText("ex: francecentral, westeurope...")
        self.edit_azure_region.textChanged.connect(self.on_azure_region_changed)
        box_azure_layout.addWidget(self.edit_azure_region)

        content_layout.addWidget(self.box_azure)

        # --- Conteneur Langue Source (Visible uniquement si Azure est actif) ---
        self.box_source_lang = QWidget(content_widget)
        self.box_source_lang.setStyleSheet("""
            QWidget#box_source_lang {
                background-color: #161b22;
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 8px;
            }
        """)
        self.box_source_lang.setObjectName("box_source_lang")
        box_source_layout = QVBoxLayout(self.box_source_lang)
        box_source_layout.setContentsMargins(10, 10, 10, 10)
        box_source_layout.setSpacing(6)

        self.lbl_azure_source = QLabel("Langue parlée au micro (Source - Azure) :", self.box_source_lang)
        box_source_layout.addWidget(self.lbl_azure_source)

        self.combo_azure_source = QComboBox(self.box_source_lang)
        self.combo_azure_source.setEditable(True)
        self.combo_azure_source.addItems([
            "Français (fr-FR)",
            "Anglais US (en-US)",
            "Anglais UK (en-GB)",
            "Espagnol (es-ES)",
            "Allemand (de-DE)",
            "Italien (it-IT)",
            "Japonais (ja-JP)",
            "Coréen (ko-KR)",
            "Portugais (pt-BR)",
            "Russe (ru-RU)",
            "Chinois (zh-CN)"
        ])
        cur_source = config.CONFIG.get("AZURE_SOURCE_LANG", "fr-FR")
        matched_idx = -1
        for i in range(self.combo_azure_source.count()):
            item_t = self.combo_azure_source.itemText(i)
            if f"({cur_source})" in item_t or item_t.strip() == cur_source.strip():
                matched_idx = i
                break
        if matched_idx >= 0:
            self.combo_azure_source.setCurrentIndex(matched_idx)
        else:
            self.combo_azure_source.setEditText(cur_source)
        self.combo_azure_source.currentTextChanged.connect(self.on_azure_source_changed)
        box_source_layout.addWidget(self.combo_azure_source)

        self.lbl_source_hint = QLabel("💡 Azure requiert la langue source. Gemini la détecte automatiquement.", self.box_source_lang)
        self.lbl_source_hint.setStyleSheet("color: #6e7681; font-size: 10px;")
        box_source_layout.addWidget(self.lbl_source_hint)

        content_layout.addWidget(self.box_source_lang)

        # --- Conteneur Gemini ---
        self.box_gemini = QWidget(content_widget)
        self.box_gemini.setStyleSheet("""
            QWidget#box_gemini {
                background-color: #161b22;
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 8px;
            }
        """)
        self.box_gemini.setObjectName("box_gemini")
        box_gemini_layout = QVBoxLayout(self.box_gemini)
        box_gemini_layout.setContentsMargins(10, 10, 10, 10)
        box_gemini_layout.setSpacing(8)

        self.lbl_api_key = QLabel("Clé GEMINI_API_KEY :", self.box_gemini)
        box_gemini_layout.addWidget(self.lbl_api_key)

        self.edit_api_key = QLineEdit(self.box_gemini)
        self.edit_api_key.setText(config.CONFIG.get("GEMINI_API_KEY", ""))
        self.edit_api_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.edit_api_key.setPlaceholderText("Collez votre clé API Gemini ici...")
        self.edit_api_key.textChanged.connect(self.on_gemini_key_changed)
        box_gemini_layout.addWidget(self.edit_api_key)

        content_layout.addWidget(self.box_gemini)

        # Synchroniser l'affichage conditionnel
        self.on_engine_changed(self.combo_engine.currentIndex())

        # 4. LANGUE CIBLE (Saisie libre)
        self.lbl_target_lang = QLabel("Langue traduite (Cible - Saisie libre) :", content_widget)
        content_layout.addWidget(self.lbl_target_lang)

        self.edit_target_lang = QLineEdit(content_widget)
        self.edit_target_lang.setText(str(config.CONFIG.get("TARGET_LANG", "en")))
        self.edit_target_lang.setPlaceholderText("ex: en, fr, ja, es-ES, de-DE, it, pt, ru...")
        self.edit_target_lang.textChanged.connect(self.on_target_lang_changed)
        content_layout.addWidget(self.edit_target_lang)

        self.lbl_target_hint = QLabel("Saisie libre : tapez votre code de langue cible (sauvegardé instantanément)", content_widget)
        self.lbl_target_hint.setStyleSheet("color: #6e7681; font-size: 10px; margin-top: -4px;")
        content_layout.addWidget(self.lbl_target_hint)

        # 5. MODE D'ACTIVATION
        self.lbl_record_mode = QLabel("Mode d'activation audio :", content_widget)
        content_layout.addWidget(self.lbl_record_mode)

        self.combo_record_mode = QComboBox(content_widget)
        self.combo_record_mode.addItems(["Maintenir pour parler (Hold)", "Appuyer / Réappuyer (Toggle)"])
        self.combo_record_mode.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        cur_mode = str(config.CONFIG.get("RECORD_MODE", "hold")).lower()
        self.combo_record_mode.setCurrentIndex(1 if cur_mode == "toggle" else 0)
        self.combo_record_mode.currentIndexChanged.connect(self.on_record_mode_changed)
        content_layout.addWidget(self.combo_record_mode)

        # 6. RACCOURCI CLAVIER
        self.lbl_hotkey = QLabel("Raccourci Clavier :", content_widget)
        content_layout.addWidget(self.lbl_hotkey)

        self.edit_hotkey = QLineEdit(content_widget)
        self.edit_hotkey.setText(config.CONFIG.get("HOTKEY", "f8"))
        self.edit_hotkey.setPlaceholderText("ex: f8, ctrl+shift+t...")
        self.edit_hotkey.textChanged.connect(self.on_hotkey_changed)
        content_layout.addWidget(self.edit_hotkey)

        # 7. RACCOURCI MANETTE (XInput)
        self.lbl_gamepad = QLabel("Raccourci Manette (XInput) :", content_widget)
        content_layout.addWidget(self.lbl_gamepad)

        gamepad_bar = QHBoxLayout()
        gamepad_bar.setContentsMargins(0, 0, 0, 0)
        gamepad_bar.setSpacing(6)

        initial_gamepad = config.GAMEPAD_BUTTON.upper() if config.GAMEPAD_BUTTON != "none" else "AUCUN"
        self.btn_capture_gamepad = QPushButton(f"Bouton : [{initial_gamepad}]", content_widget)
        self.btn_capture_gamepad.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.btn_capture_gamepad.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_capture_gamepad.clicked.connect(self.start_gamepad_capture)
        gamepad_bar.addWidget(self.btn_capture_gamepad, 1)

        self.btn_clear_gamepad = QPushButton("Aucun", content_widget)
        self.btn_clear_gamepad.setFixedWidth(60)
        self.btn_clear_gamepad.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.btn_clear_gamepad.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_clear_gamepad.clicked.connect(self.clear_gamepad_button)
        gamepad_bar.addWidget(self.btn_clear_gamepad)

        content_layout.addLayout(gamepad_bar)

        # 8. DUCKING AUDIO WINDOWS
        initial_ducking = int(float(config.CONFIG.get("DUCKING_LEVEL", 0.5)) * 100)
        self.lbl_ducking = QLabel(f"Ducking Audio (Atténuation : {initial_ducking}%)", content_widget)
        content_layout.addWidget(self.lbl_ducking)

        self.slider_ducking = QSlider(Qt.Orientation.Horizontal, content_widget)
        self.slider_ducking.setRange(0, 100)
        self.slider_ducking.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.slider_ducking.setValue(initial_ducking)
        self.slider_ducking.valueChanged.connect(self.on_ducking_changed)
        content_layout.addWidget(self.slider_ducking)

        # 9. AUTO-ENTRÉE
        self.chk_auto_enter = QCheckBox("Envoyer automatiquement (Entrée après injection)", content_widget)
        self.chk_auto_enter.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.chk_auto_enter.setChecked(bool(config.CONFIG.get("AUTO_ENTER", True)))
        self.chk_auto_enter.toggled.connect(self.on_auto_enter_toggled)
        content_layout.addWidget(self.chk_auto_enter)

        # 10. LANGUE DE L'INTERFACE (i18n)
        self.lbl_ui_lang = QLabel("Langue de l'interface :", content_widget)
        content_layout.addWidget(self.lbl_ui_lang)

        self.combo_ui_lang = QComboBox(content_widget)
        self.combo_ui_lang.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.combo_ui_lang.addItem("Français", "fr")
        self.combo_ui_lang.addItem("English", "en")
        cur_lang = getattr(config, "UI_LANG", "fr")
        self.combo_ui_lang.setCurrentIndex(1 if cur_lang == "en" else 0)
        self.combo_ui_lang.currentIndexChanged.connect(self.on_ui_lang_changed)
        content_layout.addWidget(self.combo_ui_lang)

        content_layout.addStretch(1)
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll, 1)

        # Bouton Fermer / Enregistrer
        self.btn_save = QPushButton("Fermer & Appliquer", self)
        self.btn_save.setFixedHeight(34)
        self.btn_save.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_save.setStyleSheet("""
            QPushButton {
                background-color: rgba(34, 211, 238, 0.18);
                border: 1px solid #22d3ee;
                border-radius: 6px;
                color: #22d3ee;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover { background-color: rgba(34, 211, 238, 0.35); color: #fff; }
            QPushButton:pressed { background-color: rgba(34, 211, 238, 0.55); }
        """)
        self.btn_save.clicked.connect(self.accept)
        main_layout.addWidget(self.btn_save)

        self.center_on_screen()

    def center_on_screen(self):
        screen = QApplication.primaryScreen()
        if screen:
            screen_geom = screen.geometry()
            x = (screen_geom.width() - self.width()) // 2
            y = (screen_geom.height() - self.height()) // 2
            self.move(x, y)

    def on_dock_edge_changed(self, index: int):
        edge = self.combo_dock.itemData(index)
        if edge in ("top", "bottom", "left", "right"):
            config.DOCK_EDGE = edge
            config.CONFIG["DOCK_EDGE"] = edge
            config.save_config(config.CONFIG)
            if self.hud and hasattr(self.hud, "set_dock_edge"):
                self.hud.set_dock_edge(edge)

    def on_mic_device_changed(self, index: int):
        dev_val = self.combo_mic_input.itemData(index)
        config.CONFIG["INPUT_DEVICE"] = dev_val
        config.save_config(config.CONFIG)

    def on_engine_changed(self, index: int):
        engines = ["azure", "gemini"]
        new_engine = engines[index] if 0 <= index < len(engines) else "azure"
        config.SPEECH_ENGINE = new_engine
        config.CONFIG["SPEECH_ENGINE"] = new_engine
        config.save_config(config.CONFIG)

        is_azure = (new_engine == "azure")
        self.box_azure.setVisible(is_azure)
        self.box_source_lang.setVisible(is_azure)
        self.box_gemini.setVisible(not is_azure)

    def on_azure_key_changed(self, text: str):
        config.AZURE_SPEECH_KEY = text.strip()
        config.CONFIG["AZURE_SPEECH_KEY"] = config.AZURE_SPEECH_KEY
        config.save_config(config.CONFIG)

    def on_azure_region_changed(self, text: str):
        val = text.strip()
        if val:
            config.AZURE_SPEECH_REGION = val
            config.CONFIG["AZURE_SPEECH_REGION"] = val
            config.save_config(config.CONFIG)

    def on_azure_source_changed(self, text: str):
        val = text.strip()
        if "(" in val and ")" in val:
            val = val.split("(")[-1].replace(")", "").strip()
        if val:
            config.AZURE_SOURCE_LANG = val
            config.CONFIG["AZURE_SOURCE_LANG"] = val
            config.save_config(config.CONFIG)

    def on_gemini_key_changed(self, text: str):
        config.GEMINI_API_KEY = text.strip()
        config.CONFIG["GEMINI_API_KEY"] = config.GEMINI_API_KEY
        config.save_config(config.CONFIG)
        from core.api import init_genai_client
        init_genai_client()

    def on_target_lang_changed(self, text: str):
        val = text.strip()
        if val:
            config.TARGET_LANG = val
            config.CONFIG["TARGET_LANG"] = val
            config.save_config(config.CONFIG)
            from core.api import init_genai_client
            init_genai_client()
            if config.hud_bridge and hasattr(config.hud_bridge, "target_lang_changed") and config.hud_bridge.target_lang_changed:
                config.hud_bridge.target_lang_changed.emit(val)

    def on_record_mode_changed(self, index: int):
        modes = ["hold", "toggle"]
        config.RECORD_MODE = modes[index]
        config.CONFIG["RECORD_MODE"] = config.RECORD_MODE
        config.save_config(config.CONFIG)

    def on_hotkey_changed(self, text: str):
        val = text.strip().lower()
        if val:
            config.HOTKEY_STR = val
            config.CONFIG["HOTKEY"] = val
            config.save_config(config.CONFIG)

    def on_ducking_changed(self, val: int):
        self.lbl_ducking.setText(f"Ducking Audio (Atténuation : {val}%)")
        config.DUCKING_LEVEL = float(val) / 100.0
        config.CONFIG["DUCKING_LEVEL"] = config.DUCKING_LEVEL
        config.save_config(config.CONFIG)

    def on_auto_enter_toggled(self, checked: bool):
        config.AUTO_ENTER = checked
        config.CONFIG["AUTO_ENTER"] = checked
        config.save_config(config.CONFIG)

    def on_ui_lang_changed(self, index: int):
        new_lang = self.combo_ui_lang.itemData(index)
        if new_lang:
            config.set_ui_language(new_lang)

    # --- Capture Manette non-bloquante avec timeout de 8 secondes ---
    def start_gamepad_capture(self):
        self.is_capturing_gamepad = True
        self.btn_capture_gamepad.setText("Actionnez la manette... (8s)")
        self.btn_capture_gamepad.setStyleSheet("color: #22d3ee; border: 1px solid #22d3ee; font-weight: bold;")
        self.gamepad_poll_timer.start(50)
        self.gamepad_timeout_timer.start(8000)

    def _check_gamepad_capture(self):
        btn = get_pressed_gamepad_button()
        if btn:
            self._finish_gamepad_capture(btn)

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
        self.btn_capture_gamepad.setText(f"Bouton : [{display_text}]")
        self.btn_capture_gamepad.setStyleSheet("")

    def clear_gamepad_button(self):
        if self.is_capturing_gamepad:
            self.gamepad_poll_timer.stop()
            self.gamepad_timeout_timer.stop()
            self.is_capturing_gamepad = False
        config.GAMEPAD_BUTTON = "none"
        config.CONFIG["GAMEPAD_BUTTON"] = "none"
        config.save_config(config.CONFIG)
        self.btn_capture_gamepad.setText("Bouton : [AUCUN]")
        self.btn_capture_gamepad.setStyleSheet("")

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() == Qt.MouseButton.LeftButton and not self.drag_position.isNull():
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def _dialog_stylesheet(self) -> str:
        return """
            QDialog {
                background-color: #1f1f1f;
                border: 1px solid #22d3ee;
                border-radius: 10px;
                color: #f0f6fc;
                font-family: 'Segoe UI', sans-serif;
            }
            QLabel { font-size: 12px; font-weight: 500; color: #8b949e; background: transparent; }
            QPushButton {
                background-color: rgba(255, 255, 255, 0.06);
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 6px;
                color: #f0f6fc;
                font-size: 12px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: rgba(34, 211, 238, 0.18);
                border: 1px solid #22d3ee;
            }
            QLineEdit {
                background-color: #161b22;
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 6px;
                padding: 6px;
                color: #22d3ee;
                font-weight: bold;
                font-size: 12px;
            }
            QLineEdit:focus {
                border: 1px solid #22d3ee;
                background-color: #0d1117;
            }
            QComboBox {
                background-color: #161b22;
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 6px;
                padding: 4px 8px;
                color: #f0f6fc;
                font-size: 12px;
            }
            QComboBox:hover { border: 1px solid #22d3ee; }
            QComboBox::drop-down { border: none; }
            QComboBox QAbstractItemView {
                background-color: #161b22;
                color: #f0f6fc;
                selection-background-color: #22d3ee;
                selection-color: #0d1117;
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 6px;
                padding: 4px;
            }
            QSlider::groove:horizontal {
                border-radius: 2px;
                height: 4px;
                background: rgba(255, 255, 255, 0.15);
            }
            QSlider::handle:horizontal {
                background: #22d3ee;
                width: 14px;
                height: 14px;
                margin: -5px 0;
                border-radius: 7px;
            }
            QSlider::handle:horizontal:hover { background: #38bdf8; }
            QCheckBox {
                color: #8b949e;
                font-family: 'Segoe UI', sans-serif;
                font-size: 12px;
                spacing: 8px;
                background: transparent;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border-radius: 3px;
                border: 1px solid rgba(255, 255, 255, 0.2);
                background: #161b22;
            }
            QCheckBox::indicator:hover { border: 1px solid #22d3ee; }
            QCheckBox::indicator:checked { background: #22d3ee; }
        """

# Alias de compatibilité
SettingsPage = SettingsDialog
