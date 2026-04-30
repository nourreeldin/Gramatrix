from .base_page import BasePage
from ..fonts import mi

class ArchivesPage(BasePage):
    def __init__(self, parent=None):
        super().__init__(title="Archives", icon=mi.FOLDER, subtitle="// resources vault", parent=parent)
