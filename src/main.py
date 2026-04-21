import sys
import os
import pygame

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lib import GeneradorAleatorio
from src.mundo.generador_mapa import GeneradorMapa
from src.mundo.tablero import TAM_CELDA, PUNTO, SUPER_PUNTO
from src.entidades.pacman import PacMan
from src.entidades.fantasma import (
    FantasmaAleatorio,
    FantasmaPerseguidor,
    FantasmaBlanco,
    MODO_ASUSTADO,
    MODO_RETIRADA,
    DURACION_ASUSTADO_FRAMES,
)
from src.sistemas import SistemaLoot, SistemaRanking
from src.sistemas.mejoras import MONEDAS_RECOMPENSA_NIVEL_ID, SistemaMejoras
from src.sistemas.tienda import SistemaTienda
from src.ui.hud import HUD
from src.ui.audio import GestorAudio
from src.ui import menu as ui_menu
from src.ui.menu import OPCIONES_MENU, TUTORIAL_SLIDES

ANCHO = 800
ALTO  = 680
FPS   = 60
TITULO = "Pac-Man Roguelike"

COLOR_FONDO = (10, 10, 30)

HUD_SUP = 54
HUD_INF = 48

# ── Estados del juego ─────────────────────────────────────────────────────────
ESTADO_MENU_NOMBRE       = 'menu_nombre'
ESTADO_MENU              = 'menu'
ESTADO_MENU_SEMILLA      = 'menu_semilla'
ESTADO_MENU_RANKING      = 'menu_ranking'
ESTADO_MENU_CONTROLES    = 'menu_controles'
ESTADO_MENU_TIENDA       = 'menu_tienda'
ESTADO_TUTORIAL          = 'tutorial'
ESTADO_INTRO             = 'intro'
ESTADO_JUGANDO           = 'jugando'
ESTADO_MUERTE_ANIM       = 'muerte_anim'
ESTADO_PAUSA             = 'pausa'
ESTADO_GAME_OVER         = 'game_over'
ESTADO_SELECCION_MEJORA  = 'seleccion_mejora'

# ── Número de fantasmas base por nivel ───────────────────────────────────────
_FANTASMAS_BASE = 3
# Evento "laberinto inestable": no superar ~Pac-Man (evita perseguidor imposible)
_INCREMENTO_VEL_DIVISION = 0.04
_RATIO_CAP_VS_PACMAN = 0.96  # tope fantasmas ≤ ratio × velocidad actual de Pac-Man
_VELOCIDAD_MAX_FANTASMA_ABS = 1.94  # límite duro si Pac-Man va muy rápido (botas/tienda)


def _calcular_spawn_fantasmas(nivel: int) -> list[str]:
    """
    Retorna la lista de tipos de fantasmas a spawnear para el nivel dado.
    Reglas:
      - Siempre hay 3 fantasmas base: blanco, perseguidor, aleatorio.
      - Por cada nivel adicional (nivel > 1) se agrega 1 fantasma.
      - Si el nivel es impar → el nuevo fantasma es Perseguidor.
      - Si el nivel es par  → el nuevo fantasma es Aleatorio.
    """
    tipos = ['blanco', 'perseguidor', 'aleatorio']
    for n in range(2, nivel + 1):
        if n % 2 != 0:   # nivel impar → perseguidor
            tipos.append('perseguidor')
        else:             # nivel par   → aleatorio
            tipos.append('aleatorio')
    return tipos


class Juego:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption(TITULO)
        self.pantalla = pygame.display.set_mode((ANCHO, ALTO))
        self._fuente_popup = pygame.font.SysFont('Arial', 22, bold=True)
        self._fuente_banner_rlk = pygame.font.SysFont('Arial', 17, bold=True)
        self.reloj = pygame.time.Clock()

        self.estado = ESTADO_MENU_NOMBRE
        self.buffer_nombre = ''
        self.nombre_jugador = 'Jugador'
        self.gen = None
        self.tablero = None
        self.mapeador = None
        self.pacman = None
        self.fantasmas: list = []
        self.umbral_division = 0
        self.semilla_partida = 0
        self.ranking = SistemaRanking()
        self.tienda = SistemaTienda()
        self.sistema_loot: SistemaLoot | None = None
        self.sistema_mejoras: SistemaMejoras | None = None
        self.nivel = 1

        # Tras completar nivel: puntaje antes de cargar el siguiente mapa
        self._puntaje_guardado_victoria = 0

        # Estado selección de mejora ('puntos' = EXP | 'victoria' = laberinto completado)
        self._origen_seleccion_mejora: str = 'puntos'
        self._mejora_opciones: list[dict] = []
        self._mejora_seleccionada = 0
        self._mejora_rects: list[pygame.Rect] = []

        # Tutorial (slides antes de empezar)
        self._tutorial_slide = 0
        self._tutorial_rect_atras: pygame.Rect | None = None
        self._tutorial_rect_sig = pygame.Rect(0, 0, 0, 0)
        self._tutorial_rect_skip = pygame.Rect(0, 0, 0, 0)
        self._semilla_pendiente_tutorial: int | None = None

        # Menú
        self.menu_indice = 0
        self.buffer_semilla = ''
        self.error_semilla: str | None = None
        self.tiempo_ui = 0

        # Tienda (índice de selección del menú tienda)
        self._tienda_indice = 0

        # Volumen
        self.vol_musica = 0.65
        self.vol_sfx = 0.75
        self._rect_slider_mus = pygame.Rect(0, 0, 0, 0)
        self._rect_slider_sfx = pygame.Rect(0, 0, 0, 0)
        self._arrastrando_volumen: str | None = None

        self.hud = HUD(ANCHO, ALTO)
        self.audio = GestorAudio()
        self.audio.set_volumen_musica(self.vol_musica)
        self.audio.set_volumen_sfx(self.vol_sfx)
        # La música de menú no arranca hasta salir de la pantalla de nombre (ver _eventos_menu_nombre)

        self._puntaje_prev = 0
        self._game_over_mejoro_highscore = False
        self._game_over_posicion_ranking = 1
        self._game_over_total_ranking = 0
        self._intro_sonido_lanzado = False
        self._fantasmas_en_retirada_prev = 0
        self._division_nivel_hecha = False
        self._mensaje_roguelike: tuple[str, int] | None = None
        self._popups_puntos: list[dict] = []

        # Flag para escudar con el sistema de mejoras
        self._mejora_pendiente_check = False

        self.corriendo = True

    # ─── Loop principal ───────────────────────────────────────────────────────
    def ejecutar(self) -> None:
        while self.corriendo:
            self.tiempo_ui += 1
            self._manejar_eventos()
            self._actualizar()
            self._dibujar()
            self.reloj.tick(FPS)
        pygame.quit()
        sys.exit()

    # ─── Volumen ──────────────────────────────────────────────────────────────
    def _volumen_desde_x(self, mx, rect):
        return max(0.0, min(1.0, (mx - rect.x) / max(1, rect.w)))

    def _aplicar_volumen_mouse(self, mx):
        if self._arrastrando_volumen == 'musica':
            self.vol_musica = self._volumen_desde_x(mx, self._rect_slider_mus)
            self.audio.set_volumen_musica(self.vol_musica)
        elif self._arrastrando_volumen == 'sfx':
            self.vol_sfx = self._volumen_desde_x(mx, self._rect_slider_sfx)
            self.audio.set_volumen_sfx(self.vol_sfx)

    # ─── Manejo de eventos ────────────────────────────────────────────────────
    def _manejar_eventos(self) -> None:
        mouse_pos = pygame.mouse.get_pos()

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                self.corriendo = False
                continue

            # Sliders de volumen en menú principal
            if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                if self.estado == ESTADO_MENU_RANKING:
                    if hasattr(self, '_ranking_rect_borrar') and self._ranking_rect_borrar.collidepoint(evento.pos):
                        self._borrar_estadisticas_usuario_actual()
                elif self.estado == ESTADO_MENU:
                    mx, my = evento.pos
                    if self._rect_slider_mus.collidepoint(mx, my):
                        self._arrastrando_volumen = 'musica'
                        self._aplicar_volumen_mouse(mx)
                    elif self._rect_slider_sfx.collidepoint(mx, my):
                        self._arrastrando_volumen = 'sfx'
                        self._aplicar_volumen_mouse(mx)

                elif self.estado == ESTADO_TUTORIAL:
                    pos = evento.pos
                    if self._tutorial_rect_sig.collidepoint(pos):
                        self._tutorial_avanzar_o_empezar()
                    elif self._tutorial_rect_skip.collidepoint(pos):
                        self._tutorial_saltar_al_juego()
                    elif self._tutorial_rect_atras and self._tutorial_rect_atras.collidepoint(pos):
                        self._tutorial_atras()

                elif self.estado == ESTADO_SELECCION_MEJORA:
                    self._eventos_seleccion_mejora_click(evento.pos)

                elif self.estado == ESTADO_MENU_TIENDA:
                    self._eventos_tienda_click(evento.pos)

            if evento.type == pygame.MOUSEBUTTONUP and evento.button == 1:
                self._arrastrando_volumen = None

            if evento.type == pygame.MOUSEMOTION:
                if self.estado == ESTADO_MENU and self._arrastrando_volumen and evento.buttons[0]:
                    self._aplicar_volumen_mouse(evento.pos[0])
            # Teclado del juego
            if self.estado == ESTADO_JUGANDO and self.pacman:
                self.pacman.manejar_teclado(evento)

            if evento.type != pygame.KEYDOWN:
                continue

            k = evento.key

            if self.estado == ESTADO_MENU_NOMBRE:
                self._eventos_menu_nombre(evento)
            elif self.estado == ESTADO_MENU:
                self._eventos_menu_principal(k)
            elif self.estado == ESTADO_MENU_SEMILLA:
                self._eventos_menu_semilla(k)
            elif self.estado == ESTADO_MENU_RANKING:
                if k in (pygame.K_RETURN, pygame.K_ESCAPE, pygame.K_SPACE):
                    self.estado = ESTADO_MENU
                elif k == pygame.K_b:
                    self._borrar_estadisticas_usuario_actual()
            elif self.estado == ESTADO_MENU_CONTROLES:
                if k in (pygame.K_RETURN, pygame.K_ESCAPE, pygame.K_SPACE):
                    self.estado = ESTADO_MENU
            elif self.estado == ESTADO_MENU_TIENDA:
                self._eventos_tienda_teclado(k)
            elif self.estado == ESTADO_TUTORIAL:
                self._eventos_tutorial_teclado(k)
            elif self.estado == ESTADO_SELECCION_MEJORA:
                self._eventos_seleccion_mejora_teclado(k)
            elif self.estado == ESTADO_INTRO:
                pass
            elif self.estado == ESTADO_MUERTE_ANIM:
                pass
            elif self.estado == ESTADO_JUGANDO:
                if k == pygame.K_ESCAPE:
                    self.audio.detener_loop_fantasmas()
                    self.estado = ESTADO_PAUSA
                elif k == pygame.K_r:
                    self.audio.detener_loop_fantasmas()
                    self._iniciar_partida(con_intro=True)
                elif k == pygame.K_m:
                    self.audio.alternar_musica()
            elif self.estado == ESTADO_PAUSA:
                if k == pygame.K_ESCAPE:
                    self.estado = ESTADO_JUGANDO
                    self.audio.iniciar_loop_fantasmas()
                elif k == pygame.K_q:
                    self.audio.detener_musica()
                    self.audio.detener_loop_fantasmas()
                    self.audio.iniciar_menu_loop()
                    self.estado = ESTADO_MENU
            elif self.estado == ESTADO_GAME_OVER:
                if k == pygame.K_RETURN:
                    self.audio.iniciar_menu_loop()
                    self.estado = ESTADO_MENU

    def _eventos_menu_nombre(self, evento: pygame.event.Event) -> None:
        k = evento.key
        if k == pygame.K_RETURN:
            self.nombre_jugador = (self.buffer_nombre.strip() or 'Jugador')[:32]
            self.tienda.set_usuario(self.nombre_jugador)
            self.audio.iniciar_menu_loop()
            self.estado = ESTADO_MENU
        elif k == pygame.K_ESCAPE:
            self.nombre_jugador = 'Jugador'
            self.buffer_nombre = ''
            self.tienda.set_usuario(self.nombre_jugador)
            self.audio.iniciar_menu_loop()
            self.estado = ESTADO_MENU
        elif k == pygame.K_BACKSPACE:
            self.buffer_nombre = self.buffer_nombre[:-1]
        elif len(self.buffer_nombre) < 20:
            u = evento.unicode
            if u and u.isprintable():
                self.buffer_nombre += u

    def _borrar_estadisticas_usuario_actual(self) -> None:
        """Ranking + monedas y mejoras de tienda solo del usuario con sesión actual."""
        self.ranking.eliminar_jugador(self.nombre_jugador)
        self.tienda.reiniciar_usuario(self.nombre_jugador)
        self.tienda.set_usuario(self.nombre_jugador)

    # ─── Eventos de menú principal ────────────────────────────────────────────
    def _eventos_menu_principal(self, k: int) -> None:
        if k == pygame.K_ESCAPE:
            self.corriendo = False
            return
        if k == pygame.K_UP:
            self.menu_indice = (self.menu_indice - 1) % len(OPCIONES_MENU)
        elif k == pygame.K_DOWN:
            self.menu_indice = (self.menu_indice + 1) % len(OPCIONES_MENU)
        elif k == pygame.K_RETURN:
            # 0: Jugar | 1: Semilla | 2: Tienda | 3: Ranking | 4: Controles | 5: Salir
            if self.menu_indice == 0:
                self.audio.detener_menu_loop()
                self._tutorial_slide = 0
                self._semilla_pendiente_tutorial = None
                self.estado = ESTADO_TUTORIAL
            elif self.menu_indice == 1:
                self.buffer_semilla = ''
                self.error_semilla = None
                self.estado = ESTADO_MENU_SEMILLA
            elif self.menu_indice == 2:
                self.tienda.cargar()
                self._tienda_indice = 0
                self.estado = ESTADO_MENU_TIENDA
            elif self.menu_indice == 3:
                self.ranking.recargar()
                self.estado = ESTADO_MENU_RANKING
            elif self.menu_indice == 4:
                self.estado = ESTADO_MENU_CONTROLES
            elif self.menu_indice == 5:
                self.corriendo = False

    # ─── Eventos de semilla ───────────────────────────────────────────────────
    def _eventos_menu_semilla(self, k: int) -> None:
        if k == pygame.K_ESCAPE:
            self.estado = ESTADO_MENU
            self.error_semilla = None
            return
        if k == pygame.K_BACKSPACE:
            self.buffer_semilla = self.buffer_semilla[:-1]
            self.error_semilla = None
            return
        if k == pygame.K_RETURN:
            self._intentar_iniciar_con_semilla()
            return
        if pygame.K_0 <= k <= pygame.K_9 and len(self.buffer_semilla) < 8:
            self.buffer_semilla += str(k - pygame.K_0)
            self.error_semilla = None

    def _intentar_iniciar_con_semilla(self) -> None:
        t = self.buffer_semilla.strip()
        if not t:
            self.error_semilla = 'Escribe un número.'
            return
        try:
            sem = int(t) % 100_000
            if sem == 0:
                sem = 1
        except ValueError:
            self.error_semilla = 'Semilla no válida.'
            return
        self.audio.detener_menu_loop()
        self._tutorial_slide = 0
        self.estado = ESTADO_TUTORIAL
        self._semilla_pendiente_tutorial = sem
        self.buffer_semilla = ''
        self.error_semilla = None

    # ─── Eventos de tienda ────────────────────────────────────────────────────
    def _eventos_tienda_teclado(self, k: int) -> None:
        from src.sistemas.tienda import TIENDA_ITEMS
        if k in (pygame.K_RETURN, pygame.K_ESCAPE):
            self.estado = ESTADO_MENU
        elif k == pygame.K_SPACE:
            # Intentar comprar el item seleccionado
            if self._tienda_indice < len(TIENDA_ITEMS):
                item_id = TIENDA_ITEMS[self._tienda_indice]['id']
                self.tienda.comprar(item_id)
        elif k == pygame.K_UP:
            self._tienda_indice = max(0, self._tienda_indice - 1)
        elif k == pygame.K_DOWN:
            from src.sistemas.tienda import TIENDA_ITEMS
            self._tienda_indice = min(len(TIENDA_ITEMS) - 1, self._tienda_indice + 1)

    def _eventos_tienda_click(self, pos: tuple) -> None:
        from src.sistemas.tienda import TIENDA_ITEMS
        # Los rects de compra se guardan en _tienda_rects (si existen)
        for i, r in enumerate(getattr(self, '_tienda_rects', [])):
            if r.collidepoint(pos):
                if i < len(TIENDA_ITEMS):
                    self.tienda.comprar(TIENDA_ITEMS[i]['id'])
                break

    # ─── Tutorial (instrucciones antes de jugar) ─────────────────────────────
    def _tutorial_saltar_al_juego(self) -> None:
        sem = self._semilla_pendiente_tutorial
        self._iniciar_partida(semilla_fija=sem, con_intro=True)

    def _tutorial_avanzar_o_empezar(self) -> None:
        self._tutorial_slide += 1
        if self._tutorial_slide >= len(TUTORIAL_SLIDES):
            self._tutorial_saltar_al_juego()

    def _tutorial_atras(self) -> None:
        self._tutorial_slide = max(0, self._tutorial_slide - 1)

    def _eventos_tutorial_teclado(self, k: int) -> None:
        if k == pygame.K_ESCAPE:
            self._tutorial_saltar_al_juego()
        elif k in (pygame.K_RIGHT, pygame.K_SPACE, pygame.K_RETURN):
            self._tutorial_avanzar_o_empezar()
        elif k == pygame.K_LEFT:
            self._tutorial_atras()

    def _continuar_al_siguiente_nivel(self) -> None:
        pts = self._puntaje_guardado_victoria
        self._iniciar_partida(conservar_nivel=True, con_intro=False)
        if self.pacman:
            self.pacman.puntaje = pts
        self.audio.iniciar_musica_fondo()
        self.audio.iniciar_loop_fantasmas()
        self.estado = ESTADO_JUGANDO

    # ─── Eventos de selección de mejora ──────────────────────────────────────
    def _eventos_seleccion_mejora_teclado(self, k: int) -> None:
        n = len(self._mejora_opciones)
        if k == pygame.K_1 and n >= 1:
            self._aplicar_mejora_seleccionada(0)
        elif k == pygame.K_2 and n >= 2:
            self._aplicar_mejora_seleccionada(1)
        elif k == pygame.K_3 and n >= 3:
            self._aplicar_mejora_seleccionada(2)
        elif k in (pygame.K_LEFT, pygame.K_a):
            self._mejora_seleccionada = (self._mejora_seleccionada - 1) % n
        elif k in (pygame.K_RIGHT, pygame.K_d):
            self._mejora_seleccionada = (self._mejora_seleccionada + 1) % n
        elif k in (pygame.K_RETURN, pygame.K_SPACE):
            self._aplicar_mejora_seleccionada(self._mejora_seleccionada)

    def _eventos_seleccion_mejora_click(self, pos: tuple) -> None:
        for i, rect in enumerate(self._mejora_rects):
            if rect.collidepoint(pos):
                self._aplicar_mejora_seleccionada(i)
                return

    def _aplicar_mejora_seleccionada(self, idx: int) -> None:
        if not self.sistema_mejoras or not self._mejora_opciones:
            self.estado = ESTADO_JUGANDO
            self.audio.iniciar_loop_fantasmas()
            return
        if idx >= len(self._mejora_opciones):
            return
        mid = self._mejora_opciones[idx]['id']
        origen = self._origen_seleccion_mejora

        if mid == MONEDAS_RECOMPENSA_NIVEL_ID:
            self.tienda.agregar_monedas(500)
            self._mensaje_roguelike = ('+500 monedas para la tienda', 180)
            if origen == 'puntos':
                self.sistema_mejoras.avanzar_umbral()
            if origen == 'victoria':
                self._continuar_al_siguiente_nivel()
            else:
                self.estado = ESTADO_JUGANDO
                self.audio.iniciar_loop_fantasmas()
            return

        msg = self.sistema_mejoras.aplicar_mejora(
            mid, pacman=self.pacman, fantasmas=self.fantasmas
        )
        if msg:
            self._mensaje_roguelike = (f'✦ {msg}', 180)
        if origen == 'puntos':
            self.sistema_mejoras.avanzar_umbral()

        if self.pacman and self.sistema_mejoras:
            self.pacman.aplicar_velocidad_bonus(self.sistema_mejoras.get_bonus_velocidad())

        if self.sistema_mejoras.consumir_fiebre():
            self._spawnear_fiebre_del_oro()

        if origen == 'victoria':
            self._continuar_al_siguiente_nivel()
        else:
            self.estado = ESTADO_JUGANDO
            self.audio.iniciar_loop_fantasmas()

    # ─── Fiebre del Oro ───────────────────────────────────────────────────────
    def _spawnear_fiebre_del_oro(self) -> None:
        """Spawna 15 fantasmas dorados que huyen del jugador; 10 s y desaparecen."""
        if not self.tablero or not self.gen:
            return
        pasillos = [
            (f, c)
            for f in range(self.tablero.filas)
            for c in range(self.tablero.columnas)
            if self.tablero.es_pasillo(f, c)
        ]
        if not pasillos:
            return
        for _ in range(15):
            pf, pc = self.gen.elegir(pasillos)
            fantasma_fiebre = FantasmaAleatorio(pf, pc, pf, pc, self.gen, color=(255, 180, 0))
            fantasma_fiebre.es_fiebre_oro = True
            # Fantasmas etéreos: huyen 10 s y desaparecen (timer propio, no el del miedo a pastilla)
            fantasma_fiebre.timer_fiebre_oro = 10 * FPS
            fantasma_fiebre.estado_especial = MODO_ASUSTADO
            fantasma_fiebre.timer_especial = fantasma_fiebre.timer_fiebre_oro
            fantasma_fiebre.velocidad = 1.0
            self.fantasmas.append(fantasma_fiebre)

    # ─── Actualización principal ──────────────────────────────────────────────
    def _actualizar(self) -> None:
        if self.estado == ESTADO_INTRO:
            if not self._intro_sonido_lanzado:
                self.audio.reproducir_inicio_y_preparar_canal()
                self._intro_sonido_lanzado = True
            if self.audio.intro_terminada():
                self.audio.iniciar_musica_fondo()
                self.audio.iniciar_loop_fantasmas()
                self.estado = ESTADO_JUGANDO
            return

        if self.estado == ESTADO_MUERTE_ANIM and self.pacman:
            if self.pacman.tick_animacion_muerte():
                self.pacman.vidas -= 1
                self.pacman.reiniciar_despues_muerte()
                if self.pacman.vidas <= 0:
                    pts = self.pacman.puntaje
                    self._game_over_mejoro_highscore = self.ranking.actualizar_si_mejor(
                        self.nombre_jugador, pts, self.semilla_partida
                    )
                    self._game_over_posicion_ranking = self.ranking.posicion_global(pts)
                    self._game_over_total_ranking = self.ranking.total_jugadores_en_tabla()
                    # Guardar monedas en la tienda al perder
                    self.tienda.agregar_monedas(self.pacman.puntaje)
                    self.audio.detener_musica()
                    self.audio.detener_loop_fantasmas()
                    self.audio.reproducir('game_over')
                    self.estado = ESTADO_GAME_OVER
                else:
                    self._reposicionar_actores()
                    self.audio.iniciar_loop_fantasmas()
                    self.estado = ESTADO_JUGANDO
            return

        # Selección de mejora: juego pausado
        if self.estado == ESTADO_SELECCION_MEJORA:
            return

        if self.estado != ESTADO_JUGANDO or not self.pacman or not self.tablero:
            return

        self._tick_mensaje_roguelike()
        self._tick_popups_puntos()

        self._puntaje_prev = self.pacman.puntaje
        self.pacman.mover(self.tablero)

        if self.pacman.invencible:
            for f in self.fantasmas:
                if not f.es_fiebre_oro:
                    f.asustar()
            self.pacman.invencible = False

        delta = self.pacman.puntaje - self._puntaje_prev
        if delta == 10:
            self.audio.reproducir('comer')
        elif delta == 50:
            self.audio.reproducir('comer_fruta')

        # ── Umbral de división (evento roguelike de laberinto) ─────────────
        progreso = (
            self.tablero.puntos_comidos / self.tablero.total_puntos
            if self.tablero.total_puntos > 0 else 0
        )
        um = self.umbral_division / self.tablero.total_puntos if self.tablero.total_puntos > 0 else 0
        if progreso >= um and not self._division_nivel_hecha:
            self._division_nivel_hecha = True
            self._aplicar_evento_division_roguelike()

        # ── Tick de mejoras ────────────────────────────────────────────────
        if self.sistema_mejoras:
            eventos_mej = self.sistema_mejoras.tick(self.fantasmas, self.pacman)
            if eventos_mej.get('freeze_inicio'):
                self._mensaje_roguelike = ('❄  ¡CONGELADOR ACTIVADO!  ❄', 120)
            if eventos_mej.get('escudo_recargado'):
                self._mensaje_roguelike = ('🛡  Escudo recargado', 90)
            if eventos_mej.get('modo_fantasma_fin'):
                self._mensaje_roguelike = ('Modo Fantasma finalizado', 90)

        # ── Chequear level-up de mejoras ───────────────────────────────────
        if self.sistema_mejoras and self.sistema_mejoras.chequear_levelup(self.pacman.puntaje):
            self._origen_seleccion_mejora = 'puntos'
            self._mejora_opciones = self.sistema_mejoras.obtener_opciones()
            self._mejora_seleccionada = 0
            self._mejora_rects = []
            self.audio.detener_loop_fantasmas()
            self.audio.reproducir('subir_nivel')
            self.estado = ESTADO_SELECCION_MEJORA
            return

        # Mover fantasmas
        for f in self.fantasmas:
            f.mover(self.tablero, self.pacman)

        # Fantasmas etéreos (fiebre del oro): eliminar al cumplir timer_fiebre_oro (tras mover)
        self.fantasmas = [
            f for f in self.fantasmas
            if not (f.es_fiebre_oro and f.timer_fiebre_oro <= 0)
        ]

        n_ret = sum(1 for f in self.fantasmas if f.estado_especial == MODO_RETIRADA)
        if self._fantasmas_en_retirada_prev > 0 and n_ret == 0:
            self.audio.detener_fantasma_return()
        self._fantasmas_en_retirada_prev = n_ret

        self._verificar_colisiones()

        # ── Nivel completado: misma recompensa que al subir de EXP (cartas) ──
        if self.tablero.completado:
            self._popups_puntos.clear()
            self.audio.detener_loop_fantasmas()
            self.audio.reproducir('subir_nivel')
            self._puntaje_guardado_victoria = self.pacman.puntaje
            self.nivel += 1
            if self.sistema_mejoras:
                self._origen_seleccion_mejora = 'victoria'
                self._mejora_opciones = self.sistema_mejoras.obtener_recompensa_nivel_completado()
                self._mejora_seleccionada = 0
                self._mejora_rects = []
                self.estado = ESTADO_SELECCION_MEJORA
            else:
                self._continuar_al_siguiente_nivel()

    # ─── Colisiones ───────────────────────────────────────────────────────────
    def _verificar_colisiones(self) -> None:
        if self.pacman is None:
            return
        fantasmas_a_eliminar = []
        for f in self.fantasmas:
            if f.fila != self.pacman.fila or f.col != self.pacman.col:
                continue
            if f.estado_especial == MODO_ASUSTADO:
                if f.es_fiebre_oro:
                    # Fiebre del Oro: dar 500 pts y eliminar el fantasma
                    self.pacman.puntaje += 500
                    self._agregar_popup_puntos('+500 💰')
                    self.audio.reproducir_fantasma_return()
                    fantasmas_a_eliminar.append(f)
                else:
                    f.ser_comido()
                    self.pacman.puntaje += 200
                    self._agregar_popup_puntos('+200')
                    self.audio.reproducir_fantasma_return()
                continue
            if f.puede_danar_jugador():
                # ── Chequear escudo antes de morir ──
                if self.sistema_mejoras and self.sistema_mejoras.escudo_activo:
                    self.sistema_mejoras.consumir_escudo()
                    self._mensaje_roguelike = ('🛡  ¡Escudo absorbió el golpe!', 150)
                    self._agregar_popup_puntos('🛡')
                    # No muere, pero empujar a modo inmune brevemente
                    f._ticks_gracia_danio = 60
                    continue
                self._iniciar_muerte()
                return

        for f in fantasmas_a_eliminar:
            if f in self.fantasmas:
                self.fantasmas.remove(f)

    # ─── Muerte ───────────────────────────────────────────────────────────────
    def _iniciar_muerte(self) -> None:
        self.estado = ESTADO_MUERTE_ANIM
        self.pacman.iniciar_animacion_muerte()
        self.audio.reproducir('morir')
        self.audio.detener_loop_fantasmas()

    def _reposicionar_actores(self) -> None:
        assert self.tablero is not None and self.pacman is not None
        f, c = self.tablero.filas // 2, self.tablero.columnas // 2
        if self.tablero.es_muro(f, c):
            for i in range(self.tablero.filas):
                for j in range(self.tablero.columnas):
                    if self.tablero.es_pasillo(i, j):
                        f, c = i, j
                        break
                else:
                    continue
                break
        self.pacman.fila, self.pacman.col = f, c
        self.pacman.px, self.pacman.py = c * TAM_CELDA, f * TAM_CELDA
        self.pacman.target_px, self.pacman.target_py = self.pacman.px, self.pacman.py
        for fta in self.fantasmas:
            fta.fila, fta.col = fta.fila_base, fta.col_base
            fta.px, fta.py = fta.col * TAM_CELDA, fta.fila * TAM_CELDA
            fta.target_px, fta.target_py = fta.px, fta.py
            fta.estado_especial = None
            fta.congelado = False

    # ─── Dibujo ───────────────────────────────────────────────────────────────
    def _dibujar(self) -> None:
        self.pantalla.fill(COLOR_FONDO)

        if self.estado == ESTADO_MENU_NOMBRE:
            ui_menu.dibujar_menu_nombre(self.pantalla, self.buffer_nombre, self.tiempo_ui)
        elif self.estado == ESTADO_MENU:
            self._rect_slider_mus, self._rect_slider_sfx = ui_menu.dibujar_menu_principal(
                self.pantalla, self.menu_indice, self.tiempo_ui,
                self.vol_musica, self.vol_sfx, monedas_tienda=self.tienda.monedas,
                nombre_jugador=self.nombre_jugador,
            )
        elif self.estado == ESTADO_MENU_SEMILLA:
            ui_menu.dibujar_menu_semilla(self.pantalla, self.buffer_semilla, self.error_semilla)
        elif self.estado == ESTADO_MENU_RANKING:
            self._ranking_rect_borrar = ui_menu.dibujar_menu_ranking(
                self.pantalla, self.ranking.entradas, mouse_pos=pygame.mouse.get_pos(),
            )
        elif self.estado == ESTADO_MENU_CONTROLES:
            ui_menu.dibujar_menu_controles(self.pantalla)
        elif self.estado == ESTADO_MENU_TIENDA:
            self._tienda_rects = ui_menu.dibujar_menu_tienda(
                self.pantalla, self.tienda, self._tienda_indice, self.tiempo_ui,
                mouse_pos=pygame.mouse.get_pos(),
            )

        elif self.estado == ESTADO_TUTORIAL:
            self._tutorial_rect_atras, self._tutorial_rect_sig, self._tutorial_rect_skip = (
                ui_menu.dibujar_tutorial(
                    self.pantalla, ANCHO, ALTO,
                    self._tutorial_slide, self.tiempo_ui,
                    pygame.mouse.get_pos(),
                )
            )

        elif self.estado in (ESTADO_INTRO, ESTADO_JUGANDO, ESTADO_MUERTE_ANIM):
            self._dibujar_juego()

        elif self.estado == ESTADO_SELECCION_MEJORA:
            self._dibujar_juego()
            if self.sistema_mejoras:
                nivel_mejora = self.sistema_mejoras._n_mejoras + 1
                umbral = self.sistema_mejoras.get_umbral()
                self._mejora_rects = ui_menu.dibujar_seleccion_mejora(
                    self.pantalla, ANCHO, ALTO,
                    self._mejora_opciones,
                    nivel_actual_fn=self.sistema_mejoras.nivel_de,
                    desc_siguiente_fn=self.sistema_mejoras.get_descripcion_nivel_siguiente,
                    seleccionada=self._mejora_seleccionada,
                    tiempo_ui=self.tiempo_ui,
                    mouse_pos=pygame.mouse.get_pos(),
                    nivel_mejora=nivel_mejora,
                    umbral_exp=umbral,
                    recompensa_por_nivel=(self._origen_seleccion_mejora == 'victoria'),
                )

        elif self.estado == ESTADO_PAUSA:
            self._dibujar_juego()
            ui_menu.dibujar_pausa_overlay(self.pantalla, ANCHO, ALTO)

        elif self.estado == ESTADO_GAME_OVER:
            if self.pacman is None:
                return
            self._dibujar_juego()
            ui_menu.dibujar_game_over_pantalla(
                self.pantalla,
                ANCHO,
                ALTO,
                self.nombre_jugador,
                self.pacman.puntaje,
                self._game_over_mejoro_highscore,
                self._game_over_posicion_ranking,
                self._game_over_total_ranking,
            )

        pygame.display.flip()

    def _dibujar_juego(self) -> None:
        if not self.tablero or not self.pacman:
            return
        umbral_exp = self.sistema_mejoras.get_umbral() if self.sistema_mejoras else 500
        self.hud.dibujar(
            self.pantalla,
            pacman=self.pacman,
            nivel=self.nivel,
            tablero=self.tablero,
            umbral_division=self.umbral_division,
            mejoras=self.sistema_mejoras,
            puntaje_exp=self.pacman.puntaje,
            umbral_exp=umbral_exp,
        )
        ox, oy = self._offsets_tablero()
        self.tablero.dibujar(self.pantalla, ox, oy)
        for f in self.fantasmas:
            f.dibujar(self.pantalla, ox, oy)
        if self.sistema_mejoras:
            self.pacman.escudo_activo_visual = (
                self.sistema_mejoras.nivel_de('escudo') > 0 and self.sistema_mejoras.escudo_activo
            )
        else:
            self.pacman.escudo_activo_visual = False
        self.pacman.dibujar(self.pantalla, ox, oy)
        self._dibujar_popups_puntuacion()
        self._dibujar_banner_roguelike()

        # Indicadores de mejoras al lado derecho del tablero
        if self.sistema_mejoras:
            self.hud.dibujar_indicadores_mejoras(
                self.pantalla, self.sistema_mejoras,
                ox, oy,
                self.tablero.columnas * TAM_CELDA,
                self.tablero.filas * TAM_CELDA,
            )

        # Banda inferior (vidas, comida, semilla) encima del tablero para que no la tapen los sprites
        self.hud.dibujar_banda_inferior(
            self.pantalla,
            pacman=self.pacman,
            tablero=self.tablero,
            semilla=self.semilla_partida,
            mejoras=self.sistema_mejoras,
        )

    def _offsets_tablero(self):
        if not self.tablero:
            return 0, 0
        ox = (ANCHO - (self.tablero.columnas * TAM_CELDA)) // 2
        oy = HUD_SUP + max(0, (ALTO - HUD_SUP - HUD_INF - self.tablero.filas * TAM_CELDA) // 2)
        return ox, oy

    # ─── Popups y banners ─────────────────────────────────────────────────────
    def _tick_mensaje_roguelike(self) -> None:
        if not self._mensaje_roguelike:
            return
        txt, left = self._mensaje_roguelike
        if left > 1:
            self._mensaje_roguelike = (txt, left - 1)
        else:
            self._mensaje_roguelike = None

    def _tick_popups_puntos(self) -> None:
        nuevos = []
        for p in self._popups_puntos:
            p['v'] -= 1
            p['y'] -= 0.75
            if p['v'] > 0:
                nuevos.append(p)
        self._popups_puntos = nuevos

    def _agregar_popup_puntos(self, texto: str) -> None:
        if not self.pacman or not self.tablero:
            return
        ox, oy = self._offsets_tablero()
        cx = ox + self.pacman.px + TAM_CELDA // 2
        cy = oy + self.pacman.py + TAM_CELDA // 2
        self._popups_puntos.append({'txt': texto, 'x': float(cx), 'y': float(cy), 'v': 55})

    def _dibujar_popups_puntuacion(self) -> None:
        if not self._popups_puntos:
            return
        fu = self._fuente_popup
        for p in self._popups_puntos:
            t = fu.render(p['txt'], True, (255, 230, 60))
            s = fu.render(p['txt'], True, (0, 0, 0))
            x = int(p['x'] - t.get_width() // 2)
            y = int(p['y'])
            self.pantalla.blit(s, (x + 2, y + 2))
            self.pantalla.blit(t, (x, y))

    def _dibujar_banner_roguelike(self) -> None:
        if not self._mensaje_roguelike or self.estado not in (ESTADO_JUGANDO, ESTADO_MUERTE_ANIM):
            return
        txt, _ = self._mensaje_roguelike
        surf = self._fuente_banner_rlk.render(txt, True, (255, 220, 100))
        bx = ANCHO // 2 - surf.get_width() // 2
        by = HUD_SUP + 2
        pad = pygame.Surface((surf.get_width() + 16, surf.get_height() + 6), pygame.SRCALPHA)
        pad.fill((30, 20, 60, 200))
        self.pantalla.blit(pad, (bx - 8, by - 2))
        self.pantalla.blit(surf, (bx, by))

    # ─── Evento de división de laberinto ─────────────────────────────────────
    def _aplicar_evento_division_roguelike(self) -> None:
        if not self.fantasmas or not self.gen:
            return
        ref = self.fantasmas[-1]
        bf, bc = ref.fila_base, ref.col_base
        self.fantasmas.append(
            FantasmaAleatorio(bf, bc, bf, bc, self.gen, color=(198, 42, 42))
        )
        self._mensaje_roguelike = ('¡LABERINTO INESTABLE! +1 FANTASMA · +VELOCIDAD', 120)
        pac_v = self.pacman.velocidad if self.pacman else 2.0
        cap = min(_VELOCIDAD_MAX_FANTASMA_ABS, pac_v * _RATIO_CAP_VS_PACMAN)
        for f in self.fantasmas:
            nv = min(cap, f._velocidad_normal + _INCREMENTO_VEL_DIVISION)
            f._velocidad_normal = nv
            if f.estado_especial is None and not f.congelado:
                f.velocidad = nv

    # ─── Iniciar partida ──────────────────────────────────────────────────────
    def _iniciar_partida(
        self,
        conservar_nivel: bool = False,
        semilla_fija: int | None = None,
        con_intro: bool = True,
    ) -> None:
        import time

        self.audio.detener_loop_fantasmas()
        self.audio.detener_musica()
        self.tienda.set_usuario(self.nombre_jugador)

        if not conservar_nivel:
            self.nivel = 1
            # Nueva run: crear sistema de mejoras fresco
            self.sistema_mejoras = None

        if semilla_fija is not None:
            semilla = semilla_fija % 100_000
            if semilla == 0:
                semilla = 1
        else:
            semilla = int(time.time()) % 100_000

        self.semilla_partida = semilla
        self.gen = GeneradorAleatorio(semilla=semilla, metodo='comb')
        self.sistema_loot = SistemaLoot(self.gen)
        self.mapeador = GeneradorMapa(self.gen)
        self.tablero = self.mapeador.generar(filas=19, columnas=23, cobertura=0.60)

        min_p = int(self.tablero.total_puntos * 0.15)
        max_p = int(self.tablero.total_puntos * 0.60)
        self.umbral_division = self.gen.entero(min_p, max_p)

        pasillos = [
            (f, c)
            for f in range(self.tablero.filas)
            for c in range(self.tablero.columnas)
            if self.tablero.es_pasillo(f, c)
        ]

        spawn_pf, spawn_pc = next(
            ((f, c) for f, c in pasillos if self.tablero.obtener(f, c) == PUNTO),
            next(
                ((f, c) for f, c in pasillos if self.tablero.obtener(f, c) != SUPER_PUNTO),
                pasillos[0],
            ),
        )
        self.pacman = PacMan(spawn_pf, spawn_pc)
        self._puntaje_prev = self.pacman.puntaje

        # ── Crear o preservar sistema de mejoras ──────────────────────────
        if not conservar_nivel or self.sistema_mejoras is None:
            self.sistema_mejoras = SistemaMejoras(self.gen)
            # Aplicar bonus de velocidad de la tienda
            self.sistema_mejoras.bonus_velocidad_permanente = self.tienda.get_bonus_velocidad()
        else:
            # Mantener las mejoras entre niveles: solo actualizar el gen (para reproducibilidad)
            self.sistema_mejoras.gen = self.gen

        # Aplicar velocidad al pacman recién creado
        self.pacman.aplicar_velocidad_bonus(self.sistema_mejoras.get_bonus_velocidad())

        # ── Spawnear fantasmas según el nivel ─────────────────────────────
        self.fantasmas = []
        tipos = _calcular_spawn_fantasmas(self.nivel)
        spawn_pts = pasillos[-len(tipos):]  # tomar las últimas N posiciones
        if len(spawn_pts) < len(tipos):
            spawn_pts = [pasillos[-1]] * len(tipos)

        for i, tipo in enumerate(tipos):
            sf, sc = spawn_pts[min(i, len(spawn_pts) - 1)]
            if tipo == 'blanco':
                self.fantasmas.append(FantasmaBlanco(sf, sc, sf, sc, self.gen))
            elif tipo == 'perseguidor':
                self.fantasmas.append(FantasmaPerseguidor(sf, sc, sf, sc, self.gen))
            else:
                self.fantasmas.append(FantasmaAleatorio(sf, sc, sf, sc, self.gen))

        self._intro_sonido_lanzado = False
        self._fantasmas_en_retirada_prev = 0
        self._division_nivel_hecha = False
        self._mensaje_roguelike = None
        self._popups_puntos.clear()
        self._mejora_opciones = []
        self._mejora_rects = []
        self.audio.detener_fantasma_return()

        if con_intro:
            self.estado = ESTADO_INTRO
        else:
            self.audio.iniciar_musica_fondo()
            self.audio.iniciar_loop_fantasmas()
            self.estado = ESTADO_JUGANDO


if __name__ == '__main__':
    Juego().ejecutar()
