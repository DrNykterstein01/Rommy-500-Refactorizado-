"""
ui2_round_helpers.py
======================
Utilidades varias del transcurso de una ronda: reordenar/compactar la mano
visual del jugador, reiniciar los elementos visuales al empezar una ronda
nueva, dibujar las cartas de la fase de elección de turno, recalcular sus
posiciones, la risita al revelar un Joker, el procesamiento de mensajes de
red recibidos, resolver una jugada cruda a objetos Card, y la herramienta
de desarrollo para cargar una mano ganadora predefinida. Extraído tal cual
de ui2.py.
"""
import os
import time
import pygame
import random
import ui2
from Card import Card
from ui2_cards_render import get_card_image, string_to_card


def actualizar_indices_visual_hand(visual_hand):
    """
    Reasigna el índice visual (id_visual) a cada carta en visual_hand.
    """
    for idx, carta in enumerate(visual_hand):
        carta.id_visual = idx


def compactar_visual_hand(visual_hand):
    """
    Si falta una carta (None o eliminada), mueve las cartas hacia la izquierda
    y reasigna los índices visuales para que no queden huecos.
    """
    # Elimina cualquier carta None o inexistente
    visual_hand = [c for c in visual_hand if c is not None]

    # Reasigna los índices visuales
    for idx, carta in enumerate(visual_hand):
        carta.id_visual = idx

    return visual_hand


def reiniciar_visual(jugador_local, visual_hand, cuadros_interactivos, cartas_ref):

    # ========== 1. GUARDAR COPIA DEL ORDEN VISUAL ANTES ==========
    orden_anterior = [carta for carta in visual_hand]   # copia exacta del orden visual previo

    # ========== 2. LIMPIAR ESTRUCTURAS ==========
    visual_hand.clear()
    cuadros_interactivos.clear()
    cartas_ref.clear()

    # ======= 3. CREAR NUEVO visual_hand DESDE playerHand ========
    # Pero SIN perder el orden anterior si la carta aún existe
    mano_actual = jugador_local.playerHand[:]  # copia

    # Primero agregamos en el mismo orden que estaban antes
    for carta_prev in orden_anterior:
        if carta_prev in mano_actual:
            visual_hand.append(carta_prev)
            mano_actual.remove(carta_prev)  # evitar duplicados

    # Después agregamos cualquier carta nueva (como la tomada)
    for carta in mano_actual:
        visual_hand.append(carta)

    # Reseteamos índices visuales
    for idx, carta in enumerate(visual_hand):
        carta.id_visual = idx

    # ======= 4. Reset de arrastre ========
    ui2.dragging = False
    ui2.carta_arrastrada = None
    ui2.drag_rect = None
    ui2.drag_offset_x = 0

    # ======= 5. Organizar habilitado ========
    ui2.organizar_habilitado = True



def ocultar_elementos_visual(screen, fondo_img):
    """
    Oculta todo lo visual del juego excepto el fondo.
    """
    screen.blit(fondo_img, (0, 0))
    pygame.display.flip()


def mostrar_cartas_eleccion(screen, cartas_eleccion):
    for carta in cartas_eleccion:
        # Siempre muestra la carta de reverso
        img = get_card_image("PT")
        img = pygame.transform.smoothscale(img, (60, 90))
        screen.blit(img, carta.rect.topleft)
        
        # NUEVO PARA PRUEBAS
        # Dibuja el rectángulo de colisión para diagnóstico (QUITAR DESPUÉS)
        pygame.draw.rect(screen, (255, 0, 0), carta.rect, 2) # Rojo, 2px de grosor
        
        screen.blit(img, carta.rect.topleft)


def recalcular_posiciones_eleccion(cartas_eleccion, WIDTH, HEIGHT):
    """Calcula y asigna el atributo .rect a todas las cartas de elección."""
    if not cartas_eleccion:
        return

    # Parámetros de diseño (ajustar según tu UI)
    CARD_WIDTH = 60
    CARD_HEIGHT = 90
    espacio = 120 # separación horizontal entre cartas

    centro_x = WIDTH // 2
    centro_y = HEIGHT // 2
    
    total_cartas = len(cartas_eleccion)
    total_ancho = espacio * (total_cartas - 1)
    inicio_x = centro_x - total_ancho // 2 # Punto de inicio para centrar

    for i, carta in enumerate(cartas_eleccion):
        # La línea clave: asigna el rect a la carta
        carta.rect = pygame.Rect(
            inicio_x + i * espacio, 
            centro_y - CARD_HEIGHT // 2, 
            CARD_WIDTH, 
            CARD_HEIGHT
        )



def play_risa_if_joker(cartas):
    risa_sound_path = os.path.join(ui2.ASSETS_PATH, "sonido", "risa.wav")
    risa_sound = pygame.mixer.Sound(risa_sound_path)
    for carta in cartas:
        if hasattr(carta, "joker") and carta.joker:
            risa_sound.play()
            ui2.mostrar_joker_fondo = True
            ui2.tiempo_joker_fondo = pygame.time.get_ticks()
            break


def process_received_messagesUi2():
        """Procesa los mensajes recividos de la red"""
        if hasattr(ui2.network_manager,'received_data') and ui2.network_manager.received_data:
            with ui2.network_manager.lock:
                data = ui2.network_manager.received_data
                ui2.network_manager.received_data = None  # Limpiar despues de procesar

            #print(f"Procesando mensaje recibido en Ui2.py: {data.get("type")}")
            
            if ui2.network_manager.is_host:
                #with threading.Lock:
                # Si es un mensaje de ESTADO (como el que contiene cartas_disponibles, elecciones, etc.) en ui2
                if isinstance(data, dict) and data.get("type") in ["ELECTION_CARDS","SELECTION_UPDATE", "ESTADO_CARTAS", "ORDEN_COMPLETO"]:
                    ui2.network_manager.game_state.update(data)
                    print(f"Estado del juego actualizado: {ui2.network_manager.game_state}")
                elif isinstance(data, dict) and data.get("type") in ["BAJARSE","TOMAR_DESCARTE", "TOMAR_CARTA", "DESCARTE", "COMPRAR_CARTA", "PASAR_DESCARTE", "INICIAR_COMPRA","INSERTAR_CARTA","PASAR_COMPRA","REALIZAR_COMPRA","SWAP_JOKER","SALIR","DESCONEXION"]:
                    ui2.network_manager.moves_gameServer.append(data)
                # Si es la respuesta del PING...
                elif isinstance(data, dict) and data.get("type")=="PONG":
                    pass
                # Si es otro tipo de estructura/mensaje no clasificado
                else:
                    ui2.network_manager.incoming_messages.append(("raw", data)) # Opcional: para mensajes no clasificados
                    #print(f"Mensaje guardado en incoming_messages... raw {ui2.network_manager.incoming_messages}")


def resolve_play(jugador, raw_play, play_index=None):
    """
    raw_play puede ser:
      - una lista de Card (ok) -> devuelve la misma lista
      - una lista de str -> si jugador tiene 'jugadas_bajadas' usa esa para resolver
      - un dict -> devolver dict convertida con Card objects
    Devuelve la estructura con cartas como objetos Card (no strings). Si no puede resolver,
    devuelve None.
    """
    # caso ya resuelto
    if isinstance(raw_play, dict):
        resolved = {}
        if "trio" in raw_play and raw_play["trio"]:
            resolved["trio"] = [string_to_card(c) for c in raw_play["trio"]]
        if "straight" in raw_play and raw_play["straight"]:
            resolved["straight"] = [string_to_card(c) for c in raw_play["straight"]]
        return resolved

    if isinstance(raw_play, list) and raw_play and isinstance(raw_play[0], str):
        # busca en jugadas_bajadas si existe
        if hasattr(jugador, "jugadas_bajadas") and play_index is not None and len(jugador.jugadas_bajadas) > play_index:
            return jugador.jugadas_bajadas[play_index]
        # no hay resolved, intentar convertir strings a Card
        try:
            return [string_to_card(s) for s in raw_play]
        except Exception:
            return None

    # si es lista de Card o mezcla:
    if isinstance(raw_play, list):
        return [string_to_card(c) for c in raw_play]

    # fallback
    return raw_play
# --------------------------------------------------------------------


# Nueva función: valida tipos y llama insertCard solo si todo está correcto

def _dev_cargar_mano_ganadora(jugador_local, visual_hand,
                              cuadros_interactivos, cartas_ref,
                              roundOne, roundTwo, roundThree, roundFour):
    """
    [DEV TOOL] Reemplaza la mano de jugador_local con una mano ganadora
    predefinida para la ronda activa y actualiza la visual inmediatamente.

    Instrucciones para rellenar las manos:
    ──────────────────────────────────────
    Usa objetos Card con la sintaxis:  Card("valor", "palo")
    Palos disponibles : "♠"  "♥"  "♦"  "♣"
    Valores disponibles: "2".."10", "J", "Q", "K", "A"
    Joker             : Card("Joker", "", joker=True)

    Ronda 1 → 1 Trío  (3 cartas) + 1 Seguidilla (4 cartas) = 7 cartas mínimo
              Ejemplo de estructura:
                trio      = [Card("9","♠"), Card("9","♥"), Card("9","♦")]
                seguidilla = [Card("2","♣"), Card("3","♣"), Card("4","♣"), Card("5","♣")]
                mano_r1 = trio + seguidilla

    Ronda 2 → 2 Seguidillas (4 cartas cada una) = 8 cartas mínimo
              Ejemplo:
                seg1 = [Card("2","♠"), Card("3","♠"), Card("4","♠"), Card("5","♠")]
                seg2 = [Card("7","♥"), Card("8","♥"), Card("9","♥"), Card("10","♥")]
                mano_r2 = seg1 + seg2

    Ronda 3 → 3 Tríos (3 cartas cada uno) = 9 cartas mínimo
              Ejemplo:
                trio1 = [Card("4","♠"), Card("4","♥"), Card("4","♦")]
                trio2 = [Card("7","♠"), Card("7","♥"), Card("7","♦")]
                trio3 = [Card("K","♠"), Card("K","♥"), Card("K","♦")]
                mano_r3 = trio1 + trio2 + trio3

    Ronda 4 → 2 Tríos + 1 Seguidilla, Y el jugador DEBE bajar TODAS sus cartas.
              Ejemplo:
                trio1  = [Card("5","♠"), Card("5","♥"), Card("5","♦")]
                trio2  = [Card("J","♠"), Card("J","♥"), Card("J","♦")]
                seg    = [Card("2","♣"), Card("3","♣"), Card("4","♣"), Card("5","♣")]
                mano_r4 = trio1 + trio2 + seg
    """

    # ── RONDA 1 : 1 Trío (3 cartas, mismo valor) + 1 Seguidilla (4 cartas, mismo palo, consecutivas)
    # Total: 7 cartas.  El validador acepta exactamente 3 en el trío y 4 en la seguidilla.
    mano_r1 = [
        # --- Trío de Nueves ---
        Card("9", "♠"), Card("9", "♥"), Card("9", "♦"),
        # --- Seguidilla de Tréboles 2-3-4-5 ---
        Card("2", "♣"), Card("3", "♣"), Card("4", "♣"), Card("5", "♣"),
    ]

    # ── RONDA 2 : 2 Seguidillas (4 cartas c/u, mismo palo, consecutivas) ────
    # Total: 8 cartas.  Deben ser seguidillas DISTINTAS (no una misma extendida).
    mano_r2 = [
        # --- Primera seguidilla: Picas 5-6-7-8 ---
        Card("5", "♠"), Card("6", "♠"), Card("7", "♠"), Card("8", "♠"),
        # --- Segunda seguidilla: Corazones J-Q-K-A ---
        Card("J", "♥"), Card("Q", "♥"), Card("K", "♥"), Card("A", "♥"),
    ]

    # ── RONDA 3 : 3 Tríos (3 cartas c/u, mismo valor por trío, valores DISTINTOS entre tríos)
    # Total: 9 cartas.  El validador rechaza dos tríos del mismo valor.
    mano_r3 = [
        # --- Trío de Cuatros ---
        Card("4", "♠"), Card("4", "♥"), Card("4", "♦"),
        # --- Trío de Jotas ---
        Card("J", "♠"), Card("J", "♥"), Card("J", "♦"),
        # --- Trío de Reyes ---
        Card("K", "♠"), Card("K", "♥"), Card("K", "♣"),
    ]

    # ── RONDA 4 : 2 Tríos (valores distintos) + 1 Seguidilla.
    # IMPORTANTE: en Ronda 4 el jugador DEBE bajar TODAS sus cartas en un solo turno.
    # La mano NO puede tener cartas extra; coloca aquí exactamente las que van a la mesa.
    # Total: 10 cartas  (3 + 3 + 4).
    mano_r4 = [
        # --- Trío de Seises ---
        Card("6", "♠"), Card("6", "♥"), Card("6", "♦"),
        # --- Trío de Ases ---
        Card("A", "♠"), Card("A", "♥"), Card("A", "♦"),
        # --- Seguidilla de Diamantes 7-8-9-10 ---
        Card("7", "♦"), Card("8", "♦"), Card("9", "♦"), Card("10", "♦"),
    ]

    # ── Selección de la mano según la ronda activa ───────────────────────────
    if roundOne:
        nueva_mano = mano_r1
        etiqueta_ronda = "Ronda 1"
    elif roundTwo:
        nueva_mano = mano_r2
        etiqueta_ronda = "Ronda 2"
    elif roundThree:
        nueva_mano = mano_r3
        etiqueta_ronda = "Ronda 3"
    elif roundFour:
        nueva_mano = mano_r4
        etiqueta_ronda = "Ronda 4"
    else:
        nueva_mano = []
        etiqueta_ronda = "desconocida"

    if not nueva_mano:
        print(f"[DEV] _dev_cargar_mano_ganadora: mano para {etiqueta_ronda} está vacía. "
              "Rellena la lista correspondiente en la función.")
        return f"[DEV] Mano de {etiqueta_ronda} no configurada. Agrega las cartas en _dev_cargar_mano_ganadora()."

    # ── Asignar la nueva mano al jugador ────────────────────────────────────
    jugador_local.playerHand.clear()
    jugador_local.playerHand.extend(nueva_mano)

    # Marcar cardDrawn=True para que el jugador pueda bajarse sin tomar carta
    jugador_local.cardDrawn = True

    # NOTA: la reconstrucción de visual_hand, cartas_ocultas, cuadros_interactivos
    # y cartas_ref se realiza en el handler del clic dentro de main(), donde esas
    # variables locales son accesibles. Esta función solo prepara playerHand.
    print(f"[DEV] playerHand reemplazada para {etiqueta_ronda}: "
          f"{[str(c) for c in jugador_local.playerHand]}")
    return f"[DEV] Mano de {etiqueta_ronda} cargada ({len(nueva_mano)} cartas). ¡Ya puedes bajarte!"
# ═══════════════════════════════════════════════════════════════════════════════

