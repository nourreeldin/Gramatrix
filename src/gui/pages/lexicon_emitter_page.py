from .base_page import BasePage
from ..fonts import mi

class LexiconEmitterPage(BasePage):
    def __init__(self, parent=None):
        super().__init__(title="Lexicon Emitter", icon=mi.AUTO_AWESOME, subtitle="// string generator", parent=parent)
