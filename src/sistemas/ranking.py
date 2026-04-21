# src/sistemas/ranking.py

from __future__ import annotations

import json
import os

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RUTA_RANKING = os.path.normpath(os.path.join(_BASE_DIR, '..', '..', 'datos', 'ranking.json'))


class SistemaRanking:
    """
    Un único mejor puntaje por nombre de jugador.
    El JSON guarda solo esos máximos (no un historial de partidas).
    """

    def __init__(self) -> None:
        self.jugadores: dict[str, dict] = {}
        self._cargar()
        self._migrar_json_si_lista_antigua()

    def _migrar_json_si_lista_antigua(self) -> None:
        """Si existía ranking.json como lista, reescribe al formato { jugadores: {...} }."""
        if not os.path.exists(RUTA_RANKING):
            return
        try:
            with open(RUTA_RANKING, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            return
        if isinstance(data, list):
            self._guardar()

    def recargar(self) -> None:
        self.jugadores = {}
        self._cargar()

    def _cargar(self) -> None:
        if not os.path.exists(RUTA_RANKING):
            return
        try:
            with open(RUTA_RANKING, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            return

        if isinstance(data, list):
            # Formato antiguo: lista de partidas → un mejor puntaje por nombre
            for e in data:
                if not isinstance(e, dict):
                    continue
                self._fusionar_entrada(
                    str(e.get('nombre', 'Jugador'))[:32],
                    int(e.get('puntaje', 0)),
                    int(e.get('semilla', 0)),
                )
        elif isinstance(data, dict) and 'jugadores' in data:
            j = data['jugadores']
            if isinstance(j, dict):
                for nombre, v in j.items():
                    if isinstance(v, dict) and 'puntaje' in v:
                        self.jugadores[str(nombre)[:32]] = {
                            'puntaje': int(v['puntaje']),
                            'semilla': int(v.get('semilla', 0)),
                        }

    def _fusionar_entrada(self, nombre: str, puntaje: int, semilla: int) -> None:
        nombre = nombre.strip() or 'Jugador'
        prev = self.jugadores.get(nombre, {}).get('puntaje', -1)
        if puntaje > prev:
            self.jugadores[nombre] = {'puntaje': puntaje, 'semilla': semilla}

    def _guardar(self) -> None:
        os.makedirs(os.path.dirname(RUTA_RANKING), exist_ok=True)
        with open(RUTA_RANKING, 'w', encoding='utf-8') as f:
            json.dump({'jugadores': self.jugadores}, f, indent=2, ensure_ascii=False)

    @staticmethod
    def _normalizar_nombre(nombre: str) -> str:
        n = nombre.strip()
        return n[:32] if n else 'Jugador'

    def obtener_highscore(self, nombre: str) -> int:
        n = self._normalizar_nombre(nombre)
        return int(self.jugadores.get(n, {}).get('puntaje', 0))

    def actualizar_si_mejor(self, nombre: str, puntaje: int, semilla: int) -> bool:
        """
        Si puntaje supera el mejor guardado de ese jugador, actualiza y guarda.
        Retorna True si hubo actualización.
        """
        n = self._normalizar_nombre(nombre)
        prev = self.jugadores.get(n, {}).get('puntaje', -1)
        if puntaje > prev:
            self.jugadores[n] = {'puntaje': puntaje, 'semilla': semilla}
            self._guardar()
            return True
        return False

    @property
    def entradas(self) -> list[dict]:
        """Lista ordenada para el menú (mejor puntaje primero)."""
        return sorted(
            ({'nombre': k, **v} for k, v in self.jugadores.items()),
            key=lambda e: e['puntaje'],
            reverse=True,
        )

    def posicion_global(self, puntaje_partida: int) -> int:
        """
        Puesto de esta puntuación frente al mejor de cada jugador registrado
        (1 = habrías el #1 si solo importara esta marca; empates cuentan igual).
        """
        if not self.jugadores:
            return 1
        scores = sorted((j['puntaje'] for j in self.jugadores.values()), reverse=True)
        return 1 + sum(1 for s in scores if s > puntaje_partida)

    def total_jugadores_en_tabla(self) -> int:
        return len(self.jugadores)

    def eliminar_jugador(self, nombre: str) -> None:
        """Quita el récord de ranking de un usuario (no afecta a otros)."""
        n = self._normalizar_nombre(nombre)
        self.jugadores.pop(n, None)
        self._guardar()

    def borrar_todo(self) -> None:
        self.jugadores = {}
        self._guardar()
