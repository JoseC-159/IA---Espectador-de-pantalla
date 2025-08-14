import json
import os

MEMORY_FILE = "memory.json"
MAX_HISTORY = 10

def load_memory():
    """Carga el historial de conversación"""
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, 'r') as f:
            return json.load(f)
    return []

def save_memory(history):
    """Guarda el historial de conversación"""
    with open(MEMORY_FILE, 'w') as f:
        json.dump(history[-MAX_HISTORY:], f)

def update_memory(history, role, content):
    """Actualiza el historial de conversación"""
    new_entry = {"role": role, "content": content}
    history.append(new_entry)
    save_memory(history)
    return history