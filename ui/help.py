from typing import Optional, Any
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PyQt6.QtCore import Qt
import config

class HelpPage(QWidget):
    def __init__(self, parent_hud):
        super().__init__()
        self.hud = parent_hud
        self.setup_ui()
        
    def setup_ui(self):
        self.setStyleSheet(self.hud._panel_stylesheet())
        help_layout = QVBoxLayout(self)
        help_layout.setContentsMargins(14, 12, 14, 14)
        help_layout.setSpacing(10)

        help_header = QHBoxLayout()
        help_header.setContentsMargins(0, 0, 0, 0)
        help_header.setSpacing(8)

        btn_back_help = QPushButton("← Retour", self)
        btn_back_help.setFixedHeight(28)
        btn_back_help.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        btn_back_help.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_back_help.clicked.connect(self.hud.show_main_page)
        help_header.addWidget(btn_back_help)
        help_header.addStretch(1)
        help_layout.addLayout(help_header)

        lbl_desc = QLabel(
            "Speech To Translate est un outil de dictée\nvocale et de traduction assisté par l'IA Gemini.",
            self
        )
        lbl_desc.setWordWrap(True)
        lbl_desc.setStyleSheet("color: #cbd5e1; font-size: 13px;")
        help_layout.addWidget(lbl_desc)

        btn_open_doc = QPushButton("Ouvrir la documentation complète", self)
        btn_open_doc.setFixedHeight(36)
        btn_open_doc.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        btn_open_doc.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_open_doc.setStyleSheet("""
            QPushButton {
                background-color: rgba(34, 211, 238, 0.15);
                border: 1px solid #22d3ee;
                border-radius: 6px;
                color: #22d3ee;
                font-weight: bold;
            }
            QPushButton:hover { background-color: rgba(34, 211, 238, 0.3); }
        """)
        btn_open_doc.clicked.connect(config.open_help_documentation)
        help_layout.addWidget(btn_open_doc)

        help_layout.addStretch(1)

    def update_shortcuts_display(self):
        pass
