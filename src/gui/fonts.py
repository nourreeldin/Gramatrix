from pathlib import Path
from PyQt6.QtGui import QFont, QFontDatabase

class _MI:
    HOME          = "\ue88a"   
    HISTORY       = "\ue889"   
    CODE          = "\ue86f"  
    ACCOUNT_TREE  = "\ue97a"   
    AUTO_AWESOME  = "\ue65f"   
    EXPLORE       = "\ue87a"   
    ADJUST        = "\ue39e"   
    SCATTER_PLOT  = "\ue268"   
    FOLDER        = "\ue2c7"   
    DESCRIPTION   = "\ue873"   
    POWER         = "\ue8ac"   
    CHEVRON_LEFT  = "\ue5cb"   
    CHEVRON_RIGHT = "\ue5cc"   
    DIAMOND       = "\ue8f4"   
    MENU          = "\ue5d2"   
    BACK          = "\ue5cb"   

mi = _MI()

_FAMILY   = "Material Icons"
_loaded   = False
_fam_name = _FAMILY    

def load_material_icons() -> bool:
    global _loaded, _fam_name
    if _loaded:
        return True

    font_path = (Path(__file__).resolve().parents[2] / "assets" / "fonts" / "MaterialIcons-Regular.ttf")

    """
    if not font_path.exists():
        print(f"[fonts] ERR Material Icons TTF not found: {font_path}")
        print("[fonts]   Icons will appear as blank squares until the TTF is installed.")
        return False
    """

    fid = QFontDatabase.addApplicationFont(str(font_path))
    if fid == -1:
                                                              
        return False

    families = QFontDatabase.applicationFontFamilies(fid)
                                                       
    if families:
        _fam_name = families[0]   
        _loaded   = True
                                                                       
        return True

                                                                         
    return False

def icon_font(size: int = 20) -> QFont:
    f = QFont(_fam_name)
    f.setPointSize(size)
    return f

def text_font(size: int = 10, weight: QFont.Weight = QFont.Weight.Medium) -> QFont:
    f = QFont("Segoe UI")
    f.setPointSize(size)
    f.setWeight(weight)
    return f

def material_font(size: int = 18) -> QFont:
    return icon_font(size)