# src/entidades/fantasma.py

import pygame
from collections import deque
from .actor import Actor

# Estados de la FSM
MODO_CAOTICO    = 'caotico'
MODO_IMPLACABLE  = 'implacable'
MODO_ASUSTADO   = 'asustado'
MODO_RETIRADA   = 'retirada'

# Colores Especiales
COLOR_ASUSTADO = (50, 50, 200)   # Azul
COLOR_RETIRADA = (200, 200, 200) # Gris claro (ojos)

DIRECCIONES = [(-1, 0), (1, 0), (0, -1), (0, 1)] # N, S, O, E

class Fantasma(Actor):
    def __init__(self, fila, col, color, fila_base, col_base, velocidad=2.0):
        super().__init__(fila, col, color, velocidad=velocidad)
        self.fila_base = fila_base
        self.col_base = col_base
        self.color_orig = color
        self.estado_especial = None # 'asustado' o 'retirada'
        self.timer_especial = 0

    def asustar(self, duracion_frames=60*7):
        """Activa el modo asustado a menos que ya esté en retirada."""
        if self.estado_especial != MODO_RETIRADA:
            self.estado_especial = MODO_ASUSTADO
            self.timer_especial = duracion_frames
            # Al asustarse, suelen ir más lento
            self.velocidad = 1.0

    def ser_comido(self):
        """El fantasma es comido por Pac-Man."""
        self.estado_especial = MODO_RETIRADA
        self.timer_especial = 0
        self.velocidad = 4.0 # Vuelve rápido a la base

    def dibujar(self, superficie, offset_x=0, offset_y=0):
        # Guardar color original para restaurar
        original = self.color
        if self.estado_especial == MODO_ASUSTADO:
            self.color = COLOR_ASUSTADO
        elif self.estado_especial == MODO_RETIRADA:
            self.color = COLOR_RETIRADA
        
        super().dibujar(superficie, offset_x, offset_y)
        self.color = original

    def _obtener_ruta_bfs(self, tablero, destino_f, destino_c):
        inicio = (self.fila, self.col)
        objetivo = (destino_f, destino_c)
        if inicio == objetivo: return []
        cola = deque([(inicio, [])])
        visitados = {inicio}
        while cola:
            (f, c), camino = cola.popleft()
            if (f, c) == objetivo: return camino
            for df, dc in DIRECCIONES:
                nf, nc = f + df, c + dc
                if (nf, nc) not in visitados and not tablero.es_muro(nf, nc):
                    visitados.add((nf, nc))
                    cola.append(((nf, nc), camino + [(df, dc)]))
        return []

    def _manejar_estados_especiales(self, tablero):
        """Retorna True si el estado especial tomó el control del movimiento."""
        if self.estado_especial == MODO_ASUSTADO:
            self.timer_especial -= 1
            if self.timer_especial <= 0:
                self.estado_especial = None
                self.velocidad = 1.75 # Restaurar velocidad normal aprox
            else:
                # Movimiento errático (Aleatorio PRNG)
                opciones = [d for d in DIRECCIONES if not tablero.es_muro(self.fila + d[0], self.col + d[1]) and d != (-self.dir_fila, -self.dir_col)]
                if not opciones: opciones = [(-self.dir_fila, -self.dir_col)] if (self.dir_fila or self.dir_col) else DIRECCIONES
                # Nota: Aquí usamos una elección simple ya que la PRNG está en las subclases
                # pero para mantener consistencia, dejaremos que la subclase decida si es asustado
                return False 

        elif self.estado_especial == MODO_RETIRADA:
            # Ir a la base con BFS
            ruta = self._obtener_ruta_bfs(tablero, self.fila_base, self.col_base)
            if ruta:
                self.dir_fila, self.dir_col = ruta[0]
            else:
                self.estado_especial = None
                self.velocidad = 1.75
            
            if self.fila == self.fila_base and self.col == self.col_base:
                self.estado_especial = None
                self.velocidad = 1.75
            return True
        return False

class FantasmaAleatorio(Fantasma):
    def __init__(self, fila, col, fila_base, col_base, gen, color=(255, 50, 50)):
        super().__init__(fila, col, color, fila_base, col_base, velocidad=1.75)
        self.gen = gen

    def _decidir_siguiente_paso(self, tablero, *args):
        if self._manejar_estados_especiales(tablero):
            super()._decidir_siguiente_paso(tablero, *args)
            return

        # Si está asustado o normal, decide aleatoriamente
        opciones = [d for d in DIRECCIONES if not tablero.es_muro(self.fila + d[0], self.col + d[1]) and d != (-self.dir_fila, -self.dir_col)]
        if not opciones: opciones = [(-self.dir_fila, -self.dir_col)] if (self.dir_fila or self.dir_col) else DIRECCIONES
        self.dir_fila, self.dir_col = self.gen.elegir(opciones)
        super()._decidir_siguiente_paso(tablero, *args)

class FantasmaPerseguidor(Fantasma):
    PASOS_CAOTICO    = 20
    PASOS_IMPLACABLE = 15

    def __init__(self, fila, col, fila_base, col_base, gen):
        super().__init__(fila, col, (255, 100, 200), fila_base, col_base, velocidad=1.85)
        self.gen = gen
        self.modo_actual = MODO_CAOTICO
        self.timer_modo = 0
        self._ruta = []
        self._ultimo_target = None

    def _decidir_siguiente_paso(self, tablero, *args):
        if self._manejar_estados_especiales(tablero):
            super()._decidir_siguiente_paso(tablero, *args)
            return

        self.timer_modo += 1
        if self.modo_actual == MODO_CAOTICO and self.timer_modo >= self.PASOS_CAOTICO:
            self.modo_actual = MODO_IMPLACABLE
            self.timer_modo = 0
        elif self.modo_actual == MODO_IMPLACABLE and self.timer_modo >= self.PASOS_IMPLACABLE:
            self.modo_actual = MODO_CAOTICO
            self.timer_modo = 0

        pacman = args[0] if args else None
        retroceso = (-self.dir_fila, -self.dir_col)
        opciones = [d for d in DIRECCIONES if not tablero.es_muro(self.fila + d[0], self.col + d[1]) and d != retroceso]
        if not opciones: opciones = [retroceso] if (self.dir_fila or self.dir_col) else list(DIRECCIONES)

        if self.modo_actual == MODO_CAOTICO or self.estado_especial == MODO_ASUSTADO or not pacman:
            self.dir_fila, self.dir_col = self.gen.elegir(opciones)
        else:
            target_f = pacman.fila + pacman.dir_fila * 3
            target_c = pacman.col + pacman.dir_col * 3
            target_f = max(0, min(target_f, tablero.filas - 1))
            target_c = max(0, min(target_c, tablero.columnas - 1))
            if tablero.es_muro(target_f, target_c) or (pacman.dir_fila == 0 and pacman.dir_col == 0):
                target_f, target_c = pacman.fila, pacman.col

            if (target_f, target_c) != self._ultimo_target or not self._ruta:
                self._ruta = self._obtener_ruta_bfs(tablero, target_f, target_c)
                self._ultimo_target = (target_f, target_c)

            if self._ruta: self.dir_fila, self.dir_col = self._ruta.pop(0)
            else: self.dir_fila, self.dir_col = self.gen.elegir(opciones)

        super()._decidir_siguiente_paso(tablero, *args)

class FantasmaBlanco(FantasmaAleatorio):
    def __init__(self, fila, col, fila_base, col_base, gen):
        super().__init__(fila, col, fila_base, col_base, gen, color=(255, 255, 255))
