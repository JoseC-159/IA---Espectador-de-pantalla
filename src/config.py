# Configuración global del sistema
MODEL_CONFIG = {
    "llm_model": "llama-3-8b-instruct.Q4_0.gguf",
    "tts_model": "piper",
    "stt_model": "whisper-tiny",
    "vision_model": "llava-7b-v1.5.Q4_K_M.gguf",
    "character": "GLaDOS"  # Ejemplo: personaje de Portal
}

SCREEN_CONFIG = {
    "region": (0, 0, 1920, 1080),  # Área de captura
    "capture_interval": 5  # Segundos entre capturas
}