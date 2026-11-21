"""app.py - สร้างหน้าต่างหลักและเริ่ม GUI"""
import sys

from PySide6.QtWidgets import QApplication

from gui.main_window import MainWindow
from gui.styles import STYLE


def run():
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLE)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    run()
