# src/entidades/pacman.py

import math
import pygame
from src.mundo.tablero import TAM_CELDA
from .actor import Actor

FRAMES_ANIMACION_MUERTE = 75

# Amarillo arcade Namco + reflejo
COLOR_PAC_CUERPO = (255, 237, 0)
COLOR_PAC_BORDE = (200, 170, 0)
COLOR_PAC_BRILLO = (255, 255, 160)


class PacMan(Actor):
    """
    Pac-Man con movimiento fluido y buffer de dirección.
    """

    def __init__(self, fila: int, col: int):
        # velocidad base = 2 píxeles por frame.
        super().__init__(fila, col, color=(255, 237, 0), velocidad=2.0)
        self._velocidad_base: float = 2.0
        self.puntaje = 0
        self.vidas = 3
        self.invencible = False

        self.next_dir_f = 0
        self.next_dir_c = 0
        self._muerte_activa = False
        self._escala_muerte = 1.0

        # ── Mejoras roguelike ──
        self.modo_fantasma: bool = False   # Atravesar paredes (Modo Fantasma)
        # Lo asigna main cada frame según SistemaMejoras (escudo listo para absorber golpe)
        self.escudo_activo_visual: bool = False

    def aplicar_velocidad_bonus(self, multiplicador: float) -> None:
        """Actualiza la velocidad según el bonus total (tienda + botas de run)."""
        self.velocidad = self._velocidad_base * max(1.0, multiplicador)

    def iniciar_animacion_muerte(self) -> None:
        self._muerte_activa = True
        self._escala_muerte = 1.0

    def tick_animacion_muerte(self) -> bool:
        if not self._muerte_activa:
            return False
        self._escala_muerte -= 1.0 / FRAMES_ANIMACION_MUERTE
        if self._escala_muerte <= 0:
            self._escala_muerte = 0.0
            self._muerte_activa = False
            return True
        return False

    def reiniciar_despues_muerte(self) -> None:
        self._muerte_activa = False
        self._escala_muerte = 1.0

    def manejar_teclado(self, evento: pygame.event.Event) -> None:
        if evento.type == pygame.KEYDOWN:
            if evento.key in (pygame.K_UP, pygame.K_w):
                self.next_dir_f, self.next_dir_c = -1, 0
            if evento.key in (pygame.K_DOWN, pygame.K_s):
                self.next_dir_f, self.next_dir_c = 1, 0
            if evento.key in (pygame.K_LEFT, pygame.K_a):
                self.next_dir_f, self.next_dir_c = 0, -1
            if evento.key in (pygame.K_RIGHT, pygame.K_d):
                self.next_dir_f, self.next_dir_c = 0, 1

    def _decidir_siguiente_paso(self, tablero, *args):
        puntos, es_super = tablero.comer_punto(self.fila, self.col)
        self.puntaje += puntos
        if es_super:
            self.invencible = True

        if self.modo_fantasma:
            # En modo fantasma: cambiar dirección siempre (ignorar muros)
            nf = self.fila + self.next_dir_f
            nc = self.col + self.next_dir_c
            if 0 <= nf < tablero.filas and 0 <= nc < tablero.columnas:
                self.dir_fila = self.next_dir_f
                self.dir_col = self.next_dir_c
            # Moverse ignorando muros
            nueva_f = self.fila + self.dir_fila
            nueva_c = self.col + self.dir_col
            if 0 <= nueva_f < tablero.filas and 0 <= nueva_c < tablero.columnas:
                self.fila = nueva_f
                self.col = nueva_c
                self.target_px = self.col * TAM_CELDA
                self.target_py = self.fila * TAM_CELDA
        else:
            if not tablero.es_muro(self.fila + self.next_dir_f, self.col + self.next_dir_c):
                self.dir_fila = self.next_dir_f
                self.dir_col = self.next_dir_c
            super()._decidir_siguiente_paso(tablero, *args)

    def morir(self) -> None:
        self.vidas -= 1
        self.invencible = False

    def dibujar(self, superficie: pygame.Surface, offset_x: int = 0, offset_y: int = 0) -> None:
        r_base = TAM_CELDA // 2 - 1
        r = max(0, int(r_base * self._escala_muerte))
        if r <= 0:
            return

        cx = offset_x + self.px + TAM_CELDA // 2
        cy = offset_y + self.py + TAM_CELDA // 2
        t = pygame.time.get_ticks()

        # Aura de modo fantasma (doble halo púrpura, muy visible)
        if self.modo_fantasma:
            aura_r = r_base + 10 + int(5 * math.sin(t * 0.009))
            sz = aura_r * 2 + 8
            aura_surf = pygame.Surface((sz, sz), pygame.SRCALPHA)
            acx, acy = sz // 2, sz // 2
            for i, alpha in enumerate([55, 110, 160]):
                rr = aura_r - i * 3
                if rr > 2:
                    pygame.draw.circle(
                        aura_surf, (160 + i * 15, 60 + i * 20, 255, alpha), (acx, acy), rr, 4 - i
                    )
            pygame.draw.circle(aura_surf, (220, 120, 255, 130), (acx, acy), r_base + 4, 2)
            superficie.blit(aura_surf, (cx - sz // 2, cy - sz // 2))

        # Anillo de escudo recargable (visible cuando está listo para bloquear un golpe)
        if self.escudo_activo_visual:
            pulse = 0.88 + 0.12 * math.sin(t * 0.014)
            ring_r = r_base + 7 + int(2 * math.sin(t * 0.02))
            # Brillo exterior dorado + trazo cian interior
            gold = (int(255 * pulse), int(230 * pulse), int(60 * pulse))
            pygame.draw.circle(superficie, gold, (cx, cy), ring_r, 4)
            pygame.draw.circle(superficie, (120, 220, 255), (cx, cy), ring_r - 3, 2)
            pygame.draw.circle(superficie, (255, 255, 255), (cx, cy), ring_r + 1, 1)

        # Boca tipo "wakka" (solo si no está en animación de muerte colapsando)
        if self._muerte_activa:
            boca = 0.0
        else:
            t = pygame.time.get_ticks()
            boca = math.radians(28 + 14 * math.sin(t * 0.012))

        df, dc = self.dir_fila, self.dir_col
        if df == 0 and dc == 0:
            base_ang = 0.0
        else:
            base_ang = math.atan2(df, dc)

        # Sector visible: arco de (2π - 2*boca) centrado en dirección opuesta a la boca
        # La boca mira hacia base_ang; el hueco simétrico alrededor de base_ang
        if boca < 0.01:
            pygame.draw.circle(superficie, COLOR_PAC_CUERPO, (cx, cy), r)
            pygame.draw.circle(superficie, COLOR_PAC_BRILLO, (cx - r // 3, cy - r // 3), max(2, r // 4))
        else:
            # Hueco de la boca centrado en la dirección del movimiento (base_ang)
            ang0 = base_ang + boca
            ang1 = base_ang + 2 * math.pi - boca
            pasos = 18
            pts = [(cx, cy)]
            for i in range(pasos + 1):
                t_a = ang0 + (ang1 - ang0) * (i / pasos)
                pts.append((cx + r * math.cos(t_a), cy + r * math.sin(t_a)))
            pygame.draw.polygon(superficie, COLOR_PAC_CUERPO, pts)
            # Brillo tipo píxel en el sector superior-izquierdo del cuerpo
            brx = cx - int(r * 0.35)
            bry = cy - int(r * 0.35)
            pygame.draw.circle(superficie, COLOR_PAC_BRILLO, (brx, bry), max(2, r // 5))

        # Contorno solo con boca cerrada (evita artefactos con el sector)
        if r > 4 and boca < 0.01:
            pygame.draw.circle(superficie, COLOR_PAC_BORDE, (cx, cy), r, 1)
