# Doblaje automático de vídeos (chino → español)

Toma un vídeo en chino y genera:

- **Doblaje en español** con voz neuronal, sincronizado con cada frase del original.
- **Subtítulos en español**, quemados en el vídeo y también como archivo `.srt`.
- **Zonas tapadas**: difumina o cubre logos, marcas de agua o subtítulos incrustados.

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

## Uso por línea de comandos

```bash
pip install -r requirements.txt   # necesita también ffmpeg instalado

# Todo de una vez
python -m dubber run video.mp4 --mask "blur:20,20,220,80" --background separate

# En dos fases, revisando la traducción
python -m dubber run video.mp4 --stop-after-translate        # crea video_work/segments.json
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

Salida: `video_es.mp4` y `video_es.srt` junto al original. Los archivos intermedios quedan en `video_work/`.

## Consejos

- Si una frase doblada se pisa con la siguiente, acorta la traducción en `segments.json` o sube `--max-speed`.
- Para tapar subtítulos chinos incrustados, cubre la franja inferior con `box` o `blur`. Los subtítulos en español se dibujan encima.
- `delogo` funciona mejor con logos pequeños y fondos sencillos. Para zonas grandes usa `blur`.

## Pruebas

```bash
pip install pytest && python -m pytest -q
```
