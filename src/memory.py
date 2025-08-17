import json
import os

MEMORY_FILE = "memory.json"
MAX_HISTORY = 10

class GameMemory:
    def __init__(self):
        self.context = self.load_memory()
        self.current_state = ""
        self.previous_state = ""
        
    def load_memory(self):
        """Carga el historial de conversación"""
        if os.path.exists(MEMORY_FILE):
            with open(MEMORY_FILE, 'r') as f:
                return json.load(f)
        return {
            "game": "Genshin Impact",
            "player_status": "",
            "current_mission": "",
            "enemies_encountered": [],
            "recent_events": []
        }

    def save_memory(self):
        """Guarda el historial de conversación"""
        with open(MEMORY_FILE, 'w') as f:
            json.dump(self.context, f)

    def update_memory(self, description):
        """Actualiza el historial de conversación"""
        self.previous_state = self.current_state
        self.current_state = description
        
        if self.has_significant_change():
            self.context["recent_events"].append(description)
            if len(self.context["recent_events"]) > MAX_HISTORY:
                self.context["recent_events"].pop(0)
            self.save_memory()
            
    def has_significant_change(self):
        """Determina si ha habido un cambio significativo en el estado del juego"""
        if self.previous_state == "":
            return True
        return self.current_state != self.previous_state