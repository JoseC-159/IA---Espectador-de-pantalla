import os
import time
import tempfile
import pygame
import threading
from gtts import gTTS

# Inicializar pygame para audio
pygame.mixer.init()
pygame.mixer.set_num_channels(1)

def text_to_speech(text):
    """Versión simplificada que usa solo gTTS + pygame"""
    try:
        # Limpiar texto (remover prefijo [GLaDOS]: si existe)
        clean_text = text.split("]:")[-1].strip()
        
        # 1. Generar archivo de voz temporal
        temp_file = tempfile.mktemp(suffix=".mp3")
        tts = gTTS(text=clean_text, lang='es')
        tts.save(temp_file)
        
        # Pequeña pausa para asegurar escritura
        time.sleep(0.3)
        
        # 2. Reproducir el audio
        play_audio(temp_file)
        
        # 3. Eliminar archivo después de reproducir
        time.sleep(1)  # Esperar liberación de archivo
        if os.path.exists(temp_file):
            os.remove(temp_file)
            
    except Exception as e:
        print(f"[Error TTS]: {str(e)}")

def play_audio(file_path):
    """Función dedicada para reproducir audio"""
    try:
        # Cargar y reproducir
        pygame.mixer.music.load(file_path)
        pygame.mixer.music.play()
        
        # Esperar mientras se reproduce
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
            
    except Exception as e:
        print(f"[Error Audio]: {str(e)}")

# Verificación simple del sistema de audio
def check_audio():
    """Prueba básica de reproducción"""
    try:
        test_file = tempfile.mktemp(suffix=".mp3")
        tts = gTTS(text="Test", lang='en')
        tts.save(test_file)
        play_audio(test_file)
        time.sleep(1)
        if os.path.exists(test_file):
            os.remove(test_file)
        return True
    except:
        return False

# Al importar el módulo, verificar audio
if not check_audio():
    print("¡Advertencia! Problemas detectados en el sistema de audio")
else:
    print("Sistema de audio listo")