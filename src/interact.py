import sounddevice as sd

# Configuración de audio
AUDIO_SETTINGS = {
    "sample_rate": 16000,
    "channels": 1,
    "duration": 5  # segundos para grabación
}

def text_to_speech(text):
    """Sintetiza voz usando Piper (offline)"""
    # Implementación simplificada - en la práctica usarías:
    # from piper import PiperVoice
    # voice = PiperVoice.load(f"models/{MODEL_CONFIG['tts_model']}")
    # voice.synthesize(text, "output.wav")
    print(f"[Voz]: {text}")
    # Simular generación de audio
    sd.play(*sd.wait())
    return True

def speech_to_text():
    """Captura y transcribe audio usando Whisper"""
    print("Escuchando...")
    audio = sd.rec(
        int(AUDIO_SETTINGS["duration"] * AUDIO_SETTINGS["sample_rate"]),
        samplerate=AUDIO_SETTINGS["sample_rate"],
        channels=AUDIO_SETTINGS["channels"]
    )
    sd.wait()
    
    # En la práctica usarías:
    # from whisper import load_model
    # model = load_model(MODEL_CONFIG["stt_model"])
    # result = model.transcribe(audio)
    
    # Simulación
    return "[Transcripción de voz simulada]"