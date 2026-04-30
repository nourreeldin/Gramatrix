import sys
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont
from gui.main_window import MainWindow
from gui.fonts import load_material_icons

def load_stylesheet() -> str:
    qss_path = Path(__file__).parent / "gui" / "style.qss"
    if qss_path.exists():
        return qss_path.read_text(encoding="utf-8")
    return ""

def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Gramatrix")
    app.setFont(QFont("Segoe UI", 10))
    load_material_icons()  
    app.setStyleSheet(load_stylesheet())
    window = MainWindow()
    window.show()
    return app.exec()

if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent))
    sys.exit(main())
