import cv2
import mss
import numpy as np
from datetime import datetime
from config import SCREEN_CONFIG, SCREENS_DIR

def capture_and_save():
    """Captura pantalla y guarda con marca de tiempo"""
    with mss.mss() as sct:
        monitor = {
            "top": SCREEN_CONFIG["region"][1],
            "left": SCREEN_CONFIG["region"][0],
            "width": SCREEN_CONFIG["region"][2],
            "height": SCREEN_CONFIG["region"][3]
        }
        sct_img = sct.grab(monitor)
        img = np.array(sct_img)
        
        # Preprocesamiento para mejorar el análisis
        img = cv2.resize(img, (1024, 576))  # Reducir tamaño para mejor procesamiento
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        
        height, width, _ = img.shape
        roi = img[int(height*0.2):int(height*0.8), int(width*0.2):int(width*0.8)]
        
        # Compresión y guardado
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        img_path = f"{SCREENS_DIR}/screen_{timestamp}.jpg"
        cv2.imwrite(img_path, roi, [cv2.IMWRITE_JPEG_QUALITY, SCREEN_CONFIG["quality"]])
        
        return img_path, roi