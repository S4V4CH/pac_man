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

# Paleta estilo Pac-Man arcade (Namco): muros azul eléctrico, pasillo negro, pellets blancos
COLOR_MURO_BASE   = (33, 33, 222)   # #2121de aprox.
COLOR_MURO_LUZ    = (100, 100, 255)
COLOR_MURO_SOMBRA = (16, 16, 120)
COLOR_PASILLO     = (0, 0, 0)
COLOR_PUNTO       = (255, 255, 255)
COLOR_SUPER_PUNTO = (255, 255, 220)
COLOR_MURO        = COLOR_MURO_BASE  # compatibilidad con código que use COLOR_MURO


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

    def comer_punto(self, fila: int, col: int) -> tuple[int, bool]:
        """
        Intenta comer el punto en (fila, col).
        Retorna (puntos obtenidos, es_super_punto).
        """
        celda = self.obtener(fila, col)
        if celda == PUNTO:
            self.establecer(fila, col, VACIO)
            self.puntos_comidos += 1
            return 10, False
        if celda == SUPER_PUNTO:
            self.establecer(fila, col, VACIO)
            self.puntos_comidos += 1
            return 50, True
        return 0, False

    def quedan_pellets(self) -> bool:
        """True si aún hay puntos normales o super pastillas en la rejilla (fuente de verdad)."""
        for f in range(self.filas):
            for c in range(self.columnas):
                v = self.celdas[f][c]
                if v == PUNTO or v == SUPER_PUNTO:
                    return True
        return False

    @property
    def completado(self) -> bool:
        """Nivel terminado cuando no queda comida en el mapa (no solo contadores)."""
        return not self.quedan_pellets()

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
                    pygame.draw.rect(superficie, COLOR_MURO_BASE, rect)
                    # Relieve tipo 16 bits: brillo arriba/izq, sombra abajo/dcha
                    pygame.draw.line(superficie, COLOR_MURO_LUZ, rect.topleft, rect.topright, 2)
                    pygame.draw.line(superficie, COLOR_MURO_LUZ, rect.topleft, rect.bottomleft, 2)
                    pygame.draw.line(superficie, COLOR_MURO_SOMBRA, rect.bottomleft, rect.bottomright, 2)
                    pygame.draw.line(superficie, COLOR_MURO_SOMBRA, rect.topright, rect.bottomright, 2)

                elif celda in (PASILLO, VACIO):
                    pygame.draw.rect(superficie, COLOR_PASILLO, rect)

                elif celda == PUNTO:
                    pygame.draw.rect(superficie, COLOR_PASILLO, rect)
                    centro = (x + TAM_CELDA // 2, y + TAM_CELDA // 2)
                    pygame.draw.circle(superficie, COLOR_PUNTO, centro, 2)
                    pygame.draw.circle(superficie, (220, 220, 255), centro, 1)

                elif celda == SUPER_PUNTO:
                    pygame.draw.rect(superficie, COLOR_PASILLO, rect)
                    centro = (x + TAM_CELDA // 2, y + TAM_CELDA // 2)
                    # Parpadeo tipo recreativa (grande / pequeño)
                    pulso = (pygame.time.get_ticks() // 200) % 2
                    r = 7 if pulso else 5
                    pygame.draw.circle(superficie, COLOR_SUPER_PUNTO, centro, r)
                    pygame.draw.circle(superficie, (255, 255, 255), centro, r - 2)

    def __repr__(self) -> str:
        simbolos = {MURO: '█', PASILLO: ' ', PUNTO: '·', SUPER_PUNTO: '●', VACIO: ' '}
        filas = []
        for fila in self.celdas:
            filas.append(''.join(simbolos.get(c, '?') for c in fila))
        return '\n'.join(filas)
