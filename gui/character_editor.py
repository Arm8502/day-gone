"""gui/character_editor.py - หน้าเพิ่ม/แก้ไข/ลบตัวละคร"""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox, QDialog, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QMessageBox, QPushButton, QVBoxLayout,
)

from characters.character_manager import EMOTIONS
from gui.widgets import make_card


class CharacterEditor(QDialog):
    def __init__(self, manager, parent=None):
        super().__init__(parent)
        self.setObjectName("root")
        self.setWindowTitle("จัดการตัวละคร")
        self.resize(880, 560)
        self.manager = manager
        self.current_id = None

        outer = QHBoxLayout(self)
        outer.setContentsMargins(24, 24, 24, 24)
        outer.setSpacing(18)

        # ---- left: list ----
        left = QVBoxLayout()
        title = QLabel("👥  ตัวละคร")
        title.setObjectName("title")
        title.setStyleSheet("font-size:20px;")
        left.addWidget(title)
        self.list = QListWidget()
        self.list.currentItemChanged.connect(self.on_select)
        left.addWidget(self.list, 1)
        row = QHBoxLayout()
        add_btn = QPushButton("＋  เพิ่ม")
        add_btn.setObjectName("primary")
        add_btn.clicked.connect(self.add_character)
        self.del_btn = QPushButton("🗑  ลบ")
        self.del_btn.setObjectName("danger")
        self.del_btn.clicked.connect(self.delete_character)
        row.addWidget(add_btn)
        row.addWidget(self.del_btn)
        left.addLayout(row)
        outer.addLayout(left, 3)

        # ---- right: form ----
        card, lay = make_card("✎", "โปรไฟล์ตัวละคร",
                              "ชื่อและชื่อเรียกอื่น (Aliases) ต้องเป็นภาษาอังกฤษตรงกับที่เกมแสดงในซับ "
                              "ระบบใช้ชื่อเหล่านี้จับว่าใครกำลังพูด")
        self.id_label = QLabel("")
        self.id_label.setObjectName("hint")
        lay.addWidget(self.id_label)

        self.name_edit = self._field(lay, "ชื่อตัวละคร (ตามที่เกมแสดง)")
        self.alias_edit = self._field(lay, "ชื่อเรียกอื่น / OCR มักอ่านผิดเป็น (คั่นด้วย ,)")
        self.voice_edit = self._field(lay, "ลักษณะเสียง")
        self.personality_edit = self._field(lay, "บุคลิก")
        self.style_edit = self._field(lay, "สไตล์การพูด")

        lay.addWidget(self._label("อารมณ์เริ่มต้น"))
        self.emotion_combo = QComboBox()
        self.emotion_combo.addItems(EMOTIONS)
        lay.addWidget(self.emotion_combo)

        self.voice_id_label = QLabel("")
        self.voice_id_label.setObjectName("hint")
        lay.addWidget(self.voice_id_label)

        lay.addStretch()
        self.status = QLabel("")
        self.status.setObjectName("hint")
        lay.addWidget(self.status)
        self.save_btn = QPushButton("💾  บันทึกตัวละคร")
        self.save_btn.setObjectName("primary")
        self.save_btn.clicked.connect(self.save_current)
        lay.addWidget(self.save_btn)
        outer.addWidget(card, 5)

        self.refresh_list()

    # ---- helpers ----
    @staticmethod
    def _label(text):
        lb = QLabel(text)
        lb.setObjectName("field")
        return lb

    def _field(self, layout, label):
        layout.addWidget(self._label(label))
        edit = QLineEdit()
        layout.addWidget(edit)
        return edit

    def refresh_list(self, select_id=None):
        self.list.blockSignals(True)
        self.list.clear()
        for cid, c in self.manager.all().items():
            item = QListWidgetItem(c["name"] or cid)
            item.setData(Qt.UserRole, cid)
            self.list.addItem(item)
        self.list.blockSignals(False)

        target = select_id or self.current_id
        for i in range(self.list.count()):
            if self.list.item(i).data(Qt.UserRole) == target:
                self.list.setCurrentRow(i)
                return
        if self.list.count():
            self.list.setCurrentRow(0)
        else:
            self.load_form(None)

    def on_select(self, current, _previous):
        self.load_form(current.data(Qt.UserRole) if current else None)

    def load_form(self, cid):
        self.current_id = cid
        c = self.manager.get(cid) if cid else None
        enabled = c is not None
        for w in (self.name_edit, self.alias_edit, self.voice_edit, self.personality_edit,
                  self.style_edit, self.emotion_combo, self.save_btn, self.del_btn):
            w.setEnabled(enabled)
        self.status.setText("")
        if not c:
            self.id_label.setText("ยังไม่มีตัวละคร — กด ＋ เพิ่ม")
            for e in (self.name_edit, self.alias_edit, self.voice_edit, self.personality_edit, self.style_edit):
                e.clear()
            self.voice_id_label.setText("")
            return
        self.id_label.setText(f"ID: {cid}")
        self.name_edit.setText(c["name"])
        self.alias_edit.setText(", ".join(c["aliases"]))
        self.voice_edit.setText(c["voice_description"])
        self.personality_edit.setText(c["personality"])
        self.style_edit.setText(c["speaking_style"])
        idx = self.emotion_combo.findText(c["default_emotion"])
        self.emotion_combo.setCurrentIndex(max(idx, 0))
        self.voice_id_label.setText(
            f"Voice ID: {c['voice_id']}" if c["voice_id"] else "Voice ID: ยังไม่ได้สร้างเสียงประจำตัว (ทำใน Phase 4)"
        )

    # ---- actions ----
    def add_character(self):
        cid = self.manager.add("New Character")
        self.refresh_list(select_id=cid)
        self.name_edit.setFocus()
        self.name_edit.selectAll()

    def save_current(self):
        if not self.current_id:
            return
        name = self.name_edit.text().strip()
        if not name:
            self.status.setText("⚠️  กรุณากรอกชื่อตัวละคร")
            self.status.setStyleSheet("color:#ffc14d;")
            return
        aliases = [a.strip() for a in self.alias_edit.text().split(",") if a.strip()]
        self.manager.update(
            self.current_id,
            name=name,
            aliases=aliases,
            voice_description=self.voice_edit.text().strip(),
            personality=self.personality_edit.text().strip(),
            speaking_style=self.style_edit.text().strip(),
            default_emotion=self.emotion_combo.currentText(),
        )
        self.refresh_list(select_id=self.current_id)
        self.status.setText("✅  บันทึกเรียบร้อยแล้ว")
        self.status.setStyleSheet("color:#34d399;")

    def delete_character(self):
        if not self.current_id:
            return
        c = self.manager.get(self.current_id)
        answer = QMessageBox.question(
            self, "ลบตัวละคร", f"ต้องการลบ \"{c['name']}\" ใช่หรือไม่?"
        )
        if answer == QMessageBox.Yes:
            self.manager.delete(self.current_id)
            self.current_id = None
            self.refresh_list()
