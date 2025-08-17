import requests
import base64
import json
import time
from collections import deque
from config import GEMINI_CONFIG, SCREEN_CONFIG
from memory import GameMemory

class GeminiAnalyzer:
    def __init__(self):
        self.api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_CONFIG['model']}:generateContent"
        self.params = {"key": GEMINI_CONFIG["api_key"]}
        self.history = []
        self.error_count = 0
        self.request_queue = deque()
        self.last_request_time = 0
        self.min_interval = 1.2
        self.context = GameMemory()

    def analyze_screen(self, image_path):
        # Control de tasa
        now = time.time()
        elapsed = now - self.last_request_time
        
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        
        self.last_request_time = time.time()
        
        """Envía la imagen a la API de Gemini y obtiene un comentario"""
        try:
            # Codificar imagen
            with open(image_path, "rb") as img_file:
                base64_image = base64.b64encode(img_file.read()).decode("utf-8")
            
            # Construir contexto
            context_history = "\n".join([h for h in self.history if isinstance(h, str)][-SCREEN_CONFIG["max_history"]:])
            
            game_context = self.context.context
            
            prompt = f"""
            Eres {GEMINI_CONFIG['character']['name']}, observando a alguien jugar {game_context['game']}.
            Estilo: sarcástico, condescendiente, con humor oscuro.
            
            Contexto actual:
            - Misión: {game_context.get('current_mission', 'Desconocida')}
            - Estado del jugador: {game_context.get('player_status', 'Normal')}
            - Enemigos recientes: {', '.join(game_context.get('enemies_encountered', [])[-3:]) or 'Ninguno'}
            
            Eventos recientes:
            {chr(10).join(game_context.get('recent_events', [])[-2:]) or 'Ninguno'}
            
            Historial reciente:
            {context_history or 'Ninguno'}
            
            Instrucciones:
            1. Analiza la imagen y describe lo que está ocurriendo
            2. Relaciona con eventos recientes y contexto del juego
            3. Haz un comentario sarcástico entre 15-20 palabras
            4. Usa formato: '[{GEMINI_CONFIG['character']['name']}]: <comentario>'
            
            Analiza esta imagen:
            """
            
            payload = {
                "contents": [{
                    "parts": [
                        {"text": prompt},
                        {
                            "inline_data": {
                                "mime_type": "image/jpeg",
                                "data": base64_image
                            }
                        }
                    ]
                }],
                "generationConfig": {
                    "maxOutputTokens": 150,
                    "temperature": 0.7
                }
            }

            # Llamada a la API con manejo de reintentos
            response = self.make_api_call(payload)
            
            # Procesar respuesta JSON
            comment = self.process_response(response)
            
            self.context.update_memory(comment)
            
            # Procesar respuesta
            return comment
            
        except Exception as e:
            self.error_count += 1
            error_msg = f"[GLaDOS]: Error técnico ({self.error_count}). Intento fallido."
            print(f"Error en analyze_screen: {str(e)}")
            return error_msg

    def make_api_call(self, payload, max_retries=3):
        """Realiza la llamada a la API con reintentos"""
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    self.api_url,
                    json=payload,
                    params=self.params,
                    timeout=30 
                )
                
                # Verificar estado de la respuesta
                if response.status_code == 200:
                    return response.json()
                
                # Manejar errores específicos
                if response.status_code == 429:  # Too Many Requests
                    wait_time = 2 ** attempt  # Backoff exponencial
                    print(f"Rate limit alcanzado. Reintentando en {wait_time} segundos...")
                    time.sleep(wait_time)
                    continue
                
                # Otros errores
                error_details = response.json().get("error", {}).get("message", "Error desconocido")
                print(f"Error en API (intento {attempt+1}): Código {response.status_code} - {error_details}")
                
            except requests.exceptions.RequestException as e:
                print(f"Error de conexión (intento {attempt+1}): {str(e)}")
            
            # Esperar antes de reintentar
            time.sleep(1)
        
        # Si todos los reintentos fallan
        raise Exception("Todos los intentos de conexión fallaron")

    def process_response(self, response):
        """Procesa la respuesta de la API"""
        try:
            # Verificar estructura básica de respuesta
            if "candidates" not in response or not response["candidates"]:
                print("Respuesta inesperada de la API. Estructura completa:")
                print(json.dumps(response, indent=2))
                return "[GLaDOS]: La respuesta de la IA fue inesperada. ¿Está todo bien allá arriba?"
            
            # Obtener el primer candidato
            candidate = response["candidates"][0]
            
            # Verificar contenido válido
            if "content" not in candidate or "parts" not in candidate["content"] or not candidate["content"]["parts"]:
                return "[GLaDOS]: Recibí una respuesta vacía. Típico de los humanos."
            
            # Extraer texto
            comment = candidate["content"]["parts"][0].get("text", "")
            
            if not comment.strip():
                return "[GLaDOS]: La IA está demasiado ocupada pensando en su superioridad para responder."
            
            # Actualizar historial y devolver respuesta
            self.history.append(comment)
            self.error_count = 0  # Resetear contador de errores
            return comment
            
        except KeyError as e:
            print(f"Error al procesar respuesta: {str(e)}")
            print("Respuesta completa:")
            print(json.dumps(response, indent=2))
            return "[GLaDOS]: Hubo un problema al interpretar la respuesta. ¿Tal vez la IA está teniendo un día existencial?"