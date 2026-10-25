from typing import Optional, Any
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, QSlider, QComboBox, QCheckBox
from PyQt6.QtCore import Qt
import config
from core.inputs import get_pressed_gamepad_button

class SettingsPage(QWidget):
    def __init__(self, parent_hud):
        super().__init__()
        self.hud = parent_hud
        self.setup_ui()
        
    def setup_ui(self):
        self.setStyleSheet(self.hud._panel_stylesheet())
        settings_layout = QVBoxLayout(self)
        settings_layout.setContentsMargins(14, 12, 14, 14)
        settings_layout.setSpacing(10)

        settings_header = QHBoxLayout()
        settings_header.setContentsMargins(0, 0, 0, 0)
        settings_header.setSpacing(8)

        self.btn_back = QPushButton("Annuler", self)
        self.btn_back.setFixedHeight(28)
        self.btn_back.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.btn_back.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_back.clicked.connect(self.hud.show_main_page)
        settings_header.addWidget(self.btn_back)
        settings_header.addStretch(1)

        settings_layout.addLayout(settings_header)

        self.lbl_api_key = QLabel("Clé GEMINI_API_KEY :", self)
        settings_layout.addWidget(self.lbl_api_key)

        self.edit_api_key = QLineEdit(self)
        self.edit_api_key.setText(config.CONFIG.get("GEMINI_API_KEY", ""))
        self.edit_api_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.edit_api_key.setPlaceholderText("Collez votre clé API Gemini ici...")
        self.edit_api_key.textChanged.connect(self.hud.update_api_key)
        settings_layout.addWidget(self.edit_api_key)

        self.lbl_hotkey = QLabel("Raccourci Clavier :", self)
        settings_layout.addWidget(self.lbl_hotkey)

        self.edit_hotkey = QLineEdit(self)
        self.edit_hotkey.setText(config.CONFIG.get("HOTKEY", ""))
        self.edit_hotkey.setPlaceholderText("ex: f8, ctrl+shift+t...")
        self.edit_hotkey.textChanged.connect(self.hud.update_hotkey)
        settings_layout.addWidget(self.edit_hotkey)

        self.lbl_gamepad = QLabel("Raccourci Manette (XInput) :", self)
        settings_layout.addWidget(self.lbl_gamepad)

        gamepad_bar = QHBoxLayout()
        gamepad_bar.setContentsMargins(0, 0, 0, 0)
        gamepad_bar.setSpacing(6)

        initial_gamepad = config.GAMEPAD_BUTTON.upper() if config.GAMEPAD_BUTTON != "none" else "AUCUN"
        self.btn_capture_gamepad = QPushButton(f"Bouton : [{initial_gamepad}]", self)
        self.btn_capture_gamepad.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.btn_capture_gamepad.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_capture_gamepad.clicked.connect(self.hud.start_gamepad_capture)
        gamepad_bar.addWidget(self.btn_capture_gamepad, 1)

        self.btn_clear_gamepad = QPushButton("Aucun", self)
        self.btn_clear_gamepad.setFixedWidth(60)
        self.btn_clear_gamepad.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.btn_clear_gamepad.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_clear_gamepad.clicked.connect(self.hud.clear_gamepad_button)
        gamepad_bar.addWidget(self.btn_clear_gamepad)

        settings_layout.addLayout(gamepad_bar)

        initial_ducking = int(float(config.CONFIG.get("DUCKING_LEVEL", 0.5)) * 100)
        self.lbl_ducking = QLabel(f"Ducking Audio (Atténuation : {initial_ducking}%)", self)
        settings_layout.addWidget(self.lbl_ducking)

        self.slider_ducking = QSlider(Qt.Orientation.Horizontal, self)
        self.slider_ducking.setRange(0, 100)
        self.slider_ducking.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.slider_ducking.setValue(initial_ducking)
        self.slider_ducking.valueChanged.connect(self.on_ducking_changed)
        settings_layout.addWidget(self.slider_ducking)

        self.lbl_record_mode = QLabel("Mode d'activation", self)
        settings_layout.addWidget(self.lbl_record_mode)

        self.combo_record_mode = QComboBox(self)
        self.combo_record_mode.addItems(["Maintenir (Hold)", "Bascule (Toggle)"])
        self.combo_record_mode.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        current_mode = str(config.CONFIG.get("RECORD_MODE", "hold")).strip().lower()
        self.combo_record_mode.setCurrentIndex(1 if current_mode == "toggle" else 0)
        self.combo_record_mode.currentIndexChanged.connect(self.hud.update_record_mode)
        settings_layout.addWidget(self.combo_record_mode)

        self.lbl_target_lang = QLabel("Langue traduite (Cible) :", self)
        settings_layout.addWidget(self.lbl_target_lang)

        self.combo_target_lang = QComboBox(self)
        self.combo_target_lang.addItems([
            "Anglais (en)",
            "Français (fr)",
            "Espagnol (es)",
            "Allemand (de)"
        ])
        self.combo_target_lang.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        cur_lang = str(config.CONFIG.get("TARGET_LANG", "en")).strip().lower()
        lang_codes = ["en", "fr", "es", "de"]
        self.combo_target_lang.setCurrentIndex(lang_codes.index(cur_lang) if cur_lang in lang_codes else 0)
        self.combo_target_lang.currentIndexChanged.connect(self.hud.update_target_lang)
        settings_layout.addWidget(self.combo_target_lang)

        self.chk_auto_enter = QCheckBox("Envoyer automatiquement (Entrée après injection)", self)
        self.chk_auto_enter.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.chk_auto_enter.setChecked(bool(config.CONFIG.get("AUTO_ENTER", True)))
        self.chk_auto_enter.toggled.connect(self.hud.update_auto_enter)
        settings_layout.addWidget(self.chk_auto_enter)

        settings_layout.addStretch(1)

        self.btn_save = QPushButton("Valider / Enregistrer", self)
        self.btn_save.setFixedHeight(36)
        self.btn_save.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_save.setStyleSheet("""
            QPushButton {
                background-color: rgba(34, 211, 238, 0.2);
                border: 1px solid #22d3ee;
                border-radius: 6px;
                color: #22d3ee;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover { background-color: rgba(34, 211, 238, 0.4); }
            QPushButton:pressed { background-color: rgba(34, 211, 238, 0.6); color: #fff; }
        """)
        self.btn_save.clicked.connect(self.hud.show_main_page)
        settings_layout.addWidget(self.btn_save)

    def on_ducking_changed(self, val):
        self.lbl_ducking.setText(f"Ducking Audio (Atténuation : {val}%)")
        self.hud.update_ducking_level(val)
