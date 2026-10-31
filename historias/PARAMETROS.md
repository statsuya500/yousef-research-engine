# Parámetros para una historia del canal

Fuentes:
- **Tus 3 vídeos publicados.** La muestra es muy pequeña (10-30 visualizaciones), así que son pistas, no leyes.
- **Medidas del vídeo de referencia de Yube Manhwa** (K0TpgpVEMd4, primeros 10 min), tomadas por tu sesión local el 24/10.
- **Las reglas de `revisar-guion`** y las de `yt-package` para títulos.

## 1. Lo que dicen tus vídeos

| Vídeo | Duración | Visualizaciones | Engaged | Rendimiento |
|---|---|---|---|---|
| Mi hermano me empujó desde la azotea… y desperté para vengarme de todos | 1:21:48 | 30 | 15 (50 %) | **7,2x** |
| Me despidieron con 11 euros… y esa noche desperté un sistema de cocina legendario | 1:18:11 | 10 | 3 (30 %) | 1,2x |
| Mi marido defendió a su exmujer y me echó de casa… pero sus 2 hijos me eligieron a mí | 1:19:32 | 11 | 5 (45 %) | — (1 día) |

Lo que tienen en común: los tres usan la estructura `[agravio concreto en primera persona]… [giro o promesa]`.

Lo que diferencia al que funciona:
- **La traición viene de la familia**, de alguien que debería protegerte.
- **El agravio es físico y visual:** «me empujó desde la azotea». Se imagina en un segundo.
- **La promesa es de venganza contra todos.** El espectador sabe que habrá muchas escenas de vuelta de tortilla.
- **Cero fantasía en el agravio.** El «sistema de cocina» (fantasía) funcionó peor que la traición realista.

## 2. Parámetros del canal de referencia (medidos)

| Parámetro | Valor | Cómo aplicarlo en mangavid |
|---|---|---|
| Cambio de imagen | cada ~2,4 s | `@planos: 4` y escenas de 2-3 frases |
| Velocidad de voz | ~197 palabras/min | `--rate +25%` |
| Color | saturación 21/100, brillo 60/100, contraste 24/100: suave y luminoso | estilo «cine anime» con WAI |
| Planos | muchos de dos personajes (uno de espaldas o por encima del hombro) | `{evitar=…}` y personajes sin tocarse |
| Vestuario | cada personaje con la misma ropa siempre | ropa en la primera aparición; se mantiene sola |

## 3. Estructura que funciona (80 min)

| Minuto | Qué pasa |
|---|---|
| 0:00-0:30 | **Gancho:** la peor humillación de la historia, en presente, con público mirando |
| 0:30-2:00 | Quién eres y qué te han quitado. Una pregunta abierta: ¿por qué? |
| cada 8-10 min | Una humillación nueva **o** una vuelta de tortilla, con comentarios de la gente que mira |
| 40-50 | El giro: un secreto que cambia quién es el villano |
| 65-75 | La gran vuelta de tortilla pública: el villano cae delante de los mismos que se rieron |
| 75-80 | Cierre emocional y pregunta a los comentarios |

Ritmo de texto: 1-3 frases por escena, nunca más de 45 palabras. Narración en «tú» y diálogos entre «».

## 4. Título

- **Fórmula:** `[agravio familiar concreto]… y [giro o promesa de venganza]`, en primera persona.
- **Largo:** tus títulos tienen 70-85 caracteres. En móvil se cortan hacia los 40, así que **lo esencial tiene que ir en
  las primeras 6-7 palabras**.
- **Miniatura:** no repite palabras del título (`title.py`). Etiquetas con flecha (`PROTA`, `MADRE`…) y una frase de 2-3 palabras.

## 5. Lo que no repetir

- Renacer o volver al pasado (ya está «Mi hermano me empujó»).
- Cocina o sistemas de videojuego (ya está «11 euros»).
- Madrastra o niños que eligen (ya está «Mi marido…»).
