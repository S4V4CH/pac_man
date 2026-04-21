# Pac-Man Roguelike

Proyecto académico — Ingeniería de Sistemas | Simulación

## Descripción

Implementación de un Pac-Man con generación procedural de mapas, fantasmas con comportamientos diferenciados, sistema de mejoras tipo roguelike, tienda y ranking persistente. La aleatoriedad del juego se apoya en una **librería PRNG propia** (`lib/aleatorio.py`) con tres métodos documentados: Cuadrados Medios, Generador Congruencial Lineal (Hull-Dobell) y generador combinado estilo Wichmann–Hill.

## Requisitos

- Python 3.10 o superior
- Dependencias en `requirements.txt` (principalmente Pygame 2.6.x)

## Instalación

### Windows (PowerShell)

```powershell
cd pac_man
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Linux / macOS / Git Bash

```bash
cd pac_man
bash setup.sh
source .venv/bin/activate
```

## Ejecución

Desde la **raíz del repositorio** (carpeta `pac_man`):

```bash
python src/main.py
```

El script añade automáticamente el directorio padre al `sys.path` para importar `lib/` y `src/`.

## Estructura del proyecto

```
pac_man/
├── lib/
│   ├── aleatorio.py      # Librería PRNG (mid / lcg / comb)
│   └── __init__.py
├── src/
│   ├── main.py             # Bucle principal y máquina de estados
│   ├── mundo/              # Tablero, generador de mapa
│   ├── entidades/          # Pac-Man, fantasmas (IA)
│   ├── sistemas/           # Loot, ranking, tienda, mejoras
│   └── ui/                 # Menús, HUD, audio
├── datos/
│   ├── ranking.json        # Puntuaciones (opcional; puede generarse al jugar)
│   └── tienda.json         # Estado de la meta-progresión de tienda
├── pruebas/
│   └── test_montecarlo.py  # Evidencia estadística (Monte Carlo)
├── assets/                 # Sprites y sonidos
├── requirements.txt
└── setup.sh
```

## Librería PRNG — Resumen académico

| Método      | Referencia clásica        | Uso típico en el proyecto   |
|------------|-----------------------------|-----------------------------|
| `mid`      | Von Neumann / Metropolis    | Histórico; no es el default del juego |
| `lcg`      | Lehmer; periodo Hull-Dobell | Alternativa rápida y estable |
| `comb`     | Combinación tipo Wichmann–Hill | **Default** al iniciar partida (`main.py`) |

La **semilla** introducida en el menú determina el mismo tablero y la misma secuencia de decisiones aleatorias para quien repita esa semilla (reproducibilidad tipo roguelike).

## Controles (referencia rápida)

| Entrada        | Acción |
|----------------|--------|
| Flechas        | Movimiento de Pac-Man |
| ESC            | Pausa |
| M              | Silenciar / reanudar música (si está disponible) |

Los detalles completos aparecen en el menú **Controles** del juego.

## Prueba Monte Carlo

```bash
python pruebas/test_montecarlo.py
```

Genera 10 000 puntos por método (`mid`, `lcg`, `comb`), estima pi por área del cuarto de círculo y muestra la distribución por cuadrantes. Con algunas semillas, `mid` puede degenerar (comportamiento documentado en `INFORME-FASE7-DOCUMENTACION.md`); `lcg` y `comb` suelen aproximar pi con error pequeño.

## Documentación ampliada

- `INFORME-FASE7-DOCUMENTACION.md` — informe académico, checklist de entrega y relación con `desarrollo-pacman.md`.
- `docs/LIBRERIA-PRNG-USOS-Y-CODIGO.md` — listado técnico de cada uso de la librería PRNG (rutas, métodos y fragmentos).
- `docs/LIBRERIA-PRNG-EXPLICACION-SENCILLA.md` — misma información en lenguaje de exposición, con **rangos de líneas** por archivo para cada ejemplo.
