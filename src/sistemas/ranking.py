# src/sistemas/ranking.py

from __future__ import annotations

import json
import os

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RUTA_RANKING = os.path.normpath(os.path.join(_BASE_DIR, '..', '..', 'datos', 'ranking.json'))
MAX_ENTRADAS = 10


class SistemaRanking:
    def __init__(self) -> None:
        self.entradas: list[dict] = self._cargar()

    def recargar(self) -> None:
        """Vuelve a leer el JSON (útil al abrir el menú de ranking)."""
        self.entradas = self._cargar()

    def _cargar(self) -> list:
        if not os.path.exists(RUTA_RANKING):
            return []
        try:
            with open(RUTA_RANKING, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return []

    def guardar(self, nombre: str, puntaje: int, semilla: int) -> None:
        nueva_entrada = {
            'nombre': nombre,
            'puntaje': puntaje,
            'semilla': semilla,
        }
        self.entradas.append(nueva_entrada)
        self.entradas.sort(key=lambda e: e['puntaje'], reverse=True)
        self.entradas = self.entradas[:MAX_ENTRADAS]

        os.makedirs(os.path.dirname(RUTA_RANKING), exist_ok=True)
        with open(RUTA_RANKING, 'w', encoding='utf-8') as f:
            json.dump(self.entradas, f, indent=2, ensure_ascii=False)

    def es_record(self, puntaje: int) -> bool:
        if len(self.entradas) < MAX_ENTRADAS:
            return True
        return puntaje > self.entradas[-1]['puntaje']
