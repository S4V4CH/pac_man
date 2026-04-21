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
        self._crear_ciclos(tablero, probabilidad=0.35)  # Aumentado de 0.15 a 0.35
        self._colocar_comida(tablero)
        self._colocar_super_pastillas(tablero)
        self._verificar_conectividad(tablero)

        return tablero

    # ── Paso 1.5: Crear Ciclos ───────────────────────────────────────────────
    def _crear_ciclos(self, tablero: Tablero, probabilidad: float) -> None:
        """
        Busca muros que separan dos pasillos y los elimina aleatoriamente
        para crear rutas alternativas (ciclos).
        """
        for f in range(2, tablero.filas - 2):
            for c in range(2, tablero.columnas - 2):
                if tablero.es_muro(f, c):
                    # Verificar si es un muro horizontal entre dos pasillos
                    if tablero.es_pasillo(f, c-1) and tablero.es_pasillo(f, c+1):
                        if self.gen.booleano(probabilidad):
                            tablero.establecer(f, c, PASILLO)
                    
                    # Verificar si es un muro vertical entre dos pasillos
                    elif tablero.es_pasillo(f-1, c) and tablero.es_pasillo(f+1, c):
                        if self.gen.booleano(probabilidad):
                            tablero.establecer(f, c, PASILLO)

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

        # Mezclar callejones y tomar los primeros 4 usando la librería PRNG
        callejones_mezclados = self.gen.mezclar(callejones)
        for f, c in callejones_mezclados[:4]:
            tablero.establecer(f, c, SUPER_PUNTO)

    # ── Paso 4: Verificar conectividad ───────────────────────────────────────
    def _verificar_conectividad(self, tablero: Tablero) -> None:
        """
        Usa Flood Fill para eliminar zonas aisladas y garantizar que Pac-Man
        pueda llegar a todos los puntos.
        """
        inicio = None
        for f in range(tablero.filas):
            for c in range(tablero.columnas):
                if tablero.es_pasillo(f, c):
                    inicio = (f, c)
                    break
            if inicio:
                break

        if not inicio:
            return

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

        aisladas = 0
        for f in range(tablero.filas):
            for c in range(tablero.columnas):
                if tablero.es_pasillo(f, c) and (f, c) not in visitados:
                    tablero.establecer(f, c, MURO)
                    tablero.total_puntos -= 1
                    aisladas += 1

        if aisladas > 0:
            print(f"[INFO] Flood Fill eliminó {aisladas} celdas aisladas.")
