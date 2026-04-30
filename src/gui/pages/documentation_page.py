from .base_page import BasePage
from ..fonts import mi

class DocumentationPage(BasePage):
    def __init__(self, parent=None):
        super().__init__(title="Documentation", icon=mi.DESCRIPTION, subtitle="// docs reader", parent=parent)
