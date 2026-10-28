import sys
from typing import Optional
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QRadioButton, QButtonGroup, QCheckBox, QFrame, QApplication
)
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QColor, QIcon, QMouseEvent

import config

class LanguageSelectionDialog(QDialog):
    """
    Assistant de premier lancement / Sélecteur de langue (i18n).
    Fenêtre opaque stable (#1f1f1f) sans WA_TranslucentBackground pour éviter tout crash DWM.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.drag_position = QPoint()
        self.selected_lang = getattr(config, "UI_LANG", "fr")
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Speech to Translate — Langue / Language")
        self.setWindowIcon(QIcon(config.ICON_ICO_PATH))
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Dialog
        )
        # Opaque stable background (#1f1f1f) - Jamais de WA_TranslucentBackground
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setFixedSize(360, 260)
        self.setStyleSheet("""
            QDialog {
                background-color: #1f1f1f;
                border: 1px solid #22d3ee;
                border-radius: 10px;
            }
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(18, 16, 18, 16)
        main_layout.setSpacing(12)

        # En-tête
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        title_lbl = QLabel("Speech to Translate", self)
        title_lbl.setStyleSheet("font-size: 15px; font-weight: bold; color: #22d3ee; background: transparent; border: none;")
        header_layout.addWidget(title_lbl)
        header_layout.addStretch(1)

        btn_close = QPushButton("✕", self)
        btn_close.setFixedSize(22, 22)
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: rgba(255, 255, 255, 0.5);
                font-size: 12px;
                font-weight: bold;
                border-radius: 11px;
            }
            QPushButton:hover { background: rgba(239, 68, 68, 0.85); color: #fff; }
        """)
        btn_close.clicked.connect(self.reject)
        header_layout.addWidget(btn_close)
        main_layout.addLayout(header_layout)

        # Message d'accueil bilingue
        prompt_lbl = QLabel("Choisissez votre langue / Choose your language :", self)
        prompt_lbl.setStyleSheet("font-size: 12px; color: #94a3b8; background: transparent; border: none;")
        prompt_lbl.setWordWrap(True)
        main_layout.addWidget(prompt_lbl)

        # Groupe de sélection
        self.btn_group = QButtonGroup(self)
        
        lang_layout = QHBoxLayout()
        lang_layout.setSpacing(12)

        self.radio_fr = QRadioButton("🇫🇷 Français", self)
        self.radio_fr.setCursor(Qt.CursorShape.PointingHandCursor)
        self.radio_fr.setStyleSheet(self._radio_stylesheet())
        self.btn_group.addButton(self.radio_fr, 1)

        self.radio_en = QRadioButton("🇬🇧 English", self)
        self.radio_en.setCursor(Qt.CursorShape.PointingHandCursor)
        self.radio_en.setStyleSheet(self._radio_stylesheet())
        self.btn_group.addButton(self.radio_en, 2)

        if self.selected_lang == "en":
            self.radio_en.setChecked(True)
        else:
            self.radio_fr.setChecked(True)

        lang_layout.addWidget(self.radio_fr)
        lang_layout.addWidget(self.radio_en)
        main_layout.addLayout(lang_layout)

        # Case à cocher "Ne plus afficher"
        self.chk_remember = QCheckBox("Ne plus afficher au prochain démarrage\nDo not show again on next startup", self)
        self.chk_remember.setChecked(True)
        self.chk_remember.setCursor(Qt.CursorShape.PointingHandCursor)
        self.chk_remember.setStyleSheet("""
            QCheckBox {
                color: #cbd5e1;
                font-size: 11px;
                spacing: 8px;
                background: transparent;
                border: none;
            }
            QCheckBox::indicator {
                width: 15px;
                height: 15px;
                border-radius: 3px;
                border: 1px solid rgba(255, 255, 255, 0.25);
                background: #161b22;
            }
            QCheckBox::indicator:hover { border: 1px solid #22d3ee; }
            QCheckBox::indicator:checked { background: #22d3ee; }
        """)
        main_layout.addWidget(self.chk_remember)

        # Bouton Confirmer
        self.btn_confirm = QPushButton("Valider et Lancer / Confirm", self)
        self.btn_confirm.setFixedHeight(34)
        self.btn_confirm.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_confirm.setStyleSheet("""
            QPushButton {
                background-color: rgba(34, 211, 238, 0.2);
                border: 1px solid #22d3ee;
                border-radius: 6px;
                color: #22d3ee;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(34, 211, 238, 0.4);
                color: #ffffff;
            }
            QPushButton:pressed {
                background-color: rgba(34, 211, 238, 0.6);
            }
        """)
        self.btn_confirm.clicked.connect(self.on_confirm)
        main_layout.addWidget(self.btn_confirm)

        self.center_on_screen()

    def _radio_stylesheet(self) -> str:
        return """
            QRadioButton {
                color: #f8fafc;
                font-size: 13px;
                font-weight: 600;
                padding: 6px 12px;
                background: #161b22;
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 6px;
            }
            QRadioButton:hover {
                border: 1px solid #22d3ee;
                background: rgba(34, 211, 238, 0.12);
            }
            QRadioButton:checked {
                border: 1px solid #22d3ee;
                background: rgba(34, 211, 238, 0.25);
                color: #22d3ee;
            }
            QRadioButton::indicator { width: 0px; height: 0px; }
        """

    def center_on_screen(self):
        screen = QApplication.primaryScreen()
        if screen:
            screen_geom = screen.geometry()
            x = (screen_geom.width() - self.width()) // 2
            y = (screen_geom.height() - self.height()) // 2
            self.move(x, y)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() == Qt.MouseButton.LeftButton and not self.drag_position.isNull():
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def on_confirm(self):
        chosen_lang = "en" if self.radio_en.isChecked() else "fr"
        config.set_ui_language(chosen_lang)
        
        remember = self.chk_remember.isChecked()
        config.SHOW_LANG_SELECTOR = not remember
        config.CONFIG["SHOW_LANG_SELECTOR"] = config.SHOW_LANG_SELECTOR
        config.save_config(config.CONFIG)
        
        self.accept()
