# src/entidades/fantasma.py

import math
import pygame
from collections import deque
from .actor import Actor
from src.mundo.tablero import TAM_CELDA

# Estados de la FSM
MODO_CAOTICO    = 'caotico'
MODO_IMPLACABLE  = 'implacable'
MODO_ASUSTADO   = 'asustado'
MODO_RETIRADA   = 'retirada'

# Azul Namco (mismo tono que muros); parpadeo blanco al final del miedo
COLOR_ASUSTADO = (33, 33, 222)
COLOR_RETIRADA = (200, 200, 200)  # reservado / ojos
COLOR_OJO_BLANCO = (255, 255, 255)
COLOR_PUPILA = (33, 33, 222)

DIRECCIONES = [(-1, 0), (1, 0), (0, -1), (0, 1)] # N, S, O, E

# Color del emboscador (FantasmaBlanco): morado — los de Fiebre del Oro son dorados/naranjas
COLOR_EMBOSCADOR = (165, 95, 230)

# 10 s a 60 FPS — el temporizador se decrementa cada frame en mover()
DURACION_ASUSTADO_FRAMES = 60 * 10
# Tras volver a modo normal o al llegar a la base, no dañan al jugador unos instantes
TICKS_GRACIA_TRAS_ESTADO = 45
# Máximo tiempo regresando a la base (5 s a 60 FPS)
MAX_FRAMES_RETIRADA = 60 * 5


class Fantasma(Actor):
    def __init__(self, fila, col, color, fila_base, col_base, velocidad=2.0):
        super().__init__(fila, col, color, velocidad=velocidad)
        self.fila_base = fila_base
        self.col_base = col_base
        self.color_orig = color
        self.estado_especial = None # 'asustado' o 'retirada'
        self.timer_especial = 0
        self._velocidad_normal = velocidad
        self._ticks_gracia_danio = 0
        self._frames_retirada = 0
        # Identidad roguelike (Fase 4): distintivo dibujado sobre la cabeza
        self.marca_rol = ''
        # ── Sistemas de mejoras roguelike ──
        self.congelado: bool = False        # Congelador Pasivo
        self.es_fiebre_oro: bool = False    # Fiebre del Oro (desaparece al ser comido)
        # Caducidad de los 15 fantasmas etéreos (independiente de estado_asustado / muerte)
        self.timer_fiebre_oro: int = 0

    def _teleportar_a_base(self) -> None:
        self.fila, self.col = self.fila_base, self.col_base
        self.px = self.col * TAM_CELDA
        self.py = self.fila * TAM_CELDA
        self.target_px, self.target_py = self.px, self.py
        self.estado_especial = None
        self.velocidad = self._velocidad_normal
        self._ticks_gracia_danio = TICKS_GRACIA_TRAS_ESTADO
        self._frames_retirada = 0

    def mover(self, tablero, *args) -> None:
        if self._ticks_gracia_danio > 0:
            self._ticks_gracia_danio -= 1
        # Fiebre del oro: el tiempo de vida corre siempre (aun tras reposición al morir)
        if self.es_fiebre_oro and self.timer_fiebre_oro > 0:
            self.timer_fiebre_oro -= 1
        if self.es_fiebre_oro and self.estado_especial == MODO_ASUSTADO:
            self.timer_especial = self.timer_fiebre_oro
        if self.estado_especial == MODO_ASUSTADO and not self.es_fiebre_oro:
            self.timer_especial -= 1
            if self.timer_especial <= 0:
                self.estado_especial = None
                self.velocidad = self._velocidad_normal
                self._ticks_gracia_danio = TICKS_GRACIA_TRAS_ESTADO
        if self.estado_especial == MODO_RETIRADA:
            self._frames_retirada += 1
            if self._frames_retirada >= MAX_FRAMES_RETIRADA:
                self._teleportar_a_base()
        else:
            self._frames_retirada = 0
        # ── Congelador Pasivo: no mover si está congelado ──
        if self.congelado:
            return
        super().mover(tablero, *args)

    def puede_danar_jugador(self) -> bool:
        """Solo hostil sin gracia: no en retirada ni asustado, y no justo tras cambiar de estado."""
        if self.estado_especial is not None:
            return False
        return self._ticks_gracia_danio <= 0

    def asustar(self, duracion_frames: int = DURACION_ASUSTADO_FRAMES):
        """Activa o renueva el modo asustado (super pastilla) salvo que esté en retirada."""
        if self.es_fiebre_oro:
            return
        if self.estado_especial != MODO_RETIRADA:
            self.estado_especial = MODO_ASUSTADO
            self.timer_especial = duracion_frames
            self.velocidad = 1.0

    def ser_comido(self):
        """El fantasma es comido por Pac-Man."""
        self.estado_especial = MODO_RETIRADA
        self.timer_especial = 0
        self.velocidad = 4.0  # Vuelve rápido a la base
        self._frames_retirada = 0

    def _dibujar_cuerpo_arcade(self, surf: pygame.Surface, cx: int, cy: int, color: tuple) -> None:
        """Silueta clásica: cabeza redonda, cuerpo y tres pies ondulados."""
        r = TAM_CELDA // 2 - 3
        head_cy = cy - 3
        pygame.draw.circle(surf, color, (cx, head_cy), r)
        h_rect = r + 1
        pygame.draw.rect(surf, color, pygame.Rect(cx - r, head_cy, 2 * r, h_rect))
        foot_r = max(3, r // 3) + 1
        base_y = head_cy + h_rect
        for fx in (cx - r + foot_r + 1, cx, cx + r - foot_r - 1):
            pygame.draw.circle(surf, color, (fx, base_y), foot_r)
        # Contorno para separar del fondo / muros
        pygame.draw.circle(surf, (0, 0, 0), (cx, head_cy), r, 1)
        pygame.draw.rect(surf, (0, 0, 0), pygame.Rect(cx - r, head_cy, 2 * r, h_rect), 1)

    def _dibujar_ojos_normales(self, surf: pygame.Surface, cx: int, cy: int, df: int, dc: int) -> None:
        head_cy = cy - 6
        sep = 5
        ew, eh = 5, 6
        pdx = 2 if dc > 0 else (-2 if dc < 0 else 0)
        pdy = 2 if df > 0 else (-2 if df < 0 else 0)
        for ox in (-sep, sep):
            rx = cx + ox - ew // 2
            ry = head_cy - eh // 2
            pygame.draw.ellipse(surf, COLOR_OJO_BLANCO, pygame.Rect(rx, ry, ew, eh))
            pygame.draw.circle(
                surf,
                COLOR_PUPILA,
                (cx + ox + pdx, head_cy + pdy),
                2,
            )

    def _dibujar_ojos_asustado(self, surf: pygame.Surface, cx: int, cy: int) -> None:
        """Ojos pequeños tipo recreativa (fantasma asustado)."""
        head_cy = cy - 5
        sep = 5
        for ox in (-sep, sep):
            pygame.draw.rect(surf, COLOR_OJO_BLANCO, pygame.Rect(cx + ox - 2, head_cy - 2, 4, 5))
            pygame.draw.line(surf, COLOR_PUPILA, (cx + ox - 1, head_cy + 1), (cx + ox + 1, head_cy + 2), 1)

    def _dibujar_ojos_retirada(self, surf: pygame.Surface, cx: int, cy: int, df: int, dc: int) -> None:
        """Solo ojos volviendo a la base (estilo clásico)."""
        head_cy = cy - 2
        sep = 7
        ew, eh = 7, 8
        pdx = 2 if dc > 0 else (-2 if dc < 0 else 0)
        pdy = 2 if df > 0 else (-2 if df < 0 else 0)
        for ox in (-sep, sep):
            rx = cx + ox - ew // 2
            ry = head_cy - eh // 2
            pygame.draw.ellipse(surf, COLOR_OJO_BLANCO, pygame.Rect(rx, ry, ew, eh))
            pygame.draw.circle(surf, COLOR_PUPILA, (cx + ox + pdx, head_cy + pdy), 3)

    def dibujar(self, superficie, offset_x=0, offset_y=0):
        cx = offset_x + self.px + TAM_CELDA // 2
        cy = offset_y + self.py + TAM_CELDA // 2
        df, dc = self.dir_fila, self.dir_col

        if self.estado_especial == MODO_RETIRADA:
            self._dibujar_ojos_retirada(superficie, cx, cy, df, dc)
            return

        if self.estado_especial == MODO_ASUSTADO:
            cuerpo = COLOR_ASUSTADO
            if not self.es_fiebre_oro:
                if self.timer_especial < 180 and (self.timer_especial // 12) % 2 == 0:
                    cuerpo = (255, 255, 255)
            else:
                # Fiebre del Oro: parpadeo dorado
                t = pygame.time.get_ticks()
                if (t // 150) % 2 == 0:
                    cuerpo = (255, 200, 0)
                else:
                    cuerpo = (255, 140, 0)
            self._dibujar_cuerpo_arcade(superficie, cx, cy, cuerpo)
            self._dibujar_ojos_asustado(superficie, cx, cy)
            # Indicador dorado para fantasmas de fiebre
            if self.es_fiebre_oro:
                self._dibujar_corona_fiebre(superficie, cx, cy)
            return

        self._dibujar_cuerpo_arcade(superficie, cx, cy, self.color_orig)
        self._dibujar_ojos_normales(superficie, cx, cy, df, dc)
        self._dibujar_distintivo_rol(superficie, cx, cy)

        # ── Overlay de hielo si está congelado ──
        if self.congelado:
            self._dibujar_overlay_hielo(superficie, cx, cy)

    def _dibujar_distintivo_rol(self, surf: pygame.Surface, cx: int, cy: int) -> None:
        """Marca visual por tipo de IA (aleatorio / cazador / emboscador)."""
        if not self.marca_rol:
            return
        r = TAM_CELDA // 2 - 3
        head_cy = cy - 3
        mx, my = cx, head_cy - r - 5
        if self.marca_rol == 'rnd':
            pygame.draw.line(surf, (255, 255, 220), (mx, my - 2), (mx, my + 3), 2)
            pygame.draw.circle(surf, (255, 255, 160), (mx, my - 3), 2)
        elif self.marca_rol == 'caz':
            pts = [(mx, my - 5), (mx + 5, my), (mx, my + 2), (mx - 5, my)]
            pygame.draw.polygon(surf, (255, 220, 80), pts, width=2)
        elif self.marca_rol == 'emb':
            pygame.draw.lines(surf, (60, 40, 20), False, [(mx - 6, my), (mx, my - 6), (mx + 6, my)], 2)

    def _dibujar_overlay_hielo(self, surf, cx: int, cy: int) -> None:
        """Dibuja cristales de hielo sobre el fantasma congelado."""
        r = TAM_CELDA // 2 - 1
        ice_surf = pygame.Surface((r * 2 + 4, r * 2 + 4), pygame.SRCALPHA)
        pygame.draw.circle(ice_surf, (180, 230, 255, 100), (r + 2, r + 2), r)
        surf.blit(ice_surf, (cx - r - 2, cy - r - 2))
        # Copos de nieve pequeños
        for i in range(4):
            ang = math.radians(i * 90 + 45)
            sx = int(cx + r * 0.55 * math.cos(ang))
            sy = int(cy + r * 0.55 * math.sin(ang))
            pygame.draw.circle(surf, (200, 240, 255), (sx, sy), 2)
        # Cruz central
        pygame.draw.line(surf, (220, 245, 255), (cx - 5, cy), (cx + 5, cy), 1)
        pygame.draw.line(surf, (220, 245, 255), (cx, cy - 5), (cx, cy + 5), 1)

    def _dibujar_corona_fiebre(self, surf, cx: int, cy: int) -> None:
        """Dibuja una pequeña corona dorada sobre fantasmas de fiebre del oro."""
        r = TAM_CELDA // 2 - 3
        head_cy = cy - 3
        # Tres puntitas doradas
        pts_corona = [
            (cx - 8, head_cy - r - 2),
            (cx - 5, head_cy - r - 7),
            (cx - 2, head_cy - r - 3),
            (cx, head_cy - r - 8),
            (cx + 2, head_cy - r - 3),
            (cx + 5, head_cy - r - 7),
            (cx + 8, head_cy - r - 2),
        ]
        pygame.draw.lines(surf, (255, 215, 0), False, pts_corona, 2)

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
            # El temporizador del miedo se actualiza en mover() cada frame
            return False

        if self.estado_especial == MODO_RETIRADA:
            ruta = self._obtener_ruta_bfs(tablero, self.fila_base, self.col_base)
            if ruta:
                self.dir_fila, self.dir_col = ruta[0]
            else:
                self.estado_especial = None
                self.velocidad = self._velocidad_normal
                self._ticks_gracia_danio = TICKS_GRACIA_TRAS_ESTADO
                self._frames_retirada = 0

            if self.fila == self.fila_base and self.col == self.col_base:
                self.estado_especial = None
                self.velocidad = self._velocidad_normal
                self._ticks_gracia_danio = TICKS_GRACIA_TRAS_ESTADO
                self._frames_retirada = 0
            return True
        return False

class FantasmaAleatorio(Fantasma):
    def __init__(self, fila, col, fila_base, col_base, gen, color=(222, 33, 33)):
        super().__init__(fila, col, color, fila_base, col_base, velocidad=1.75)
        self.gen = gen
        self.marca_rol = 'rnd'

    def _decidir_siguiente_paso(self, tablero, *args):
        if self._manejar_estados_especiales(tablero):
            super()._decidir_siguiente_paso(tablero, *args)
            return

        pacman = args[0] if args else None
        # Fiebre del oro: huir del jugador (maximizar distancia Manhattan en un paso)
        if self.es_fiebre_oro and self.estado_especial == MODO_ASUSTADO and pacman:
            opciones = [
                d for d in DIRECCIONES
                if not tablero.es_muro(self.fila + d[0], self.col + d[1])
                and d != (-self.dir_fila, -self.dir_col)
            ]
            if not opciones:
                opciones = [(-self.dir_fila, -self.dir_col)] if (self.dir_fila or self.dir_col) else list(DIRECCIONES)
            mejor_dist = -1
            mejores: list = []
            for d in opciones:
                nf, nc = self.fila + d[0], self.col + d[1]
                dist = abs(nf - pacman.fila) + abs(nc - pacman.col)
                if dist > mejor_dist:
                    mejor_dist = dist
                    mejores = [d]
                elif dist == mejor_dist:
                    mejores.append(d)
            self.dir_fila, self.dir_col = self.gen.elegir(mejores)
            super()._decidir_siguiente_paso(tablero, *args)
            return

        # Si está asustado (normal) o en modo aleatorio, decide al azar
        opciones = [d for d in DIRECCIONES if not tablero.es_muro(self.fila + d[0], self.col + d[1]) and d != (-self.dir_fila, -self.dir_col)]
        if not opciones: opciones = [(-self.dir_fila, -self.dir_col)] if (self.dir_fila or self.dir_col) else DIRECCIONES
        self.dir_fila, self.dir_col = self.gen.elegir(opciones)
        super()._decidir_siguiente_paso(tablero, *args)

class FantasmaPerseguidor(Fantasma):
    PASOS_CAOTICO    = 20
    PASOS_IMPLACABLE = 15

    def __init__(self, fila, col, fila_base, col_base, gen):
        # Ligeramente por debajo de Pac-Man (2.0); el evento de división sube velocidad con tope global
        super().__init__(fila, col, (255, 181, 255), fila_base, col_base, velocidad=1.78)
        self.gen = gen
        self.modo_actual = MODO_CAOTICO
        self.timer_modo = 0
        self._ruta = []
        self._ultimo_target = None
        self.marca_rol = 'caz'

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


class FantasmaEmboscador(Fantasma):
    """
    Emboscador (Fase 4): lejos corta camino hacia ~4 celdas delante de Pac-Man;
    cerca se vuelve tímido (estilo Clyde) usando el PRNG.
    """

    PASOS_CAOTICO = 22
    PASOS_IMPLACABLE = 16
    DIST_MANHATTAN_TIMIDO = 8

    def __init__(self, fila, col, fila_base, col_base, gen):
        super().__init__(fila, col, COLOR_EMBOSCADOR, fila_base, col_base, velocidad=1.8)
        self.gen = gen
        self.modo_actual = MODO_CAOTICO
        self.timer_modo = 0
        self._ruta: list = []
        self._ultimo_target = None
        self.marca_rol = 'emb'

    @staticmethod
    def _meta_embesque(tablero, pacman) -> tuple[int, int]:
        tf = pacman.fila + pacman.dir_fila * 4
        tc = pacman.col + pacman.dir_col * 4
        tf = max(0, min(tf, tablero.filas - 1))
        tc = max(0, min(tc, tablero.columnas - 1))
        if tablero.es_muro(tf, tc) or (pacman.dir_fila == 0 and pacman.dir_col == 0):
            return pacman.fila, pacman.col
        return tf, tc

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
        if not opciones:
            opciones = [retroceso] if (self.dir_fila or self.dir_col) else list(DIRECCIONES)

        if self.modo_actual == MODO_CAOTICO or self.estado_especial == MODO_ASUSTADO or not pacman:
            self._ruta = []
            self._ultimo_target = None
            self.dir_fila, self.dir_col = self.gen.elegir(opciones)
        else:
            dist = abs(self.fila - pacman.fila) + abs(self.col - pacman.col)
            if dist >= self.DIST_MANHATTAN_TIMIDO:
                tf, tc = self._meta_embesque(tablero, pacman)
                if (tf, tc) != self._ultimo_target or not self._ruta:
                    self._ruta = self._obtener_ruta_bfs(tablero, tf, tc)
                    self._ultimo_target = (tf, tc)
                if self._ruta:
                    self.dir_fila, self.dir_col = self._ruta.pop(0)
                else:
                    self.dir_fila, self.dir_col = self.gen.elegir(opciones)
            else:
                self._ruta = []
                self._ultimo_target = None
                self.dir_fila, self.dir_col = self.gen.elegir(opciones)

        super()._decidir_siguiente_paso(tablero, *args)


class FantasmaBlanco(FantasmaEmboscador):
    """Emboscador (antes naranja; ahora morado para no confundir con Fiebre del Oro)."""

    pass
