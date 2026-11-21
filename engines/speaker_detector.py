"""engines/speaker_detector.py - ระบุว่าใครเป็นผู้พูด (Auto)

ลำดับการตัดสิน:
  1. หาชื่อผู้พูดจากซับ ("Name: ...", "[Name] ...", หรือบรรทัดแรกสั้นๆ ที่เป็นชื่อ)
  2. เทียบกับ characters.json (ทนต่อ OCR เพี้ยนเล็กน้อย)
  3. เจอ -> ใช้ character_id นั้น
  4. ไม่เจอชื่อเลย + เพิ่งมีผู้พูดที่ยืนยันด้วยชื่อในช่วงบทสนทนาเดียวกัน -> ใช้ผู้พูดเดิม (method = "context")
  5. นอกนั้น -> "unknown" (ไม่เดา)
"""
import re
import time

import config
from characters.character_manager import UNKNOWN_ID
from engines.textutil import normalize_text

COLON_RE = re.compile(r"^\s*([A-Za-z][A-Za-z0-9 '\.\-]{0,23}?)\s*[:：]\s*(\S.*)$")
BRACKET_RE = re.compile(r"^\s*[\[\(<]\s*([A-Za-z][A-Za-z0-9 '\.\-]{0,23}?)\s*[\]\)>]\s*(.*)$")


def _looks_like_name(line):
    return (
        len(line) <= 24
        and len(line.split()) <= 3
        and re.match(r"^[A-Za-z]", line) is not None
        and not re.search(r"[.!?,…\"“”]$", line)
    )


class SpeakerDetector:
    def __init__(self, manager):
        self.manager = manager
        self.last_id = None
        self.last_time = 0.0

    @staticmethod
    def _result(cid, text, label, method):
        return {"character_id": cid, "text": text, "speaker_label": label, "method": method}

    @staticmethod
    def _extract_label(texts):
        """คืน (label, dialogue_lines, explicit) หรือ (None, texts, False)"""
        m = COLON_RE.match(texts[0])
        if m:
            return m.group(1).strip(), [m.group(2)] + texts[1:], True
        m = BRACKET_RE.match(texts[0])
        if m:
            rest = ([m.group(2)] if m.group(2) else []) + texts[1:]
            if rest:
                return m.group(1).strip(), rest, True
        if len(texts) >= 2 and _looks_like_name(texts[0]):
            return texts[0], texts[1:], False
        return None, texts, False

    def detect(self, lines, now=None):
        now = time.time() if now is None else now
        texts = [t.strip() for t in lines if t and t.strip()]
        if not texts:
            return self._result(UNKNOWN_ID, "", None, "unknown")

        label, dialogue, explicit = self._extract_label(texts)
        if label:
            cid = self.manager.match_name(label)
            if cid:
                self.last_id, self.last_time = cid, now
                return self._result(cid, normalize_text(" ".join(dialogue)), label, "name")
            if explicit:
                # มีป้ายชื่อชัดเจนแต่ไม่ใช่ตัวละครที่เรารู้จัก -> ไม่เดา และไม่ใช้ผู้พูดเก่าต่อ
                self.last_id = None
                return self._result(UNKNOWN_ID, normalize_text(" ".join(texts)), label, "unknown")

        full = normalize_text(" ".join(texts))
        if (
            self.last_id
            and self.manager.get(self.last_id)
            and now - self.last_time <= config.SPEAKER_CONTEXT_SECONDS
        ):
            return self._result(self.last_id, full, None, "context")
        return self._result(UNKNOWN_ID, full, None, "unknown")
