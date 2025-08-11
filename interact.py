import edge_tts
import asyncio
from img_process import get_ai_comment
from playsound import playsound

async def text_to_speech(text: str, voice: str = "es-MX-JorgeNeural"):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save("Output.mp3")
    voice.save("Alerta.mp3")
    
    playsound("output.mp3")

if __name__ == "__main__":
    while True:
        ai_comment = get_ai_comment()
        asyncio.run(text_to_speech(ai_comment))
