"""characters/character_manager.py - จัดการโปรไฟล์ตัวละคร (characters.json)"""
import copy
import json
import os
import re
import threading
from difflib import SequenceMatcher

import config

UNKNOWN_ID = "unknown"
UNKNOWN_LABEL = "ไม่ทราบผู้พูด"
EMOTIONS = ["neutral", "calm", "happy", "sad", "angry", "fear", "surprised", "whisper"]

DEFAULTS = {
    "name": "",
    "aliases": [],
    "voice_description": "",
    "personality": "",
    "voice_id": None,
    "speaking_style": "",
    "default_emotion": "neutral",
}


def _norm(text):
    return re.sub(r"[^0-9a-z]+", "", (text or "").lower())


class CharacterManager:
    def __init__(self, path=None):
        self.path = path or config.CHARACTERS_PATH
        self._lock = threading.RLock()
        self._chars = {}
        self.load()

    # ---------- persistence ----------
    def load(self):
        with self._lock:
            self._chars = {}
            if not self.path.exists():
                return
            data = json.loads(self.path.read_text(encoding="utf-8"))
            for cid, raw in data.get("characters", {}).items():
                self._chars[cid] = {**copy.deepcopy(DEFAULTS), **raw}

    def save(self):
        with self._lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.path.with_suffix(".tmp")
            tmp.write_text(
                json.dumps({"characters": self._chars}, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            os.replace(tmp, self.path)

    # ---------- read ----------
    def all(self):
        with self._lock:
            return copy.deepcopy(self._chars)

    def get(self, cid):
        with self._lock:
            c = self._chars.get(cid)
            return copy.deepcopy(c) if c else None

    def display_name(self, cid):
        c = self.get(cid)
        return c["name"] if c else UNKNOWN_LABEL

    # ---------- write ----------
    def new_id(self, name):
        slug = re.sub(r"[^a-z0-9]+", "_", (name or "").lower()).strip("_") or "character"
        with self._lock:
            n = 1
            while f"{slug}_{n:02d}" in self._chars:
                n += 1
            return f"{slug}_{n:02d}"

    def add(self, name, **fields):
        with self._lock:
            cid = self.new_id(name)
            data = copy.deepcopy(DEFAULTS)
            data.update({k: v for k, v in fields.items() if k in DEFAULTS})
            data["name"] = name
            self._chars[cid] = data
            self.save()
            return cid

    def update(self, cid, **fields):
        with self._lock:
            if cid not in self._chars:
                raise KeyError(cid)
            for k, v in fields.items():
                if k in DEFAULTS:
                    self._chars[cid][k] = v
            self.save()

    def delete(self, cid):
        with self._lock:
            if self._chars.pop(cid, None) is not None:
                self.save()

    # ---------- matching ----------
    def match_name(self, text):
        """จับคู่ชื่อที่ OCR อ่านได้กับตัวละคร (ทนต่อ OCR เพี้ยนเล็กน้อย) คืน id หรือ None"""
        q = _norm(text)
        if len(q) < 2:
            return None
        best_id, best = None, 0.0
        with self._lock:
            for cid, c in self._chars.items():
                for cand in [c.get("name", "")] + list(c.get("aliases", [])):
                    n = _norm(cand)
                    if not n:
                        continue
                    if n == q:
                        return cid
                    ratio = SequenceMatcher(None, q, n).ratio()
                    if ratio > best:
                        best, best_id = ratio, cid
        return best_id if best >= config.SPEAKER_MATCH_THRESHOLD else None
