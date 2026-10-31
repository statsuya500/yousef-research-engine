# «A los 18 llamé a la puerta de mis padres» con los scripts locales

Mismo flujo y mismo estilo que «El pastor» y «Mis hijos me eligieron». Todo se ejecuta desde `~/doblaje`.
Los resultados van a `C:\videos\puerta`.

```bash
cd ~/doblaje && git checkout main && git pull
source venv/bin/activate
export PYTHONPATH=$PWD HF_HUB_OFFLINE=1
mkdir -p /mnt/c/videos/puerta
cp historias/puerta/historia_local.txt /mnt/c/videos/puerta/historia.txt
```

| Paso | Comando | Qué hace |
|---|---|---|
| 1 | `python doblaje_scripts/puerta_duraciones.py` | Voz de las 373 escenas y `trabajo/duraciones.json` (~84 min) |
| 2 | `python doblaje_scripts/puerta_calibrar.py` | 6 imágenes de prueba por personaje y ropa, y paisajes clave, en `calibracion/`. **Míralas**: si un personaje sale mal, cambia su ficha en `puerta_comun.py` |
| 3 | `python doblaje_scripts/puerta_filtro.py calibrar` | Dice qué pruebas no pasan el filtro (pelo, ropa, caras) |
| 4 | `python doblaje_scripts/puerta_generar.py` | ~1.780 imágenes en 329 grupos (personaje, ropa, lugar y tono), en `planos/`. Reanudable |
| 5 | `python doblaje_scripts/puerta_filtro.py` | Filtra las imágenes (`planos/filtro.json`) |
| 6 | `python doblaje_scripts/puerta_montar.py` | Reparte las imágenes buenas en las 1.006 posiciones (`escenas/`), con viñetas dobles para las escenas de dos personajes |
| 7 | `python doblaje_scripts/render_sistema.py /mnt/c/videos/puerta /mnt/c/videos/puerta/a_los_18.mp4 /mnt/c/videos/puerta/trabajo/tramos` | Vídeo final con voz y subtítulos |

Miniatura: como en las otras historias, con `miniatura_paneles.py` o `python -m mangavid miniatura`.

## Qué hay

- `historias/puerta/historia_local.txt`: el guion en formato local (`[NNN] @personajes, lugar, tono`). Se genera con
  `puerta_convertir.py` a partir de `historias/puerta/historia.txt`; si cambias el guion largo, vuelve a convertirlo.
- `puerta_comun.py`: estilo, fichas (9 personajes y 4 secundarios: guardia, director, policía y Darío de niño), ropa por
  fases, 29 lugares y negativos.
- `puerta_plan.py`: una imagen cada ~5 s, como en «Mis hijos». Las escenas sin personajes (público o paisaje) llevan solo
  planos de escenario. Darío cambia de ropa por fases: sudadera → botones (escena 69) → chófer (178) → traje (339), y
  lleva mono en el taller.
- `puerta_generar.py`, `puerta_filtro.py`, `puerta_montar.py`: copias de las del pastor con las rutas, los lugares y las
  reglas de pelo y ropa de esta historia.

Probado en la nube sin GPU: el guion convertido se lee bien, el plan sale con 1.006 posiciones y la generación prepara
1.777 trabajos en 329 grupos. No se han generado imágenes: eso se hace en el PC.
