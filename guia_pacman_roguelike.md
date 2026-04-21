# Guía de Desarrollo: Pac-Man Roguelike
### Proyecto Académico — Ingeniería de Sistemas | Simulación
> **Stack:** Python 3.10+ · Pygame · Librería PRNG propia  
> **Objetivo:** Implementar un juego Pac-Man con generación procedural, IA avanzada y una librería de números pseudoaleatorios documentada académicamente.

---

# FASE 1 — Librería PRNG (Corazón Matemático)

> **Meta:** Tener un módulo `aleatorio.py` completamente funcional, testeado y documentado **antes** de escribir una sola línea del juego. Todo lo aleatorio del juego depende de este módulo.

---

## Paso 1.1 — Crear el archivo y la clase base

**Qué hacer:**  
Crear el archivo `lib/aleatorio.py` y definir la estructura de la clase con su constructor.

**Por qué hacerlo primero:**  
El constructor define el "estado interno" del generador. Sin estado no hay secuencia. Sin secuencia no hay aleatoriedad. Todo lo demás depende de esto.

**Código base:**
```python
class GeneradorAleatorio:
    def __init__(self, semilla: int, metodo: str = 'lcg') -> None:
        self.semilla = semilla
        self.metodo = metodo
        self._xn_lcg = semilla
        self._xn_mid = semilla % 10_000 or 1234
```

**Qué hace cada línea:**
- `self.semilla = semilla` → Guarda la semilla original para poder reiniciar el generador si se necesita reproducir la misma secuencia.
- `self.metodo = metodo` → Determina cuál de los tres algoritmos se usa cuando el juego pide un número.
- `self._xn_lcg = semilla` → Estado interno del Generador Congruencial Lineal. Este valor se actualiza con cada llamada.
- `self._xn_mid = semilla % 10_000 or 1234` → Estado interno del Midsquare. El `% 10_000` garantiza que sea de 4 dígitos. El `or 1234` evita que sea 0 (que colapsaría el algoritmo).

**Errores comunes en este paso:**
- Olvidar guardar `semilla` original (sin esto no se puede implementar `restablecer()`).
- Usar el mismo estado para LCG y Midsquare (cada algoritmo necesita su propio estado independiente).

---

## Paso 1.2 — Implementar el Método Midsquare

**Qué hacer:**  
Implementar el método `midsquare()` que extrae los dígitos centrales del cuadrado del número actual.

**Fundamento matemático:**  
Propuesto por John Von Neumann y Nicholas Metropolis en los años 40. La fórmula es:

```
X_{n+1} = k dígitos centrales de (X_n)²
u_n     = X_n / 10^k
```

**Ejemplo manual con semilla 3708 (el mismo de tu documento de clase):**
```
Paso 1: X0 = 3708
        3708² = 13.749.264
        Representación: "13749264" (8 dígitos = 2*k)
        Centro (posiciones 2 a 5): "7492"
        X1 = 7492   →   u1 = 7492/10000 = 0.7492

Paso 2: X1 = 7492
        7492² = 56.130.064
        Representación: "56130064"
        Centro: "1300"
        X2 = 1300   →   u2 = 0.1300

Paso 3: X2 = 1300
        1300² = 1.690.000
        Representación: "01690000" (se rellena con 0 a la izquierda)
        Centro: "6900"
        X3 = 6900   →   u3 = 0.6900
```

**Código:**
```python
def midsquare(self, k: int = 4) -> float:
    cuadrado = str(self._xn_mid ** 2).zfill(k * 2)
    mitad    = len(cuadrado) // 2
    inicio   = mitad - k // 2
    self._xn_mid = int(cuadrado[inicio: inicio + k])
    return self._xn_mid / (10 ** k)
```

**Qué hace cada línea:**
- `str(self._xn_mid ** 2)` → Eleva al cuadrado y convierte a string para poder extraer caracteres.
- `.zfill(k * 2)` → Rellena con ceros a la izquierda hasta tener `2k` dígitos. Crítico: sin esto, números como 1300² = 1690000 (7 dígitos) quedarían descentrados.
- `mitad = len(cuadrado) // 2` → Calcula el centro exacto del string.
- `inicio = mitad - k // 2` → Calcula desde dónde empezar a extraer para obtener exactamente k dígitos centrados.
- `int(cuadrado[inicio: inicio + k])` → Extrae la subcadena y la convierte a entero. Este es el nuevo Xn.
- `/ (10 ** k)` → Divide entre 10000 para normalizar a [0, 1).

**Debilidades documentadas (para mencionar en tu entrega):**
- Si Xn llega a 0, el generador colapsa: 0² = 0, siempre. Ejemplo: semilla 1009 → colapsa en pocos pasos.
- Ciclos cortos para ciertas semillas (periodo no garantizado).
- Por estas razones, en el juego se usa SOLO para efectos visuales menores, no para lógica crítica.

---

## Paso 1.3 — Implementar el Generador Congruencial Lineal (LCG)

**Qué hacer:**  
Implementar el método `congruencial()` con los parámetros que cumplen el Teorema Hull-Dobell.

**Fundamento matemático:**  
Introducido por Lehmer en 1951. La fórmula de recurrencia es:

```
X_{n+1} = (a × X_n + c) mod m
u_n     = X_n / m
```

Donde:
- `m` = módulo (tamaño del espacio de estados)
- `a` = multiplicador
- `c` = incremento
- `X_0` = semilla

**Ejemplo manual con parámetros pequeños (a=5, c=1, m=9, X0=1):**
```
X1 = (5×1  + 1) % 9 = 6 mod 9 = 6   →   u1 = 6/9 = 0.667
X2 = (5×6  + 1) % 9 = 31 mod 9 = 4  →   u2 = 4/9 = 0.444
X3 = (5×4  + 1) % 9 = 21 mod 9 = 3  →   u3 = 3/9 = 0.333
X4 = (5×3  + 1) % 9 = 16 mod 9 = 7  →   u4 = 7/9 = 0.778
X5 = (5×7  + 1) % 9 = 36 mod 9 = 0  →   u5 = 0/9 = 0.000
X6 = (5×0  + 1) % 9 = 1 mod 9  = 1  →   u6 = 1/9 = 0.111
```
Después de 6 pasos vuelve a X0=1 → periodo = 6 < m=9 (no es periodo completo).

**Parámetros usados en el proyecto (ANSI C / glibc):**
```python
a = 1_103_515_245
c = 12_345
m = 2 ** 31   # = 2_147_483_648
```

**Por qué ESTOS parámetros exactamente — Teorema Hull-Dobell (1962):**  
Un LCG tiene periodo completo (= m) si y solo si se cumplen 3 condiciones:

```
Condición 1: mcd(c, m) = 1
             mcd(12345, 2^31) = 1  ✓  (12345 es impar, no comparte factores con 2^31)

Condición 2: (a-1) es divisible por todos los factores primos de m
             m = 2^31 → único factor primo es 2
             a-1 = 1103515244 → 1103515244 / 2 = 551757622  ✓  (es par)

Condición 3: Si 4 divide a m, entonces 4 divide a (a-1)
             4 | 2^31  ✓
             a-1 = 1103515244 → 1103515244 / 4 = 275878811  ✓  (divisible por 4)

Conclusión: Periodo completo = 2^31 = 2.147.483.648 números antes de repetirse.
```

**Código:**
```python
def congruencial(self, a=1_103_515_245, c=12_345, m=2**31) -> float:
    self._xn_lcg = (a * self._xn_lcg + c) % m
    return self._xn_lcg / m
```

**Por qué Python no tiene problema con números tan grandes:**  
En C, `a * Xn` podría causar integer overflow. Python maneja enteros de precisión arbitraria de forma nativa, así que la multiplicación `1103515245 * 2147483647` se calcula exactamente sin desbordamiento.

**Uso en el juego:**
```python
gen = GeneradorAleatorio(semilla=42, metodo='lcg')

# Dirección del fantasma en intersección (0=N, 1=S, 2=E, 3=O)
dir = gen.entero(0, 3)

# Velocidad aleatoria del enemigo al inicio del nivel
vel = gen.decimal(0.5, 2.0)
```

---

## Paso 1.4 — Implementar el Generador Combinado

**Qué hacer:**  
Implementar `combinado()` que suma los resultados de LCG y Midsquare aplicando parte fraccional.

**Fundamento matemático:**  
Basado en el algoritmo de Wichmann y Hill (1982). El principio es:

```
Si U1 ~ U(0,1) y U2 ~ U(0,1) son independientes,
entonces frac(U1 + U2) también sigue U(0,1).

u_comb = (u_lcg + u_mid) mod 1.0
```

El periodo del combinado es aproximadamente mcm(periodo_LCG, periodo_Mid), que es un número astronómicamente mayor que cualquiera de los dos solos.

**Código:**
```python
def combinado(self) -> float:
    u1 = self.congruencial()
    u2 = self.midsquare()
    return (u1 + u2) % 1.0
```

**Por qué `% 1.0` y no simplemente sumar:**  
La suma de dos números entre [0,1) puede dar hasta 1.999... Si no se aplica el módulo, el resultado no estaría en [0,1) y rompería todas las funciones de utilidad que asumen ese rango.

**Cuándo usar cada método:**

| Método | Cuándo usarlo | Por qué |
|---|---|---|
| `midsquare` | Efectos visuales menores | Histórico, suficiente para cosas no críticas |
| `congruencial` | IA de fantasmas, decisiones en tiempo real | Rápido, periodo garantizado |
| `combinado` | Generación de mapas | Menor correlación, más "impredecible" |

---

## Paso 1.5 — Implementar las Funciones de Utilidad

**Qué hacer:**  
Implementar `entero()`, `decimal()`, `booleano()`, `elegir()` y `mezclar()`. Estas son las funciones que el juego realmente llama.

### `_siguiente()` — el dispatcher interno

```python
def _siguiente(self) -> float:
    return {
        'lcg':  self.congruencial,
        'mid':  self.midsquare,
        'comb': self.combinado,
    }[self.metodo]()
```

**Por qué existe esta función:**  
Evita repetir la lógica de selección de método en cada función de utilidad. El juego puede cambiar `gen.metodo = 'comb'` y automáticamente todas las funciones de utilidad usarán el nuevo método.

### `entero(min_val, max_val)`

```python
def entero(self, min_val: int, max_val: int) -> int:
    rango = max_val - min_val + 1
    return min_val + int(self._siguiente() * rango)
```

**Ejemplo detallado:**  
Quieres un número entre 0 y 3 (4 direcciones posibles). `_siguiente()` devuelve 0.73.
```
rango = 3 - 0 + 1 = 4
int(0.73 * 4) = int(2.92) = 2
resultado = 0 + 2 = 2   →   dirección Este
```

**Por qué `+ 1` en el rango:**  
`_siguiente()` devuelve valores en [0, 1). Si el rango fuera 3 en vez de 4, el valor 3 nunca podría alcanzarse (porque 0.999... * 3 = 2.999... → int = 2).

### `decimal(min_val, max_val)`

```python
def decimal(self, min_val: float, max_val: float) -> float:
    return min_val + self._siguiente() * (max_val - min_val)
```

**Ejemplo:**  
Velocidad del fantasma entre 0.5 y 2.0. `_siguiente()` devuelve 0.4.
```
0.5 + 0.4 * (2.0 - 0.5) = 0.5 + 0.4 * 1.5 = 0.5 + 0.6 = 1.1
→ El fantasma se mueve al 110% de velocidad base.
```

### `booleano(probabilidad)`

```python
def booleano(self, probabilidad: float = 0.5) -> bool:
    return self._siguiente() < probabilidad
```

**Cómo funciona el sistema de probabilidades:**  
Como `_siguiente()` devuelve valores uniformes en [0,1), exactamente el `probabilidad * 100`% de las veces el valor caerá por debajo del umbral.
```
booleano(0.05)  →  True solo cuando u < 0.05  →  5% de las veces   (legendario)
booleano(0.20)  →  True solo cuando u < 0.20  →  20% de las veces  (vida extra)
booleano(0.02)  →  True solo cuando u < 0.02  →  2% de las veces   (super pastilla)
```

### `elegir(opciones)`

```python
def elegir(self, opciones: list) -> object:
    return opciones[self.entero(0, len(opciones) - 1)]
```

**Uso en el juego:**
```python
power_ups = ['botas_hermes', 'radar_fantasmal', 'aliento_fuego']
seleccionado = gen.elegir(power_ups)
# Elige uno de los 3 con probabilidad 1/3 cada uno
```

### `mezclar(lista)` — Fisher-Yates con PRNG propio

```python
def mezclar(self, lista: list) -> list:
    resultado = list(lista)
    for i in range(len(resultado) - 1, 0, -1):
        j = self.entero(0, i)
        resultado[i], resultado[j] = resultado[j], resultado[i]
    return resultado
```

**Ejemplo paso a paso con [0, 1, 2, 3]:**
```
i=3: j=entero(0,3)=1  →  swap pos 3 y 1  →  [0, 3, 2, 1]
i=2: j=entero(0,2)=0  →  swap pos 2 y 0  →  [2, 3, 0, 1]
i=1: j=entero(0,1)=1  →  swap pos 1 y 1  →  [2, 3, 0, 1] (sin cambio)
Resultado: [2, 3, 0, 1]
```

**Por qué usar este algoritmo y no `random.shuffle()` de Python:**  
Porque `random.shuffle()` usa el generador interno de Python, que ignora tu semilla. Con `mezclar()` propio, si la semilla es 42, el orden de mezcla siempre será el mismo — fundamental para que los niveles sean reproducibles.

---

## Paso 1.6 — Implementar Herramientas de Análisis Estadístico

**Qué hacer:**  
Implementar `activar_historial()`, `estadisticas()` y `restablecer()`. Estas funciones son para la documentación académica.

**Código:**
```python
def activar_historial(self) -> None:
    self._track = True
    self._historial = []

def estadisticas(self) -> dict:
    n = len(self._historial)
    media = sum(self._historial) / n
    varianza = sum((x - media) ** 2 for x in self._historial) / n
    return {
        'n':                 n,
        'media':             round(media, 6),
        'varianza':          round(varianza, 6),
        'media_esperada':    0.5,
        'varianza_esperada': round(1/12, 6),  # = 0.083333
    }

def restablecer(self) -> None:
    self.__init__(self.semilla, self.metodo)
```

**Por qué media ≈ 0.5 y varianza ≈ 1/12 son los valores esperados:**  
Para una distribución uniforme U(0,1) perfecta:
- Media teórica = ∫₀¹ x dx = 1/2 = 0.5
- Varianza teórica = ∫₀¹ (x - 0.5)² dx = 1/12 ≈ 0.0833

Si tus estadísticas se acercan a esos valores, el generador está bien calibrado. Eso es lo que demuestra en tu entrega.

---

## Paso 1.7 — Script de Prueba y Verificación

**Qué hacer:**  
Agregar el bloque `if __name__ == '__main__':` con pruebas que se ejecutan directamente.

**Por qué es importante:**  
Cuando el profesor ejecute `python aleatorio.py`, verá evidencia en consola de que los tres algoritmos funcionan, que las estadísticas son correctas y que la reproducibilidad está garantizada.

**Prueba clave de reproducibilidad:**
```python
for semilla in [42, 42, 777]:
    g = GeneradorAleatorio(semilla=semilla, metodo='lcg')
    seq = [round(g.congruencial(), 4) for _ in range(5)]
    print(f"Semilla {semilla}: {seq}")

# Salida esperada:
# Semilla  42: [0.5823, 0.5198, 0.466, 0.777, 0.4229]
# Semilla  42: [0.5823, 0.5198, 0.466, 0.777, 0.4229]  ← IDÉNTICO
# Semilla 777: [0.2726, 0.1515, 0.2863, 0.5634, 0.4546] ← DIFERENTE
```

**Esto demuestra:** Misma semilla = mismo mapa = reproducibilidad completa del Roguelike.

---

# FASE 2 — Entorno y Arquitectura del Juego

> **Meta:** Tener el "cascarón" del proyecto configurado profesionalmente antes de escribir lógica de juego. Esto incluye el entorno virtual, la estructura de carpetas y el game loop básico vacío.

---

## Paso 2.1 — Configurar el Entorno Virtual

**Qué hacer:**  
Crear un entorno virtual de Python aislado para el proyecto.

**Por qué es necesario:**  
Sin entorno virtual, Pygame se instala globalmente y puede entrar en conflicto con otros proyectos. El profesor necesita poder replicar tu entorno exactamente.

**Comandos en Linux (uno por uno):**
```bash
# 1. Ir a la carpeta raíz del proyecto
cd ~/pacman-roguelike

# 2. Crear el entorno virtual
python3 -m venv venv

# 3. Activarlo (debes hacerlo cada vez que abras una terminal)
source venv/bin/activate

# 4. Verificar que el pip es el del entorno (debe mostrar una ruta con /venv/)
which pip

# 5. Instalar Pygame
pip install pygame

# 6. Verificar la instalación
python -c "import pygame; print(pygame.version.ver)"

# 7. Guardar las dependencias
pip freeze > requirements.txt
```

**Contenido esperado de `requirements.txt`:**
```
pygame==2.6.1
```

**Script de configuración automática (para incluir en el repo):**  
Crea un archivo `setup.sh` en la raíz:
```bash
#!/bin/bash
echo "Configurando entorno Pac-Man Roguelike..."
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
echo "Listo. Ejecuta: source venv/bin/activate && python src/main.py"
```

El profesor solo ejecuta `bash setup.sh` y tiene todo listo.

---

## Paso 2.2 — Crear la Estructura de Carpetas

**Qué hacer:**  
Crear la jerarquía de directorios del proyecto desde la terminal.

**Estructura completa:**
```
pacman-roguelike/
│
├── lib/                    ← Tu librería PRNG (Fase 1)
│   ├── __init__.py         ← La hace importable como módulo
│   └── aleatorio.py        ← El archivo que ya tienes
│
├── src/                    ← Código fuente del juego
│   ├── __init__.py
│   ├── main.py             ← Punto de entrada, game loop
│   ├── entidades/          ← Pac-Man, fantasmas
│   │   ├── __init__.py
│   │   ├── pacman.py
│   │   └── fantasma.py
│   ├── mundo/              ← Tablero, generador de mapas
│   │   ├── __init__.py
│   │   ├── tablero.py
│   │   └── generador_mapa.py
│   └── ui/                 ← Menús, HUD, pantallas
│       ├── __init__.py
│       ├── menu.py
│       └── hud.py
│
├── assets/                 ← Recursos estáticos
│   ├── sonidos/
│   │   ├── comer.wav
│   │   ├── morir.wav
│   │   └── musica_fondo.ogg
│   └── fuentes/
│       └── pixel_font.ttf
│
├── datos/                  ← Persistencia
│   └── ranking.json        ← Se crea automáticamente al jugar
│
├── venv/                   ← Entorno virtual (NO subir a Git)
├── requirements.txt
├── setup.sh
└── README.md
```

**Comandos para crear toda la estructura de una vez:**
```bash
mkdir -p pacman-roguelike/{lib,src/{entidades,mundo,ui},assets/{sonidos,fuentes},datos}
cd pacman-roguelike
touch lib/__init__.py lib/aleatorio.py
touch src/__init__.py src/main.py
touch src/entidades/__init__.py src/entidades/pacman.py src/entidades/fantasma.py
touch src/mundo/__init__.py src/mundo/tablero.py src/mundo/generador_mapa.py
touch src/ui/__init__.py src/ui/menu.py src/ui/hud.py
touch datos/ranking.json
echo "[]" > datos/ranking.json
```

**El `__init__.py`:**  
Cada carpeta con un `__init__.py` se convierte en un "paquete" de Python. Esto permite hacer imports como `from lib.aleatorio import GeneradorAleatorio` desde cualquier parte del proyecto.

---

## Paso 2.3 — Configurar el `__init__.py` de la Librería

**Qué hacer:**  
Editar `lib/__init__.py` para que la librería sea importable directamente.

```python
# lib/__init__.py
from .aleatorio import GeneradorAleatorio

__all__ = ['GeneradorAleatorio']
__version__ = '1.0.0'
__author__ = 'Tu Nombre'
```

**Con esto, en el juego puedes importar así:**
```python
# En cualquier archivo del juego
from lib import GeneradorAleatorio

gen = GeneradorAleatorio(semilla=42, metodo='comb')
```

En vez de la forma más larga `from lib.aleatorio import GeneradorAleatorio`.

---

## Paso 2.4 — Implementar el Game Loop Base en `main.py`

**Qué hacer:**  
Crear el ciclo principal del juego con la máquina de estados y las 4 fases del loop.

**El Game Loop — concepto fundamental:**  
Todo juego funciona en un ciclo infinito que se repite ~60 veces por segundo:
```
┌──────────────────────────────────────────┐
│  1. EVENTOS   → ¿Qué hizo el usuario?   │
│  2. UPDATE    → Actualizar lógica        │
│  3. DRAW      → Dibujar en pantalla      │
│  4. CLOCK     → Limitar a 60 FPS         │
└──────────────────────────────────────────┘
         ↑_________________________________↓
                (repite para siempre)
```

**Máquina de Estados — qué es y por qué:**  
El juego puede estar en distintos "modos": menú, jugando, pausa, game over. En vez de usar variables booleanas dispersas (`en_menu = True, jugando = False...`), usamos un único estado activo.

**Código de `main.py`:**
```python
import sys
import pygame
from lib import GeneradorAleatorio

# ─── Constantes ────────────────────────────────────────────────────────────────
ANCHO         = 800
ALTO          = 600
FPS           = 60
TITULO        = "Pac-Man Roguelike"

COLOR_FONDO   = (10, 10, 30)       # Azul muy oscuro
COLOR_TEXTO   = (255, 255, 255)

# Estados de la máquina de estados
ESTADO_MENU      = 'menu'
ESTADO_JUGANDO   = 'jugando'
ESTADO_PAUSA     = 'pausa'
ESTADO_GAME_OVER = 'game_over'


# ─── Clase principal del juego ─────────────────────────────────────────────────
class Juego:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption(TITULO)

        self.pantalla = pygame.display.set_mode((ANCHO, ALTO))
        self.reloj    = pygame.time.Clock()
        self.fuente   = pygame.font.Font(None, 36)

        # Estado inicial
        self.estado = ESTADO_MENU

        # El generador se inicializa sin semilla fija
        # (se asignará cuando el jugador empiece una partida)
        self.gen = None

        self.corriendo = True

    # ── Ciclo principal ──────────────────────────────────────────────────────
    def ejecutar(self):
        while self.corriendo:
            self._manejar_eventos()
            self._actualizar()
            self._dibujar()
            self.reloj.tick(FPS)

        pygame.quit()
        sys.exit()

    # ── 1. Eventos ───────────────────────────────────────────────────────────
    def _manejar_eventos(self):
        for evento in pygame.event.get():

            # Cerrar ventana con la X
            if evento.type == pygame.QUIT:
                self.corriendo = False

            # Teclas presionadas
            if evento.type == pygame.KEYDOWN:
                if self.estado == ESTADO_MENU:
                    self._eventos_menu(evento)
                elif self.estado == ESTADO_JUGANDO:
                    self._eventos_jugando(evento)
                elif self.estado == ESTADO_PAUSA:
                    self._eventos_pausa(evento)
                elif self.estado == ESTADO_GAME_OVER:
                    self._eventos_game_over(evento)

    def _eventos_menu(self, evento):
        if evento.key == pygame.K_RETURN:    # Enter → iniciar partida
            self._iniciar_partida()
        if evento.key == pygame.K_ESCAPE:    # Escape → salir
            self.corriendo = False

    def _eventos_jugando(self, evento):
        if evento.key == pygame.K_ESCAPE:    # Escape → pausar
            self.estado = ESTADO_PAUSA

    def _eventos_pausa(self, evento):
        if evento.key == pygame.K_ESCAPE:    # Escape → reanudar
            self.estado = ESTADO_JUGANDO
        if evento.key == pygame.K_q:         # Q → menú principal
            self.estado = ESTADO_MENU

    def _eventos_game_over(self, evento):
        if evento.key == pygame.K_RETURN:    # Enter → volver al menú
            self.estado = ESTADO_MENU

    # ── 2. Actualizar lógica ─────────────────────────────────────────────────
    def _actualizar(self):
        if self.estado == ESTADO_JUGANDO:
            pass   # Aquí irá la lógica del juego (Fases 3-5)

    # ── 3. Dibujar ───────────────────────────────────────────────────────────
    def _dibujar(self):
        self.pantalla.fill(COLOR_FONDO)

        if self.estado == ESTADO_MENU:
            self._dibujar_menu()
        elif self.estado == ESTADO_JUGANDO:
            self._dibujar_juego()
        elif self.estado == ESTADO_PAUSA:
            self._dibujar_pausa()
        elif self.estado == ESTADO_GAME_OVER:
            self._dibujar_game_over()

        pygame.display.flip()   # Mostrar el frame renderizado

    def _dibujar_menu(self):
        titulo = self.fuente.render("PAC-MAN ROGUELIKE", True, (255, 200, 0))
        inicio = self.fuente.render("ENTER  →  Jugar", True, COLOR_TEXTO)
        salida = self.fuente.render("ESC    →  Salir", True, COLOR_TEXTO)

        self.pantalla.blit(titulo, (ANCHO//2 - titulo.get_width()//2, 200))
        self.pantalla.blit(inicio, (ANCHO//2 - inicio.get_width()//2, 320))
        self.pantalla.blit(salida, (ANCHO//2 - salida.get_width()//2, 370))

    def _dibujar_juego(self):
        # Placeholder: se reemplaza en Fase 3
        msg = self.fuente.render("JUGANDO... (Fase 3 pendiente)", True, COLOR_TEXTO)
        self.pantalla.blit(msg, (ANCHO//2 - msg.get_width()//2, ALTO//2))

    def _dibujar_pausa(self):
        msg   = self.fuente.render("PAUSA", True, (255, 200, 0))
        reanu = self.fuente.render("ESC → Reanudar  |  Q → Menú", True, COLOR_TEXTO)
        self.pantalla.blit(msg,   (ANCHO//2 - msg.get_width()//2,   ALTO//2 - 40))
        self.pantalla.blit(reanu, (ANCHO//2 - reanu.get_width()//2, ALTO//2 + 10))

    def _dibujar_game_over(self):
        msg = self.fuente.render("GAME OVER", True, (255, 50, 50))
        sub = self.fuente.render("ENTER → Menú Principal", True, COLOR_TEXTO)
        self.pantalla.blit(msg, (ANCHO//2 - msg.get_width()//2, ALTO//2 - 40))
        self.pantalla.blit(sub, (ANCHO//2 - sub.get_width()//2, ALTO//2 + 20))

    # ── Helpers ──────────────────────────────────────────────────────────────
    def _iniciar_partida(self):
        """Crea un nuevo generador con semilla basada en el tiempo actual."""
        import time
        semilla = int(time.time()) % 100_000   # Semilla diferente cada partida
        self.gen = GeneradorAleatorio(semilla=semilla, metodo='comb')
        self.estado = ESTADO_JUGANDO
        print(f"[DEBUG] Nueva partida. Semilla: {semilla}")
        # En la versión final, mostrar esta semilla al jugador
        # para que pueda compartirla con amigos (Sistema de Seeds)


# ─── Punto de entrada ──────────────────────────────────────────────────────────
if __name__ == '__main__':
    juego = Juego()
    juego.ejecutar()
```

**Qué hace `pygame.display.flip()`:**  
Pygame usa "double buffering": mientras ves el frame actual, el siguiente se dibuja en un buffer oculto. `flip()` intercambia los buffers, mostrando el nuevo frame instantáneamente y evitando parpadeo.

**Por qué `self.reloj.tick(FPS)`:**  
Sin esto el juego correría tan rápido como el CPU permitiera (miles de FPS). `tick(60)` pausa el loop el tiempo necesario para mantener exactamente 60 iteraciones por segundo, haciendo el juego consistente en cualquier máquina.

---

## Paso 2.5 — Configurar `.gitignore`

**Qué hacer:**  
Crear `.gitignore` para que Git no suba el entorno virtual ni archivos basura.

```gitignore
# Entorno virtual
venv/
.venv/
env/

# Python
__pycache__/
*.py[cod]
*.pyo
*.pyd
.Python

# Datos de usuario (el ranking se genera en ejecución)
datos/ranking.json

# IDEs
.vscode/
.idea/
*.swp

# Sistema operativo
.DS_Store
Thumbs.db
```

**Por qué excluir `ranking.json`:**  
Es un archivo generado por el juego en tiempo de ejecución. Cada jugador tendrá el suyo. No tiene sentido versionarlo.

---

# FASE 3 — Generación Procedural de Tableros

> **Meta:** El mapa del juego se genera algorítmicamente usando la librería PRNG propia. Cada semilla produce un mapa diferente pero siempre conectable (sin zonas aisladas).

---

## Paso 3.1 — Definir la Clase Tablero

**Qué hacer:**  
Crear `src/mundo/tablero.py` con la representación de la rejilla y sus constantes.

**Por qué una clase y no un array global:**  
Encapsular el tablero permite que el generador de mapas (Fase 3.2) lo llene, el juego lo consulte, y el dibujador lo renderice, sin que ninguno dependa del otro directamente.

```python
# src/mundo/tablero.py

# ─── Tipos de celda ────────────────────────────────────────────────────────────
MURO        = 0
PASILLO     = 1
PUNTO       = 2   # Punto normal (+10 pts)
SUPER_PUNTO = 3   # Super pastilla (activa modo asustado en fantasmas)
VACIO       = 4   # Pasillo sin comida (ya comido)


class Tablero:
    """
    Representa el laberinto como una matriz de enteros.

    Cada celda tiene un valor:
        0 = MURO
        1 = PASILLO (sin comida)
        2 = PUNTO   (comida normal)
        3 = SUPER_PUNTO (pastilla de poder)
        4 = VACIO   (celda ya visitada)
    """

    def __init__(self, filas: int = 21, columnas: int = 21):
        # Las dimensiones deben ser impares para que el algoritmo
        # de excavación funcione correctamente
        self.filas    = filas if filas % 2 != 0 else filas + 1
        self.columnas = columnas if columnas % 2 != 0 else columnas + 1

        # Inicializar todo como MURO
        self.celdas = [[MURO] * self.columnas for _ in range(self.filas)]

        # Estadísticas (calculadas al generar)
        self.total_puntos  = 0
        self.puntos_comidos = 0

    def obtener(self, fila: int, col: int) -> int:
        """Retorna el tipo de celda en (fila, col)."""
        if 0 <= fila < self.filas and 0 <= col < self.columnas:
            return self.celdas[fila][col]
        return MURO   # Fuera del tablero = muro

    def establecer(self, fila: int, col: int, valor: int) -> None:
        """Establece el tipo de celda en (fila, col)."""
        if 0 <= fila < self.filas and 0 <= col < self.columnas:
            self.celdas[fila][col] = valor

    def es_muro(self, fila: int, col: int) -> bool:
        return self.obtener(fila, col) == MURO

    def es_pasillo(self, fila: int, col: int) -> bool:
        return self.obtener(fila, col) in (PASILLO, PUNTO, SUPER_PUNTO, VACIO)

    def comer_punto(self, fila: int, col: int) -> int:
        """
        Intenta comer el punto en (fila, col).
        Retorna los puntos obtenidos (0 si no había nada).
        """
        celda = self.obtener(fila, col)
        if celda == PUNTO:
            self.establecer(fila, col, VACIO)
            self.puntos_comidos += 1
            return 10
        if celda == SUPER_PUNTO:
            self.establecer(fila, col, VACIO)
            self.puntos_comidos += 1
            return 50
        return 0

    @property
    def completado(self) -> bool:
        """Retorna True si todos los puntos han sido comidos."""
        return self.total_puntos > 0 and self.puntos_comidos >= self.total_puntos

    def __repr__(self) -> str:
        simbolos = {MURO: '█', PASILLO: ' ', PUNTO: '·', SUPER_PUNTO: '●', VACIO: ' '}
        filas = []
        for fila in self.celdas:
            filas.append(''.join(simbolos.get(c, '?') for c in fila))
        return '\n'.join(filas)
```

---

## Paso 3.2 — Implementar el Generador de Mapas (Caminata Aleatoria)

**Qué hacer:**  
Crear `src/mundo/generador_mapa.py` con el algoritmo de excavación aleatorio usando la librería PRNG.

**El algoritmo — Caminata Aleatoria (Random Walk):**

```
1. Empezar con todo el tablero como muros.
2. Colocar un "excavador" en el centro.
3. El excavador se mueve en una dirección aleatoria (N/S/E/O).
4. Si el movimiento es válido (sin salirse del tablero), convierte esas celdas en pasillos.
5. Repetir hasta haber excavado suficientes pasillos (p.ej. 40% del tablero).
6. Colocar la comida en todos los pasillos.
7. Colocar super pastillas en las esquinas/callejones.
8. Verificar conectividad con Flood Fill.
```

**Por qué se mueve DE A DOS celdas:**  
Para que los pasillos tengan paredes de grosor 1 entre ellos. Si el excavador avanzara de a 1, los pasillos se fusionarían y no habría laberinto.

```python
# src/mundo/generador_mapa.py

from .tablero import Tablero, MURO, PASILLO, PUNTO, SUPER_PUNTO
from lib import GeneradorAleatorio


# Direcciones: (delta_fila, delta_columna)
NORTE = (-1,  0)
SUR   = ( 1,  0)
ESTE  = ( 0,  1)
OESTE = ( 0, -1)
DIRECCIONES = [NORTE, SUR, ESTE, OESTE]


class GeneradorMapa:
    """
    Genera tableros de laberinto usando el algoritmo de Caminata Aleatoria.
    Usa la librería PRNG propia para que el tablero sea reproducible con la semilla.
    """

    def __init__(self, gen: GeneradorAleatorio):
        self.gen = gen

    def generar(self, filas: int = 21, columnas: int = 21,
                cobertura: float = 0.45) -> Tablero:
        """
        Genera un tablero nuevo.

        Parámetros
        ----------
        filas, columnas : int  Dimensiones del tablero (deben ser impares)
        cobertura       : float  Fracción mínima de celdas que serán pasillo (0.0 a 1.0)
        """
        tablero = Tablero(filas, columnas)

        self._excavar(tablero, cobertura)
        self._colocar_comida(tablero)
        self._colocar_super_pastillas(tablero)
        self._verificar_conectividad(tablero)

        return tablero

    # ── Paso 1: Excavación ───────────────────────────────────────────────────
    def _excavar(self, tablero: Tablero, cobertura: float) -> None:
        """Mueve el excavador aleatoriamente abriendo pasillos."""
        total_celdas    = tablero.filas * tablero.columnas
        objetivo        = int(total_celdas * cobertura)
        celdas_abiertas = 0

        # Empezar en el centro (debe ser una celda impar)
        fila = tablero.filas // 2
        col  = tablero.columnas // 2

        tablero.establecer(fila, col, PASILLO)
        celdas_abiertas += 1

        # Excavador: se mueve hasta alcanzar la cobertura deseada
        intentos_maximos = total_celdas * 10   # Evitar loop infinito
        intentos = 0

        while celdas_abiertas < objetivo and intentos < intentos_maximos:
            # Elegir dirección aleatoria con la librería PRNG
            idx = self.gen.entero(0, 3)
            df, dc = DIRECCIONES[idx]

            # Moverse DE A DOS para mantener paredes entre pasillos
            nueva_fila = fila + df * 2
            nueva_col  = col  + dc * 2

            # Verificar que la nueva posición está dentro del tablero
            # (con margen de 1 para no tocar los bordes)
            if (1 <= nueva_fila < tablero.filas - 1 and
                    1 <= nueva_col < tablero.columnas - 1):

                # Si la celda destino aún es muro, abrir el pasaje
                if tablero.es_muro(nueva_fila, nueva_col):
                    # Abrir celda intermedia (la pared entre las dos)
                    tablero.establecer(fila + df, col + dc, PASILLO)
                    # Abrir celda destino
                    tablero.establecer(nueva_fila, nueva_col, PASILLO)
                    celdas_abiertas += 2

                # Mover el excavador aunque la celda ya estuviera abierta
                # (así el excavador no se queda atascado)
                fila = nueva_fila
                col  = nueva_col

            intentos += 1

    # ── Paso 2: Colocar comida ───────────────────────────────────────────────
    def _colocar_comida(self, tablero: Tablero) -> None:
        """Coloca PUNTO en cada celda que sea PASILLO."""
        for f in range(tablero.filas):
            for c in range(tablero.columnas):
                if tablero.obtener(f, c) == PASILLO:
                    tablero.establecer(f, c, PUNTO)
                    tablero.total_puntos += 1

    # ── Paso 3: Colocar super pastillas ─────────────────────────────────────
    def _colocar_super_pastillas(self, tablero: Tablero) -> None:
        """
        Coloca 4 super pastillas en callejones sin salida (celdas con solo 1 vecino pasillo).
        Los callejones son las posiciones más arriesgadas → mayor recompensa.
        """
        callejones = []
        for f in range(1, tablero.filas - 1):
            for c in range(1, tablero.columnas - 1):
                if tablero.obtener(f, c) == PUNTO:
                    vecinos_pasillo = sum([
                        1 for df, dc in DIRECCIONES
                        if tablero.es_pasillo(f + df, c + dc)
                    ])
                    if vecinos_pasillo == 1:   # Solo un vecino = callejón
                        callejones.append((f, c))

        # Mezclar callejones y tomar los primeros 4
        callejones_mezclados = self.gen.mezclar(callejones)
        for f, c in callejones_mezclados[:4]:
            tablero.establecer(f, c, SUPER_PUNTO)

    # ── Paso 4: Verificar conectividad ───────────────────────────────────────
    def _verificar_conectividad(self, tablero: Tablero) -> None:
        """
        Flood Fill desde el primer pasillo encontrado.
        Marca todas las celdas alcanzables. Las no alcanzables se convierten en muro
        para evitar zonas aisladas donde Pac-Man no puede llegar.
        """
        # Encontrar primer pasillo
        inicio = None
        for f in range(tablero.filas):
            for c in range(tablero.columnas):
                if tablero.es_pasillo(f, c):
                    inicio = (f, c)
                    break
            if inicio:
                break

        if not inicio:
            return   # Tablero vacío (no debería ocurrir)

        # BFS desde el inicio
        from collections import deque
        visitados = set()
        cola = deque([inicio])

        while cola:
            f, c = cola.popleft()
            if (f, c) in visitados:
                continue
            visitados.add((f, c))

            for df, dc in DIRECCIONES:
                nf, nc = f + df, c + dc
                if (nf, nc) not in visitados and tablero.es_pasillo(nf, nc):
                    cola.append((nf, nc))

        # Aislar celdas no alcanzables
        aisladas = 0
        for f in range(tablero.filas):
            for c in range(tablero.columnas):
                if tablero.es_pasillo(f, c) and (f, c) not in visitados:
                    tablero.establecer(f, c, MURO)
                    tablero.total_puntos -= 1
                    aisladas += 1

        if aisladas > 0:
            print(f"[INFO] Flood Fill eliminó {aisladas} celdas aisladas.")
```

---

## Paso 3.3 — Renderizar el Tablero en Pygame

**Qué hacer:**  
Añadir el método `dibujar()` al tablero para que Pygame lo muestre.

**Por qué separar la lógica del dibujo:**  
El tablero no debería saber cómo se dibuja. Esto se llama principio de separación de responsabilidades. Si mañana cambias de Pygame a otra librería, solo cambias el `dibujar()`, no la lógica del juego.

```python
# Agregar a src/mundo/tablero.py

import pygame

# Tamaño de cada celda en píxeles
TAM_CELDA = 28

# Colores
COLOR_MURO        = (30,  30, 100)
COLOR_PASILLO     = (10,  10,  30)
COLOR_PUNTO       = (255, 200,   0)
COLOR_SUPER_PUNTO = (255, 100, 100)

class Tablero:
    # ... (código anterior) ...

    def dibujar(self, superficie: pygame.Surface,
                offset_x: int = 0, offset_y: int = 0) -> None:
        """
        Dibuja el tablero completo en la superficie de Pygame.

        Parámetros
        ----------
        superficie : pygame.Surface   La ventana del juego
        offset_x   : int              Desplazamiento horizontal (para centrar)
        offset_y   : int              Desplazamiento vertical
        """
        for f in range(self.filas):
            for c in range(self.columnas):
                x = offset_x + c * TAM_CELDA
                y = offset_y + f * TAM_CELDA
                rect = pygame.Rect(x, y, TAM_CELDA, TAM_CELDA)
                celda = self.celdas[f][c]

                if celda == MURO:
                    pygame.draw.rect(superficie, COLOR_MURO, rect)
                    # Borde interior para efecto 3D simple
                    pygame.draw.rect(superficie, (50, 50, 150), rect, 1)

                elif celda in (PASILLO, VACIO):
                    pygame.draw.rect(superficie, COLOR_PASILLO, rect)

                elif celda == PUNTO:
                    pygame.draw.rect(superficie, COLOR_PASILLO, rect)
                    # Punto pequeño en el centro
                    centro = (x + TAM_CELDA // 2, y + TAM_CELDA // 2)
                    pygame.draw.circle(superficie, COLOR_PUNTO, centro, 3)

                elif celda == SUPER_PUNTO:
                    pygame.draw.rect(superficie, COLOR_PASILLO, rect)
                    # Círculo más grande, parpadeante
                    centro = (x + TAM_CELDA // 2, y + TAM_CELDA // 2)
                    pygame.draw.circle(superficie, COLOR_SUPER_PUNTO, centro, 7)
```

---

# FASE 4 — Entidades e Inteligencia Artificial

> **Meta:** Implementar Pac-Man y los fantasmas como clases independientes. Los fantasmas tienen comportamientos diferenciados: aleatorio (usa PRNG), perseguidor (A*) y amboscador.

---

## Paso 4.1 — Clase Base Actor

**Qué hacer:**  
Crear la clase `Actor` en `src/entidades/` que comparten Pac-Man y todos los fantasmas.

```python
# src/entidades/actor.py

import pygame

class Actor:
    """
    Clase base para Pac-Man y los fantasmas.
    Encapsula posición, movimiento y colisiones en la rejilla.
    """

    def __init__(self, fila: int, col: int, color: tuple,
                 velocidad: float = 1.0, tam_celda: int = 28):
        self.fila     = fila       # Posición en la rejilla (no en píxeles)
        self.col      = col
        self.color    = color
        self.velocidad = velocidad
        self.tam_celda = tam_celda

        # Dirección actual (df=delta_fila, dc=delta_col)
        self.dir_fila = 0
        self.dir_col  = 0

        # Posición en píxeles (para animación suave)
        self.px = col * tam_celda
        self.py = fila * tam_celda

    @property
    def rect(self) -> pygame.Rect:
        """Rectángulo de colisión en píxeles."""
        return pygame.Rect(self.px, self.py, self.tam_celda, self.tam_celda)

    def mover(self, tablero) -> None:
        """
        Intenta mover el actor en su dirección actual.
        Solo avanza si la celda destino no es un muro.
        Subclases sobreescriben esto para cambiar la dirección antes de moverse.
        """
        nueva_fila = self.fila + self.dir_fila
        nueva_col  = self.col  + self.dir_col

        if not tablero.es_muro(nueva_fila, nueva_col):
            self.fila = nueva_fila
            self.col  = nueva_col
            self.px   = self.col  * self.tam_celda
            self.py   = self.fila * self.tam_celda

    def dibujar(self, superficie: pygame.Surface,
                offset_x: int = 0, offset_y: int = 0) -> None:
        x = offset_x + self.px
        y = offset_y + self.py
        centro = (x + self.tam_celda // 2, y + self.tam_celda // 2)
        pygame.draw.circle(superficie, self.color, centro, self.tam_celda // 2 - 2)
```

---

## Paso 4.2 — Clase PacMan

**Qué hacer:**  
Implementar `src/entidades/pacman.py` con movimiento controlado por teclado y gestión de vidas.

```python
# src/entidades/pacman.py

import pygame
from .actor import Actor

class PacMan(Actor):
    """
    Pac-Man: controlado por el jugador mediante las teclas de dirección.
    """

    def __init__(self, fila: int, col: int):
        super().__init__(fila, col, color=(255, 220, 0))   # Amarillo
        self.vidas      = 3
        self.puntaje    = 0
        self.invencible = False   # Activado al comer super pastilla
        self.timer_invencible = 0

        # Dirección deseada (la que el jugador presionó)
        # Se aplica cuando el pasillo lo permite
        self.dir_deseada_f = 0
        self.dir_deseada_c = 0

    def manejar_teclado(self, evento: pygame.event.Event) -> None:
        """Registra la dirección que quiere el jugador."""
        if evento.type == pygame.KEYDOWN:
            if evento.key in (pygame.K_UP,    pygame.K_w):
                self.dir_deseada_f, self.dir_deseada_c = -1,  0
            elif evento.key in (pygame.K_DOWN,  pygame.K_s):
                self.dir_deseada_f, self.dir_deseada_c =  1,  0
            elif evento.key in (pygame.K_LEFT,  pygame.K_a):
                self.dir_deseada_f, self.dir_deseada_c =  0, -1
            elif evento.key in (pygame.K_RIGHT, pygame.K_d):
                self.dir_deseada_f, self.dir_deseada_c =  0,  1

    def mover(self, tablero) -> None:
        """
        Intenta aplicar la dirección deseada primero.
        Si no puede (hay muro), mantiene la dirección actual.
        """
        nf = self.fila + self.dir_deseada_f
        nc = self.col  + self.dir_deseada_c

        if not tablero.es_muro(nf, nc):
            # La dirección deseada es válida → aplicarla
            self.dir_fila = self.dir_deseada_f
            self.dir_col  = self.dir_deseada_c

        # Moverse en la dirección actual (que puede ser la deseada o la anterior)
        super().mover(tablero)

        # Comer puntos
        puntos = tablero.comer_punto(self.fila, self.col)
        self.puntaje += puntos

    def morir(self) -> None:
        self.vidas -= 1
        self.invencible = False
```

---

## Paso 4.3 — Clase Fantasma Base y FSM

**Qué hacer:**  
Implementar la Máquina de Estados Finitos (FSM) de los fantasmas. Cada fantasma puede estar en 4 estados.

**Los 4 estados:**

```
DISPERSIÓN  → El fantasma patrulla su esquina asignada
PERSECUCIÓN → El fantasma busca a Pac-Man activamente
ASUSTADO    → Pac-Man comió una super pastilla; el fantasma huye
RETIRADA    → El fantasma fue comido; vuelve a su base
```

```python
# src/entidades/fantasma.py

import pygame
from .actor import Actor

# Estados de la FSM
DISPERSION  = 'dispersion'
PERSECUCION = 'persecucion'
ASUSTADO    = 'asustado'
RETIRADA    = 'retirada'

COLOR_ASUSTADO  = (50,  50, 200)
COLOR_RETIRADA  = (200, 200, 200)


class Fantasma(Actor):
    """
    Fantasma base con Máquina de Estados Finitos.
    Subclases sobreescriben _elegir_direccion() para diferenciar comportamientos.
    """

    def __init__(self, fila: int, col: int, color: tuple,
                 fila_base: int, col_base: int):
        super().__init__(fila, col, color)
        self.fila_base   = fila_base   # Posición de reaparición
        self.col_base    = col_base
        self.color_orig  = color

        self.estado = DISPERSION
        self.timer  = 0   # Controla cuántos ticks dura cada estado

        # Tiempos de cada estado (en frames a 60 FPS)
        self.DURACION_DISPERSION  = 60 * 7    # 7 segundos
        self.DURACION_PERSECUCION = 60 * 20   # 20 segundos
        self.DURACION_ASUSTADO    = 60 * 8    # 8 segundos

    def actualizar_estado(self) -> None:
        """
        Avanza el timer y transiciona entre estados cuando corresponde.
        """
        self.timer += 1

        if self.estado == DISPERSION:
            if self.timer >= self.DURACION_DISPERSION:
                self._cambiar_estado(PERSECUCION)

        elif self.estado == PERSECUCION:
            if self.timer >= self.DURACION_PERSECUCION:
                self._cambiar_estado(DISPERSION)

        elif self.estado == ASUSTADO:
            if self.timer >= self.DURACION_ASUSTADO:
                self._cambiar_estado(PERSECUCION)

        elif self.estado == RETIRADA:
            # Cuando llega a la base, vuelve a dispersión
            if self.fila == self.fila_base and self.col == self.col_base:
                self._cambiar_estado(DISPERSION)

    def _cambiar_estado(self, nuevo_estado: str) -> None:
        self.estado = nuevo_estado
        self.timer  = 0

    def asustar(self) -> None:
        """Llamado cuando Pac-Man come una super pastilla."""
        if self.estado != RETIRADA:
            self._cambiar_estado(ASUSTADO)

    def ser_comido(self) -> None:
        """Llamado cuando Pac-Man come al fantasma asustado."""
        self._cambiar_estado(RETIRADA)

    def dibujar(self, superficie, offset_x=0, offset_y=0) -> None:
        """Cambia el color según el estado antes de dibujar."""
        if self.estado == ASUSTADO:
            self.color = COLOR_ASUSTADO
        elif self.estado == RETIRADA:
            self.color = COLOR_RETIRADA
        else:
            self.color = self.color_orig
        super().dibujar(superficie, offset_x, offset_y)
```

---

## Paso 4.4 — Fantasma Aleatorio (usa la librería PRNG)

**Qué hacer:**  
Implementar el fantasma que usa `gen.entero(0, 3)` para decidir su dirección en cada intersección.

```python
# Agregar a src/entidades/fantasma.py

DIRECCIONES = [(-1,0), (1,0), (0,-1), (0,1)]   # N, S, O, E

class FantasmaAleatorio(Fantasma):
    """
    En cada intersección consulta la librería PRNG para elegir dirección.
    Este es el uso más directo y documentable de la librería en el juego.
    """

    def __init__(self, fila, col, fila_base, col_base, gen):
        super().__init__(fila, col, color=(255, 0, 0),
                         fila_base=fila_base, col_base=col_base)
        self.gen = gen   # Referencia al generador del juego

    def mover(self, tablero, pacman=None) -> None:
        self.actualizar_estado()

        # Detectar si estamos en una intersección (2+ pasillos disponibles)
        pasillos_disponibles = [
            (df, dc) for df, dc in DIRECCIONES
            if not tablero.es_muro(self.fila + df, self.col + dc)
            and (df, dc) != (-self.dir_fila, -self.dir_col)   # No regresar
        ]

        if len(pasillos_disponibles) > 1:
            # AQUÍ se usa la librería PRNG ← punto académico clave
            idx = self.gen.entero(0, len(pasillos_disponibles) - 1)
            self.dir_fila, self.dir_col = pasillos_disponibles[idx]

        super().mover(tablero)
```

---

## Paso 4.5 — Fantasma Perseguidor (Algoritmo A*)

**Qué hacer:**  
Implementar el fantasma que usa A* para encontrar el camino más corto a Pac-Man.

**Cómo funciona A\*:**

```
f(n) = g(n) + h(n)

g(n) = costo real desde el inicio hasta n (número de pasos)
h(n) = heurística: distancia Manhattan desde n hasta el objetivo
       |fila_actual - fila_objetivo| + |col_actual - col_objetivo|

El algoritmo siempre expande el nodo con menor f(n).
Garantiza el camino más corto en laberintos sin costos variables.
```

```python
import heapq

class FantasmaPerseguidor(Fantasma):
    """
    Usa el algoritmo A* para encontrar siempre el camino más corto a Pac-Man.
    Recalcula la ruta cada N frames para no ser demasiado omnisciente.
    """

    def __init__(self, fila, col, fila_base, col_base):
        super().__init__(fila, col, color=(255, 100, 0),
                         fila_base=fila_base, col_base=col_base)
        self.ruta = []              # Lista de (fila, col) hacia Pac-Man
        self.recalcular_cada = 30   # Recalcular cada 30 frames (0.5 seg)
        self.frames_sin_recalc = 0

    def mover(self, tablero, pacman) -> None:
        self.actualizar_estado()

        if self.estado == PERSECUCION:
            self.frames_sin_recalc += 1
            if self.frames_sin_recalc >= self.recalcular_cada or not self.ruta:
                self.ruta = self._astar(tablero, pacman.fila, pacman.col)
                self.frames_sin_recalc = 0

            if self.ruta:
                siguiente = self.ruta.pop(0)
                self.dir_fila = siguiente[0] - self.fila
                self.dir_col  = siguiente[1] - self.col

        super().mover(tablero)

    def _astar(self, tablero, meta_f: int, meta_c: int) -> list:
        """
        Retorna lista de (fila, col) desde la posición actual hasta (meta_f, meta_c).
        """
        inicio = (self.fila, self.col)
        meta   = (meta_f, meta_c)

        # Cola de prioridad: (f, g, nodo, camino)
        cola = [(0, 0, inicio, [])]
        visitados = set()

        while cola:
            f_val, g, nodo, camino = heapq.heappop(cola)

            if nodo in visitados:
                continue
            visitados.add(nodo)

            camino_actual = camino + [nodo]

            if nodo == meta:
                return camino_actual[1:]   # Excluir posición actual

            fila, col = nodo
            for df, dc in DIRECCIONES:
                vecino = (fila + df, col + dc)
                if vecino not in visitados and not tablero.es_muro(*vecino):
                    nuevo_g = g + 1
                    h = abs(vecino[0] - meta_f) + abs(vecino[1] - meta_c)
                    heapq.heappush(cola, (nuevo_g + h, nuevo_g, vecino, camino_actual))

        return []   # Sin camino (no debería ocurrir con conectividad garantizada)
```

---

# FASE 5 — Mecánicas de Juego y Persistencia

> **Meta:** Sistema de colisiones, gestión de créditos, ranking guardado en JSON, y sistema de loot con probabilidades usando la librería PRNG.

---

## Paso 5.1 — Sistema de Colisiones

**Qué hacer:**  
Detectar colisiones entre Pac-Man y los fantasmas basándose en su posición en la rejilla.

```python
# En src/main.py, dentro del método _actualizar()

def _verificar_colisiones(self) -> None:
    """
    Verifica si Pac-Man colisionó con algún fantasma.
    La detección es por celda (no por píxeles) para simplicidad.
    """
    for fantasma in self.fantasmas:
        if (fantasma.fila == self.pacman.fila and
                fantasma.col == self.pacman.col):

            if fantasma.estado == ASUSTADO:
                # Pac-Man come al fantasma
                fantasma.ser_comido()
                self.pacman.puntaje += 200
            else:
                # Fantasma mata a Pac-Man
                self.pacman.morir()
                self._reposicionar_actores()

                if self.pacman.vidas <= 0:
                    self.estado = ESTADO_GAME_OVER
                    self._guardar_ranking()
                return
```

---

## Paso 5.2 — Sistema de Loot con Probabilidades PRNG

**Qué hacer:**  
Implementar las tablas de botín usando `gen.booleano()` y `gen.elegir()`.

```python
# src/sistemas/loot.py

from lib import GeneradorAleatorio

ITEMS = {
    'legendario': {'prob': 0.05, 'puntos': 500, 'nombre': 'Imán de Puntos'},
    'raro':       {'prob': 0.15, 'puntos': 200, 'nombre': 'Radar Fantasmal'},
    'comun':      {'prob': 0.30, 'puntos':  50, 'nombre': 'Botas de Hermes'},
    'vida':       {'prob': 0.20, 'puntos':   0, 'nombre': 'Vida Extra'},
}

class SistemaLoot:
    def __init__(self, gen: GeneradorAleatorio):
        self.gen = gen

    def tirar_loot(self) -> dict | None:
        """
        Determina qué item cae al terminar un nivel.
        Las probabilidades se aplican en orden: legendario > raro > común > vida.
        """
        # AQUÍ se usa la librería PRNG ← segundo punto académico clave
        if self.gen.booleano(ITEMS['legendario']['prob']):
            return ITEMS['legendario']
        elif self.gen.booleano(ITEMS['raro']['prob']):
            return ITEMS['raro']
        elif self.gen.booleano(ITEMS['vida']['prob']):
            return ITEMS['vida']
        elif self.gen.booleano(ITEMS['comun']['prob']):
            return ITEMS['comun']
        return None   # Sin loot (el 30% restante)
```

---

## Paso 5.3 — Persistencia del Ranking en JSON

**Qué hacer:**  
Guardar y cargar el ranking de los 10 mejores puntajes en `datos/ranking.json`.

```python
# src/sistemas/ranking.py

import json
import os

RUTA_RANKING = 'datos/ranking.json'
MAX_ENTRADAS = 10


class SistemaRanking:

    def __init__(self):
        self.entradas = self._cargar()

    def _cargar(self) -> list:
        """Carga el ranking desde el archivo JSON."""
        if not os.path.exists(RUTA_RANKING):
            return []
        try:
            with open(RUTA_RANKING, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []   # Si el archivo está corrupto, empezar de cero

    def guardar(self, nombre: str, puntaje: int, semilla: int) -> None:
        """
        Agrega una nueva entrada al ranking y guarda.
        La semilla se guarda para que otros puedan jugar el mismo mapa.
        """
        nueva_entrada = {
            'nombre':  nombre,
            'puntaje': puntaje,
            'semilla': semilla,   # ← Clave para el sistema de Seeds del Roguelike
        }
        self.entradas.append(nueva_entrada)

        # Ordenar de mayor a menor puntaje
        self.entradas.sort(key=lambda e: e['puntaje'], reverse=True)

        # Mantener solo los 10 mejores
        self.entradas = self.entradas[:MAX_ENTRADAS]

        with open(RUTA_RANKING, 'w', encoding='utf-8') as f:
            json.dump(self.entradas, f, indent=2, ensure_ascii=False)

    def es_record(self, puntaje: int) -> bool:
        """Retorna True si el puntaje entraría al top 10."""
        if len(self.entradas) < MAX_ENTRADAS:
            return True
        return puntaje > self.entradas[-1]['puntaje']
```

**Formato del `ranking.json` generado:**
```json
[
  { "nombre": "ANA", "puntaje": 4500, "semilla": 83421 },
  { "nombre": "BOB", "puntaje": 3200, "semilla": 19088 },
  { "nombre": "CAR", "puntaje": 2800, "semilla": 55501 }
]
```

La semilla guardada permite que otros jugadores ingresen exactamente ese número al inicio del juego y jueguen el mismo mapa donde se obtuvo ese puntaje.

---

# FASE 6 — UI, Menús y Audio

> **Meta:** Menú principal navegable, HUD con información de juego en tiempo real, y audio mediante el mixer de Pygame.

---

## Paso 6.1 — HUD (Heads-Up Display)

**Qué hacer:**  
Crear `src/ui/hud.py` con la información visible durante el juego.

```python
# src/ui/hud.py

import pygame

class HUD:
    """
    Muestra en pantalla: vidas, puntaje, nivel, barra de progreso del laberinto.
    Se actualiza cada frame con los datos actuales del juego.
    """

    def __init__(self, ancho_ventana: int):
        self.ancho = ancho_ventana
        self.fuente_grande = pygame.font.Font(None, 36)
        self.fuente_pequeña = pygame.font.Font(None, 24)

    def dibujar(self, superficie: pygame.Surface,
                pacman, nivel: int, tablero) -> None:

        # ── Puntaje (arriba izquierda)
        txt_pts = self.fuente_grande.render(
            f"PUNTAJE: {pacman.puntaje}", True, (255, 255, 255))
        superficie.blit(txt_pts, (10, 8))

        # ── Nivel (arriba centro)
        txt_niv = self.fuente_grande.render(
            f"NIVEL {nivel}", True, (255, 220, 0))
        superficie.blit(txt_niv, (self.ancho // 2 - txt_niv.get_width() // 2, 8))

        # ── Vidas (arriba derecha, como círculos)
        for i in range(pacman.vidas):
            cx = self.ancho - 30 - i * 28
            pygame.draw.circle(superficie, (255, 220, 0), (cx, 20), 10)

        # ── Barra de progreso del laberinto (abajo)
        if tablero.total_puntos > 0:
            progreso = tablero.puntos_comidos / tablero.total_puntos
            ancho_barra = self.ancho - 40
            altura_barra = 8
            y_barra = superficie.get_height() - 20

            # Fondo gris
            pygame.draw.rect(superficie, (80, 80, 80),
                             (20, y_barra, ancho_barra, altura_barra))
            # Progreso amarillo
            pygame.draw.rect(superficie, (255, 220, 0),
                             (20, y_barra, int(ancho_barra * progreso), altura_barra))
```

---

## Paso 6.2 — Sistema de Audio

**Qué hacer:**  
Implementar `src/ui/audio.py` para gestionar música y efectos de sonido.

```python
# src/ui/audio.py

import pygame
import os


class AudioManager:
    """
    Gestiona dos canales de audio:
        Canal 0: Música de fondo (loop continuo, volumen bajo)
        Canal 1: Efectos de sonido cortos (comer, morir, subir nivel)
    """

    def __init__(self):
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        self.sonidos = {}
        self.musica_activa = False

    def cargar_sonidos(self) -> None:
        """Carga los archivos de audio desde assets/sonidos/."""
        nombres = ['comer', 'super_comer', 'morir', 'subir_nivel', 'comer_fantasma']
        for nombre in nombres:
            ruta = os.path.join('assets', 'sonidos', f'{nombre}.wav')
            if os.path.exists(ruta):
                self.sonidos[nombre] = pygame.mixer.Sound(ruta)
            else:
                print(f"[AUDIO] Advertencia: {ruta} no encontrado. Sin sonido para '{nombre}'.")

    def reproducir(self, nombre: str) -> None:
        """Reproduce un efecto de sonido en el canal 1."""
        if nombre in self.sonidos:
            pygame.mixer.Channel(1).play(self.sonidos[nombre])

    def iniciar_musica(self, ruta: str) -> None:
        """Inicia la música de fondo en loop."""
        if os.path.exists(ruta):
            pygame.mixer.music.load(ruta)
            pygame.mixer.music.set_volume(0.4)
            pygame.mixer.music.play(-1)   # -1 = loop infinito
            self.musica_activa = True

    def toggle_musica(self) -> None:
        """Activa/desactiva la música (para tecla M)."""
        if self.musica_activa:
            pygame.mixer.music.pause()
        else:
            pygame.mixer.music.unpause()
        self.musica_activa = not self.musica_activa
```

---

# FASE 7 — Documentación y Entrega Profesional

> **Meta:** Producir la evidencia académica que el profesor necesita para evaluar la librería PRNG y su integración con el juego.

---

## Paso 7.1 — Prueba de Monte Carlo con la Librería

**Qué hacer:**  
Crear `pruebas/test_montecarlo.py` que genera 10.000 puntos y verifica distribución uniforme.

```python
# pruebas/test_montecarlo.py
"""
Prueba de Monte Carlo con la librería PRNG.
Genera N puntos (x, y) en [0,1)² y verifica que se distribuyan uniformemente.
"""

from lib import GeneradorAleatorio
import math


def test_montecarlo(semilla: int = 42, n: int = 10_000) -> None:
    gen = GeneradorAleatorio(semilla=semilla, metodo='comb')
    gen.activar_historial()

    puntos = []
    for _ in range(n):
        x = gen.decimal(0, 1)
        y = gen.decimal(0, 1)
        puntos.append((x, y))

    # ── Test básico: ¿cuántos puntos caen dentro del círculo unidad?
    # Si la distribución es uniforme, la proporción ≈ π/4 ≈ 0.7854
    dentro = sum(1 for x, y in puntos if x**2 + y**2 <= 1)
    pi_aprox = 4 * dentro / n

    print(f"Puntos generados : {n}")
    print(f"Puntos en círculo: {dentro}")
    print(f"π aproximado     : {pi_aprox:.5f}")
    print(f"π real           : {math.pi:.5f}")
    print(f"Error relativo   : {abs(pi_aprox - math.pi) / math.pi * 100:.3f}%")

    # ── Test de uniformidad por cuadrantes
    cuadrantes = [0, 0, 0, 0]
    for x, y in puntos:
        q = (1 if x >= 0.5 else 0) + (2 if y >= 0.5 else 0)
        cuadrantes[q] += 1

    print("\nDistribución por cuadrantes (esperado ≈ 25% cada uno):")
    for i, c in enumerate(cuadrantes):
        print(f"  Cuadrante {i+1}: {c} puntos ({c/n*100:.1f}%)")

    stats = gen.estadisticas()
    print(f"\nEstadísticas globales:")
    print(f"  Media    : {stats['media']:.6f}  (esperada: {stats['media_esperada']})")
    print(f"  Varianza : {stats['varianza']:.6f}  (esperada: {stats['varianza_esperada']})")


if __name__ == '__main__':
    print("=" * 50)
    print("TEST MONTE CARLO — Librería PRNG")
    print("=" * 50)
    for metodo in ('mid', 'lcg', 'comb'):
        print(f"\n[{metodo.upper()}]")
        gen = GeneradorAleatorio(semilla=42, metodo=metodo)
        test_montecarlo.__globals__['gen'] = gen
        test_montecarlo(semilla=42, n=10_000)
```

---

## Paso 7.2 — README.md Profesional

**Qué hacer:**  
Escribir el `README.md` que el profesor verá primero al abrir el repositorio.

````markdown
# Pac-Man Roguelike

Proyecto académico — Ingeniería de Sistemas | Simulación

## Descripción
Implementación de Pac-Man con generación procedural de mapas, IA diferenciada
para los fantasmas, y una librería de generación de números pseudoaleatorios
desarrollada desde cero.

## Estructura del proyecto
```
pacman-roguelike/
├── lib/aleatorio.py      ← Librería PRNG (Midsquare, LCG, Combinado)
├── src/                  ← Código del juego
├── pruebas/              ← Tests estadísticos
└── datos/ranking.json    ← Ranking persistente
```

## Instalación y ejecución
```bash
git clone <url-del-repo>
cd pacman-roguelike
bash setup.sh
source venv/bin/activate
python src/main.py
```

## Librería PRNG — Fundamento académico
La aleatoriedad del juego proviene exclusivamente de `lib/aleatorio.py`.
Implementa tres algoritmos:

| Algoritmo | Referencia | Uso en el juego |
|---|---|---|
| Cuadrados Medios | Von Neumann (1940s) | Efectos visuales |
| Congruencial Lineal | Lehmer (1951), Hull-Dobell (1962) | IA de fantasmas |
| Combinado | Wichmann-Hill (1982) | Generación de mapas |

## Sistema de Seeds
Cada partida tiene una semilla numérica visible en el menú.
Compartir la semilla con otro jugador garantiza el mismo mapa.

## Controles
| Tecla | Acción |
|---|---|
| ↑ ↓ ← → | Mover Pac-Man |
| ESC | Pausar |
| M | Toggle música |
| Q (en pausa) | Menú principal |
````

---

## Paso 7.3 — Checklist de Entrega Final

Antes de entregar, verificar cada ítem:

**Librería PRNG:**
- [ ] `aleatorio.py` tiene docstrings con referencias a Hull-Dobell y Downham & Roberts
- [ ] Los tres métodos están implementados y probados
- [ ] `python aleatorio.py` imprime resultados correctos sin errores
- [ ] `pruebas/test_montecarlo.py` muestra π ≈ 3.14 y distribución uniforme por cuadrantes
- [ ] La reproducibilidad está demostrada (misma semilla = misma secuencia)

**Juego:**
- [ ] El mapa cambia con cada semilla diferente
- [ ] Los fantasmas tienen comportamientos distintos entre sí
- [ ] El ranking se guarda en `datos/ranking.json` correctamente
- [ ] El sistema de loot usa `gen.booleano()` de la librería propia
- [ ] El mezclado de power-ups usa `gen.mezclar()` de la librería propia

**Video de evidencia (3 escenas):**
- [ ] Escena 1: Consola ejecutando `python aleatorio.py` y mostrando los números
- [ ] Escena 2: El juego generando un mapa diferente al cambiar la semilla en el menú
- [ ] Escena 3: Los fantasmas moviéndose con comportamientos diferenciados

**Repositorio:**
- [ ] `README.md` explica la estructura y cómo ejecutar
- [ ] `requirements.txt` tiene las dependencias exactas
- [ ] `setup.sh` configura el entorno automáticamente
- [ ] `.gitignore` excluye `venv/` y `__pycache__/`

