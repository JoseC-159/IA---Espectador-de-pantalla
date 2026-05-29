from pathlib import Path
import cv2
import mss
import numpy as np
from datetime import datetime
from config import SCREEN_CONFIG, TEMP_SCREENSHOT_DIR

def prune_files(folder: Path, keep: int):
    files = sorted(folder.glob("*"), key=lambda p: p.stat().st_mtime)
    while len(files) > keep:
        files[0].unlink(missing_ok=True)
        files.pop(0)

def capture_and_save():
    """Captura pantalla y guarda con marca de tiempo"""
    with mss.mss() as sct:
        # Capturar la vista entera del monitor para evitar offsets por escalado/DPI.
        monitor = sct.monitors[1]
        sct_img = sct.grab(monitor)
        img = np.array(sct_img)
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        
        # Compresión y guardado
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        img_path = TEMP_SCREENSHOT_DIR / f"screen_{timestamp}.jpg"
        cv2.imwrite(str(img_path), img, [cv2.IMWRITE_JPEG_QUALITY, SCREEN_CONFIG["quality"]])
        
        return str(img_path), img