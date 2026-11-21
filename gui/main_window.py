"""gui/main_window.py - หน้าต่างหลัก"""
import os

from dotenv import set_key
from PySide6.QtCore import QTimer, Qt, QObject, Signal
from PySide6.QtGui import QColor, QImage, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QFileDialog, QGraphicsDropShadowEffect, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QPlainTextEdit, QPushButton, QVBoxLayout, QWidget,
)

import config
from characters.character_manager import CharacterManager
from engines.ocr_engine import grab_preview, list_monitors
from gui.character_editor import CharacterEditor
from gui.styles import PILL
from gui.widgets import make_card
from pipeline import Engine


class Bridge(QObject):
    """ส่งสัญญาณจาก thread ของ engine เข้า GUI thread อย่างปลอดภัย"""
    log = Signal(str)
    state = Signal(str)
    subtitle = Signal(str, object)


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("root")
        self.setWindowTitle("Game Voice Translator — พากย์ไทยด้วย AI")
        self.resize(1100, 800)
        self.setMinimumSize(1000, 780)

        self.manager = CharacterManager()
        self.bridge = Bridge()
        self.bridge.log.connect(self.append_log)
        self.bridge.state.connect(self.set_state)
        self.bridge.subtitle.connect(self.show_subtitle)
        self.engine = Engine(
            self.manager,
            log=self.bridge.log.emit,
            on_state=self.bridge.state.emit,
            on_subtitle=self.bridge.subtitle.emit,
        )
        self.state = "idle"

        self.build_ui()
        self.scan_monitors()

        self.preview_timer = QTimer(self)
        self.preview_timer.timeout.connect(self.update_preview)
        self.preview_timer.start(1500)

    # ---------------- UI ----------------
    def build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(28, 24, 28, 24)
        outer.setSpacing(18)

        header = QHBoxLayout()
        titles = QVBoxLayout()
        titles.setSpacing(2)
        title = QLabel("🎮  Game Voice Translator")
        title.setObjectName("title")
        sub = QLabel("อ่านซับอังกฤษจากหน้าจอเกม → ระบุผู้พูด → แปลเป็นไทยด้วย Gemini → พากย์เสียงไทยด้วย AI")
        sub.setObjectName("subtitle")
        titles.addWidget(title)
        titles.addWidget(sub)
        header.addLayout(titles)
        header.addStretch()
        self.char_btn = QPushButton("👥  จัดการตัวละคร")
        self.char_btn.clicked.connect(self.open_character_editor)
        header.addWidget(self.char_btn, alignment=Qt.AlignVCenter)
        self.pill = QLabel()
        self.pill.setObjectName("pill")
        header.addWidget(self.pill, alignment=Qt.AlignVCenter)
        outer.addLayout(header)

        body = QHBoxLayout()
        body.setSpacing(20)
        outer.addLayout(body, 1)

        # ---------- Left ----------
        left = QVBoxLayout()
        left.setSpacing(16)
        body.addLayout(left, 5)

        c1, l1 = make_card(1, "เลือกจอที่ใช้จับซับ",
                           "โปรแกรมสแกนจอที่ต่ออยู่ให้อัตโนมัติ — กรอบสีม่วงคือบริเวณด้านล่างที่ใช้อ่านซับ")
        row = QHBoxLayout()
        self.monitor_combo = QComboBox()
        self.monitor_combo.currentIndexChanged.connect(self.update_preview)
        self.rescan_btn = QPushButton("⟳  สแกนจอใหม่")
        self.rescan_btn.clicked.connect(self.scan_monitors)
        row.addWidget(self.monitor_combo, 1)
        row.addWidget(self.rescan_btn)
        l1.addLayout(row)
        self.preview = QLabel()
        self.preview.setObjectName("preview")
        self.preview.setAlignment(Qt.AlignCenter)
        self.preview.setFixedHeight(180)
        l1.addWidget(self.preview)
        left.addWidget(c1)

        c2, l2 = make_card(2, "Gemini API Key",
                           "รับคีย์ฟรีได้ที่ aistudio.google.com/apikey — คีย์จะถูกบันทึกในไฟล์ .env บนเครื่องคุณเท่านั้น")
        krow = QHBoxLayout()
        self.key_edit = QLineEdit(os.getenv("GEMINI_API_KEY", ""))
        self.key_edit.setPlaceholderText("วาง Gemini API Key ที่นี่")
        self.key_edit.setEchoMode(QLineEdit.Password)
        self.eye_btn = QPushButton("👁")
        self.eye_btn.setFixedWidth(46)
        self.eye_btn.setCheckable(True)
        self.eye_btn.toggled.connect(
            lambda on: self.key_edit.setEchoMode(QLineEdit.Normal if on else QLineEdit.Password)
        )
        self.save_btn = QPushButton("💾  บันทึก")
        self.save_btn.setObjectName("primary")
        self.save_btn.clicked.connect(self.save_key)
        krow.addWidget(self.key_edit, 1)
        krow.addWidget(self.eye_btn)
        krow.addWidget(self.save_btn)
        l2.addLayout(krow)
        self.key_status = QLabel("")
        self.key_status.setObjectName("hint")
        l2.addWidget(self.key_status)

        crow = QHBoxLayout()
        self.cred_edit = QLineEdit(os.getenv("GOOGLE_APPLICATION_CREDENTIALS", ""))
        self.cred_edit.setPlaceholderText("ไฟล์ Google Cloud TTS (.json) — สำหรับเสียงพากย์")
        self.cred_edit.setReadOnly(True)
        cred_btn = QPushButton("📁  เลือกไฟล์")
        cred_btn.clicked.connect(self.pick_credentials)
        crow.addWidget(self.cred_edit, 1)
        crow.addWidget(cred_btn)
        l2.addLayout(crow)
        left.addWidget(c2)

        self.start_btn = QPushButton("▶   เริ่มการทำงาน")
        self.start_btn.setObjectName("start")
        self.start_btn.setCursor(Qt.PointingHandCursor)
        self.start_btn.clicked.connect(self.toggle_run)
        glow = QGraphicsDropShadowEffect(self.start_btn)
        glow.setBlurRadius(36)
        glow.setOffset(0, 6)
        glow.setColor(QColor(124, 92, 255, 140))
        self.start_btn.setGraphicsEffect(glow)
        left.addWidget(self.start_btn)
        left.addStretch()

        # ---------- Right ----------
        right = QVBoxLayout()
        right.setSpacing(16)
        body.addLayout(right, 6)

        c3, l3 = make_card("💬", "ซับล่าสุด")
        self.speaker_label = QLabel("")
        self.speaker_label.setObjectName("speaker")
        self.en_label = QLabel("— รอซับจากเกม —")
        self.en_label.setObjectName("subEn")
        self.en_label.setWordWrap(True)
        self.th_label = QLabel("")
        self.th_label.setObjectName("subTh")
        self.th_label.setWordWrap(True)
        l3.addWidget(self.speaker_label)
        l3.addWidget(self.en_label)
        l3.addWidget(self.th_label)
        c3.setMinimumHeight(190)
        right.addWidget(c3)

        c4, l4 = make_card("📜", "บันทึกการทำงาน")
        self.log_box = QPlainTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setMaximumBlockCount(400)
        l4.addWidget(self.log_box, 1)
        right.addWidget(c4, 1)

        self.set_state("idle")

    # ---------------- Monitors / preview ----------------
    def scan_monitors(self):
        current = self.monitor_combo.currentData()
        self.monitor_combo.blockSignals(True)
        self.monitor_combo.clear()
        monitors = list_monitors()
        for m in monitors:
            self.monitor_combo.addItem(m["label"], m["index"])
        if current is not None:
            pos = self.monitor_combo.findData(current)
            if pos >= 0:
                self.monitor_combo.setCurrentIndex(pos)
        self.monitor_combo.blockSignals(False)
        self.append_log(f"สแกนพบ {len(monitors)} จอ")
        self.update_preview()

    def update_preview(self):
        idx = self.monitor_combo.currentData()
        if idx is None:
            return
        try:
            img = grab_preview(idx, 520)
        except Exception as exc:
            self.preview.setText(f"แสดงตัวอย่างไม่ได้: {exc}")
            return
        h, w, _ = img.shape
        qimg = QImage(img.data, w, h, 3 * w, QImage.Format_RGB888).copy()
        p = QPainter(qimg)
        y = int(h * (1 - config.BOTTOM_RATIO))
        p.fillRect(0, y, w, h - y, QColor(124, 92, 255, 80))
        pen = QPen(QColor(124, 92, 255))
        pen.setWidth(3)
        p.setPen(pen)
        p.drawRect(1, y, w - 3, h - y - 2)
        p.end()
        pm = QPixmap.fromImage(qimg).scaled(
            self.preview.width() - 4, self.preview.height() - 4,
            Qt.KeepAspectRatio, Qt.SmoothTransformation,
        )
        self.preview.setPixmap(pm)

    # ---------------- Settings ----------------
    def _write_env(self, key, value):
        config.ENV_PATH.touch(exist_ok=True)
        set_key(str(config.ENV_PATH), key, value)
        os.environ[key] = value

    def save_key(self):
        key = self.key_edit.text().strip()
        if not key:
            self.key_status.setText("⚠️  กรุณากรอก API Key ก่อนบันทึก")
            self.key_status.setStyleSheet("color:#ffc14d;")
            return
        self._write_env("GEMINI_API_KEY", key)
        self.key_status.setText("✅  บันทึกเรียบร้อยแล้ว")
        self.key_status.setStyleSheet("color:#34d399;")
        self.append_log("บันทึก Gemini API Key แล้ว")

    def pick_credentials(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "เลือกไฟล์ Google Cloud credentials", "", "JSON (*.json)"
        )
        if path:
            self.cred_edit.setText(path)
            self._write_env("GOOGLE_APPLICATION_CREDENTIALS", path)
            self.append_log("ตั้งค่าไฟล์ Google TTS credentials แล้ว")

    def open_character_editor(self):
        CharacterEditor(self.manager, self).exec()

    # ---------------- Run control ----------------
    def toggle_run(self):
        if self.state in ("loading", "running"):
            self.engine.stop()
            return
        if self.state == "stopping":
            return

        key = self.key_edit.text().strip()
        if not key:
            self.key_status.setText("⚠️  ต้องกรอกและบันทึก API Key ก่อนเริ่มทำงาน")
            self.key_status.setStyleSheet("color:#ffc14d;")
            return
        if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS") and not self.cred_edit.text():
            self.append_log("[WARN] ยังไม่ได้เลือกไฟล์ Google TTS credentials — เสียงอาจใช้งานไม่ได้")

        idx = self.monitor_combo.currentData()
        if idx is None:
            self.append_log("[ERROR] ไม่พบจอ ลองกดสแกนจอใหม่")
            return
        self.engine.start(idx, key)

    def set_state(self, state):
        self.state = state
        text, css = PILL[state]
        self.pill.setText(text)
        self.pill.setStyleSheet(css)

        locked = state in ("loading", "running", "stopping")
        self.monitor_combo.setEnabled(not locked)
        self.rescan_btn.setEnabled(not locked)
        self.key_edit.setEnabled(not locked)
        self.save_btn.setEnabled(not locked)

        if state == "loading":
            self.start_btn.setObjectName("stop")
            self.start_btn.setText("■   ยกเลิก")
            self.start_btn.setEnabled(True)
        elif state == "running":
            self.start_btn.setObjectName("stop")
            self.start_btn.setText("■   หยุดการทำงาน")
            self.start_btn.setEnabled(True)
        elif state == "stopping":
            self.start_btn.setObjectName("start")
            self.start_btn.setText("กำลังหยุด...")
            self.start_btn.setEnabled(False)
        else:
            self.start_btn.setObjectName("start")
            self.start_btn.setText("▶   เริ่มการทำงาน")
            self.start_btn.setEnabled(True)
        self.start_btn.style().unpolish(self.start_btn)
        self.start_btn.style().polish(self.start_btn)

        if hasattr(self, "preview_timer"):
            if state in ("loading", "running"):
                self.preview_timer.stop()
            elif state in ("idle", "error"):
                self.preview_timer.start(1500)

    # ---------------- Live updates ----------------
    def append_log(self, msg):
        self.log_box.appendPlainText(msg)

    def show_subtitle(self, kind, data):
        if kind == "en":
            tag = f"🗣  {data['speaker_name']}"
            if data["method"] == "context":
                tag += "  (เดาจากบทสนทนาก่อนหน้า)"
            self.speaker_label.setText(tag)
            self.en_label.setText(data["english"])
            self.th_label.setText("…")
        else:
            self.th_label.setText(data["thai"])

    def closeEvent(self, event):
        if self.engine.active:
            self.engine.stop()
        event.accept()
