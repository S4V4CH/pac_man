# src/entidades/pacman.py

import pygame
from .actor import Actor

class PacMan(Actor):
    """
    Pac-Man con movimiento fluido y buffer de dirección.
    """

    def __init__(self, fila: int, col: int):
        # velocidad = 2 píxeles por frame. 
        # TAM_CELDA (28) / 2 = 14 frames por celda. Muy equilibrado.
        super().__init__(fila, col, color=(255, 220, 0), velocidad=2.0)
        self.puntaje    = 0
        self.vidas      = 3
        self.invencible = False

        # Dirección que el jugador quiere tomar
        self.next_dir_f = 0
        self.next_dir_c = 0

    def manejar_teclado(self, evento: pygame.event.Event) -> None:
        if evento.type == pygame.KEYDOWN:
            if evento.key in (pygame.K_UP,    pygame.K_w): self.next_dir_f, self.next_dir_c = -1, 0
            if evento.key in (pygame.K_DOWN,  pygame.K_s): self.next_dir_f, self.next_dir_c = 1, 0
            if evento.key in (pygame.K_LEFT,  pygame.K_a): self.next_dir_f, self.next_dir_c = 0, -1
            if evento.key in (pygame.K_RIGHT, pygame.K_d): self.next_dir_f, self.next_dir_c = 0, 1

    def _decidir_siguiente_paso(self, tablero, *args):
        """
        Se ejecuta cada vez que Pac-Man llega al centro de una celda.
        """
        # 1. Intentar comer lo que hay en la celda actual
        puntos, es_super = tablero.comer_punto(self.fila, self.col)
        self.puntaje += puntos
        if es_super:
            self.invencible = True

        # 2. ¿Podemos girar hacia donde el jugador quiere? (RESTAURADO)
        if not tablero.es_muro(self.fila + self.next_dir_f, self.col + self.next_dir_c):
            self.dir_fila = self.next_dir_f
            self.dir_col  = self.next_dir_c
        
        # 3. Seguir moviéndose si no hay muro enfrente
        super()._decidir_siguiente_paso(tablero, *args)

    def morir(self) -> None:
        self.vidas -= 1
        self.invencible = False
