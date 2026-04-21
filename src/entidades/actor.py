# src/entidades/actor.py

import pygame
from src.mundo.tablero import TAM_CELDA

class Actor:
    """
    Clase base para Pac-Man y los fantasmas.
    Implementa movimiento fluido basado en píxeles.
    """

    def __init__(self, fila: int, col: int, color: tuple, velocidad: float = 2.0):
        self.fila     = fila       # Celda lógica (destino o actual)
        self.col      = col
        self.color    = color
        self.velocidad = velocidad # Píxeles por frame

        # Dirección actual
        self.dir_fila = 0
        self.dir_col  = 0

        # Posición exacta en píxeles
        self.px = col * TAM_CELDA
        self.py = fila * TAM_CELDA
        
        # Objetivo en píxeles (donde queremos llegar)
        self.target_px = self.px
        self.target_py = self.py

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(self.px, self.py, TAM_CELDA, TAM_CELDA)

    def en_centro_celda(self) -> bool:
        """Retorna True si el actor ha llegado a su celda objetivo."""
        return self.px == self.target_px and self.py == self.target_py

    def mover(self, tablero, *args) -> None:
        """
        Maneja el desplazamiento fluido píxel a píxel.
        """
        # Si no hemos llegado al objetivo, nos seguimos moviendo hacia él
        if not self.en_centro_celda():
            if self.px < self.target_px: self.px = min(self.px + self.velocidad, self.target_px)
            elif self.px > self.target_px: self.px = max(self.px - self.velocidad, self.target_px)
            
            if self.py < self.target_py: self.py = min(self.py + self.velocidad, self.target_py)
            elif self.py > self.target_py: self.py = max(self.py - self.velocidad, self.target_py)
        
        # Si ya estamos en el centro, podemos iniciar un nuevo movimiento
        if self.en_centro_celda():
            self._decidir_siguiente_paso(tablero, *args)

    def _decidir_siguiente_paso(self, tablero, *args):
        """
        Calcula la siguiente celda objetivo basada en la dirección.
        Subclases como PacMan pueden cambiar la dirección aquí.
        """
        nueva_f = self.fila + self.dir_fila
        nueva_c = self.col + self.dir_col
        
        if not tablero.es_muro(nueva_f, nueva_c):
            self.fila = nueva_f
            self.col = nueva_c
            self.target_px = self.col * TAM_CELDA
            self.target_py = self.fila * TAM_CELDA

    def dibujar(self, superficie: pygame.Surface, offset_x: int = 0, offset_y: int = 0) -> None:
        x = offset_x + self.px
        y = offset_y + self.py
        centro = (x + TAM_CELDA // 2, y + TAM_CELDA // 2)
        pygame.draw.circle(superficie, self.color, centro, TAM_CELDA // 2 - 2)
