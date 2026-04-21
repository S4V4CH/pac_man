# src/ui/menu.py
"""Menús principales estilo Pac-Man clásico con animaciones."""

from __future__ import annotations

import math

import pygame

# Paleta Pac-Man clásica
COLOR_BG = (0, 0, 0)
COLOR_AZUL_OSCURO = (0, 0, 128)
COLOR_AMARILLO = (255, 255, 0)
COLOR_BLANCO = (255, 255, 255)
COLOR_CYAN = (0, 255, 255)
COLOR_ROJO = (255, 0, 0)
COLOR_ROSA = (255, 184, 255)
COLOR_NARANJA = (255, 184, 82)
COLOR_AZUL = (33, 33, 255)
COLOR_VERDE = (0, 255, 0)
COLOR_GRIS = (130, 130, 130)


def _f(name: str, size: int, bold: bool = False) -> pygame.font.Font:
    """Carga fuente del sistema con fallback."""
    try:
        return pygame.font.SysFont(name, size, bold=bold)
    except (OSError, AttributeError):
        return pygame.font.Font(None, size)


def _dibujar_pacman(surf: pygame.Surface, x: int, y: int, radio: int, apertura: float, direccion: int = 0) -> None:
    """Dibuja Pac-Man con boca animada. Dirección: 0=derecha, 1=abajo, 2=izquierda, 3=arriba."""
    pygame.draw.circle(surf, COLOR_AMARILLO, (int(x), int(y)), radio)
    
    # Boca (triángulo)
    ang_base = direccion * 90
    ang_inicio = math.radians(ang_base + apertura)
    ang_fin = math.radians(ang_base + 360 - apertura)
    
    puntos = [(int(x), int(y))]
    for ang in [ang_inicio, ang_fin]:
        px = x + radio * math.cos(ang)
        py = y - radio * math.sin(ang)
        puntos.append((int(px), int(py)))
    
    if len(puntos) == 3:
        pygame.draw.polygon(surf, COLOR_BG, puntos)


def _dibujar_fantasma(surf: pygame.Surface, x: int, y: int, color: tuple, tamano: int = 20, asustado: bool = False) -> None:
    """Dibuja un fantasma estilo clásico."""
    if asustado:
        color = COLOR_AZUL
    
    # Cuerpo redondeado
    pygame.draw.circle(surf, color, (int(x), int(y) - tamano // 3), tamano // 2)
    
    # Parte inferior con ondas
    puntos = [
        (int(x - tamano // 2), int(y - tamano // 3)),
        (int(x - tamano // 2), int(y + tamano // 2)),
        (int(x - tamano // 3), int(y + tamano // 3)),
        (int(x), int(y + tamano // 2)),
        (int(x + tamano // 3), int(y + tamano // 3)),
        (int(x + tamano // 2), int(y + tamano // 2)),
        (int(x + tamano // 2), int(y - tamano // 3)),
    ]
    pygame.draw.polygon(surf, color, puntos)
    
    # Ojos
    if asustado:
        # Ojos asustados (líneas blancas)
        for ox in [-tamano // 4, tamano // 4]:
            pygame.draw.line(surf, COLOR_BLANCO, 
                           (int(x + ox - 2), int(y - tamano // 4)), 
                           (int(x + ox + 2), int(y)), 2)
    else:
        # Ojos normales
        ojo_tam = tamano // 4
        for ox in [-tamano // 4, tamano // 4]:
            pygame.draw.circle(surf, COLOR_BLANCO, (int(x + ox), int(y - tamano // 4)), ojo_tam)
            pygame.draw.circle(surf, COLOR_AZUL, (int(x + ox), int(y - tamano // 4)), ojo_tam // 2)


def _dibujar_pellet(surf: pygame.Surface, x: int, y: int, grande: bool = False) -> None:
    """Dibuja un pellet (punto de comida)."""
    radio = 6 if grande else 2
    color = COLOR_BLANCO if not grande else COLOR_ROSA
    pygame.draw.circle(surf, color, (int(x), int(y)), radio)


def _titulo_animado(surf: pygame.Surface, texto: str, y: float, t: int) -> None:
    """Dibuja el título con efecto de pulso."""
    fuente = _f("Arial Black", 56, True)
    pulse = 0.9 + 0.1 * math.sin(t * 0.08)
    
    # Colores amarillo brillante con pulso
    r = 255
    g = int(255 * pulse)
    b = 0
    
    # Sombra
    shadow = fuente.render(texto, True, (100, 100, 0))
    main = fuente.render(texto, True, (r, g, b))
    
    x = surf.get_width() // 2 - main.get_width() // 2
    surf.blit(shadow, (x + 4, int(y) + 4))
    surf.blit(main, (x, int(y)))


OPCIONES_MENU = [
    "JUGAR  (semilla aleatoria)",
    "SEMILLA PERSONALIZADA",
    "RANKING",
    "CONTROLES",
    "SALIR",
]


def dibujar_menu_principal(
    surf: pygame.Surface,
    indice_seleccion: int,
    tiempo_tick: int,
    vol_musica: float = 0.65,
    vol_sfx: float = 0.75,
) -> tuple[pygame.Rect, pygame.Rect]:
    """Menú principal estilo Pac-Man con animaciones."""
    surf.fill(COLOR_BG)
    
    w = surf.get_width()
    h = surf.get_height()
    
    # Decoración: pellets en las esquinas
    for x in range(40, w, 60):
        _dibujar_pellet(surf, x, 20, False)
        _dibujar_pellet(surf, x, h - 20, False)
    
    # Pellets grandes en esquinas
    _dibujar_pellet(surf, 30, 30, True)
    _dibujar_pellet(surf, w - 30, 30, True)
    _dibujar_pellet(surf, 30, h - 30, True)
    _dibujar_pellet(surf, w - 30, h - 30, True)
    
    # Título principal
    _titulo_animado(surf, "PAC-MAN", 50, tiempo_tick)
    
    # Subtítulo "ROGUELIKE" más pequeño
    fuente_sub = _f("Arial", 24, True)
    sub_txt = fuente_sub.render("ROGUELIKE EDITION", True, COLOR_CYAN)
    surf.blit(sub_txt, (w // 2 - sub_txt.get_width() // 2, 120))
    
    # Animación: Pac-Man perseguido por fantasmas
    anim_y = 160
    ciclo_x = (tiempo_tick * 3) % (w + 200) - 100
    
    # Fantasmas persiguiendo
    colores_fantasma = [COLOR_ROJO, COLOR_ROSA, COLOR_CYAN, COLOR_NARANJA]
    for i, color in enumerate(colores_fantasma):
        offset_x = -50 - i * 30
        offset_y = 5 * math.sin(tiempo_tick * 0.1 + i)
        _dibujar_fantasma(surf, ciclo_x + offset_x, anim_y + offset_y, color, 20)
    
    # Pac-Man huyendo
    apertura = 20 + 15 * abs(math.sin(tiempo_tick * 0.2))
    _dibujar_pacman(surf, ciclo_x, anim_y, 14, apertura, 0)
    
    # Opciones del menú
    y0 = 230
    esp = 50
    fuente_op = _f("Arial", 24, True)
    
    for i, op in enumerate(OPCIONES_MENU):
        sel = i == indice_seleccion
        y_pos = y0 + i * esp
        
        if sel:
            # Fondo de selección
            txt_temp = fuente_op.render(op, True, COLOR_BLANCO)
            rect_w = txt_temp.get_width() + 60
            rect_x = w // 2 - rect_w // 2
            
            pygame.draw.rect(surf, COLOR_AZUL_OSCURO, 
                           (rect_x, y_pos - 8, rect_w, 40), 
                           border_radius=8)
            pygame.draw.rect(surf, COLOR_AMARILLO, 
                           (rect_x, y_pos - 8, rect_w, 40), 
                           width=3, border_radius=8)
            
            # Pac-Man indicador
            pac_anim = 15 + 10 * abs(math.sin(tiempo_tick * 0.3))
            _dibujar_pacman(surf, rect_x - 25, y_pos + 12, 10, pac_anim, 0)
            
            color_txt = COLOR_AMARILLO
        else:
            color_txt = COLOR_BLANCO
        
        # Texto de la opción
        t = fuente_op.render(op, True, color_txt)
        surf.blit(t, (w // 2 - t.get_width() // 2, y_pos))
    
    # Controles hint
    fuente_hint = _f("Arial", 14)
    hint = fuente_hint.render("↑ ↓ SELECCIONAR   ·   ENTER CONFIRMAR   ·   ESC SALIR", True, COLOR_GRIS)
    surf.blit(hint, (w // 2 - hint.get_width() // 2, h - 150))
    
    # Controles de volumen
    bar_w = 200
    bar_h = 14
    x0 = w // 2 - bar_w // 2
    y_mus = h - 120
    y_sfx = h - 88
    
    fuente_vol = _f("Arial", 15, True)
    
    # Música
    lbl_mus = fuente_vol.render("MÚSICA", True, COLOR_CYAN)
    surf.blit(lbl_mus, (x0 - 80, y_mus - 2))
    
    pygame.draw.rect(surf, COLOR_AZUL_OSCURO, (x0, y_mus, bar_w, bar_h), border_radius=7)
    pygame.draw.rect(surf, COLOR_CYAN, (x0, y_mus, max(0, int(bar_w * vol_musica)), bar_h), border_radius=7)
    pygame.draw.rect(surf, COLOR_BLANCO, (x0, y_mus, bar_w, bar_h), 2, border_radius=7)
    
    pct_mus = fuente_hint.render(f"{int(vol_musica * 100)}%", True, COLOR_BLANCO)
    surf.blit(pct_mus, (x0 + bar_w + 10, y_mus - 2))
    
    # Efectos
    lbl_sfx = fuente_vol.render("EFECTOS", True, COLOR_VERDE)
    surf.blit(lbl_sfx, (x0 - 80, y_sfx - 2))
    
    pygame.draw.rect(surf, COLOR_AZUL_OSCURO, (x0, y_sfx, bar_w, bar_h), border_radius=7)
    pygame.draw.rect(surf, COLOR_VERDE, (x0, y_sfx, max(0, int(bar_w * vol_sfx)), bar_h), border_radius=7)
    pygame.draw.rect(surf, COLOR_BLANCO, (x0, y_sfx, bar_w, bar_h), 2, border_radius=7)
    
    pct_sfx = fuente_hint.render(f"{int(vol_sfx * 100)}%", True, COLOR_BLANCO)
    surf.blit(pct_sfx, (x0 + bar_w + 10, y_sfx - 2))
    
    rect_mus = pygame.Rect(x0, y_mus - 6, bar_w, bar_h + 12)
    rect_sfx = pygame.Rect(x0, y_sfx - 6, bar_w, bar_h + 12)
    return rect_mus, rect_sfx


def dibujar_menu_semilla(surf: pygame.Surface, buffer_texto: str, error: str | None) -> None:
    """Menú de ingreso de semilla personalizada."""
    surf.fill(COLOR_BG)
    
    w = surf.get_width()
    h = surf.get_height()
    
    # Título
    fuente_tit = _f("Arial", 36, True)
    t = fuente_tit.render("SEMILLA DE PARTIDA", True, COLOR_AMARILLO)
    surf.blit(t, (w // 2 - t.get_width() // 2, 80))
    
    # Explicación
    fuente_exp = _f("Arial", 16)
    ex = fuente_exp.render("Misma semilla = mismo mapa (competir en ranking)", True, COLOR_CYAN)
    surf.blit(ex, (w // 2 - ex.get_width() // 2, 135))
    
    ex2 = fuente_exp.render("Solo números permitidos", True, COLOR_GRIS)
    surf.blit(ex2, (w // 2 - ex2.get_width() // 2, 160))
    
    # Caja de entrada
    caja = pygame.Rect(w // 2 - 220, 220, 440, 58)
    pygame.draw.rect(surf, COLOR_AZUL_OSCURO, caja, border_radius=10)
    pygame.draw.rect(surf, COLOR_AMARILLO, caja, 3, border_radius=10)
    
    fuente_in = _f("Courier New", 32, True)
    display = buffer_texto if buffer_texto else "_"
    txt = fuente_in.render(display, True, COLOR_BLANCO)
    surf.blit(txt, (caja.x + 20, caja.y + 13))
    
    # Error
    if error:
        fuente_err = _f("Arial", 17, True)
        e = fuente_err.render(error, True, COLOR_ROJO)
        surf.blit(e, (w // 2 - e.get_width() // 2, 300))
    
    # Hints
    fuente_hint = _f("Arial", 14)
    hint_txt = fuente_hint.render("ENTER CONFIRMAR   ·   BACKSPACE BORRAR   ·   ESC VOLVER", True, COLOR_GRIS)
    surf.blit(hint_txt, (w // 2 - hint_txt.get_width() // 2, h - 50))


def dibujar_menu_ranking(surf: pygame.Surface, entradas: list[dict]) -> None:
    """Menú de ranking de mejores puntajes."""
    surf.fill(COLOR_BG)
    
    w = surf.get_width()
    h = surf.get_height()
    
    # Título
    fuente_tit = _f("Arial Black", 42, True)
    t = fuente_tit.render("TOP 10", True, COLOR_AMARILLO)
    surf.blit(t, (w // 2 - t.get_width() // 2, 40))
    
    # Subtítulo
    fuente_sub = _f("Arial", 18)
    sub = fuente_sub.render("MEJORES PUNTAJES", True, COLOR_CYAN)
    surf.blit(sub, (w // 2 - sub.get_width() // 2, 90))
    
    if not entradas:
        fuente_vac = _f("Arial", 20)
        vac = fuente_vac.render("Aún no hay partidas guardadas", True, COLOR_GRIS)
        surf.blit(vac, (w // 2 - vac.get_width() // 2, 250))
        
        # Pac-Man triste decorativo
        _dibujar_pacman(surf, w // 2, 350, 30, 5, 2)
    else:
        fuente_rank = _f("Courier New", 19, True)
        y = 140
        
        for i, e in enumerate(entradas[:10]):
            nombre = str(e.get("nombre", "?"))[:12]
            pts = e.get("puntaje", 0)
            sem = e.get("semilla", 0)
            
            # Color según posición
            if i == 0:
                col = COLOR_AMARILLO
                medal = "👑"
            elif i == 1:
                col = COLOR_CYAN
                medal = "🥈"
            elif i == 2:
                col = COLOR_ROSA
                medal = "🥉"
            else:
                col = COLOR_BLANCO
                medal = " "
            
            linea = f"{medal} {i+1:2}. {nombre:<12}  {pts:>7}pts  seed:{sem}"
            txt = fuente_rank.render(linea, True, col)
            surf.blit(txt, (w // 2 - 280, y))
            y += 38
    
    # Hint
    fuente_hint = _f("Arial", 14)
    hint_txt = fuente_hint.render("ENTER / ESC  VOLVER AL MENÚ", True, COLOR_GRIS)
    surf.blit(hint_txt, (w // 2 - hint_txt.get_width() // 2, h - 40))


def dibujar_menu_controles(surf: pygame.Surface) -> None:
    """Menú de controles del juego."""
    surf.fill(COLOR_BG)
    
    w = surf.get_width()
    h = surf.get_height()
    
    # Título
    fuente_tit = _f("Arial", 38, True)
    t = fuente_tit.render("CONTROLES", True, COLOR_AMARILLO)
    surf.blit(t, (w // 2 - t.get_width() // 2, 50))
    
    # Controles organizados
    y = 130
    fuente_ctrl = _f("Arial", 20, True)
    fuente_desc = _f("Arial", 18)
    
    controles = [
        ("MOVIMIENTO", "WASD  o  Flechas ↑↓←→", COLOR_CYAN),
        ("PAUSA", "ESC", COLOR_VERDE),
        ("MENÚ", "Q  (desde pausa)", COLOR_ROSA),
        ("REINICIAR", "R  (en juego)", COLOR_NARANJA),
        ("MÚSICA", "M  (alternar on/off)", COLOR_AMARILLO),
    ]
    
    for ctrl, desc, color in controles:
        # Etiqueta
        lbl = fuente_ctrl.render(ctrl, True, color)
        surf.blit(lbl, (w // 2 - 260, y))
        
        # Descripción
        desc_txt = fuente_desc.render(desc, True, COLOR_BLANCO)
        surf.blit(desc_txt, (w // 2 - 70, y + 2))
        
        y += 48
    
    # Separador
    pygame.draw.line(surf, COLOR_AZUL_OSCURO, (w // 2 - 280, y + 10), (w // 2 + 280, y + 10), 2)
    y += 30
    
    # Información del juego
    fuente_info = _f("Arial", 18)
    info_lines = [
        "🔵 Pellets: 10 pts · ⭕ Super: 50 pts + miedo ~10 s",
        "👻 Comer fantasma asustado: 200 pts (texto flotante +200)",
        "Rojo+antena: PRNG · Rosa+rombo: caza adelantada · Naranja+⌃: emboscada (tímido cerca)",
        "⚡ Roguelike: al superar el umbral de pellets → +1 fantasma y más velocidad",
        "🎁 Fin de nivel: botín con probabilidades PRNG (ranking guarda semilla)",
        "🎯 Objetivo: vaciar el laberinto y subir de nivel con mapa nuevo",
    ]
    
    for line in info_lines:
        txt = fuente_info.render(line, True, COLOR_BLANCO)
        surf.blit(txt, (w // 2 - 260, y))
        y += 32
    
    # Hint
    fuente_hint = _f("Arial", 14)
    hint_txt = fuente_hint.render("ENTER / ESC  VOLVER", True, COLOR_GRIS)
    surf.blit(hint_txt, (w // 2 - hint_txt.get_width() // 2, h - 36))


def dibujar_pausa_overlay(surf: pygame.Surface, ancho: int, alto: int) -> None:
    """Overlay de pausa con fondo semi-transparente."""
    ov = pygame.Surface((ancho, alto), pygame.SRCALPHA)
    ov.fill((0, 0, 0, 180))
    surf.blit(ov, (0, 0))
    
    # Título PAUSA
    fuente_pausa = _f("Arial Black", 52, True)
    t = fuente_pausa.render("PAUSA", True, COLOR_AMARILLO)
    surf.blit(t, (ancho // 2 - t.get_width() // 2, alto // 2 - 80))
    
    # Opciones
    fuente_op = _f("Arial", 22, True)
    opciones = [
        ("ESC", "Reanudar", COLOR_CYAN),
        ("Q", "Menú principal", COLOR_ROSA),
        ("M", "Alternar música", COLOR_VERDE),
    ]
    
    y = alto // 2 - 10
    for tecla, desc, color in opciones:
        # Tecla resaltada
        txt_tecla = fuente_op.render(f"[{tecla}]", True, color)
        txt_desc = fuente_op.render(f" {desc}", True, COLOR_BLANCO)
        
        x_start = ancho // 2 - (txt_tecla.get_width() + txt_desc.get_width()) // 2
        surf.blit(txt_tecla, (x_start, y))
        surf.blit(txt_desc, (x_start + txt_tecla.get_width(), y))
        y += 40


def dibujar_game_over_pantalla(
    surf: pygame.Surface,
    ancho: int,
    alto: int,
    puntaje: int,
    es_record: bool,
) -> None:
    """Pantalla de Game Over."""
    ov = pygame.Surface((ancho, alto), pygame.SRCALPHA)
    ov.fill((0, 0, 50, 200))
    surf.blit(ov, (0, 0))
    
    # Título GAME OVER
    fuente_go = _f("Arial Black", 56, True)
    t = fuente_go.render("GAME OVER", True, COLOR_ROJO)
    surf.blit(t, (ancho // 2 - t.get_width() // 2, alto // 2 - 120))
    
    # Puntaje final
    fuente_pts = _f("Arial", 28, True)
    p = fuente_pts.render(f"PUNTAJE FINAL", True, COLOR_AMARILLO)
    surf.blit(p, (ancho // 2 - p.get_width() // 2, alto // 2 - 40))
    
    fuente_num = _f("Courier New", 36, True)
    num = fuente_num.render(f"{puntaje:06d}", True, COLOR_BLANCO)
    surf.blit(num, (ancho // 2 - num.get_width() // 2, alto // 2))
    
    # Record
    if es_record:
        fuente_rec = _f("Arial", 24, True)
        r = fuente_rec.render("¡ENTRASTE EN EL TOP 10!", True, COLOR_VERDE)
        surf.blit(r, (ancho // 2 - r.get_width() // 2, alto // 2 + 50))
    
    # Hint
    fuente_hint = _f("Arial", 18)
    h = fuente_hint.render("ENTER  MENÚ PRINCIPAL", True, COLOR_GRIS)
    surf.blit(h, (ancho // 2 - h.get_width() // 2, alto // 2 + 100))


def dibujar_victoria_nivel(
    surf: pygame.Surface,
    ancho: int,
    alto: int,
    nivel_terminado: int,
    siguiente_nivel: int,
    tick: int,
    *,
    loot: dict | None = None,
    semilla: int = 0,
) -> None:
    """Pantalla de victoria roguelike: nuevo mapa, botín y semilla."""
    ov = pygame.Surface((ancho, alto), pygame.SRCALPHA)
    ov.fill((0, 40, 55, 195))
    surf.blit(ov, (0, 0))

    # Marco decorativo tipo recreativa
    borde = pygame.Rect(24, 80, ancho - 48, alto - 160)
    pygame.draw.rect(surf, (20, 20, 80), borde, border_radius=12)
    pygame.draw.rect(surf, COLOR_AMARILLO, borde, width=4, border_radius=12)

    a = 0.85 + 0.15 * math.sin(tick * 0.1)
    color_anim = (int(255 * a), int(255 * a), int(80 * a))

    fuente_vic = _f("Arial Black", 44, True)
    t = fuente_vic.render("¡NIVEL COMPLETADO!", True, color_anim)
    surf.blit(t, (ancho // 2 - t.get_width() // 2, 100))

    fuente_sub = _f("Arial", 17, True)
    sub = fuente_sub.render("ROGUELIKE — NUEVO LABERINTO PROCEDURAL", True, COLOR_CYAN)
    surf.blit(sub, (ancho // 2 - sub.get_width() // 2, 152))

    fuente_info = _f("Arial", 24, True)
    n1 = fuente_info.render(f"Nivel {nivel_terminado}  →  {siguiente_nivel}", True, COLOR_BLANCO)
    surf.blit(n1, (ancho // 2 - n1.get_width() // 2, 188))

    # Tarjeta de botín (Fase 5)
    card_y = 228
    card = pygame.Rect(ancho // 2 - 200, card_y, 400, 118)
    pygame.draw.rect(surf, (12, 14, 40), card, border_radius=10)
    pygame.draw.rect(surf, COLOR_VERDE, card, width=2, border_radius=10)

    fu_loot_t = _f("Arial", 16, True)
    surf.blit(fu_loot_t.render("BOTÍN DEL NIVEL (PRNG)", True, COLOR_VERDE), (card.x + 14, card.y + 10))

    if loot:
        nombre = str(loot.get("nombre", "?"))
        desc = str(loot.get("desc", ""))
        pts = loot.get("puntos", 0)
        rid = str(loot.get("id", ""))
        rareza = {
            "legendario": COLOR_AMARILLO,
            "raro": COLOR_CYAN,
            "comun": COLOR_BLANCO,
            "vida": COLOR_ROSA,
        }.get(rid, COLOR_BLANCO)
        fu_nom = _f("Arial", 22, True)
        surf.blit(fu_nom.render(nombre, True, rareza), (card.x + 14, card.y + 36))
        fu_d = _f("Arial", 15)
        linea = f"+{pts} pts" if pts else "Efecto especial"
        if rid == "vida":
            linea = "+1 vida"
        surf.blit(fu_d.render(linea, True, COLOR_GRIS), (card.x + 14, card.y + 64))
        surf.blit(fu_d.render(desc[:52], True, (160, 170, 200)), (card.x + 14, card.y + 86))
    else:
        fu_d = _f("Arial", 18)
        surf.blit(fu_d.render("Sin botín esta vez — la run sigue.", True, COLOR_GRIS), (card.x + 14, card.y + 48))

    fu_seed = _f("Courier New", 15)
    seed_txt = fu_seed.render(f"Semilla de run: {semilla}", True, (140, 200, 255))
    surf.blit(seed_txt, (ancho // 2 - seed_txt.get_width() // 2, card_y + 128))

    for i in range(3):
        offset_x = -40 + i * 40
        offset_y = 10 * math.sin(tick * 0.15 + i)
        _dibujar_pacman(
            surf,
            ancho // 2 + offset_x,
            alto - 120 + offset_y,
            12,
            20 + 10 * abs(math.sin(tick * 0.2 + i)),
            0,
        )

    fuente_hint = _f("Arial", 17, True)
    hint_txt = fuente_hint.render("ENTER / ESPACIO  CONTINUAR", True, COLOR_AMARILLO)
    surf.blit(hint_txt, (ancho // 2 - hint_txt.get_width() // 2, alto - 48))
