from .base_page import BasePage
from ..fonts import mi

class NexusPage(BasePage):
    def __init__(self, parent=None):
        super().__init__(title="Nexus", icon=mi.HOME, subtitle="// dashboard interface online", parent=parent, isBackBtnVisible=False)
