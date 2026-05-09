from .base_page import BasePage
from ..fonts import mi

class DeterministicSectorPage(BasePage):
    def __init__(self, parent=None):
        super().__init__(title="Finite Automata", icon=mi.ADJUST, subtitle="// DFA module", parent=parent)
