# src/ui/audio.py
"""Audio con volumen separado música/SFX, loops de menú y fantasmas, intro bloqueante."""

from __future__ import annotations

import io
import math
import os
import struct
import wave

import pygame

_BASE = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..'))

CANAL_INTRO = 0
CANAL_FANTASMA_RETURN = 5
CANAL_LOOP_FANTASMA = 6


def _ruta_assets(*partes: str) -> str:
    return os.path.join(_BASE, *partes)


def _generar_tono_wav(freq: float, dur_ms: int, volumen: float = 0.12) -> pygame.mixer.Sound:
    sr = 44100
    n = max(1, int(sr * dur_ms / 1000))
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        frames = []
        for i in range(n):
            t = i / sr
            env = 1.0 - (i / max(1, n - 1)) ** 0.5
            s = int(32767 * volumen * env * math.sin(2 * math.pi * freq * t))
            frames.append(struct.pack('<h', max(-32767, min(32767, s))))
        w.writeframes(b''.join(frames))
    buf.seek(0)
    return pygame.mixer.Sound(file=buf)


def _cargar_sound(ruta: str, fallback: tuple[float, int]) -> pygame.mixer.Sound:
    if os.path.isfile(ruta):
        try:
            return pygame.mixer.Sound(ruta)
        except pygame.error:
            pass
    return _generar_tono_wav(float(fallback[0]), fallback[1])


class GestorAudio:
    def __init__(self) -> None:
        try:
            pygame.mixer.set_num_channels(16)
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        except pygame.error:
            pass

        self.volumen_musica: float = 0.65
        self.volumen_sfx: float = 0.75

        self._sonidos: dict[str, pygame.mixer.Sound] = {}
        self._musica_pausada = False
        self._menu_activo = False
        self._loop_fantasma_activo = False

        self._cargar_sonidos()

    def _cargar_sonidos(self) -> None:
        defs = [
            ('comer', 'comer.wav', (880, 35)),
            ('super_comer', 'super_comer.wav', (420, 120)),
            ('comer_fruta', 'comer_fruta.wav', (520, 100)),
            ('morir', 'morir.wav', (120, 400)),
            ('subir_nivel', 'subir_nivel.wav', (660, 180)),
            ('comer_fantasma', 'comer_fantasma.wav', (520, 90)),
            ('fantasma_return', 'Fantasma_return.wav', (300, 200)),
            ('inicio', 'inicio.wav', (440, 2000)),
            ('game_over', 'game over.wav', (150, 2500)),
        ]
        for clave, archivo, fb in defs:
            self._sonidos[clave] = _cargar_sound(_ruta_assets('assets', 'sonidos', archivo), fb)

        self._snd_menu = _cargar_sound(_ruta_assets('assets', 'sonidos', 'menu.wav'), (220, 800))
        self._snd_fantasma_loop = _cargar_sound(_ruta_assets('assets', 'sonidos', 'fantasma.wav'), (180, 400))

    def set_volumen_musica(self, v: float) -> None:
        self.volumen_musica = max(0.0, min(1.0, v))
        try:
            pygame.mixer.music.set_volume(self.volumen_musica)
            ch = pygame.mixer.Channel(CANAL_LOOP_FANTASMA)
            if ch.get_busy():
                ch.set_volume(self.volumen_musica)
        except pygame.error:
            pass

    def set_volumen_sfx(self, v: float) -> None:
        self.volumen_sfx = max(0.0, min(1.0, v))

    def _vol_sfx(self) -> float:
        return self.volumen_sfx

    def reproducir(self, nombre: str) -> None:
        if nombre not in self._sonidos:
            return
        try:
            s = self._sonidos[nombre]
            s.set_volume(self._vol_sfx())
            c = pygame.mixer.find_channel(True)
            if c:
                c.play(s)
        except pygame.error:
            pass

    def iniciar_menu_loop(self) -> None:
        self.detener_loop_fantasmas()
        ruta = _ruta_assets('assets', 'sonidos', 'menu.wav')
        if not os.path.isfile(ruta):
            return
        try:
            pygame.mixer.music.load(ruta)
            pygame.mixer.music.set_volume(self.volumen_musica)
            pygame.mixer.music.play(-1)
            self._menu_activo = True
        except pygame.error:
            pass

    def detener_menu_loop(self) -> None:
        try:
            pygame.mixer.music.stop()
        except pygame.error:
            pass
        self._menu_activo = False

    def iniciar_musica_fondo(self) -> None:
        for nombre in ('musica_fondo.ogg', 'musica_fondo.wav'):
            ruta = _ruta_assets('assets', 'sonidos', nombre)
            if os.path.isfile(ruta):
                try:
                    pygame.mixer.music.load(ruta)
                    pygame.mixer.music.set_volume(self.volumen_musica)
                    pygame.mixer.music.play(-1)
                    return
                except pygame.error:
                    continue

    def detener_musica(self) -> None:
        try:
            pygame.mixer.music.stop()
        except pygame.error:
            pass

    def reproducir_inicio_y_preparar_canal(self) -> None:
        """Inicia el jingle de inicio en un canal fijo (esperar con intro_terminada)."""
        self.detener_menu_loop()
        try:
            s = self._sonidos.get('inicio')
            if s:
                s.set_volume(self._vol_sfx())
                ch = pygame.mixer.Channel(CANAL_INTRO)
                ch.play(s)
        except pygame.error:
            pass

    def intro_terminada(self) -> bool:
        try:
            return not pygame.mixer.Channel(CANAL_INTRO).get_busy()
        except pygame.error:
            return True

    def iniciar_loop_fantasmas(self) -> None:
        try:
            ch = pygame.mixer.Channel(CANAL_LOOP_FANTASMA)
            self._snd_fantasma_loop.set_volume(self.volumen_musica * 0.85)
            ch.play(self._snd_fantasma_loop, loops=-1)
            self._loop_fantasma_activo = True
        except pygame.error:
            pass

    def detener_loop_fantasmas(self) -> None:
        try:
            pygame.mixer.Channel(CANAL_LOOP_FANTASMA).stop()
        except pygame.error:
            pass
        self._loop_fantasma_activo = False

    def reproducir_fantasma_return(self) -> None:
        """Un solo canal: al repetirse corta el anterior (varios fantasmas comidos)."""
        s = self._sonidos.get('fantasma_return')
        if not s:
            return
        try:
            s.set_volume(self._vol_sfx())
            ch = pygame.mixer.Channel(CANAL_FANTASMA_RETURN)
            ch.play(s)
        except pygame.error:
            pass

    def detener_fantasma_return(self) -> None:
        try:
            pygame.mixer.Channel(CANAL_FANTASMA_RETURN).stop()
        except pygame.error:
            pass

    def alternar_musica(self) -> None:
        try:
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.pause()
                self._musica_pausada = True
            else:
                if self._musica_pausada:
                    pygame.mixer.music.unpause()
                else:
                    self.iniciar_musica_fondo()
                self._musica_pausada = False
        except pygame.error:
            pass
