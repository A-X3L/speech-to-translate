import os
import sys
import math
import threading
from typing import Optional, Any
from PyQt6.QtCore import Qt, QPoint, QTimer, QSize, pyqtSignal
from PyQt6.QtWidgets import (
    QApplication, QWidget, QHBoxLayout, QVBoxLayout, QPushButton,
    QMenu, QSystemTrayIcon
)
from PyQt6.QtGui import (
    QColor, QPainter, QIcon, QMouseEvent, QBrush, QPen, QFont,
    QAction, QPixmap
)

import config
from core.api import declencher_action_micro
from core.flags import flag_manager, resolve_country_code
from ui.settings import SettingsDialog
from ui.help import HelpDialog


class FlagBadgeWidget(QWidget):
    """
    Badge drapeau dynamique pour la langue cible.
    Affiche le drapeau officiel depuis le cache local (cache/flags/) ou Flagcdn en arrière-plan.
    En cas de mode hors ligne ou de téléchargement en cours, affiche un fallback textuel propre.
    """
    clicked = pyqtSignal()

    def __init__(self, parent=None, is_horizontal: bool = True):
        super().__init__(parent)
        self.is_horizontal = is_horizontal
        self.target_lang = config.TARGET_LANG
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.update_dimensions()
        self.update_tooltip()

        # Connexions aux mises à jour dynamiques
        if flag_manager and flag_manager.flag_ready:
            flag_manager.flag_ready.connect(self.on_flag_downloaded)
        if config.hud_bridge and hasattr(config.hud_bridge, "target_lang_changed") and config.hud_bridge.target_lang_changed:
            config.hud_bridge.target_lang_changed.connect(self.on_target_lang_changed)

    def update_dimensions(self):
        if self.is_horizontal:
            self.setFixedSize(24, 16)
        else:
            self.setFixedSize(20, 14)
        self.update()

    def update_tooltip(self):
        desc = config.get_tgt_desc()
        self.setToolTip(f"Langue cible : {desc}\n(Cliquer pour ouvrir l'Atelier de Configuration)")

    def set_target_lang(self, lang_code: str):
        self.target_lang = lang_code.strip().lower()
        self.update_tooltip()
        self.update()

    def on_target_lang_changed(self, new_lang: str):
        self.set_target_lang(new_lang)

    def on_flag_downloaded(self, country: str):
        if country == resolve_country_code(self.target_lang):
            self.update()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
            event.accept()
        else:
            super().mousePressEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        w = self.width()
        h = self.height()

        pix = flag_manager.get_flag_pixmap(self.target_lang, target_w=w - 2, target_h=h - 2)

        if pix and not pix.isNull():
            # Rendu du drapeau avec bordure subtile
            px = (w - pix.width()) // 2
            py = (h - pix.height()) // 2
            painter.drawPixmap(px, py, pix)
            painter.setPen(QPen(QColor(255, 255, 255, 40), 1.0))
            painter.drawRect(px, py, pix.width() - 1, pix.height() - 1)
        else:
            # Fallback textuel élégant (code pays à 2 lettres) sur fond anthracite
            painter.fillRect(0, 0, w, h, QColor(36, 41, 47))
            painter.setPen(QPen(QColor(56, 189, 248, 180), 1.0))
            painter.drawRect(0, 0, w - 1, h - 1)

            country_text = resolve_country_code(self.target_lang).upper()[:2]
            painter.setPen(QColor(224, 242, 254))
            font = QFont("Segoe UI", 7, QFont.Weight.Bold)
            painter.setFont(font)
            painter.drawText(0, 0, w, h, Qt.AlignmentFlag.AlignCenter, country_text)


class VoiceEqualizerWidget(QWidget):
    """
    Égaliseur vocal dynamique à 5 barrettes acoustiques réactives.
    Remplace définitivement l'ancien logo AI Studio et la bulle centrale.
    S'anime en temps réel selon le volume du microphone (volume_level),
    pulse lors du traitement et vire au rouge en cas d'erreur.
    Cliquer dessus démarre ou arrête la dictée vocale.
    """
    clicked = pyqtSignal()

    def __init__(self, parent=None, is_horizontal: bool = True):
        super().__init__(parent)
        self.is_horizontal = is_horizontal
        self.current_state = "idle"
        self.volume_level = 0.0
        self.pulse_phase = 0.0
        self.pulse_dir = 1.0
        self.is_muted = config.IS_MUTED

        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.update_dimensions()
        self.update_tooltip()

        if config.hud_bridge and hasattr(config.hud_bridge, "mute_changed") and config.hud_bridge.mute_changed:
            config.hud_bridge.mute_changed.connect(self.on_mute_changed)

    def update_dimensions(self):
        if self.is_horizontal:
            self.setFixedSize(52, 20)
        else:
            self.setFixedSize(20, 52)
        self.update()

    def update_tooltip(self):
        if self.is_muted:
            self.setToolTip("Microphone coupé [MUTE]\n(Actionnez le bouton Mute pour réactiver)")
        elif self.current_state == "recording":
            self.setToolTip("Écoute audio active... Parlez !\n(Cliquer pour arrêter la dictée)")
        elif self.current_state == "processing":
            self.setToolTip("Traduction IA en cours...")
        else:
            self.setToolTip("Speech to Translate\n(Cliquer ou appuyer sur F8 pour dicter)")

    def set_state(self, state: str):
        self.current_state = state
        if state == "idle":
            self.volume_level = 0.0
            self.pulse_phase = 0.0
        self.update_tooltip()
        self.update()

    def set_volume(self, level: float):
        self.volume_level = max(0.0, min(1.0, level))
        self.update()

    def on_mute_changed(self, muted: bool):
        self.is_muted = muted
        self.update_tooltip()
        self.update()

    def step_animation(self):
        self.pulse_phase += 0.08 * self.pulse_dir
        if self.pulse_phase >= 1.0:
            self.pulse_phase = 1.0
            self.pulse_dir = -1.0
        elif self.pulse_phase <= 0.0:
            self.pulse_phase = 0.0
            self.pulse_dir = 1.0
        self.update()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
            event.accept()
        else:
            super().mousePressEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()

        num_bars = 5
        bar_thickness = 3
        bar_spacing = 3
        weights = [0.65, 0.9, 1.25, 0.95, 0.7]
        phase_offsets = [0.0, 1.2, 2.5, 3.8, 5.0]

        if self.is_horizontal:
            total_span = num_bars * bar_thickness + (num_bars - 1) * bar_spacing
            start_x = (w - total_span) / 2.0
            center_y = h / 2.0
            max_bar_h = 16.0
            min_bar_h = 3.0

            for i in range(num_bars):
                bx = start_x + i * (bar_thickness + bar_spacing)

                if self.is_muted:
                    bar_h = 2.0
                    bar_color = QColor(100, 116, 139) # Ardoise sourdine
                elif self.current_state == "recording":
                    # Barrettes acoustiques réactives au volume sonore et modulation organique
                    dynamic_boost = self.volume_level * weights[i] + 0.12 * math.sin(self.pulse_phase * 6.0 + phase_offsets[i])
                    bar_h = min_bar_h + (max_bar_h - min_bar_h) * max(0.0, min(1.0, dynamic_boost))
                    bar_color = QColor(34, 211, 238) # Cyan vif
                elif self.current_state == "processing":
                    # Vague d'onde fluide en phase d'envoi IA
                    wave = 0.5 + 0.5 * math.sin(self.pulse_phase * 7.0 + i * 1.1)
                    bar_h = min_bar_h + (max_bar_h - min_bar_h) * wave
                    bar_color = QColor(14, 165, 233) # Bleu azur électrique
                elif self.current_state in ("error", "focus_error"):
                    # Alerte rouge
                    bar_h = 8.0 + 4.0 * math.sin(self.pulse_phase * 10.0 + i)
                    bar_color = QColor(239, 68, 68) # Rouge vif
                else:
                    # Veille sobre (profil acoustique au repos)
                    idle_heights = [4.0, 6.0, 9.0, 6.0, 4.0]
                    bar_h = idle_heights[i]
                    bar_color = QColor(34, 211, 238, 160)

                by = center_y - (bar_h / 2.0)
                painter.setBrush(QBrush(bar_color))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawRoundedRect(int(bx), int(by), bar_thickness, int(max(2.0, bar_h)), 1.5, 1.5)

        else:
            # Mode vertical pour les ancrages latéraux gauche et droit
            total_span = num_bars * bar_thickness + (num_bars - 1) * bar_spacing
            start_y = (h - total_span) / 2.0
            center_x = w / 2.0
            max_bar_w = 14.0
            min_bar_w = 3.0

            for i in range(num_bars):
                by = start_y + i * (bar_thickness + bar_spacing)

                if self.is_muted:
                    bar_w = 2.0
                    bar_color = QColor(100, 116, 139)
                elif self.current_state == "recording":
                    dynamic_boost = self.volume_level * weights[i] + 0.12 * math.sin(self.pulse_phase * 6.0 + phase_offsets[i])
                    bar_w = min_bar_w + (max_bar_w - min_bar_w) * max(0.0, min(1.0, dynamic_boost))
                    bar_color = QColor(34, 211, 238)
                elif self.current_state == "processing":
                    wave = 0.5 + 0.5 * math.sin(self.pulse_phase * 7.0 + i * 1.1)
                    bar_w = min_bar_w + (max_bar_w - min_bar_w) * wave
                    bar_color = QColor(14, 165, 233)
                elif self.current_state in ("error", "focus_error"):
                    bar_w = 8.0 + 4.0 * math.sin(self.pulse_phase * 10.0 + i)
                    bar_color = QColor(239, 68, 68)
                else:
                    idle_widths = [4.0, 6.0, 9.0, 6.0, 4.0]
                    bar_w = idle_widths[i]
                    bar_color = QColor(34, 211, 238, 160)

                bx = center_x - (bar_w / 2.0)
                painter.setBrush(QBrush(bar_color))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawRoundedRect(int(bx), int(by), int(max(2.0, bar_w)), bar_thickness, 1.5, 1.5)


class MuteButtonWidget(QPushButton):
    """
    Interrupteur Mute discret pour couper ou autoriser l'écoute globale à la volée.
    Dessin vectoriel net du microphone actif (cyan/blanc) ou barré de rouge (Mute).
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_muted = config.IS_MUTED
        self.setFixedSize(20, 20)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet("background: transparent; border: none;")
        self.update_tooltip()

        self.clicked.connect(self.on_clicked)

        if config.hud_bridge and hasattr(config.hud_bridge, "mute_changed") and config.hud_bridge.mute_changed:
            config.hud_bridge.mute_changed.connect(self.on_mute_changed)

    def update_tooltip(self):
        if self.is_muted:
            self.setToolTip("Microphone coupé [MUTE]\n(Cliquer pour réactiver l'écoute)")
        else:
            self.setToolTip("Microphone actif\n(Cliquer pour couper l'écoute à la volée)")

    def on_clicked(self):
        config.toggle_mute()

    def on_mute_changed(self, muted: bool):
        self.is_muted = muted
        self.update_tooltip()
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()

        # Fond du bouton
        if self.is_muted:
            painter.setBrush(QBrush(QColor(239, 68, 68, 45)))
            painter.setPen(QPen(QColor(239, 68, 68, 180), 1.0))
        elif self.underMouse():
            painter.setBrush(QBrush(QColor(34, 211, 238, 35)))
            painter.setPen(QPen(QColor(34, 211, 238, 180), 1.0))
        else:
            painter.setBrush(QBrush(QColor(255, 255, 255, 15)))
            painter.setPen(QPen(QColor(255, 255, 255, 25), 1.0))

        painter.drawRoundedRect(0, 0, w - 1, h - 1, 4.0, 4.0)

        # Dessin vectoriel du microphone
        icon_color = QColor(239, 68, 68) if self.is_muted else (QColor(34, 211, 238) if self.underMouse() else QColor(229, 231, 235))
        painter.setPen(QPen(icon_color, 1.2))
        painter.setBrush(QBrush(icon_color))

        # Capsule du micro (w=4, h=7)
        cx = w / 2.0
        painter.drawRoundedRect(int(cx - 2), 4, 4, 7, 2.0, 2.0)

        # Berceau en U sous la capsule
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawArc(int(cx - 4), 6, 8, 7, 0, -180 * 16)

        # Pied et base
        painter.drawLine(int(cx), 13, int(cx), 15)
        painter.drawLine(int(cx - 3), 15, int(cx + 3), 15)

        # Diagonale de coupe rouge en état Mute
        if self.is_muted:
            painter.setPen(QPen(QColor(239, 68, 68), 1.8))
            painter.drawLine(3, 17, 17, 3)


class HUDWidget(QWidget):
    """
    Entité 1 : Le HUD Actif / Micro-Languette Triptyque.
    Micro-fenêtre ultra-légère 100% OPAQUE (#1f1f1f, sans WA_TranslucentBackground ni scintillement DWM).
    Ancrable sur les 4 bords de l'écran (Haut, Bas, Gauche, Droite) avec adaptation horizontale/verticale.
    Intègre le triptyque :
      1. Badge Drapeau de la Langue Cible (cache local + Flagcdn)
      2. Égaliseur Vocal Dynamique (centre)
      3. Interrupteur Mute discret
    Les Ateliers de Configuration (⚙) et d'Aide (❓) sont accessibles depuis le System Tray et par clic droit.
    """
    def __init__(self):
        super().__init__()
        self.current_state = "idle"
        self.drag_position = QPoint()

        # Bord d'aimantation actif : 'top', 'bottom', 'left', 'right'
        self.dock_edge = str(config.CONFIG.get("DOCK_EDGE", "top")).lower()
        if self.dock_edge not in ("top", "bottom", "left", "right"):
            self.dock_edge = "top"

        # Dimensions de la micro-languette
        self.HORIZ_W = 126
        self.HORIZ_H = 26
        self.VERT_W = 26
        self.VERT_H = 126

        self.dock_center_x = 960
        self.dock_center_y = 540

        # Dialogues indépendants (Entité 2)
        self.settings_dialog: Optional[SettingsDialog] = None
        self.help_dialog: Optional[HelpDialog] = None

        self.init_ui()
        self.init_system_tray()

        # Connexions du pont événementiel
        if config.hud_bridge:
            config.hud_bridge.state_changed.connect(self.on_state_changed)
            config.hud_bridge.volume_level.connect(self.on_volume_level)

        # Timer d'animation (pulse)
        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self.update_animation)
        self.anim_timer.start(50)

    def init_ui(self):
        self.setWindowIcon(QIcon(config.ICON_ICO_PATH))
        # Ancrage permanent premier plan sans transparence composite DWM instable
        flags = Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)

        # Initialisation de la position centrale
        screen = QApplication.primaryScreen()
        if screen:
            geom = screen.geometry()
            self.dock_center_x = geom.width() // 2
            self.dock_center_y = geom.height() // 2

        self.content_container = QWidget(self)
        self.build_triptyque_layout()
        self.position_on_screen()

    def build_triptyque_layout(self):
        """Construit le triptyque (Drapeau - Égaliseur - Mute) selon l'orientation."""
        if self.content_container.layout() is not None:
            old_layout = self.content_container.layout()
            while old_layout.count():
                item = old_layout.takeAt(0)
                w = item.widget()
                if w:
                    w.setParent(None)

        is_horizontal = self.dock_edge in ("top", "bottom")

        if is_horizontal:
            layout = QHBoxLayout(self.content_container)
            layout.setContentsMargins(5, 2, 5, 2)
            layout.setSpacing(6)
            layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        else:
            layout = QVBoxLayout(self.content_container)
            layout.setContentsMargins(2, 5, 2, 5)
            layout.setSpacing(6)
            layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 1. Badge Drapeau Langue Cible
        self.badge_flag = FlagBadgeWidget(self.content_container, is_horizontal=is_horizontal)
        self.badge_flag.clicked.connect(self.open_settings_dialog)
        layout.addWidget(self.badge_flag)

        # 2. Égaliseur Vocal Dynamique (Centre)
        self.equalizer = VoiceEqualizerWidget(self.content_container, is_horizontal=is_horizontal)
        self.equalizer.clicked.connect(self.on_equalizer_clicked)
        layout.addWidget(self.equalizer)

        # 3. Bouton Mute
        self.btn_mute = MuteButtonWidget(self.content_container)
        layout.addWidget(self.btn_mute)

    def init_system_tray(self):
        """Initialise l'icône et le menu contextuel dans la zone de notification Windows (System Tray)."""
        self.tray_icon = QSystemTrayIcon(self)
        if os.path.exists(config.ICON_ICO_PATH):
            self.tray_icon.setIcon(QIcon(config.ICON_ICO_PATH))
        self.tray_icon.setToolTip("Speech to Translate — Traducteur Vocal IA")

        tray_menu = self.create_context_menu()
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.on_tray_activated)
        self.tray_icon.show()

    def create_context_menu(self) -> QMenu:
        """Crée le menu contextuel unifié partagé entre le System Tray et le clic droit du HUD."""
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #1f1f1f;
                color: #f3f4f6;
                border: 1px solid #374151;
                padding: 4px;
                font-size: 12px;
            }
            QMenu::item {
                padding: 6px 18px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #0891b2;
                color: #ffffff;
            }
            QMenu::separator {
                height: 1px;
                background: #374151;
                margin: 4px 6px;
            }
        """)

        # Atelier de Configuration
        act_settings = QAction("⚙  Atelier de Configuration", self)
        act_settings.triggered.connect(self.open_settings_dialog)
        menu.addAction(act_settings)

        # Atelier d'Aide & Guide
        act_help = QAction("❓  Atelier d'Aide & Guide", self)
        act_help.triggered.connect(self.open_help_dialog)
        menu.addAction(act_help)

        menu.addSeparator()

        # Mute
        mute_label = "🔊  Réactiver le microphone" if config.IS_MUTED else "🔇  Couper le microphone (Mute)"
        act_mute = QAction(mute_label, self)
        act_mute.triggered.connect(config.toggle_mute)
        menu.addAction(act_mute)

        menu.addSeparator()

        # Bord d'ancrage
        sub_dock = menu.addMenu("📐  Bord d'ancrage")
        for edge_key, label in [("top", "Haut (Top)"), ("bottom", "Bas (Bottom)"), ("left", "Gauche (Left)"), ("right", "Droite (Right)")]:
            act_edge = QAction(label, self)
            act_edge.setCheckable(True)
            act_edge.setChecked(self.dock_edge == edge_key)
            act_edge.triggered.connect(lambda checked, ek=edge_key: self.set_dock_edge(ek))
            sub_dock.addAction(act_edge)

        menu.addSeparator()

        # Quitter
        act_quit = QAction("✕  Quitter Speech to Translate", self)
        act_quit.triggered.connect(self.close_application)
        menu.addAction(act_quit)

        return menu

    def on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.open_settings_dialog()

    def set_dock_edge(self, edge: str):
        """Change le bord d'ancrage actif et adapte l'orientation de la micro-languette."""
        if edge in ("top", "bottom", "left", "right"):
            self.dock_edge = edge
            config.DOCK_EDGE = edge
            config.CONFIG["DOCK_EDGE"] = edge
            config.save_config(config.CONFIG)
            self.build_triptyque_layout()
            self.position_on_screen()

    def position_on_screen(self):
        """Repositionne la micro-languette collée au bord actif avec fond 100% opaque."""
        screen = QApplication.primaryScreen()
        sw = screen.geometry().width() if screen else 1920
        sh = screen.geometry().height() if screen else 1080

        if self.dock_edge == "top":
            self.setFixedSize(self.HORIZ_W, self.HORIZ_H)
            self.content_container.setGeometry(0, 0, self.HORIZ_W, self.HORIZ_H)
            x = max(0, min(sw - self.HORIZ_W, self.dock_center_x - self.HORIZ_W // 2))
            self.move(x, 0)
        elif self.dock_edge == "bottom":
            self.setFixedSize(self.HORIZ_W, self.HORIZ_H)
            self.content_container.setGeometry(0, 0, self.HORIZ_W, self.HORIZ_H)
            x = max(0, min(sw - self.HORIZ_W, self.dock_center_x - self.HORIZ_W // 2))
            self.move(x, sh - self.HORIZ_H)
        elif self.dock_edge == "left":
            self.setFixedSize(self.VERT_W, self.VERT_H)
            self.content_container.setGeometry(0, 0, self.VERT_W, self.VERT_H)
            y = max(0, min(sh - self.VERT_H, self.dock_center_y - self.VERT_H // 2))
            self.move(0, y)
        elif self.dock_edge == "right":
            self.setFixedSize(self.VERT_W, self.VERT_H)
            self.content_container.setGeometry(0, 0, self.VERT_W, self.VERT_H)
            y = max(0, min(sh - self.VERT_H, self.dock_center_y - self.VERT_H // 2))
            self.move(sw - self.VERT_W, y)

        self.update()

    def open_settings_dialog(self):
        """Ouvre l'Atelier de Configuration indépendant (Entité 2)."""
        if not self.settings_dialog:
            self.settings_dialog = SettingsDialog(self)
        self.settings_dialog.show()
        self.settings_dialog.raise_()
        self.settings_dialog.activateWindow()

    def open_help_dialog(self):
        """Ouvre l'Atelier d'Aide & Guide indépendant (Entité 2)."""
        if not self.help_dialog:
            self.help_dialog = HelpDialog(self)
        self.help_dialog.update_shortcuts_display()
        self.help_dialog.show()
        self.help_dialog.raise_()
        self.help_dialog.activateWindow()

    def on_equalizer_clicked(self):
        """Déclenchement réactif de l'enregistrement au clic sur l'égaliseur."""
        if config.IS_MUTED:
            return
        if self.current_state == "idle":
            threading.Thread(target=declencher_action_micro, daemon=True).start()
        elif self.current_state == "recording" and config.RECORD_MODE == "toggle":
            config.stop_toggle_recording.set()

    def update_animation(self):
        if self.equalizer:
            self.equalizer.step_animation()

    def on_state_changed(self, state_str: str):
        self.current_state = state_str
        if self.equalizer:
            self.equalizer.set_state(state_str)
        self.update()

    def on_volume_level(self, level: float):
        if self.equalizer:
            self.equalizer.set_volume(level)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
        elif event.button() == Qt.MouseButton.RightButton:
            # Menu contextuel direct au clic droit sur le HUD
            menu = self.create_context_menu()
            menu.exec(event.globalPosition().toPoint())
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() == Qt.MouseButton.LeftButton and not self.drag_position.isNull():
            screen = QApplication.primaryScreen()
            sw = screen.geometry().width() if screen else 1920
            sh = screen.geometry().height() if screen else 1080

            curr_pos = event.globalPosition().toPoint() - self.drag_position
            if self.dock_edge in ("top", "bottom"):
                new_x = max(0, min(sw - self.width(), curr_pos.x()))
                self.dock_center_x = new_x + self.width() // 2
                y = 0 if self.dock_edge == "top" else (sh - self.height())
                self.move(new_x, y)
            else:
                new_y = max(0, min(sh - self.height(), curr_pos.y()))
                self.dock_center_y = new_y + self.height() // 2
                x = 0 if self.dock_edge == "left" else (sw - self.width())
                self.move(x, new_y)
            event.accept()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()

        # Fond 100% OPAQUE anthracite stable (#1f1f1f)
        painter.fillRect(0, 0, w, h, QColor(31, 31, 31))

        # Fine bordure d'état cyan (#22d3ee) ou alerte rouge (#ef4444)
        if self.current_state == "recording":
            border_col = QColor(34, 211, 238)
            border_w = 1.5
        elif self.current_state in ("error", "focus_error"):
            border_col = QColor(239, 68, 68)
            border_w = 1.5
        elif config.IS_MUTED:
            border_col = QColor(239, 68, 68, 120)
            border_w = 1.0
        else:
            border_col = QColor(34, 211, 238, 140)
            border_w = 1.0

        painter.setPen(QPen(border_col, border_w))
        painter.drawRect(0, 0, w - 1, h - 1)

    def close_application(self):
        sys.exit(0)
