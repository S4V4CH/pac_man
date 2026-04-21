# src/ui/menu.py
"""Menús completos del Pac-Man Roguelike: principal, mejoras, tienda, victoria."""

from __future__ import annotations

import math
import pygame

# ─── Paleta clásica Pac-Man ───────────────────────────────────────────────────
COLOR_BG         = (0, 0, 0)
COLOR_BG_DARK    = (5, 5, 20)
COLOR_AZUL_OSC   = (0, 0, 128)
COLOR_PANEL      = (10, 12, 35)
COLOR_AMARILLO   = (255, 255, 0)
COLOR_BLANCO     = (255, 255, 255)
COLOR_CYAN       = (0, 255, 255)
COLOR_ROJO       = (255, 0, 0)
COLOR_ROSA       = (255, 184, 255)
COLOR_NARANJA    = (255, 184, 82)
COLOR_AZUL       = (33, 33, 255)
COLOR_VERDE      = (0, 255, 0)
COLOR_GRIS       = (130, 130, 130)
COLOR_GRIS_OSC   = (60, 60, 70)
COLOR_ORO        = (255, 215, 0)


def _f(name: str, size: int, bold: bool = False) -> pygame.font.Font:
    try:
        return pygame.font.SysFont(name, size, bold=bold)
    except (OSError, AttributeError):
        return pygame.font.Font(None, size)


# ─── Primitivos compartidos ───────────────────────────────────────────────────

def _dibujar_pacman(surf, x, y, radio, apertura, direccion=0):
    """
    Círculo menos sector de boca. El hueco debe seguir el arco del círculo
    (no un triángulo centro–cuerda), si no queda un segmento amarillo en la boca.
    """
    cx, cy = float(x), float(y)
    pygame.draw.circle(surf, COLOR_AMARILLO, (int(cx), int(cy)), radio)
    ang_base = direccion * 90
    n = max(12, int(apertura) + 8)
    puntos: list[tuple[float, float]] = [(cx, cy)]
    for i in range(n + 1):
        ang_deg = ang_base + apertura - (2 * apertura * i / n)
        a = math.radians(ang_deg)
        puntos.append((cx + radio * math.cos(a), cy - radio * math.sin(a)))
    pygame.draw.polygon(surf, COLOR_BG, puntos)


def _dibujar_fantasma(surf, x, y, color, tamano=20, asustado=False):
    c = COLOR_AZUL if asustado else color
    pygame.draw.circle(surf, c, (int(x), int(y) - tamano // 3), tamano // 2)
    pts = [
        (int(x - tamano // 2), int(y - tamano // 3)),
        (int(x - tamano // 2), int(y + tamano // 2)),
        (int(x - tamano // 3), int(y + tamano // 3)),
        (int(x), int(y + tamano // 2)),
        (int(x + tamano // 3), int(y + tamano // 3)),
        (int(x + tamano // 2), int(y + tamano // 2)),
        (int(x + tamano // 2), int(y - tamano // 3)),
    ]
    pygame.draw.polygon(surf, c, pts)
    ojo_tam = tamano // 4
    for ox in [-tamano // 4, tamano // 4]:
        pygame.draw.circle(surf, COLOR_BLANCO, (int(x + ox), int(y - tamano // 4)), ojo_tam)
        pygame.draw.circle(surf, COLOR_AZUL, (int(x + ox), int(y - tamano // 4)), ojo_tam // 2)


def _dibujar_pellet(surf, x, y, grande=False):
    radio = 6 if grande else 2
    color = COLOR_ROSA if grande else COLOR_BLANCO
    pygame.draw.circle(surf, color, (int(x), int(y)), radio)


def _dibujar_icono_moneda(surf: pygame.Surface, cx: int, cy: int, radio: int = 11) -> None:
    """Moneda dibujada a mano (sin emoji): legible en Windows y sin recortes."""
    pygame.draw.circle(surf, (160, 110, 0), (cx + 1, cy + 1), radio)
    pygame.draw.circle(surf, COLOR_ORO, (cx, cy), radio)
    pygame.draw.circle(surf, (255, 245, 180), (cx - radio // 3, cy - radio // 3), max(3, radio // 3))
    pygame.draw.circle(surf, (200, 150, 0), (cx, cy), radio, 2)


def _tam_badge_monedas(cantidad: int) -> tuple[int, int, pygame.Surface, pygame.Surface]:
    panel_pad = 12
    coin_r = 11
    fu_lbl = _f("Arial", 13, True)
    fu_num = _f("Courier New", 24, True)
    lbl_s = fu_lbl.render("MONEDAS", True, COLOR_GRIS)
    num_s = fu_num.render(f"{cantidad:,}", True, COLOR_AMARILLO)
    inner_w = max(lbl_s.get_width(), num_s.get_width())
    panel_w = panel_pad + (coin_r * 2) + 14 + inner_w + panel_pad
    panel_h = 54
    return panel_w, panel_h, lbl_s, num_s


def _dibujar_badge_monedas_en(
    surf: pygame.Surface,
    cantidad: int,
    panel_x: int,
    panel_y: int,
) -> None:
    panel_pad = 12
    coin_r = 11
    panel_w, panel_h, lbl_s, num_s = _tam_badge_monedas(cantidad)
    pygame.draw.rect(surf, COLOR_PANEL, (panel_x, panel_y, panel_w, panel_h), border_radius=12)
    pygame.draw.rect(surf, COLOR_ORO, (panel_x, panel_y, panel_w, panel_h), width=3, border_radius=12)
    cx = panel_x + panel_pad + coin_r
    cy = panel_y + panel_h // 2
    _dibujar_icono_moneda(surf, cx, cy, coin_r)
    tx = panel_x + panel_pad + coin_r * 2 + 14
    surf.blit(lbl_s, (tx, panel_y + 7))
    surf.blit(num_s, (tx, panel_y + 24))


def _titulo_animado(surf, texto, y, t):
    fuente = _f("Arial Black", 56, True)
    pulse = 0.9 + 0.1 * math.sin(t * 0.08)
    color = (255, int(255 * pulse), 0)
    sombra = fuente.render(texto, True, (100, 100, 0))
    main = fuente.render(texto, True, color)
    x = surf.get_width() // 2 - main.get_width() // 2
    surf.blit(sombra, (x + 4, int(y) + 4))
    surf.blit(main, (x, int(y)))


# ─── Iconos de mejoras dibujados con primitivas ───────────────────────────────

def _dibujar_icono_mejora(surf: pygame.Surface, cx: int, cy: int,
                           icono_id: str, color: tuple, size: int = 26) -> None:
    """Dibuja el ícono representativo de cada tipo de mejora."""

    if icono_id == 'freeze':
        # Copo de nieve: 6 brazos
        for i in range(6):
            ang = math.radians(i * 60)
            ex = int(cx + size * math.cos(ang))
            ey = int(cy + size * math.sin(ang))
            pygame.draw.line(surf, color, (cx, cy), (ex, ey), 2)
            # Ramitas
            for d in [-1, 1]:
                mid_x = int(cx + size * 0.55 * math.cos(ang))
                mid_y = int(cy + size * 0.55 * math.sin(ang))
                ba = ang + d * math.radians(45)
                bx = int(mid_x + size * 0.28 * math.cos(ba))
                by = int(mid_y + size * 0.28 * math.sin(ba))
                pygame.draw.line(surf, color, (mid_x, mid_y), (bx, by), 2)
        pygame.draw.circle(surf, color, (cx, cy), 4)

    elif icono_id == 'shield':
        # Escudo hexagonal
        pts = [
            (cx, cy - size),
            (cx + int(size * 0.82), cy - size // 2),
            (cx + int(size * 0.82), cy + size // 3),
            (cx, cy + size),
            (cx - int(size * 0.82), cy + size // 3),
            (cx - int(size * 0.82), cy - size // 2),
        ]
        glow = pygame.Surface((size * 2 + 10, size * 2 + 10), pygame.SRCALPHA)
        gpts = [(p[0] - cx + size + 5, p[1] - cy + size + 5) for p in pts]
        pygame.draw.polygon(glow, (*color, 40), gpts)
        surf.blit(glow, (cx - size - 5, cy - size - 5))
        pygame.draw.polygon(surf, color, pts, 0)
        pygame.draw.polygon(surf, (255, 255, 255), pts, 2)
        # Cruz central
        pygame.draw.line(surf, (255, 255, 255), (cx, cy - size // 2), (cx, cy + size // 3), 3)
        pygame.draw.line(surf, (255, 255, 255), (cx - size // 3, cy - size // 8),
                         (cx + size // 3, cy - size // 8), 3)

    elif icono_id == 'boots':
        # Rayo (velocidad)
        pts = [
            (cx + size // 4, cy - size),
            (cx - size // 6, cy - size // 10),
            (cx + size // 5, cy - size // 10),
            (cx - size // 4, cy + size),
            (cx + size // 6, cy + size // 10),
            (cx - size // 5, cy + size // 10),
        ]
        pygame.draw.polygon(surf, color, pts)
        pygame.draw.polygon(surf, (255, 255, 200), pts, 2)

    elif icono_id == 'fever':
        # Estrella de 8 puntas
        for i in range(8):
            ang_out = math.radians(i * 45)
            ang_in = math.radians(i * 45 + 22.5)
            ox = int(cx + size * math.cos(ang_out))
            oy = int(cy + size * math.sin(ang_out))
            ix = int(cx + size * 0.45 * math.cos(ang_in))
            iy = int(cy + size * 0.45 * math.sin(ang_in))
            pygame.draw.line(surf, color, (cx, cy), (ox, oy), 2)
            pygame.draw.circle(surf, color, (ox, oy), 3)
        pygame.draw.circle(surf, (255, 240, 100), (cx, cy), size // 3)
        pygame.draw.circle(surf, color, (cx, cy), size // 3, 2)

    elif icono_id == 'coins':
        # Monedas apiladas (recompensa tienda)
        pygame.draw.circle(surf, (160, 110, 0), (cx + 2, cy + 2), size // 2 + 2)
        pygame.draw.circle(surf, (220, 170, 40), (cx - 3, cy - 2), size // 2)
        pygame.draw.circle(surf, color, (cx, cy), size // 2)
        pygame.draw.circle(surf, (255, 245, 200), (cx - size // 4, cy - size // 4), max(2, size // 4))
        pygame.draw.circle(surf, (180, 130, 0), (cx, cy), size // 2, 2)

    elif icono_id == 'ghost_mode':
        # Silueta de fantasma semitransparente
        gsurf = pygame.Surface((size * 2 + 4, size * 2 + 4), pygame.SRCALPHA)
        gc = size + 2
        pygame.draw.circle(gsurf, (*color, 180), (gc, gc - size // 3), size // 2)
        gpts = [
            (gc - size // 2, gc - size // 3),
            (gc - size // 2, gc + size // 2),
            (gc - size // 3, gc + size // 4),
            (gc, gc + size // 2),
            (gc + size // 3, gc + size // 4),
            (gc + size // 2, gc + size // 2),
            (gc + size // 2, gc - size // 3),
        ]
        pygame.draw.polygon(gsurf, (*color, 180), gpts)
        surf.blit(gsurf, (cx - size - 2, cy - size - 2))
        # Ojos blancos brillantes
        ejo_r = max(2, size // 5)
        for ox_e in [-size // 4, size // 4]:
            pygame.draw.circle(surf, (255, 255, 255), (cx + ox_e, cy - size // 3), ejo_r)

    elif icono_id == 'life':
        # Corazón (dos círculos + triángulo)
        r = size // 2
        pygame.draw.circle(surf, color, (cx - r // 2, cy - r // 3), r // 2 + 1)
        pygame.draw.circle(surf, color, (cx + r // 2, cy - r // 3), r // 2 + 1)
        pts = [
            (cx - r, cy - r // 3),
            (cx + r, cy - r // 3),
            (cx, cy + int(r * 1.1)),
        ]
        pygame.draw.polygon(surf, color, pts)
        # Brillo
        pygame.draw.circle(surf, (255, 180, 180), (cx - r // 3, cy - r // 2), max(2, r // 5))


# ─── Tarjeta de mejora ────────────────────────────────────────────────────────

def _dibujar_tarjeta_mejora(
    surf: pygame.Surface,
    x: int, y: int,
    ancho: int, alto: int,
    mejora: dict,
    nivel_actual: int,
    desc_siguiente: str,
    seleccionada: bool,
    hover: bool,
    tiempo_ui: int,
) -> pygame.Rect:
    """
    Dibuja una tarjeta de mejora roguelike y retorna su Rect para detección de clicks.
    """
    rect = pygame.Rect(x, y, ancho, alto)
    color_b = mejora['color']
    color_borde = mejora['color_borde']
    max_nivel = mejora['max_nivel']

    # ── Fondo de la tarjeta ──
    bg_surf = pygame.Surface((ancho, alto), pygame.SRCALPHA)
    bg_surf.fill((8, 10, 30, 230))
    surf.blit(bg_surf, (x, y))

    # ── Borde con brillo si está seleccionada ──
    borde_w = 3 if not seleccionada else 4
    borde_color = color_borde if not seleccionada else color_b
    if seleccionada or hover:
        # Glow pulsante
        glow_a = int(80 + 60 * math.sin(tiempo_ui * 0.12))
        for offset in range(4, 0, -1):
            glow_surf = pygame.Surface((ancho + offset * 2, alto + offset * 2), pygame.SRCALPHA)
            pygame.draw.rect(glow_surf, (*color_b, glow_a // (offset + 1)),
                             (0, 0, ancho + offset * 2, alto + offset * 2),
                             border_radius=14)
            surf.blit(glow_surf, (x - offset, y - offset))

    pygame.draw.rect(surf, (15, 18, 45), rect, border_radius=12)
    pygame.draw.rect(surf, borde_color, rect, width=borde_w, border_radius=12)

    # ── Franja superior con color de tipo ──
    franja = pygame.Rect(x + borde_w, y + borde_w, ancho - borde_w * 2, 6)
    pygame.draw.rect(surf, color_b, franja, border_radius=6)

    # ── Ícono centrado ──
    icon_cx = x + ancho // 2
    icon_cy = y + 62
    _dibujar_icono_mejora(surf, icon_cx, icon_cy, mejora['icono'], color_b, size=24)

    # ── Nombre ──
    fu_nombre = _f("Arial", 15, True)
    nombre_surf = fu_nombre.render(mejora['nombre'], True, color_b)
    surf.blit(nombre_surf, (x + ancho // 2 - nombre_surf.get_width() // 2, y + 100))

    # ── Nivel actual ──
    if max_nivel == -1:
        nivel_txt = "Efecto inmediato"
        nivel_color = COLOR_AMARILLO
    elif nivel_actual >= max_nivel:
        nivel_txt = "NIVEL MÁXIMO"
        nivel_color = COLOR_ORO
    else:
        nivel_txt = f"Nv. {nivel_actual + 1}" if nivel_actual == 0 else f"Nv. {nivel_actual} → {nivel_actual + 1}"
        nivel_color = COLOR_GRIS

    fu_nivel = _f("Arial", 12, True)
    nivel_surf = fu_nivel.render(nivel_txt, True, nivel_color)
    surf.blit(nivel_surf, (x + ancho // 2 - nivel_surf.get_width() // 2, y + 120))

    # ── Separador ──
    pygame.draw.line(surf, color_borde,
                     (x + 16, y + 138), (x + ancho - 16, y + 138), 1)

    # ── Descripción (multilinea) ──
    fu_desc = _f("Arial", 12)
    lineas = desc_siguiente.split('\n')
    dy = y + 148
    for linea in lineas[:3]:
        ls = fu_desc.render(linea.strip(), True, COLOR_BLANCO)
        surf.blit(ls, (x + ancho // 2 - ls.get_width() // 2, dy))
        dy += 18

    # ── Botón inferior ──
    btn_rect = pygame.Rect(x + 14, y + alto - 42, ancho - 28, 30)
    btn_color = color_b if (seleccionada or hover) else color_borde
    pygame.draw.rect(surf, btn_color, btn_rect, border_radius=8)
    fu_btn = _f("Arial", 13, True)
    btn_txt = fu_btn.render("SELECCIONAR", True, COLOR_BG)
    surf.blit(btn_txt, (btn_rect.x + btn_rect.w // 2 - btn_txt.get_width() // 2,
                        btn_rect.y + btn_rect.h // 2 - btn_txt.get_height() // 2))

    return rect


# ─── Pantalla de selección de mejora ─────────────────────────────────────────

def dibujar_seleccion_mejora(
    surf: pygame.Surface,
    ancho: int, alto: int,
    opciones: list[dict],
    nivel_actual_fn,   # callable(mid) → nivel actual
    desc_siguiente_fn, # callable(mid) → str descripción
    seleccionada: int,
    tiempo_ui: int,
    mouse_pos: tuple[int, int],
    nivel_mejora: int,
    umbral_exp: int,
    *,
    recompensa_por_nivel: bool = False,
) -> list[pygame.Rect]:
    """
    Pantalla de selección de mejora roguelike con 3 tarjetas.
    Retorna lista de Rects para detección de clicks (una por opción).
    """
    # Overlay oscuro
    ov = pygame.Surface((ancho, alto), pygame.SRCALPHA)
    ov.fill((0, 0, 15, 210))
    surf.blit(ov, (0, 0))

    # ── Encabezado (EXP vs recompensa por completar laberinto) ──
    fu_titulo = _f("Arial Black", 34 if recompensa_por_nivel else 36, True)
    a = 0.8 + 0.2 * math.sin(tiempo_ui * 0.1)
    color_titulo = (int(255 * a), int(255 * a), int(80 * a))
    if recompensa_por_nivel:
        tit_txt = "¡LABERINTO COMPLETADO!"
        sub_txt = "Misma recompensa que al subir de EXP: elige una mejora roguelike"
        hint_txt = "Haz clic o 1 · 2 · 3  ·  Luego sigues al siguiente nivel"
    else:
        tit_txt = "¡SUBISTE DE NIVEL (EXP)!"
        sub_txt = f"Mejora #{nivel_mejora}  ·  Próximo umbral: {umbral_exp} pts  ·  Elige una carta"
        hint_txt = "Haz clic en una tarjeta o usa las teclas  1 · 2 · 3"
    tit = fu_titulo.render(tit_txt, True, color_titulo)
    surf.blit(tit, (ancho // 2 - tit.get_width() // 2, 34))

    fu_sub = _f("Arial", 16, True)
    sub = fu_sub.render(sub_txt, True, COLOR_CYAN)
    surf.blit(sub, (ancho // 2 - sub.get_width() // 2, 78))

    fu_hint = _f("Arial", 14)
    hint = fu_hint.render(hint_txt, True, COLOR_GRIS)
    surf.blit(hint, (ancho // 2 - hint.get_width() // 2, 102))

    # ── Tarjetas ──
    n_opciones = len(opciones)
    card_w = 185
    card_h = 258
    gap = 22
    total_w = n_opciones * card_w + (n_opciones - 1) * gap
    start_x = ancho // 2 - total_w // 2
    card_y = 140

    rects: list[pygame.Rect] = []
    for i, op in enumerate(opciones):
        cx = start_x + i * (card_w + gap)
        nivel_a = nivel_actual_fn(op['id'])
        desc = desc_siguiente_fn(op['id'])
        hover = pygame.Rect(cx, card_y, card_w, card_h).collidepoint(mouse_pos)
        r = _dibujar_tarjeta_mejora(
            surf, cx, card_y, card_w, card_h,
            op, nivel_a, desc,
            seleccionada=i == seleccionada,
            hover=hover,
            tiempo_ui=tiempo_ui,
        )
        rects.append(r)

        # Número de tecla
        fu_num = _f("Arial", 22, True)
        num_s = fu_num.render(str(i + 1), True, COLOR_AMARILLO if i == seleccionada else COLOR_GRIS)
        surf.blit(num_s, (cx + card_w // 2 - num_s.get_width() // 2, card_y + card_h + 10))

    # Pac-Man decorativo animado
    pac_x = ancho // 2 + int(80 * math.cos(tiempo_ui * 0.04))
    pac_y = alto - 50
    aper = 20 + 15 * abs(math.sin(tiempo_ui * 0.15))
    _dibujar_pacman(surf, pac_x, pac_y, 13, aper, 0)

    return rects


# ─── Victoria de nivel con botones ───────────────────────────────────────────

def dibujar_victoria_nivel(
    surf: pygame.Surface,
    ancho: int, alto: int,
    nivel_terminado: int,
    siguiente_nivel: int,
    tick: int,
    *,
    loot: dict | None = None,
    semilla: int = 0,
    mouse_pos: tuple[int, int] = (0, 0),
) -> tuple[pygame.Rect, pygame.Rect]:
    """
    Pantalla de nivel completado con botones Menú Principal / Continuar.
    Retorna (rect_menu, rect_continuar).
    """
    ov = pygame.Surface((ancho, alto), pygame.SRCALPHA)
    ov.fill((0, 40, 55, 195))
    surf.blit(ov, (0, 0))

    # Marco principal
    borde = pygame.Rect(24, 55, ancho - 48, alto - 110)
    pygame.draw.rect(surf, (12, 15, 45), borde, border_radius=16)
    pygame.draw.rect(surf, COLOR_AMARILLO, borde, width=4, border_radius=16)

    # Título animado
    a = 0.85 + 0.15 * math.sin(tick * 0.1)
    color_anim = (int(255 * a), int(255 * a), int(80 * a))
    fu_vic = _f("Arial Black", 40, True)
    t = fu_vic.render("¡NIVEL COMPLETADO!", True, color_anim)
    surf.blit(t, (ancho // 2 - t.get_width() // 2, 72))

    fu_sub = _f("Arial", 16, True)
    sub = fu_sub.render("ROGUELIKE — NUEVO LABERINTO PROCEDURAL", True, COLOR_CYAN)
    surf.blit(sub, (ancho // 2 - sub.get_width() // 2, 118))

    # Info nivel
    fu_info = _f("Arial", 28, True)
    n1 = fu_info.render(f"Nivel  {nivel_terminado}  →  Nivel  {siguiente_nivel}", True, COLOR_BLANCO)
    surf.blit(n1, (ancho // 2 - n1.get_width() // 2, 150))

    # Tarjeta de botín
    card_y = 195
    card = pygame.Rect(ancho // 2 - 210, card_y, 420, 120)
    pygame.draw.rect(surf, (10, 14, 40), card, border_radius=12)
    pygame.draw.rect(surf, COLOR_VERDE, card, width=2, border_radius=12)

    fu_loot_t = _f("Arial", 15, True)
    surf.blit(fu_loot_t.render("BOTÍN DEL NIVEL (PRNG)", True, COLOR_VERDE), (card.x + 16, card.y + 10))

    if loot:
        nombre = str(loot.get("nombre", "?"))
        desc = str(loot.get("desc", ""))
        pts = loot.get("puntos", 0)
        rid = str(loot.get("id", ""))
        rareza = {"legendario": COLOR_AMARILLO, "raro": COLOR_CYAN,
                  "comun": COLOR_BLANCO, "vida": COLOR_ROSA}.get(rid, COLOR_BLANCO)
        fu_nom = _f("Arial", 21, True)
        surf.blit(fu_nom.render(nombre, True, rareza), (card.x + 16, card.y + 36))
        fu_d = _f("Arial", 14)
        linea = f"+{pts} pts" if pts else ("Efecto especial" if rid != "vida" else "+1 vida")
        surf.blit(fu_d.render(linea, True, COLOR_GRIS), (card.x + 16, card.y + 64))
        surf.blit(fu_d.render(desc[:54], True, (160, 170, 200)), (card.x + 16, card.y + 84))
    else:
        fu_d = _f("Arial", 17)
        surf.blit(fu_d.render("Sin botín esta vez — ¡la run sigue!", True, COLOR_GRIS),
                  (card.x + 16, card.y + 46))

    fu_seed = _f("Courier New", 14)
    seed_txt = fu_seed.render(f"Semilla de run: {semilla}", True, (140, 200, 255))
    surf.blit(seed_txt, (ancho // 2 - seed_txt.get_width() // 2, card_y + 130))

    # Pregunta al jugador
    fu_q = _f("Arial", 20, True)
    q_txt = fu_q.render(
        f"¿Deseas continuar al Nivel {siguiente_nivel}?",
        True, COLOR_BLANCO,
    )
    surf.blit(q_txt, (ancho // 2 - q_txt.get_width() // 2, alto - 148))

    # ── Botones ──
    btn_w, btn_h = 200, 44
    gap_btns = 24
    total_btns = btn_w * 2 + gap_btns
    btn_x0 = ancho // 2 - total_btns // 2

    # Botón Menú Principal
    rect_menu = pygame.Rect(btn_x0, alto - 110, btn_w, btn_h)
    hover_menu = rect_menu.collidepoint(mouse_pos)
    pygame.draw.rect(surf, (60, 20, 20) if hover_menu else (40, 10, 10), rect_menu, border_radius=10)
    pygame.draw.rect(surf, COLOR_ROJO if hover_menu else (150, 30, 30), rect_menu, width=2, border_radius=10)
    fu_btn = _f("Arial", 15, True)
    bt = fu_btn.render("MENÚ PRINCIPAL", True, COLOR_BLANCO)
    surf.blit(bt, (rect_menu.centerx - bt.get_width() // 2, rect_menu.centery - bt.get_height() // 2))

    # Botón Continuar
    rect_cont = pygame.Rect(btn_x0 + btn_w + gap_btns, alto - 110, btn_w, btn_h)
    hover_cont = rect_cont.collidepoint(mouse_pos)
    pygame.draw.rect(surf, (20, 80, 20) if hover_cont else (10, 50, 10), rect_cont, border_radius=10)
    pygame.draw.rect(surf, COLOR_VERDE if hover_cont else (30, 150, 30), rect_cont, width=2, border_radius=10)
    ct = fu_btn.render("CONTINUAR →", True, COLOR_BLANCO)
    surf.blit(ct, (rect_cont.centerx - ct.get_width() // 2, rect_cont.centery - ct.get_height() // 2))

    # Hint de teclado
    fu_hint = _f("Arial", 12)
    ht = fu_hint.render("M · Menú Principal       ENTER / ESPACIO · Continuar", True, COLOR_GRIS)
    surf.blit(ht, (ancho // 2 - ht.get_width() // 2, alto - 58))

    # Pac-Men decorativos
    for i in range(3):
        ofs_x = -44 + i * 44
        ofs_y = 10 * math.sin(tick * 0.15 + i)
        _dibujar_pacman(surf, ancho // 2 + ofs_x, alto - 35 + ofs_y,
                        11, 20 + 10 * abs(math.sin(tick * 0.2 + i)), 0)

    return rect_menu, rect_cont


# ─── Tienda permanente ────────────────────────────────────────────────────────

def dibujar_menu_tienda(
    surf: pygame.Surface,
    tienda,              # SistemaTienda
    indice_sel: int,
    tiempo_ui: int,
    mouse_pos: tuple[int, int] = (0, 0),
) -> list[pygame.Rect]:
    """
    Pantalla de la tienda de mejoras permanentes.
    Retorna lista de Rects de botones de compra.
    """
    from src.sistemas.tienda import TIENDA_ITEMS

    surf.fill(COLOR_BG_DARK)
    w, h = surf.get_width(), surf.get_height()

    # Decoración esquinas
    for px in range(40, w, 60):
        _dibujar_pellet(surf, px, 22, False)
        _dibujar_pellet(surf, px, h - 22, False)
    _dibujar_pellet(surf, 30, 30, True)
    _dibujar_pellet(surf, w - 30, 30, True)

    # Título
    fu_t = _f("Arial Black", 42, True)
    t_surf = fu_t.render("TIENDA", True, COLOR_ORO)
    surf.blit(t_surf, (w // 2 - t_surf.get_width() // 2, 35))

    fu_sub = _f("Arial", 18, True)
    sub = fu_sub.render("MEJORAS PERMANENTES — persisten entre todas las runs", True, COLOR_CYAN)
    surf.blit(sub, (w // 2 - sub.get_width() // 2, 88))

    pw, _, _, _ = _tam_badge_monedas(tienda.monedas)
    _dibujar_badge_monedas_en(surf, tienda.monedas, w // 2 - pw // 2, 100)

    fu_hint_m = _f("Arial", 13)
    hm = fu_hint_m.render("Ganas monedas = puntaje final de cada run al terminar", True, COLOR_GRIS)
    surf.blit(hm, (w // 2 - hm.get_width() // 2, 158))

    # Separador
    pygame.draw.line(surf, COLOR_AZUL_OSC, (40, 168), (w - 40, 168), 2)

    # Items de la tienda
    rects_comprar: list[pygame.Rect] = []
    item_y = 185

    for idx, item in enumerate(TIENDA_ITEMS):
        nivel_actual = tienda.nivel_de(item['id'])
        max_n = item['max_nivel']
        puede = tienda.puede_comprar(item['id'])
        costo_sig = tienda.costo_siguiente(item['id'])
        color_i = item['color']
        color_b = item['color_borde']

        # Panel del item
        panel = pygame.Rect(w // 2 - 320, item_y, 640, 135)
        sel = idx == indice_sel
        hover_p = panel.collidepoint(mouse_pos)

        pygame.draw.rect(surf, (12, 16, 40), panel, border_radius=14)
        borde_color = color_i if (sel or hover_p) else color_b
        pygame.draw.rect(surf, borde_color, panel, width=3 if (sel or hover_p) else 2,
                         border_radius=14)

        # Franja superior
        pygame.draw.rect(surf, color_b,
                         pygame.Rect(panel.x + 3, panel.y + 3, panel.w - 6, 5),
                         border_radius=6)

        # Ícono
        _dibujar_icono_mejora(surf, panel.x + 52, panel.centery - 5, item['icono'], color_i, 22)

        # Nombre y nivel
        fu_n = _f("Arial", 18, True)
        surf.blit(fu_n.render(item['nombre'], True, color_i),
                  (panel.x + 96, panel.y + 18))
        fu_nv = _f("Arial", 14)
        nv_txt = (f"Nivel {nivel_actual} / {max_n}" if nivel_actual < max_n
                  else f"Nivel {nivel_actual} / {max_n}  —  MÁXIMO")
        surf.blit(fu_nv.render(nv_txt, True, COLOR_ORO if nivel_actual >= max_n else COLOR_GRIS),
                  (panel.x + 96, panel.y + 42))

        # Descripción del nivel actual obtenido
        if nivel_actual > 0:
            desc_act = item['niveles_desc'][nivel_actual - 1]
            fu_da = _f("Arial", 13)
            surf.blit(fu_da.render(f"Tienes: {desc_act}", True, (160, 200, 160)),
                      (panel.x + 96, panel.y + 63))

        # Descripción del siguiente nivel
        if nivel_actual < max_n:
            desc_sig = item['niveles_desc'][nivel_actual]
            fu_ds = _f("Arial", 13)
            surf.blit(fu_ds.render(f"Siguiente: {desc_sig}", True, COLOR_BLANCO),
                      (panel.x + 96, panel.y + 82))

        # Botón comprar
        btn_r = pygame.Rect(panel.right - 174, panel.centery - 20, 160, 40)
        hover_btn = btn_r.collidepoint(mouse_pos)

        if nivel_actual >= max_n:
            pygame.draw.rect(surf, (30, 30, 30), btn_r, border_radius=10)
            pygame.draw.rect(surf, COLOR_GRIS_OSC, btn_r, width=2, border_radius=10)
            fu_b = _f("Arial", 13, True)
            max_s = fu_b.render("MÁXIMO", True, COLOR_GRIS)
            surf.blit(max_s, (btn_r.centerx - max_s.get_width() // 2,
                               btn_r.centery - max_s.get_height() // 2))
        else:
            puede_comprar = tienda.puede_comprar(item['id'])
            c_bg = (20, 70, 20) if (puede_comprar and hover_btn) else (10, 40, 10) if puede_comprar else (35, 15, 15)
            c_br = COLOR_VERDE if (puede_comprar and hover_btn) else (30, 140, 30) if puede_comprar else (120, 30, 30)
            pygame.draw.rect(surf, c_bg, btn_r, border_radius=10)
            pygame.draw.rect(surf, c_br, btn_r, width=2, border_radius=10)
            fu_b = _f("Arial", 12, True)
            costo_txt = f"Comprar  {costo_sig:,}" if costo_sig else "MAX"
            c_txt = COLOR_BLANCO if puede_comprar else COLOR_GRIS
            bs = fu_b.render(costo_txt, True, c_txt)
            surf.blit(bs, (btn_r.centerx - bs.get_width() // 2,
                           btn_r.centery - bs.get_height() // 2))

        rects_comprar.append(btn_r)
        item_y += 150

    # Hint de teclado
    pygame.draw.line(surf, COLOR_AZUL_OSC, (40, h - 55), (w - 40, h - 55), 1)
    fu_h = _f("Arial", 14)
    ht = fu_h.render("ESC / ENTER · Volver al menú principal", True, COLOR_GRIS)
    surf.blit(ht, (w // 2 - ht.get_width() // 2, h - 40))

    return rects_comprar


# ─── Menú principal ───────────────────────────────────────────────────────────

OPCIONES_MENU = [
    "JUGAR  (semilla aleatoria)",
    "SEMILLA PERSONALIZADA",
    "TIENDA",
    "RANKING",
    "CONTROLES",
    "SALIR",
]


def dibujar_menu_nombre(surf: pygame.Surface, buffer_nombre: str, tick: int) -> None:
    """Pantalla inicial: elegir nombre de usuario antes del menú principal."""
    surf.fill(COLOR_BG)
    w, h = surf.get_width(), surf.get_height()
    for x in range(40, w, 60):
        _dibujar_pellet(surf, x, 20, False)
        _dibujar_pellet(surf, x, h - 20, False)

    fu_t = _f("Arial Black", 38, True)
    t = fu_t.render("¿CÓMO TE LLAMAS?", True, COLOR_AMARILLO)
    surf.blit(t, (w // 2 - t.get_width() // 2, 100))

    fu_sub = _f("Arial", 17)
    sub = fu_sub.render("Se usará en el ranking y para guardar tu mejor puntaje.", True, COLOR_CYAN)
    surf.blit(sub, (w // 2 - sub.get_width() // 2, 158))

    caja = pygame.Rect(w // 2 - 240, 230, 480, 56)
    pygame.draw.rect(surf, COLOR_AZUL_OSC, caja, border_radius=12)
    pygame.draw.rect(surf, COLOR_AMARILLO, caja, 3, border_radius=12)
    fu_in = _f("Courier New", 28, True)
    display = buffer_nombre if buffer_nombre else ""
    cursor = "_" if (tick // 25) % 2 == 0 else ""
    txt = fu_in.render(display + cursor, True, COLOR_BLANCO)
    surf.blit(txt, (caja.x + 20, caja.y + 14))

    fu_h = _f("Arial", 14)
    h1 = fu_h.render("ENTER · continuar con este nombre   ·   ESC · usar «Jugador»", True, COLOR_GRIS)
    surf.blit(h1, (w // 2 - h1.get_width() // 2, h - 72))
    h2 = fu_h.render("BACKSPACE borrar · letras y números (máx. 20)", True, (100, 100, 120))
    surf.blit(h2, (w // 2 - h2.get_width() // 2, h - 48))


def dibujar_menu_principal(
    surf: pygame.Surface,
    indice_seleccion: int,
    tiempo_tick: int,
    vol_musica: float = 0.65,
    vol_sfx: float = 0.75,
    monedas_tienda: int = 0,
    nombre_jugador: str | None = None,
) -> tuple[pygame.Rect, pygame.Rect]:
    surf.fill(COLOR_BG)
    w, h = surf.get_width(), surf.get_height()

    for x in range(40, w, 60):
        _dibujar_pellet(surf, x, 20, False)
        _dibujar_pellet(surf, x, h - 20, False)
    _dibujar_pellet(surf, 30, 30, True)
    _dibujar_pellet(surf, w - 30, 30, True)
    _dibujar_pellet(surf, 30, h - 30, True)
    _dibujar_pellet(surf, w - 30, h - 30, True)

    _titulo_animado(surf, "PAC-MAN", 46, tiempo_tick)

    fu_sub = _f("Arial", 24, True)
    sub = fu_sub.render("ROGUELIKE EDITION", True, COLOR_CYAN)
    surf.blit(sub, (w // 2 - sub.get_width() // 2, 115))
    if nombre_jugador:
        fu_nom = _f("Arial", 16, True)
        sn = fu_nom.render(f"Usuario: {nombre_jugador}", True, (180, 200, 255))
        surf.blit(sn, (w // 2 - sn.get_width() // 2, 144))

    # Monedas: debajo de la franja de pellets (y≈20) y del pellet grande esquina (y≈30)
    pw, _, _, _ = _tam_badge_monedas(monedas_tienda)
    margen = 28
    panel_x = max(margen, w - pw - margen)
    panel_y = 52
    _dibujar_badge_monedas_en(surf, monedas_tienda, panel_x, panel_y)

    # Animación Pac-Man perseguido por fantasmas
    anim_y = 157
    ciclo_x = (tiempo_tick * 3) % (w + 200) - 100
    colores_fantasma = [COLOR_ROJO, COLOR_ROSA, COLOR_CYAN, COLOR_NARANJA]
    for i, color in enumerate(colores_fantasma):
        oy_f = 5 * math.sin(tiempo_tick * 0.1 + i)
        _dibujar_fantasma(surf, ciclo_x - 50 - i * 30, anim_y + oy_f, color, 20)
    apertura = 20 + 15 * abs(math.sin(tiempo_tick * 0.2))
    _dibujar_pacman(surf, ciclo_x, anim_y, 14, apertura, 0)

    # Opciones (un poco más abajo si mostramos nombre de usuario)
    y0 = 222 if nombre_jugador else 210
    esp = 48
    fu_op = _f("Arial", 22, True)

    for i, op in enumerate(OPCIONES_MENU):
        sel = i == indice_seleccion
        y_pos = y0 + i * esp

        if sel:
            txt_temp = fu_op.render(op, True, COLOR_BLANCO)
            rect_w = txt_temp.get_width() + 60
            rect_x = w // 2 - rect_w // 2
            pygame.draw.rect(surf, COLOR_AZUL_OSC,
                             (rect_x, y_pos - 8, rect_w, 40), border_radius=8)
            pygame.draw.rect(surf, COLOR_AMARILLO,
                             (rect_x, y_pos - 8, rect_w, 40), width=3, border_radius=8)
            pac_anim = 15 + 10 * abs(math.sin(tiempo_tick * 0.3))
            _dibujar_pacman(surf, rect_x - 25, y_pos + 12, 10, pac_anim, 0)
            color_txt = COLOR_AMARILLO
        else:
            color_txt = COLOR_BLANCO

        # Ícono especial para Tienda
        txt_op = op
        if op == "TIENDA":
            color_txt = COLOR_ORO if sel else (200, 160, 0)

        t = fu_op.render(txt_op, True, color_txt)
        surf.blit(t, (w // 2 - t.get_width() // 2, y_pos))

    # Hint de controles
    fu_hint = _f("Arial", 13)
    hint = fu_hint.render("↑ ↓ SELECCIONAR   ·   ENTER CONFIRMAR   ·   ESC SALIR", True, COLOR_GRIS)
    surf.blit(hint, (w // 2 - hint.get_width() // 2, h - 145))

    # Sliders de volumen
    bar_w = 200
    bar_h = 14
    x0_bar = w // 2 - bar_w // 2
    y_mus = h - 114
    y_sfx = h - 82

    fu_vol = _f("Arial", 14, True)

    lbl_mus = fu_vol.render("MÚSICA", True, COLOR_CYAN)
    surf.blit(lbl_mus, (x0_bar - 80, y_mus - 2))
    pygame.draw.rect(surf, COLOR_AZUL_OSC, (x0_bar, y_mus, bar_w, bar_h), border_radius=7)
    pygame.draw.rect(surf, COLOR_CYAN,
                     (x0_bar, y_mus, max(0, int(bar_w * vol_musica)), bar_h), border_radius=7)
    pygame.draw.rect(surf, COLOR_BLANCO, (x0_bar, y_mus, bar_w, bar_h), 2, border_radius=7)
    pct_mus = _f("Arial", 12).render(f"{int(vol_musica * 100)}%", True, COLOR_BLANCO)
    surf.blit(pct_mus, (x0_bar + bar_w + 10, y_mus - 2))

    lbl_sfx = fu_vol.render("EFECTOS", True, COLOR_VERDE)
    surf.blit(lbl_sfx, (x0_bar - 80, y_sfx - 2))
    pygame.draw.rect(surf, COLOR_AZUL_OSC, (x0_bar, y_sfx, bar_w, bar_h), border_radius=7)
    pygame.draw.rect(surf, COLOR_VERDE,
                     (x0_bar, y_sfx, max(0, int(bar_w * vol_sfx)), bar_h), border_radius=7)
    pygame.draw.rect(surf, COLOR_BLANCO, (x0_bar, y_sfx, bar_w, bar_h), 2, border_radius=7)
    pct_sfx = _f("Arial", 12).render(f"{int(vol_sfx * 100)}%", True, COLOR_BLANCO)
    surf.blit(pct_sfx, (x0_bar + bar_w + 10, y_sfx - 2))

    return (
        pygame.Rect(x0_bar, y_mus - 6, bar_w, bar_h + 12),
        pygame.Rect(x0_bar, y_sfx - 6, bar_w, bar_h + 12),
    )


# ─── Submenús existentes ──────────────────────────────────────────────────────

def dibujar_menu_semilla(surf, buffer_texto, error):
    surf.fill(COLOR_BG)
    w, h = surf.get_width(), surf.get_height()
    fu_t = _f("Arial", 36, True)
    t = fu_t.render("SEMILLA DE PARTIDA", True, COLOR_AMARILLO)
    surf.blit(t, (w // 2 - t.get_width() // 2, 80))
    fu_e = _f("Arial", 16)
    ex = fu_e.render("Misma semilla = mismo mapa (competir en ranking)", True, COLOR_CYAN)
    surf.blit(ex, (w // 2 - ex.get_width() // 2, 135))
    ex2 = fu_e.render("Solo números permitidos", True, COLOR_GRIS)
    surf.blit(ex2, (w // 2 - ex2.get_width() // 2, 160))
    caja = pygame.Rect(w // 2 - 220, 220, 440, 58)
    pygame.draw.rect(surf, COLOR_AZUL_OSC, caja, border_radius=10)
    pygame.draw.rect(surf, COLOR_AMARILLO, caja, 3, border_radius=10)
    fu_in = _f("Courier New", 32, True)
    display = buffer_texto if buffer_texto else "_"
    txt = fu_in.render(display, True, COLOR_BLANCO)
    surf.blit(txt, (caja.x + 20, caja.y + 13))
    if error:
        e = _f("Arial", 17, True).render(error, True, COLOR_ROJO)
        surf.blit(e, (w // 2 - e.get_width() // 2, 300))
    hint = _f("Arial", 14).render(
        "ENTER CONFIRMAR   ·   BACKSPACE BORRAR   ·   ESC VOLVER", True, COLOR_GRIS
    )
    surf.blit(hint, (w // 2 - hint.get_width() // 2, h - 50))


def dibujar_menu_ranking(
    surf: pygame.Surface,
    entradas: list,
    mouse_pos: tuple[int, int] = (0, 0),
) -> pygame.Rect:
    """
    Un mejor puntaje por jugador. Retorna el rect del botón borrar estadísticas.
    """
    surf.fill(COLOR_BG)
    w, h = surf.get_width(), surf.get_height()
    fu_t = _f("Arial Black", 40, True)
    t = fu_t.render("RANKING", True, COLOR_AMARILLO)
    surf.blit(t, (w // 2 - t.get_width() // 2, 36))
    fu_sub = _f("Arial", 17)
    sub = fu_sub.render("MEJOR PUNTAJE POR USUARIO (solo récords personales)", True, COLOR_CYAN)
    surf.blit(sub, (w // 2 - sub.get_width() // 2, 86))
    if not entradas:
        vac = _f("Arial", 20).render("Aún no hay jugadores registrados", True, COLOR_GRIS)
        surf.blit(vac, (w // 2 - vac.get_width() // 2, 240))
        _dibujar_pacman(surf, w // 2, 330, 30, 5, 2)
    else:
        fu_r = _f("Courier New", 18, True)
        y = 128
        for i, e in enumerate(entradas[:24]):
            nombre = str(e.get("nombre", "?"))[:14]
            pts = e.get("puntaje", 0)
            sem = e.get("semilla", 0)
            col = [COLOR_AMARILLO, COLOR_CYAN, COLOR_ROSA][i] if i < 3 else COLOR_BLANCO
            medal = ["👑", "🥈", "🥉"][i] if i < 3 else " "
            linea = f"{medal} {i+1:2}. {nombre:<14}  {pts:>7} pts  seed:{sem}"
            surf.blit(fu_r.render(linea, True, col), (w // 2 - 300, y))
            y += 34
    rect_borrar = pygame.Rect(w // 2 - 130, h - 108, 260, 40)
    hover_b = rect_borrar.collidepoint(mouse_pos)
    pygame.draw.rect(surf, (90, 25, 25) if hover_b else (55, 15, 15), rect_borrar, border_radius=10)
    pygame.draw.rect(surf, COLOR_ROJO if hover_b else (160, 50, 50), rect_borrar, width=2, border_radius=10)
    fu_b = _f("Arial", 15, True)
    bt = fu_b.render("BORRAR ESTADÍSTICAS", True, COLOR_BLANCO)
    surf.blit(bt, (rect_borrar.centerx - bt.get_width() // 2, rect_borrar.centery - bt.get_height() // 2))
    hint = _f("Arial", 12).render(
        "ENTER / ESC · volver  ·  B o clic · borrar TU récord, monedas y mejoras de tienda",
        True,
        COLOR_GRIS,
    )
    surf.blit(hint, (w // 2 - hint.get_width() // 2, h - 52))
    return rect_borrar


def dibujar_menu_controles(surf):
    surf.fill(COLOR_BG)
    w, h = surf.get_width(), surf.get_height()
    t = _f("Arial", 38, True).render("CONTROLES", True, COLOR_AMARILLO)
    surf.blit(t, (w // 2 - t.get_width() // 2, 50))
    y = 130
    fu_ctrl = _f("Arial", 20, True)
    fu_desc = _f("Arial", 18)
    controles = [
        ("MOVIMIENTO", "WASD  o  Flechas ↑↓←→", COLOR_CYAN),
        ("PAUSA", "ESC", COLOR_VERDE),
        ("MENÚ", "Q  (desde pausa)", COLOR_ROSA),
        ("REINICIAR", "R  (en juego)", COLOR_NARANJA),
        ("MÚSICA", "M  (alternar on/off)", COLOR_AMARILLO),
    ]
    for ctrl, desc, color in controles:
        surf.blit(fu_ctrl.render(ctrl, True, color), (w // 2 - 260, y))
        surf.blit(fu_desc.render(desc, True, COLOR_BLANCO), (w // 2 - 70, y + 2))
        y += 48
    pygame.draw.line(surf, COLOR_AZUL_OSC, (w // 2 - 280, y + 10), (w // 2 + 280, y + 10), 2)
    y += 30
    fu_info = _f("Arial", 17)
    info_lines = [
        "Pellets: 10 pts  ·  Super Pellet: 50 pts + fantasmas asustados ~10 seg",
        "Comer fantasma asustado: +200 pts  ·  Fiebre del Oro: +500 pts c/u",
        "Roguelike: al superar el umbral de pellets → +1 fantasma y más velocidad",
        "Al alcanzar el umbral de la barra EXP: elige una mejora roguelike",
        "Al completar un nivel: la misma elección de mejoras; luego pasas al siguiente laberinto",
        "Tienda: gasta las monedas ganadas en mejoras permanentes entre runs",
    ]
    for line in info_lines:
        surf.blit(fu_info.render(line, True, COLOR_BLANCO), (w // 2 - 300, y))
        y += 30
    hint = _f("Arial", 14).render("ENTER / ESC  VOLVER", True, COLOR_GRIS)
    surf.blit(hint, (w // 2 - hint.get_width() // 2, h - 36))


def dibujar_pausa_overlay(surf, ancho, alto):
    ov = pygame.Surface((ancho, alto), pygame.SRCALPHA)
    ov.fill((0, 0, 0, 180))
    surf.blit(ov, (0, 0))
    t = _f("Arial Black", 52, True).render("PAUSA", True, COLOR_AMARILLO)
    surf.blit(t, (ancho // 2 - t.get_width() // 2, alto // 2 - 80))
    fu_op = _f("Arial", 22, True)
    opciones = [
        ("ESC", "Reanudar", COLOR_CYAN),
        ("Q", "Menú principal", COLOR_ROSA),
    ]
    y = alto // 2 - 10
    for tecla, desc, color in opciones:
        tk = fu_op.render(f"[{tecla}]", True, color)
        ds = fu_op.render(f" {desc}", True, COLOR_BLANCO)
        x_s = ancho // 2 - (tk.get_width() + ds.get_width()) // 2
        surf.blit(tk, (x_s, y))
        surf.blit(ds, (x_s + tk.get_width(), y))
        y += 40
    fu_m = _f("Arial", 14)
    m = fu_m.render("La música se ajusta desde el menú principal (sliders)", True, (120, 120, 140))
    surf.blit(m, (ancho // 2 - m.get_width() // 2, y + 8))


def dibujar_game_over_pantalla(
    surf: pygame.Surface,
    ancho: int,
    alto: int,
    nombre: str,
    puntaje: int,
    mejoro_tu_highscore: bool,
    posicion_ranking: int,
    total_jugadores_tabla: int,
) -> None:
    ov = pygame.Surface((ancho, alto), pygame.SRCALPHA)
    ov.fill((0, 0, 50, 200))
    surf.blit(ov, (0, 0))
    t = _f("Arial Black", 56, True).render("GAME OVER", True, COLOR_ROJO)
    surf.blit(t, (ancho // 2 - t.get_width() // 2, alto // 2 - 128))
    nm = _f("Arial", 18, True).render(f"Jugador: {nombre}", True, COLOR_CYAN)
    surf.blit(nm, (ancho // 2 - nm.get_width() // 2, alto // 2 - 78))
    p = _f("Arial", 26, True).render("PUNTAJE DE ESTA PARTIDA", True, COLOR_AMARILLO)
    surf.blit(p, (ancho // 2 - p.get_width() // 2, alto // 2 - 42))
    num = _f("Courier New", 36, True).render(f"{puntaje:06d}", True, COLOR_BLANCO)
    surf.blit(num, (ancho // 2 - num.get_width() // 2, alto // 2 - 2))
    if mejoro_tu_highscore:
        r = _f("Arial", 22, True).render("¡Nuevo récord personal guardado!", True, COLOR_VERDE)
        surf.blit(r, (ancho // 2 - r.get_width() // 2, alto // 2 + 44))
    rk = _f("Arial", 20, True).render(
        f"Posición en el ranking (mejores marcas):  #{posicion_ranking}"
        + (f"  de {total_jugadores_tabla} jugadores" if total_jugadores_tabla else ""),
        True,
        COLOR_ROSA,
    )
    surf.blit(rk, (ancho // 2 - rk.get_width() // 2, alto // 2 + 78))
    h = _f("Arial", 17).render("ENTER  ·  MENÚ PRINCIPAL", True, COLOR_GRIS)
    surf.blit(h, (ancho // 2 - h.get_width() // 2, alto // 2 + 118))


# ─── Tutorial (slides antes de la primera partida) ─────────────────────────────

TUTORIAL_SLIDES: list[dict] = [
    {
        'titulo': 'Objetivo',
        'sub': 'Cada laberinto es distinto (semilla aleatoria)',
        'lineas': [
            'Come todos los pellets (puntos pequeños) del mapa para completar el nivel.',
            'Evita a los fantasmas… o hazlos vulnerables con una super pastilla.',
            'WASD o flechas para moverte. ESC pausa · Q en pausa vuelve al menú.',
        ],
    },
    {
        'titulo': 'Puntos y pellets',
        'sub': 'La barra amarilla arriba es tu progreso de EXP',
        'lineas': [
            'Pellet normal: +10 pts. Super pellet (grande): +50 pts y asusta a los fantasmas.',
            'Fantasma asustado comido: +200 pts (o +500 en la Fiebre del Oro).',
            'Al acumular suficientes puntos subes de “nivel de mejora” y eliges una carta.',
        ],
    },
    {
        'titulo': 'Los fantasmas',
        'sub': 'Cada color se comporta distinto',
        'lineas': [
            'Morado: repite el mismo camino una y otra vez; puedes ver por dónde va.',
            'Rosa te persigue. El rojo se mueve de forma más impredecible.',
            'La super pastilla los vuelve azules: ¡huyen y puedes comerlos!',
            'Los dorados con corona no son enemigos normales: salen cuando eliges la mejora Fiebre del Oro, huyen y dan muchos puntos.',
        ],
    },
    {
        'titulo': 'Iconos en pantalla',
        'sub': 'A la derecha del laberinto verás tus mejoras activas',
        'lineas': [
            'Copo: Congelador — congela a todos los fantasmas unos segundos de forma periódica.',
            'Escudo: absorbe un golpe mortal (se recarga solo).',
            'Bota: más velocidad (acumulable).',
            'Estrella / fantasma / corazón: efectos inmediatos al elegirlos en la carta.',
        ],
    },
    {
        'titulo': 'Mejoras roguelike',
        'sub': 'Al subir de EXP o al completar un nivel',
        'lineas': [
            'Es el mismo tipo de elección: tres cartas con icono, nombre y descripción.',
            'Congelador, Escudo, Botas, Fiebre del Oro, Modo Fantasma (atraviesa muros) y Vida extra.',
            'Si ya tienes todo al máximo en mejoras con tope, recibirás 500 monedas para la tienda.',
        ],
    },
    {
        'titulo': 'Progreso y tienda',
        'sub': 'Entre partidas conservas monedas y compras permanentes',
        'lineas': [
            'Al comer pellets se llena una barra secundaria: al llegar al fin, el laberinto se “divide” y aparece un fantasma extra (más difícil).',
            'Las monedas se ganan con el puntaje y sirven en la Tienda del menú principal.',
            'Puedes jugar con semilla fija para repetir o comparar mapas.',
        ],
    },
]


def _dibujar_tutorial_cinta_visual(
    surf: pygame.Surface,
    rx: int,
    ry: int,
    rw: int,
    rh: int,
    indice: int,
    t: int,
) -> None:
    """Franja ilustrada encima del texto (primitivas + iconos de mejora)."""
    banda = pygame.Surface((rw, rh), pygame.SRCALPHA)
    banda.fill((12, 14, 38, 255))
    pygame.draw.rect(banda, (45, 70, 140), (0, 0, rw, rh), 1, border_radius=12)
    surf.blit(banda, (rx, ry))

    cx = rx + rw // 2
    pulse = 0.5 + 0.5 * math.sin(t * 0.12)

    if indice == 0:
        # Mini laberinto de puntos + Pac-Man
        for row in range(5):
            for col in range(11):
                bx = rx + 24 + col * 14
                by = ry + 22 + row * 10
                if (row + col) % 5 == 0:
                    continue
                pygame.draw.circle(surf, (55, 55, 85), (bx, by), 2)
        aper = 28 + 12 * abs(math.sin(t * 0.18))
        _dibujar_pacman(surf, cx + rw // 4, ry + rh // 2 + 8, 22, aper, 0)
        fu = _f("Arial", 12, True)
        f1 = fu.render('COME TODOS LOS PUNTOS', True, COLOR_AMARILLO)
        surf.blit(f1, (cx - f1.get_width() // 2, ry + 10))
        mov = _f("Arial", 13, True).render('WASD  o  flechas  ↑ ↓ ← →', True, COLOR_CYAN)
        surf.blit(mov, (cx - mov.get_width() // 2, ry + rh - 26))

    elif indice == 1:
        yc = ry + rh // 2
        _dibujar_pellet(surf, rx + 48, yc, grande=False)
        t10 = _f("Arial", 14, True).render('+10', True, COLOR_BLANCO)
        surf.blit(t10, (rx + 60, yc - 10))
        _dibujar_pellet(surf, rx + 130, yc, grande=True)
        t50 = _f("Arial", 14, True).render('+50 · asusta', True, COLOR_ROSA)
        surf.blit(t50, (rx + 148, yc - 10))
        _dibujar_fantasma(surf, rx + rw - 90, yc, COLOR_AZUL, tamano=26, asustado=True)
        tu = _f("Arial", 12).render('200 / 500 pts al comer', True, (180, 200, 255))
        surf.blit(tu, (cx - tu.get_width() // 2, ry + 14))
        # Barra EXP mini
        bx, bw, bh = rx + 40, rw - 80, 12
        by = ry + rh - 32
        pygame.draw.rect(surf, (25, 25, 45), (bx, by, bw, bh), border_radius=4)
        fw = int(bw * (0.35 + 0.2 * pulse))
        pygame.draw.rect(surf, (255, 200, 0), (bx, by, fw, bh), border_radius=4)
        pygame.draw.rect(surf, (100, 100, 130), (bx, by, bw, bh), 1, border_radius=4)

    elif indice == 2:
        # Fila 1: los cuatro roles habituales. Fila 2: fantasma dorado (Fiebre del Oro).
        fu_peq = _f("Arial", 10, True)
        tit = fu_peq.render('En cada partida', True, (160, 170, 210))
        surf.blit(tit, (cx - tit.get_width() // 2, ry + 6))

        specs = [
            ((165, 95, 230), 'Mismo camino'),
            ((255, 181, 255), 'Te persigue'),
            ((222, 45, 45), 'Al azar'),
            (COLOR_AZUL, '¡Miedo!'),
        ]
        n = len(specs)
        gap = rw // (n + 1)
        gy = ry + 34
        for i, (col, etiqueta) in enumerate(specs):
            fx = rx + gap * (i + 1)
            asust = i == 3
            _dibujar_fantasma(surf, fx, gy, col, tamano=21, asustado=asust)
            # Pista gráfica: pequeño camino repetido junto al morado
            if i == 0:
                for ox, oy in [(0, 0), (-8, 6), (-15, 3), (-22, 8)]:
                    pygame.draw.circle(surf, (130, 90, 180), (int(fx + ox), int(gy + oy)), 2)
                cam = fu_peq.render('siempre igual', True, (140, 120, 190))
                surf.blit(cam, (fx - cam.get_width() // 2, gy + 22))

            te = fu_peq.render(etiqueta, True, COLOR_GRIS)
            surf.blit(te, (fx - te.get_width() // 2, gy + 26))

        # Dorados: solo con la mejora Fiebre del Oro
        sep_y = ry + 78
        pygame.draw.line(surf, (55, 65, 110), (rx + 16, sep_y), (rx + rw - 16, sep_y), 1)

        gx = cx
        gy2 = sep_y + 10
        _dibujar_fantasma(surf, gx, gy2, (255, 195, 50), tamano=20, asustado=False)
        hc = gy2 - 6
        pts_c = [
            (gx - 8, hc),
            (gx - 5, hc - 4),
            (gx - 2, hc),
            (gx, hc - 5),
            (gx + 2, hc),
            (gx + 5, hc - 4),
            (gx + 8, hc),
        ]
        pygame.draw.lines(surf, (255, 220, 80), False, pts_c, 2)

        dor = _f("Arial", 10, True).render('Dorados con corona = Fiebre del Oro', True, (255, 210, 100))
        surf.blit(dor, (gx - dor.get_width() // 2, gy2 + 24))
        sub_d = _f("Arial", 9).render('Solo si eliges esa carta; huyen y dan muchos puntos', True, (150, 165, 200))
        surf.blit(sub_d, (cx - sub_d.get_width() // 2, gy2 + 38))

        sup = fu_peq.render('Super pastilla → se vuelven azules', True, COLOR_CYAN)
        surf.blit(sup, (cx - sup.get_width() // 2, ry + rh - 14))

    elif indice == 3:
        # Cuadrícula de iconos de mejoras
        ids_cols = [
            ('freeze', (120, 210, 255)),
            ('shield', (255, 210, 60)),
            ('boots', (50, 255, 120)),
            ('fever', (255, 170, 40)),
            ('ghost_mode', (200, 100, 255)),
            ('life', (255, 90, 90)),
        ]
        cols, rows = 3, 2
        gw = rw // cols
        gh = rh // rows
        for k, (iid, col) in enumerate(ids_cols):
            c = k % cols
            r = k // cols
            ix = rx + c * gw + gw // 2
            iy = ry + r * gh + gh // 2
            _dibujar_icono_mejora(surf, ix, iy, iid, col, size=20)
        tl = _f("Arial", 11, True).render('Panel derecho del laberinto', True, (140, 160, 200))
        surf.blit(tl, (cx - tl.get_width() // 2, ry + 6))

    elif indice == 4:
        # Tres cartas esquemáticas
        cw, ch, g = 100, 118, 18
        sx0 = cx - (cw * 3 + g * 2) // 2
        for i in range(3):
            sx = sx0 + i * (cw + g)
            sy = ry + 24
            pygame.draw.rect(surf, (18, 22, 50), (sx, sy, cw, ch), border_radius=10)
            pygame.draw.rect(surf, (120, 140, 220), (sx, sy, cw, ch), 2, border_radius=10)
            _dibujar_icono_mejora(
                surf, sx + cw // 2, sy + 38,
                ['freeze', 'shield', 'boots'][i],
                [(100, 210, 255), (255, 220, 50), (50, 255, 120)][i],
                size=22,
            )
            el = _f("Arial", 10, True).render(f'Opción {i + 1}', True, COLOR_GRIS)
            surf.blit(el, (sx + cw // 2 - el.get_width() // 2, sy + ch - 22))
        ar = _f("Arial", 12, True).render('EXP o nivel completado → misma elección', True, COLOR_AMARILLO)
        surf.blit(ar, (cx - ar.get_width() // 2, ry + rh - 22))

    elif indice == 5:
        # Barra “laberinto inestable” + moneda
        bx, bw = rx + 32, rw - 64
        by = ry + 36
        bh = 14
        pygame.draw.rect(surf, (20, 22, 40), (bx, by, bw, bh), border_radius=5)
        prog = (t * 0.02) % 1.0
        pygame.draw.rect(surf, (255, 80, 80), (bx, by, int(bw * prog), bh), border_radius=5)
        pygame.draw.rect(surf, (90, 90, 120), (bx, by, bw, bh), 1, border_radius=5)
        t1 = _f("Arial", 11, True).render('Progreso de pellets → evento “inestable” (+1 fantasma)', True, (255, 160, 140))
        surf.blit(t1, (cx - t1.get_width() // 2, ry + 10))
        _dibujar_icono_moneda(surf, rx + rw // 2 - 50, ry + 70, 14)
        _dibujar_icono_moneda(surf, rx + rw // 2 + 50, ry + 70, 14)
        tm = _f("Arial", 12, True).render('Monedas → tienda permanente', True, COLOR_ORO)
        surf.blit(tm, (cx - tm.get_width() // 2, ry + rh - 24))


def dibujar_tutorial(
    surf: pygame.Surface,
    ancho: int,
    alto: int,
    indice: int,
    tiempo_ui: int,
    mouse_pos: tuple[int, int],
) -> tuple[pygame.Rect | None, pygame.Rect, pygame.Rect]:
    """
    Pantalla de instrucciones tipo carrusel.
    Retorna (rect_atras o None si indice==0, rect_siguiente, rect_saltar).
    """
    n = len(TUTORIAL_SLIDES)
    idx = max(0, min(indice, n - 1))
    slide = TUTORIAL_SLIDES[idx]
    ultima = idx >= n - 1

    ov = pygame.Surface((ancho, alto), pygame.SRCALPHA)
    ov.fill((5, 8, 28, 250))
    surf.blit(ov, (0, 0))

    # Panel central (más alto para franja gráfica + texto)
    pw, ph = min(740, ancho - 40), min(560, alto - 100)
    px = (ancho - pw) // 2
    py = (alto - ph) // 2 - 6
    panel = pygame.Rect(px, py, pw, ph)
    ps = pygame.Surface((pw, ph), pygame.SRCALPHA)
    ps.fill((*COLOR_PANEL, 245))
    surf.blit(ps, (px, py))
    pygame.draw.rect(surf, (90, 110, 210), panel, width=2, border_radius=16)

    a = 0.85 + 0.15 * math.sin(tiempo_ui * 0.08)
    fu_t = _f("Arial Black", 30, True)
    tit = fu_t.render(slide['titulo'], True, (int(255 * a), int(240 * a), int(80 * a)))
    surf.blit(tit, (ancho // 2 - tit.get_width() // 2, py + 22))

    fu_s = _f("Arial", 15, True)
    sub = fu_s.render(slide['sub'], True, COLOR_CYAN)
    surf.blit(sub, (ancho // 2 - sub.get_width() // 2, py + 60))

    vh = 158
    y_vis = py + 86
    _dibujar_tutorial_cinta_visual(surf, px + 14, y_vis, pw - 28, vh, idx, tiempo_ui)

    fu_l = _f("Arial", 15)
    ly = y_vis + vh + 14
    for linea in slide['lineas']:
        # word-wrap simple por ancho
        palabras = linea.split()
        linea_actual = ''
        for p in palabras:
            prueba = (linea_actual + ' ' + p).strip()
            if fu_l.size(prueba)[0] > pw - 52:
                if linea_actual:
                    s = fu_l.render(linea_actual, True, (235, 238, 255))
                    surf.blit(s, (px + 26, ly))
                    ly += 24
                linea_actual = p
            else:
                linea_actual = prueba
        if linea_actual:
            s = fu_l.render(linea_actual, True, (235, 238, 255))
            surf.blit(s, (px + 26, ly))
            ly += 26

    # Puntos de progreso
    dot_y = py + ph - 82
    esp = 14
    total_w = n * esp + (n - 1) * 8
    x0 = ancho // 2 - total_w // 2
    for i in range(n):
        cx = x0 + i * (esp + 8) + esp // 2
        col = COLOR_AMARILLO if i == idx else COLOR_GRIS_OSC
        r = 5 if i != idx else 7
        pygame.draw.circle(surf, col, (cx, dot_y), r)

    fu_h = _f("Arial", 13)
    hint = fu_h.render(f"Diapositiva {idx + 1} / {n}", True, COLOR_GRIS)
    surf.blit(hint, (ancho // 2 - hint.get_width() // 2, dot_y + 16))

    # Botones (fila inferior)
    by = alto - 72
    rect_atras: pygame.Rect | None = None
    if idx > 0:
        rect_atras = pygame.Rect(32, by, 118, 40)
        hover_a = rect_atras.collidepoint(mouse_pos)
        pygame.draw.rect(surf, (60, 80, 140) if hover_a else (40, 50, 90), rect_atras, border_radius=8)
        pygame.draw.rect(surf, COLOR_CYAN, rect_atras, width=2, border_radius=8)
        t_a = _f("Arial", 16, True).render('← Atrás', True, COLOR_BLANCO)
        surf.blit(t_a, (rect_atras.centerx - t_a.get_width() // 2, rect_atras.centery - t_a.get_height() // 2))

    txt_sig = '¡A jugar!' if ultima else 'Siguiente →'
    rw = 168
    rx = (ancho - rw) // 2
    rect_sig = pygame.Rect(rx, by, rw, 40)
    hover_s = rect_sig.collidepoint(mouse_pos)
    pygame.draw.rect(surf, (50, 120, 70) if hover_s else (35, 90, 55), rect_sig, border_radius=8)
    pygame.draw.rect(surf, COLOR_VERDE, rect_sig, width=2, border_radius=8)
    t_s = _f("Arial", 16, True).render(txt_sig, True, COLOR_BLANCO)
    surf.blit(t_s, (rect_sig.centerx - t_s.get_width() // 2, rect_sig.centery - t_s.get_height() // 2))

    rect_skip = pygame.Rect(ancho - 32 - 118, by, 118, 40)
    hover_k = rect_skip.collidepoint(mouse_pos)
    pygame.draw.rect(surf, (90, 50, 50) if hover_k else (70, 35, 35), rect_skip, border_radius=8)
    pygame.draw.rect(surf, COLOR_ROSA, rect_skip, width=2, border_radius=8)
    t_k = _f("Arial", 15, True).render('Saltar', True, COLOR_BLANCO)
    surf.blit(t_k, (rect_skip.centerx - t_k.get_width() // 2, rect_skip.centery - t_k.get_height() // 2))

    fu_keys = _f("Arial", 12)
    keys = fu_keys.render('← → · cambiar   ·   ESPACIO / ENTER · avanzar   ·   ESC · saltar', True, (100, 100, 120))
    surf.blit(keys, (ancho // 2 - keys.get_width() // 2, alto - 28))

    return rect_atras, rect_sig, rect_skip
