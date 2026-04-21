# src/mundo/tablero.py

import pygame

# ─── Tipos de celda ────────────────────────────────────────────────────────────
MURO        = 0
PASILLO     = 1
PUNTO       = 2   # Punto normal (+10 pts)
SUPER_PUNTO = 3   # Super pastilla (activa modo asustado en fantasmas)
VACIO       = 4   # Pasillo sin comida (ya comido)

# ─── Configuración Visual ──────────────────────────────────────────────────────
TAM_CELDA = 28

# Colores
COLOR_MURO        = (30,  30, 100)
COLOR_PASILLO     = (10,  10,  30)
COLOR_PUNTO       = (255, 200,   0)
COLOR_SUPER_PUNTO = (255, 100, 100)


class Tablero:
    """
    Representa el laberinto como una matriz de enteros.
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

    def dibujar(self, superficie: pygame.Surface,
                offset_x: int = 0, offset_y: int = 0) -> None:
        """
        Dibuja el tablero completo en la superficie de Pygame.
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
                    # Círculo más grande
                    centro = (x + TAM_CELDA // 2, y + TAM_CELDA // 2)
                    pygame.draw.circle(superficie, COLOR_SUPER_PUNTO, centro, 7)

    def __repr__(self) -> str:
        simbolos = {MURO: '█', PASILLO: ' ', PUNTO: '·', SUPER_PUNTO: '●', VACIO: ' '}
        filas = []
        for fila in self.celdas:
            filas.append(''.join(simbolos.get(c, '?') for c in fila))
        return '\n'.join(filas)
