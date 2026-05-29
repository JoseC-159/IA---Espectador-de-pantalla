import json
from pathlib import Path
import os

from numpy import character
from config import DEFAULT_CHARACTER, MEMORY_DIR, get_character

MAX_HISTORY = 10


class Memory:
    def __init__(self, character_key=DEFAULT_CHARACTER):
        self.character_key = character_key
        self.memory_file = self._memory_path(character_key)
        self.memory_file.parent.mkdir(parents=True, exist_ok=True)
        self.context = self.load_memory()
        self.current_state = ""
        self.previous_state = ""
        
    def _memory_path(self, character_key):
        """Genera una memoria exclusiva para cada personaje basada en su nombre"""
        character = get_character(character_key)
        language = character.get("language", "en")
        return MEMORY_DIR / language / f"memo_{character_key.replace(' ','_')}.json"
    
    def set_character(self, character_key):
        """Cambia el personaje activo y carga su memoria correspondiente"""
        if character_key == self.character_key:
            return
        self.save_memory()
        self.character_key = character_key
        self.memory_file = self._memory_path(character_key)
        self.context = self.load_memory()
        self.current_state = ""
        self.previous_state = ""
        
    def load_memory(self):
        """Carga el historial de conversación"""
        if self.memory_file.exists():
            with self.memory_file.open("r", encoding="utf-8") as f:
                return json.load(f)
        return {
            "context": "",
            "user_status": "",
            "current_objective": "",
            "recent_events": [],
            "previous_comments": [],
        }

    def save_memory(self):
        """Guarda el historial de conversación"""
        with self.memory_file.open("w", encoding="utf-8") as f:
            json.dump(self.context, f, ensure_ascii=False, indent=2)

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
        """Determina si ha habido un cambio significativo en el estado actual"""
        if self.previous_state == "":
            return True
        return self.current_state != self.previous_state