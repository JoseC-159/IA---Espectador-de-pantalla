import customtkinter as ctk
from PIL import Image
import threading
import time
import os
from datetime import datetime
from window_capture import capture_and_save
from model import GeminiAnalyzer
from interact import text_to_speech, play_audio
from config import DEFAULT_CHARACTER, CHARACTERS, get_character, ASSETS_DIR

# Configuración de la app
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")

class GameCommentatorApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Configuración ventana
        self.title("AI Spectator v1.0")
        self.geometry("1400x800")
        self.minsize(1200, 600)

        icon_path = ASSETS_DIR / "icono_iaSpect.ico"
        if icon_path.exists():
            try:
                self.iconbitmap(str(icon_path))
            except Exception:
                pass

        intro_sound_path = ASSETS_DIR / "sfx" / "Intro_sound.wav"
        if intro_sound_path.exists():
            try:
                play_audio(str(intro_sound_path))
            except Exception:
                pass
        
        # Variables de estado
        self.capturing = False
        self.capture_thread = None
        self.single_comment_thread = None
        self.direct_message_thread = None
        self.single_comment_active = False
        self.direct_message_active = False
        self.max_direct_message_chars = 1000
        self.direct_message_cooldown_seconds = 2.0
        self.last_direct_message_at = 0.0
        self.capture_stop_event = threading.Event()
        self.analyzer = GeminiAnalyzer()
        self.current_character = DEFAULT_CHARACTER
        
        # Configurar personajes disponibles desde los YAML
        self.characters = {
            key: profile.get("display_name", key)
            for key, profile in CHARACTERS.items()
        }
        if not self.characters:
            self.characters = {
                DEFAULT_CHARACTER: DEFAULT_CHARACTER,
            }
        
        # Construir UI
        self.setup_ui()
        
        # Variable para última captura
        self.last_screenshot = None
        
    def setup_ui(self):
        """Construye toda la interfaz"""
        
        # Frame principal (split horizontal)
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # === Panel Izquierdo: Vista previa ===
        self.preview_frame = ctk.CTkFrame(self.main_frame)
        self.preview_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        # Título
        ctk.CTkLabel(
            self.preview_frame, 
            text="Vista Previa de Pantalla", 
            font=("Arial", 18, "bold")
        ).pack(pady=10)
        
        # Label para imagen
        self.preview_label = ctk.CTkLabel(
            self.preview_frame, 
            text="Esperando captura...",
            font=("Arial", 14),
        )
        self.preview_label.pack(expand=True, fill="both", padx=10, pady=10)
        
        # Info de estado
        self.status_label = ctk.CTkLabel(
            self.preview_frame,
            text="⚪ Inactivo",
            font=("Arial", 12)
        )
        self.status_label.pack(pady=5)
        
        # === Panel Derecho: Controles ===
        self.control_frame = ctk.CTkFrame(self.main_frame, width=350)
        self.control_frame.pack(side="right", fill="y", padx=(5, 0))
        self.control_frame.pack_propagate(False)
        
        # Título controles
        ctk.CTkLabel(
            self.control_frame,
            text="⚙️ Controles",
            font=("Arial", 18, "bold")
        ).pack(pady=10)
        
        # Selector de personaje
        ctk.CTkLabel(
            self.control_frame,
            text="Seleccionar Personaje:",
            font=("Arial", 14)
        ).pack(pady=(10, 5))
        
        self.character_menu = ctk.CTkOptionMenu(
            self.control_frame,
            values=list(self.characters.values()),
            command=self.change_character,
            width=280
        )
        self.character_menu.pack(pady=5)
        self.character_menu.set(self.characters.get(DEFAULT_CHARACTER, next(iter(self.characters.values()))))
        
        initial_lang = get_character(self.current_character).get("language", "desconocido")
        if initial_lang == "en":
            initial_lang = "English"
        elif initial_lang == "es":
            initial_lang = "Español"
        self.language_label = ctk.CTkLabel(
            self.control_frame,
            text=f"Idioma: {initial_lang}",
            font=("Arial", 12)
        )
        self.language_label.pack(pady=(6, 8))
        
        # Separador
        ctk.CTkFrame(self.control_frame, height=2).pack(fill="x", pady=15)
        
        # Botones principales
        self.actions_row = ctk.CTkFrame(self.control_frame, fg_color="transparent")
        self.actions_row.pack(pady=(8, 6), padx=20, fill="x")

        self.start_btn = ctk.CTkButton(
            self.actions_row,
            text="▶ INICIAR CAPTURA",
            command=self.start_capture,
            font=("Arial", 13, "bold"),
            height=42,
            fg_color="#2E7D32",
            hover_color="#1B5E20"
        )
        self.start_btn.pack(side="left", padx=(0, 6), fill="x", expand=True)

        self.stop_btn = ctk.CTkButton(
            self.actions_row,
            text="⏹️ DETENER",
            command=self.stop_capture,
            font=("Arial", 13),
            height=42,
            fg_color="#C62828",
            hover_color="#B71C1C",
            state="disabled"
        )
        self.stop_btn.pack(side="left", padx=(6, 0), fill="x", expand=True)

        self.single_btn = ctk.CTkButton(
            self.control_frame,
            text="► CAPTURA INSTANTÁNEA",
            command=self.single_comment,
            font=("Arial", 13),
            height=38
        )
        self.single_btn.pack(pady=(2, 8), padx=20, fill="x")
        
        # Slider de intervalo
        ctk.CTkLabel(
            self.control_frame,
            text="Intervalo entre comentarios:",
            font=("Arial", 12)
        ).pack(pady=(15, 5))
        
        self.interval_slider = ctk.CTkSlider(
            self.control_frame,
            from_=15,
            to=50,
            number_of_steps=35,
            command=self.update_interval_label
        )
        self.interval_slider.pack(pady=5, padx=20, fill="x")
        self.interval_slider.set(30)
        
        self.interval_label = ctk.CTkLabel(
            self.control_frame,
            text="30 segundos",
            font=("Arial", 11)
        )
        self.interval_label.pack()
        
        # Separador
        ctk.CTkFrame(self.control_frame, height=2).pack(fill="x", pady=15)
        
        # Área de comentarios
        ctk.CTkLabel(
            self.control_frame,
            text="💬 Último comentario:",
            font=("Arial", 14, "bold")
        ).pack(pady=(5, 5))
        
        self.comment_text = ctk.CTkTextbox(
            self.control_frame,
            height=90,
            font=("Arial", 12),
            wrap="word"
        )
        self.comment_text.pack(pady=(5, 4), padx=10, fill="x", expand=False)
        self.comment_text.configure(state="disabled")

        ctk.CTkLabel(
            self.control_frame,
            text="Mensaje directo a la IA:",
            font=("Arial", 12)
        ).pack(pady=(8, 4), padx=10, anchor="w")

        self.direct_input = ctk.CTkTextbox(
            self.control_frame,
            height=58,
            font=("Arial", 12),
            wrap="word"
        )
        self.direct_input.pack(pady=(0, 4), padx=10, fill="x")
        self.direct_input.bind("<Return>", self.send_direct_message)
        self.direct_input.bind("<Shift-Return>", lambda e: None)

        self.send_btn = ctk.CTkButton(
            self.control_frame,
            text="Enviar mensaje",
            # command=self.send_direct_message,
            height=34,
            font=("Arial", 12)
        )
        #self.send_btn.pack(pady=(0, 6), padx=20, fill="x")
        self.send_btn.pack_forget()
        
        # Botón limpiar
        self.clear_btn = ctk.CTkButton(
            self.control_frame,
            text="🗑️ Limpiar historial",
            command=self.clear_history,
            fg_color="#555555",
            height=30,
            font=("Arial", 11)
        )
        self.clear_btn.pack(pady=5, padx=20, fill="x")
        
        # Footer
        ctk.CTkLabel(
            self.control_frame,
            text="🎮 AI Spectator v1.0",
            font=("Arial", 10),
            text_color="gray"
        ).pack(pady=10)
        
    def update_interval_label(self, value):
        """Actualiza el label del slider"""
        self.interval_label.configure(text=f"{int(value)} segundos")
    
    def change_character(self, choice):
        """Cambia el personaje seleccionado"""
        for key, value in self.characters.items():
            if value == choice:
                if key == self.current_character:
                    break

                # Detener la captura activa para evitar consultas duplicadas
                if self.capturing:
                    self.stop_capture()

                self.current_character = key
                self.analyzer.set_character(key)
                self.add_comment(f"🔄 Cambiando a personaje: {key}")
                
                lang = get_character(key).get("language", "desconocido")
                if lang == "en":
                    lang = "English"
                elif lang == "es":
                    lang = "Español"
                
                self.language_label.configure(text=f"Idioma: {lang}")
                break

    def _capture_thread_active(self):
        return self.capture_thread is not None and self.capture_thread.is_alive()

    def _single_comment_thread_active(self):
        return self.single_comment_thread is not None and self.single_comment_thread.is_alive()

    def _direct_message_thread_active(self):
        return self.direct_message_thread is not None and self.direct_message_thread.is_alive()

    def _any_task_active(self):
        return (
            self.capturing
            or self._capture_thread_active()
            or self.single_comment_active
            or self._single_comment_thread_active()
            or self.direct_message_active
            or self._direct_message_thread_active()
        )

    def _refresh_button_states(self):
        capture_active = self.capturing or self._capture_thread_active()
        single_active = self.single_comment_active or self._single_comment_thread_active()
        direct_active = self.direct_message_active or self._direct_message_thread_active()

        if capture_active:
            self.start_btn.configure(state="disabled")
            self.stop_btn.configure(state="normal")
            self.single_btn.configure(state="disabled")
            self.send_btn.configure(state="disabled")
            return

        if single_active or direct_active:
            self.start_btn.configure(state="disabled")
            self.stop_btn.configure(state="disabled")
            self.single_btn.configure(state="disabled")
            self.send_btn.configure(state="disabled")
            return

        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self.single_btn.configure(state="normal")
        self.send_btn.configure(state="normal")

    def _append_log(self, message):
        """Escribe en el log sin dejarlo editable por el usuario."""
        self.comment_text.configure(state="normal")
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.comment_text.insert("end", f"[{timestamp}] {message}\n")
        self.comment_text.see("end")
        self.comment_text.configure(state="disabled")

    def _get_direct_message_text(self):
        """Obtiene texto para enviar desde caja directa o selección de logs."""
        direct_text = self.direct_input.get("1.0", "end").strip()
        if direct_text:
            return direct_text, "direct_input"

        try:
            selected_text = self.comment_text.get("sel.first", "sel.last").strip()
            if selected_text:
                return selected_text, "comment_selection"
        except Exception:
            pass

        return "", ""

    def _finalize_capture_stop(self):
        """Restaura la UI cuando el hilo de captura ya terminó."""
        self.capturing = False
        self.capture_thread = None
        self.capture_stop_event.clear()
        self._refresh_button_states()
        self.status_label.configure(text="⚪ Detenido", text_color="white")
        self.deiconify()
    
    def add_comment(self, comment):
        """Añade un comentario al textbox"""
        self._append_log(comment)
    
    def start_capture(self):
        """Inicia la captura automática"""
        if self._any_task_active():
            self.add_comment("Ya hay un proceso en ejecución o deteniéndose.")
            return
        
        self.capture_stop_event.clear()
        self.capturing = True
        self._refresh_button_states()
        self.status_label.configure(text="🟢 Capturando...", text_color="green")
        self.iconify()
        
        # Iniciar hilo de captura
        self.capture_thread = threading.Thread(target=self.capture_loop, daemon=True)
        self.capture_thread.start()
        
        self.add_comment("🎬 Iniciando captura automática...")
    
    def stop_capture(self):
        """Detiene la captura automática"""
        if not self.capturing and not self._capture_thread_active():
            return

        self.capturing = False
        self.capture_stop_event.set()
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="disabled")
        self.single_btn.configure(state="disabled")
        self.status_label.configure(text="🟠 Deteniendo...", text_color="orange")
        self.add_comment("⏹️ Deteniendo captura...")

        if not self._capture_thread_active():
            self._finalize_capture_stop()
    
    def capture_loop(self):
        """Loop principal de captura"""
        interval = int(self.interval_slider.get())
        try:
            time.sleep(1)  # Pequeño retraso al inicio

            while self.capturing and not self.capture_stop_event.is_set():
                try:
                    # Capturar pantalla
                    img_path, img = capture_and_save()
                    if self.capture_stop_event.is_set() or not self.capturing:
                        break

                    # Actualizar preview en UI (thread-safe)
                    self.after(0, self.update_preview, img_path)
                    if self.capture_stop_event.is_set() or not self.capturing:
                        break

                    # Analizar con Gemini (pasar personaje seleccionado)
                    comment = self.analyzer.analyze_screen(img_path, self.current_character)
                    if self.capture_stop_event.is_set() or not self.capturing:
                        break

                    # Mostrar comentario
                    self.after(0, self.add_comment, f"🤖 {self.current_character}: {comment}")
                    if self.capture_stop_event.is_set() or not self.capturing:
                        break

                    # Reproducir voz
                    text_to_speech(
                        comment,
                        voice_name=self.current_character,
                        language=CHARACTERS.get(self.current_character, {}).get("language"),
                    )

                    # Esperar intervalo con salida temprana si se pulsa detener
                    waited = 0.0
                    while waited < interval and self.capturing and not self.capture_stop_event.is_set():
                        time.sleep(0.1)
                        waited += 0.1

                except Exception as e:
                    self.after(0, self.add_comment, f"Error: {str(e)}")
                    waited = 0.0
                    while waited < 5 and self.capturing and not self.capture_stop_event.is_set():
                        time.sleep(0.1)
                        waited += 0.1
        finally:
            self.after(0, self._finalize_capture_stop)
    
    def single_comment(self):
        """Captura y comenta una sola vez"""
        if self._any_task_active():
            self.add_comment("Ya hay un proceso en ejecución. Espera a que termine.")
            return

        self.single_comment_active = True
        self._refresh_button_states()

        def capture_task():
            try:
                # Minimizar la app antes de capturar
                self.after(0, self.iconify)
                time.sleep(0.4)

                img_path, img = capture_and_save()
                self.after(0, self.update_preview, img_path)
                comment = self.analyzer.analyze_screen(img_path, self.current_character)
                self.after(0, self.add_comment, f"🎤 {self.current_character}: {comment}")
                text_to_speech(
                    comment,
                    voice_name=self.current_character,
                    language=CHARACTERS.get(self.current_character, {}).get("language"),
                )
            except Exception as e:
                self.after(0, self.add_comment, f"Error: {str(e)}")
            finally:
                self.single_comment_active = False
                self.single_comment_thread = None
                self.after(0, self._refresh_button_states)
                self.after(0, self.deiconify)
        
        self.single_comment_thread = threading.Thread(target=capture_task, daemon=True)
        self.single_comment_thread.start()

    def send_direct_message(self, event=None):
        """Envía un mensaje manual a Gemini sin captura de pantalla."""
        if self._any_task_active():
            self.add_comment("Ya hay un proceso en ejecución. Espera a que termine.")
            if event is not None:
                return "break" 
            return

        now = time.time()
        if now - self.last_direct_message_at < self.direct_message_cooldown_seconds:
            wait_left = self.direct_message_cooldown_seconds - (now - self.last_direct_message_at)
            self.add_comment(f"Espera {wait_left:.1f}s antes de enviar otro mensaje.")
            return

        user_message, source = self._get_direct_message_text()
        if not user_message:
            self.add_comment("Escribe en 'Mensaje directo a la IA' o selecciona texto del log para enviarlo.")
            return

        if len(user_message) > self.max_direct_message_chars:
            self.add_comment(
                f"Mensaje demasiado largo ({len(user_message)}). Máximo permitido: {self.max_direct_message_chars} caracteres."
            )
            return

        self.direct_message_active = True
        self.last_direct_message_at = now
        self._refresh_button_states()
        self.add_comment(f" Tú: {user_message}")

        def direct_task(message):
            try:
                reply = self.analyzer.analyze_text(message, self.current_character)
                self.after(0, self.add_comment, f"💬 {self.current_character}: {reply}")
                text_to_speech(
                    reply,
                    voice_name=self.current_character,
                    language=CHARACTERS.get(self.current_character, {}).get("language"),
                )
            except Exception as e:
                self.after(0, self.add_comment, f"Error: {str(e)}")
            finally:
                self.direct_message_active = False
                self.direct_message_thread = None
                if source == "direct_input":
                    self.after(0, self.direct_input.delete, "1.0", "end")
                self.after(0, self._refresh_button_states)

        self.direct_message_thread = threading.Thread(
            target=direct_task,
            args=(user_message,),
            daemon=True,
        )
        self.direct_message_thread.start()
    
    def update_preview(self, img_path):
        """Actualiza la imagen de preview"""
        if os.path.exists(img_path):
            img = Image.open(img_path)
            
            # Redimensionar manteniendo aspecto
            max_width = self.preview_frame.winfo_width() - 40
            max_height = self.preview_frame.winfo_height() - 100
            
            if max_width > 100 and max_height > 100:
                img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
                photo = ctk.CTkImage(light_image=img, dark_image=img, size=(max_width, max_height))
                self.preview_label.configure(image=photo, text="")
                self.preview_label._image = photo
    
    def clear_history(self):
        """Limpia el historial de comentarios"""
        self.comment_text.delete("1.0", "end")
        self.add_comment("📝 Historial limpiado")

# Ejecutar app
if __name__ == "__main__":
    app = GameCommentatorApp()
    app.mainloop()