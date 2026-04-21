# src/sistemas/loot.py

from __future__ import annotations

from lib import GeneradorAleatorio

ITEMS = {
    'legendario': {
        'prob': 0.05,
        'puntos': 500,
        'nombre': 'Imán de Puntos',
        'desc': 'Una lluvia de puntos bendecida por el PRNG.',
    },
    'raro': {
        'prob': 0.15,
        'puntos': 200,
        'nombre': 'Radar Fantasmal',
        'desc': 'Sientes el mapa un poco más predecible.',
    },
    'comun': {
        'prob': 0.30,
        'puntos': 50,
        'nombre': 'Botas de Hermes',
        'desc': 'Pequeño empujón a tu marcador.',
    },
    'vida': {
        'prob': 0.20,
        'puntos': 0,
        'nombre': 'Vida Extra',
        'desc': 'Un crédito más en la recreativa.',
    },
}


class SistemaLoot:
    def __init__(self, gen: GeneradorAleatorio):
        self.gen = gen

    def tirar_loot(self) -> dict | None:
        """
        Determina qué item cae al terminar un nivel.
        Las probabilidades se aplican en orden: legendario > raro > común > vida.
        """
        if self.gen.booleano(ITEMS['legendario']['prob']):
            return {**ITEMS['legendario'], 'id': 'legendario'}
        if self.gen.booleano(ITEMS['raro']['prob']):
            return {**ITEMS['raro'], 'id': 'raro'}
        if self.gen.booleano(ITEMS['vida']['prob']):
            return {**ITEMS['vida'], 'id': 'vida'}
        if self.gen.booleano(ITEMS['comun']['prob']):
            return {**ITEMS['comun'], 'id': 'comun'}
        return None
