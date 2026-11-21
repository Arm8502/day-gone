"""gui/styles.py - ธีมมืด gradient ม่วง-ฟ้า"""

STYLE = """
* { font-family: "Segoe UI", "Leelawadee UI", "Noto Sans Thai", "Sarabun", sans-serif; }
QWidget#root, QDialog#root { background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #0b0e1a, stop:1 #151a33); }
QLabel { color: #e8ebff; font-size: 13px; }
QLabel#title { font-size: 26px; font-weight: 700; color: #ffffff; }
QLabel#subtitle { font-size: 13px; color: #8a92b8; }
QLabel#cardTitle { font-size: 15px; font-weight: 600; color: #ffffff; }
QLabel#hint { font-size: 12px; color: #7d86ad; }
QLabel#field { font-size: 12px; color: #8a92b8; }
QLabel#badge {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #7c5cff, stop:1 #22d3ee);
    color: white; font-weight: 700; border-radius: 13px; min-width: 26px; max-width: 26px;
    min-height: 26px; max-height: 26px; qproperty-alignment: AlignCenter;
}
QFrame#card {
    background: rgba(255,255,255,0.045);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 18px;
}
QLabel#preview {
    background: #090b14; border: 1px solid rgba(255,255,255,0.08); border-radius: 12px;
}
QComboBox, QLineEdit {
    background: #0e1224; color: #ffffff; border: 1px solid #2a3158; border-radius: 10px;
    padding: 9px 12px; font-size: 13px; selection-background-color: #7c5cff;
}
QComboBox:hover, QLineEdit:hover { border: 1px solid #4a56a0; }
QLineEdit:focus, QComboBox:focus { border: 1px solid #7c5cff; }
QComboBox QAbstractItemView {
    background: #0e1224; color: #ffffff; border: 1px solid #2a3158;
    selection-background-color: #7c5cff; outline: 0;
}
QListWidget {
    background: #0e1224; color: #e8ebff; border: 1px solid #2a3158; border-radius: 12px;
    padding: 6px; font-size: 14px; outline: 0;
}
QListWidget::item { padding: 10px 12px; border-radius: 8px; }
QListWidget::item:hover { background: rgba(255,255,255,0.06); }
QListWidget::item:selected { background: #2f376a; color: #ffffff; }
QPushButton {
    background: rgba(255,255,255,0.07); color: #e8ebff; border: 1px solid rgba(255,255,255,0.12);
    border-radius: 10px; padding: 9px 16px; font-size: 13px; font-weight: 600;
}
QPushButton:hover { background: rgba(255,255,255,0.13); }
QPushButton:pressed { background: rgba(255,255,255,0.05); }
QPushButton:disabled { color: #5d6488; }
QPushButton#primary {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #7c5cff, stop:1 #22d3ee);
    border: none; color: white;
}
QPushButton#primary:hover {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #8e72ff, stop:1 #4de0f5);
}
QPushButton#danger { color: #ff8da1; }
QPushButton#start {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #7c5cff, stop:1 #22d3ee);
    border: none; color: white; font-size: 17px; font-weight: 700;
    border-radius: 16px; padding: 16px;
}
QPushButton#start:hover {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #8e72ff, stop:1 #4de0f5);
}
QPushButton#start:disabled { background: #2a3158; color: #7d86ad; }
QPushButton#stop {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #ff4d6d, stop:1 #ff8a4c);
    border: none; color: white; font-size: 17px; font-weight: 700;
    border-radius: 16px; padding: 16px;
}
QPushButton#stop:hover {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #ff6684, stop:1 #ffa070);
}
QLabel#pill { border-radius: 14px; padding: 6px 14px; font-weight: 600; font-size: 12px; }
QLabel#speaker { font-size: 13px; font-weight: 700; color: #22d3ee; }
QLabel#subEn { font-size: 15px; color: #aab3dd; }
QLabel#subTh { font-size: 22px; font-weight: 700; color: #ffffff; }
QPlainTextEdit {
    background: #090b14; color: #9fb0ff; border: 1px solid rgba(255,255,255,0.08);
    border-radius: 12px; padding: 8px; font-family: "Consolas", "Cascadia Mono", monospace; font-size: 12px;
}
QScrollBar:vertical { background: transparent; width: 8px; margin: 2px; }
QScrollBar::handle:vertical { background: #2f376a; border-radius: 4px; min-height: 24px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QMessageBox { background: #151a33; }
"""

PILL = {
    "idle":     ("● พร้อมใช้งาน",      "background:rgba(138,146,184,0.18); color:#aab3dd;"),
    "loading":  ("● กำลังโหลดระบบ...",  "background:rgba(255,193,77,0.18); color:#ffc14d;"),
    "running":  ("● กำลังทำงาน",        "background:rgba(52,211,153,0.18); color:#34d399;"),
    "stopping": ("● กำลังหยุด...",      "background:rgba(255,193,77,0.18); color:#ffc14d;"),
    "error":    ("● เกิดข้อผิดพลาด",     "background:rgba(255,77,109,0.18); color:#ff6b86;"),
}
