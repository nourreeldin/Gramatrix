from __future__ import annotations
from typing import List
from PyQt6.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve,
)
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QGridLayout, QScrollArea,
)
from PyQt6.QtGui import QFont
from .base_page import BasePage
from ..fonts import mi
from regex_module.preprocessor import (
    expand, to_display, validate, PreprocessorError,
)
from regex_module.validator  import validate_expanded
from regex_module.tokenizer  import tokenize as tokenize_expanded
from regex_module.parser     import parse


MAX_EXPR_LEN = 30
LETTER_KEYS: List[str] = list("abcdefghijklmnopqrstuvwxyz")
DIGIT_KEYS:  List[str] = [str(d) for d in range(10)]
SYMBOL_KEYS: List[str] = ["+", "*", "(", ")", "Φ", "Λ"]
CONTROL_KEYS: List[str] = ["Undo", "Redo", "Del", "AC", "="]
SUP_DIGIT_MAP = {
    "¹": "^1", "²": "^2", "³": "^3", "⁴": "^4", "⁵": "^5",
    "⁶": "^6", "⁷": "^7", "⁸": "^8", "⁹": "^9",
}
SUP_REVERSE_LABEL = "ᴿ"
SUP_REVERSE_TOKEN = "^R"
SUP_POSITIVE_LABEL = "⁺"         
SUP_POSITIVE_TOKEN = "^+"           
SUP_KEYS_LABELS: List[str] = (
    list(SUP_DIGIT_MAP.keys()) + [SUP_REVERSE_LABEL, SUP_POSITIVE_LABEL]
)

def _build_display_text(expr: str) -> str:
    return to_display(expr)

def _compute_expanded(expr: str) -> tuple[str, bool]:
    try:
        result = expand(expr)
        return result, True
    except PreprocessorError:
        return "", False


class RegexMatrixPage(BasePage):

    def __init__(self, parent=None):
        super().__init__(
            title="Regex Matrix",
            icon=mi.CODE,
            subtitle="// pattern studio initialized",
            parent=parent,
        )
        self._expression: str = ""
        self._undo_stack: List[str] = []
        self._redo_stack: List[str] = []
        self._mode: str = "letters"
        self._panel_shown = False

        self._build_calculator_panel()
        self._calc_panel.hide()

    def _build_calculator_panel(self) -> None:
        self._calc_panel = QFrame()
        self._calc_panel.setObjectName("CalcPanel")
        self._calc_panel.setStyleSheet("""
            QFrame#CalcPanel {
                background-color: #FFFFFF;
                border: 3px solid #111111;
                border-radius: 0px;
            }
        """)

        panel_layout = QVBoxLayout(self._calc_panel)
        panel_layout.setContentsMargins(24, 18, 24, 18)
        panel_layout.setSpacing(14)

        display_frame = QFrame()
        display_frame.setObjectName("DisplayFrame")
        display_frame.setStyleSheet("""
            QFrame#DisplayFrame {
                background-color: #111111;
                border: 3px solid #111111;
                border-radius: 0px;
                min-height: 72px;
            }
        """)
        display_layout = QHBoxLayout(display_frame)
        display_layout.setContentsMargins(20, 12, 20, 12)
        display_layout.setSpacing(16)

        expr_col = QVBoxLayout()
        expr_col.setSpacing(3)
        raw_caption = QLabel("INPUT")
        raw_caption.setStyleSheet(
            "color: #888888; font-size: 9px; font-weight: 900; "
            "letter-spacing: 3px; background: transparent; border: none;"
        )
        self._expr_label = QLabel("…")
        self._expr_label.setFont(QFont("Consolas", 18, QFont.Weight.Bold))
        self._expr_label.setStyleSheet(
            "color: #FFE000; background: transparent; border: none;"
        )
        self._expr_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        self._expr_label.setTextFormat(Qt.TextFormat.PlainText)
        expr_col.addWidget(raw_caption)
        expr_col.addWidget(self._expr_label)
        display_layout.addLayout(expr_col, 2)

        arrow = QLabel("→")
        arrow.setFont(QFont("Segoe UI", 18))
        arrow.setStyleSheet(
            "color: #FFFFFF; background: transparent; border: none; font-weight: 900;"
        )
        arrow.setAlignment(Qt.AlignmentFlag.AlignCenter)
        display_layout.addWidget(arrow)

        out_col = QVBoxLayout()
        out_col.setSpacing(3)
        out_caption = QLabel("EXPANDED")
        out_caption.setStyleSheet(
            "color: #888888; font-size: 9px; font-weight: 900; "
            "letter-spacing: 3px; background: transparent; border: none;"
        )
        self._result_label = QLabel("…")
        self._result_label.setFont(QFont("Consolas", 18, QFont.Weight.Bold))
        self._result_label.setStyleSheet(
            "color: #FFFFFF; background: transparent; border: none;"
        )
        self._result_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        self._result_label.setTextFormat(Qt.TextFormat.PlainText)
        out_col.addWidget(out_caption)
        out_col.addWidget(self._result_label)
        display_layout.addLayout(out_col, 2)

        panel_layout.addWidget(display_frame)

        self._error_label = QLabel("")
        self._error_label.setStyleSheet(
            "color: #FF2020; font-size: 10px; font-weight: 700; "
            "background: transparent; border: none;"
        )
        self._error_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self._error_label.setVisible(False)
        panel_layout.addWidget(self._error_label)

        mode_row = QHBoxLayout()
        mode_row.setSpacing(10)
        self._letters_btn = QPushButton("Aa  Letters")
        self._letters_btn.setCheckable(True)
        self._letters_btn.setChecked(True)
        self._letters_btn.setObjectName("ModeButton")
        self._letters_btn.clicked.connect(lambda: self._switch_mode("letters"))

        self._digits_btn = QPushButton("01  Digits")
        self._digits_btn.setCheckable(True)
        self._digits_btn.setObjectName("ModeButton")
        self._digits_btn.clicked.connect(lambda: self._switch_mode("digits"))

        for btn in (self._letters_btn, self._digits_btn):
            btn.setFixedHeight(34)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(self._mode_btn_style())

        mode_row.addWidget(self._letters_btn)
        mode_row.addWidget(self._digits_btn)
        mode_row.addStretch()
        panel_layout.addLayout(mode_row)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent; border: none;")
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self._kb_container = QWidget()
        self._kb_container.setStyleSheet("background: transparent;")
        self._kb_layout = QVBoxLayout(self._kb_container)
        self._kb_layout.setContentsMargins(0, 4, 0, 4)
        self._kb_layout.setSpacing(10)

        scroll.setWidget(self._kb_container)
        panel_layout.addWidget(scroll)

        self.layout().addWidget(self._calc_panel)
        self._rebuild_keyboard()

    def _clear_layout(self, layout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())

    def _rebuild_keyboard(self) -> None:
        self._clear_layout(self._kb_layout)

        alpha_keys = LETTER_KEYS if self._mode == "letters" else DIGIT_KEYS
        alpha_grid = QGridLayout()
        alpha_grid.setSpacing(5)
        cols = 9
        for idx, key in enumerate(alpha_keys):
            btn = self._make_key(key, "KeyAlpha", key)
            alpha_grid.addWidget(btn, idx // cols, idx % cols)
        self._kb_layout.addLayout(alpha_grid)

        sup_section = QLabel("SUPERSCRIPTS")
        sup_section.setStyleSheet(
            "color: #555555; font-size: 8px; font-weight: 900; "
            "letter-spacing: 3px; background: transparent; border: none; "
            "padding-top: 4px;"
        )
        self._kb_layout.addWidget(sup_section)

        sup_row = QHBoxLayout()
        sup_row.setSpacing(5)
        for label in SUP_KEYS_LABELS:
            if label in SUP_DIGIT_MAP:
                token = SUP_DIGIT_MAP[label]
            elif label == SUP_REVERSE_LABEL:
                token = SUP_REVERSE_TOKEN
            elif label == SUP_POSITIVE_LABEL:
                token = SUP_POSITIVE_TOKEN  
            else:
                token = label
            btn = self._make_key(label, "KeySuper", token)
            sup_row.addWidget(btn)
        sup_row.addStretch()
        self._kb_layout.addLayout(sup_row)

        sym_section = QLabel("SYMBOLS")
        sym_section.setStyleSheet(
            "color: #555555; font-size: 8px; font-weight: 900; "
            "letter-spacing: 3px; background: transparent; border: none; "
            "padding-top: 2px;"
        )
        self._kb_layout.addWidget(sym_section)

        sym_row = QHBoxLayout()
        sym_row.setSpacing(5)
        for sym in SYMBOL_KEYS:
            btn = self._make_key(sym, "KeySymbol", sym)
            sym_row.addWidget(btn)
        sym_row.addStretch()
        self._kb_layout.addLayout(sym_row)

        ctrl_row = QHBoxLayout()
        ctrl_row.setSpacing(5)
        for ctrl in CONTROL_KEYS[:-1]:
            btn = self._make_key(ctrl, "KeyControl", ctrl)
            ctrl_row.addWidget(btn)
        submit_btn = self._make_key("=", "KeySubmit", "=")
        submit_btn.setMinimumWidth(64)
        ctrl_row.addWidget(submit_btn)
        ctrl_row.addStretch()
        self._kb_layout.addLayout(ctrl_row)

    def _make_key(self, label: str, obj_name: str, token: str) -> QPushButton:
        btn = QPushButton(label)
        btn.setObjectName(obj_name)
        btn.setFixedHeight(36)
        btn.setMinimumWidth(36)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(lambda _=False, t=token: self.handle_input(t))
        btn.setStyleSheet(self._key_style(obj_name))
        if obj_name == "KeySuper":
            btn.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        return btn

    def handle_input(self, key: str) -> None:
        if key == "AC":
            self._push_undo()
            self._set_expression("")
            self._redo_stack.clear()
            self._clear_error()

        elif key == "Del":
            if self._expression:
                self._push_undo()
                new_expr = self._delete_last_token(self._expression)
                self._set_expression(new_expr)
                self._redo_stack.clear()

        elif key == "Undo":
            if self._undo_stack:
                self._redo_stack.append(self._expression)
                self._expression = self._undo_stack.pop()
                self._refresh_display()
                self._clear_error()

        elif key == "Redo":
            if self._redo_stack:
                self._undo_stack.append(self._expression)
                self._expression = self._redo_stack.pop()
                self._refresh_display()
                self._clear_error()

        elif key == "=":
            if self._expression:
                self._evaluate()

        else:
            candidate = self._expression + key
            try:
                validate(candidate, check_brackets=False)
            except PreprocessorError as err:
                self._flash_result(success=False)
                self._show_error(str(err))
                return

            try:
                expanded = expand(candidate, check_brackets=False)
                if len(expanded) > MAX_EXPR_LEN:
                    self._flash_result(success=False)
                    self._show_error(f"Expanded regex is too long ({len(expanded)} chars, max {MAX_EXPR_LEN}).")
                    return
            except PreprocessorError:
                pass

            if len(candidate) <= MAX_EXPR_LEN:
                self._push_undo()
                self._set_expression(candidate)
                self._redo_stack.clear()
                self._clear_error()

    def _evaluate(self) -> None:
        try:
            expanded = expand(self._expression)
            if len(expanded) > MAX_EXPR_LEN:
                raise PreprocessorError(
                    f"Expanded regex is too long ({len(expanded)} chars, max {MAX_EXPR_LEN})."
                )
            validate_expanded(expanded)
            tokens   = tokenize_expanded(expanded)
            tree     = parse(tokens)
            self._flash_result(success=True)
            self._clear_error()
        except PreprocessorError as err:
            self._flash_result(success=False)
            self._show_error(str(err))

    @staticmethod
    def _delete_last_token(expr: str) -> str:
        if not expr:
            return expr
        import re as _re
        m = _re.search(r'\^R$|\^\+$|\^\d$', expr, _re.IGNORECASE)
        if m:
            return expr[:m.start()]
        if expr.endswith(")"):
            depth = 0
            for i in range(len(expr) - 1, -1, -1):
                if expr[i] == ")":
                    depth += 1
                elif expr[i] == "(":
                    depth -= 1
                    if depth == 0:
                        return expr[:i]
        return expr[:-1]

    def _push_undo(self) -> None:
        self._undo_stack.append(self._expression)

    def _set_expression(self, expr: str) -> None:
        self._expression = expr
        self._refresh_display()

    def _refresh_display(self) -> None:
        display_text = _build_display_text(self._expression) if self._expression else "…"
        self._expr_label.setText(display_text)
        expanded, ok = _compute_expanded(self._expression)
        if ok and expanded:
            self._result_label.setText(expanded)
            self._result_label.setStyleSheet(
                "color: #FFFFFF; background: transparent; border: none;"
            )
        elif not self._expression:
            self._result_label.setText("…")
            self._result_label.setStyleSheet(
                "color: #FFFFFF; background: transparent; border: none;"
            )
        else:
            self._result_label.setText("…")
            self._result_label.setStyleSheet(
                "color: #888888; background: transparent; border: none;"
            )

    def _flash_result(self, success: bool) -> None:
        ok_style = (
            "color: #111111; background: #FFE000; "
            "border: 2px solid #111111; border-radius: 0px;"
        )
        err_style = (
            "color: #FFFFFF; background: #FF2020; "
            "border: 2px solid #111111; border-radius: 0px;"
        )
        normal_style = "color: #FFFFFF; background: transparent; border: none;"
        self._result_label.setStyleSheet(ok_style if success else err_style)
        QTimer.singleShot(500, lambda: self._result_label.setStyleSheet(normal_style))

    def _show_error(self, msg: str) -> None:
        self._error_label.setText(f"⚠ {msg}")
        self._error_label.setVisible(True)
        QTimer.singleShot(3000, self._clear_error)

    def _clear_error(self) -> None:
        self._error_label.setText("")
        self._error_label.setVisible(False)

    def _switch_mode(self, mode: str) -> None:
        if mode == self._mode:
            return
        self._mode = mode
        self._expression = ""
        self._undo_stack.clear()
        self._redo_stack.clear()
        self._refresh_display()
        self._rebuild_keyboard()
        self._letters_btn.setChecked(mode == "letters")
        self._digits_btn.setChecked(mode == "digits")
        self._clear_error()

    def play_enter_animation(self) -> None:
        self._panel_shown = False
        self._calc_panel.hide()
        super().play_enter_animation()
        self._watch_for_typing_done()

    def _watch_for_typing_done(self) -> None:
        def _check():
            if hasattr(self, "_subtitle_timer") and not self._subtitle_timer.isActive():
                _poller.stop()
                QTimer.singleShot(200, self._show_calc_panel)

        _poller = QTimer(self)
        _poller.timeout.connect(_check)
        _poller.start(50)
        self._typing_poller = _poller

    def _show_calc_panel(self) -> None:
        if self._panel_shown:
            return
        self._panel_shown = True
        self._calc_panel.setMaximumHeight(0)
        self._calc_panel.show()
        grow = QPropertyAnimation(self._calc_panel, b"maximumHeight", self)
        grow.setDuration(440)
        grow.setStartValue(0)
        grow.setEndValue(16_777_215)
        grow.setEasingCurve(QEasingCurve.Type.OutCubic)
        grow.start()
        self._grow_anim = grow

    @staticmethod
    def _mode_btn_style() -> str:
        return """
            QPushButton#ModeButton {
                background: #F5F0E8;
                border: 2px solid #111111;
                border-radius: 0px;
                color: #111111;
                font-size: 12px;
                font-weight: 900;
                padding: 0 14px;
                letter-spacing: 1px;
            }
            QPushButton#ModeButton:checked {
                background: #FFE000;
                border: 2px solid #111111;
                color: #111111;
            }
            QPushButton#ModeButton:hover:!checked {
                background: #111111;
                border-color: #111111;
                color: #FFE000;
            }
        """

    @staticmethod
    def _key_style(obj_name: str) -> str:
        if obj_name == "KeyAlpha":
            return """
                QPushButton#KeyAlpha {
                    background: #F5F0E8;
                    border: 2px solid #111111;
                    border-radius: 0px;
                    color: #111111;
                    font-size: 13px;
                    font-weight: 700;
                }
                QPushButton#KeyAlpha:hover {
                    background: #111111;
                    color: #FFE000;
                }
                QPushButton#KeyAlpha:pressed {
                    background: #333333;
                    color: #FFE000;
                }
            """
        if obj_name == "KeySuper":
            return """
                QPushButton#KeySuper {
                    background: #FFE000;
                    border: 2px solid #111111;
                    border-radius: 0px;
                    color: #111111;
                    font-size: 15px;
                    font-weight: 900;
                    min-width: 36px;
                }
                QPushButton#KeySuper:hover {
                    background: #111111;
                    color: #FFE000;
                }
                QPushButton#KeySuper:pressed {
                    background: #333333;
                    color: #FFE000;
                }
            """
        if obj_name == "KeySymbol":
            return """
                QPushButton#KeySymbol {
                    background: #FFFFFF;
                    border: 2px solid #111111;
                    border-radius: 0px;
                    color: #111111;
                    font-size: 15px;
                    font-weight: 900;
                    min-width: 40px;
                }
                QPushButton#KeySymbol:hover {
                    background: #111111;
                    color: #FFFFFF;
                }
                QPushButton#KeySymbol:pressed {
                    background: #333333;
                }
            """
        if obj_name == "KeySubmit":
            return """
                QPushButton#KeySubmit {
                    background: #FFE000;
                    border: 2px solid #111111;
                    border-radius: 0px;
                    color: #111111;
                    font-size: 16px;
                    font-weight: 900;
                    min-width: 64px;
                }
                QPushButton#KeySubmit:hover {
                    background: #111111;
                    color: #FFE000;
                }
                QPushButton#KeySubmit:pressed {
                    background: #333333;
                    color: #FFE000;
                }
            """
        return """
            QPushButton#KeyControl {
                background: #FFFFFF;
                border: 2px solid #FF2020;
                border-radius: 0px;
                color: #FF2020;
                font-size: 12px;
                font-weight: 900;
                min-width: 52px;
                letter-spacing: 1px;
            }
            QPushButton#KeyControl:hover {
                background: #FF2020;
                color: #FFFFFF;
            }
            QPushButton#KeyControl:pressed {
                background: #CC0000;
                color: #FFFFFF;
            }
        """