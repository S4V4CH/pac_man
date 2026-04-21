# Uso de la librería PRNG (`lib/aleatorio.py`) en el proyecto

Para una versión **menos técnica**, con lenguaje de exposición y rangos de línea por sección, ver `LIBRERIA-PRNG-EXPLICACION-SENCILLA.md` en esta misma carpeta.

Este documento enumera **dónde** se instancia y **cómo** se usa `GeneradorAleatorio` en el código, con **rutas de archivo**, **explicación** y **extractos** del código fuente.

**Idea clave:** existe **una sola instancia** de generador por partida (`Juego.gen` en `src/main.py`), creada con la **semilla de partida** y `metodo='comb'`. Esa misma referencia se pasa a mapas, loot, mejoras y fantasmas. Cada llamada a `decimal`, `entero`, `booleano`, `elegir` o `mezclar` **avanza la secuencia** pseudoaleatoria: por eso dos partidas con la misma semilla obtienen el mismo mapa y el mismo comportamiento (salvo que se introduzcan otras fuentes de aleatoriedad externas al `gen`, p. ej. tiempo real para la semilla).

---

## 1. Definición y exportación de la librería

### 1.1 Implementación — `lib/aleatorio.py`

Aquí vive la clase `GeneradorAleatorio` y los métodos internos (`congruencial`, `midsquare`, `combinado`) más la API del juego (`entero`, `decimal`, `booleano`, `elegir`, `mezclar`, `restablecer`, historial para estadísticas).

El bloque `if __name__ == '__main__'` permite **demostración en consola** (útil para vídeos de evidencia académica); no forma parte del bucle del juego, pero **sí ejecuta** la misma librería.

```32:47:lib/aleatorio.py
class GeneradorAleatorio:
    """
    Generador de números pseudoaleatorios con tres métodos intercambiables.
    ...
    metodo : str
        Algoritmo activo: 'lcg' | 'mid' | 'comb'
```

```187:206:lib/aleatorio.py
    def _siguiente(self) -> float:
        """Delega al método activo."""
        return {
            'lcg':  self.congruencial,
            'mid':  self.midsquare,
            'comb': self.combinado,
        }[self.metodo]()

    def entero(self, min_val: int, max_val: int) -> int:
        ...
        rango = max_val - min_val + 1
        return min_val + int(self._siguiente() * rango)
```

### 1.2 Paquete — `lib/__init__.py`

Reexporta la clase para poder hacer `from lib import GeneradorAleatorio`.

```1:4:lib/__init__.py
from .aleatorio import GeneradorAleatorio

__all__ = ['GeneradorAleatorio']
__version__ = '1.0.0'
```

---

## 2. Punto central: creación del generador y reparto a subsistemas — `src/main.py`

### 2.1 Importación

```7:7:src/main.py
from lib import GeneradorAleatorio
```

### 2.2 Inicio de partida: semilla, método `comb`, subsistemas

En `_iniciar_partida` se fija `self.semilla_partida`, se construye **`GeneradorAleatorio(..., metodo='comb')`** (generador combinado, recomendado en la documentación de la librería para mapas), y **el mismo objeto** alimenta:

- `SistemaLoot(self.gen)` — loot por probabilidades.
- `GeneradorMapa(self.gen)` — laberinto procedural.
- `self.gen.entero(...)` — umbral del evento “laberinto inestable”.
- `SistemaMejoras(self.gen)` — baraja de cartas de mejoras (vía `entero` internamente).

```922:956:src/main.py
        self.semilla_partida = semilla
        self.gen = GeneradorAleatorio(semilla=semilla, metodo='comb')
        self.sistema_loot = SistemaLoot(self.gen)
        self.mapeador = GeneradorMapa(self.gen)
        self.tablero = self.mapeador.generar(filas=19, columnas=23, cobertura=0.60)

        min_p = int(self.tablero.total_puntos * 0.15)
        max_p = int(self.tablero.total_puntos * 0.60)
        self.umbral_division = self.gen.entero(min_p, max_p)
        ...
        if not conservar_nivel or self.sistema_mejoras is None:
            self.sistema_mejoras = SistemaMejoras(self.gen)
            ...
        else:
            # Mantener las mejoras entre niveles: solo actualizar el gen (para reproducibilidad)
            self.sistema_mejoras.gen = self.gen
```

**Qué hace cada uso:**

| Llamada | Rol |
|--------|-----|
| `GeneradorMapa(self.gen)` + `generar(...)` | Durante la generación del mapa se consumen muchos valores: dirección del excavador, apertura de ciclos, orden de callejones para super pastillas, etc. |
| `self.gen.entero(min_p, max_p)` | Elige un **entero aleatorio** entre límites derivados del total de puntos del tablero. Ese valor es `umbral_division`: al comer suficientes puntos se dispara el evento roguelike de “división” (más abajo). |

### 2.3 Reparto del `gen` a los fantasmas

Cada fantasma que necesita decisiones aleatorias recibe la referencia `self.gen` en el constructor:

```968:975:src/main.py
        for i, tipo in enumerate(tipos):
            sf, sc = spawn_pts[min(i, len(spawn_pts) - 1)]
            if tipo == 'blanco':
                self.fantasmas.append(FantasmaBlanco(sf, sc, sf, sc, self.gen))
            elif tipo == 'perseguidor':
                self.fantasmas.append(FantasmaPerseguidor(sf, sc, sf, sc, self.gen))
            else:
                self.fantasmas.append(FantasmaAleatorio(sf, sc, sf, sc, self.gen))
```

**Efecto:** movimientos que usan `elegir` en `fantasma.py` comparten la **misma secuencia global** que el mapa y el loot, en **orden de ejecución** del juego. Por eso el diseño debe tener cuidado con el orden de llamadas si se busca reproducibilidad estricta.

### 2.4 Fiebre del Oro: posiciones iniciales aleatorias

`_spawnear_fiebre_del_oro` usa **`elegir`** sobre la lista de celdas pasillo para colocar cada uno de los 15 fantasmas dorados:

```505:507:src/main.py
        for _ in range(15):
            pf, pc = self.gen.elegir(pasillos)
            fantasma_fiebre = FantasmaAleatorio(pf, pc, pf, pc, self.gen, color=(255, 180, 0))
```

`elegir` en la librería internamente usa `entero(0, len-1)`; cada iteración consume al menos un valor uniforme.

### 2.5 Evento “laberinto inestable”: un fantasma más

`_aplicar_evento_division_roguelike` añade otro `FantasmaAleatorio` pasándole `self.gen`:

```885:886:src/main.py
        self.fantasmas.append(
            FantasmaAleatorio(bf, bc, bf, bc, self.gen, color=(198, 42, 42))
```

---

## 3. Generación procedural del mapa — `src/mundo/generador_mapa.py`

La clase `GeneradorMapa` guarda `self.gen` y lo usa en tres momentos importantes.

### 3.1 Importación y constructor

```4:22:src/mundo/generador_mapa.py
from lib import GeneradorAleatorio
...
    def __init__(self, gen: GeneradorAleatorio):
        self.gen = gen
```

### 3.2 Crear ciclos en el laberinto — `booleano`

Tras la excavación, se recorren posibles muros entre dos pasillos; con probabilidad fija (`0.35` en la llamada desde `generar`) se **tiran dados** para abrir el muro y crear un ciclo:

```54:60:src/mundo/generador_mapa.py
                    if tablero.es_pasillo(f, c-1) and tablero.es_pasillo(f, c+1):
                        if self.gen.booleano(probabilidad):
                            tablero.establecer(f, c, PASILLO)
                    ...
                    elif tablero.es_pasillo(f-1, c) and tablero.es_pasillo(f+1, c):
                        if self.gen.booleano(probabilidad):
                            tablero.establecer(f, c, PASILLO)
```

Cada `booleano(p)` compara un `u ∈ [0,1)` de `_siguiente()` contra `p`.

### 3.3 Excavación (random walk) — `entero`

El excavador elige una de cuatro direcciones con **`entero(0, 3)`**:

```81:84:src/mundo/generador_mapa.py
        while celdas_abiertas < objetivo and intentos < intentos_maximos:
            # Elegir dirección aleatoria con la librería PRNG
            idx = self.gen.entero(0, 3)
            df, dc = DIRECCIONES[idx]
```

Esto se ejecuta muchas veces hasta aproximar la **cobertura** deseada; es la principal fuente de consumo de aleatoriedad en la forma del mapa.

### 3.4 Super pastillas en callejones — `mezclar`

Se listan celdas `PUNTO` con un solo vecino pasillo (callejones), luego se **barajan** con Fisher–Yates interno de la librería:

```134:137:src/mundo/generador_mapa.py
        # Mezclar callejones y tomar los primeros 4 usando la librería PRNG
        callejones_mezclados = self.gen.mezclar(callejones)
        for f, c in callejones_mezclados[:4]:
            tablero.establecer(f, c, SUPER_PUNTO)
```

**Por qué importa:** el orden de los callejones determina **qué** cuatro reciben super pastilla si hay más de cuatro candidatos; con la misma semilla, el orden es reproducible.

---

## 4. Botín al terminar nivel — `src/sistemas/loot.py`

`SistemaLoot` recibe `GeneradorAleatorio` y, en `tirar_loot`, encadena **varias** pruebas **`booleano`** con probabilidades distintas (orden: legendario → raro → vida → común):

```36:52:src/sistemas/loot.py
class SistemaLoot:
    def __init__(self, gen: GeneradorAleatorio):
        self.gen = gen

    def tirar_loot(self) -> dict | None:
        ...
        if self.gen.booleano(ITEMS['legendario']['prob']):
            return {**ITEMS['legendario'], 'id': 'legendario'}
        if self.gen.booleano(ITEMS['raro']['prob']):
            return {**ITEMS['raro'], 'id': 'raro'}
        if self.gen.booleano(ITEMS['vida']['prob']):
            return {**ITEMS['vida'], 'id': 'vida'}
        if self.gen.booleano(ITEMS['comun']['prob']):
            return {**ITEMS['comun'], 'id': 'comun'}
        return None
```

**Nota de integración:** la instancia se crea en `_iniciar_partida` junto con el resto de sistemas; cuando el flujo del juego llame a `tirar_loot()`, cada `booleano` consumirá valores del **mismo** `gen` en el orden en que se ejecuten las comprobaciones. Si en tu rama `tirar_loot` aún no se invoca desde `main` o la UI, la lógica sigue siendo la referencia oficial de cómo se aplicaría la PRNG al botín.

---

## 5. Selección de mejoras roguelike — `src/sistemas/mejoras.py`

Cuando hay **más de tres** mejoras disponibles, se hace un **barajado Fisher–Yates** manual usando `self.gen.entero(0, i)` (equivalente en espíritu a `mezclar` del catálogo de índices):

```207:217:src/sistemas/mejoras.py
    def obtener_opciones(self) -> list[dict]:
        """Genera hasta 3 mejoras aleatorias disponibles para ofrecer."""
        disponibles = [m for m in CATALOGO_MEJORAS if self.puede_subir(m['id'])]
        if len(disponibles) <= 3:
            return list(disponibles)
        # Mezclar usando el PRNG del juego para reproducibilidad
        idx = list(range(len(disponibles)))
        for i in range(len(idx) - 1, 0, -1):
            j = self.gen.entero(0, i)
            idx[i], idx[j] = idx[j], idx[i]
        return [disponibles[i] for i in idx[:3]]
```

Cada intercambio consume un entero uniforme; las tres cartas mostradas dependen de esa secuencia.

---

## 6. Inteligencia artificial de fantasmas — `src/entidades/fantasma.py`

Los subtipos que incorporan azar guardan `self.gen` y llaman a **`elegir`** sobre listas de direcciones `(df, dc)` cuando hay varias opciones válidas (empates, modo caótico, emboscador “tímido”, etc.).

### 6.1 `FantasmaAleatorio`

- Empate al huir en fiebre del oro: `elegir(mejores)`.
- Movimiento aleatorio habitual: `elegir(opciones)`.

```318:325:src/entidades/fantasma.py
            self.dir_fila, self.dir_col = self.gen.elegir(mejores)
            ...
        self.dir_fila, self.dir_col = self.gen.elegir(opciones)
```

### 6.2 `FantasmaPerseguidor`

- En modo caótico o asustado, o sin Pac-Man: elige dirección al azar entre las legales.
- Si BFS no devuelve ruta hacia el punto de emboscaje: `elegir(opciones)`.

```360:375:src/entidades/fantasma.py
        if self.modo_actual == MODO_CAOTICO or self.estado_especial == MODO_ASUSTADO or not pacman:
            self.dir_fila, self.dir_col = self.gen.elegir(opciones)
        else:
            ...
            if self._ruta: self.dir_fila, self.dir_col = self._ruta.pop(0)
            else: self.dir_fila, self.dir_col = self.gen.elegir(opciones)
```

### 6.3 `FantasmaEmboscador` (y `FantasmaBlanco`, que hereda el comportamiento)

- Modo caótico / asustado / sin jugador: `elegir(opciones)`.
- Si no hay ruta BFS al punto de emboscaje: `elegir(opciones)`.
- Cerca del jugador (comportamiento “tímido”): `elegir(opciones)`.

```428:446:src/entidades/fantasma.py
        if self.modo_actual == MODO_CAOTICO or self.estado_especial == MODO_ASUSTADO or not pacman:
            ...
            self.dir_fila, self.dir_col = self.gen.elegir(opciones)
        else:
            ...
                else:
                    self.dir_fila, self.dir_col = self.gen.elegir(opciones)
            else:
                ...
                self.dir_fila, self.dir_col = self.gen.elegir(opciones)
```

**Resumen:** `elegir` traduce la aleatoriedad uniforme en **decisiones discretas** (qué flecha tomar), lo que diferencia el comportamiento “aleatorio” del puramente determinista cuando hay empatés o rutas vacías.

---

## 7. Pruebas y demostración fuera del juego

### 7.1 Prueba Monte Carlo — `pruebas/test_montecarlo.py`

Script de evidencia estadística: instancia `GeneradorAleatorio(semilla=..., metodo=...)` y usa **`decimal(0, 1)`** en bucle para puntos 2D y estimación de π.

```25:33:pruebas/test_montecarlo.py
def test_montecarlo(semilla: int = 42, n: int = 10_000, metodo: str = 'comb') -> None:
    gen = GeneradorAleatorio(semilla=semilla, metodo=metodo)
    gen.activar_historial()
    ...
        x = gen.decimal(0, 1)
        y = gen.decimal(0, 1)
```

### 7.2 Ejecución directa de la librería — `lib/aleatorio.py` (`__main__`)

Al ejecutar `python lib/aleatorio.py` se imprimen secuencias de prueba para los tres métodos y utilidades; es independiente de Pygame.

---

## 8. Tabla resumen por archivo

| Ruta | Métodos PRNG usados | Función |
|------|---------------------|---------|
| `lib/aleatorio.py` | (definición) `_siguiente`, `entero`, `decimal`, `booleano`, `elegir`, `mezclar`, … | Implementación y demo en `__main__` |
| `lib/__init__.py` | — | Exporta `GeneradorAleatorio` |
| `src/main.py` | Construcción, `entero`, `elegir` | Semilla, umbral división, loot/map/mejoras, spawns, fiebre del oro |
| `src/mundo/generador_mapa.py` | `booleano`, `entero`, `mezclar` | Ciclos, excavación, super pastillas |
| `src/sistemas/loot.py` | `booleano` | Cadena de rarezas del botín |
| `src/sistemas/mejoras.py` | `entero` | Fisher–Yates para 3 cartas |
| `src/entidades/fantasma.py` | `elegir` | Decisiones de dirección en IA |
| `pruebas/test_montecarlo.py` | `decimal`, `activar_historial`, `estadisticas` | Prueba Monte Carlo |

---

## 9. Orden de consumo y reproducibilidad

Para una misma **semilla** y el mismo **orden de llamadas** al `gen` (misma versión del código), el resultado debe coincidir. Si se añaden llamadas nuevas al PRNG **antes** en el frame o al cargar el nivel, la secuencia “se desplaza” y el mapa o las decisiones posteriores pueden cambiar aunque la semilla sea igual. Por eso conviene:

- Mantener **una** instancia compartida por partida (como ya hace `main.py`).
- Evitar mezclar `random` del módulo estándar con la lógica que debe depender de la semilla.

---

*Documento generado para describir la integración de `lib/aleatorio.py` en el repositorio Pac-Man Roguelike.*
