---
name: miniatura
description: Crea la miniatura de YouTube de una historia de mangavid - propone el texto y la escena a partir del guion, genera opciones con los personajes de la historia y recomienda una. Úsala cuando el usuario pida una miniatura, portada o thumbnail de un capítulo o historia.
---

# Miniatura de un capítulo de mangavid

El usuario habla español y quiere aprobar cada paso: **para siempre en los puntos marcados con ⏸**.
Todos los comandos, desde `~/doblaje` y con `HF_HUB_OFFLINE=1`. Las fichas de personaje tienen que
estar elegidas (`python -m mangavid personajes`); si faltan, díselo y para.

## 1. Leer el guion y proponer ⏸

Lee la historia entera y busca **el momento que hace clic**: la traición, la revelación, el giro,
la emoción más fuerte. No el principio ni un plano bonito sin tensión.

Propón **tres** opciones. Cada una tiene:
- **Texto:** 2-3 palabras en español, máximo 4. Tiene que abrir una pregunta, no resumir.
  Marca con `*asteriscos*` la palabra que irá en amarillo.
  Buenos: `La *traición*`, `¡Me *engañó*!`, `Volvió del *infierno*`. Malos: `Capítulo 1`, el título repetido.
- **Imagen:** etiquetas Animagine como en las escenas, con **un solo personaje** (`1girl, solo` /
  `1boy, solo`), una emoción clara en la cara y el fondo de la escena. Deja que el programa añada
  el primer plano y el contraste.

Si el usuario ya tiene título, comprueba que miniatura y título no repitan palabras:
`python3 .claude/skills/yt-package/title.py --title "<título>" --thumb "<texto>"`.

Enseña las tres opciones y espera a que elija.

## 2. Escribirla en el guion

Añade, antes de la primera escena (junto a los personajes):

```text
@miniatura: 1girl, solo, @elena[black dress], crying, angry, burning mansion, night
@miniatura_texto: La *traición*
```

## 3. Generar

```bash
HF_HUB_OFFLINE=1 venv/bin/python -m mangavid miniatura <historia.txt>
```

Genera 4 imágenes (unos 45 s en total) y les pone el texto en el lado más despejado. El resultado
queda en `<historia>_miniaturas/`: `miniatura_1.jpg` … `miniatura_4.jpg` y `opciones.jpg`, con todas.

- Solo cambiar el texto: `--texto "Otra *frase*"`. Las imágenes no se regeneran: tarda segundos.
- Forzar el lado del texto: `--lado izquierda` o `--lado derecha`.
- Usar una imagen ya generada del vídeo, sin GPU: `--escena 12` (o varias: `--escena 12 30 41`).
- Otras 4 imágenes distintas: `--seed 5000`.

## 4. Revisar y recomendar ⏸

Mira `opciones.jpg` y comprueba en cada una:
- La cara se ve grande y con la emoción pedida. Descarta caras pequeñas, de espaldas o deformes.
- El texto no tapa la cara.
- Se entiende en pequeño: imagina el tamaño del móvil.

Recomienda una y di por qué en una frase. Dile la ruta de Windows del archivo elegido
(`C:\videos\...`) y recuérdale que la miniatura de YouTube se sube a mano: tú no publicas nada.
