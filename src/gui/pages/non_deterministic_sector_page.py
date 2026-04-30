from .base_page import BasePage
from ..fonts import mi

class NonDeterministicSectorPage(BasePage):
    def __init__(self, parent=None):
        super().__init__(title="Non-Deterministic Sector", icon=mi.SCATTER_PLOT, subtitle="// NFA module", parent=parent)
