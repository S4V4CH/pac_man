# src/sistemas/tienda.py
"""
Sistema de tienda permanente para Pac-Man Roguelike.
Las monedas y mejoras compradas son por nombre de usuario; persisten en datos/tienda.json.
"""

from __future__ import annotations
import json
import os

RUTA_TIENDA = os.path.join(
    os.path.dirname(__file__), '..', '..', 'datos', 'tienda.json'
)

# ─────────────────────────────────────────────────────────────
# Catálogo de la tienda (mejoras permanentes entre runs)
# ─────────────────────────────────────────────────────────────
TIENDA_ITEMS: list[dict] = [
    {
        'id': 'botas_permanentes',
        'nombre': 'Botas Permanentes',
        'desc': 'Velocidad base aumentada de forma\npermanente en todas las runs.',
        'icono': 'boots',
        'color': (50, 255, 120),
        'color_borde': (20, 180, 70),
        'max_nivel': 5,
        'costos': [500, 1_000, 2_000, 3_500, 5_500],
        'bonus_velocidad_por_nivel': 0.05,  # +5% por nivel
        'niveles_desc': [
            '+5% velocidad permanente',
            '+10% velocidad permanente',
            '+15% velocidad permanente',
            '+20% velocidad permanente',
            '+25% velocidad permanente — MÁXIMO',
        ],
    },
]


def get_item_tienda(item_id: str) -> dict | None:
    for item in TIENDA_ITEMS:
        if item['id'] == item_id:
            return item
    return None


# ─────────────────────────────────────────────────────────────
class SistemaTienda:
    """
    Gestiona la tienda permanente con persistencia entre sesiones.
    Cada usuario (nombre de jugador) tiene sus propias monedas y niveles de mejora.
    """

    def __init__(self) -> None:
        self._usuarios: dict[str, dict] = {}
        self._usuario_actual: str = 'Jugador'
        self.cargar()

    @staticmethod
    def _normalizar_nombre(nombre: str) -> str:
        n = (nombre or '').strip()
        return n[:32] if n else 'Jugador'

    def _entrada_vacia(self) -> dict:
        return {'monedas': 0, 'mejoras': {}}

    def _asegurar_usuario(self, nombre: str) -> None:
        if nombre not in self._usuarios:
            self._usuarios[nombre] = self._entrada_vacia()

    def set_usuario(self, nombre: str) -> None:
        """Define qué perfil de tienda se lee/escribe (nombre del jugador actual)."""
        self._usuario_actual = self._normalizar_nombre(nombre)
        self._asegurar_usuario(self._usuario_actual)

    def cargar(self) -> None:
        try:
            with open(RUTA_TIENDA, 'r', encoding='utf-8') as f:
                cargado = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError, ValueError):
            cargado = {}

        self._usuarios = {}

        if isinstance(cargado, dict) and 'usuarios' in cargado and isinstance(cargado['usuarios'], dict):
            for nombre, datos in cargado['usuarios'].items():
                n = self._normalizar_nombre(str(nombre))
                if isinstance(datos, dict):
                    self._usuarios[n] = {
                        'monedas': int(datos.get('monedas', 0)),
                        'mejoras': dict(datos.get('mejoras', {})),
                    }
        elif isinstance(cargado, dict) and ('monedas' in cargado or 'mejoras' in cargado):
            # Formato antiguo global → se asigna al usuario «Jugador»
            self._usuarios['Jugador'] = {
                'monedas': int(cargado.get('monedas', 0)),
                'mejoras': dict(cargado.get('mejoras', {})),
            }

        self._asegurar_usuario(self._usuario_actual)

    def guardar(self) -> None:
        os.makedirs(os.path.dirname(RUTA_TIENDA), exist_ok=True)
        with open(RUTA_TIENDA, 'w', encoding='utf-8') as f:
            json.dump({'usuarios': self._usuarios}, f, indent=2, ensure_ascii=False)

    def _datos_actuales(self) -> dict:
        self._asegurar_usuario(self._usuario_actual)
        return self._usuarios[self._usuario_actual]

    # ── Propiedades ───────────────────────────────────────────

    @property
    def monedas(self) -> int:
        return int(self._datos_actuales().get('monedas', 0))

    def nivel_de(self, item_id: str) -> int:
        return int(self._datos_actuales().get('mejoras', {}).get(item_id, 0))

    # ── Operaciones ───────────────────────────────────────────

    def agregar_monedas(self, cantidad: int) -> None:
        d = self._datos_actuales()
        d['monedas'] = int(d.get('monedas', 0)) + max(0, cantidad)
        self.guardar()

    def puede_comprar(self, item_id: str) -> bool:
        item = get_item_tienda(item_id)
        if item is None:
            return False
        nivel_actual = self.nivel_de(item_id)
        if nivel_actual >= item['max_nivel']:
            return False
        costo = item['costos'][nivel_actual]
        return self.monedas >= costo

    def comprar(self, item_id: str) -> bool:
        """Intenta comprar el siguiente nivel. Retorna True si tuvo éxito."""
        item = get_item_tienda(item_id)
        if item is None:
            return False
        nivel_actual = self.nivel_de(item_id)
        if nivel_actual >= item['max_nivel']:
            return False
        costo = item['costos'][nivel_actual]
        if self.monedas < costo:
            return False
        d = self._datos_actuales()
        d['monedas'] = int(d.get('monedas', 0)) - costo
        if 'mejoras' not in d:
            d['mejoras'] = {}
        d['mejoras'][item_id] = nivel_actual + 1
        self.guardar()
        return True

    def costo_siguiente(self, item_id: str) -> int | None:
        """Retorna el costo del siguiente nivel o None si está al máximo."""
        item = get_item_tienda(item_id)
        if item is None:
            return None
        nivel_actual = self.nivel_de(item_id)
        if nivel_actual >= item['max_nivel']:
            return None
        return item['costos'][nivel_actual]

    def reiniciar_usuario(self, nombre: str) -> None:
        """Pone a 0 monedas y mejoras de tienda del usuario indicado."""
        n = self._normalizar_nombre(nombre)
        self._usuarios[n] = self._entrada_vacia()
        self.guardar()

    # ── Bonus para el juego ───────────────────────────────────

    def get_bonus_velocidad(self) -> float:
        """Retorna el bonus permanente de velocidad (0.0 = ninguno)."""
        nivel = self.nivel_de('botas_permanentes')
        item = get_item_tienda('botas_permanentes')
        if item is None:
            return 0.0
        return nivel * item['bonus_velocidad_por_nivel']
