"""config.py - ตั้งค่าระบบทั้งหมด (อ่านจาก .env ได้)"""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"
load_dotenv(ENV_PATH)

# ---- Gemini ----
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
MAX_CONTEXT_TURNS = int(os.getenv("MAX_CONTEXT_TURNS", "4"))

# ---- OCR ----
OCR_INTERVAL = float(os.getenv("OCR_INTERVAL", "0.45"))
STABLE_HITS = int(os.getenv("STABLE_HITS", "2"))
BOTTOM_RATIO = float(os.getenv("BOTTOM_RATIO", "0.32"))
MIN_TEXT_LENGTH = int(os.getenv("MIN_TEXT_LENGTH", "3"))
# ซับต้องหายไปกี่รอบสแกนติดกัน ถึงจะถือว่า "จบประโยค" (แล้วประโยคเดิมกลับมาพูดซ้ำได้)
SUBTITLE_GONE_POLLS = int(os.getenv("SUBTITLE_GONE_POLLS", "3"))

# ---- Speaker detection ----
SPEAKER_MATCH_THRESHOLD = float(os.getenv("SPEAKER_MATCH_THRESHOLD", "0.82"))
# ใช้ผู้พูดล่าสุดต่อได้ไม่เกินกี่วินาที (เมื่อซับบรรทัดถัดมาไม่มีชื่อ)
SPEAKER_CONTEXT_SECONDS = float(os.getenv("SPEAKER_CONTEXT_SECONDS", "15"))

# ---- TTS ----
TTS_RATE = float(os.getenv("TTS_RATE", "1.0"))
TTS_GENDER = os.getenv("TTS_GENDER", "FEMALE").upper()

# ---- Paths ----
DB_PATH = Path(os.getenv("CACHE_DB", BASE_DIR / "database" / "history.db"))
CHARACTERS_PATH = Path(os.getenv("CHARACTERS_JSON", BASE_DIR / "characters" / "characters.json"))
