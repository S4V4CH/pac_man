

---

## **1\. El Ciclo de Juego (Gameplay Loop) Roguelike**

A diferencia del Pac-Man tradicional donde solo sobrevives, en un Roguelike el objetivo es **gestionar recursos** para llegar lo más lejos posible.

| Característica | Implementación Roguelike |
| :---- | :---- |
| **Generación Procedural** | El "Generador de tableros" no debe crear laberintos aleatorios sin sentido, sino usar **algoritmos de excavación** (como *Cellular Automata* o *Binary Space Partitioning*) para asegurar que siempre haya un camino y zonas de "tesoro". |
| **Muerte Permanente (Permadeath)** | Cuando pierdes tus créditos/vidas, el progreso de la "run" se borra, pero podrías mantener una "Meta Progresión" (mejoras permanentes compradas con el puntaje acumulado). |
| **Semillas (Seeds)** | Permite que los jugadores compartan el código de un tablero específico para competir en el ranking bajo las mismas condiciones aleatorias. |

---

## **2\. Sistemas de Progresión: "Power-ups" y Sinergias**

* **Árbol de Habilidades (Buffs):** Al limpiar un nivel, el jugador elige una mejora entre tres opciones aleatorias:  
  * *Botas de Hermes:* \+10% de velocidad permanente.  
  * *Radar Fantasmal:* Ves la trayectoria de los enemigos por 2 segundos.  
  * *Aliento de Fuego:* Pac-Man puede disparar un proyectil de corto alcance limitado.  
* **Sinergias:** Si tienes el objeto "Imán de Puntos" y "Doble Puntaje", desbloqueas una habilidad especial: "Fiebre de Oro".

---

## **3\. Evolución de los Enemigos (IA Avanzada)**

Para que el juego sea más "completo", los enemigos no pueden simplemente moverse al azar. Implementa **comportamientos diferenciados**:

* **El Acechador (Stalker):** Utiliza el algoritmo *A (A-Star)*\* para encontrar siempre la ruta más corta hacia el jugador.  
* **El Emboscador:** No busca al jugador, sino que intenta posicionarse en la intersección *delante* de la dirección hacia donde se mueve el jugador.  
* **El Caótico:** Se mueve aleatoriamente hasta que el jugador está a menos de 5 casillas, entonces entra en modo pánico o ataque.

**Tip Técnico:** Usa una **Máquina de Estados Finitos (FSM)** para que los fantasmas cambien entre estados: *Dispersión, Persecución, Asustado y Retirada*.

---

## **4\. Gestión de Créditos y Tiendas**

Aprovechando tu requisito de "Administración de créditos y premios", introduce una **Tienda entre niveles**:

* **NPC Vendedor:** Un fantasma neutral que te vende vidas extra, mejoras de velocidad o "llaves" para saltar niveles a cambio de los puntos (o una moneda secundaria) recolectada.  
* **Riesgo vs. Recompensa:** Habitaciones secretas que requieren gastar una vida para entrar, pero que contienen un premio garantizado de alto nivel.

---

## **5\. Elementos de Diseño Visual y UI**

Para que el menú sea "amigable" y el avance sea claro:

* **Minimap Dinámico:** Un pequeño recuadro que muestre las zonas exploradas y las que faltan por limpiar (niebla de guerra).  
* **Barra de Progresión:** Un indicador visual de cuánta "comida" falta para completar el nivel actual.  
* **Feedback Visual:** Cuando el jugador sube la velocidad por la dificultad, cambia ligeramente la paleta de colores del laberinto (de azul frío a rojo intenso) para transmitir tensión.

---

## **Estructura Sugerida para el Generador de Tableros**

Para que el generador sea robusto, puedes usar esta lógica:

1. **Layout Base:** Crear una rejilla de $N \\times M$.  
2. **Caminos:** Trazar pasillos principales asegurando conectividad.  
3. **Simetría (Opcional):** Reflejar la mitad del mapa para que se sienta como un Pac-Man clásico.  
4. **Ubicación de Items:** Colocar la comida en los pasillos y los "premios" en callejones sin salida (dead ends) para obligar al jugador a arriesgarse.  
     
   ---

   

