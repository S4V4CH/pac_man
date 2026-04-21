# src/ui/hud.py
"""HUD estilo Pac-Man clásico con toques modernos."""

from __future__ import annotations

import math
import pygame

# Paleta clásica de Pac-Man
COLOR_FONDO_HUD = (0, 0, 0)
COLOR_TEXTO_BLANCO = (255, 255, 255)
COLOR_AMARILLO = (255, 255, 0)
COLOR_CYAN = (0, 255, 255)
COLOR_ROJO = (255, 0, 0)
COLOR_ROSA = (255, 184, 255)
COLOR_NARANJA = (255, 184, 82)
COLOR_AZUL = (33, 33, 255)


def _fuente(nombre_sistema: str, tam: int, negrita: bool = False) -> pygame.font.Font:
    """Intenta cargar fuente del sistema, fallback a fuente por defecto."""
    try:
        return pygame.font.SysFont(nombre_sistema, tam, bold=negrita)
    except (OSError, AttributeError):
        return pygame.font.Font(None, tam)


class HUD:
    """
    HUD estilo Pac-Man clásico: puntajes arriba, vidas con iconos Pac-Man.
    """

    def __init__(self, ancho: int, alto: int) -> None:
        self.ancho = ancho
        self.alto = alto
        # Fuentes estilo arcade (monoespaciadas para puntajes)
        self.fuente_label = _fuente("Arial", 14, True)
        self.fuente_score = _fuente("Courier New", 22, True)
        self.fuente_info = _fuente("Arial", 13)
        self._tick = 0
        self._high_score = 0  # Simulación de high score

    def actualizar_tick(self) -> None:
        self._tick += 1
    
    def actualizar_high_score(self, puntaje: int) -> None:
        """Actualiza el high score si el puntaje actual es mayor."""
        if puntaje > self._high_score:
            self._high_score = puntaje
    
    def _dibujar_pacman_vida(self, surf: pygame.Surface, x: int, y: int, radio: int) -> None:
        """Dibuja un icono de Pac-Man para las vidas."""
        # Animación de boca simple
        apertura = 25 + 10 * math.sin(self._tick * 0.15)
        
        # Cuerpo amarillo
        pygame.draw.circle(surf, COLOR_AMARILLO, (x, y), radio)
        
        # Boca (triángulo negro)
        ang_inicio = math.radians(apertura)
        ang_fin = math.radians(360 - apertura)
        puntos = [(x, y)]
        for ang in [ang_inicio, ang_fin]:
            px = x + radio * math.cos(ang)
            py = y - radio * math.sin(ang)
            puntos.append((int(px), int(py)))
        if len(puntos) == 3:
            pygame.draw.polygon(surf, COLOR_FONDO_HUD, puntos)
    
    def _dibujar_fantasma_mini(self, surf: pygame.Surface, x: int, y: int, color: tuple, tamano: int = 10) -> None:
        """Dibuja un mini fantasma decorativo."""
        # Cuerpo redondo arriba
        pygame.draw.circle(surf, color, (x, y - tamano // 3), tamano // 2)
        # Parte inferior con ondas
        puntos = [
            (x - tamano // 2, y - tamano // 3),
            (x - tamano // 2, y + tamano // 2),
            (x - tamano // 4, y + tamano // 4),
            (x, y + tamano // 2),
            (x + tamano // 4, y + tamano // 4),
            (x + tamano // 2, y + tamano // 2),
            (x + tamano // 2, y - tamano // 3),
        ]
        pygame.draw.polygon(surf, color, puntos)
        # Ojos blancos
        ojo_tam = tamano // 5
        pygame.draw.circle(surf, COLOR_TEXTO_BLANCO, (x - tamano // 4, y - tamano // 3), ojo_tam)
        pygame.draw.circle(surf, COLOR_TEXTO_BLANCO, (x + tamano // 4, y - tamano // 3), ojo_tam)
        # Pupilas
        pygame.draw.circle(surf, COLOR_AZUL, (x - tamano // 4, y - tamano // 3), ojo_tam // 2)
        pygame.draw.circle(surf, COLOR_AZUL, (x + tamano // 4, y - tamano // 3), ojo_tam // 2)

    def dibujar(
        self,
        superficie: pygame.Surface,
        *,
        pacman,
        nivel: int,
        tablero,
        semilla: int,
        umbral_division: int,
    ) -> None:
        """Dibuja el HUD estilo Pac-Man clásico."""
        self.actualizar_tick()
        self.actualizar_high_score(pacman.puntaje)
        
        alto_barra_sup = 54
        alto_barra_inf = 48
        
        # Fondo negro del HUD superior
        pygame.draw.rect(superficie, COLOR_FONDO_HUD, (0, 0, self.ancho, alto_barra_sup))
        pygame.draw.line(superficie, COLOR_AZUL, (0, alto_barra_sup - 1), (self.ancho, alto_barra_sup - 1), 2)
        
        # === SECCIÓN SUPERIOR (estilo arcade clásico) ===
        margen = 20
        
        # 1UP + Puntaje del jugador (izquierda)
        lbl_1up = self.fuente_label.render("1UP", True, COLOR_TEXTO_BLANCO)
        superficie.blit(lbl_1up, (margen, 6))
        
        score_txt = self.fuente_score.render(f"{pacman.puntaje:06d}", True, COLOR_TEXTO_BLANCO)
        superficie.blit(score_txt, (margen, 24))
        
        # HIGH SCORE (centro)
        cx = self.ancho // 2
        lbl_high = self.fuente_label.render("HIGH SCORE", True, COLOR_ROJO)
        superficie.blit(lbl_high, (cx - lbl_high.get_width() // 2, 6))
        
        high_txt = self.fuente_score.render(f"{self._high_score:06d}", True, COLOR_TEXTO_BLANCO)
        superficie.blit(high_txt, (cx - high_txt.get_width() // 2, 24))
        
        # LEVEL (derecha)
        lbl_level = self.fuente_label.render("LEVEL", True, COLOR_CYAN)
        superficie.blit(lbl_level, (self.ancho - margen - 70, 6))
        
        nivel_txt = self.fuente_score.render(f"{nivel:02d}", True, COLOR_AMARILLO)
        superficie.blit(nivel_txt, (self.ancho - margen - 50, 24))
        
        # === SECCIÓN INFERIOR ===
        # Fondo negro del HUD inferior
        pygame.draw.rect(superficie, COLOR_FONDO_HUD, (0, self.alto - alto_barra_inf, self.ancho, alto_barra_inf))
        pygame.draw.line(superficie, COLOR_AZUL, (0, self.alto - alto_barra_inf), (self.ancho, self.alto - alto_barra_inf), 2)
        
        y_base_inf = self.alto - alto_barra_inf + 8
        
        # Vidas con iconos Pac-Man animados (izquierda)
        x_vida = margen
        for i in range(max(0, min(pacman.vidas, 5))):  # Máximo 5 iconos mostrados
            self._dibujar_pacman_vida(superficie, x_vida + i * 28, y_base_inf + 10, 10)
        
        # Texto de vidas si tiene más de 5
        if pacman.vidas > 5:
            txt_vidas = self.fuente_info.render(f"x{pacman.vidas}", True, COLOR_AMARILLO)
            superficie.blit(txt_vidas, (x_vida + 5 * 28 + 8, y_base_inf + 4))
        
        # Progreso del nivel (centro) - estilo minimalista
        comidos = tablero.puntos_comidos if tablero else 0
        total = tablero.total_puntos if tablero else 1
        progreso_pct = int((comidos / total) * 100) if total > 0 else 0
        
        txt_progreso = self.fuente_info.render(f"COMIDA: {comidos}/{total}  ({progreso_pct}%)", True, COLOR_TEXTO_BLANCO)
        superficie.blit(txt_progreso, (cx - txt_progreso.get_width() // 2, y_base_inf + 4))
        
        # Mini fantasmas decorativos y info de semilla (derecha)
        x_ghost = self.ancho - margen - 120
        colores_fantasmas = [COLOR_ROJO, COLOR_ROSA, COLOR_CYAN, COLOR_NARANJA]
        for i, col in enumerate(colores_fantasmas):
            offset_y = 3 * math.sin(self._tick * 0.1 + i * 1.5)
            self._dibujar_fantasma_mini(superficie, x_ghost + i * 22, y_base_inf + 10 + int(offset_y), col, 16)
        
        # Semilla (abajo a la derecha, pequeño)
        txt_seed = self.fuente_info.render(f"seed:{semilla}", True, (100, 100, 150))
        superficie.blit(txt_seed, (self.ancho - margen - 100, y_base_inf + 26))
