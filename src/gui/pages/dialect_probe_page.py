from .base_page import BasePage
from ..fonts import mi

class DialectProbePage(BasePage):
    def __init__(self, parent=None):
        super().__init__(title="Dialect Probe", icon=mi.EXPLORE, subtitle="// language explorer", parent=parent)
