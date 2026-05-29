# IA | Espectador de pantalla (v.1.0)

Aplicación de escritorio en Python que captura lo que aparece en pantalla, lo analiza con Gemini y genera comentarios por texto y voz en tiempo real. La interfaz permite elegir personajes con personalidad propia, ajustar el intervalo de captura, enviar mensajes directos a la IA y revisar el historial de comentarios.

## Funcionalidad general

- Captura la pantalla o la ventana activa y guarda imágenes temporales.
- Envía la captura a Gemini para generar una descripción o comentario.
- Usa perfiles de personaje definidos en `data/characters/**/*.yaml`.
- Muestra en la UI el idioma del personaje seleccionado.
- Reproduce la respuesta con voz usando ElevenLabs y un sistema de respaldo local.
- Mantiene memoria separada por personaje en `data/memory/`.
- Permite usar una interfaz gráfica para iniciar, detener, capturar una vez y enviar mensajes directos.

## Requisitos

- Python 3.11 o compatible.
- Dependencias instaladas desde `requirements.txt`.
- Claves de API configuradas en variables de entorno (seguir ".env.example" como referencia).

## Configuración necesaria

Define estas variables de entorno antes de ejecutar la aplicación:

- `GEMINI_API_KEY`: clave API para Gemini.
- `ELEVENLABS_API_KEY`: clave API para ElevenLabs.

Opcionalmente, puedes ajustar los archivos YAML de `data/characters/` (incluyendo subcarpetas como `en/` y `es/`) para modificar:

- `key`: identificador interno del personaje.
- `display_name`: nombre visible en la interfaz.
- `prompt`: instrucciones de personalidad para Gemini.
- `language`: idioma del personaje (ej. `en`, `es`).
- `gender`: referencia para selección de voz local.
- `voice_id`: voz asociada para ElevenLabs.
- `enabled`: habilita o deshabilita el personaje.

**Puedes agregar tus propios personajes y modificar las personalidades**, pero deben ser construidos en archivos .yaml ubicados en `data/characters/`, bajo la siguiente estructura (puedes copiarla y reemplazar los valores directamente si prefieres):

```yaml
key: [nombre] # se recomienda utilizar un nombre simple. P.Ej: Pablo
display_name: [nombre a mostrar en interfaz]
prompt: [Descripción...] # Puedes explayarte todo lo que requieras. Para una referencia de cómo debería ser un prompt 'funcional', verifica los archivos de personajes predefinidos ya existentes.
language: [idioma] # por ejemplo: en, es
gender: [género opcional] # por ejemplo: male, female, neutral
voice_id: [Id de elevenlabs]
enabled: [¿habilitado?] # (true/false)
```


## Ejecución

Una vez dentro del proyecto, instala las dependencias:

```bash
pip install -r requirements.txt
```

Inicia la interfaz gráfica desde la carpeta `src`:

```bash
cd src
python app_ctk.py
```

Si prefieres la versión de consola, también puedes ejecutar:

```bash
cd src
python main.py
```

## Estructura principal

- `src/config.py`: rutas, carga de personajes YAML y configuración general.
- `src/model.py`: integración con Gemini y construcción del prompt.
- `src/interact.py`: síntesis de voz y reproducción de audio.
- `src/app_ctk.py`: interfaz gráfica principal.
- `src/window_capture.py`: captura de pantalla.
- `data/characters/`: perfiles de personajes (admite subcarpetas por idioma).
- `data/memory/`: memoria persistente por personaje.
- `runtime/`: archivos temporales generados en ejecución.

## Uso de la interfaz

- Selecciona un personaje desde el menú; la app actualiza el idioma mostrado bajo el selector.
- Usa `INICIAR CAPTURA` para comentarios automáticos por intervalo.
- Usa `CAPTURA INSTANTÁNEA` para un análisis único.
- Usa `Mensaje directo a la IA` para consultar sin captura: puedes enviarlo con Enter (y conservar salto de línea con Shift+Enter).
- El historial permanece en modo solo lectura para evitar ediciones accidentales.

## Notas

- Carpetas como `runtime/` se crean automáticamente si no existen.
- Si no hay personajes válidos en `data/characters/`, la aplicación usa un perfil de respaldo por defecto.
- Si una voz de ElevenLabs no está definida o falla, se utiliza síntesis local como respaldo.
## Futuras mejoras:

- Añadir la posibilidad de comunicarse (tanto por voz como por un chat) con la IA en cuestión.
- Establecer más parámetros ajustables (como por ejemplo, ajustes del modelo de IA) desde la UI.
- Mejora de la UI en general.
- Variedad en la selección de modelos de generación de texto, interpretación de imágenes y de voz.
- Despliegue de modelo gratuito (o al menos lo más ilimitado posible) para generación de audio.
