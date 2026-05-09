from __future__ import annotations
from typing import List
from PyQt6.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve,
)
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QGridLayout, QScrollArea, QTabWidget, QTableWidget,
    QTableWidgetItem, QHeaderView, QLineEdit, QSizePolicy, QSplitter,
    QAbstractItemView, QStackedWidget
)
from PyQt6.QtGui import QFont, QPixmap, QImage
import os
import tempfile

from .base_page import BasePage
from ..fonts import mi
from core.preprocessor import (
    expand, to_display, validate, PreprocessorError,
)
from core.validator  import validate_expanded
from core.tokenizer  import tokenize as tokenize_expanded
from core.parser     import parse
from core.nfa        import build_nfa
from core.dfa        import build_dfa
from core.dfa_minimizer import minimize_dfa
from core.cfg        import build_cfg
from core.string_generator import generate_strings
from core.english_phrase import describe_language
from graphviz.backend.execute import ExecutableNotFound


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
            title="Regex",
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

        self._build_results_panel()
        self._temp_dir = tempfile.mkdtemp()
        self._min_dfa = None
        self._sim_timer = QTimer()
        self._sim_timer.timeout.connect(self._sim_step)
        self._sim_steps = []
        self._sim_current_step = 0

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
            self._hide_results_panel()

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
            
            nfa = build_nfa(tree)
            dfa = build_dfa(nfa)
            min_dfa = minimize_dfa(dfa)
            self._min_dfa = min_dfa
            
            cfg = build_cfg(min_dfa)
            strings = generate_strings(min_dfa, count=5)
            desc = describe_language(min_dfa, nfa, strings, self._expression)
            
            self._populate_nfa_tab(nfa)
            self._populate_dfa_tab(dfa)
            self._populate_min_dfa_tab(min_dfa)
            self._populate_props_tab(cfg, strings, desc)
            self._reset_sim_tab()
            
            self._show_results_panel()
            
        except PreprocessorError as err:
            self._flash_result(success=False)
            self._show_error(str(err))

    def _show_results_panel(self) -> None:
        self._calc_panel.hide()
        self._results_expr_label.setText(f"REGEX: {self._expression}")
        self._results_panel.show()
            
    def _hide_results_panel(self) -> None:
        self._results_panel.hide()
        self._calc_panel.show()

    def _build_results_panel(self) -> None:
        self._results_panel = QFrame()
        self._results_panel.setObjectName("ResultsPanel")
        self._results_panel.setStyleSheet("""
            QFrame#ResultsPanel {
                background-color: #FFFFFF;
                border: 3px solid #111111;
                border-radius: 0px;
                margin-top: 10px;
            }
        """)
        self._results_panel.hide()
        self._results_panel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        results_layout = QVBoxLayout(self._results_panel)
        results_layout.setContentsMargins(10, 10, 10, 10)
        results_layout.setSpacing(8)
        
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)
        self._btn_return = QPushButton("← BACK")
        self._btn_return.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_return.setFixedHeight(32)
        self._btn_return.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        self._btn_return.setStyleSheet("""
            QPushButton {
                background: #111111;
                color: #FFE000;
                border: 3px solid #111111;
                padding: 4px 12px;
                font-weight: 900;
                font-family: 'Segoe UI';
                font-size: 12px;
                letter-spacing: 1px;
            }
            QPushButton:hover {
                background: #FFE000;
                color: #111111;
            }
        """)
        self._btn_return.clicked.connect(self._hide_results_panel)
        header_layout.addWidget(self._btn_return)
        
        self._results_expr_label = QLabel()
        self._results_expr_label.setStyleSheet(
            "color: #111111; font-family: 'Consolas'; font-size: 13px; font-weight: bold;"
        )
        self._results_expr_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self._results_expr_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self._results_expr_label.setMinimumWidth(0)
        header_layout.addWidget(self._results_expr_label, 1)
        
        results_layout.addLayout(header_layout)
        
        self._results_tabs = QTabWidget()
        self._results_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 3px solid #111111;
                background: #FFFFFF;
                top: -3px;
            }
            QTabBar::tab {
                background: #F5F0E8;
                color: #111111;
                border: 3px solid #111111;
                padding: 7px 14px;
                font-weight: 900;
                font-family: 'Segoe UI';
                font-size: 12px;
                margin-right: -3px;
                letter-spacing: 0.5px;
                min-width: 40px;
            }
            QTabBar::tab:selected {
                background: #FFE000;
                z-index: 10;
            }
            QTabBar::tab:hover:!selected {
                background: #111111;
                color: #FFE000;
            }
            QTabBar::scroller {
                width: 28px;
            }
            QToolButton {
                background: #F5F0E8;
                border: 3px solid #111111;
                color: #111111;
                border-radius: 0px;
                margin: 2px;
            }
            QToolButton:hover {
                background: #111111;
                color: #FFE000;
            }
        """)
        
        self._results_tabs.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        self._tab_nfa = QWidget()
        self._tab_dfa = QWidget()
        self._tab_min_dfa = QWidget()
        self._tab_props = QWidget()
        self._tab_sim = QWidget()
        
        self._results_tabs.addTab(self._tab_nfa, "ε-NFA")
        self._results_tabs.addTab(self._tab_dfa, "DFA")
        self._results_tabs.addTab(self._tab_min_dfa, "Min DFA")
        self._results_tabs.addTab(self._tab_props, "Properties")
        self._results_tabs.addTab(self._tab_sim, "Simulator")
        
        results_layout.addWidget(self._results_tabs)
        self.layout().addWidget(self._results_panel)
        
        self._build_automata_tab(self._tab_nfa)
        self._build_automata_tab(self._tab_dfa)
        self._build_automata_tab(self._tab_min_dfa)
        self._build_props_tab()
        self._build_sim_tab()

    def _build_automata_tab(self, tab: QWidget) -> None:
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(0, 0, 0, 0)
        
        toggle_btn = QPushButton("⇌ SHOW TRANSITION TABLE")
        toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        toggle_btn.setFixedHeight(32)
        toggle_btn.setStyleSheet("""
            QPushButton {
                background: #F5F0E8;
                color: #111111;
                border: 2px solid #111111;
                font-weight: 900;
                font-family: 'Segoe UI';
                font-size: 11px;
                padding: 4px 16px;
                letter-spacing: 1px;
            }
            QPushButton:hover {
                background: #111111;
                color: #FFE000;
            }
        """)
        top_bar.addStretch()
        top_bar.addWidget(toggle_btn)
        layout.addLayout(top_bar)
        
        stack = QStackedWidget()
        
        img_scroll = QScrollArea()
        img_scroll.setWidgetResizable(True)
        img_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        img_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        img_scroll.setStyleSheet("""
            QScrollArea {
                background: #FFFFFF;
                border: 2px solid #111111;
            }
            QScrollBar:vertical, QScrollBar:horizontal {
                background: #F5F0E8;
                border: 1px solid #CCCCCC;
                width: 10px;
                height: 10px;
            }
            QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
                background: #111111;
                min-height: 20px;
                min-width: 20px;
            }
            QScrollBar::add-line, QScrollBar::sub-line { height: 0; width: 0; }
        """)
        img_label = QLabel()
        img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        img_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        img_scroll.setWidget(img_label)
        stack.addWidget(img_scroll)
        
        table_container = QWidget()
        table_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        table_vbox = QVBoxLayout(table_container)
        table_vbox.setContentsMargins(0, 0, 0, 0)
        table_vbox.setSpacing(0)

        table_header = QLabel("TRANSITION TABLE")
        table_header.setStyleSheet(
            "color: #111111; font-size: 9px; font-weight: 900; letter-spacing: 2px;"
            " background: #FFE000; border: 2px solid #111111; border-bottom: none;"
            " padding: 4px 8px;"
        )
        table_vbox.addWidget(table_header)

        table = QTableWidget()
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        table.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        table.setStyleSheet("""
            QTableWidget {
                background: #FFFFFF;
                color: #111111;
                gridline-color: #CCCCCC;
                font-family: 'Consolas';
                font-size: 12px;
                font-weight: bold;
                border: 2px solid #111111;
            }
            QHeaderView::section {
                background: #F5F0E8;
                color: #111111;
                font-weight: 900;
                font-family: 'Segoe UI';
                border: 1px solid #CCCCCC;
                padding: 4px 8px;
                font-size: 12px;
            }
            QHeaderView::section:checked {
                background: #FFE000;
            }
            QTableWidget::item {
                padding: 4px 8px;
            }
            QTableWidget::item:selected {
                background: #FFE000;
                color: #111111;
            }
            QScrollBar:vertical, QScrollBar:horizontal {
                background: #F5F0E8;
                border: 1px solid #CCCCCC;
                width: 10px;
                height: 10px;
                margin: 0;
            }
            QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
                background: #111111;
                min-height: 20px;
                min-width: 20px;
                border-radius: 0px;
            }
            QScrollBar::add-line, QScrollBar::sub-line { height: 0; width: 0; }
            QScrollBar::add-page, QScrollBar::sub-page { background: none; }
        """)
        table.setShowGrid(True)
        table.setAlternatingRowColors(True)

        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        table.horizontalHeader().setStretchLastSection(False)
        table.horizontalHeader().setMinimumSectionSize(48)
        table.horizontalHeader().setDefaultSectionSize(72)

        table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        table.verticalHeader().setDefaultSectionSize(28)
        table.verticalHeader().setMinimumSectionSize(28)

        table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        table.setHorizontalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)
        table.setVerticalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)

        table_vbox.addWidget(table)
        table_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        stack.addWidget(table_container)
        
        layout.addWidget(stack)
        
        def _toggle_view(checked=False, s=stack, btn=toggle_btn):
            if s.currentIndex() == 0:
                s.setCurrentIndex(1)
                btn.setText("⇌ SHOW VISUAL DIAGRAM")
            else:
                s.setCurrentIndex(0)
                btn.setText("⇌ SHOW TRANSITION TABLE")
                
        toggle_btn.clicked.connect(_toggle_view)
        
        tab.img_label = img_label
        tab.table = table

    def _build_props_tab(self) -> None:
        outer_layout = QVBoxLayout(self._tab_props)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setStyleSheet("""
            QScrollArea { border: none; background: #FFFFFF; }
            QScrollBar:vertical {
                background: #F5F0E8; border: 1px solid #CCCCCC; width: 10px;
            }
            QScrollBar::handle:vertical { background: #111111; min-height: 20px; }
            QScrollBar::add-line, QScrollBar::sub-line { height: 0; }
        """)

        content = QWidget()
        content.setStyleSheet("background: #FFFFFF;")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        def _section_label(text: str) -> QLabel:
            lbl = QLabel(text)
            lbl.setStyleSheet(
                "color: #111111; font-weight: 900; font-size: 10px; font-family: 'Segoe UI';"
                " letter-spacing: 2px; background: #FFE000; border: 2px solid #111111;"
                " border-bottom: none; padding: 4px 8px;"
            )
            return lbl

        layout.addWidget(_section_label("CONTEXT-FREE GRAMMAR"))
        self._cfg_label = QLabel()
        self._cfg_label.setFont(QFont("Consolas", 11, QFont.Weight.Bold))
        self._cfg_label.setStyleSheet(
            "color: #111111; background: #F5F0E8; border: 2px solid #111111; padding: 10px;"
        )
        self._cfg_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self._cfg_label.setTextFormat(Qt.TextFormat.PlainText)
        self._cfg_label.setWordWrap(True)
        layout.addWidget(self._cfg_label)

        layout.addWidget(_section_label("GENERATED STRINGS"))
        self._strings_label = QLabel()
        self._strings_label.setFont(QFont("Consolas", 12, QFont.Weight.Bold))
        self._strings_label.setStyleSheet(
            "color: #111111; background: #FFE000; border: 2px solid #111111; padding: 10px;"
        )
        self._strings_label.setWordWrap(True)
        layout.addWidget(self._strings_label)

        layout.addWidget(_section_label("ENGLISH DESCRIPTION"))
        self._desc_label = QLabel()
        self._desc_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self._desc_label.setStyleSheet(
            "color: #111111; background: #F5F0E8; border: 2px solid #111111; padding: 10px;"
        )
        self._desc_label.setWordWrap(True)
        layout.addWidget(self._desc_label)

        layout.addStretch()
        scroll.setWidget(content)
        outer_layout.addWidget(scroll)

    def _build_sim_tab(self) -> None:
        layout = QVBoxLayout(self._tab_sim)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(6)
        self._sim_input = QLineEdit()
        self._sim_input.setPlaceholderText("Enter test string…")
        self._sim_input.setStyleSheet("""
            QLineEdit {
                background: #FFFFFF;
                color: #111111;
                border: 2px solid #111111;
                padding: 6px 10px;
                font-family: 'Consolas';
                font-weight: bold;
                font-size: 13px;
            }
        """)
        self._sim_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        sim_btn_style = """
            QPushButton {
                background: #FFE000;
                border: 2px solid #111111;
                border-radius: 0px;
                color: #111111;
                font-size: 12px;
                font-weight: 900;
                font-family: 'Segoe UI';
                padding: 6px 12px;
                letter-spacing: 1px;
                white-space: nowrap;
            }
            QPushButton:hover {
                background: #111111;
                color: #FFE000;
            }
            QPushButton:pressed {
                background: #333333;
                color: #FFE000;
            }
            QPushButton:disabled {
                background: #E0E0E0;
                color: #888888;
                border: 2px solid #888888;
            }
        """
        
        self._btn_test = QPushButton("TEST")
        self._btn_test.setStyleSheet(sim_btn_style)
        self._btn_test.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_test.setFixedHeight(34)
        self._btn_test.clicked.connect(self._start_sim)
        
        self._btn_step = QPushButton("STEP")
        self._btn_step.setStyleSheet(sim_btn_style)
        self._btn_step.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_step.setFixedHeight(34)
        self._btn_step.clicked.connect(self._sim_step)
        self._btn_step.setEnabled(False)
        
        self._btn_play = QPushButton("▶ / ‖")
        self._btn_play.setStyleSheet(sim_btn_style)
        self._btn_play.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_play.setFixedHeight(34)
        self._btn_play.clicked.connect(self._toggle_play)
        self._btn_play.setEnabled(False)
        
        controls_layout.addWidget(self._sim_input, 1)
        controls_layout.addWidget(self._btn_test)
        controls_layout.addWidget(self._btn_step)
        controls_layout.addWidget(self._btn_play)
        layout.addLayout(controls_layout)
        
        self._sim_status = QLabel("Ready")
        self._sim_status.setStyleSheet(
            "color: #111111; background: #F5F0E8; border: 2px solid #111111;"
            " padding: 6px 10px; font-size: 12px; font-weight: 900; font-family: 'Segoe UI';"
        )
        self._sim_status.setFixedHeight(34)
        layout.addWidget(self._sim_status)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setStyleSheet("""
            QScrollArea { background: #FFFFFF; border: 2px solid #111111; }
            QScrollBar:vertical, QScrollBar:horizontal {
                background: #F5F0E8; border: 1px solid #CCCCCC;
                width: 10px; height: 10px;
            }
            QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
                background: #111111; min-height: 20px; min-width: 20px;
            }
            QScrollBar::add-line, QScrollBar::sub-line { height: 0; width: 0; }
        """)
        self._sim_img_label = QLabel()
        self._sim_img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._sim_img_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        scroll.setWidget(self._sim_img_label)
        layout.addWidget(scroll, 1)

    def _populate_nfa_tab(self, nfa) -> None:
        img_path = os.path.join(self._temp_dir, "nfa")
        try:
            path = nfa.render_graphviz(img_path)
            self._tab_nfa.img_label.setPixmap(QPixmap(path))
        except ExecutableNotFound:
            self._tab_nfa.img_label.setText("Graphviz not found. Please install Graphviz to view visual models.")
            self._tab_nfa.img_label.setStyleSheet("color: #FF2020; font-size: 14px; font-weight: bold;")
        
        table_data = nfa.transition_table()
        symbols = sorted(nfa.alphabet) + ["ε"]
        self._setup_table(self._tab_nfa.table, [str(r["state"]) for r in table_data], symbols)
        
        for r_idx, row in enumerate(table_data):
            for c_idx, sym in enumerate(symbols):
                nexts = row.get(sym, [])
                if nexts:
                    val = ", ".join(map(str, nexts))
                else:
                    val = ""
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self._tab_nfa.table.setItem(r_idx, c_idx, item)
        self._tab_nfa.table.resizeColumnsToContents()

    def _populate_dfa_tab(self, dfa) -> None:
        img_path = os.path.join(self._temp_dir, "dfa")
        try:
            path = dfa.render_graphviz(img_path)
            self._tab_dfa.img_label.setPixmap(QPixmap(path))
        except ExecutableNotFound:
            self._tab_dfa.img_label.setText("Graphviz not found.")
            self._tab_dfa.img_label.setStyleSheet("color: #FF2020;")
        
        table_data = dfa.transition_table()
        symbols = sorted(dfa.alphabet)
        self._setup_table(self._tab_dfa.table, [r["state"] for r in table_data], symbols)
        
        for r_idx, row in enumerate(table_data):
            for c_idx, sym in enumerate(symbols):
                val = row.get(sym, "")
                if val:
                    item = QTableWidgetItem(str(val))
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self._tab_dfa.table.setItem(r_idx, c_idx, item)
        self._tab_dfa.table.resizeColumnsToContents()

    def _populate_min_dfa_tab(self, min_dfa) -> None:
        img_path = os.path.join(self._temp_dir, "min_dfa")
        try:
            path = min_dfa.render_graphviz(img_path)
            self._tab_min_dfa.img_label.setPixmap(QPixmap(path))
        except ExecutableNotFound:
            self._tab_min_dfa.img_label.setText("Graphviz not found.")
            self._tab_min_dfa.img_label.setStyleSheet("color: #FF2020;")
        
        table_data = min_dfa.transition_table()
        symbols = sorted(min_dfa.alphabet)
        self._setup_table(self._tab_min_dfa.table, [r["state"] for r in table_data], symbols)
        
        for r_idx, row in enumerate(table_data):
            for c_idx, sym in enumerate(symbols):
                val = row.get(sym, "")
                if val:
                    item = QTableWidgetItem(str(val))
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self._tab_min_dfa.table.setItem(r_idx, c_idx, item)
        self._tab_min_dfa.table.resizeColumnsToContents()

    def _setup_table(self, table: QTableWidget, row_labels: list, col_labels: list) -> None:
        table.clear()
        table.setRowCount(len(row_labels))
        table.setColumnCount(len(col_labels))
        table.setHorizontalHeaderLabels(col_labels)
        table.setVerticalHeaderLabels(row_labels)

    def _populate_props_tab(self, cfg, strings, desc) -> None:
        self._cfg_label.setText(cfg.rules_text() or "No rules generated.")
        self._strings_label.setText(", ".join(strings) if strings else "None")
        self._desc_label.setText(desc)

    def _reset_sim_tab(self) -> None:
        self._sim_input.clear()
        self._sim_status.setText("Ready")
        self._sim_status.setStyleSheet(
            "color: #111111; background: #F5F0E8; border: 2px solid #111111;"
            " padding: 6px 10px; font-size: 12px; font-weight: 900; font-family: 'Segoe UI';"
        )
        self._btn_step.setEnabled(False)
        self._btn_play.setEnabled(False)
        self._sim_timer.stop()
        self._sim_steps = []
        if self._min_dfa:
            img_path = os.path.join(self._temp_dir, "sim_dfa")
            try:
                path = self._min_dfa.render_graphviz(img_path)
                self._sim_img_label.setPixmap(QPixmap(path))
            except ExecutableNotFound:
                self._sim_img_label.setText("Graphviz not found.")
                self._sim_img_label.setStyleSheet("color: #FF2020;")

    def _start_sim(self) -> None:
        if not self._min_dfa:
            return
        
        self._sim_timer.stop()
        string = self._sim_input.text()
        self._sim_steps = self._min_dfa.step_trace(string)
        self._sim_current_step = 0
        self._sim_status.setText(f"Simulating: '{string}'")
        self._btn_step.setEnabled(True)
        self._btn_play.setEnabled(True)
        
        img_path = os.path.join(self._temp_dir, f"sim_step_init")
        try:
            path = self._min_dfa.render_graphviz(img_path, highlight_state=self._min_dfa.label(self._min_dfa.start))
            self._sim_img_label.setPixmap(QPixmap(path))
        except ExecutableNotFound:
            self._sim_img_label.setText("Graphviz not found.")
            self._sim_img_label.setStyleSheet("color: #FF2020;")

    def _toggle_play(self) -> None:
        if self._sim_timer.isActive():
            self._sim_timer.stop()
            self._sim_status.setText("Paused")
        else:
            if self._sim_current_step >= len(self._sim_steps):
                self._start_sim()
            self._sim_timer.start(1000) 
            self._sim_status.setText("Playing...")

    def _sim_step(self) -> None:
        if self._sim_current_step >= len(self._sim_steps):
            self._btn_step.setEnabled(False)
            self._btn_play.setEnabled(False)
            self._sim_timer.stop()
            if self._sim_steps and self._sim_steps[-1]["accepted"]:
                self._sim_status.setText("Result: ACCEPTED ✓")
                self._sim_status.setStyleSheet("color: #111111; background: #00E5CC; border: 2px solid #111111; padding: 6px 10px; font-size: 12px; font-weight: 900; font-family: 'Segoe UI';")
            else:
                self._sim_status.setText("Result: REJECTED ✗")
                self._sim_status.setStyleSheet("color: #FFFFFF; background: #FF2020; border: 2px solid #111111; padding: 6px 10px; font-size: 12px; font-weight: 900; font-family: 'Segoe UI';")
            return
            
        step = self._sim_steps[self._sim_current_step]
        frm = step["from_state"]
        to = step["to_state"]
        sym = step["char"]
        
        img_path = os.path.join(self._temp_dir, f"sim_step_{self._sim_current_step}")
        try:
            if step["dead"]:
                self._sim_status.setText(f"Step {self._sim_current_step + 1}: Dead state on '{sym}'")
                self._sim_status.setStyleSheet("color: #FFFFFF; background: #FF2020; border: 2px solid #111111; padding: 6px 10px; font-size: 12px; font-weight: 900; font-family: 'Segoe UI';")
                path = self._min_dfa.render_graphviz(img_path, highlight_state=frm)
                self._btn_step.setEnabled(False)
            else:
                self._sim_status.setText(f"Step {self._sim_current_step + 1}: '{frm}' → '{sym}' → '{to}'")
                self._sim_status.setStyleSheet("color: #111111; background: #FFE000; border: 2px solid #111111; padding: 6px 10px; font-size: 12px; font-weight: 900; font-family: 'Segoe UI';")
                path = self._min_dfa.render_graphviz(img_path, highlight_state=to, highlight_edge=(frm, to, sym))
                
            self._sim_img_label.setPixmap(QPixmap(path))
        except ExecutableNotFound:
            pass 
            
        self._sim_current_step += 1

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
            
        if hasattr(self, '_results_panel') and self._results_panel.isVisible():
            self._panel_shown = True
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