from window_capture import capture_and_save
from model import GeminiAnalyzer
from config import SCREEN_CONFIG
import time
import os
from interact import text_to_speech

def main():
    analyzer = GeminiAnalyzer()
    
    while True:
        try:
            # 1. Capturar pantalla
            img_path, _ = capture_and_save()
            
            # 2. Analizar con Gemini
            comment = analyzer.analyze_screen(img_path)
            print(f"\n{comment}")
            
            # 3. Respuesta por voz
            text_to_speech(comment)
            
            # Eliminar imagen capturada para ahorrar espacio
            os.remove(img_path)
            
            # 4. Esperar intervalo
            time.sleep(SCREEN_CONFIG["capture_interval"])
            
        except KeyboardInterrupt:
            print("\nSistema terminado por el usuario")
            break

if __name__ == "__main__":
    main()