from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QStackedWidget,
    QFrame, QApplication, QGraphicsOpacityEffect, QPushButton,
)
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QFont

from .sidebar import Sidebar
from .fonts import mi, material_font
from .pages import (
    RegexMatrixPage, DFAInputPage,
    CFGInputPage, EnglishPhrasePage, StringInputPage, CanvasPage
)

def _make_app_icon(size: int = 64) -> QIcon:
    pix = QPixmap(size, size)
    pix.fill(QColor("#0A0A0A"))
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.fillRect(0, 0, max(4, size // 16), size, QColor("#FFE000"))
    font = QFont("Segoe UI", size // 2, QFont.Weight.Black)
    painter.setFont(font)
    painter.setPen(QColor("#FFE000"))
    painter.drawText(pix.rect(), Qt.AlignmentFlag.AlignCenter, "G")
    painter.end()
    return QIcon(pix)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gramatrix")
        self.setWindowIcon(_make_app_icon())
        self.resize(1280, 820)
        self.setMinimumSize(900, 600)

        root = QWidget()
        root.setObjectName("RootBackground")
        self.setCentralWidget(root)

        layout = QHBoxLayout(root)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(0)

        self.sidebar = Sidebar()
        self.sidebar.navigate.connect(self.go_to)
        self.sidebar.exit_requested.connect(self._on_exit)
        self.sidebar.collapsed_changed.connect(self._on_sidebar_toggled)
        layout.addWidget(self.sidebar)

        self._toggle_btn = QPushButton(mi.CHEVRON_LEFT)
        self._toggle_btn.setFont(material_font(18))
        self._toggle_btn.setObjectName("SidebarToggle")
        self._toggle_btn.setFixedSize(22, 56)
        self._toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._toggle_btn.clicked.connect(self.sidebar.toggle)

        toggle_wrap = QWidget()
        toggle_wrap.setFixedWidth(22)
        toggle_wrap.setObjectName("ToggleWrap")
        tw_layout = QVBoxLayout(toggle_wrap)
        tw_layout.setContentsMargins(0, 0, 0, 0)
        tw_layout.setSpacing(0)
        tw_layout.addStretch()
        tw_layout.addWidget(self._toggle_btn)
        tw_layout.addStretch()
        layout.addWidget(toggle_wrap)

        layout.addSpacing(10)

        content_panel = QFrame()
        content_panel.setObjectName("GlassPanel")
        content_layout = QVBoxLayout(content_panel)
        content_layout.setContentsMargins(8, 8, 8, 8)

        self.stack = QStackedWidget()
        content_layout.addWidget(self.stack)
        layout.addWidget(content_panel, 1)

        self._pages = {
            "regex":    RegexMatrixPage(),
            "dfa":      DFAInputPage(),
            "canvas":   CanvasPage(),
            "cfg":      CFGInputPage(),
            "dialect":  EnglishPhrasePage(),
            "lexicon":  StringInputPage(),
        }
        for page in self._pages.values():
            self.stack.addWidget(page)

        self.go_to("regex", animate=False)

    def go_to(self, key: str, animate: bool = True) -> None:
        if key not in self._pages:
            return
        page = self._pages[key]
        self.stack.setCurrentWidget(page)
        self.sidebar.select(key)
        if animate:
            self._fade_in(page)
        page.play_enter_animation()

    def _fade_in(self, page: QWidget) -> None:
        effect = QGraphicsOpacityEffect(page)
        page.setGraphicsEffect(effect)
        anim = QPropertyAnimation(effect, b"opacity", self)
        anim.setDuration(260)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.start()
        self._fade_anim = anim

    def _on_sidebar_toggled(self, collapsed: bool) -> None:
        self._toggle_btn.setText(mi.CHEVRON_RIGHT if collapsed else mi.CHEVRON_LEFT)

    def _on_exit(self) -> None:
        QApplication.instance().quit()