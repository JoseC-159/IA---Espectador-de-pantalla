import mss
import numpy as np
from config import SCREEN_CONFIG

def capture_screen():
    """Captura la pantalla en la región especificada"""
    with mss.mss() as sct:
        monitor = {
            "top": 0, "left": 0, "width": 1366, "height": 768  # 720p
        }
        sct_img = sct.grab(monitor)
        return np.array(sct_img)
    return cv2.resize(np.array(sct.grab(monitor)), (683, 384))