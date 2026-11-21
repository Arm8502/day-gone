"""gui/widgets.py - ชิ้นส่วน UI ที่ใช้ร่วมกัน"""
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QFrame, QGraphicsDropShadowEffect, QHBoxLayout, QLabel, QVBoxLayout


def make_card(step, title, hint=None):
    card = QFrame()
    card.setObjectName("card")
    shadow = QGraphicsDropShadowEffect(card)
    shadow.setBlurRadius(30)
    shadow.setOffset(0, 8)
    shadow.setColor(QColor(0, 0, 0, 110))
    card.setGraphicsEffect(shadow)

    lay = QVBoxLayout(card)
    lay.setContentsMargins(20, 18, 20, 18)
    lay.setSpacing(12)

    head = QHBoxLayout()
    head.setSpacing(10)
    badge = QLabel(str(step))
    badge.setObjectName("badge")
    t = QLabel(title)
    t.setObjectName("cardTitle")
    head.addWidget(badge)
    head.addWidget(t)
    head.addStretch()
    lay.addLayout(head)

    if hint:
        h = QLabel(hint)
        h.setObjectName("hint")
        h.setWordWrap(True)
        lay.addWidget(h)
    return card, lay
