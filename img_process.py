from llava import LlavaAPI
from window_capture import process_frame
from ultralytics import YOLO

yolo = YOLO("yolov8n.pt")
llava = LlavaAPI("llava-1.5-7b")

def get_ai_comment():
    #Modelo de YOLO para poder procesar imagenes 
    results = yolo(process_frame)
    results.show()

    # LLava para comentar y esas cosas
    respuesta = llava.query("Menciona algo relevante", image=process_frame)
    print(respuesta)
    return respuesta