# Audio sample sources & attribution

Recordings used for the item 8 analysis (`report/figuras/*.png`), used to
reproduce the report's figures via `scripts/generate_animal_figures.py`.
Kept in this repo (an exception to the general `audio_samples/` gitignore
rule) because they are small and either freely licensed or synthesized
in-house.

## Animales

| Categoría | Archivo | Fuente | Autor | Licencia |
|---|---|---|---|---|
| Gato | `gato/gato.ogg` | [Meow domestic cat.ogg](https://commons.wikimedia.org/wiki/File:Meow_domestic_cat.ogg) | Smser | GFDL |
| Perro | `perro/perro.ogg` | [Barking of a dog.ogg](https://commons.wikimedia.org/wiki/File:Barking_of_a_dog.ogg) | Amada44 | CC BY-SA 3.0 |
| Gallo | `gallo/gallo.ogg` | [Rooster crowing.ogg](https://commons.wikimedia.org/wiki/File:Rooster_crowing.ogg) | Wikimedia Commons contributor | CC BY-SA 4.0 |

## Instrumentos

| Categoría | Archivo | Fuente | Licencia | Nota |
|---|---|---|---|---|
| Contrabajo | `contrabajo/contrabajo.oga` | [Jazz walking bass on double bass.oga](https://commons.wikimedia.org/wiki/File:Jazz_walking_bass_on_double_bass.oga) | CC BY 2.5 | El instrumento entra ~2.5 s dentro de la ventana de 3 s analizada; el resto es silencio de estudio. |
| Piano | `piano/piano.ogg` | [Piano.ogg](https://commons.wikimedia.org/wiki/File:Piano.ogg) | CC BY-SA 3.0 | Frase corta de varias notas, no una nota sostenida única. |
| Flauta | `flauta/flauta.ogg` | [Bach - Flute Sonata Amaj - 2. Largo e Dolce.ogg](https://commons.wikimedia.org/wiki/File:Bach_-_Flute_Sonata_Amaj_-_2._Largo_e_Dolce.ogg) | Public domain | Solo se usan sus primeros 3 s (introducción de clavecín + entrada de la flauta ~1 s). |

## Voces

| Categoría | Archivo | Fuente | Nota |
|---|---|---|---|
| Persona 1 | `persona1/persona1.wav` | Sintetizada localmente con Windows SAPI (`Microsoft David Desktop`, voz masculina en-US) | **No es una grabación humana real.** Generada con `System.Speech.Synthesis` leyendo la frase del informe; el motor es en inglés, por lo que pronuncia el texto en español con fonética inglesa. Usada como sustituto reproducible mientras no se cuente con grabaciones humanas reales. |
| Persona 2 | `persona2/persona2.wav` | Sintetizada localmente con Windows SAPI (`Microsoft Zira Desktop`, voz femenina en-US) | Igual que Persona 1, con la otra voz instalada del sistema. |

Frase sintetizada: *"Hoy estamos analizando senales de voz mediante la transformada de Fourier."* (sin tildes, por compatibilidad con el motor SAPI).
