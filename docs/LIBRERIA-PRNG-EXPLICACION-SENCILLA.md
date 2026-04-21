# La “suerte” del juego, explicada sin tecnicismos

Este texto cuenta **qué hace** la librería de números aleatorios en el proyecto y **dónde** está en el código. Está pensado para que lo entienda alguien que no programa: basta con saber que el juego es un archivo que sigue instrucciones paso a paso.

Si quieres el detalle técnico (nombres de métodos, tablas, citas largas), está en `docs/LIBRERIA-PRNG-USOS-Y-CODIGO.md`.

---

## La idea en una frase

Imagina un **dado muy largo**: el programa va pidiendo “el siguiente número” una y otra vez. Esa **secuencia** decide qué forma tiene el laberinto, qué fantasma gira a la izquierda o a la derecha cuando hay empate, y otras cosas parecidas.

Lo importante: si dos personas escriben **el mismo número de semilla** en el menú, el juego intenta que les salga **la misma** secuencia de decisiones (mismo mapa, misma lógica de azar). Ese número es como la **receta** de la partida.

---

## 1. El corazón: la clase que genera los números

**Archivo:** `lib/aleatorio.py`  

**Líneas aproximadas:** **32–47** (presentación de la clase y qué significa la semilla y el método).

Ahí se define `GeneradorAleatorio`: es el objeto que “sigue sacando números” según una semilla y un modo de trabajo (`lcg`, `mid` o `comb`). El juego usa sobre todo el modo **combinado** (`comb`) al empezar una partida.

**Líneas aproximadas:** **187–253** (lo que el resto del programa llama de verdad).

En ese bloque está la lógica que traduce números entre 0 y 1 en cosas entendibles para el juego:

- un **entero** entre dos límites (como elegir una dirección entre cuatro);
- un **decimal** entre dos valores;
- un **sí o no** con una probabilidad (como “¿sale premio raro?”);
- **elegir** algo de una lista (como una casilla entre muchas);
- **mezclar** una lista (como barajar cartas).

Cada vez que el programa usa una de esas funciones, **gasta** el siguiente número de la secuencia, en orden.

---

## 2. Cómo el resto del programa “ve” esa clase

**Archivo:** `lib/__init__.py`  
**Líneas:** **1–4**

Aquí solo se dice: “cuando alguien importe `lib`, que pueda usar `GeneradorAleatorio`”. Es el puente corto entre la carpeta y el resto del juego.

**Archivo:** `src/main.py`  
**Línea:** **7**

Ahí el juego principal **trae** la clase para poder crear el generador al arrancar una partida.

---

## 3. Al empezar la partida: un solo generador para todo

**Archivo:** `src/main.py`  
**Función:** `_iniciar_partida`  
**Líneas:** **906–999** (toda la función; lo más importante está hacia el medio).

En pocas palabras, este trozo hace lo siguiente:

- **Elige la semilla** (la que escribes o una basada en la hora).  
  Líneas **923–931** aproximadamente.
- **Crea** el `GeneradorAleatorio` con método `comb`.  
  Líneas **931–932**.
- **Conecta** ese mismo generador al sistema de botín, al creador de mapas y al de mejoras.  
  Líneas **932–934** y **958–964**.
- **Pide un número entero** para decidir cuántos puntos hay que comer antes de un evento especial del laberinto (“cuánto hay que llenar el medidor”).  
  Líneas **936–938**.
- **Crea los fantasmas** y le pasa a cada uno **la misma referencia** al generador, para que cuando un fantasma “tire un dado mental”, use la misma secuencia que el mapa.  
  Líneas **976–983**.

Si lees solo un fragmento para explicar el juego en voz alta, que **931–938** y **976–983** son los más claros.

---

## 4. El mapa: abrir pasillos, barajar y poner las pastillas grandes

**Archivo:** `src/mundo/generador_mapa.py`

| Qué cuenta en lenguaje cotidiano | Dónde está en el código (líneas) |
|----------------------------------|-----------------------------------|
| El generador entra al crear el mapa | **21–22** |
| Cómo se arma el mapa por pasos (excavar, ciclos, comida, pastillas grandes) | **24–42** |
| “¿Abro este muro para hacer un atajo?” — muchas veces **sí/no** al azar | **44–61** |
| El “excavador” elige hacia dónde moverse (norte, sur, este, oeste) una y otra vez | **63–107** (la parte del azar está sobre todo en **81–84**) |
| Dónde van las **cuatro pastillas grandes**: se **barajan** los callejones y se toman los primeros cuatro | **118–137** |

La parte de **118–137** es fácil de explicar: es como mezclar un mazo de cartas que son posiciones del mapa y repartir las cuatro “grandes” a las primeras cartas.

---

## 5. El botín: varias “tiradas” seguidas

**Archivo:** `src/sistemas/loot.py`  
**Líneas:** **35–52** (el comportamiento útil está en **39–52**).

Se pregunta, en orden: ¿tocó premio muy bueno? ¿uno medio? ¿vida extra? ¿algo común? Cada pregunta es un **sí o no** con una probabilidad. No hace falta entender porcentajes: es como una ruleta que se para varias veces seguidas.

*(Nota: el sistema se crea al iniciar la partida; si en tu versión del juego aún no se llama a `tirar_loot` desde otro sitio, la lógica sigue siendo la que verías aquí cuando se conecte.)*

---

## 6. Las cartas de mejoras: barajar la lista de opciones

**Archivo:** `src/sistemas/mejoras.py`  
**Líneas:** **207–217**

Si hay muchas mejoras posibles y solo puedes mostrar tres, el programa **mezcla** mentalmente la lista usando números aleatorios (igual que barajar) y se queda con tres. Así las tres opciones cambian de partida en partida, pero de forma **repetible** si la semilla es la misma.

---

## 7. Los fantasmas: cuando hay que decidir y hay varias buenas opciones

**Archivo:** `src/entidades/fantasma.py`

Aquí el azar no “persigue” al jugador solo: ayuda a **romper empates**. Por ejemplo, si hay dos caminos igual de buenos para huir, el juego **elige uno al azar** de la lista.

| Personaje (idea) | Líneas (aprox.) | Qué se explica en una frase |
|------------------|-----------------|-----------------------------|
| Fantasma aleatorio | **287–326** | Guarda el generador (**290**); usa **elegir** para decidir dirección cuando toca ir al azar o en empates (**318**, **325**) |
| Fantasma perseguidor | **328–376** | A veces sigue un plan; cuando toca modo caótico o no hay ruta, **elegir** entre direcciones válidas (**361**, **375**) |
| Fantasma emboscador | **380–447** | Igual: en ciertos modos elige al azar entre opciones legales (**431**, **442**, **446**) |
| Fantasma blanco | **451–454** | No añade lógica nueva: **hereda** al emboscador, así que usa el mismo tipo de **elegir** |

---

## 8. Dos momentos del juego que también gastan “la suerte”

**Archivo:** `src/main.py`

| Momento | Líneas | Qué pasa en palabras simples |
|---------|--------|------------------------------|
| Fiebre del Oro (muchos fantasmas dorados) | **492–514** | Quince veces se **elige** una casilla pasillo al azar para aparecer un fantasma (**506–507**) |
| Laberinto inestable (un fantasma más) | **887–895** | Se añade un fantasma aleatorio nuevo que también recibe el generador (**893–894**) |

---

## 9. Pruebas fuera del juego (para demostraciones o clase)

**Archivo:** `pruebas/test_montecarlo.py`  
**Líneas:** **25–62** (la función que prueba miles de puntos); **64–70** (el programa que repite la prueba para tres modos).

Sirve para mostrar en consola que los números “se parecen” a tirar dados muchas veces (por ejemplo, para acercarse a ciertos valores conocidos en matemáticas).

**Archivo:** `lib/aleatorio.py`  
**Líneas:** **308–361**

Si ejecutas `python lib/aleatorio.py`, este bloque imprime ejemplos: tres estilos de generador, utilidades básicas y una demostración de que **la misma semilla repite la misma secuencia**.

---

## Tabla rápida: archivo → líneas → idea

| Archivo | Líneas (ejemplo) | Idea en una frase |
|---------|------------------|-------------------|
| `lib/aleatorio.py` | 32–47, 187–253 | Aquí vive la “máquina de números” y las funciones que usa el juego |
| `lib/__init__.py` | 1–4 | Exporta la clase para importarla fácil |
| `lib/aleatorio.py` | 308–361 | Demo en consola (no es el juego en sí) |
| `src/main.py` | 7 | Import del generador |
| `src/main.py` | 492–514 | Posiciones aleatorias para la Fiebre del Oro |
| `src/main.py` | 887–895 | Nuevo fantasma en el evento de división |
| `src/main.py` | 906–999 | Arranque de partida: semilla, un solo `gen`, reparto a sistemas y fantasmas |
| `src/mundo/generador_mapa.py` | 21–22, 44–61, 63–107, 118–137 | Mapa: ciclos al azar, excavación, pastillas grandes barajadas |
| `src/sistemas/loot.py` | 35–52 | Botín: varias preguntas sí/no seguidas |
| `src/sistemas/mejoras.py` | 207–217 | Tres mejoras al azar entre muchas |
| `src/entidades/fantasma.py` | 287–326, 328–376, 380–447 | Elegir dirección cuando hay empate o modo aleatorio |
| `pruebas/test_montecarlo.py` | 25–70 | Prueba estadística en consola |

---

*Los números de línea corresponden al estado del repositorio cuando se redactó este documento; si alguien añade código arriba, las líneas pueden desplazarse un poco.*
