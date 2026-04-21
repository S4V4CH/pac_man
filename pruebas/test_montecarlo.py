# pruebas/test_montecarlo.py
"""
Prueba de Monte Carlo con la librería PRNG.
Genera N puntos (x, y) en [0,1)² y verifica que se distribuyan de forma compatible
con uniformidad (estimación de π y reparto por cuadrantes).

Ejecución desde la raíz del proyecto:
    python pruebas/test_montecarlo.py
"""

from __future__ import annotations

import math
import os
import sys

# Raíz del proyecto (padre de pruebas/)
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from lib import GeneradorAleatorio  # noqa: E402


def test_montecarlo(semilla: int = 42, n: int = 10_000, metodo: str = 'comb') -> None:
    gen = GeneradorAleatorio(semilla=semilla, metodo=metodo)
    gen.activar_historial()

    puntos: list[tuple[float, float]] = []
    for _ in range(n):
        x = gen.decimal(0, 1)
        y = gen.decimal(0, 1)
        puntos.append((x, y))

    # Test: puntos dentro del círculo unidad → proporción ≈ π/4
    dentro = sum(1 for x, y in puntos if x**2 + y**2 <= 1)
    pi_aprox = 4 * dentro / n

    print(f"Puntos generados : {n}")
    print(f"Puntos en circulo: {dentro}")
    # Etiquetas ASCII para compatibilidad con consolas Windows (cp1252)
    print(f"pi aproximado     : {pi_aprox:.5f}")
    print(f"pi (math.pi)      : {math.pi:.5f}")
    print(f"Error relativo    : {abs(pi_aprox - math.pi) / math.pi * 100:.3f}%")

    # Uniformidad por cuadrantes (esperado ~25% cada uno)
    cuadrantes = [0, 0, 0, 0]
    for x, y in puntos:
        q = (1 if x >= 0.5 else 0) + (2 if y >= 0.5 else 0)
        cuadrantes[q] += 1

    print("\nDistribucion por cuadrantes (esperado ~25% cada uno):")
    for i, c in enumerate(cuadrantes):
        print(f"  Cuadrante {i + 1}: {c} puntos ({c / n * 100:.1f}%)")

    stats = gen.estadisticas()
    if stats:
        print("\nEstadisticas del historial (valores u en [0,1) del PRNG):")
        print(f"  n        : {stats.get('n', 'N/A')}")
        print(f"  Media    : {stats['media']:.6f}  (esperada U(0,1): {stats['media_esperada']})")
        print(f"  Varianza : {stats['varianza']:.6f}  (esperada: {stats['varianza_esperada']})")


if __name__ == '__main__':
    print("=" * 50)
    print("TEST MONTE CARLO - Libreria PRNG")
    print("=" * 50)
    for metodo in ('mid', 'lcg', 'comb'):
        print(f"\n[{metodo.upper()}]")
        test_montecarlo(semilla=42, n=10_000, metodo=metodo)
