# «Volví diez años atrás para salvar el restaurante de mi padre» — plan y autocrítica

Duración objetivo: 80-120 min. Medido en historias anteriores: «El heredero» (10.699 palabras, 440 escenas)
duró 82 min a velocidad normal (~136 palabras/min); con `--rate +25%` la voz va a ~175 palabras/min.
Objetivo: ~15.500 palabras en ~580 escenas -> ~105 min a velocidad normal, ~90 min con +25%.

## Idea

Regresión + venganza + secreto familiar + amor, estilo del canal (Bienvenido a Destino de Millones).
Leo Ferrer, 34 años, friega platos en el hotel de lujo que Gonzalo Gálvez construyó sobre las cenizas del
restaurante de su padre. Su mejor amigo, Bruno, ahora jefe de cocina, lo humilla en una gala y le confiesa
al oído que fue él quien abrió la puerta la noche del incendio. Leo muere esa noche bajo la lluvia… y se
despierta con 24 años, treinta días antes del incendio, con su padre vivo.

## Cronología (30 días)

| Día | Hecho | Capítulo |
|---|---|---|
| — | Gala en el hotel, humillación, muerte (futuro, 10 años después) | Gancho |
| 13 feb | Despierta. Padre vivo. Bruno, Nerea, Valeria | 1 |
| 14 feb | Encuentra el préstamo: 60.000 € a Inversiones Altamira (Gálvez), vence el 15 de marzo, el local como garantía | 2 |
| 16 feb | Primer dolor en el pecho del padre (en el original lo escondió y murió meses después). Leo lo lleva a urgencias: le ponen un stent | 2 |
| 19 feb | Visita de incógnito de la crítica Elena Ríos. En el original Bruno salaba el plato y la crítica hundió el restaurante | 3 |
| 21 feb | Casting de «El Gran Fogón». Nerea deja a Leo en público por Bruno | 4 |
| 5 mar | Semifinal. Sabotaje de Bruno. Leo prepara la trampa del incendio con la inspectora Vidal | 5 |
| 12 mar | Final en directo. Bruno presenta el arroz robado de Ramón. Leo gana 100.000 € (se pagan en 48 h) | 6 |
| 14 mar | Noche del incendio: Bruno abre la puerta trasera, el Chispa entra con gasolina. Cámaras y detenciones | 7 |
| 15 mar | Gálvez llega con el notario para quedarse el local. Leo paga y Vidal detiene a Gálvez | 8 |
| +1 año | Restaurante con estrella, Valeria, la carta | 9 |

## Autocrítica de la primera versión del plan (y cómo se arregló)

Revisado con las preguntas de la skill `revisar-guion`:

1. **¿Por qué Leo no va a la policía el primer día?** No tiene pruebas: el incendio aún no ha pasado y no puede decir
   «vengo del futuro». → Arreglo: Vidal ya investiga a Gálvez por otros tres incendios de locales (Leo lo sabe porque
   en el futuro salió en las noticias cuando ya era tarde). Leo le da un dato verificable (el nombre de la empresa
   pantalla y el próximo local) y ella acepta vigilar, sin saber de dónde lo saca.
2. **Dinero.** Primera versión: Leo pagaba la deuda con reservas del restaurante. Imposible juntar 60.000 € en un mes.
   → Arreglo: el premio del concurso (100.000 €), con una regla sembrada en el capítulo 4: «se paga en 48 horas».
   La operación del padre la cubre la sanidad pública por urgencias: no aparece dinero que no exista.
3. **Motivación de Bruno.** «Envidia» no basta. → Arreglo: deudas de juego (se ven en el capítulo 1: llamadas que
   cuelga, un hombre que lo espera fuera), Gálvez le promete el puesto de jefe de cocina y le paga la deuda; y Nerea.
4. **Casualidades.** La crítica Elena Ríos aparece dos veces (cena de incógnito y jurado de la final). → Justificado:
   en el capítulo 3 ella misma dice que es jurado del programa; por eso Leo sabe que importa ganársela. Queda una sola
   casualidad real: que Bruno elija el arroz de Ramón para la final (en el futuro lo hizo, Leo lo sabe y lo espera).
5. **Si Leo sabe que Bruno es el traidor, ¿por qué no lo echa?** Porque si lo echa, Gálvez buscará otra forma de quemar
   el local y Leo ya no sabrá cuándo. Mantenerlo cerca es la única manera de saber la fecha. Se dice en el capítulo 2.
6. **Nerea.** En la primera versión desaparecía tras el capítulo 4. → Vuelve en el 9 a pedir otra oportunidad.
7. **Promesas sembradas y pagadas:**
   - La cerradura rota de la puerta trasera (cap. 1) → Bruno tiene la única copia de la llave (cap. 7).
   - El cuaderno de recetas del padre con fechas (cap. 1) → prueba en directo de que el arroz es de Ramón (cap. 6).
   - El caldo de los domingos de su madre, el olor al despertar (cap. 1) → plato de la final (cap. 6).
   - La carta de Valeria que Leo no abrió en el futuro (gancho) → se la cuenta en el epílogo (cap. 9).
   - El plato que Bruno rompe en la gala (gancho) → se invierte en la final y en el epílogo.
8. **Imágenes.** Casi todas las escenas con un solo personaje y `solo`. Las de dos personajes, sin tocarse. Nada de
   uniformes de policía (el negativo los evita): Vidal va de paisano con gabardina. El incendio no llega a ocurrir,
   así que no hay escenas de personas entre llamas. Sin letreros con texto.

## Autocrítica después de escribir

Comprobación automática del guion terminado (`mangavid.storyboard`):

- **517 escenas, 14.703 palabras**, media de 28 por escena y máximo de 44 (límite 45).
- **Duración estimada: ~112 min** a velocidad normal; **~90 min con `--rate +25%`**. Las dos dentro de 80-120.
- Los 11 personajes aparecen y tienen función: Leo 138 veces, Ramón 60, Valeria 45, Bruno 42, Vidal 30, Gálvez 24,
  Elena 20, Nerea 18, Chispa 10, Leo y Bruno del futuro solo en el gancho.
- Solo 7 escenas con dos `@personajes`, ninguna tocándose, todas con `{evitar=…}`. Las que el revisor no puede contar
  son escenas de público a propósito.

Fallos encontrados al releer y corregidos:

| Problema | Gravedad | Arreglo |
|---|---|---|
| Los intereses no cuadraban: «30 %» en un sitio y 64.500 € en otro | Se nota | La deuda es de 60.000 € en total en todo el guion |
| ¿Cómo recuerda Leo una noticia pequeña de hace diez años? | Rompe la historia | En su primera vida leyó todo sobre Gálvez cien veces cuando empezó a sospechar |
| Vidal debería sospechar de Leo si acierta un incendio | Rompe la historia | Tiene coartada: esa noche durmió en el hospital con su padre, y hay cámaras (escena cambiada) |
| El candado está fuera, pero las cámaras estaban dentro | Rompe la historia | Una cámara escondida en una maceta del callejón y otra en la cocina |
| ¿Por qué llega Gálvez tranquilo si el Chispa no le llamó? | Se nota | «Pasaba a menudo»: el Chispa desaparecía tras cada trabajo |
| El seguro: Gálvez cuenta con un local quemado «sin seguro» | Se nota | Se siembra en el cap. 6 que Leo renueva el seguro que su padre dejó caducar |
| Etiqueta de personaje rota y narración en tercera persona en una escena | Detalle | Corregido |

Casualidades: solo una real, que Bruno elija el arroz robado para la final (en el futuro lo hizo; Leo lo espera).

## Títulos (revisados con `yt-package/title.py`, sin repetir palabras con la miniatura)

- A) Murió fregando platos y despertó 10 años antes del incendio (98/100) ← recomendado
- B) Despertó 30 días antes de perderlo todo… y esta vez lo sabía (98/100)
- C) Su mejor amigo quemó el restaurante de su padre (más corto que la versión probada)

Miniatura (ya en el guion): Leo de chef, tranquilo, frente a Bruno pálido en el plató de la final.
Rótulos: `PROTA` → Leo · `TRAIDOR` → Bruno · «¡VOLVÍ AL PASADO!»
