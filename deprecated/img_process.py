import cv2
import pytesseract
import base64
from io import BytesIO
import numpy as np
from llama_cpp import Llama
from config import GEMINI_CONFIG
import os
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ImageProcessor")

# Configuración de Tesseract OCR para Windows
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Variable global para el modelo (carga única)
vision_model = None

def extract_text(image):
    """Extrae texto de la imagen usando OCR con preprocesamiento mejorado"""
    try:
        # Convertir a escala de grises
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Preprocesamiento para mejorar OCR
        gray = cv2.medianBlur(gray, 3)
        gray = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)
        
        # Operación morfológica para unir caracteres rotos
        kernel = np.ones((3, 3), np.uint8)
        gray = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)
        
        # Configuración para texto en juegos
        custom_config = r'--oem 3 --psm 6 -l eng+spa'
        
        text = pytesseract.image_to_string(gray, config=custom_config)
        
        return text.strip()
    except Exception as e:
        logger.error(f"Error en OCR: {str(e)}")
        return ""

def compress_image(image, quality=30, max_size=336):
    """Comprime la imagen para reducir su tamaño en base64"""
    try:
        # Redimensionar manteniendo aspect ratio
        h, w = image.shape[:2]
        scale = max_size / max(h, w)
        new_h, new_w = int(h * scale), int(w * scale)
        resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
        
        # Codificar con compresión JPEG
        success, buffer = cv2.imencode('.jpg', resized, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
        if not success:
            raise ValueError("Fallo en codificación JPEG")
        
        return buffer
    except Exception as e:
        logger.error(f"Error comprimiendo imagen: {str(e)}")
        return None

def initialize_vision_model():
    """Inicializa el modelo de visión una sola vez"""
    global vision_model
    if vision_model is None:
        try:
            model_path = MODELS_DIR / MODEL_CONFIG["vision_model"]
            logger.info(f"Inicializando modelo LLaVA: {model_path}")
            
            vision_model = Llama(
                model_path=str(model_path),
                n_ctx=7000,
                n_threads=4,
                n_gpu_layers=0,
                verbose=True
            )
            logger.info(f"✅ Modelo de visión cargado correctamente")
        except Exception as e:
            logger.error(f"Error inicializando modelo: {str(e)}")
            raise
    return vision_model

def analyze_image(image, prompt):
    """Analiza la imagen usando LLaVA con compresión optimizada"""
    try:
        # Comprimir imagen antes de convertir a base64
        compressed_buffer = compress_image(image)
        if compressed_buffer is None:
            return "Error procesando imagen"
        
        # Convertir a base64
        img_base64 = base64.b64encode(compressed_buffer.tobytes()).decode('utf-8')
        
        # Cargar modelo
        model = initialize_vision_model()
        
        
        if isinstance(model, str) and model.startswith("ERROR:"):
            raise RuntimeError(model)
        
        # Crear prompt optimizado
        llava_prompt = (
            f"<|im_start|>user\n{prompt}\n"
            f"<image>{img_base64}</image>\n"
            "<|im_end|>\n"
            "<|im_start|>assistant\n"
        )
        
        # Enviar solicitud con token limit
        response = model.create_completion(
            prompt=llava_prompt,
            max_tokens=100,
            temperature=0.2,
            stop=["<|im_end|>"],
            stream=False
        )
        
        if isinstance(response, dict):
            # Respuesta directa
            return response['choices'][0]['text'].strip()
        else:
            # Respuesta en streaming (concatenar todos los chunks)
            full_text = ""
            for chunk in response:
                if 'choices' in chunk and len(chunk['choices']) > 0:
                    if 'text' in chunk['choices'][0]:
                        full_text += chunk['choices'][0]['text']
            return full_text.strip()
    
    except Exception as e:
        logger.error(f"Error en análisis de imagen: {str(e)}")
        # Fallback a OCR si falla LLaVA
        ocr_text = extract_text(image)
        return f"Análisis fallido. Texto detectado: {ocr_text[:200]}..." if ocr_text else "Error en procesamiento de imagen"