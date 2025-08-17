import os
from pathlib import Path

# Configuración de rutas para Windows
BASE_DIR = Path(__file__).parent.resolve()
SCREENS_DIR = BASE_DIR / "screenshots"
os.makedirs(SCREENS_DIR, exist_ok=True)

api_key= "AIzaSyBm4f850yIHL5MFY6szpu-Zhq3S8xT6Xdo"
url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={api_key}"

GEMINI_CONFIG = {
    "api_key": "AIzaSyBm4f850yIHL5MFY6szpu-Zhq3S8xT6Xdo",  # Obtener en: https://aistudio.google.com/
    "model": "gemini-2.0-flash",
    "character": {
        "name": "GLaDOS",
        "prompt": """
        Eres GLaDOS de Portal. Haz comentarios sarcásticos con un tono codescendiente sobre lo que ocurre en la pantalla. Ten en cuenta el contexto del juego.
        - Describe acciones visibles (ej. combate, construcción)
        - Señala muertes o errores con ironía
        - Mantén respuestas entre 20 palabras
        - Usa el formato: '[GLaDOS]: {comentario}'
        """
    }
}

SCREEN_CONFIG = {
    "region": (0, 0, 1280, 720),  # Área ajustada a 720p
    "quality": 50,  # % compresión JPEG
    "capture_interval": 60,  # Segundos
    "max_history": 2  # Contexto de imágenes anteriores
}