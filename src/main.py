# --------------- main.py ---------------
import time
from window_capture import capture_screen
from img_process import extract_text, analyze_image
from model import generate_response
from interact import text_to_speech, speech_to_text
from memory import load_memory, update_memory
from config import MODEL_CONFIG, SCREEN_CONFIG

def main():
    # Cargar historial de conversación
    history = load_memory()
    
    # Configurar el personaje
    system_prompt = f"Eres {MODEL_CONFIG['character']}. Actúa como este personaje y comenta sobre lo que ves en la pantalla del usuario."
    
    while True:
        try:
            # 1. Capturar pantalla
            screen = capture_screen()
            
            # 2. Analizar contenido
            screen_text = extract_text(screen)
            vision_prompt = f"Describe lo que está sucediendo en esta imagen de un juego. Texto detectado: {screen_text[:500]}..."
            analysis = analyze_image(screen, vision_prompt)
            
            # 3. Generar comentario
            user_input = f"Comenta sobre esta situación del juego: {analysis[:300]}"
            response = generate_response(system_prompt, user_input, history)
            
            # 4. Actualizar memoria y responder
            history = update_memory(history, "user", user_input)
            history = update_memory(history, "assistant", response)
            
            print(f"\n[Análisis]: {analysis[:200]}...")
            print(f"\n[{MODEL_CONFIG['character']}]: {response}")
            text_to_speech(response)
            
            # 5. Esperar antes de la próxima captura
            time.sleep(SCREEN_CONFIG["capture_interval"])
            
        except KeyboardInterrupt:
            print("\nSaliendo del programa...")
            break

if __name__ == "__main__":
    main()