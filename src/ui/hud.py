# src/ui/hud.py
"""HUD estilo Pac-Man clásico — con barra de EXP e indicadores de mejoras roguelike."""

from __future__ import annotations

import math
import pygame

COLOR_FONDO_HUD   = (0, 0, 0)
COLOR_TEXTO_BLANCO = (255, 255, 255)
COLOR_AMARILLO    = (255, 255, 0)
COLOR_CYAN        = (0, 255, 255)
COLOR_ROJO        = (255, 0, 0)
COLOR_ROSA        = (255, 184, 255)
COLOR_NARANJA     = (255, 184, 82)
COLOR_AZUL        = (33, 33, 255)
COLOR_VERDE       = (0, 220, 0)
COLOR_ORO         = (255, 215, 0)
COLOR_PURPURA     = (180, 80, 255)
COLOR_HIELO       = (100, 200, 255)


def _fuente(nombre: str, tam: int, negrita: bool = False) -> pygame.font.Font:
    try:
        return pygame.font.SysFont(nombre, tam, bold=negrita)
    except (OSError, AttributeError):
        return pygame.font.Font(None, tam)


class HUD:
    """HUD estilo Pac-Man clásico con EXP bar e indicadores de mejoras."""

    def __init__(self, ancho: int, alto: int) -> None:
        self.ancho = ancho
        self.alto = alto
        self.fuente_label = _fuente("Arial", 14, True)
        self.fuente_score = _fuente("Courier New", 22, True)
        self.fuente_info  = _fuente("Arial", 13)
        self.fuente_tiny  = _fuente("Arial", 11, True)
        self._tick = 0
        self._high_score = 0

    def actualizar_tick(self) -> None:
        self._tick += 1

    def actualizar_high_score(self, puntaje: int) -> None:
        if puntaje > self._high_score:
            self._high_score = puntaje

    # ─── Ícono Pac-Man de vida ────────────────────────────────────────────────
    def _dibujar_pacman_vida(self, surf, x, y, radio):
        apertura = 25 + 10 * math.sin(self._tick * 0.15)
        cx, cy = float(x), float(y)
        pygame.draw.circle(surf, COLOR_AMARILLO, (int(cx), int(cy)), radio)
        ang_base = 0.0
        n = max(12, int(apertura) + 8)
        pts: list[tuple[float, float]] = [(cx, cy)]
        for i in range(n + 1):
            ang_deg = ang_base + apertura - (2 * apertura * i / n)
            a = math.radians(ang_deg)
            pts.append((cx + radio * math.cos(a), cy - radio * math.sin(a)))
        pygame.draw.polygon(surf, COLOR_FONDO_HUD, pts)

    # ─── Mini ícono de escudo ─────────────────────────────────────────────────
    def _dibujar_icono_escudo(self, surf, cx, cy, size, color):
        pts = [
            (cx, cy - size),
            (cx + int(size * 0.75), cy - size // 2),
            (cx + int(size * 0.75), cy + size // 3),
            (cx, cy + size),
            (cx - int(size * 0.75), cy + size // 3),
            (cx - int(size * 0.75), cy - size // 2),
        ]
        pygame.draw.polygon(surf, color, pts)
        pygame.draw.polygon(surf, (255, 255, 255), pts, 1)

    # ─── Mini ícono de copo de nieve ─────────────────────────────────────────
    def _dibujar_icono_nieve(self, surf, cx, cy, size, color):
        for i in range(6):
            ang = math.radians(i * 60)
            ex = int(cx + size * math.cos(ang))
            ey = int(cy + size * math.sin(ang))
            pygame.draw.line(surf, color, (cx, cy), (ex, ey), 2)
        pygame.draw.circle(surf, color, (cx, cy), 3)

    # ─── Mini ícono de fantasma ───────────────────────────────────────────────
    def _dibujar_icono_fantasma(self, surf, cx, cy, size, color):
        pygame.draw.circle(surf, color, (cx, cy - size // 3), size // 2)
        pts = [
            (cx - size // 2, cy - size // 3),
            (cx - size // 2, cy + size // 2),
            (cx - size // 3, cy + size // 4),
            (cx, cy + size // 2),
            (cx + size // 3, cy + size // 4),
            (cx + size // 2, cy + size // 2),
            (cx + size // 2, cy - size // 3),
        ]
        pygame.draw.polygon(surf, color, pts)

    # ─── Barra de progreso genérica ───────────────────────────────────────────
    def _barra(self, surf, x, y, w, h, progreso, color_fill, color_bg=(30, 30, 50),
               border_radius=4, borde_color=(80, 80, 100)):
        pygame.draw.rect(surf, color_bg, (x, y, w, h), border_radius=border_radius)
        fill_w = max(0, int(w * max(0.0, min(1.0, progreso))))
        if fill_w > 0:
            pygame.draw.rect(surf, color_fill, (x, y, fill_w, h), border_radius=border_radius)
        pygame.draw.rect(surf, borde_color, (x, y, w, h), 1, border_radius=border_radius)

    # ─── Indicadores de mejoras activas (lateral derecho del game area) ───────
    def dibujar_indicadores_mejoras(
        self,
        surf: pygame.Surface,
        mejoras,       # SistemaMejoras | None
        ox: int,
        oy: int,
        tablero_w: int,
        tablero_h: int,
    ) -> None:
        """Dibuja indicadores compactos a la derecha del tablero."""
        if mejoras is None:
            return

        item_h = 46
        bar_w = 62
        icon_size = 12
        panel_w = bar_w + icon_size * 2 + 28
        # Columna a la derecha del tablero; si no cabe, pegada al borde de la ventana
        col_x = ox + tablero_w + 6
        if col_x + panel_w > self.ancho - 6:
            col_x = max(ox + 4, self.ancho - panel_w - 8)
        col_y = oy + 2

        indicadores = []

        # Escudo
        if mejoras.nivel_de('escudo') > 0:
            ea = mejoras.escudo_activo
            indicadores.append({
                'tipo': 'escudo',
                'progreso': mejoras.get_escudo_progreso(),
                'activo': ea,
                'color': COLOR_ORO if ea else (140, 130, 90),
                'titulo': 'ESCUDO',
                'sub': 'LISTO · bloquea 1 golpe' if ea else 'Recargando…',
            })

        # Congelador
        if mejoras.nivel_de('congelador') > 0:
            indicadores.append({
                'tipo': 'freeze',
                'progreso': mejoras.get_freeze_progreso(),
                'activo': mejoras.get_freeze_activo(),
                'color': COLOR_HIELO,
                'titulo': 'HIELO',
                'sub': 'Activo' if mejoras.get_freeze_activo() else 'En espera',
            })

        # Modo fantasma
        if mejoras.modo_fantasma_activo:
            indicadores.append({
                'tipo': 'ghost',
                'progreso': mejoras.get_modo_fantasma_progreso(),
                'activo': True,
                'color': COLOR_PURPURA,
                'titulo': 'FANTASMA',
                'sub': 'Atraviesa muros',
            })

        if not indicadores:
            return

        # Fondo semitransparente para la columna
        total_h = len(indicadores) * item_h + 10
        bg = pygame.Surface((panel_w, total_h), pygame.SRCALPHA)
        bg.fill((8, 10, 35, 210))
        pygame.draw.rect(bg, (80, 120, 200), (0, 0, panel_w, total_h), 1, border_radius=6)
        surf.blit(bg, (col_x - 6, col_y - 4))

        for ind in indicadores:
            prog = ind['progreso']
            color = ind['color']
            activo = ind['activo']

            # Ícono
            ico_cx = col_x + icon_size + 4
            ico_cy = col_y + 18

            if ind['tipo'] == 'escudo':
                icol = (255, 230, 100) if activo else (120, 110, 70)
                self._dibujar_icono_escudo(surf, ico_cx, ico_cy, icon_size, icol)
            elif ind['tipo'] == 'freeze':
                self._dibujar_icono_nieve(surf, ico_cx, ico_cy, icon_size, color)
            elif ind['tipo'] == 'ghost':
                self._dibujar_icono_fantasma(surf, ico_cx, ico_cy, icon_size, color)

            # Título + subtítulo
            tit = self.fuente_tiny.render(ind['titulo'], True, (220, 225, 255))
            surf.blit(tit, (col_x + icon_size * 2 + 14, col_y + 2))
            subc = (180, 255, 200) if (ind['tipo'] == 'escudo' and activo) else (150, 150, 170)
            sub = self.fuente_tiny.render(ind['sub'][:22], True, subc)
            surf.blit(sub, (col_x + icon_size * 2 + 14, col_y + 16))

            # Barra
            bar_x = col_x + icon_size * 2 + 14
            bar_y_top = col_y + 30
            if activo and ind['tipo'] in ('escudo', 'ghost', 'freeze'):
                alpha_pulse = int(160 + 95 * math.sin(self._tick * 0.12))
                glow = pygame.Surface((bar_w + 4, 12), pygame.SRCALPHA)
                pygame.draw.rect(
                    glow,
                    (*color[:3], min(120, alpha_pulse // 2)) if len(color) == 3 else (120, 80, 200, 70),
                    (0, 0, bar_w + 4, 12),
                    border_radius=4,
                )
                surf.blit(glow, (bar_x - 2, bar_y_top - 1))
            bar_fill = color if activo or ind['tipo'] == 'freeze' else (80, 90, 120)
            self._barra(surf, bar_x, bar_y_top, bar_w, 9, prog, bar_fill,
                        color_bg=(18, 18, 35), border_radius=4,
                        borde_color=color if activo else (55, 55, 75))

            col_y += item_h

    # ─── Dibujo principal ─────────────────────────────────────────────────────
    def dibujar(
        self,
        superficie: pygame.Surface,
        *,
        pacman,
        nivel: int,
        tablero,
        umbral_division: int,
        mejoras=None,       # SistemaMejoras | None
        puntaje_exp: int = 0,
        umbral_exp: int = 500,
    ) -> None:
        self.actualizar_tick()
        self.actualizar_high_score(pacman.puntaje)

        alto_barra_sup = 54
        alto_barra_inf = 48

        # ── HUD Superior ──────────────────────────────────────────────────────
        pygame.draw.rect(superficie, COLOR_FONDO_HUD, (0, 0, self.ancho, alto_barra_sup))
        pygame.draw.line(superficie, COLOR_AZUL, (0, alto_barra_sup - 1), (self.ancho, alto_barra_sup - 1), 2)

        margen = 20

        # 1UP + puntaje (izquierda)
        lbl_1up = self.fuente_label.render("1UP", True, COLOR_TEXTO_BLANCO)
        superficie.blit(lbl_1up, (margen, 6))
        score_txt = self.fuente_score.render(f"{pacman.puntaje:06d}", True, COLOR_TEXTO_BLANCO)
        superficie.blit(score_txt, (margen, 22))

        # HIGH SCORE (centro)
        cx = self.ancho // 2
        lbl_high = self.fuente_label.render("HIGH SCORE", True, COLOR_ROJO)
        superficie.blit(lbl_high, (cx - lbl_high.get_width() // 2, 6))
        high_txt = self.fuente_score.render(f"{self._high_score:06d}", True, COLOR_TEXTO_BLANCO)
        superficie.blit(high_txt, (cx - high_txt.get_width() // 2, 22))

        # LEVEL (derecha)
        lbl_level = self.fuente_label.render("LEVEL", True, COLOR_CYAN)
        superficie.blit(lbl_level, (self.ancho - margen - 70, 6))
        nivel_txt = self.fuente_score.render(f"{nivel:02d}", True, COLOR_AMARILLO)
        superficie.blit(nivel_txt, (self.ancho - margen - 50, 22))

        # ── Barra de EXP (abajo del HUD superior) ────────────────────────────
        exp_bar_y = alto_barra_sup - 9
        exp_bar_w = self.ancho - 2 * margen
        progreso_exp = min(1.0, pacman.puntaje / max(1, umbral_exp))

        # Fondo gris oscuro
        pygame.draw.rect(superficie, (20, 20, 40), (margen, exp_bar_y, exp_bar_w, 7), border_radius=3)

        # Relleno: gradiente de amarillo a naranja
        fill_w = max(0, int(exp_bar_w * progreso_exp))
        if fill_w > 0:
            for px in range(fill_w):
                ratio = px / max(1, exp_bar_w)
                r = 255
                g = int(255 - ratio * 80)
                b = 0
                pygame.draw.line(superficie, (r, g, b),
                                 (margen + px, exp_bar_y),
                                 (margen + px, exp_bar_y + 6))

        # Borde
        pygame.draw.rect(superficie, (80, 80, 120), (margen, exp_bar_y, exp_bar_w, 7), 1, border_radius=3)

        # Texto EXP a la derecha de la barra
        pts_restantes = max(0, umbral_exp - pacman.puntaje)
        exp_lbl = self.fuente_tiny.render(
            f"EXP  {pacman.puntaje}/{umbral_exp}  (faltan {pts_restantes} para mejora)",
            True, (180, 180, 120),
        )
        # Lo dibujamos centrado sobre la barra
        superficie.blit(exp_lbl, (cx - exp_lbl.get_width() // 2, exp_bar_y - 1))

        # La banda inferior se dibuja aparte al final del frame (ver dibujar_banda_inferior)
        # para que quede por encima del tablero y los personajes y la semilla sea siempre visible.

    def dibujar_banda_inferior(
        self,
        superficie: pygame.Surface,
        *,
        pacman,
        tablero,
        semilla: int,
        mejoras=None,
    ) -> None:
        """Franja inferior del HUD: debe llamarse al final del dibujado del juego."""
        alto_barra_inf = 48
        margen = 20
        cx = self.ancho // 2
        y_base_inf = self.alto - alto_barra_inf + 8

        pygame.draw.rect(superficie, COLOR_FONDO_HUD,
                         (0, self.alto - alto_barra_inf, self.ancho, alto_barra_inf))
        pygame.draw.line(superficie, COLOR_AZUL,
                         (0, self.alto - alto_barra_inf), (self.ancho, self.alto - alto_barra_inf), 2)

        # Vidas (iconos Pac-Man)
        x_vida = margen
        for i in range(max(0, min(pacman.vidas, 5))):
            self._dibujar_pacman_vida(superficie, x_vida + i * 28, y_base_inf + 10, 10)
        if pacman.vidas > 5:
            tv = self.fuente_info.render(f"x{pacman.vidas}", True, COLOR_AMARILLO)
            superficie.blit(tv, (x_vida + 5 * 28 + 8, y_base_inf + 4))

        comidos = tablero.puntos_comidos if tablero else 0
        total = tablero.total_puntos if tablero else 1
        pct = int((comidos / total) * 100) if total > 0 else 0
        txt_prog = self.fuente_info.render(
            f"COMIDA: {comidos}/{total}  ({pct}%)", True, COLOR_TEXTO_BLANCO
        )
        superficie.blit(txt_prog, (cx - txt_prog.get_width() // 2, y_base_inf + 4))

        seed_txt = self.fuente_tiny.render(
            f"Semilla {semilla % 100000:05d}",
            True,
            (170, 185, 220),
        )
        superficie.blit(seed_txt, (margen, y_base_inf + 26))

        if mejoras:
            self._dibujar_indicadores_inferiores(superficie, mejoras, y_base_inf)

    def _dibujar_indicadores_inferiores(self, surf, mejoras, y_base):
        """Indicadores a la derecha (antes del seed), sin solapar el texto central."""
        # (superficie de texto, tipo: 'escudo_ok' | 'escudo_cd' | 'hielo' | 'cong' | 'fantasma')
        bloques: list[tuple[pygame.Surface, str]] = []

        if mejoras.nivel_de('escudo') > 0:
            if mejoras.escudo_activo:
                bloques.append((
                    self.fuente_tiny.render('ESCUDO LISTO', True, (255, 230, 120)),
                    'escudo_ok',
                ))
            else:
                bloques.append((
                    self.fuente_tiny.render('ESCUDO: recarga', True, (140, 130, 100)),
                    'escudo_cd',
                ))

        if mejoras.get_freeze_activo():
            bloques.append((self.fuente_tiny.render('HIELO', True, COLOR_HIELO), 'hielo'))
        elif mejoras.nivel_de('congelador') > 0:
            bloques.append((
                self.fuente_tiny.render('CONGELADOR', True, (80, 140, 170)),
                'cong',
            ))

        if mejoras.modo_fantasma_activo:
            bloques.append((
                self.fuente_tiny.render('MODO FANTASMA', True, COLOR_PURPURA),
                'fantasma',
            ))

        if not bloques:
            return

        gap = 10
        total_w = sum(s[0].get_width() for s in bloques) + gap * (len(bloques) - 1)
        x_end = self.ancho - 20 - 100
        x = x_end - total_w
        ty = y_base + 24

        for surf_txt, tipo in bloques:
            cy = ty + surf_txt.get_height() // 2
            if tipo == 'fantasma':
                pulse = int(180 + 75 * math.sin(self._tick * 0.18))
                pygame.draw.line(
                    surf, (pulse, 120, 255),
                    (x, ty + surf_txt.get_height()),
                    (x + surf_txt.get_width(), ty + surf_txt.get_height()),
                    2,
                )
            elif tipo == 'escudo_ok':
                pygame.draw.circle(surf, (255, 220, 80), (x + 5, cy), 4, 2)
                surf.blit(surf_txt, (x + 12, ty))
                x += surf_txt.get_width() + gap
                continue
            elif tipo == 'escudo_cd':
                pygame.draw.circle(surf, (90, 85, 70), (x + 5, cy), 4, 1)
                surf.blit(surf_txt, (x + 12, ty))
                x += surf_txt.get_width() + gap
                continue
            surf.blit(surf_txt, (x, ty))
            x += surf_txt.get_width() + gap
