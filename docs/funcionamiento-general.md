# Funcionamiento general del proyecto

Este proyecto es un espectador de pantalla asistido por IA. Su objetivo es observar lo que se muestra en pantalla, interpretar la escena con Gemini y generar una respuesta en texto y voz con detalles personalizables.

## Flujo principal

1. La aplicación captura una imagen de la pantalla.
2. La captura se guarda en un directorio temporal (%localappdata%).
3. `src/model.py` construye el prompt usando el personaje seleccionado y el contexto de memoria.
4. Gemini devuelve un comentario en texto.
5. `src/interact.py` convierte el texto en audio usando ElevenLabs o un respaldo local.
6. La interfaz muestra el comentario, mantiene un historial visible y permite enviar mensajes directos sin captura.

## Componentes principales

### Interfaz gráfica

`src/app_ctk.py` contiene la ventana principal. Desde allí se puede:

- Elegir el personaje activo.
- Ver en todo momento el idioma del personaje seleccionado.
- Iniciar y detener la captura automática.
- Pedir un comentario manual con `CAPTURA INSTANTÁNEA`.
- Enviar mensajes directos a la IA desde la caja de texto (Enter para enviar, Shift+Enter para salto de línea).
- Ver el último comentario y la vista previa de la captura.

### Captura de pantalla

`src/window_capture.py` se encarga de tomar la captura y guardarla como archivo temporal. La captura se usa como entrada para el análisis visual.

### Análisis con Gemini

`src/model.py` recibe la imagen y construye el prompt. El contenido del personaje se obtiene desde `src/config.py` mediante `get_character()`.

### Personajes

Los perfiles se cargan desde `data/characters/**/*.yaml`, por lo que se pueden organizar por carpetas (por ejemplo `en/` y `es/`).

Cada archivo define:

- `key`: nombre interno del personaje.
- `display_name`: texto que ve el usuario.
- `prompt`: instrucciones para Gemini.
- `language`: idioma principal del personaje.
- `gender`: referencia para selección de voz local.
- `voice_id`: voz asociada para ElevenLabs.
- `enabled`: estado del personaje.

### Memoria

`src/memory.py` guarda historial y contexto por personaje en `data/memory/`. Esto permite que cada perfil conserve su propio estado.

### Voz

`src/interact.py` sintetiza el texto generado. Primero intenta ElevenLabs y, si no puede, usa una alternativa local.

## Carpetas relevantes

- `data/characters/`: definición de personajes.
- `data/memory/`: memoria persistente.
- `runtime/audio/`: audio temporal generado.
- `runtime/`: archivos creados en ejecución.
- `assets/`: recursos estáticos del proyecto.

## Variables de entorno

- `GEMINI_API_KEY`: necesaria para llamar a Gemini.
- `ELEVENLABS_API_KEY`: necesaria para usar ElevenLabs.

## Comportamiento por defecto

Si no existe un personaje solicitado o la carpeta de personajes está vacía, `get_character()` devuelve un perfil de respaldo para evitar errores en tiempo de ejecución.

## Comportamiento de concurrencia en UI

- La interfaz evita ejecutar tareas superpuestas de captura, comentario instantáneo y mensaje directo.
- Cuando una tarea está activa, los botones se bloquean temporalmente para evitar envíos duplicados.
- El historial de comentarios permanece en modo solo lectura; la aplicación habilita escritura solo al agregar mensajes nuevos.