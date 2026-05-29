import os
import time
import tempfile
import traceback

import pygame
from elevenlabs import VoiceSettings, save
from elevenlabs.client import ElevenLabs
from pathlib import Path
from uuid import uuid4
from config import ELEVENLABS_CONFIG, DEFAULT_CHARACTER, AUDIO_RUNTIME_DIR, SFX_DIR, MAX_RUNTIME_AUDIO_KEEP
from window_capture import prune_files

# Inicializar pygame para audio
pygame.mixer.init()
pygame.mixer.set_num_channels(1)

client = ElevenLabs(api_key=ELEVENLABS_CONFIG["api_key"])
BASE_DIR = Path(__file__).resolve().parent.parent
AUDIO_RUNTIME_DIR.mkdir(exist_ok=True)

# Perfiles locales por defecto para cuando el personaje no tenga voice_id de ElevenLabs.
# La selección final se hace por idioma y, si existe, por género.
LOCAL_VOICE_PROFILES = {
    "HelpfulGuide": {"language": "en", "gender": "female"},
    "ConciseTutor": {"language": "en", "gender": "male"},
    "EmpatheticCoach": {"language": "en", "gender": "female"},
    "StepByStepTech": {"language": "en", "gender": "male"},
}


def resolve_voice_source(character_key=None, language=None):
    """Resuelve si se debe usar ElevenLabs o una voz local.

    Returns a dictionary with:
    - source: "elevenlabs" or "local"
    - voice_id: resolved ElevenLabs voice id or empty string
    - language: resolved language hint
    - gender: resolved gender hint
    - voice_profile_key: local profile key used for selection
    """
    from config import CHARACTERS, get_character

    profile = get_character(character_key or DEFAULT_CHARACTER)
    resolved_language = language or profile.get("language") or "en"
    voice_id = (profile.get("voice_id") or "").strip()

    if voice_id:
        return {
            "source": "elevenlabs",
            "voice_id": voice_id,
            "language": resolved_language,
            "gender": None,
            "voice_profile_key": None,
        }

    local_profile = LOCAL_VOICE_PROFILES.get(character_key or DEFAULT_CHARACTER, {})
    if not local_profile:
        local_profile = {"language": resolved_language or "en", "gender": None}

    return {
        "source": "local",
        "voice_id": "",
        "language": resolved_language,
        "gender": local_profile.get("gender"),
        "voice_profile_key": character_key or DEFAULT_CHARACTER,
    }


def _normalize_language(language, default="en"):
    """Convierte valores desconocidos o None en un string seguro."""
    if isinstance(language, str) and language.strip():
        return language.strip()
    return default


def _select_local_voice(voices, language="en", gender=None):
    """Selecciona la mejor voz local según idioma y género."""
    if not voices:
        return None

    language = _normalize_language(language).lower()
    gender = (gender or "").lower()

    preferred_names = []
    if language.startswith("en"):
        if gender == "female":
            preferred_names = ["zira", "susan", "eva", "hazel", "lisa"]
        elif gender == "male":
            preferred_names = ["david", "mark", "george", "tom", "daniel"]
        else:
            preferred_names = ["zira", "david", "mark", "susan", "eva", "hazel"]

    def voice_text(voice):
        return " ".join(
            [
                str(getattr(voice, "name", "")),
                str(getattr(voice, "id", "")),
                str(getattr(voice, "languages", "")),
                str(getattr(voice, "gender", "")),
            ]
        ).lower()

    def matches(voice):
        text = voice_text(voice)
        language_match = language in text or "english" in text or "en" in text
        gender_match = not gender or gender in text
        return language_match and gender_match

    for voice in voices:
        text = voice_text(voice)
        if any(name in text for name in preferred_names):
            return getattr(voice, "id", None)

    for voice in voices:
        if matches(voice):
            return getattr(voice, "id", None)

    english_matches = []
    for voice in voices:
        text = voice_text(voice)
        if language in text or "english" in text or "en" in text:
            english_matches.append(getattr(voice, "id", None))

    if english_matches:
        return english_matches[0]

    # Último recurso: mantener la voz actual antes que cambiar a una voz no inglesa
    return getattr(voices[0], "id", None)


def text_to_speech_elevenlabs(text, voice_name=None, language=None):
    """Sintetiza voz usando ElevenLabs API v2."""
    try:
        clean_text = text.split("]:")[-1].strip() if "]" in text else text

        voice_source = resolve_voice_source(voice_name, language)
        if voice_source["source"] != "elevenlabs":
            print(
                f"ElevenLabs skipped for voice_name={voice_name}; local voice selected instead"
            )
            return False

        voice_id = voice_source["voice_id"]

        try:
            print(
                f"ElevenLabs voice resolution: voice_name={voice_name} "
                f"language={voice_source['language']} -> voice_id={voice_id or 'None'}"
            )
        except Exception:
            pass

        # Fallback por si no se resuelve la voz
        if not voice_id:
            print("[ElevenLabs] No hay voice_id configurada para este personaje; omitiendo ElevenLabs TTS")
            return False

        audio = client.text_to_speech.convert(
            voice_id=voice_id,
            text=clean_text,
            model_id=ELEVENLABS_CONFIG["model_id"],
            voice_settings=VoiceSettings(
                stability=ELEVENLABS_CONFIG["stability"],
                similarity_boost=ELEVENLABS_CONFIG["similarity_boost"],
                style=ELEVENLABS_CONFIG["style"],
                use_speaker_boost=ELEVENLABS_CONFIG["use_speaker_boost"],
                speed=ELEVENLABS_CONFIG["speed"],
            ),
            output_format=ELEVENLABS_CONFIG["output_format"],
        )
        
        # guardar audio
        audio_path = AUDIO_RUNTIME_DIR / f"tts_{uuid4().hex}.mp3"
        save(audio, str(audio_path))
        
        # Limpiar audios antiguos
        prune_files(AUDIO_RUNTIME_DIR, MAX_RUNTIME_AUDIO_KEEP)
        
        # Reproducir audio
        pygame.mixer.music.load(str(audio_path))
        pygame.mixer.music.play()

        while pygame.mixer.music.get_busy():
            time.sleep(0.1)

        pygame.mixer.music.stop()
        if hasattr(pygame.mixer.music, "unload"):
            pygame.mixer.music.unload()

        try:
            audio_path.unlink()
        except Exception:
            pass

        return True
    except Exception as e:
        print(f"[Error ElevenLabs]: {str(e)}")
        return False

# Función para listar voces disponibles
def list_available_voices():
    """Lista todas las voces disponibles en ElevenLabs."""
    try:
        voices = client.voices.get_all()
        print("\nVoces disponibles:")
        for voice in voices.voices:
            print(f"→ {voice.name} (ID: {voice.voice_id})")
        return voices.voices
    except Exception as e:
        print(f"Error al obtener voces: {str(e)}")
        return []

# Función principal de tts
def text_to_speech(text, voice_name=None, language=None):
    """Sistema de TTS con fallback."""
    if not voice_name:
        voice_name = DEFAULT_CHARACTER

    voice_source = resolve_voice_source(voice_name, language)

    if voice_source["source"] == "local":
        text_to_speech_fallback(text, voice_name=voice_name, language=voice_source.get("language"))
        return

    # Intentar ElevenLabs primero
    if ELEVENLABS_CONFIG.get("api_key"):
        if text_to_speech_elevenlabs(text, voice_name, language=voice_source.get("language")):
            return

    # Fallback local si ElevenLabs falla o no está configurado
    text_to_speech_fallback(text, voice_name=voice_name, language=voice_source.get("language"))


def text_to_speech_fallback(text, voice_name=None, language=None):
    """
        Fallback local con selección de voz en inglés.

        La selección usa idioma y género como pistas. Cuando los YAML incorporen
        el campo `language`, esta función ya podrá usarlo sin cambios adicionales.
    """
    try:
        import pyttsx3

        engine = pyttsx3.init()
        voices = engine.getProperty("voices") or []

        resolved = resolve_voice_source(voice_name, language)
        voice_id = _select_local_voice(
            voices,
            language=_normalize_language(resolved.get("language")),
            gender=resolved.get("gender"),
        )

        if voice_id:
            try:
                engine.setProperty("voice", voice_id)
            except Exception:
                pass

        try:
            engine.setProperty("rate", 180)
        except Exception:
            pass

        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        print(f"[TTS Fallido]: {text} ({str(e)})")


def play_audio(file_path):
    """Función dedicada para reproducir audio."""
    try:
        pygame.mixer.music.load(file_path)
        pygame.mixer.music.play()

        while pygame.mixer.music.get_busy():
            time.sleep(0.1)

        pygame.mixer.music.stop()
        if hasattr(pygame.mixer.music, "unload"):
            pygame.mixer.music.unload()
    except Exception as e:
        print(f"[Error Audio]: {str(e)}")
        raise
