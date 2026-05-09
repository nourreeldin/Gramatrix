from .base_page import BasePage
from ..fonts import mi

class ContextFreeGridPage(BasePage):
    def __init__(self, parent=None):
        super().__init__(title="Context Free Grammar", icon=mi.ACCOUNT_TREE, subtitle="// CFG studio", parent=parent)
