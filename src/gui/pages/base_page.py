from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QSpacerItem, QSizePolicy, QGraphicsOpacityEffect,
)
from ..fonts import mi, material_font

class BasePage(QWidget):
    back_requested = pyqtSignal()

    def __init__(self, title: str, icon: str, subtitle: str = "", parent=None, isBackBtnVisible=True):
        super().__init__(parent)
        self._title_text = title
        self._icon_text = icon
        self._subtitle_text = subtitle or "// system module ready"
        self.setBackBtnVisible = isBackBtnVisible
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 28)
        root.setSpacing(18)

        top = QHBoxLayout()
        self.back_btn = QPushButton("Back")
        self.back_btn.setObjectName("BackButton")
        self.back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.back_btn.clicked.connect(self.back_requested.emit)
        top.addWidget(self.back_btn)
        top.addStretch(1)
        root.addLayout(top)
        self.back_btn.setVisible(self.setBackBtnVisible)

        self.card = QFrame()
        self.card.setObjectName("PageCard")
        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(36, 36, 36, 36)
        card_layout.setSpacing(14)
        card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        icon_label = QLabel(self._icon_text)
        icon_label.setObjectName("PageIcon")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setFont(material_font(152))

        self.title_label = QLabel("")
        self.title_label.setObjectName("PageTitle")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.subtitle_label = QLabel("")
        self.subtitle_label.setObjectName("TypingLabel")
        self.subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card_layout.addItem(QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        card_layout.addWidget(icon_label)
        card_layout.addWidget(self.title_label)
        card_layout.addWidget(self.subtitle_label)
        card_layout.addItem(QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        root.addWidget(self.card, 1)

    def play_enter_animation(self) -> None:
        if hasattr(self, "_title_timer"):
            self._title_timer.stop()
        if hasattr(self, "_subtitle_timer"):
            self._subtitle_timer.stop()

        effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(effect)
        anim = QPropertyAnimation(effect, b"opacity", self)
        anim.setDuration(300)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.start()
        self._fade_anim = anim

        self._type_title()

    def _type_title(self) -> None:
        self.title_label.setText("")
        self.subtitle_label.setText("")
        self._t_i = 0
        self._s_i = 0

        def tick_title():
            self._t_i += 1
            self.title_label.setText(self._title_text[: self._t_i])
            if self._t_i >= len(self._title_text):
                self._title_timer.stop()
                self._subtitle_timer.start(20)

        def tick_sub():
            self._s_i += 1
            self.subtitle_label.setText(self._subtitle_text[: self._s_i])
            if self._s_i >= len(self._subtitle_text):
                self._subtitle_timer.stop()

        self._title_timer = QTimer(self)
        self._title_timer.timeout.connect(tick_title)
        self._subtitle_timer = QTimer(self)
        self._subtitle_timer.timeout.connect(tick_sub)
        self._title_timer.start(40)
