from __future__ import annotations
from typing import List, Dict, Tuple, Set
import os, tempfile

from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QTabWidget, QTableWidget, QTableWidgetItem,
    QHeaderView, QLineEdit, QSizePolicy, QStackedWidget,
    QAbstractItemView, QSpinBox, QCheckBox, QGridLayout, QMessageBox,
)
from PyQt6.QtGui import QFont, QPixmap

from .base_page import BasePage
from ..fonts import mi
from core.dfa_builder import build_dfa_from_table
from core.state_elimination import dfa_to_regex
from core.dfa_minimizer import minimize_dfa
from core.cfg import build_cfg
from core.string_generator import generate_strings
from core.english_phrase import describe_language
try:
    from graphviz.backend.execute import ExecutableNotFound
except ImportError:
    ExecutableNotFound = Exception

                                                                                
_PANEL_SS = """
QFrame#CalcPanel {
    background-color: #FFFFFF;
    border: 3px solid #111111;
    border-radius: 0px;
}
"""
_RESULTS_SS = """
QFrame#ResultsPanel {
    background-color: #FFFFFF;
    border: 3px solid #111111;
    border-radius: 0px;
    margin-top: 10px;
}
"""
_TAB_SS = """
QTabWidget::pane { border: 3px solid #111111; background: #FFFFFF; top: -3px; }
QTabBar::tab { background: #F5F0E8; color: #111111; border: 3px solid #111111;
    padding: 7px 14px; font-weight: 900; font-family: 'Segoe UI';
    font-size: 12px; margin-right: -3px; min-width: 40px; }
QTabBar::tab:selected { background: #FFE000; }
QTabBar::tab:hover:!selected { background: #111111; color: #FFE000; }
QTabBar::scroller { width: 28px; }
QToolButton { background: #F5F0E8; border: 3px solid #111111; color: #111111;
    border-radius: 0px; margin: 2px; }
QToolButton:hover { background: #111111; color: #FFE000; }
"""
_BTN_BACK_SS = """
QPushButton { background: #111111; color: #FFE000; border: 3px solid #111111;
    padding: 4px 12px; font-weight: 900; font-family: 'Segoe UI';
    font-size: 12px; letter-spacing: 1px; }
QPushButton:hover { background: #FFE000; color: #111111; }
"""
_BTN_SIM_SS = """
QPushButton { background: #FFE000; border: 2px solid #111111; border-radius: 0px;
    color: #111111; font-size: 12px; font-weight: 900; font-family: 'Segoe UI';
    padding: 6px 12px; letter-spacing: 1px; }
QPushButton:hover { background: #111111; color: #FFE000; }
QPushButton:pressed { background: #333333; color: #FFE000; }
QPushButton:disabled { background: #E0E0E0; color: #888888; border: 2px solid #888888; }
"""
_TABLE_CELL_SS = """
QTableWidget { background: #FFFFFF; color: #111111; gridline-color: #CCCCCC;
    font-family: 'Consolas'; font-size: 12px; font-weight: bold;
    border: 2px solid #111111; }
QHeaderView::section { background: #F5F0E8; color: #111111; font-weight: 900;
    font-family: 'Segoe UI'; border: 1px solid #CCCCCC; padding: 4px 8px; font-size:12px; }
QTableWidget::item { padding: 4px 8px; }
QTableWidget::item:selected { background: #FFE000; color: #111111; }
QScrollBar:vertical, QScrollBar:horizontal { background: #F5F0E8;
    border: 1px solid #CCCCCC; width: 10px; height: 10px; margin: 0; }
QScrollBar::handle:vertical, QScrollBar::handle:horizontal { background: #111111;
    min-height: 20px; min-width: 20px; }
QScrollBar::add-line, QScrollBar::sub-line { height: 0; width: 0; }
"""

def _sec_lbl(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(
        "color: #111111; font-weight: 900; font-size: 10px; font-family: 'Segoe UI';"
        " letter-spacing: 2px; background: #FFE000; border: 2px solid #111111;"
        " border-bottom: none; padding: 4px 8px;"
    )
    return lbl


class DFAInputPage(BasePage):

    def __init__(self, parent=None):
        super().__init__(title="Finite Automata", icon=mi.ADJUST,
                         subtitle="// DFA transition table input", parent=parent)
        self._temp_dir = tempfile.mkdtemp()
        self._min_dfa = None
        self._sim_timer = QTimer()
        self._sim_timer.timeout.connect(self._sim_step)
        self._sim_steps: list = []
        self._sim_current_step = 0
        self._panel_shown = False

        self._build_input_panel()
        self._build_results_panel()
        self._input_panel.hide()

                                                                              
                   
                                                                              
    def _build_input_panel(self) -> None:
        self._input_panel = QFrame()
        self._input_panel.setObjectName("CalcPanel")
        self._input_panel.setStyleSheet(_PANEL_SS)

        layout = QVBoxLayout(self._input_panel)
        layout.setContentsMargins(24, 18, 24, 18)
        layout.setSpacing(14)

                                                                        
        disp = QFrame()
        disp.setObjectName("DisplayFrame")
        disp.setStyleSheet("""
            QFrame#DisplayFrame {
                background-color: #111111; border: 3px solid #111111;
                border-radius: 0px; min-height: 60px;
            }
        """)
        disp_lay = QHBoxLayout(disp)
        disp_lay.setContentsMargins(20, 10, 20, 10)
        disp_lay.setSpacing(16)

        cap = QLabel("DFA TRANSITION TABLE INPUT")
        cap.setStyleSheet("color: #FFE000; font-size: 11px; font-weight: 900;"
                          " letter-spacing: 3px; background: transparent; border: none;")
        sub = QLabel("Define states, alphabet and transitions below")
        sub.setStyleSheet("color: #888888; font-size: 10px; font-weight: 700;"
                          " background: transparent; border: none;")
        col = QVBoxLayout()
        col.setSpacing(3)
        col.addWidget(cap)
        col.addWidget(sub)
        disp_lay.addLayout(col, 1)
        layout.addWidget(disp)

                                                                        
        self._error_lbl = QLabel("")
        self._error_lbl.setStyleSheet("color: #FF2020; font-size: 10px; font-weight: 700;"
                                      " background: transparent; border: none;")
        self._error_lbl.setVisible(False)
        layout.addWidget(self._error_lbl)

                                                                          
        grid_lay = QGridLayout()
        grid_lay.setSpacing(14)
        grid_lay.setColumnStretch(1, 1)
        grid_lay.setColumnStretch(3, 2)
        
               
        grid_lay.addWidget(QLabel("States:"), 0, 0)
        self._state_spin = QSpinBox()
        self._state_spin.setRange(1, 20)
        self._state_spin.setValue(3)
        self._state_spin.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._state_spin.setStyleSheet(
            "QSpinBox { background:#F5F0E8; border:2px solid #111111; padding:4px;"
            " font-weight:700; font-family:'Segoe UI'; }"
        )
        grid_lay.addWidget(self._state_spin, 0, 1)

        grid_lay.addWidget(QLabel("Alphabet:"), 0, 2)
        self._alpha_input = QLineEdit()
        self._alpha_input.setPlaceholderText("e.g.  a b")
        self._alpha_input.setText("a b")
        self._alpha_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._alpha_input.setStyleSheet(
            "QLineEdit { background:#F5F0E8; border:2px solid #111111; padding:4px 8px;"
            " font-family:'Consolas'; font-weight:700; }"
        )
        grid_lay.addWidget(self._alpha_input, 0, 3)

        build_btn = QPushButton("BUILD TABLE")
        build_btn.setFixedHeight(34)
        build_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        build_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        build_btn.setStyleSheet(
            "QPushButton { background:#111111; color:#FFE000; border:2px solid #111111;"
            " font-weight:900; font-family:'Segoe UI'; padding:0 14px; letter-spacing:1px; }"
            "QPushButton:hover { background:#FFE000; color:#111111; }"
        )
        build_btn.clicked.connect(self._build_table)
        grid_lay.addWidget(build_btn, 0, 4)

               
        grid_lay.addWidget(QLabel("Start state:"), 1, 0)
        self._start_input = QLineEdit()
        self._start_input.setPlaceholderText("q0")
        self._start_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._start_input.setStyleSheet(
            "QLineEdit { background:#F5F0E8; border:2px solid #111111; padding:4px 8px;"
            " font-family:'Consolas'; font-weight:700; }"
        )
        grid_lay.addWidget(self._start_input, 1, 1)

        grid_lay.addWidget(QLabel("Accept states:"), 1, 2)
        self._accept_input = QLineEdit()
        self._accept_input.setPlaceholderText("e.g. q2")
        self._accept_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._accept_input.setStyleSheet(
            "QLineEdit { background:#F5F0E8; border:2px solid #111111; padding:4px 8px;"
            " font-family:'Consolas'; font-weight:700; }"
        )
        grid_lay.addWidget(self._accept_input, 1, 3)

        layout.addLayout(grid_lay)

                                                                        
        self._trans_table = QTableWidget()
        self._trans_table.setEditTriggers(QAbstractItemView.EditTrigger.AllEditTriggers)
        self._trans_table.setStyleSheet(_TABLE_CELL_SS)
        self._trans_table.setMinimumHeight(200)
        self._trans_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(self._trans_table, 1)

                                                                        
        submit_btn = QPushButton("ANALYSE DFA  ▶")
        submit_btn.setFixedHeight(40)
        submit_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        submit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        submit_btn.setStyleSheet(
            "QPushButton { background:#FFE000; color:#111111; border:3px solid #111111;"
            " font-weight:900; font-family:'Segoe UI'; font-size:13px;"
            " padding:0 24px; letter-spacing:1px; }"
            "QPushButton:hover { background:#111111; color:#FFE000; }"
        )
        submit_btn.clicked.connect(self._evaluate)
        layout.addWidget(submit_btn)

        self.layout().addWidget(self._input_panel)
                                                         
        QTimer.singleShot(0, self._build_table)

    def _build_table(self) -> None:
        n = self._state_spin.value()
        raw_alpha = self._alpha_input.text().strip()
        symbols = [s for s in raw_alpha.split() if s]
        if not symbols:
            symbols = ["a"]
        state_names = [f"q{i}" for i in range(n)]

        self._trans_table.clear()
        self._trans_table.setRowCount(n)
        self._trans_table.setColumnCount(len(symbols))
        self._trans_table.setHorizontalHeaderLabels(symbols)
        self._trans_table.setVerticalHeaderLabels(state_names)
        self._trans_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._trans_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        self._trans_table.verticalHeader().setDefaultSectionSize(32)

                                   
        for r in range(n):
            for c in range(len(symbols)):
                it = QTableWidgetItem("")
                it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self._trans_table.setItem(r, c, it)

                                            
        if not self._start_input.text().strip():
            self._start_input.setText("q0")
        if not self._accept_input.text().strip() and n > 0:
            self._accept_input.setText(f"q{n-1}")

                                                                              
                
                                                                              
    def _evaluate(self) -> None:
                                                                       
        n = self._trans_table.rowCount()
        symbols = [
            self._trans_table.horizontalHeaderItem(c).text()
            for c in range(self._trans_table.columnCount())
        ]
        if n == 0 or not symbols:
            self._show_error("Please build a table first.")
            return

        state_names = []
        for r in range(n):
            vh = self._trans_table.verticalHeaderItem(r)
            state_names.append(vh.text() if vh else f"q{r}")

        start = self._start_input.text().strip() or state_names[0]
        accept_raw = self._accept_input.text().strip()
        accept_states: Set[str] = set(accept_raw.split()) if accept_raw else set()

        if start not in state_names:
            self._show_error(f"Start state '{start}' not in state list.")
            return
        unknown = accept_states - set(state_names)
        if unknown:
            self._show_error(f"Unknown accept states: {', '.join(sorted(unknown))}")
            return

                                                                        
        transitions: Dict[Tuple[str, str], str] = {}
        for r, sname in enumerate(state_names):
            for c, sym in enumerate(symbols):
                it = self._trans_table.item(r, c)
                cell = it.text().strip() if it else ""
                if cell and cell in state_names:
                    transitions[(sname, sym)] = cell

                                                                        
        try:
            dfa = build_dfa_from_table(state_names, symbols, transitions, start, accept_states)
        except Exception as e:
            self._show_error(f"DFA build error: {e}")
            return

                                                                        
        regex_str = dfa_to_regex(state_names, symbols, transitions, start, accept_states)

                                                                        
        try:
            min_dfa = minimize_dfa(dfa)
        except Exception:
            min_dfa = dfa
        self._min_dfa = min_dfa

                                                                        
        cfg = build_cfg(min_dfa)
        strings = generate_strings(min_dfa, count=5)
        desc = describe_language(min_dfa, None, strings, regex_str)                

                                                                        
        self._populate_regex_tab(regex_str)
        self._populate_dfa_tab(dfa)
        self._populate_min_dfa_tab(min_dfa)
        self._populate_props_tab(cfg, strings, desc)
        self._reset_sim_tab()

        self._results_expr_label.setText(f"DFA  →  REGEX: {regex_str}")
        self._show_results_panel()

                                                                              
                     
                                                                              
    def _build_results_panel(self) -> None:
        self._results_panel = QFrame()
        self._results_panel.setObjectName("ResultsPanel")
        self._results_panel.setStyleSheet(_RESULTS_SS)
        self._results_panel.hide()
        self._results_panel.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        rl = QVBoxLayout(self._results_panel)
        rl.setContentsMargins(10, 10, 10, 10)
        rl.setSpacing(8)

                
        hdr = QHBoxLayout()
        self._btn_return = QPushButton("← BACK")
        self._btn_return.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_return.setFixedHeight(32)
        self._btn_return.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        self._btn_return.setStyleSheet(_BTN_BACK_SS)
        self._btn_return.clicked.connect(self._hide_results_panel)
        hdr.addWidget(self._btn_return)

        self._results_expr_label = QLabel()
        self._results_expr_label.setStyleSheet(
            "color:#111111; font-family:'Consolas'; font-size:13px; font-weight:bold;")
        self._results_expr_label.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self._results_expr_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        hdr.addWidget(self._results_expr_label, 1)
        rl.addLayout(hdr)

              
        self._results_tabs = QTabWidget()
        self._results_tabs.setStyleSheet(_TAB_SS)
        self._results_tabs.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self._tab_regex = QWidget()
        self._tab_dfa   = QWidget()
        self._tab_min   = QWidget()
        self._tab_props = QWidget()
        self._tab_sim   = QWidget()

        self._results_tabs.addTab(self._tab_regex, "Regex")
        self._results_tabs.addTab(self._tab_dfa,   "DFA Graph")
        self._results_tabs.addTab(self._tab_min,   "Min DFA")
        self._results_tabs.addTab(self._tab_props, "Properties")
        self._results_tabs.addTab(self._tab_sim,   "Simulator")
        rl.addWidget(self._results_tabs)

        self.layout().addWidget(self._results_panel)

        self._build_regex_tab()
        self._build_automata_tab(self._tab_dfa)
        self._build_automata_tab(self._tab_min)
        self._build_props_tab()
        self._build_sim_tab()

    def _show_results_panel(self) -> None:
        self._input_panel.hide()
        self._results_panel.show()

    def _hide_results_panel(self) -> None:
        self._results_panel.hide()
        self._input_panel.show()

                                                                            
    def _build_regex_tab(self) -> None:
        lay = QVBoxLayout(self._tab_regex)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(12)

        lbl = QLabel("EQUIVALENT REGULAR EXPRESSION")
        lbl.setStyleSheet(
            "color:#111111; font-weight:900; font-size:10px; letter-spacing:2px;"
            " background:#FFE000; border:2px solid #111111; border-bottom:none; padding:4px 8px;"
        )
        lay.addWidget(lbl)

        self._regex_result_lbl = QLabel("…")
        self._regex_result_lbl.setFont(QFont("Consolas", 20, QFont.Weight.Bold))
        self._regex_result_lbl.setStyleSheet(
            "color:#111111; background:#F5F0E8; border:2px solid #111111; padding:18px;"
        )
        self._regex_result_lbl.setWordWrap(True)
        self._regex_result_lbl.setTextFormat(Qt.TextFormat.PlainText)
        self._regex_result_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self._regex_result_lbl)

        note = QLabel("Generated using the State Elimination Algorithm")
        note.setStyleSheet("color:#888888; font-size:10px; font-weight:700;"
                           " background:transparent; border:none; padding:4px;")
        note.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(note)
        lay.addStretch()

    def _populate_regex_tab(self, regex_str: str) -> None:
        self._regex_result_lbl.setText(regex_str if regex_str else "∅")

                                                                            
    def _build_automata_tab(self, tab: QWidget) -> None:
        lay = QVBoxLayout(tab)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.setSpacing(8)

        top = QHBoxLayout()
        toggle_btn = QPushButton("⇌ SHOW TRANSITION TABLE")
        toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        toggle_btn.setFixedHeight(32)
        toggle_btn.setStyleSheet(
            "QPushButton { background:#F5F0E8; color:#111111; border:2px solid #111111;"
            " font-weight:900; font-family:'Segoe UI'; font-size:11px; padding:4px 16px; letter-spacing:1px; }"
            "QPushButton:hover { background:#111111; color:#FFE000; }"
        )
        top.addStretch()
        top.addWidget(toggle_btn)
        lay.addLayout(top)

        stack = QStackedWidget()

        img_scroll = QScrollArea()
        img_scroll.setWidgetResizable(True)
        img_scroll.setStyleSheet(
            "QScrollArea { background:#FFFFFF; border:2px solid #111111; }"
            "QScrollBar:vertical,QScrollBar:horizontal { background:#F5F0E8;"
            " border:1px solid #CCCCCC; width:10px; height:10px; }"
            "QScrollBar::handle:vertical,QScrollBar::handle:horizontal { background:#111111;"
            " min-height:20px; min-width:20px; }"
            "QScrollBar::add-line,QScrollBar::sub-line { height:0; width:0; }"
        )
        img_lbl = QLabel()
        img_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        img_lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        img_scroll.setWidget(img_lbl)
        stack.addWidget(img_scroll)

        tbl_cont = QWidget()
        tbl_vbox = QVBoxLayout(tbl_cont)
        tbl_vbox.setContentsMargins(0, 0, 0, 0)
        tbl_hdr = QLabel("TRANSITION TABLE")
        tbl_hdr.setStyleSheet(
            "color:#111111; font-size:9px; font-weight:900; letter-spacing:2px;"
            " background:#FFE000; border:2px solid #111111; border-bottom:none; padding:4px 8px;"
        )
        tbl_vbox.addWidget(tbl_hdr)
        tbl = QTableWidget()
        tbl.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        tbl.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        tbl.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        tbl.setStyleSheet(_TABLE_CELL_SS)
        tbl.setShowGrid(True)
        tbl.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        tbl.horizontalHeader().setMinimumSectionSize(48)
        tbl.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        tbl.verticalHeader().setDefaultSectionSize(28)
        tbl.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        tbl.setHorizontalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)
        tbl.setVerticalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)
        tbl_vbox.addWidget(tbl)
        tbl_cont.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        stack.addWidget(tbl_cont)
        lay.addWidget(stack)

        def _toggle(checked=False, s=stack, b=toggle_btn):
            if s.currentIndex() == 0:
                s.setCurrentIndex(1); b.setText("⇌ SHOW VISUAL DIAGRAM")
            else:
                s.setCurrentIndex(0); b.setText("⇌ SHOW TRANSITION TABLE")
        toggle_btn.clicked.connect(_toggle)

        tab.img_label = img_lbl
        tab.table = tbl

    def _populate_dfa_tab(self, dfa) -> None:
        img_path = os.path.join(self._temp_dir, "dfa_inp")
        try:
            path = dfa.render_graphviz(img_path)
            self._tab_dfa.img_label.setPixmap(QPixmap(path))
        except ExecutableNotFound:
            self._tab_dfa.img_label.setText("Graphviz not found.")
        table_data = dfa.transition_table()
        symbols = sorted(dfa.alphabet)
        self._setup_table(self._tab_dfa.table, [r["state"] for r in table_data], symbols)
        for ri, row in enumerate(table_data):
            for ci, sym in enumerate(symbols):
                val = row.get(sym, "")
                if val:
                    it = QTableWidgetItem(str(val))
                    it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self._tab_dfa.table.setItem(ri, ci, it)
        self._tab_dfa.table.resizeColumnsToContents()

    def _populate_min_dfa_tab(self, min_dfa) -> None:
        img_path = os.path.join(self._temp_dir, "min_dfa_inp")
        try:
            path = min_dfa.render_graphviz(img_path)
            self._tab_min.img_label.setPixmap(QPixmap(path))
        except ExecutableNotFound:
            self._tab_min.img_label.setText("Graphviz not found.")
        table_data = min_dfa.transition_table()
        symbols = sorted(min_dfa.alphabet)
        self._setup_table(self._tab_min.table, [r["state"] for r in table_data], symbols)
        for ri, row in enumerate(table_data):
            for ci, sym in enumerate(symbols):
                val = row.get(sym, "")
                if val:
                    it = QTableWidgetItem(str(val))
                    it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self._tab_min.table.setItem(ri, ci, it)
        self._tab_min.table.resizeColumnsToContents()

    @staticmethod
    def _setup_table(table: QTableWidget, row_labels: list, col_labels: list) -> None:
        table.clear()
        table.setRowCount(len(row_labels))
        table.setColumnCount(len(col_labels))
        table.setHorizontalHeaderLabels(col_labels)
        table.setVerticalHeaderLabels(row_labels)

                                                                            
    def _build_props_tab(self) -> None:
        outer = QVBoxLayout(self._tab_props)
        outer.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(
            "QScrollArea { border:none; background:#FFFFFF; }"
            "QScrollBar:vertical { background:#F5F0E8; border:1px solid #CCCCCC; width:10px; }"
            "QScrollBar::handle:vertical { background:#111111; min-height:20px; }"
            "QScrollBar::add-line,QScrollBar::sub-line { height:0; }"
        )
        content = QWidget()
        content.setStyleSheet("background:#FFFFFF;")
        lay = QVBoxLayout(content)
        lay.setContentsMargins(12, 12, 12, 12)
        lay.setSpacing(10)

        lay.addWidget(_sec_lbl("CONTEXT-FREE GRAMMAR"))
        self._cfg_label = QLabel()
        self._cfg_label.setFont(QFont("Consolas", 11, QFont.Weight.Bold))
        self._cfg_label.setStyleSheet(
            "color:#111111; background:#F5F0E8; border:2px solid #111111; padding:10px;")
        self._cfg_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self._cfg_label.setWordWrap(True)
        lay.addWidget(self._cfg_label)

        lay.addWidget(_sec_lbl("GENERATED STRINGS"))
        self._strings_label = QLabel()
        self._strings_label.setFont(QFont("Consolas", 12, QFont.Weight.Bold))
        self._strings_label.setStyleSheet(
            "color:#111111; background:#FFE000; border:2px solid #111111; padding:10px;")
        self._strings_label.setWordWrap(True)
        lay.addWidget(self._strings_label)

        lay.addWidget(_sec_lbl("ENGLISH DESCRIPTION"))
        self._desc_label = QLabel()
        self._desc_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self._desc_label.setStyleSheet(
            "color:#111111; background:#F5F0E8; border:2px solid #111111; padding:10px;")
        self._desc_label.setWordWrap(True)
        lay.addWidget(self._desc_label)

        lay.addStretch()
        scroll.setWidget(content)
        outer.addWidget(scroll)

    def _populate_props_tab(self, cfg, strings, desc) -> None:
        self._cfg_label.setText(cfg.rules_text() or "No rules generated.")
        self._strings_label.setText(", ".join(strings) if strings else "None")
        self._desc_label.setText(desc)

                                                                            
    def _build_sim_tab(self) -> None:
        lay = QVBoxLayout(self._tab_sim)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.setSpacing(8)

        ctrl = QHBoxLayout()
        ctrl.setSpacing(6)
        self._sim_input = QLineEdit()
        self._sim_input.setPlaceholderText("Enter test string…")
        self._sim_input.setStyleSheet(
            "QLineEdit { background:#FFFFFF; color:#111111; border:2px solid #111111;"
            " padding:6px 10px; font-family:'Consolas'; font-weight:bold; font-size:13px; }"
        )
        self._sim_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self._btn_test = QPushButton("TEST")
        self._btn_test.setStyleSheet(_BTN_SIM_SS)
        self._btn_test.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_test.setFixedHeight(34)
        self._btn_test.clicked.connect(self._start_sim)

        self._btn_step = QPushButton("STEP")
        self._btn_step.setStyleSheet(_BTN_SIM_SS)
        self._btn_step.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_step.setFixedHeight(34)
        self._btn_step.clicked.connect(self._sim_step)
        self._btn_step.setEnabled(False)

        self._btn_play = QPushButton("▶ / ‖")
        self._btn_play.setStyleSheet(_BTN_SIM_SS)
        self._btn_play.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_play.setFixedHeight(34)
        self._btn_play.clicked.connect(self._toggle_play)
        self._btn_play.setEnabled(False)

        ctrl.addWidget(self._sim_input, 1)
        ctrl.addWidget(self._btn_test)
        ctrl.addWidget(self._btn_step)
        ctrl.addWidget(self._btn_play)
        lay.addLayout(ctrl)

        self._sim_status = QLabel("Ready")
        self._sim_status.setStyleSheet(
            "color:#111111; background:#F5F0E8; border:2px solid #111111;"
            " padding:6px 10px; font-size:12px; font-weight:900; font-family:'Segoe UI';"
        )
        self._sim_status.setFixedHeight(34)
        lay.addWidget(self._sim_status)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(
            "QScrollArea { background:#FFFFFF; border:2px solid #111111; }"
            "QScrollBar:vertical,QScrollBar:horizontal { background:#F5F0E8;"
            " border:1px solid #CCCCCC; width:10px; height:10px; }"
            "QScrollBar::handle:vertical,QScrollBar::handle:horizontal { background:#111111;"
            " min-height:20px; min-width:20px; }"
            "QScrollBar::add-line,QScrollBar::sub-line { height:0; width:0; }"
        )
        self._sim_img_label = QLabel()
        self._sim_img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._sim_img_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        scroll.setWidget(self._sim_img_label)
        lay.addWidget(scroll, 1)

    def _reset_sim_tab(self) -> None:
        self._sim_input.clear()
        self._sim_status.setText("Ready")
        self._sim_status.setStyleSheet(
            "color:#111111; background:#F5F0E8; border:2px solid #111111;"
            " padding:6px 10px; font-size:12px; font-weight:900; font-family:'Segoe UI';"
        )
        self._btn_step.setEnabled(False)
        self._btn_play.setEnabled(False)
        self._sim_timer.stop()
        self._sim_steps = []
        if self._min_dfa:
            img_path = os.path.join(self._temp_dir, "sim_dfa_inp")
            try:
                path = self._min_dfa.render_graphviz(img_path)
                self._sim_img_label.setPixmap(QPixmap(path))
            except ExecutableNotFound:
                self._sim_img_label.setText("Graphviz not found.")

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
        img_path = os.path.join(self._temp_dir, "sim_step_init_inp")
        try:
            path = self._min_dfa.render_graphviz(
                img_path, highlight_state=self._min_dfa.label(self._min_dfa.start))
            self._sim_img_label.setPixmap(QPixmap(path))
        except ExecutableNotFound:
            self._sim_img_label.setText("Graphviz not found.")

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
                self._sim_status.setStyleSheet(
                    "color:#111111; background:#00E5CC; border:2px solid #111111;"
                    " padding:6px 10px; font-size:12px; font-weight:900; font-family:'Segoe UI';")
            else:
                self._sim_status.setText("Result: REJECTED ✗")
                self._sim_status.setStyleSheet(
                    "color:#FFFFFF; background:#FF2020; border:2px solid #111111;"
                    " padding:6px 10px; font-size:12px; font-weight:900; font-family:'Segoe UI';")
            return

        step = self._sim_steps[self._sim_current_step]
        frm, to, sym = step["from_state"], step["to_state"], step["char"]
        img_path = os.path.join(self._temp_dir, f"sim_step_inp_{self._sim_current_step}")
        try:
            if step["dead"]:
                self._sim_status.setText(f"Step {self._sim_current_step + 1}: Dead state on '{sym}'")
                self._sim_status.setStyleSheet(
                    "color:#FFFFFF; background:#FF2020; border:2px solid #111111;"
                    " padding:6px 10px; font-size:12px; font-weight:900; font-family:'Segoe UI';")
                path = self._min_dfa.render_graphviz(img_path, highlight_state=frm)
                self._btn_step.setEnabled(False)
            else:
                self._sim_status.setText(f"Step {self._sim_current_step + 1}: '{frm}' → '{sym}' → '{to}'")
                self._sim_status.setStyleSheet(
                    "color:#111111; background:#FFE000; border:2px solid #111111;"
                    " padding:6px 10px; font-size:12px; font-weight:900; font-family:'Segoe UI';")
                path = self._min_dfa.render_graphviz(
                    img_path, highlight_state=to, highlight_edge=(frm, to, sym))
            self._sim_img_label.setPixmap(QPixmap(path))
        except ExecutableNotFound:
            pass
        self._sim_current_step += 1

                                                                            
    def _show_error(self, msg: str) -> None:
        self._error_lbl.setText(f"⚠ {msg}")
        self._error_lbl.setVisible(True)
        QTimer.singleShot(4000, self._clear_error)

    def _clear_error(self) -> None:
        self._error_lbl.setText("")
        self._error_lbl.setVisible(False)

                                                                           
    def play_enter_animation(self) -> None:
        self._panel_shown = False
        self._input_panel.hide()
        super().play_enter_animation()
        self._watch_for_typing_done()

    def _watch_for_typing_done(self) -> None:
        def _check():
            if hasattr(self, "_subtitle_timer") and not self._subtitle_timer.isActive():
                _poller.stop()
                QTimer.singleShot(200, self._show_input_panel)
        _poller = QTimer(self)
        _poller.timeout.connect(_check)
        _poller.start(50)
        self._typing_poller = _poller

    def _show_input_panel(self) -> None:
        if self._panel_shown:
            return
        if hasattr(self, "_results_panel") and self._results_panel.isVisible():
            self._panel_shown = True
            return
        self._panel_shown = True
        self._input_panel.setMaximumHeight(0)
        self._input_panel.show()
        grow = QPropertyAnimation(self._input_panel, b"maximumHeight", self)
        grow.setDuration(440)
        grow.setStartValue(0)
        grow.setEndValue(16_777_215)
        grow.setEasingCurve(QEasingCurve.Type.OutCubic)
        grow.start()
        self._grow_anim = grow
