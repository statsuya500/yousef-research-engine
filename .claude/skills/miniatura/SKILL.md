---
name: miniatura
description: Crea la miniatura de YouTube de una historia de mangavid al estilo de los canales de manhwa narrado (personajes con etiquetas PROTA/HIJA/CEO y flechas, más una frase corta) - propone imagen y textos a partir del guion, genera opciones y recomienda una. Úsala cuando el usuario pida una miniatura, portada o thumbnail de un capítulo o historia.
---

# Miniatura de un capítulo de mangavid

El estilo es el de canales como Yube Manhwa:
- Imagen luminosa y colorida con **los dos personajes clave** de la historia.
- **Etiquetas** amarillas inclinadas con flecha curva hacia cada personaje: quién es en la historia
  (`PROTA`, `HIJA`, `CEO`, `HERMANAS`, `ASESINO SECRETO DE RANGO SSS`).
- **Una frase corta** que alguien dice en el momento clave (`¡NO SALTES!`, `TE PROTEGERÉ SIEMPRE`,
  `SOLO SON HERRAMIENTAS.`) o un rótulo como `?!?` o `-80 °C`.

El usuario habla español y quiere aprobar cada paso: **para siempre en los puntos marcados con ⏸**.
Todos los comandos, desde `~/doblaje` y con `HF_HUB_OFFLINE=1`. Las fichas de personaje tienen que
estar elegidas (`python -m mangavid personajes`); si faltan, díselo y para.

## 1. Leer el guion y proponer ⏸

Lee la historia entera y busca el momento que hace clic: la traición, la revelación, el giro.
Propón **tres** opciones. Cada una tiene:
- **Imagen:** etiquetas Animagine con **1 o 2 personajes**, en el orden en que quieres que salgan
  de izquierda a derecha (el primero a la izquierda). Cada uno con su emoción y pose, y un fondo
  reconocible de la historia. Ejemplo: `1boy, 1girl, @kai, @luna, kai grabbing her arm, she is crying, rooftop, blue sky`.
- **Rótulos:** una etiqueta por personaje (su papel, en 1-3 palabras) y una frase de máximo 4
  palabras que abra una pregunta. No repitas palabras del título del vídeo.

Si el usuario ya tiene título, comprueba que título y frase no repitan palabras:
`python3 .claude/skills/yt-package/title.py --title "<título>" --thumb "<frase>"`.

## 2. Escribirla en el guion

Antes de la primera escena, junto a los personajes:

```text
@miniatura: 1boy, 1girl, @kai, @luna[school uniform], kai grabbing her arm, she is crying, rooftop, blue sky
@miniatura_texto: @kai=PROTA | @luna=HIJA | ¡No saltes!
```

Formato de los rótulos, separados por `|`:
- `@personaje=TEXTO`: etiqueta con flecha hacia ese personaje (tiene que salir en `@miniatura`).
- Texto sin `@`: frase suelta en el hueco más despejado.

## 3. Generar

```bash
HF_HUB_OFFLINE=1 venv/bin/python -m mangavid miniatura <historia.txt>
```

Genera 4 imágenes (unos 45 s) y les pone los rótulos. Las flechas buscan las cabezas con el
detector de `imgutils`. El resultado queda en `<historia>_miniaturas/`: `miniatura_1.jpg` …
`miniatura_4.jpg` y `opciones.jpg`, con todas juntas.

- Solo cambiar los rótulos: `--texto "@kai=PROTA | ?!?"`. No regenera las imágenes: tarda segundos.
- Usar una imagen ya generada del vídeo, sin GPU: `--escena 12` (o varias: `--escena 12 30 41`).
- Otras 4 imágenes distintas: `--seed 5000`.
- Una imagen hecha por el usuario (Fooocus, ChatGPT…): `--imagen mia.png --texto "@a=PROTA | @b=TÍO | ¿…?"`.
  Las etiquetas `@` van en orden de izquierda a derecha, según dónde estén los personajes en su imagen.

## 4. Revisar y recomendar ⏸

Mira `opciones.jpg` y comprueba en cada una:
- Las caras se ven y tienen la emoción pedida. Descarta personajes duplicados o deformes.
- Cada flecha apunta al personaje correcto y ningún rótulo tapa una cara.
- Se entiende en pequeño: imagina el tamaño del móvil.

Recomienda una y di por qué en una frase. Dile la ruta de Windows del archivo elegido
(`C:\videos\...`) y recuérdale que la miniatura se sube a mano en YouTube Studio: tú no publicas nada.
