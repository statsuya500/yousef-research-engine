---
name: crear-historia
description: Crear una historia nueva para mangavid (guion historia.txt). Úsala SIEMPRE que el usuario pida una historia, guion o capítulo nuevo. Antes de escribir nada hay que proponerle ideas y esperar su elección, porque ya tiene historias parecidas.
---

# Crear una historia nueva

El usuario habla español y **ya tiene muchas historias hechas**. No escribas ni una escena sin su visto bueno.
Para siempre en cada ⏸ y espera su respuesta.

## 1. Mirar lo que ya existe

Lee `historias/PARAMETROS.md` (qué funciona en el canal: título, gancho, ritmo, duración) y
`historias/CATALOGO.md`: lista de historias que el usuario ya tiene, con su premisa. Lee también los
`historias/*/PLAN.md` que haya. Ninguna propuesta puede repetir la premisa central de una ya hecha
(por ejemplo, otra regresión en el tiempo, otro heredero con amnesia o otro repartidor que salva a un abuelo).

## 2. Proponer ideas ⏸

Propón **5 ideas distintas entre sí**. Cada una en 3 líneas:
- **Título provisional.**
- **Premisa:** quién es el protagonista, qué le hacen y qué gira la historia.
- **Por qué es distinta** de las del catálogo.

Pregunta también la **duración** que quiere y si tiene personajes o estilo fijos. Espera a que elija una,
mezcle varias o pida otras.

## 3. Plan antes de escribir ⏸

Con la idea elegida, escribe solo `historias/<nombre>/PLAN.md`:
- Cronología.
- Personajes.
- Capítulos en una línea cada uno.
- Autocrítica con las preguntas de la skill `revisar-guion`.

Enséñale el resumen y espera su aprobación o sus cambios.

## 4. Escribir y revisar

Solo después de aprobado el plan:
1. Escribe `historia.txt` por capítulos, con el formato y el estilo del canal (ver `revisar-guion`).
2. Comprueba con `mangavid.storyboard` que se lee bien. Cuenta palabras: unas 136 palabras/min a velocidad normal
   y 172 con `--rate +25%`, más 0,5 s por escena. Ninguna escena debe pasar de 45 palabras.
3. Relee entera, corrige los huecos de trama y apúntalos en `PLAN.md`.

Al terminar, añade la historia a `historias/CATALOGO.md`.
