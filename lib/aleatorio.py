"""
Librería PRNG para Pac-Man Roguelike
====================================================
Implementa tres algoritmos de generación de números pseudoaleatorios:
  1. Método de los Cuadrados Medios (Midsquare) 
  2. Generador Congruencial Lineal (LCG)    
  3. Generador Combinado (Wichmann-Hill style) 


Uso básico:
    gen = GeneradorAleatorio(semilla=42, metodo='lcg')
    direccion  = gen.entero(0, 3)       # 0=N 1=S 2=E 3=O
    velocidad  = gen.decimal(0.5, 2.0)  # multiplicador de velocidad
    es_pasillo = gen.decimal(0, 1) > 0.35

Autor: [Tu nombre]
Materia: Ingeniería de Sistemas — Simulación
"""

from __future__ import annotations


# ---------------------------------------------------------------------------
# Parámetros LCG por defecto (ANSI C / glibc — cumplen Teorema Hull-Dobell)
# Fuente: Downham & Roberts (1967), tabla de parámetros comunes
# ---------------------------------------------------------------------------
_LCG_A = 1_103_515_245   # multiplicador
_LCG_C = 12_345           # incremento
_LCG_M = 2 ** 31          # módulo (2_147_483_648)


class GeneradorAleatorio:
    """
    Generador de números pseudoaleatorios con tres métodos intercambiables.

    Parámetros
    ----------
    semilla : int
        Valor inicial X_0.  Determina completamente la secuencia generada.
        Dos instancias con la misma semilla producen idéntica secuencia,
        lo que garantiza mapas reproducibles (requisito Roguelike de Seeds).
    metodo : str
        Algoritmo activo: 'lcg' | 'mid' | 'comb'
        - 'lcg'  → Congruencial Lineal (recomendado para tiempo real)
        - 'mid'  → Cuadrados Medios   (uso estético / histórico)
        - 'comb' → Combinado          (recomendado para generación de mapas)
    """

    def __init__(self, semilla: int, metodo: str = 'lcg') -> None:
        if metodo not in ('lcg', 'mid', 'comb'):
            raise ValueError("metodo debe ser 'lcg', 'mid' o 'comb'")

        self.semilla: int = semilla
        self.metodo: str = metodo

        # Estado interno del LCG
        self._xn_lcg: int = semilla

        # Estado interno del Midsquare (necesita semilla de 4 dígitos)
        seed_mid = semilla % 10_000 or 1234   # garantiza 4 dígitos
        self._xn_mid: int = seed_mid

    # ------------------------------------------------------------------
    # Método 1 — Cuadrados Medios (Midsquare)
    # ------------------------------------------------------------------
    def midsquare(self, k: int = 4) -> float:
        """
        Genera un número pseudoaleatorio en [0, 1) usando el método de
        los Cuadrados Medios propuesto por Von Neumann y Metropolis.

        Algoritmo:
            X_{n+1} = k dígitos centrales de X_n^2
            u_n     = X_n / 10^k

        Parámetros
        ----------
        k : int
            Cantidad de dígitos a extraer (default 4).
            Debe coincidir con la cantidad de dígitos de la semilla.

        Advertencias
        ------------
        - Propenso a degenerar a 0 si X_n llega a un valor cuyo cuadrado
          tenga ceros centrales (ej. semilla 1009 → colapso rápido).
        - Ciclos cortos para ciertas semillas.
        - Recomendado solo para efectos visuales menores en el juego.

        Retorna
        -------
        float en [0, 1)
        """
        cuadrado = str(self._xn_mid ** 2).zfill(k * 2)
        mitad = len(cuadrado) // 2
        inicio = mitad - k // 2
        self._xn_mid = int(cuadrado[inicio: inicio + k])

        u = self._xn_mid / (10 ** k)
        return u

    # ------------------------------------------------------------------
    # Método 2 — Generador Congruencial Lineal (LCG)
    # ------------------------------------------------------------------
    def congruencial(
        self,
        a: int = _LCG_A,
        c: int = _LCG_C,
        m: int = _LCG_M,
    ) -> float:
        """
        Genera un número pseudoaleatorio en [0, 1) usando el Generador
        Congruencial Lineal Mixto (GLCM).

        Fórmula de recurrencia:
            X_{n+1} = (a * X_n + c) mod m
            u_n     = X_n / m

        Parámetros por defecto (ANSI C / glibc):
            a = 1_103_515_245   (multiplicador)
            c = 12_345          (incremento)
            m = 2^31            (módulo)

        Estos parámetros cumplen el Teorema Hull-Dobell (1962):
            1. mcd(c, m) = 1            → c=12345 y m=2^31 son coprimos
            2. a ≡ 1 (mod p) ∀ primo p | m → a-1 es divisible por 2
            3. Si 4 | m → 4 | (a-1)    → (1103515245-1) % 4 == 0  ✓
        Por tanto tiene PERIODO COMPLETO = m = 2_147_483_648.

        Parámetros
        ----------
        a : int  Multiplicador
        c : int  Incremento
        m : int  Módulo

        Retorna
        -------
        float en [0, 1)
        """
        self._xn_lcg = (a * self._xn_lcg + c) % m
        u = self._xn_lcg / m
        return u

    # ------------------------------------------------------------------
    # Método 3 — Generador Combinado (Wichmann-Hill style)
    # ------------------------------------------------------------------
    def combinado(self) -> float:
        """
        Genera un número pseudoaleatorio combinando LCG y Midsquare.

        Fórmula:
            u_comb = frac(u_lcg + u_mid)   ∈ [0, 1)

        Fundamento matemático:
            Si U1 ~ U(0,1) y U2 ~ U(0,1) son independientes, entonces
            la parte fraccional de U1+U2 también sigue U(0,1).
            El período resultante es ≈ mcm(período_LCG, período_Mid),
            lo que reduce la correlación serial entre valores consecutivos.

        Aplicación en el juego:
            Recomendado para generación procedural de mapas donde la
            predictibilidad arruinaría la experiencia Roguelike.

        Retorna
        -------
        float en [0, 1)
        """
        u1 = self.congruencial()
        u2 = self.midsquare()
        return (u1 + u2) % 1.0

    # ------------------------------------------------------------------
    # Funciones de utilidad (interfaz principal del juego)
    # ------------------------------------------------------------------
    def _siguiente(self) -> float:
        """Delega al método activo."""
        return {
            'lcg':  self.congruencial,
            'mid':  self.midsquare,
            'comb': self.combinado,
        }[self.metodo]()

    def entero(self, min_val: int, max_val: int) -> int:
        """
        Retorna un entero uniforme en [min_val, max_val].

        Uso en el juego:
            gen.entero(0, 3)  → dirección del fantasma (N/S/E/O)
            gen.entero(1, 3)  → power-up aleatorio entre 3 opciones
        """
        if min_val > max_val:
            raise ValueError("min_val debe ser <= max_val")
        rango = max_val - min_val + 1
        return min_val + int(self._siguiente() * rango)

    def decimal(self, min_val: float, max_val: float) -> float:
        """
        Retorna un float uniforme en [min_val, max_val].

        Uso en el juego:
            gen.decimal(0.5, 2.0)  → multiplicador de velocidad del fantasma
            gen.decimal(0, 1)      → comparar contra probabilidad de loot
        """
        if min_val > max_val:
            raise ValueError("min_val debe ser <= max_val")
        return min_val + self._siguiente() * (max_val - min_val)

    def booleano(self, probabilidad: float = 0.5) -> bool:
        """
        Retorna True con la probabilidad dada.

        Uso en el juego:
            gen.booleano(0.02)   → celda tiene Super Pastilla (2%)
        """
        return self._siguiente() < probabilidad

    def elegir(self, opciones: list) -> object:
        """
        Elige un elemento aleatorio de una lista.

        Uso en el juego:
            gen.elegir(['botas', 'radar', 'fuego'])  → power-up del nivel
        """
        if not opciones:
            raise ValueError("La lista de opciones no puede estar vacía")
        return opciones[self.entero(0, len(opciones) - 1)]

    def mezclar(self, lista: list) -> list:
        """
        Retorna una copia mezclada de la lista (Fisher-Yates con PRNG propio).

        Garantiza que el orden de mezcla depende de la semilla,
        haciendo los niveles completamente reproducibles.
        """
        resultado = list(lista)
        for i in range(len(resultado) - 1, 0, -1):
            j = self.entero(0, i)
            resultado[i], resultado[j] = resultado[j], resultado[i]
        return resultado

    def restablecer(self) -> None:
        """
        Reinicia el generador a su semilla original.
        Útil para regenerar el mismo mapa cambiando solo los parámetros.
        """
        self.__init__(self.semilla, self.metodo)

    def __repr__(self) -> str:
        return (
            f"GeneradorAleatorio("
            f"semilla={self.semilla}, "
            f"metodo='{self.metodo}', "
            f"xn_lcg={self._xn_lcg}, "
            f"xn_mid={self._xn_mid})"
        )