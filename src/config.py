import os
from pathlib import Path
import yaml

# Configuración de rutas (para Windows por ahora)
BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"
MEMORY_DIR = DATA_DIR / "memory"
MEMORY_DIR.mkdir(parents=True, exist_ok=True)
CHARACTERS_DIR = DATA_DIR / "characters"
CHARACTERS_DIR.mkdir(parents=True, exist_ok=True)

RUNTIME_DIR = BASE_DIR / "runtime"
AUDIO_RUNTIME_DIR = RUNTIME_DIR / "audio"
AUDIO_RUNTIME_DIR.mkdir(parents=True, exist_ok=True)

ASSETS_DIR = BASE_DIR / "assets"
SFX_DIR = ASSETS_DIR / "sfx"

# Directorio TEMP para almacenamientos temporales.
TEMP_DIR = Path(os.getenv("LOCALAPPDATA", str(BASE_DIR / "temp")))
TEMP_SCREENSHOT_DIR = TEMP_DIR / "IA Spectator"
TEMP_SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

# Valores de almacenado
MAX_SCREENSHOTS_KEEP = 3
MAX_RUNTIME_AUDIO_KEEP = 6
DEFAULT_CHARACTER = "IShowSpeed"

api_key= os.getenv("GEMINI_API_KEY")
url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={api_key}"

  
def infer_language_from_path(file_path):
    """Inferir el idioma a partir del nombre del archivo o su ruta."""
    name = file_path.stem.lower()
    lang = "en"  # Valor por defecto
    if "english" in name or "en" in name:
        return lang
    elif "spanish" in name or "es" in name:
        lang = "es"
        return lang
    # Más idiomas (por ahora no está contemplado)
    return lang # Valor por defecto si no se puede inferir.    


def load_characters():
    characters = {}

    for file_path in CHARACTERS_DIR.glob("**/*.yaml"):
        with file_path.open("r", encoding="utf-8") as file:
            raw = yaml.safe_load(file) or {}

        key = raw.get("key")
        if not key:
            continue

        characters[key] = {
            "key": key,
            "display_name": raw.get("display_name", key),
            "prompt": raw.get("prompt", ""),
            "voice_id": raw.get("voice_id", ""),
            "language": raw.get("language", infer_language_from_path(file_path)),
            "gender": raw.get("gender", "unknown"),
            "enabled": raw.get("enabled", True),
        }

    return characters

CHARACTERS = load_characters()

# print(f"[DEBUG] Loaded characters: {list(CHARACTERS.keys())}")

def get_character(character_key):
    """Devuelve siempre un diccionario de personaje válido.

    Si no hay personajes cargados devuelve un perfil por defecto mínimo.
    """
    # Si no hay personajes definidos, devolver un perfil mínimo
    if not CHARACTERS:
        return {
            "key": DEFAULT_CHARACTER,
            "display_name": DEFAULT_CHARACTER,
            "prompt": "",
            "voice_id": "",
            "language": "en",
            "enabled": True,
        }

    # Si el personaje solicitado existe, devolverlo
    if character_key and character_key in CHARACTERS:
        return CHARACTERS[character_key]

    # Intentar devolver el personaje por defecto si existe
    if DEFAULT_CHARACTER in CHARACTERS:
        return CHARACTERS[DEFAULT_CHARACTER]

    # Último recurso: devolver el primer personaje disponible
    return next(iter(CHARACTERS.values()))

GEMINI_CONFIG = {
    "api_key": api_key,
    "model": "gemini-2.5-flash-lite",
}

DEFAULT_CHARACTER = "ConciseTutor"

# Configuración de ElevenLabs
ELEVENLABS_CONFIG = {
    "api_key": os.getenv("ELEVENLABS_API_KEY"),
    "voice_id": "jC3jKfbuO8QaWgJq2Eaz",  
    "model_id": "eleven_multilingual_v2",
    "output_format": "mp3_44100_128",
    "stability": 0.9,
    "similarity_boost": 0.85,
    "style": 0.5,
    "speed": 0.9,
    "use_speaker_boost": True
}

SCREEN_CONFIG = {
    "region": (0, 0, 1920, 1080),  # Área ajustada a 1080p
    "quality": 50,  # % compresión JPEG
    "capture_interval": 30,  # Segundos
    "max_history": MAX_SCREENSHOTS_KEEP  # Contexto de imágenes anteriores
}