# src/sistemas/mejoras.py
"""
Sistema de mejoras roguelike para Pac-Man.
Gestiona las 6 mejoras disponibles, el sistema de EXP y los timers activos.
"""

from __future__ import annotations

FPS = 60
FREEZE_DURACION_FRAMES = 5 * FPS  # 5 segundos de congelamiento al activarse el congelador
MODO_FANTASMA_DURACION = 10 * FPS  # 10 segundos de fase etérea

# Recompensa sintética cuando todas las mejoras con tope están al máximo (solo pantalla de nivel)
MONEDAS_RECOMPENSA_NIVEL_ID = '_monedas_nivel'

OPCION_MONEDAS_500: dict = {
    'id': MONEDAS_RECOMPENSA_NIVEL_ID,
    'nombre': '500 monedas',
    'icono': 'coins',
    'color': (255, 200, 80),
    'color_borde': (180, 130, 40),
    'max_nivel': -1,
    'desc_corta': 'Para la tienda permanente.',
    'niveles_desc': ['500 monedas para gastar\nen la tienda.'],
}

# ─────────────────────────────────────────────────────────────
# Catálogo de todas las mejoras disponibles en el roguelike
# ─────────────────────────────────────────────────────────────
CATALOGO_MEJORAS: list[dict] = [
    {
        'id': 'congelador',
        'nombre': 'Congelador Pasivo',
        'icono': 'freeze',
        'color': (100, 210, 255),
        'color_borde': (40, 140, 220),
        'desc_corta': 'Congela todos los fantasmas\nperiódicamente',
        'max_nivel': 3,
        'niveles_desc': [
            'Congela todos los fantasmas\ncada 50 segundos',
            'Congela todos los fantasmas\ncada 40 segundos',
            'Congela todos los fantasmas\ncada 20 segundos',
        ],
        'intervalos_frames': [50 * FPS, 40 * FPS, 20 * FPS],
    },
    {
        'id': 'escudo',
        'nombre': 'Escudo Recargable',
        'icono': 'shield',
        'color': (255, 220, 50),
        'color_borde': (200, 150, 0),
        'desc_corta': 'Absorbe un golpe mortal.\nSe recarga con el tiempo.',
        'max_nivel': 2,
        'niveles_desc': [
            'Absorbe 1 golpe fatal.\nCooldown: 50 segundos.',
            'Absorbe 1 golpe fatal.\nCooldown: 30 segundos.',
        ],
        'cooldowns_frames': [50 * FPS, 30 * FPS],
    },
    {
        'id': 'botas',
        'nombre': 'Botas de Velocidad',
        'icono': 'boots',
        'color': (50, 255, 120),
        'color_borde': (20, 180, 70),
        'desc_corta': '+10% velocidad.\nStackeable hasta +50%.',
        'max_nivel': 5,
        'niveles_desc': [
            '+10% de velocidad de movimiento',
            '+20% de velocidad de movimiento',
            '+30% de velocidad de movimiento',
            '+40% de velocidad de movimiento',
            '+50% de velocidad — MÁXIMO',
        ],
    },
    {
        'id': 'fiebre_oro',
        'nombre': 'Fiebre del Oro',
        'icono': 'fever',
        'color': (255, 180, 0),
        'color_borde': (200, 110, 0),
        'desc_corta': '15 fantasmas asustados\naparecen en el mapa.',
        'max_nivel': -1,  # sin límite, efecto inmediato cada vez
        'niveles_desc': [
            '15 fantasmas asustados\n+500 pts al comerlos',
        ],
    },
    {
        'id': 'modo_fantasma',
        'nombre': 'Modo Fantasma',
        'icono': 'ghost_mode',
        'color': (180, 80, 255),
        'color_borde': (110, 30, 200),
        'desc_corta': 'Atraviesa paredes\ndurante 10 segundos.',
        'max_nivel': -1,  # sin límite, se activa al elegir
        'niveles_desc': [
            'Activa 10 segundos\nde fase etérea',
        ],
    },
    {
        'id': 'vida_extra',
        'nombre': 'Vida Extra',
        'icono': 'life',
        'color': (255, 80, 80),
        'color_borde': (180, 20, 20),
        'desc_corta': 'Obtén una vida\nadicional al instante.',
        'max_nivel': -1,  # sin límite
        'niveles_desc': [
            'Gana +1 vida al instante',
        ],
    },
]


def get_mejora(mid: str) -> dict | None:
    """Retorna la definición de una mejora por su ID."""
    for m in CATALOGO_MEJORAS:
        if m['id'] == mid:
            return m
    return None


# ─────────────────────────────────────────────────────────────
class SistemaMejoras:
    """
    Gestiona las mejoras activas durante una run roguelike.
    Controla timers de congelador, escudo y modo fantasma.
    """

    def __init__(self, gen) -> None:
        self.gen = gen

        # Niveles actuales de cada mejora (0 = no obtenida)
        self._niveles: dict[str, int] = {m['id']: 0 for m in CATALOGO_MEJORAS}

        # ── Congelador ──
        self._freeze_countdown = 0          # frames hasta próximo freeze
        self._freeze_activo = False
        self._freeze_restantes = 0          # frames que dura el freeze

        # ── Escudo ──
        self.escudo_activo = False
        self._escudo_cooldown_restante = 0

        # ── Modo Fantasma ──
        self.modo_fantasma_activo = False
        self._modo_fantasma_restante = 0

        # ── Fiebre del Oro ──
        self._fiebre_pendiente = False

        # ── EXP / umbral de mejoras (progresión más suave que 1.5^n) ──
        self._exp_umbral = 480              # próximo umbral de puntos
        self._n_mejoras = 0                 # cuántas mejoras por EXP ya se eligieron
        self._exp_base_incremento = 360
        self._exp_mult_suave = 1.12        # antes 1.5 — a nivel 5+ sigue siendo razonable

        # ── Bonus permanente (viene de la tienda) ──
        self.bonus_velocidad_permanente: float = 0.0

    # ── Consultas ────────────────────────────────────────────

    def nivel_de(self, mid: str) -> int:
        return self._niveles.get(mid, 0)

    def puede_subir(self, mid: str) -> bool:
        """True si la mejora aún puede subir de nivel."""
        m = get_mejora(mid)
        if m is None:
            return False
        max_n = m['max_nivel']
        if max_n == -1:
            return True
        return self._niveles[mid] < max_n

    def get_umbral(self) -> int:
        return self._exp_umbral

    def chequear_levelup(self, puntaje: int) -> bool:
        return puntaje >= self._exp_umbral

    def avanzar_umbral(self) -> None:
        """Solo para recompensa por puntos (EXP). No llamar tras completar nivel."""
        self._n_mejoras += 1
        self._exp_umbral += int(self._exp_base_incremento * (self._exp_mult_suave ** self._n_mejoras))

    def todas_las_mejoras_limitadas_al_maximo(self) -> bool:
        """True si congelador, escudo y botas están en nivel máximo."""
        for m in CATALOGO_MEJORAS:
            if m['max_nivel'] == -1:
                continue
            if self.nivel_de(m['id']) < m['max_nivel']:
                return False
        return True

    def obtener_recompensa_nivel_completado(self) -> list[dict]:
        """
        Misma lógica que al subir de EXP, salvo que si ya no quedan mejoras con tope
        por subir, se ofrecen 500 monedas.
        """
        if self.todas_las_mejoras_limitadas_al_maximo():
            return [dict(OPCION_MONEDAS_500)]
        return self.obtener_opciones()

    # ── Selección de opciones ─────────────────────────────────

    def obtener_opciones(self) -> list[dict]:
        """Genera hasta 3 mejoras aleatorias disponibles para ofrecer."""
        disponibles = [m for m in CATALOGO_MEJORAS if self.puede_subir(m['id'])]
        if len(disponibles) <= 3:
            return list(disponibles)
        # Mezclar usando el PRNG del juego para reproducibilidad
        idx = list(range(len(disponibles)))
        for i in range(len(idx) - 1, 0, -1):
            j = self.gen.entero(0, i)
            idx[i], idx[j] = idx[j], idx[i]
        return [disponibles[i] for i in idx[:3]]

    # ── Aplicar mejora ────────────────────────────────────────

    def aplicar_mejora(self, mid: str, pacman=None, fantasmas: list | None = None) -> str:
        """
        Aplica la mejora elegida.
        Retorna un mensaje descriptivo del efecto.
        """
        m = get_mejora(mid)
        if m is None:
            return ''

        if mid == 'congelador':
            nivel_nuevo = self._niveles['congelador'] + 1
            self._niveles['congelador'] = nivel_nuevo
            intervalo = m['intervalos_frames'][nivel_nuevo - 1]
            self._freeze_countdown = intervalo
            self._freeze_activo = False
            return f'Congelador Nv.{nivel_nuevo} activado'

        elif mid == 'escudo':
            nivel_nuevo = self._niveles['escudo'] + 1
            self._niveles['escudo'] = nivel_nuevo
            if not self.escudo_activo:
                self.escudo_activo = True
                self._escudo_cooldown_restante = 0
            return f'Escudo Nv.{nivel_nuevo} equipado'

        elif mid == 'botas':
            self._niveles['botas'] += 1
            pct = self._niveles['botas'] * 10
            return f'+{pct}% velocidad'

        elif mid == 'fiebre_oro':
            self._fiebre_pendiente = True
            return '¡15 fantasmas asustados!'

        elif mid == 'modo_fantasma':
            self.modo_fantasma_activo = True
            self._modo_fantasma_restante = MODO_FANTASMA_DURACION
            if pacman:
                pacman.modo_fantasma = True
            return '10 seg de modo fantasma'

        elif mid == 'vida_extra':
            if pacman:
                pacman.vidas += 1
            return '+1 vida'

        return ''

    # ── Consumo de recursos ───────────────────────────────────

    def consumir_fiebre(self) -> bool:
        """Retorna True y limpia el flag si hay fiebre pendiente."""
        if self._fiebre_pendiente:
            self._fiebre_pendiente = False
            return True
        return False

    def consumir_escudo(self) -> None:
        """El escudo absorbe un golpe: lo desactiva e inicia cooldown."""
        self.escudo_activo = False
        m = get_mejora('escudo')
        nivel = self._niveles['escudo']
        if m and nivel > 0:
            self._escudo_cooldown_restante = m['cooldowns_frames'][nivel - 1]

    # ── Bonus de velocidad ────────────────────────────────────

    def get_bonus_velocidad(self) -> float:
        """Multiplicador total de velocidad (1.0 = normal)."""
        run_bonus = self._niveles['botas'] * 0.10
        return 1.0 + run_bonus + self.bonus_velocidad_permanente

    # ── Tick principal ────────────────────────────────────────

    def tick(self, fantasmas: list, pacman=None) -> dict:
        """
        Actualiza todos los timers activos.
        Retorna un diccionario de eventos que ocurrieron este frame.
        """
        eventos: dict[str, bool] = {
            'freeze_inicio': False,
            'freeze_fin': False,
            'escudo_recargado': False,
            'modo_fantasma_fin': False,
        }

        # ── Congelador pasivo ──────────────────────────────
        if self._niveles['congelador'] > 0:
            if not self._freeze_activo:
                self._freeze_countdown -= 1
                if self._freeze_countdown <= 0:
                    self._freeze_activo = True
                    self._freeze_restantes = FREEZE_DURACION_FRAMES
                    eventos['freeze_inicio'] = True
                    for f in fantasmas:
                        f.congelado = True
            else:
                self._freeze_restantes -= 1
                if self._freeze_restantes <= 0:
                    self._freeze_activo = False
                    m_def = get_mejora('congelador')
                    nivel = self._niveles['congelador']
                    if m_def:
                        self._freeze_countdown = m_def['intervalos_frames'][nivel - 1]
                    eventos['freeze_fin'] = True
                    for f in fantasmas:
                        f.congelado = False

        # ── Escudo cooldown ────────────────────────────────
        if not self.escudo_activo and self._niveles['escudo'] > 0:
            if self._escudo_cooldown_restante > 0:
                self._escudo_cooldown_restante -= 1
                if self._escudo_cooldown_restante <= 0:
                    self.escudo_activo = True
                    eventos['escudo_recargado'] = True

        # ── Modo Fantasma timer ────────────────────────────
        if self.modo_fantasma_activo:
            self._modo_fantasma_restante -= 1
            if self._modo_fantasma_restante <= 0:
                self.modo_fantasma_activo = False
                if pacman:
                    pacman.modo_fantasma = False
                eventos['modo_fantasma_fin'] = True

        return eventos

    # ── Progreso para HUD ─────────────────────────────────────

    def get_escudo_progreso(self) -> float:
        """0.0–1.0 para la barra de cooldown del escudo."""
        if self.escudo_activo:
            return 1.0
        m = get_mejora('escudo')
        nivel = self._niveles['escudo']
        if not m or nivel == 0:
            return 0.0
        cd_total = m['cooldowns_frames'][nivel - 1]
        if cd_total <= 0:
            return 1.0
        return 1.0 - (self._escudo_cooldown_restante / cd_total)

    def get_freeze_progreso(self) -> float:
        """0.0–1.0 para la barra de progreso del congelador (1.0 = activo)."""
        if self._freeze_activo:
            return 1.0
        m = get_mejora('congelador')
        nivel = self._niveles['congelador']
        if not m or nivel == 0:
            return 0.0
        cd_total = m['intervalos_frames'][nivel - 1]
        if cd_total <= 0:
            return 1.0
        return 1.0 - (self._freeze_countdown / cd_total)

    def get_freeze_activo(self) -> bool:
        return self._freeze_activo

    def get_modo_fantasma_progreso(self) -> float:
        """0.0–1.0 de tiempo restante del modo fantasma."""
        if not self.modo_fantasma_activo:
            return 0.0
        return self._modo_fantasma_restante / MODO_FANTASMA_DURACION

    def get_descripcion_nivel_siguiente(self, mid: str) -> str:
        """Retorna la descripción del nivel que se obtendría al elegir esta mejora."""
        if mid == MONEDAS_RECOMPENSA_NIVEL_ID:
            return OPCION_MONEDAS_500['niveles_desc'][0]
        m = get_mejora(mid)
        if m is None:
            return ''
        nivel_actual = self._niveles.get(mid, 0)
        descs = m['niveles_desc']
        if nivel_actual < len(descs):
            return descs[nivel_actual]
        if descs:
            return descs[-1]
        return ''
