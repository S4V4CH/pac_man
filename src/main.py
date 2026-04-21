import sys
import os
import pygame

# Añadir la raíz del proyecto al path para que encuentre 'lib'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lib import GeneradorAleatorio
from src.mundo.generador_mapa import GeneradorMapa
from src.mundo.tablero import TAM_CELDA

# ─── Constantes ────────────────────────────────────────────────────────────────
ANCHO         = 800
ALTO          = 650  # Aumentado un poco para dar espacio al HUD
FPS           = 60
TITULO        = "Pac-Man Roguelike - Fase 3: Generación Procedural"

COLOR_FONDO   = (10, 10, 30)       # Azul muy oscuro
COLOR_TEXTO   = (255, 255, 255)

# Estados de la máquina de estados
ESTADO_MENU      = 'menu'
ESTADO_JUGANDO   = 'jugando'
ESTADO_PAUSA     = 'pausa'
ESTADO_GAME_OVER = 'game_over'


# ─── Clase principal del juego ─────────────────────────────────────────────────
class Juego:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption(TITULO)

        self.pantalla = pygame.display.set_mode((ANCHO, ALTO))
        self.reloj    = pygame.time.Clock()
        self.fuente   = pygame.font.Font(None, 36)

        # Estado inicial
        self.estado = ESTADO_MENU

        # El generador y el tablero
        self.gen = None
        self.tablero = None
        self.mapeador = None

        self.corriendo = True

    # ── Ciclo principal ──────────────────────────────────────────────────────
    def ejecutar(self):
        while self.corriendo:
            self._manejar_eventos()
            self._actualizar()
            self._dibujar()
            self.reloj.tick(FPS)

        pygame.quit()
        sys.exit()

    # ── 1. Eventos ───────────────────────────────────────────────────────────
    def _manejar_eventos(self):
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                self.corriendo = False

            if evento.type == pygame.KEYDOWN:
                if self.estado == ESTADO_MENU:
                    self._eventos_menu(evento)
                elif self.estado == ESTADO_JUGANDO:
                    self._eventos_jugando(evento)
                elif self.estado == ESTADO_PAUSA:
                    self._eventos_pausa(evento)
                elif self.estado == ESTADO_GAME_OVER:
                    self._eventos_game_over(evento)

    def _eventos_menu(self, evento):
        if evento.key == pygame.K_RETURN:    # Enter → iniciar partida
            self._iniciar_partida()
        if evento.key == pygame.K_ESCAPE:    # Escape → salir
            self.corriendo = False

    def _eventos_jugando(self, evento):
        if evento.key == pygame.K_ESCAPE:    # Escape → pausar
            self.estado = ESTADO_PAUSA
        if evento.key == pygame.K_r:         # R → Regenerar mapa (para pruebas)
            self._iniciar_partida()

    def _eventos_pausa(self, evento):
        if evento.key == pygame.K_ESCAPE:    # Escape → reanudar
            self.estado = ESTADO_JUGANDO
        if evento.key == pygame.K_q:         # Q → menú principal
            self.estado = ESTADO_MENU

    def _eventos_game_over(self, evento):
        if evento.key == pygame.K_RETURN:    # Enter → volver al menú
            self.estado = ESTADO_MENU

    # ── 2. Actualizar lógica ─────────────────────────────────────────────────
    def _actualizar(self):
        if self.estado == ESTADO_JUGANDO:
            pass

    # ── 3. Dibujar ───────────────────────────────────────────────────────────
    def _dibujar(self):
        self.pantalla.fill(COLOR_FONDO)

        if self.estado == ESTADO_MENU:
            self._dibujar_menu()
        elif self.estado == ESTADO_JUGANDO:
            self._dibujar_juego()
        elif self.estado == ESTADO_PAUSA:
            self._dibujar_pausa()
        elif self.estado == ESTADO_GAME_OVER:
            self._dibujar_game_over()

        pygame.display.flip()

    def _dibujar_menu(self):
        titulo = self.fuente.render("PAC-MAN ROGUELIKE", True, (255, 200, 0))
        instru = self.fuente.render("ENTER para Generar Mapa", True, COLOR_TEXTO)
        salida = self.fuente.render("ESC para Salir", True, COLOR_TEXTO)

        self.pantalla.blit(titulo, (ANCHO//2 - titulo.get_width()//2, 200))
        self.pantalla.blit(instru, (ANCHO//2 - instru.get_width()//2, 320))
        self.pantalla.blit(salida, (ANCHO//2 - salida.get_width()//2, 370))

    def _dibujar_juego(self):
        if self.tablero:
            # Centrar el tablero
            offset_x = (ANCHO - (self.tablero.columnas * TAM_CELDA)) // 2
            offset_y = (ALTO - (self.tablero.filas * TAM_CELDA)) // 2 + 20
            self.tablero.dibujar(self.pantalla, offset_x, offset_y)
            
            # Info de la semilla
            msg = self.fuente.render(f"Semilla: {self.gen.semilla} | 'R' para regenerar", True, (200, 200, 200))
            self.pantalla.blit(msg, (ANCHO//2 - msg.get_width()//2, 10))

    def _dibujar_pausa(self):
        msg = self.fuente.render("PAUSA", True, (255, 200, 0))
        self.pantalla.blit(msg, (ANCHO//2 - msg.get_width()//2, ALTO//2))

    def _dibujar_game_over(self):
        msg = self.fuente.render("GAME OVER", True, (255, 50, 50))
        self.pantalla.blit(msg, (ANCHO//2 - msg.get_width()//2, ALTO//2))

    # ── Helpers ──────────────────────────────────────────────────────────────
    def _iniciar_partida(self):
        import time
        semilla = int(time.time()) % 100_000
        self.gen = GeneradorAleatorio(semilla=semilla, metodo='comb')
        
        # Crear el mapa
        self.mapeador = GeneradorMapa(self.gen)
        # Aumentamos cobertura a 0.60 para que esté más "destapado"
        self.tablero = self.mapeador.generar(filas=19, columnas=23, cobertura=0.60)
        
        self.estado = ESTADO_JUGANDO
        print(f"[DEBUG] Mapa generado con semilla: {semilla}")


if __name__ == '__main__':
    juego = Juego()
    juego.ejecutar()
