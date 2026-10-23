---
name: montar-capitulo
description: Flujo completo para convertir un guion de mangavid en vídeo, con paradas para que el usuario apruebe cada paso. Úsala cuando el usuario pida generar, montar o producir un capítulo o historia.
---

# Montar un capítulo de mangavid

El usuario habla español y quiere aprobar cada paso: **para siempre en los puntos marcados con ⏸**
y no sigas sin su visto bueno. Si dice «stop», detén el proceso en segundo plano (TaskStop)
y comprueba con `pgrep -af mangavid` que no queda nada corriendo.

Todos los comandos, desde `~/doblaje` y con `HF_HUB_OFFLINE=1` (los modelos ya están descargados).
Los procesos largos, en segundo plano.

1. **Revisar el guion** con la skill `revisar-guion`. ⏸ Enseña los problemas y espera.
2. **Retratos:** `venv/bin/python -m mangavid personajes <historia.txt>`
   Genera 4 opciones por personaje (los derivados, como `@alex5`, parten del retrato elegido de su base).
   Haz una hoja con las opciones (ffmpeg tile) y míralas: descarta las que no cuadren
   (sexo, edad, rasgos de la ficha). ⏸ Recomienda una por personaje y espera la elección.
   Aplica con `venv/bin/python -m mangavid elegir <historia.txt> <personaje> <n>`.
3. **Escenas:** `venv/bin/python -m mangavid run <historia.txt> --only-images` (~11 s por imagen).
4. **Revisar imágenes** con la skill `revisar-imagenes` y arregla lo que falle. ⏸ Enseña el resultado y espera.
5. **Vídeo:** `venv/bin/python -m mangavid run <historia.txt>` (voz, movimiento, subtítulos de 2 líneas).
   Opciones: `--music musica.mp3`, `--voice es-MX-JorgeNeural`, `--rate +5%`.
6. **Comprobar:** saca 2-3 fotogramas con ffmpeg y míralos (subtítulos legibles, imagen correcta).
   Dile al usuario la ruta de Windows del vídeo (`C:\videos\...`) y la duración.
7. **Miniatura** con la skill `miniatura`. ⏸ Enseña las opciones y espera.

Notas del equipo del usuario (8 GB de RAM, RTX 5060 Ti de 8 GB): no lances dos generaciones a la vez
ni otro proceso pesado mientras se generan imágenes; Windows se queda sin memoria.
