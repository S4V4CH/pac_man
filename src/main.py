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
)
from src.sistemas import SistemaLoot, SistemaRanking
from src.ui.hud import HUD
from src.ui.audio import GestorAudio
from src.ui import menu as ui_menu
from src.ui.menu import OPCIONES_MENU

ANCHO = 800
ALTO = 680
FPS = 60
TITULO = "Pac-Man Roguelike"

COLOR_FONDO = (10, 10, 30)

HUD_SUP = 54
HUD_INF = 48

ESTADO_MENU = 'menu'
ESTADO_MENU_SEMILLA = 'menu_semilla'
ESTADO_MENU_RANKING = 'menu_ranking'
ESTADO_MENU_CONTROLES = 'menu_controles'
ESTADO_INTRO = 'intro'
ESTADO_JUGANDO = 'jugando'
ESTADO_MUERTE_ANIM = 'muerte_anim'
ESTADO_PAUSA = 'pausa'
ESTADO_GAME_OVER = 'game_over'
ESTADO_VICTORIA_NIVEL = 'victoria_nivel'


class Juego:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption(TITULO)
        self.pantalla = pygame.display.set_mode((ANCHO, ALTO))
        self._fuente_popup = pygame.font.SysFont('Arial', 22, bold=True)
        self._fuente_banner_rlk = pygame.font.SysFont('Arial', 17, bold=True)
        self.reloj = pygame.time.Clock()
        self.estado = ESTADO_MENU
        self.gen = None
        self.tablero = None
        self.mapeador = None
        self.pacman = None
        self.fantasmas = []
        self.umbral_division = 0
        self.semilla_partida = 0
        self.ranking = SistemaRanking()
        self.sistema_loot: SistemaLoot | None = None
        self.nivel = 1
        self._frames_victoria = 0
        self._puntaje_guardado_victoria = 0
        self._nivel_terminado_victoria = 1
        self._siguiente_nivel_victoria = 2

        self.menu_indice = 0
        self.buffer_semilla = ''
        self.error_semilla: str | None = None
        self.tiempo_ui = 0

        self.vol_musica = 0.65
        self.vol_sfx = 0.75
        self._rect_slider_mus = pygame.Rect(0, 0, 0, 0)
        self._rect_slider_sfx = pygame.Rect(0, 0, 0, 0)
        self._arrastrando_volumen: str | None = None

        self.hud = HUD(ANCHO, ALTO)
        self.audio = GestorAudio()
        self.audio.set_volumen_musica(self.vol_musica)
        self.audio.set_volumen_sfx(self.vol_sfx)
        self.audio.iniciar_menu_loop()

        self._puntaje_prev = 0
        self._game_over_es_record = False
        self._intro_sonido_lanzado = False
        self._fantasmas_en_retirada_prev = 0
        self._division_nivel_hecha = False
        self._mensaje_roguelike: tuple[str, int] | None = None
        self._popups_puntos: list[dict] = []
        self._ultimo_loot_victoria: dict | None = None

        self.corriendo = True

    def ejecutar(self) -> None:
        while self.corriendo:
            self.tiempo_ui += 1
            self._manejar_eventos()
            self._actualizar()
            self._dibujar()
            self.reloj.tick(FPS)
        pygame.quit()
        sys.exit()

    def _volumen_desde_x(self, mx: int, rect: pygame.Rect) -> float:
        return max(0.0, min(1.0, (mx - rect.x) / max(1, rect.w)))

    def _aplicar_volumen_mouse(self, mx: int) -> None:
        if self._arrastrando_volumen == 'musica':
            self.vol_musica = self._volumen_desde_x(mx, self._rect_slider_mus)
            self.audio.set_volumen_musica(self.vol_musica)
        elif self._arrastrando_volumen == 'sfx':
            self.vol_sfx = self._volumen_desde_x(mx, self._rect_slider_sfx)
            self.audio.set_volumen_sfx(self.vol_sfx)

    def _manejar_eventos(self) -> None:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                self.corriendo = False
                continue

            if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                if self.estado == ESTADO_MENU:
                    mx, my = evento.pos
                    if self._rect_slider_mus.collidepoint(mx, my):
                        self._arrastrando_volumen = 'musica'
                        self._aplicar_volumen_mouse(mx)
                    elif self._rect_slider_sfx.collidepoint(mx, my):
                        self._arrastrando_volumen = 'sfx'
                        self._aplicar_volumen_mouse(mx)

            if evento.type == pygame.MOUSEBUTTONUP and evento.button == 1:
                self._arrastrando_volumen = None

            if evento.type == pygame.MOUSEMOTION:
                if self.estado == ESTADO_MENU and self._arrastrando_volumen and evento.buttons[0]:
                    self._aplicar_volumen_mouse(evento.pos[0])

            if self.estado == ESTADO_JUGANDO and self.pacman:
                self.pacman.manejar_teclado(evento)

            if evento.type != pygame.KEYDOWN:
                continue

            k = evento.key

            if self.estado == ESTADO_MENU:
                self._eventos_menu_principal(k)
            elif self.estado == ESTADO_MENU_SEMILLA:
                self._eventos_menu_semilla(k)
            elif self.estado in (ESTADO_MENU_RANKING, ESTADO_MENU_CONTROLES):
                if k in (pygame.K_RETURN, pygame.K_ESCAPE, pygame.K_SPACE):
                    self.estado = ESTADO_MENU
            elif self.estado == ESTADO_VICTORIA_NIVEL:
                if k in (pygame.K_RETURN, pygame.K_SPACE):
                    self._frames_victoria = 0
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
                elif k == pygame.K_m:
                    self.audio.alternar_musica()
            elif self.estado == ESTADO_GAME_OVER:
                if k == pygame.K_RETURN:
                    self.audio.iniciar_menu_loop()
                    self.estado = ESTADO_MENU

    def _eventos_menu_principal(self, k: int) -> None:
        if k == pygame.K_ESCAPE:
            self.corriendo = False
            return
        if k == pygame.K_UP:
            self.menu_indice = (self.menu_indice - 1) % len(OPCIONES_MENU)
        elif k == pygame.K_DOWN:
            self.menu_indice = (self.menu_indice + 1) % len(OPCIONES_MENU)
        elif k == pygame.K_RETURN:
            if self.menu_indice == 0:
                self.audio.detener_menu_loop()
                self._iniciar_partida(con_intro=True)
            elif self.menu_indice == 1:
                self.buffer_semilla = ''
                self.error_semilla = None
                self.estado = ESTADO_MENU_SEMILLA
            elif self.menu_indice == 2:
                self.ranking.recargar()
                self.estado = ESTADO_MENU_RANKING
            elif self.menu_indice == 3:
                self.estado = ESTADO_MENU_CONTROLES
            elif self.menu_indice == 4:
                self.corriendo = False

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
        self._iniciar_partida(semilla_fija=sem, con_intro=True)
        self.buffer_semilla = ''
        self.error_semilla = None

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
                    self._game_over_es_record = self.ranking.es_record(self.pacman.puntaje)
                    if self._game_over_es_record:
                        self.ranking.guardar('Jugador', self.pacman.puntaje, self.semilla_partida)
                    self.audio.detener_musica()
                    self.audio.detener_loop_fantasmas()
                    self.audio.reproducir('game_over')
                    self.estado = ESTADO_GAME_OVER
                else:
                    self._reposicionar_actores()
                    self.audio.iniciar_loop_fantasmas()
                    self.estado = ESTADO_JUGANDO
            return

        if self.estado == ESTADO_VICTORIA_NIVEL:
            self._frames_victoria -= 1
            if self._frames_victoria <= 0:
                pts = self._puntaje_guardado_victoria
                self._iniciar_partida(conservar_nivel=True, con_intro=False)
                self.pacman.puntaje = pts
                self.audio.iniciar_musica_fondo()
                self.audio.iniciar_loop_fantasmas()
                self.estado = ESTADO_JUGANDO
            return

        if self.estado != ESTADO_JUGANDO or not self.pacman or not self.tablero:
            return

        self._tick_mensaje_roguelike()
        self._tick_popups_puntos()

        self._puntaje_prev = self.pacman.puntaje
        self.pacman.mover(self.tablero)

        if self.pacman.invencible:
            for f in self.fantasmas:
                f.asustar()
            self.pacman.invencible = False

        delta = self.pacman.puntaje - self._puntaje_prev
        if delta == 10:
            self.audio.reproducir('comer')
        elif delta == 50:
            self.audio.reproducir('comer_fruta')

        progreso = (
            self.tablero.puntos_comidos / self.tablero.total_puntos
            if self.tablero.total_puntos > 0
            else 0
        )
        um = self.umbral_division / self.tablero.total_puntos if self.tablero.total_puntos > 0 else 0
        if progreso >= um and not self._division_nivel_hecha:
            self._division_nivel_hecha = True
            self._aplicar_evento_division_roguelike()

        for f in self.fantasmas:
            f.mover(self.tablero, self.pacman)

        n_ret = sum(1 for f in self.fantasmas if f.estado_especial == MODO_RETIRADA)
        if self._fantasmas_en_retirada_prev > 0 and n_ret == 0:
            self.audio.detener_fantasma_return()
        self._fantasmas_en_retirada_prev = n_ret

        self._verificar_colisiones()

        if self.tablero.completado:
            self._popups_puntos.clear()
            self.audio.detener_loop_fantasmas()
            self.audio.reproducir('subir_nivel')
            self._puntaje_guardado_victoria = self.pacman.puntaje
            self._ultimo_loot_victoria = None
            if self.sistema_loot:
                item = self.sistema_loot.tirar_loot()
                self._ultimo_loot_victoria = item
                if item:
                    if item.get('id') == 'vida':
                        self.pacman.vidas += 1
                    else:
                        self.pacman.puntaje += item.get('puntos', 0)
                self._puntaje_guardado_victoria = self.pacman.puntaje
            self._nivel_terminado_victoria = self.nivel
            self.nivel += 1
            self._siguiente_nivel_victoria = self.nivel
            self._frames_victoria = 120
            self.estado = ESTADO_VICTORIA_NIVEL

    def _verificar_colisiones(self) -> None:
        if self.pacman is None:
            return
        for f in self.fantasmas:
            if f.fila != self.pacman.fila or f.col != self.pacman.col:
                continue
            if f.estado_especial == MODO_ASUSTADO:
                f.ser_comido()
                self.pacman.puntaje += 200
                self._agregar_popup_puntos('+200')
                self.audio.reproducir_fantasma_return()
                continue
            if f.puede_danar_jugador():
                self._iniciar_muerte()
                return

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

    def _dibujar(self) -> None:
        self.pantalla.fill(COLOR_FONDO)

        if self.estado == ESTADO_MENU:
            self._rect_slider_mus, self._rect_slider_sfx = ui_menu.dibujar_menu_principal(
                self.pantalla, self.menu_indice, self.tiempo_ui, self.vol_musica, self.vol_sfx
            )
        elif self.estado == ESTADO_MENU_SEMILLA:
            ui_menu.dibujar_menu_semilla(self.pantalla, self.buffer_semilla, self.error_semilla)
        elif self.estado == ESTADO_MENU_RANKING:
            ui_menu.dibujar_menu_ranking(self.pantalla, self.ranking.entradas)
        elif self.estado == ESTADO_MENU_CONTROLES:
            ui_menu.dibujar_menu_controles(self.pantalla)
        elif self.estado in (ESTADO_INTRO, ESTADO_JUGANDO, ESTADO_MUERTE_ANIM):
            self._dibujar_juego()
        elif self.estado == ESTADO_VICTORIA_NIVEL:
            self._dibujar_juego()
            ui_menu.dibujar_victoria_nivel(
                self.pantalla,
                ANCHO,
                ALTO,
                self._nivel_terminado_victoria,
                self._siguiente_nivel_victoria,
                self.tiempo_ui,
                loot=self._ultimo_loot_victoria,
                semilla=self.semilla_partida,
            )
        elif self.estado == ESTADO_PAUSA:
            self._dibujar_juego()
            ui_menu.dibujar_pausa_overlay(self.pantalla, ANCHO, ALTO)
        elif self.estado == ESTADO_GAME_OVER:
            if self.pacman is None:
                return
            self._dibujar_juego()
            ui_menu.dibujar_game_over_pantalla(
                self.pantalla, ANCHO, ALTO, self.pacman.puntaje, self._game_over_es_record
            )

        pygame.display.flip()

    def _dibujar_juego(self) -> None:
        if not self.tablero or not self.pacman:
            return
        self.hud.dibujar(
            self.pantalla,
            pacman=self.pacman,
            nivel=self.nivel,
            tablero=self.tablero,
            semilla=self.semilla_partida,
            umbral_division=self.umbral_division,
        )
        ox, oy = self._offsets_tablero()
        self.tablero.dibujar(self.pantalla, ox, oy)
        for f in self.fantasmas:
            f.dibujar(self.pantalla, ox, oy)
        self.pacman.dibujar(self.pantalla, ox, oy)
        self._dibujar_popups_puntuacion()
        self._dibujar_banner_roguelike()

    def _offsets_tablero(self) -> tuple[int, int]:
        if not self.tablero:
            return 0, 0
        ox = (ANCHO - (self.tablero.columnas * TAM_CELDA)) // 2
        oy = (
            HUD_SUP
            + max(0, (ALTO - HUD_SUP - HUD_INF - self.tablero.filas * TAM_CELDA) // 2)
        )
        return ox, oy

    def _tick_mensaje_roguelike(self) -> None:
        if not self._mensaje_roguelike:
            return
        txt, left = self._mensaje_roguelike
        if left > 1:
            self._mensaje_roguelike = (txt, left - 1)
        else:
            self._mensaje_roguelike = None

    def _tick_popups_puntos(self) -> None:
        nuevos: list[dict] = []
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
        if not self._mensaje_roguelike or self.estado != ESTADO_JUGANDO:
            return
        txt, _ = self._mensaje_roguelike
        surf = self._fuente_banner_rlk.render(txt, True, (255, 220, 100))
        bx = ANCHO // 2 - surf.get_width() // 2
        by = HUD_SUP + 2
        pad = pygame.Surface((surf.get_width() + 16, surf.get_height() + 6), pygame.SRCALPHA)
        pad.fill((30, 20, 60, 200))
        self.pantalla.blit(pad, (bx - 8, by - 2))
        self.pantalla.blit(surf, (bx, by))

    def _aplicar_evento_division_roguelike(self) -> None:
        """Fase 5 / roguelike: al superar el umbral del laberinto, refuerzo enemigo + ritmo."""
        if not self.fantasmas or not self.gen:
            return
        ref = self.fantasmas[-1]
        bf, bc = ref.fila_base, ref.col_base
        self.fantasmas.append(
            FantasmaAleatorio(bf, bc, bf, bc, self.gen, color=(198, 42, 42))
        )
        self._mensaje_roguelike = ('¡LABERINTO INESTABLE! +1 FANTASMA · +VELOCIDAD', 120)
        for f in self.fantasmas:
            nv = min(2.85, f._velocidad_normal + 0.1)
            f._velocidad_normal = nv
            if f.estado_especial is None:
                f.velocidad = nv

    def _iniciar_partida(
        self,
        conservar_nivel: bool = False,
        semilla_fija: int | None = None,
        con_intro: bool = True,
    ) -> None:
        import time

        self.audio.detener_loop_fantasmas()
        self.audio.detener_musica()

        if not conservar_nivel:
            self.nivel = 1

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
        # No spawnear sobre super pastilla: activaría invencible y asustaría a todos al primer frame.
        spawn_pf, spawn_pc = next(
            ((f, c) for f, c in pasillos if self.tablero.obtener(f, c) == PUNTO),
            next(
                ((f, c) for f, c in pasillos if self.tablero.obtener(f, c) != SUPER_PUNTO),
                pasillos[0],
            ),
        )
        self.pacman = PacMan(spawn_pf, spawn_pc)
        self._puntaje_prev = self.pacman.puntaje

        self.fantasmas = []
        fb_f, fb_c = pasillos[-1]
        self.fantasmas.append(FantasmaBlanco(fb_f, fb_c, fb_f, fb_c, self.gen))
        ff_p, fc_p = pasillos[-2]
        self.fantasmas.append(FantasmaPerseguidor(ff_p, fc_p, ff_p, fc_p, self.gen))
        ff_a, fc_a = pasillos[-3]
        self.fantasmas.append(FantasmaAleatorio(ff_a, fc_a, ff_a, fc_a, self.gen))

        self._intro_sonido_lanzado = False
        self._fantasmas_en_retirada_prev = 0
        self._division_nivel_hecha = False
        self._mensaje_roguelike = None
        self._popups_puntos.clear()
        self._ultimo_loot_victoria = None
        self.audio.detener_fantasma_return()
        if con_intro:
            self.estado = ESTADO_INTRO
        else:
            self.audio.iniciar_musica_fondo()
            self.audio.iniciar_loop_fantasmas()
            self.estado = ESTADO_JUGANDO


if __name__ == '__main__':
    Juego().ejecutar()
