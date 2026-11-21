"""engines/ocr_engine.py - จับภาพจอ + อ่านซับด้วย PaddleOCR (เก็บแยกบรรทัดพร้อมตำแหน่ง)"""
import re

import cv2
import mss
import numpy as np

import config
from engines.textutil import group_boxes_into_lines, normalize_text


# -------------------- Monitors --------------------
def list_monitors():
    """สแกนจอที่ต่ออยู่ (index เริ่มที่ 1 ตามแบบของ mss)"""
    result = []
    with mss.mss() as sct:
        for i, m in enumerate(sct.monitors[1:], start=1):
            result.append({
                "index": i,
                "width": m["width"],
                "height": m["height"],
                "label": f"จอ {i}  •  {m['width']}×{m['height']}",
            })
    return result


def grab_preview(monitor_index, max_width=520):
    """แคปภาพจอแบบย่อ (RGB) ไว้แสดง preview"""
    with mss.mss() as sct:
        monitors = sct.monitors
        if monitor_index >= len(monitors):
            monitor_index = 1
        shot = np.array(sct.grab(monitors[monitor_index]))
    frame = cv2.cvtColor(shot, cv2.COLOR_BGRA2RGB)
    h, w = frame.shape[:2]
    scale = max_width / float(w)
    frame = cv2.resize(frame, (max_width, max(1, int(h * scale))), interpolation=cv2.INTER_AREA)
    return np.ascontiguousarray(frame)


def likely_subtitle(text):
    if len(text) < config.MIN_TEXT_LENGTH:
        return False
    if not re.search(r"[A-Za-z]", text):
        return False
    letters = sum(ch.isalpha() for ch in text)
    return letters / max(len(text), 1) >= 0.45


# -------------------- OCR --------------------
class SubtitleOCR:
    def __init__(self, monitor_index):
        from paddleocr import PaddleOCR

        self.monitor_index = monitor_index
        self.ocr = PaddleOCR(use_angle_cls=False, lang="en", show_log=False)
        self.last_candidate = ""
        self.same_count = 0
        self.absent_count = 0
        self.last_emitted = ""

    def capture_bottom(self):
        with mss.mss() as sct:
            monitors = sct.monitors
            idx = self.monitor_index if self.monitor_index < len(monitors) else 1
            shot = np.array(sct.grab(monitors[idx]))
        frame = cv2.cvtColor(shot, cv2.COLOR_BGRA2BGR)
        h = frame.shape[0]
        return frame[int(h * (1.0 - config.BOTTOM_RATIO)):h, :]

    def read_lines(self):
        """คืนรายการบรรทัด [{"text","x","y"}] เรียงบนลงล่าง"""
        crop = self.capture_bottom()
        crop = cv2.resize(crop, None, fx=1.35, fy=1.35, interpolation=cv2.INTER_CUBIC)
        result = self.ocr.ocr(crop, cls=False)

        boxes = []
        if result and result[0]:
            for item in result[0]:
                try:
                    box, rec = item
                    text, confidence = rec
                    if confidence >= 0.55 and text:
                        xs = [p[0] for p in box]
                        ys = [p[1] for p in box]
                        boxes.append((min(xs), min(ys), max(ys), text))
                except (TypeError, ValueError):
                    continue
        return group_boxes_into_lines(boxes)

    def poll(self):
        """คืน {"text": ข้อความรวม, "lines": [...]} เมื่อซับนิ่งพอและเป็นประโยคใหม่ ไม่งั้นคืน None"""
        lines = self.read_lines()
        full = normalize_text(" ".join(l["text"] for l in lines))

        if not likely_subtitle(full):
            self.last_candidate = ""
            self.same_count = 0
            self.absent_count += 1
            # แก้บั๊กเดิม: ซับหายไปนานพอ -> ล้าง last_emitted เพื่อให้ประโยคเดิมที่กลับมาถูกส่งอีกได้
            if self.absent_count >= config.SUBTITLE_GONE_POLLS:
                self.last_emitted = ""
            return None

        self.absent_count = 0
        if full == self.last_candidate:
            self.same_count += 1
        else:
            self.last_candidate = full
            self.same_count = 1

        if self.same_count >= config.STABLE_HITS and full != self.last_emitted:
            self.last_emitted = full
            return {"text": full, "lines": lines}
        return None
