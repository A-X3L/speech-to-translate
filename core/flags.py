import os
import urllib.request
import threading
from typing import Optional, Dict, Any, Set

import config

CACHE_FLAGS_DIR = os.path.join(config.BASE_DIR, "cache", "flags")

# Table de correspondance codes de langue -> codes pays Flagcdn (ISO 3166-1-alpha-2)
LANG_TO_COUNTRY: Dict[str, str] = {
    "fr": "fr",
    "en": "us",   # Standard American Gaming English par défaut
    "es": "es",
    "de": "de",
    "it": "it",
    "pt": "pt",
    "ja": "jp",
    "ko": "kr",
    "ru": "ru",
    "zh": "cn",
    "nl": "nl",
    "pl": "pl",
    "sv": "se",
    "tr": "tr",
    "uk": "ua",
    "ar": "sa",
    "hi": "in",
    "el": "gr",
    "cs": "cz",
    "ro": "ro",
    "hu": "hu",
    "da": "dk",
    "fi": "fi",
    "no": "no",
    "id": "id",
    "th": "th",
    "vi": "vn"
}

def resolve_country_code(lang_code: str) -> str:
    """Détermine le code pays à 2 lettres à partir d'un code de langue (ex: 'en-US' -> 'us', 'fr' -> 'fr')."""
    s = str(lang_code).strip().lower()
    if not s:
        return "un"
    # Extraction du suffixe pays si présent (ex: es-MX, pt-BR, zh-CN)
    if "-" in s:
        parts = s.split("-")
        if len(parts) >= 2 and len(parts[1]) == 2:
            return parts[1]
    if "_" in s:
        parts = s.split("_")
        if len(parts) >= 2 and len(parts[1]) == 2:
            return parts[1]
    
    # Correspondance directe
    if s in LANG_TO_COUNTRY:
        return LANG_TO_COUNTRY[s]
    
    # Si code à 2 lettres standard
    base = s[:2]
    return LANG_TO_COUNTRY.get(base, base)

try:
    from PyQt6.QtCore import QObject, pyqtSignal, Qt
    from PyQt6.QtGui import QPixmap
    PYQT_FLAG_SUPPORT = True
except ImportError:
    PYQT_FLAG_SUPPORT = False

class FlagManager(QObject if PYQT_FLAG_SUPPORT else object):
    """
    Gestionnaire intelligent de drapeaux avec cache local sur disque (cache/flags/)
    et téléchargement asynchrone non-bloquant depuis Flagcdn.
    """
    if PYQT_FLAG_SUPPORT:
        flag_ready = pyqtSignal(str) # Émis avec le code pays lorsque le drapeau est disponible
    else:
        flag_ready = None

    def __init__(self):
        if PYQT_FLAG_SUPPORT:
            super().__init__()
        self._downloading_set = set()
        self._pixmap_cache: Dict[str, Any] = {}
        try:
            os.makedirs(CACHE_FLAGS_DIR, exist_ok=True)
        except Exception as e:
            print(f"[FLAGS] Impossible de créer le dossier cache : {e}")

    def get_flag_pixmap(self, lang_code: str, target_w: int = 22, target_h: int = 15) -> Optional[Any]:
        if not PYQT_FLAG_SUPPORT:
            return None

        country = resolve_country_code(lang_code)
        cache_key = f"{country}_{target_w}_{target_h}"
        
        if cache_key in self._pixmap_cache:
            return self._pixmap_cache[cache_key]

        local_path = os.path.join(CACHE_FLAGS_DIR, f"{country}.png")
        if os.path.exists(local_path):
            try:
                pix = QPixmap(local_path)
                if not pix.isNull():
                    scaled = pix.scaled(
                        target_w, target_h,
                        Qt.AspectRatioMode.IgnoreAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    self._pixmap_cache[cache_key] = scaled
                    return scaled
            except Exception:
                pass

        # Téléchargement asynchrone sans bloquer le thread graphique principal
        self.download_flag_async(country)
        return None

    def download_flag_async(self, country: str):
        if country in self._downloading_set or len(country) != 2:
            return
        self._downloading_set.add(country)

        def _worker():
            try:
                url = f"https://flagcdn.com/w40/{country}.png"
                req = urllib.request.Request(
                    url,
                    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) SpeechToTranslate/2.0"}
                )
                with urllib.request.urlopen(req, timeout=2.5) as response:
                    data = response.read()
                    if data and len(data) > 100:
                        file_path = os.path.join(CACHE_FLAGS_DIR, f"{country}.png")
                        with open(file_path, "wb") as f:
                            f.write(data)
                        if PYQT_FLAG_SUPPORT and self.flag_ready:
                            self.flag_ready.emit(country)
            except Exception:
                # Silencieux : le fallback textuel prend le relais en cas d'absence d'internet
                pass
            finally:
                self._downloading_set.discard(country)

        thread = threading.Thread(target=_worker, daemon=True)
        thread.start()

# Instance globale partagée
flag_manager = FlagManager()
