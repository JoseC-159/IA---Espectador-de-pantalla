import cv2
import pytesseract
import base64
from io import BytesIO
from PIL import Image
import numpy as np
from llama_cpp import Llama
from config import MODEL_CONFIG
import os

# Configuración de Tesseract OCR (¡IMPORTANTE para Windows!)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Ajusta esta ruta

# Cargar modelo de visión (se inicializa solo cuando se necesita)
vision_model = None

def extract_text(image):
    """Extrae texto de la imagen usando OCR con preprocesamiento mejorado"""
    # Convertir a escala de grises
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Preprocesamiento para mejorar OCR
    gray = cv2.medianBlur(gray, 3)
    gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    
    # Configuración personalizada para texto en juegos
    custom_config = r'--oem 3 --psm 6 -l eng+spa'  # OEM 3 = LSTM + Legacy, PSM 6 = Bloque uniforme
    
    return pytesseract.image_to_string(gray, config=custom_config)

def image_to_base64(image):
    """Convierte imagen numpy array a base64"""
    pil_img = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    buffered = BytesIO()
    pil_img.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

def analyze_image(image, prompt):
    """Analiza la imagen usando LLaVA con implementación real de imagen"""
    global vision_model
    
    if not vision_model:
        model_path = os.path.join("models", MODEL_CONFIG["vision_model"])
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Modelo LLaVA no encontrado en {model_path}")
        
        vision_model = Llama(
            model_path=model_path,
            n_ctx=2048,  # Aumentar si tienes RAM suficiente
            n_threads=6,  # Ajustar según tus núcleos de CPU
            n_gpu_layers=0,
            stream=False,
            logits_all=True  # Necesario para LLaVA
        )
    
    # Convertir imagen a base64
    img_base64 = image_to_base64(image)
    
    # Formato especial para LLaVA (requiere template específico)
    llava_prompt = (
        "A user has uploaded an image. Here is the image description: "
        f"<image>{img_base64}</image>\n\n"
        f"User prompt: {prompt}"
    )
    
    response = vision_model.create_chat_completion(
        messages=[{
            "role": "user",
            "content": llava_prompt
        }],
        max_tokens=300,
        temperature=0.2,  # Más bajo para descripciones precisas
        stop=["</s>"]
    )
    
    if isinstance(response, dict):
        content = response['choices'][0]['message']['content']
        return content.strip() if content is not None else ""
    else:
        # Si es un iterador (streaming), concatenamos todo
        full_response = ""
        for chunk in response:
            if 'choices' in chunk:
                content = chunk['choices'][0]['delta'].get('content', '')
                if content is not None:
                    full_response += str(content)
        return full_response.strip()
if __name__ == "__main__":
    # Prueba OCR
    test_img = np.array(Image.open("fghfghfg.PNG"))
    print("Texto detectado:", extract_text(test_img))
    
    # Prueba LLaVA (solo si el modelo está descargado)
    print("Descripción:", analyze_image(test_img, "¿Qué está pasando en este juego?"))