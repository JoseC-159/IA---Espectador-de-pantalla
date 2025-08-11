import numpy as np
import pyautogui
import cv2

def process_frame():
    screenshot = pyautogui.screenshot() # Esto es para capturar la pantalla.
    frame = cv2.cvt.Color(np.array(screenshot), cv2.COLOR_RGB2BGR)
    return frame

while True:
    frame = process_frame()
    cv2.imshow("Pantalla", frame)
    if cv2.waitKey(1) == ord("q"): #COn esta tecla se detiene el bucle.
        break
    cv2.destroyAllWindows()