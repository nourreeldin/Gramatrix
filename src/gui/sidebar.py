from PyQt6.QtCore import (
    Qt, QPropertyAnimation, QEasingCurve,
    pyqtSignal, QParallelAnimationGroup, QObject, QEvent, QTimer,
)
from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QButtonGroup, QSizePolicy, QWidget, QScrollArea,
)
from PyQt6.QtGui import QFont
from .fonts import mi, icon_font, text_font

_TEXT_FONT = text_font(10, QFont.Weight.Medium)
_ICON_SIZE = 20

_C_NORMAL   = "#CCCCCC"
_C_HOVER    = "#FFE000"
_C_ACTIVE   = "#FFE000"   
_C_EXIT_NRM = "#FF3C3C"
_C_EXIT_HOV = "#FFFFFF"
NAV_ITEMS = [
    ("regex",    "CODE",         "Regex"),
    ("dfa",      "ADJUST",       "Finite Automata"),
    ("canvas",   "PALETTE",      "Canvas"),
    ("cfg",      "ACCOUNT_TREE", "Context Free Grammar"),
    ("dialect",  "EXPLORE",      "English Phrase"),
    ("lexicon",  "AUTO_AWESOME", "String Generations"),
]

class _NavBtnFilter(QObject):
    def __init__(self, btn: QPushButton, icon_lbl: QLabel, text_lbl: QLabel):
        super().__init__(btn)
        self._btn     = btn
        self._icon    = icon_lbl
        self._text    = text_lbl
        self._hovered = False
        btn.installEventFilter(self)

    def refresh(self) -> None:
        if self._btn.isChecked():
            col = _C_ACTIVE
        elif self._hovered:
            col = _C_HOVER
        else:
            col = _C_NORMAL

        ss = f"color: {col}; background: transparent;"
        self._icon.setStyleSheet(ss)
        self._text.setStyleSheet(ss)
        self._icon.setFont(icon_font(_ICON_SIZE))
        self._text.setFont(_TEXT_FONT)

    def eventFilter(self, obj, event) -> bool:
        t = event.type()
        if t == QEvent.Type.Enter:
            self._hovered = True
            self.refresh()
        elif t == QEvent.Type.Leave:
            self._hovered = False
            self.refresh()
        elif t in (QEvent.Type.MouseButtonPress, QEvent.Type.MouseButtonRelease):
            QTimer.singleShot(0, self.refresh)
        return False

class _ExitFilter(QObject):
    def __init__(self, btn: QPushButton, icon: QLabel, text: QLabel):
        super().__init__(btn)
        self._icon = icon
        self._text = text
        btn.installEventFilter(self)

    def _set(self, col: str) -> None:
        ss = f"color: {col}; background: transparent;"
        self._icon.setStyleSheet(ss)
        self._text.setStyleSheet(ss)
        self._icon.setFont(icon_font(_ICON_SIZE))
        self._text.setFont(_TEXT_FONT)

    def eventFilter(self, obj, event) -> bool:
        t = event.type()
        if t == QEvent.Type.Enter:
            self._set(_C_EXIT_HOV)
        elif t == QEvent.Type.Leave:
            self._set(_C_EXIT_NRM)
        return False

class Sidebar(QFrame):
    navigate          = pyqtSignal(str)
    exit_requested    = pyqtSignal()
    collapsed_changed = pyqtSignal(bool)

    EXPANDED_WIDTH  = 245
    COLLAPSED_WIDTH = 64

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.setMinimumWidth(self.EXPANDED_WIDTH)
        self.setMaximumWidth(self.EXPANDED_WIDTH)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        self._collapsed = False

        self._buttons:        dict[str, QPushButton]  = {}
        self._btn_icon:       dict[str, QLabel]        = {}
        self._btn_text:       dict[str, QLabel]        = {}
        self._btn_filters:    dict[str, _NavBtnFilter] = {}
        self._section_labels: list[QLabel]             = []
        self._exit_icon:      QLabel | None            = None
        self._exit_text:      QLabel | None            = None

        self._build_ui()

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(8, 14, 8, 14)
        outer.setSpacing(0)

        self._logo_row_widget = QWidget()
        self._logo_row_widget.setStyleSheet("background: transparent;")
        logo_row = QHBoxLayout(self._logo_row_widget)
        logo_row.setContentsMargins(0, 0, 0, 0)
        logo_row.setSpacing(8)

        self._logo_icon = QLabel(mi.DIAMOND)
        self._logo_icon.setFont(icon_font(18))
        self._logo_icon.setObjectName("LogoIcon")
        self._logo_icon.setFixedWidth(24)
        self._logo_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._logo_icon.setStyleSheet("color: #FFE000; background: transparent;")

        self.logo_text = QLabel("GRAMATRIX")
        self.logo_text.setObjectName("LogoText")
        self.logo_text.setFont(QFont("Segoe UI", 11, QFont.Weight.ExtraBold))
        self.logo_text.setStyleSheet(
            "color: #FFE000; background: transparent; letter-spacing: 4px;"
        )

        logo_row.addStretch()
        logo_row.addWidget(self._logo_icon)
        logo_row.addWidget(self.logo_text)
        logo_row.addStretch()

        outer.addWidget(self._logo_row_widget)
        outer.addSpacing(10)

        div1 = QFrame()
        div1.setObjectName("Divider")
        div1.setFixedHeight(1)
        outer.addWidget(div1)
        outer.addSpacing(6)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setStyleSheet(
            "QScrollArea { background: transparent; border: none; }"
            "QScrollArea > QWidget > QWidget { background: transparent; }"
        )

        nav_widget = QWidget()
        nav_widget.setStyleSheet("background: transparent;")
        nav_layout = QVBoxLayout(nav_widget)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.setSpacing(2)

        self._group = QButtonGroup(self)
        self._group.setExclusive(True)

        for key, icon_attr, label in NAV_ITEMS:
            glyph = getattr(mi, icon_attr)
            btn   = self._make_nav_btn(key, glyph, label)
            btn.clicked.connect(lambda _=False, k=key: self.navigate.emit(k))
            self._group.addButton(btn)
            self._buttons[key] = btn
            nav_layout.addWidget(btn)

        self._group.idToggled.connect(lambda _id, _chk: self._refresh_all())

        nav_layout.addStretch()
        scroll.setWidget(nav_widget)
        outer.addWidget(scroll, 1)
        outer.addSpacing(8)

        div2 = QFrame()
        div2.setObjectName("Divider")
        div2.setFixedHeight(1)
        outer.addWidget(div2)
        outer.addSpacing(8)

        self.exit_btn = QPushButton()
        self.exit_btn.setObjectName("ExitButton")
        self.exit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.exit_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.exit_btn.setFixedHeight(42)
        self.exit_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.exit_btn.clicked.connect(self.exit_requested.emit)

        exit_layout = QHBoxLayout(self.exit_btn)
        exit_layout.setContentsMargins(14, 0, 14, 0)
        exit_layout.setSpacing(10)

        exit_icon = QLabel(mi.POWER)
        exit_icon.setObjectName("ExitIcon")
        exit_icon.setFont(icon_font(_ICON_SIZE))
        exit_icon.setFixedWidth(24)
        exit_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        exit_icon.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        exit_icon.setStyleSheet(f"color: {_C_EXIT_NRM}; background: transparent;")

        exit_text = QLabel("Exit")
        exit_text.setFont(_TEXT_FONT)
        exit_text.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        exit_text.setStyleSheet(f"color: {_C_EXIT_NRM}; background: transparent;")

        self._exit_icon = exit_icon
        self._exit_text = exit_text
        _ExitFilter(self.exit_btn, exit_icon, exit_text)

        exit_layout.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        exit_layout.addWidget(exit_icon)
        exit_layout.addWidget(exit_text)
        outer.addWidget(self.exit_btn)

        self._buttons["regex"].setChecked(True)
        QTimer.singleShot(0, self._refresh_all)

    def _make_nav_btn(self, key: str, glyph: str, label: str) -> QPushButton:
        btn = QPushButton()
        btn.setObjectName("NavButton")
        btn.setCheckable(True)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        btn.setFixedHeight(42)
        btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        row = QHBoxLayout(btn)
        row.setContentsMargins(14, 0, 14, 0)
        row.setSpacing(10)

        icon_lbl = QLabel(glyph)
        icon_lbl.setObjectName("NavIcon")
        icon_lbl.setFont(icon_font(_ICON_SIZE))
        icon_lbl.setFixedWidth(24)
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        icon_lbl.setStyleSheet(f"color: {_C_NORMAL}; background: transparent;")

        text_lbl = QLabel(label)
        text_lbl.setFont(_TEXT_FONT)
        text_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        text_lbl.setStyleSheet(f"color: {_C_NORMAL}; background: transparent;")

        row.addWidget(icon_lbl)
        row.addWidget(text_lbl, 1)

        self._btn_icon[key]    = icon_lbl
        self._btn_text[key]    = text_lbl
        self._btn_filters[key] = _NavBtnFilter(btn, icon_lbl, text_lbl)

        return btn

    def _refresh_all(self) -> None:
        for f in self._btn_filters.values():
            f.refresh()

    def select(self, key: str) -> None:
        if key in self._buttons:
            self._buttons[key].setChecked(True)
            QTimer.singleShot(0, self._refresh_all)

    @property
    def is_collapsed(self) -> bool:
        return self._collapsed

    def toggle(self) -> None:
        self._collapsed = not self._collapsed
        current = self.width()
        target  = self.COLLAPSED_WIDTH if self._collapsed else self.EXPANDED_WIDTH

        if self._collapsed:
            self._apply_collapsed()
        else:
            self._apply_expanded()

        anim_min = QPropertyAnimation(self, b"minimumWidth")
        anim_min.setStartValue(current)
        anim_min.setEndValue(target)
        anim_min.setDuration(240)
        anim_min.setEasingCurve(QEasingCurve.Type.InOutCubic)

        anim_max = QPropertyAnimation(self, b"maximumWidth")
        anim_max.setStartValue(current)
        anim_max.setEndValue(target)
        anim_max.setDuration(240)
        anim_max.setEasingCurve(QEasingCurve.Type.InOutCubic)

        self._anim_group = QParallelAnimationGroup(self)
        self._anim_group.addAnimation(anim_min)
        self._anim_group.addAnimation(anim_max)
        self._anim_group.start()

        self.collapsed_changed.emit(self._collapsed)

    def _apply_collapsed(self) -> None:
        self.logo_text.setVisible(False)
        self._logo_icon.setFixedWidth(24)
        self._logo_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_layout = self._logo_row_widget.layout()
        if logo_layout:
            logo_layout.setContentsMargins(0, 0, 0, 0)
            logo_layout.setSpacing(0)

        for key, btn in self._buttons.items():
            self._btn_text[key].setVisible(False)
            icon_lbl = self._btn_icon[key]

            btn_layout = btn.layout()
            if btn_layout:
                btn_layout.setContentsMargins(0, 0, 0, 0)
                btn_layout.setSpacing(0)
                btn_layout.setAlignment(
                    Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter
                )

            icon_lbl.setFixedWidth(24)
            icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        if self._exit_text:
            self._exit_text.setVisible(False)
        if self._exit_icon:
            el = self.exit_btn.layout()
            if el:
                el.setContentsMargins(0, 0, 0, 0)
                el.setSpacing(0)
                el.setAlignment(
                    Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter
                )
            self._exit_icon.setFixedWidth(24)
            self._exit_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def _apply_expanded(self) -> None:
        self.logo_text.setVisible(True)
        self._logo_icon.setFixedWidth(24)
        self._logo_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_layout = self._logo_row_widget.layout()
        if logo_layout:
            logo_layout.setContentsMargins(0, 0, 0, 0)
            logo_layout.setSpacing(8)

        for key, btn in self._buttons.items():
            self._btn_text[key].setVisible(True)
            icon_lbl = self._btn_icon[key]

            btn_layout = btn.layout()
            if btn_layout:
                btn_layout.setContentsMargins(14, 0, 14, 0)
                btn_layout.setSpacing(10)
                btn_layout.setAlignment(
                    Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
                )

            icon_lbl.setFixedWidth(24)
            icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        if self._exit_text:
            self._exit_text.setVisible(True)
        if self._exit_icon:
            el = self.exit_btn.layout()
            if el:
                el.setContentsMargins(14, 0, 14, 0)
                el.setSpacing(10)
                el.setAlignment(
                    Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
                )
            self._exit_icon.setFixedWidth(24)
            self._exit_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)