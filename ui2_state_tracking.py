"""
ui2_state_tracking.py
========================
Pequeño grupo de funciones que leen y ESCRIBEN estado global compartido con
el bucle principal de ui2.py (quién tiene la carta que acaba de tomar, el
texto del "toast" de compra, y los flags que controlan si se ven los
botones Descartar/Bajarse/Comprar). Por eso, en vez de duplicar esas
variables acá, se accede siempre a través de `ui2.NOMBRE` -nunca con una
copia propia-, para que el estado siga sincronizado exactamente igual que
cuando este código vivía dentro de ui2.py.
"""
import time
import pygame
import ui2


def register_taken_card(player, card):
    ui2.last_taken_card = card
    ui2.last_taken_player = player


def clear_taken_card_for_player(player):
    if ui2.last_taken_player is not player:
        ui2.last_taken_card = None
        ui2.last_taken_player = None


def can_discard(player, cards):
    # devuelve False si el jugador intentara descartar la carta que tomó este turno
    # si no es el mismo jugador o no hay carta registrada, permitir
    if ui2.last_taken_player is not player or ui2.last_taken_card is None:
        return True

    # normaliza a lista
    if isinstance(cards, (list, tuple, set)):
        items = list(cards)
    else:
        items = [cards]

    for c in items:
        # compara por identidad primero, luego por igualdad de string/valor
        try:
            if (c is ui2.last_taken_card or c == ui2.last_taken_card) and len(items) >= 1:
                return False
        except Exception:
            if str(c) == str(ui2.last_taken_card):
                return False
    return True

# ---------------------- Helpers robustos para UI ----------------------

def mostrar_toast_compra(nombre_jugador, origen="descarte"):
    if origen == "mazo":
        ui2.toast_compra_texto = f"{nombre_jugador} tomó una carta del mazo"
    elif origen == "central":
        ui2.toast_compra_texto = f"{nombre_jugador} tomó la carta central"
    else:
        ui2.toast_compra_texto = f"{nombre_jugador} tomó la carta del descarte"
    ui2.toast_compra_hasta = time.time() + ui2.TOAST_COMPRA_DURACION


def dibujar_toast_compra(surface, width, turno_rect=None):

    texto_a_mostrar = ""
    if ui2.jugador_local is not None and getattr(ui2.jugador_local, "isHand", False):
        texto_a_mostrar = "¡ES TU TURNO!"
    elif ui2.toast_compra_texto and time.time() < ui2.toast_compra_hasta:
        texto_a_mostrar = ui2.toast_compra_texto
    else:
        ui2.toast_compra_texto = ""
        return

    font_toast = ui2.get_game_font(14)
    text_surf = font_toast.render(texto_a_mostrar, True, (255, 255, 255))
    padding_x = 18
    padding_y = 10
    toast_w = min(width - 40, text_surf.get_width() + padding_x * 2)
    toast_h = text_surf.get_height() + padding_y * 2
    x = (width - toast_w) // 2
    y = 76
    if turno_rect:
        y = max(y, turno_rect.bottom + 8)

    toast_surface = pygame.Surface((toast_w, toast_h), pygame.SRCALPHA)
    pygame.draw.rect(toast_surface, (45, 35, 35, 210), toast_surface.get_rect(), border_radius=10)
    pygame.draw.rect(toast_surface, (249, 170, 51, 230), toast_surface.get_rect(), 2, border_radius=10)

    text_rect = text_surf.get_rect(center=(toast_w // 2, toast_h // 2))
    toast_surface.blit(text_surf, text_rect)
    surface.blit(toast_surface, (x, y))



def update_descartar_visibility(zona_cartas, roundThree, roundFour):
    """
    Botón 'Descartar':
    - Rondas 1/2 → visible si zona_cartas[2] tiene al menos 1 carta.
    - Rondas 3/4 → visible si zona_cartas[3] tiene al menos 1 carta.
    """

    try:
        if zona_cartas is None:
            ui2.mostrar_boton_descartar = False
            return

        if roundThree or roundFour:
            # revisar zona 3
            ui2.mostrar_boton_descartar = len(zona_cartas) > 3 and len(zona_cartas[3]) > 0
        else:
            # revisar zona 2
            ui2.mostrar_boton_descartar = len(zona_cartas) > 2 and len(zona_cartas[2]) > 0

    except Exception:
        ui2.mostrar_boton_descartar = False

def update_bajarse_visibility(zona_cartas, roundThree, roundFour):
    """
    Reglas:
    - En rondas 1/2 → zonas 0 y 1 deben tener al menos 1 carta.
    - En rondas 3/4 → zonas 0, 1 y 2 deben tener al menos 1 carta.
    """
    try:
        # Validar que realmente llegó una lista de zonas.
        if zona_cartas is None:
            ui2.mostrar_boton_bajarse = False
            return

        # Rondas 3 o 4 → revisar zonas 0,1,2
        if roundThree or roundFour:
            if len(zona_cartas) > 2:
                ui2.mostrar_boton_bajarse = (
                    len(zona_cartas[0]) > 0 and
                    len(zona_cartas[1]) > 0 and
                    len(zona_cartas[2]) > 0
                )
            else:
                ui2.mostrar_boton_bajarse = False
            return

        # Rondas 1 o 2 → solo revisar zonas 0 y 1
        if len(zona_cartas) > 1:
            ui2.mostrar_boton_bajarse = (
                len(zona_cartas[0]) > 0 and
                len(zona_cartas[1]) > 0
            )
        else:
            ui2.mostrar_boton_bajarse = False

    except Exception:
        ui2.mostrar_boton_bajarse = False

def update_comprar_visibility():
    """
    El botón 'Comprar carta' será visible solo mientras:
    1. La flag ui2.mostrar_boton_comprar sea True
    2. El jugador NO sea quien descartó la carta del tope
    3. El jugador NO sea la mano actual
    """
    
    # Si ya es False, no hacemos nada
    if not ui2.mostrar_boton_comprar:
        return
    
    # Aplicar restricciones: si no hay cartas, si es mano, o si es su propio descarte
    if not ui2.mazo_descarte:
        ui2.mostrar_boton_comprar = False
    elif ui2.jugador_local.isHand:
        ui2.mostrar_boton_comprar = False
    elif getattr(ui2.mazo_descarte[-1], "discarded_by", None) == ui2.jugador_local.playerId:
        ui2.mostrar_boton_comprar = False
    
    return True

# ═══════════════════════════════════════════════════════════════════════════════
# DEV TOOL — Carga de mano ganadora predefinida según la ronda actual
# ═══════════════════════════════════════════════════════════════════════════════