import sys
import pygame
from lib import GeneradorAleatorio

# ─── Constantes ────────────────────────────────────────────────────────────────
ANCHO         = 800
ALTO          = 600
FPS           = 60
TITULO        = "Pac-Man Roguelike"

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

        # El generador se inicializa sin semilla fija
        # (se asignará cuando el jugador empiece una partida)
        self.gen = None

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

            # Cerrar ventana con la X
            if evento.type == pygame.QUIT:
                self.corriendo = False

            # Teclas presionadas
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
            pass   # Aquí irá la lógica del juego (Fases 3-5)

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

        pygame.display.flip()   # Mostrar el frame renderizado

    def _dibujar_menu(self):
        titulo = self.fuente.render("PAC-MAN ROGUELIKE", True, (255, 200, 0))
        inicio = self.fuente.render("ENTER  →  Jugar", True, COLOR_TEXTO)
        salida = self.fuente.render("ESC    →  Salir", True, COLOR_TEXTO)

        self.pantalla.blit(titulo, (ANCHO//2 - titulo.get_width()//2, 200))
        self.pantalla.blit(inicio, (ANCHO//2 - inicio.get_width()//2, 320))
        self.pantalla.blit(salida, (ANCHO//2 - salida.get_width()//2, 370))

    def _dibujar_juego(self):
        # Placeholder: se reemplaza en Fase 3
        msg = self.fuente.render("JUGANDO... (Fase 3 pendiente)", True, COLOR_TEXTO)
        self.pantalla.blit(msg, (ANCHO//2 - msg.get_width()//2, ALTO//2))

    def _dibujar_pausa(self):
        msg   = self.fuente.render("PAUSA", True, (255, 200, 0))
        reanu = self.fuente.render("ESC → Reanudar  |  Q → Menú", True, COLOR_TEXTO)
        self.pantalla.blit(msg,   (ANCHO//2 - msg.get_width()//2,   ALTO//2 - 40))
        self.pantalla.blit(reanu, (ANCHO//2 - reanu.get_width()//2, ALTO//2 + 10))

    def _dibujar_game_over(self):
        msg = self.fuente.render("GAME OVER", True, (255, 50, 50))
        sub = self.fuente.render("ENTER → Menú Principal", True, COLOR_TEXTO)
        self.pantalla.blit(msg, (ANCHO//2 - msg.get_width()//2, ALTO//2 - 40))
        self.pantalla.blit(sub, (ANCHO//2 - sub.get_width()//2, ALTO//2 + 20))

    # ── Helpers ──────────────────────────────────────────────────────────────
    def _iniciar_partida(self):
        """Crea un nuevo generador con semilla basada en el tiempo actual."""
        import time
        semilla = int(time.time()) % 100_000   # Semilla diferente cada partida
        self.gen = GeneradorAleatorio(semilla=semilla, metodo='comb')
        self.estado = ESTADO_JUGANDO
        print(f"[DEBUG] Nueva partida. Semilla: {semilla}")


# ─── Punto de entrada ──────────────────────────────────────────────────────────
if __name__ == '__main__':
    juego = Juego()
    juego.ejecutar()
