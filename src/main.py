import sys
import os
import pygame

# Añadir la raíz del proyecto al path para que encuentre 'lib'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lib import GeneradorAleatorio
from src.mundo.generador_mapa import GeneradorMapa
from src.mundo.tablero import TAM_CELDA
from src.entidades.pacman import PacMan
from src.entidades.fantasma import FantasmaAleatorio, FantasmaPerseguidor

# ─── Constantes ────────────────────────────────────────────────────────────────
ANCHO         = 800
ALTO          = 650
FPS           = 60
TITULO        = "Pac-Man Roguelike - Fase 4: IA Avanzada (A*)"

COLOR_FONDO   = (10, 10, 30)
COLOR_TEXTO   = (255, 255, 255)

ESTADO_MENU      = 'menu'
ESTADO_JUGANDO   = 'jugando'
ESTADO_PAUSA     = 'pausa'
ESTADO_GAME_OVER = 'game_over'


class Juego:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption(TITULO)

        self.pantalla = pygame.display.set_mode((ANCHO, ALTO))
        self.reloj    = pygame.time.Clock()
        self.fuente   = pygame.font.Font(None, 36)

        self.estado = ESTADO_MENU
        self.gen = None
        self.tablero = None
        self.mapeador = None
        self.pacman = None
        self.fantasmas = []

        self.corriendo = True

    def ejecutar(self):
        while self.corriendo:
            self._manejar_eventos()
            self._actualizar()
            self._dibujar()
            self.reloj.tick(FPS)

        pygame.quit()
        sys.exit()

    def _manejar_eventos(self):
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                self.corriendo = False

            if self.estado == ESTADO_JUGANDO and self.pacman:
                self.pacman.manejar_teclado(evento)

            if evento.type == pygame.KEYDOWN:
                if self.estado == ESTADO_MENU:
                    if evento.key == pygame.K_RETURN: self._iniciar_partida()
                    if evento.key == pygame.K_ESCAPE: self.corriendo = False
                elif self.estado == ESTADO_JUGANDO:
                    if evento.key == pygame.K_ESCAPE: self.estado = ESTADO_PAUSA
                    if evento.key == pygame.K_r: self._iniciar_partida()
                elif self.estado == ESTADO_PAUSA:
                    if evento.key == pygame.K_ESCAPE: self.estado = ESTADO_JUGANDO
                    if evento.key == pygame.K_q: self.estado = ESTADO_MENU
                elif self.estado == ESTADO_GAME_OVER:
                    if evento.key == pygame.K_RETURN: self.estado = ESTADO_MENU

    def _actualizar(self):
        if self.estado == ESTADO_JUGANDO and self.pacman and self.tablero:
            # Mover Pac-Man
            self.pacman.mover(self.tablero)
            
            # Mover Fantasmas
            for f in self.fantasmas:
                f.mover(self.tablero, self.pacman)
                
                # Verificar colisión con Pac-Man (por celda lógica)
                if f.fila == self.pacman.fila and f.col == self.pacman.col:
                    self._morir()
            
            if self.tablero.completado:
                print(f"[INFO] Nivel completado!")
                pts = self.pacman.puntaje
                self._iniciar_partida()
                self.pacman.puntaje = pts

    def _morir(self):
        self.pacman.vidas -= 1
        if self.pacman.vidas <= 0:
            self.estado = ESTADO_GAME_OVER
        else:
            self._reposicionar_actores()

    def _reposicionar_actores(self):
        f, c = self.tablero.filas // 2, self.tablero.columnas // 2
        if self.tablero.es_muro(f, c):
            for i in range(self.tablero.filas):
                for j in range(self.tablero.columnas):
                    if self.tablero.es_pasillo(i, j):
                        f, c = i, j
                        break
                else: continue
                break
        
        self.pacman.fila, self.pacman.col = f, c
        self.pacman.px, self.pacman.py = c * TAM_CELDA, f * TAM_CELDA
        self.pacman.target_px, self.pacman.target_py = self.pacman.px, self.pacman.py
        
        for fta in self.fantasmas:
            fta.fila, fta.col = fta.fila_base, fta.col_base
            fta.px, fta.py = fta.col * TAM_CELDA, fta.fila * TAM_CELDA
            fta.target_px, fta.target_py = fta.px, fta.py

    def _dibujar(self):
        self.pantalla.fill(COLOR_FONDO)
        if self.estado == ESTADO_MENU: self._dibujar_menu()
        elif self.estado == ESTADO_JUGANDO: self._dibujar_juego()
        elif self.estado == ESTADO_PAUSA: self._dibujar_pausa()
        elif self.estado == ESTADO_GAME_OVER: self._dibujar_game_over()
        pygame.display.flip()

    def _dibujar_menu(self):
        t = self.fuente.render("PAC-MAN ROGUELIKE", True, (255, 200, 0))
        i = self.fuente.render("ENTER para Iniciar", True, COLOR_TEXTO)
        self.pantalla.blit(t, (ANCHO//2 - t.get_width()//2, 200))
        self.pantalla.blit(i, (ANCHO//2 - i.get_width()//2, 320))

    def _dibujar_juego(self):
        if self.tablero:
            ox = (ANCHO - (self.tablero.columnas * TAM_CELDA)) // 2
            oy = (ALTO - (self.tablero.filas * TAM_CELDA)) // 2 + 20
            self.tablero.dibujar(self.pantalla, ox, oy)
            
            for f in self.fantasmas:
                f.dibujar(self.pantalla, ox, oy)
            
            if self.pacman:
                self.pacman.dibujar(self.pantalla, ox, oy)
            
            txt = f"Vidas: {self.pacman.vidas} | Puntos: {self.pacman.puntaje} | Semilla: {self.gen.semilla}"
            msg = self.fuente.render(txt, True, (200, 200, 200))
            self.pantalla.blit(msg, (ANCHO//2 - msg.get_width()//2, 10))

    def _dibujar_pausa(self):
        msg = self.fuente.render("PAUSA", True, (255, 200, 0))
        self.pantalla.blit(msg, (ANCHO//2 - msg.get_width()//2, ALTO//2))

    def _dibujar_game_over(self):
        msg = self.fuente.render("GAME OVER", True, (255, 50, 50))
        sub = self.fuente.render("ENTER para volver", True, COLOR_TEXTO)
        self.pantalla.blit(msg, (ANCHO//2 - msg.get_width()//2, ALTO//2 - 20))
        self.pantalla.blit(sub, (ANCHO//2 - sub.get_width()//2, ALTO//2 + 20))

    def _iniciar_partida(self):
        import time
        semilla = int(time.time()) % 100_000
        self.gen = GeneradorAleatorio(semilla=semilla, metodo='comb')
        self.mapeador = GeneradorMapa(self.gen)
        self.tablero = self.mapeador.generar(filas=19, columnas=23, cobertura=0.60)
        
        pasillos = []
        for f in range(self.tablero.filas):
            for c in range(self.tablero.columnas):
                if self.tablero.es_pasillo(f, c):
                    pasillos.append((f, c))
        
        pf, pc = pasillos[0]
        self.pacman = PacMan(pf, pc)
        
        self.fantasmas = []
        # Añadir un fantasma perseguidor (Rosa) - Ahora con el generador para torpeza
        ff_p, fc_p = pasillos[-1]
        self.fantasmas.append(FantasmaPerseguidor(ff_p, fc_p, ff_p, fc_p, self.gen))
        
        # Añadir dos fantasmas aleatorios (Rojos)
        for i in range(2):
            ff_a, fc_a = pasillos[-(i+2)]
            self.fantasmas.append(FantasmaAleatorio(ff_a, fc_a, ff_a, fc_a, self.gen))
        
        self.estado = ESTADO_JUGANDO
        print(f"[DEBUG] Nueva partida. 1 Perseguidor, 2 Aleatorios.")


if __name__ == '__main__':
    juego = Juego()
    juego.ejecutar()
