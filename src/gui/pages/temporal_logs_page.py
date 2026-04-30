from .base_page import BasePage
from ..fonts import mi

class TemporalLogsPage(BasePage):
    def __init__(self, parent=None):
        super().__init__(title="Temporal Logs", icon=mi.HISTORY, subtitle="// session history archive", parent=parent)
