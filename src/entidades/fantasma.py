# src/entidades/fantasma.py

import pygame
from .actor import Actor

# Estados de la FSM
MODO_CAOTICO   = 'caotico'   # Se mueve al azar (PRNG)
MODO_IMPLACABLE = 'implacable' # Persigue directamente

DIRECCIONES = [(-1, 0), (1, 0), (0, -1), (0, 1)] # N, S, O, E

class Fantasma(Actor):
    """
    Clase base para fantasmas con soporte para dibujo y estados.
    """
    def __init__(self, fila, col, color, velocidad=2.0):
        super().__init__(fila, col, color, velocidad=velocidad)
        self.color_orig = color

    def dibujar(self, superficie, offset_x=0, offset_y=0):
        super().dibujar(superficie, offset_x, offset_y)

class FantasmaAleatorio(Fantasma):
    """
    Fantasma Rojo: Siempre caótico, usa PRNG para cada decisión.
    """
    def __init__(self, fila, col, fila_base, col_base, gen):
        super().__init__(fila, col, (255, 50, 50), velocidad=1.75)
        self.gen = gen

    def _decidir_siguiente_paso(self, tablero, *args):
        # 1. Buscar opciones válidas (no muros, no 180°)
        opciones = [d for d in DIRECCIONES if not tablero.es_muro(self.fila + d[0], self.col + d[1]) and d != (-self.dir_fila, -self.dir_col)]
        
        # 2. Si no hay opciones de avance, permitir retroceder (callejón)
        if not opciones:
            opciones = [(-self.dir_fila, -self.dir_col)] if self.dir_fila != 0 or self.dir_col != 0 else DIRECCIONES

        # 3. Elegir al azar con PRNG
        self.dir_fila, self.dir_col = self.gen.elegir(opciones)
        super()._decidir_siguiente_paso(tablero, *args)

class FantasmaPerseguidor(Fantasma):
    """
    Fantasma Rosa: Rota entre ser Caótico e Implacable.
    """
    def __init__(self, fila, col, fila_base, col_base, gen):
        super().__init__(fila, col, (255, 100, 200), velocidad=1.8)
        self.gen = gen
        self.modo_actual = MODO_CAOTICO
        self.timer_modo = 0
        
        # Tiempos de rotación (frames)
        self.DURACION_CAOTICO   = 60 * 8 # 10 segundos paseando
        self.DURACION_IMPLACABLE = 60 * 15  # 8 segundos de caza intensa (Actualizado)

    def _decidir_siguiente_paso(self, tablero, *args):
        self.timer_modo += 1
        pacman = args[0] if args else None

        # 1. Rotación de estados
        if self.modo_actual == MODO_CAOTICO and self.timer_modo >= self.DURACION_CAOTICO:
            self.modo_actual = MODO_IMPLACABLE
            self.timer_modo = 0
            print("[IA] Pinky entra en modo IMPLACABLE")
        elif self.modo_actual == MODO_IMPLACABLE and self.timer_modo >= self.DURACION_IMPLACABLE:
            self.modo_actual = MODO_CAOTICO
            self.timer_modo = 0
            print("[IA] Pinky vuelve a modo CAÓTICO")

        # 2. Obtener opciones de movimiento (evitando 180°)
        opciones = [d for d in DIRECCIONES if not tablero.es_muro(self.fila + d[0], self.col + d[1]) and d != (-self.dir_fila, -self.dir_col)]
        
        if not opciones:
            self.dir_fila, self.dir_col = -self.dir_fila, -self.dir_col
        else:
            if self.modo_actual == MODO_CAOTICO or not pacman:
                # Comportamiento Rojo (Aleatorio con PRNG)
                self.dir_fila, self.dir_col = self.gen.elegir(opciones)
            else:
                # Comportamiento Implacable (Distancia Manhattan)
                meta_f, meta_c = pacman.fila, pacman.col
                
                # Evaluar cada opción y elegir la que más acerque a Pac-Man
                mejor_dir = opciones[0]
                min_dist = 9999
                
                for d in opciones:
                    dist = abs(self.fila + d[0] - meta_f) + abs(self.col + d[1] - meta_c)
                    if dist < min_dist:
                        min_dist = dist
                        mejor_dir = d
                
                self.dir_fila, self.dir_col = mejor_dir

        super()._decidir_siguiente_paso(tablero, *args)
