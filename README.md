# Transcripción, traducción y doblaje (chino → español)

Acepta **vídeos** (mp4, mov…) y **audios** (mp3, wav, m4a…) en chino y genera:

| Archivo | Contenido |
|---|---|
| `nombre_es.txt` | Transcripción bilingüe con tiempos: cada frase en chino y su traducción. |
| `nombre_es_original.srt` | Subtítulos en chino. |
| `nombre_es.srt` | Subtítulos en español. |
| `nombre_es.mp3` | Audio doblado al español, con voz neuronal sincronizada con el original. |
| `nombre_es.mp4` | Solo con vídeos: vídeo doblado, con subtítulos quemados y las zonas que elijas tapadas. |

Para obtener solo los textos, sin doblar, añade `--text-only`.

Todo es gratis: no necesita claves de API.

| Paso | Herramienta |
|---|---|
| Transcripción | [faster-whisper](https://github.com/SYSTRAN/faster-whisper) (`large-v3`) |
| Traducción | [NLLB-200](https://huggingface.co/facebook/nllb-200-distilled-600M) de Meta, local |
| Voz | [Edge-TTS](https://github.com/rany2/edge-tts) (voces neuronales de Microsoft) |
| Separar música y voz | [Demucs](https://github.com/facebookresearch/demucs) (opcional) |
| Vídeo, mezcla y subtítulos | FFmpeg |

> Usa solo vídeos sobre los que tengas derechos o permiso para reutilizar.

## Uso en Google Colab (recomendado)

1. Abre `notebooks/Doblaje_Colab.ipynb` en Colab: *Archivo → Abrir cuaderno → GitHub* y marca «Incluir repositorios privados».
2. Activa la GPU: *Entorno de ejecución → Cambiar tipo → T4 GPU*.
3. Ejecuta las celdas en orden. El repositorio es privado, así que el primer paso pide un [token de GitHub](https://github.com/settings/tokens) con permiso de lectura. También puedes guardarlo como secreto `GITHUB_TOKEN` en Colab.

El notebook hace todo en dos fases:

1. **Transcribir y traducir.** Te muestra una tabla con el texto chino y la traducción, y puedes corregirla en `segments.json`.
2. **Doblar y renderizar.** Genera la voz, mezcla el audio, tapa las zonas, quema los subtítulos y descarga el resultado.

## Uso en tu PC (Windows con WSL Ubuntu y GPU NVIDIA)

Instalación, una sola vez:

```bash
sudo apt update && sudo apt install -y ffmpeg git
curl -LsSf https://astral.sh/uv/install.sh | sh && source ~/.bashrc
git clone https://github.com/statsuya500/yousef-research-engine.git ~/doblaje
cd ~/doblaje
uv venv -p 3.11 venv && source venv/bin/activate
uv pip install torch --index-url https://download.pytorch.org/whl/cu128
uv pip install -r requirements.txt
```

`git clone` pide usuario y contraseña. Como contraseña usa un [token de GitHub](https://github.com/settings/tokens): GitHub no acepta la contraseña normal.

Para procesar un vídeo o audio, cópialo a `C:\videos` y ejecuta:

```bash
cd ~/doblaje && source venv/bin/activate
python -m dubber run /mnt/c/videos/clip.mp4 --background separate
```

Los resultados (`clip_es.mp4`, `.mp3`, `.txt` y `.srt`) aparecen en la misma carpeta de Windows.

- Cierra Fooocus u otros programas que usen la GPU antes de doblar.
- Con 8 GB de RAM, si se cierra a mitad, usa `--whisper-model medium`.

## Traducción de mejor calidad (guion → traducir → transcript)

La traducción automática traduce frase a frase sin contexto y a veces falla. Para un resultado mejor, traduce el guion completo con ChatGPT, Claude o DeepL:

```bash
# 1. Transcribe y saca el guion chino numerado, sin tiempos
python -m dubber guion /mnt/c/videos/clip.mp4        # crea clip_guion_zh.txt

# 2. Traduce clip_guion_zh.txt (manteniendo los números [001]…) y guárdalo como clip_guion_es.txt

# 3. Junta la traducción con los tiempos: transcript, subtítulos y doblaje
python -m dubber run /mnt/c/videos/clip.mp4 --translation /mnt/c/videos/clip_guion_es.txt
```

Añade `--text-only` en el paso 3 si solo quieres el transcript (`.txt`) y los subtítulos, sin doblaje.

## Uso por línea de comandos

```bash
pip install -r requirements.txt   # necesita también ffmpeg instalado

# Todo de una vez
python -m dubber run video.mp4 --mask "blur:20,20,220,80" --background separate

# Un audio: genera textos y mp3 doblado
python -m dubber run entrevista.m4a

# Solo transcribir y traducir (txt + srt), sin doblar
python -m dubber run entrevista.m4a --text-only

# En dos fases, revisando la traducción
python -m dubber run video.mp4 --text-only                   # crea los textos y video_work/segments.json
python -m dubber run video.mp4 --segments video_work/segments.json --voice es-MX-JorgeNeural

# Probar las zonas en un fotograma antes de renderizar
python -m dubber preview video.mp4 --at 3 --mask "box:0,620,1280,100" -o preview.png
```

### Opciones principales

| Opción | Qué hace |
|---|---|
| `--mask modo:x,y,ancho,alto` | Zona a tapar (repetible). Modos: `blur` (difuminar), `delogo` (rellenar con el entorno), `box` (rectángulo negro). |
| `--background separate` | Quita la voz china con Demucs y conserva música y efectos. Es lo que mejor suena. |
| `--background duck` | Deja el audio original bajito debajo del doblaje (`--bg-volume 0.2`). Es más rápido. |
| `--background none` | Solo la voz doblada. |
| `--voice` | Voz de Edge-TTS: `es-ES-AlvaroNeural`, `es-ES-ElviraNeural`, `es-MX-JorgeNeural`, `es-MX-DaliaNeural`… |
| `--rate +10%` | Velocidad base de la voz. |
| `--max-speed 1.5` | Cuánto se puede acelerar una frase para que quepa en su hueco. |
| `--no-burn` / `--no-subs` | Subtítulos solo en `.srt` / sin subtítulos. |
| `--font-size 16` | Tamaño de los subtítulos quemados. |
| `--whisper-model` | `large-v3` (mejor), `medium` o `small` (más rápido). |

Los resultados se guardan junto al original y los archivos intermedios en `nombre_work/`.

## Consejos

- Si una frase doblada se pisa con la siguiente, acorta la traducción en `segments.json` o sube `--max-speed`.
- Para tapar subtítulos chinos incrustados, cubre la franja inferior con `box` o `blur`. Los subtítulos en español se dibujan encima.
- `delogo` funciona mejor con logos pequeños y fondos sencillos. Para zonas grandes usa `blur`.

## Vídeos estilo manhwa desde una historia (`mangavid`)

Convierte un guion de escenas en un vídeo narrado: una imagen por escena generada en tu GPU
(Animagine XL 4.0, ~11 s por imagen con 8 GB de VRAM), voz con Edge-TTS, movimiento suave,
subtítulos de 2 líneas como máximo y un `.srt` completo para YouTube.

```text
@estilo: masterpiece, high score, great score, absurdres, manhwa style, detailed background
@negativo: lowres, bad anatomy, bad hands, text, watermark, blurry
@elena: young woman, long straight black hair, red eyes, gold hair ornament

[001] 1girl, solo, @elena, black dress, kneeling, crying, burning mansion, night
La noche en que Elena Vargas murió, la mansión de su familia ardía como una antorcha.
```

```bash
python -m mangavid run historia.txt                 # historia.mp4 + historia.srt
python -m mangavid run historia.txt --only-images   # solo imágenes, para revisarlas
python -m mangavid run historia.txt --music musica.mp3 --voice es-MX-JorgeNeural
```

Todo se guarda en `historia_work/` con un hash por escena: si se corta o cambias una escena,
al relanzar solo se rehace lo que falta. Pensado para vídeos de horas.

### Miniaturas

Al estilo de los canales de manhwa narrado: los personajes, una etiqueta amarilla con flecha curva hacia cada uno (`PROTA`, `HIJA`, `CEO`…) y una frase corta.

```text
@miniatura: 1boy, 1girl, @kai, @luna, kai grabbing her arm, she is crying, rooftop, blue sky
@miniatura_texto: @kai=PROTA | @luna=HIJA | ¡No saltes!
```

```bash
python -m mangavid miniatura historia.txt                           # 4 opciones en historia_miniaturas/
python -m mangavid miniatura historia.txt --texto "@kai=PROTA | ?!?" # cambia solo los rótulos (segundos)
python -m mangavid miniatura historia.txt --escena 12               # usa la imagen de la escena 12
```

- **Tamaño:** 1280×720 y menos de 2 MB, como pide YouTube.
- **Personajes:** salen de izquierda a derecha en el orden de `@miniatura`, con las caras de sus fichas.
- **Rótulos:** `@personaje=TEXTO` lleva flecha hacia su cabeza (detectada con `imgutils`). Un texto sin `@` va en el hueco más despejado.
- **Skill `miniatura`:** hace que Claude proponga la imagen y los rótulos leyendo el guion.
- **Tipografía:** Anton (licencia SIL OFL, en `mangavid/fonts/`).

Consejos para las imágenes:
- Evita colores en accesorios que puedan contagiarse al pelo (p. ej. `red hair ornament` tiñe el pelo de rojo).
- Las escenas con dos personajes pueden mezclar rasgos (color de ojos o pelo). Si importa, usa planos de un solo personaje.
- Para rehacer una imagen concreta, cambia algo de su descripción; para rehacerlas todas, usa `--seed`.

## Pruebas

```bash
pip install pytest && python -m pytest -q
```

## Skills de YouTube para Claude

En `.claude/skills/` están las 11 skills de [youtube-agent-skill](https://github.com/Jakeschincariol/youtube-agent-skill) (licencia MIT). Funcionan solas al abrir Claude Code en esta carpeta, en tu PC o en la nube:

| Orden | Para qué |
|---|---|
| `/yt-package` | Título y texto de miniatura, revisados juntos |
| `/yt-seo` | Descripción y etiquetas |
| `/yt-chapters` | Capítulos a partir del `.srt` que genera el doblaje |
| `/yt-shorts` | Shorts que se pueden sacar del vídeo largo |
| `/yt-script` | Guion con gancho puntuado |
| `/yt-edit`, `/yt-retention`, `/yt-comment`, `/yt-plan`, `/yt-viral`, `/yt-audit` | Edición, retención, comentarios, planificación, tendencias y auditoría del canal |

Las skills leen tu perfil de voz en `~/.claude/youtube/voice.md`. Hay una plantilla en `templates/youtube-voice.md`.

Ejemplo con un vídeo doblado: `python3 .claude/skills/yt-chapters/chapters.py /mnt/c/videos/clip_es.srt`
