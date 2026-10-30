---
name: revisar-imagenes
description: Revisa las imágenes de escena generadas por mangavid (personajes duplicados, cuerpos fundidos con objetos, persona u objeto equivocado, imagen que no cuadra con la narración) y propone o aplica arreglos. Úsala cuando el usuario pida revisar, comprobar o arreglar las imágenes de una historia, o después de generar escenas con --only-images.
---

# Revisar imágenes de una historia de mangavid

El usuario habla español: todo lo que le digas, en español.

## 1. Revisión automática

```bash
cd ~/doblaje && HF_HUB_OFFLINE=1 venv/bin/python -m mangavid revisar <historia.txt>
```

Cuenta caras y cabezas en cada imagen y las compara con las personas que pide la descripción
(«1boy, 1girl» = 2, «solo» = 1, «no humans»/«no face» = 0). Deja en `<historia>_work/revision/`:
- `informe.txt`: escenas marcadas como DUPLICADO, DUDOSO o SIN CARA.
- `hoja_01.jpg`, `hoja_02.jpg`…: todas las imágenes numeradas, 8 por hoja; las marcadas llevan el estado en rojo.

Además, `revisar` comprueba la **coherencia visual** (`mangavid/coherencia.py`) y escribe
`revision/coherencia.json` (estructurado, por escena) más un resumen al final de `informe.txt`:
- Referencia: la **ficha** y la ropa vigente (la ropa sigue puesta hasta que el guion la cambie).
  Nunca la mayoría de imágenes. La aparición válida anterior solo da avisos (POSSIBLE).
- Por personaje: cara (CCIP contra la ficha y contra su aparición anterior), ojos, color, largo
  y peinado del pelo, barba, edad aparente, accesorios, prenda y color, número en la ropa.
- Niveles: `OK` (verificado), `CONFIRMED` (error seguro), `POSSIBLE` (posible error),
  `NOT CHECKABLE` (no se puede verificar; nunca se da por bueno). Cada uno con confianza y evidencia.
- El número de una camiseta sale siempre NOT CHECKABLE: el OCR necesita un modelo no descargado.
  Míralo a ojo.

Después de mirar a ojo cada imagen marcada, apruébala: `python -m mangavid aprobar <historia.txt> 003b 004`.
La aprobación vale solo para ese archivo con ese contenido: si la imagen se retoca o se regenera,
`run` la bloquea como «modificada después del informe» hasta que vuelvas a ejecutar `revisar` y aprobarla.
`run` no monta el vídeo si hay imágenes sin revisar o con fallos sin aprobar (solo con `--forzar`),
y antes de generar comprueba fichas, rostros elegidos, vestuario y miniatura (`python -m mangavid comprobar`).

DUPLICADO es casi siempre un fallo real. DUDOSO a veces es un falso positivo (un póster, un reflejo): compruébalo a ojo.

## 2. Revisión a ojo (obligatoria)

Lee TODAS las hojas con Read, no solo las marcadas: el detector no ve los fallos de abajo.
Para cada escena, compara con su descripción y narración en el guion:

| Fallo | Ejemplos reales de este proyecto |
|---|---|
| Personaje duplicado | Dos Álex en «solo»; Sara de pie y otra Sara tumbada |
| Cuerpo fundido con objetos | Julián «dentro» del motor; Álex con el motor dentro del coche |
| Persona equivocada | Una chica en lugar de Álex bajo el coche; un guardia «mayor» que sale joven |
| Género o edad que no cuadra | Julián que parece una anciana; Álex demasiado femenino |
| Objeto que no se parece | Un reloj que sale como un cuenco; un móvil flotando |
| Acción o lugar distinto a la narración | Sara no tira el anillo; el coche cae en una ciudad, no en un río |
| Época del personaje | Escenas de «5 años después» con la versión joven |

## 3. Cómo arreglar cada fallo

Cambia SOLO las escenas con fallo en el guion; el resto se reutiliza de la caché.

- **Descripción bien pero imagen mala:** añade `{semilla=1}` al final de la descripción (luego 2, 3…).
- **Duplicados en «solo»:** añade `{evitar=multiple boys, 2boys, clone, duplicate, twins, extra person, reflection}`
  (solo esa escena) y `{semilla=N}`. Si a la tercera sigue, haz un primer plano («close-up, upper body»).
  En historias nuevas, pon `@negativo_solo:` con esa lista en la cabecera y te ahorras la mayoría.
- **Clon que no se va con nada:** escribe los rasgos del personaje con palabras en lugar de `@personaje`
  (sin la cara del retrato la imagen no se duplica).
- **Documentos o grabadoras que salen como un ojo gigante:** «paper document lying on desk, top-down view,
  no humans» + `{evitar=eye, eyes, face, close-up of eye}`.
- **El detector cuenta caras que son legítimas** (gente al fondo en una plaza, una foto en la mano): no lo arregles.
- **Dos personajes que interactúan (uno tumbado, abrazos, rescates):** el IP-Adapter pone la misma cara a los dos.
  Deja solo un `@personaje` y describe al otro con palabras sin `@` (p. ej. «man lying face down, face not visible»).
- **Fundido con objetos:** separa a la persona del objeto («standing next to car with open hood») o usa un plano de manos («close-up of hands, no face»).
- **Género/edad:** añade `male focus`, `old man`, `middle-aged male…`.
- **Objetos raros:** descríbelos con detalle («round clock face, cracked glass, metal strap»).
- **Colores en accesorios** («red hair ornament») tiñen el pelo: usa otro color o quita el color.
- **Versiones adultas:** usa los personajes derivados (`@alex5`) en las escenas de después del salto temporal.

Después regenera solo las imágenes y vuelve al paso 1:

```bash
cd ~/doblaje && HF_HUB_OFFLINE=1 venv/bin/python -m mangavid run <historia.txt> --only-images
```

## 4. Qué decirle al usuario

Una tabla corta con escena, fallo y arreglo aplicado o propuesto, y qué escenas siguen mal.
No le envíes las hojas (no se pueden adjuntar en esta sesión); dile la ruta de Windows
(`C:\videos\...`). No montes el vídeo: eso lo decide el usuario.
