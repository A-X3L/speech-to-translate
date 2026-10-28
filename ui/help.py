import os
import sys
from typing import Optional, Any
from PyQt6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QScrollArea, QFrame, QApplication
)
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QIcon, QMouseEvent

import config

class HelpDialog(QDialog):
    """
    Entité 2 : L'Atelier d'Aide & Guide Rapide.
    Fenêtre de dialogue indépendante et opaque (#1f1f1f), accessible depuis le HUD
    ou le System Tray, sans encombrer la micro-fenêtre d'écoute.
    """
    def __init__(self, parent_hud=None):
        super().__init__(parent_hud)
        self.hud = parent_hud
        self.drag_position = QPoint()
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Speech to Translate — " + config.get_msg("help_workshop_title"))
        self.setWindowIcon(QIcon(config.ICON_ICO_PATH))
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Dialog
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setFixedSize(360, 520)
        self.setStyleSheet(self._dialog_stylesheet())

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(8)

        # En-tête
        header = QHBoxLayout()
        header.setContentsMargins(4, 2, 4, 2)
        header.setSpacing(8)

        title_lbl = QLabel(f"? {config.get_msg('help_workshop_title')}", self)
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

        # Zone déroulante
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

        # 1. CARTE MOTEUR ACTIF
        card_engine = QFrame()
        card_engine.setStyleSheet("""
            QFrame {
                background-color: #161b22;
                border: 1px solid rgba(34, 211, 238, 0.3);
                border-radius: 8px;
            }
        """)
        engine_vbox = QVBoxLayout(card_engine)
        engine_vbox.setContentsMargins(10, 8, 10, 8)
        engine_vbox.setSpacing(4)

        lbl_engine_title = QLabel("MOTEUR DE RECONNAISSANCE")
        lbl_engine_title.setStyleSheet("font-size: 10px; font-weight: bold; color: #8b949e; letter-spacing: 0.5px;")
        engine_vbox.addWidget(lbl_engine_title)

        self.lbl_engine_val = QLabel("Azure Speech (Streaming continu)")
        self.lbl_engine_val.setStyleSheet("font-size: 12px; font-weight: bold; color: #22d3ee;")
        engine_vbox.addWidget(self.lbl_engine_val)

        self.lbl_key_status = QLabel("Clé API : Configurée")
        self.lbl_key_status.setStyleSheet("font-size: 11px; color: #a7f3d0;")
        engine_vbox.addWidget(self.lbl_key_status)

        self.lbl_target_lang = QLabel("Langue Cible : Anglais (EN)")
        self.lbl_target_lang.setStyleSheet("font-size: 11px; color: #cbd5e1;")
        engine_vbox.addWidget(self.lbl_target_lang)

        content_layout.addWidget(card_engine)

        # 2. CARTE CONTRÔLES ACTIFS
        card_shortcuts = QFrame()
        card_shortcuts.setStyleSheet("""
            QFrame {
                background-color: #161b22;
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 8px;
            }
        """)
        shortcuts_vbox = QVBoxLayout(card_shortcuts)
        shortcuts_vbox.setContentsMargins(10, 8, 10, 8)
        shortcuts_vbox.setSpacing(4)

        lbl_sc_title = QLabel("CONTRÔLES ACTIFS")
        lbl_sc_title.setStyleSheet("font-size: 10px; font-weight: bold; color: #8b949e; letter-spacing: 0.5px;")
        shortcuts_vbox.addWidget(lbl_sc_title)

        self.lbl_hotkey_val = QLabel("Clavier : F8")
        self.lbl_hotkey_val.setStyleSheet("font-size: 11px; color: #f8fafc;")
        shortcuts_vbox.addWidget(self.lbl_hotkey_val)

        self.lbl_gamepad_val = QLabel("Manette : R_THUMB (RS / R3)")
        self.lbl_gamepad_val.setStyleSheet("font-size: 11px; color: #f8fafc;")
        shortcuts_vbox.addWidget(self.lbl_gamepad_val)

        self.lbl_mode_val = QLabel("Mode : Maintenir pour parler (Hold)")
        self.lbl_mode_val.setStyleSheet("font-size: 11px; color: #8b949e;")
        shortcuts_vbox.addWidget(self.lbl_mode_val)

        self.lbl_dock_val = QLabel("Ancrage : Bord Supérieur (Haut)")
        self.lbl_dock_val.setStyleSheet("font-size: 11px; color: #8b949e;")
        shortcuts_vbox.addWidget(self.lbl_dock_val)

        content_layout.addWidget(card_shortcuts)

        # 3. CARTE GUIDE FONCTIONNEMENT
        card_guide = QFrame()
        card_guide.setStyleSheet("""
            QFrame {
                background-color: #161b22;
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 8px;
            }
        """)
        guide_vbox = QVBoxLayout(card_guide)
        guide_vbox.setContentsMargins(10, 8, 10, 8)
        guide_vbox.setSpacing(6)

        lbl_guide_title = QLabel("GUIDE D'UTILISATION")
        lbl_guide_title.setStyleSheet("font-size: 10px; font-weight: bold; color: #8b949e; letter-spacing: 0.5px;")
        guide_vbox.addWidget(lbl_guide_title)

        tip1 = QLabel("<b>1. Déclenchement instantané :</b> Appuyez sur F8 ou le bouton central pour parler. L'écoute démarre à la milliseconde sans bloquer.")
        tip1.setStyleSheet("font-size: 11px; color: #cbd5e1;")
        tip1.setWordWrap(True)
        guide_vbox.addWidget(tip1)

        tip2 = QLabel("<b>2. Tiroir Rétractable Opaque :</b> Le HUD s'aimante sur l'un des 4 bords de l'écran et se rétracte en languette lumineuse réactive.")
        tip2.setStyleSheet("font-size: 11px; color: #cbd5e1;")
        tip2.setWordWrap(True)
        guide_vbox.addWidget(tip2)

        tip3 = QLabel("<b>3. Ducking Audio :</b> Le son Windows est atténué pendant la dictée et restauré immédiatement après l'injection.")
        tip3.setStyleSheet("font-size: 11px; color: #cbd5e1;")
        tip3.setWordWrap(True)
        guide_vbox.addWidget(tip3)

        content_layout.addWidget(card_guide)

        # 4. BOUTON OUVRIR DOCUMENTATION HTML COMPLÈTE
        self.btn_open_doc = QPushButton("📖 Ouvrir la documentation complète (help.html)", content_widget)
        self.btn_open_doc.setFixedHeight(34)
        self.btn_open_doc.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_open_doc.setStyleSheet("""
            QPushButton {
                background-color: rgba(34, 211, 238, 0.15);
                border: 1px solid #22d3ee;
                border-radius: 6px;
                color: #22d3ee;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover { background-color: rgba(34, 211, 238, 0.3); color: #fff; }
        """)
        self.btn_open_doc.clicked.connect(config.open_help_documentation)
        content_layout.addWidget(self.btn_open_doc)

        content_layout.addStretch(1)
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll, 1)

        # Bouton Fermer
        self.btn_close = QPushButton("Fermer", self)
        self.btn_close.setFixedHeight(34)
        self.btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_close.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 6px;
                color: #f0f6fc;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover { background-color: rgba(255, 255, 255, 0.15); }
        """)
        self.btn_close.clicked.connect(self.accept)
        main_layout.addWidget(self.btn_close)

        self.update_shortcuts_display()
        self.center_on_screen()

    def center_on_screen(self):
        screen = QApplication.primaryScreen()
        if screen:
            screen_geom = screen.geometry()
            x = (screen_geom.width() - self.width()) // 2
            y = (screen_geom.height() - self.height()) // 2
            self.move(x, y)

    def update_shortcuts_display(self):
        engine = str(config.CONFIG.get("SPEECH_ENGINE", "azure")).strip().lower()
        if engine == "azure":
            self.lbl_engine_val.setText("Azure Speech (Streaming continu)")
            has_key = bool(str(config.CONFIG.get("AZURE_SPEECH_KEY", "")).strip())
            self.lbl_key_status.setText("Clé Azure : " + ("Configurée ✅" if has_key else "Non renseignée ⚠️"))
            self.lbl_key_status.setStyleSheet("font-size: 11px; color: " + ("#a7f3d0;" if has_key else "#f87171;"))
        else:
            m_name = config.CONFIG.get("GEMINI_MODEL", "gemini-3.5-flash-lite")
            self.lbl_engine_val.setText(f"Gemini Flash ({m_name})")
            has_key = bool(str(config.CONFIG.get("GEMINI_API_KEY", "")).strip())
            self.lbl_key_status.setText("Clé Gemini : " + ("Configurée ✅" if has_key else "Non renseignée ⚠️"))
            self.lbl_key_status.setStyleSheet("font-size: 11px; color: " + ("#a7f3d0;" if has_key else "#f87171;"))

        tl_desc = config.get_tgt_desc()
        self.lbl_target_lang.setText(f"Langue Cible : {tl_desc}")

        hotkey = config.CONFIG.get("HOTKEY", "f8").upper()
        self.lbl_hotkey_val.setText(f"Clavier : {hotkey}")

        gamepad = config.CONFIG.get("GAMEPAD_BUTTON", "r_thumb").upper()
        if gamepad == "NONE":
            self.lbl_gamepad_val.setText("Manette : Désactivée (Aucun)")
        else:
            self.lbl_gamepad_val.setText(f"Manette : [{gamepad}]")

        mode = str(config.CONFIG.get("RECORD_MODE", "hold")).lower()
        self.lbl_mode_val.setText("Mode : " + ("Bascule (Toggle)" if mode == "toggle" else "Maintenir (Hold)"))

        edge = str(config.CONFIG.get("DOCK_EDGE", "top")).lower()
        edge_labels = {
            "top": "Bord Supérieur (Haut)",
            "bottom": "Bord Inférieur (Bas)",
            "left": "Bord Latéral Gauche",
            "right": "Bord Latéral Droit"
        }
        self.lbl_dock_val.setText(f"Ancrage : {edge_labels.get(edge, 'Haut')}")

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
        """

# Alias de compatibilité
HelpPage = HelpDialog
