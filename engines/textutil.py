"""engines/textutil.py - ฟังก์ชันจัดการข้อความ"""
import re


def normalize_text(text):
    """ใช้กับข้อความ *อังกฤษ* จาก OCR เท่านั้น (ห้ามใช้กับภาษาไทย ดู clean_translation)"""
    text = re.sub(r"\s+", " ", text or "").strip()
    text = re.sub(r"^[\W_]+", "", text)
    # เก็บ . ! ? … ท้ายประโยคไว้ เพราะเป็นสัญญาณอารมณ์สำหรับการแปล/พากย์ (Phase 3-4)
    text = re.sub(r"[^\w.!?…]+$", "", text)
    return text


def clean_translation(text):
    """ล้างคำแปลภาษาไทย: ยุบช่องว่างและตัดเครื่องหมายคำพูดครอบ
    หมายเหตุ: ห้ามใช้ regex \\W ตัดท้ายข้อความ เพราะสระ/วรรณยุกต์ไทย (เช่น ่ ้ ี ิ) ไม่นับเป็น \\w
    จะทำให้คำว่า "ไม่" กลายเป็น "ไม" """
    text = re.sub(r"\s+", " ", text or "").strip()
    return text.strip("\"'“”‘’ ")


def group_boxes_into_lines(boxes):
    """รวมกล่องข้อความจาก OCR เป็น 'บรรทัด' พร้อมตำแหน่ง
    boxes: list ของ (x_left, y_top, y_bottom, text)
    คืน: list ของ {"text", "x", "y"} เรียงบนลงล่าง
    """
    boxes = sorted(boxes, key=lambda b: (b[1] + b[2]) / 2)
    rows = []
    for x, top, bottom, text in boxes:
        cy = (top + bottom) / 2
        h = max(bottom - top, 1)
        if rows and abs(cy - rows[-1]["cy"]) <= 0.6 * max(h, rows[-1]["h"]):
            row = rows[-1]
            row["items"].append((x, text))
            row["cy"] += (cy - row["cy"]) / len(row["items"])
            row["h"] = max(row["h"], h)
        else:
            rows.append({"cy": cy, "h": h, "items": [(x, text)]})

    lines = []
    for row in rows:
        row["items"].sort(key=lambda it: it[0])
        line = re.sub(r"\s+", " ", " ".join(t for _, t in row["items"])).strip()
        if line:
            lines.append({"text": line, "x": row["items"][0][0], "y": row["cy"]})
    return lines
