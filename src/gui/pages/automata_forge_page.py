from .base_page import BasePage

class AutomataForgePage(BasePage):
    def __init__(self, parent=None):
        super().__init__(title="Automata Forge", icon="✦", subtitle="// automata workspace", parent=parent)
