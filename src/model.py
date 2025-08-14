from llama_cpp import Llama
from config import MODEL_CONFIG

# Instancia global del modelo (carga perezosa)
llm_instance = None

def get_llm():
    """Obtiene la instancia del modelo de lenguaje"""
    global llm_instance
    
    if not llm_instance:
        llm_instance = Llama(
            model_path=f"models/{MODEL_CONFIG['llm_model']}",
            n_ctx=4096,
            n_threads=6,
            n_gpu_layers=0,  # 0 para usar solo CPU
            verbose=False
        )
    
    return llm_instance

def generate_response(system_prompt, user_input, history):
    """Genera respuesta usando el LLM"""
    llm = get_llm()
    
    messages = [
        {"role": "system", "content": system_prompt},
        *history,
        {"role": "user", "content": user_input}
    ]
    
    response = llm.create_chat_completion(
        messages=messages,
        max_tokens=250,
        temperature=0.6
    )
    
    return response['choices'][0]['message']['content']