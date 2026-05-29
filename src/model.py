import profile

import requests
import base64
import json
import time
from collections import deque
from config import GEMINI_CONFIG, SCREEN_CONFIG, get_character, DEFAULT_CHARACTER
from memory import Memory

class GeminiAnalyzer:
    def __init__(self):
        self.api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_CONFIG['model']}:generateContent"
        self.params = {"key": GEMINI_CONFIG["api_key"]}
        self.history = []
        self.error_count = 0
        self.request_queue = deque()
        self.last_request_time = 0
        self.min_interval = 1.2
        self.context = Memory()

    def _wait_rate_limit(self):
        """Evita consultas demasiado seguidas a la API."""
        now = time.time()
        elapsed = now - self.last_request_time
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self.last_request_time = time.time()

    def analyze_screen(self, image_path, character_key=None):
        # Control de tasa
        self._wait_rate_limit()
        
        """Envía la imagen a la API de Gemini y obtiene un comentario"""
        try:
            # Codificar imagen
            with open(image_path, "rb") as img_file:
                base64_image = base64.b64encode(img_file.read()).decode("utf-8")
            
            # Construir contexto estable...
            activity_context = self.context.context

            # Resolve character profile
            if character_key is None:
                character_key = DEFAULT_CHARACTER
            self.context.set_character(character_key)
            activity_context = self.context.context
            profile = get_character(character_key)
            
            if not profile or not profile.get("enabled", True):
                character_key = DEFAULT_CHARACTER
                profile = get_character(DEFAULT_CHARACTER)

            """
            # Debug: mostrar qué perfil se está usando
            try:
                vid = profile.get("voice_id", "")
                prompt_len = len(profile.get("prompt", "") or "")
            except Exception:
                vid = ""
                prompt_len = 0
             print(f"[DEBUG] analyze_screen using character={character_key} name={profile.get('display_name')} voice_id={vid or 'None'} prompt_len={prompt_len} language={profile.get('language', 'undefined')}")
            """    

            # Construir prompt con el perfil del personaje
            base_prompt = profile.get("prompt", "")
            voice_id = profile.get("voice_id", "")
            prompt = f"""
            {base_prompt}

            Describe exactly what is visible in the current screenshot.

            Context:
            - Game or app: {activity_context.get('context', 'Unknown')}
            - Objective: {activity_context.get('current_objective', 'Unknown')}
            - User state: {activity_context.get('user_status', 'Normal')}
            - Recent events: {', '.join(activity_context.get('recent_events', [])[-3:]) or 'None'}
            - Recent comments: {', '.join(activity_context.get('previous_comments', [])[-3:]) or 'None'}

            Instructions:
            1. Focus only on the current image. Consider the context of previous if there's nothing new to comment. For example, comparing the state of previous images with the recent one.
            2. Do not reuse previous replies or mention prior screenshots unless they are visible now.
            3. If the screenshot shows an application window, describe the application window.
            4. Only say the screen is black or empty if the current image is actually black or empty.
            5. If the image is unclear or repetitive, make opinions about it, and suggest to the user to do something else related with what the context is, and/or what the image shows.
            6. Respond in the respective language of the character profile, prioritizing clarity and usefulness. If the profile doesn't specify a language, respond in English.

            Analyze this image:
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
                    "maxOutputTokens": 100,
                    "temperature": 0.7
                }
            }

            # Llamada a la API con manejo de reintentos
            response = self.make_api_call(payload)
            
            # Procesar respuesta JSON
            comment = self.process_response(response)
            
            self.context.update_memory(comment)
            self.history.append(comment)
            if len(self.history) > SCREEN_CONFIG["max_history"]:
                self.history.pop(0)
            
            # Procesar respuesta
            return comment
            
        except Exception as e:
            self.error_count += 1
            error_msg = f"Error técnico ({self.error_count}). Intento fallido."
            print(f"Error en analyze_screen: {str(e)}")
            return error_msg

    def set_character(self, character_key):
        self.context.set_character(character_key)

    def analyze_text(self, user_text, character_key=None):
        """Envía texto directo a Gemini (sin captura de pantalla)."""
        self._wait_rate_limit()

        try:
            if character_key is None:
                character_key = DEFAULT_CHARACTER

            self.context.set_character(character_key)
            activity_context = self.context.context
            profile = get_character(character_key)

            if not profile or not profile.get("enabled", True):
                character_key = DEFAULT_CHARACTER
                profile = get_character(DEFAULT_CHARACTER)

            base_prompt = profile.get("prompt", "")

            prompt = f"""
            {base_prompt}

            The user is sending a direct message. Respond as the selected character.

            Context:
            - Game or app: {activity_context.get('context', 'Unknown')}
            - Objective: {activity_context.get('current_objective', 'Unknown')}
            - User state: {activity_context.get('user_status', 'Normal')}
            - Recent events: {', '.join(activity_context.get('recent_events', [])[-3:]) or 'None'}
            - Recent comments: {', '.join(activity_context.get('previous_comments', [])[-3:]) or 'None'}

            User message:
            {user_text}

            Instructions:
            1. Respond in the respective language of the character profile, prioritizing clarity and usefulness. If the profile doesn't specify a language, respond in English.
            2. Keep the response useful and in-character.
            3. If the message asks for action, propose clear next steps.
            """

            payload = {
                "contents": [{
                    "parts": [
                        {"text": prompt}
                    ]
                }],
                "generationConfig": {
                    "maxOutputTokens": 230,
                    "temperature": 0.7
                }
            }

            response = self.make_api_call(payload)
            comment = self.process_response(response)

            self.context.update_memory(comment)
            self.history.append(comment)
            if len(self.history) > SCREEN_CONFIG["max_history"]:
                self.history.pop(0)

            return comment

        except Exception as e:
            self.error_count += 1
            error_msg = f"Error técnico ({self.error_count}). Intento fallido."
            print(f"Error en analyze_text: {str(e)}")
            return error_msg

    def make_api_call(self, payload, max_retries=3):
        """Realiza la llamada a la API con reintentos..."""
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
                return "La respuesta de la IA fue inesperada. ¿Está todo bien allá arriba?"
            
            # Obtener el primer candidato
            candidate = response["candidates"][0]
            
            # Verificar contenido válido
            if "content" not in candidate or "parts" not in candidate["content"] or not candidate["content"]["parts"]:
                return "No hay respuesta válida de la IA. Parece que está teniendo un momento de bloqueo creativo."
            
            # Extraer texto
            comment = candidate["content"]["parts"][0].get("text", "")
            
            if not comment.strip():
                return "La IA está demasiado ocupada."
            
            # Actualizar historial y devolver respuesta
            self.history.append(comment)
            self.error_count = 0  # Resetear contador de errores
            return comment
            
        except KeyError as e:
            print(f"Error al procesar respuesta: {str(e)}")
            print("Respuesta completa:")
            print(json.dumps(response, indent=2))
            return "Hubo un problema al interpretar la respuesta. ¿Tal vez la IA está teniendo un día existencial?"