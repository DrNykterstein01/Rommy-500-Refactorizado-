"""
ui2_cards_render.py
====================
Funciones de dibujo relacionadas con cartas: obtener la imagen de una carta,
dibujar la mano de un jugador (propia o de un oponente, boca arriba o boca
abajo), y un par de utilidades genéricas de dibujo/entrada (botones simples,
texto con borde, rectángulos semitransparentes, detección de click).

Se extrajo tal cual de ui2.py -sin cambiar ninguna lógica-, como parte de la
refactorización para que ui2.py no sea un único archivo gigante. Como varias
de estas funciones leen variables que viven y cambian en tiempo de ejecución
en ui2.py (el tamaño actual de la ventana, si estamos en el encuentro oculto
contra Gaster, etc.), este módulo hace `import ui2` y las lee como
`ui2.ALGO` en vez de importarlas por nombre: así siempre ven el valor
ACTUAL, no una copia vieja de cuando se importó el módulo.
"""
import os
import pygame
import ui2
from Card import Card


def get_card_image(card):
    """
    Devuelve la imagen pygame de la carta según su string (por ejemplo, '2♣.png').
    Si es Joker, busca JokerV2.png.
    Si no existe, devuelve una imagen de carta genérica.
    """
    if hasattr(card, "joker") and card.joker:
        nombre = "JokerV2.png"
    else:
        nombre = str(card) + ".png"

    if ui2.MODO_OCULTO_GASTER and nombre == "back.png":
        ruta_bw = os.path.join(ui2.ASSETS_PATH, "cartas", "back_bw.png")
        if os.path.exists(ruta_bw):
            return pygame.image.load(ruta_bw).convert_alpha()

    ruta = os.path.join(ui2.ASSETS_PATH, "cartas", nombre)
    if os.path.exists(ruta):
        return pygame.image.load(ruta).convert_alpha()
    else:
        # Imagen genérica si no existe la carta
        generic_path = os.path.join(ui2.ASSETS_PATH, "cartas", "back.png")
        if os.path.exists(generic_path):
            return pygame.image.load(generic_path).convert_alpha()
        else:
            # Si tampoco existe back.png, crea una carta vacía
            img = pygame.Surface((60, 90), pygame.SRCALPHA)
            pygame.draw.rect(img, (200, 200, 200), img.get_rect(), border_radius=8)
            return img

#CAMBIO 1
# --- Añadir en ui2.py (zona de utilidades/UI) ---

def draw_player_hand(player, rect, cuadros_interactivos=None, cartas_ref=None, ocultas=None):
    """
    Dibuja la mano del jugador alineada horizontalmente, solapada, sin curva ni inclinación.
    """
    hand = getattr(player, "playerHand", [])
    n = len(hand)
    if n == 0:
        return

    card_height = rect.height - 6
    card_width = int(card_height * 0.68)

    # Solapamiento horizontal
    if n > 1:
        base_sep = int(card_width * 1.25)
        min_sep = int(card_width * 0.65)
        if n <= 6:
            solapamiento = base_sep
        elif n >= 12:
            solapamiento = min_sep
        else:
            solapamiento = int(base_sep - (base_sep - min_sep) * (n - 6) / 6)
        total_width = card_width + (n - 1) * solapamiento
        if total_width > rect.width:
            solapamiento = max(4, (rect.width - card_width) // (n - 1))
        start_x = rect.x + (rect.width - (card_width + (n - 1) * solapamiento)) // 2
    else:
        solapamiento = 0
        start_x = rect.x + (rect.width - card_width) // 2

    y_base = rect.y + 18  # Puedes ajustar este valor si quieres subir/bajar las cartas

    for i in range(n):
        if ocultas and i in ocultas:
            continue
        card = hand[i]
        string_to_card(card)
        img = get_card_image(card)
        img = pygame.transform.smoothscale(img, (card_width, card_height))
        # Sin curva ni inclinación
        img_rect = img.get_rect(topleft=(start_x + i * solapamiento, y_base))
        ui2.screen.blit(img, img_rect.topleft)

        if cuadros_interactivos is not None:
            cuadros_interactivos[f"Carta_{i}"] = img_rect
        if cartas_ref is not None:
            cartas_ref[f"Carta_{i}"] = card


def draw_vertical_back_hand(player, rect):
    """
    Dibuja cartas boca abajo en vertical, tipo lluvia, según la cantidad real de cartas del jugador.
    """
    n = len(getattr(player, "playerHand", []))
    if n == 0:
        return

    # Tamaño de carta
    card_width = rect.width - 8
    card_height = int(card_width / 0.68)
    if card_height > rect.height // 2:
        card_height = rect.height // 2
        card_width = int(card_height * 0.68)

    # Solapamiento vertical
    if n > 1:
        solapamiento = (rect.height - card_height) // (n - 1)
        if solapamiento > card_height * 0.7:
            solapamiento = int(card_height * 0.7)
    else:
        solapamiento = 0

    start_y = rect.y + rect.height - card_height - (n - 1) * solapamiento

    # Imagen de reverso
    back_img = get_card_image("back")

    for i in range(n):
        img = pygame.transform.smoothscale(back_img, (card_width, card_height))
        card_rect = pygame.Rect(rect.x + (rect.width - card_width) // 2,
                                start_y + i * solapamiento,
                                card_width, card_height)
        ui2.screen.blit(img, card_rect.topleft)


def draw_back_cards_by_count(count, rect):
    """
    Dibuja 'count' cartas boca abajo en vertical (tipo lluvia) en el rectángulo dado.
    """
    if count == 0:
        return

    # Tamaño de carta
    card_width = rect.width - 8
    card_height = int(card_width / 0.68)
    if card_height > rect.height // 2:
        card_height = rect.height // 2
        card_width = int(card_height * 0.68)

    # Solapamiento vertical
    if count > 1:
        solapamiento = (rect.height - card_height) // (count - 1)
        if solapamiento > card_height * 0.7:
            solapamiento = int(card_height * 0.7)
    else:
        solapamiento = 0

    start_y = rect.y + rect.height - card_height - (count - 1) * solapamiento

    # Imagen de reverso
    back_img = get_card_image("back")

    for i in range(count):
        img = pygame.transform.smoothscale(back_img, (card_width, card_height))
        card_rect = pygame.Rect(rect.x + (rect.width - card_width) // 2,
                                start_y + i * solapamiento,
                                card_width, card_height)
        ui2.screen.blit(img, card_rect.topleft)


def draw_horizontal_pt_hand(player, rect):
    """
    Dibuja cartas horizontales usando PT.png, según la cantidad real de cartas del jugador.
    """
    n = len(getattr(player, "playerHand", []))
    if n == 0:
        return

    # Tamaño de carta
    card_height = rect.height - 8
    card_width = int(card_height * 0.68)
    if n > 1:
        max_width = rect.width - 8
        solapamiento = (max_width - card_width) // (n - 1)
        if solapamiento > card_width * 0.7:
            solapamiento = int(card_width * 0.7)
    else:
        solapamiento = 0

    start_x = rect.x
    y = rect.y + (rect.height - card_height) // 2

    # Imagen PT.png
    if ui2.MODO_OCULTO_GASTER:
        pt_img_path = os.path.join(ui2.ASSETS_PATH, "cartas", "PT_bw.png")
    else:
        pt_img_path = os.path.join(ui2.ASSETS_PATH, "cartas", "PT.png")
    if os.path.exists(pt_img_path):
        pt_img = pygame.image.load(pt_img_path).convert_alpha()
    else:
        pt_img = get_card_image("back")

    for i in range(n):
        img = pygame.transform.smoothscale(pt_img, (card_width, card_height))
        card_rect = pygame.Rect(start_x + i * solapamiento, y, card_width, card_height)
        ui2.screen.blit(img, card_rect.topleft)


def draw_vertical_pt_hand(player, rect):
    """
    Dibuja cartas verticales usando PT.png, según la cantidad real de cartas del jugador.
    """
    n = len(getattr(player, "playerHand", []))
    if n == 0:
        return

    # Tamaño de carta
    card_width = rect.width - 8
    card_height = int(card_width / 0.68)
    if n > 1:
        max_height = rect.height - 8
        solapamiento = (max_height - card_height) // (n - 1)
        if solapamiento > card_height * 0.7:
            solapamiento = int(card_height * 0.7)
    else:
        solapamiento = 0

    x = rect.x + (rect.width - card_width) // 2
    start_y = rect.y

    # Imagen PT.png
    pt_img_path = os.path.join(ui2.ASSETS_PATH, "cartas", "PT.png")
    if os.path.exists(pt_img_path):
        pt_img = pygame.image.load(pt_img_path).convert_alpha()
    else:
        pt_img = get_card_image("back")

    for i in range(n):
        img = pygame.transform.smoothscale(pt_img, (card_width, card_height))
        card_rect = pygame.Rect(x, start_y + i * solapamiento, card_width, card_height)
        ui2.screen.blit(img, card_rect.topleft)


def draw_horizontal_rain_hand_rotated(player, rect):
    """
    Dibuja cartas en modo 'lluvia horizontal' pero verticalmente (cartas apiladas horizontalmente, rotadas 90 grados).
    El ancho de la carta es igual al de las cartas superiores y el ALTO (largo real de la carta) es más fino.
    """
    n = len(getattr(player, "playerHand", []))
    if n == 0:
        return

    # MISMO ancho que las cartas superiores, pero más finas (menos alto)
    card_width = 120   # igual que cuadro_w_carta
    card_height = 120  # más fino que las superiores (antes era 188)

    if n > 1:
        max_height = rect.height - 8
        solapamiento = (max_height - card_height) // (n - 1)
        if solapamiento > card_height * 0.7:
            solapamiento = int(card_height * 0.7)
        if solapamiento < 0:
            solapamiento = 0
    else:
        solapamiento = 0

    x = rect.x + (rect.width - card_height) // 2
    start_y = rect.y

    pt_img_path = os.path.join(ui2.ASSETS_PATH, "cartas", "PT.png")
    if os.path.exists(pt_img_path):
        pt_img = pygame.image.load(pt_img_path).convert_alpha()
    else:
        pt_img = get_card_image("back")

    for i in range(n):
        img = pygame.transform.smoothscale(pt_img, (card_height, card_width))
        img = pygame.transform.rotate(img, 90)
        card_rect = pygame.Rect(x, start_y + i * solapamiento, card_width, card_height)
        # No dibujar si se sale del recuadro
        if card_rect.bottom <= rect.bottom:
            ui2.screen.blit(img, card_rect.topleft)


def draw_simple_button(surface, rect, text, font, bg=(70,70,70), fg=(255,255,255)):
    pygame.draw.rect(surface, bg, rect, border_radius=8)
    pygame.draw.rect(surface, (180,180,180), rect, 2, border_radius=8)
    txt = font.render(text, True, fg)
    tr = txt.get_rect(center=rect.center)
    surface.blit(txt, tr)


#COMPRAR CARTA


def render_text_with_border(text, font, color, border_color, pos, surface):
    # Dibuja el texto en 8 posiciones alrededor (borde)
    for dx, dy in [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(1,-1),(-1,1),(1,1)]:
        border = font.render(text, True, border_color)
        surface.blit(border, (pos[0]+dx, pos[1]+dy))
    # Dibuja el texto principal encima
    txt = font.render(text, True, color)
    surface.blit(txt, pos)


def draw_transparent_rect(surface, color, rect, border=1):
    temp_surface = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    temp_surface.fill(color)
    surface.blit(temp_surface, (rect.x, rect.y))
    pygame.draw.rect(surface, ui2.BORDER, rect, border)


def draw_label(rect, text):
    label = ui2.font.render(text, True, ui2.TEXTO)
    label_rect = label.get_rect(center=rect.center)
    ui2.screen.blit(label, label_rect)


def get_clicked_box(mouse_pos, cuadros):
    """
    Retorna el nombre del cuadro clickeado o None si no se clickeó ninguno.
    Si hay solapamiento (como en las cartas), prioriza la carta más a la derecha (la que está encima).
    """
    # Recorre los cuadros en orden inverso para que la última carta (más a la derecha) tenga prioridad
    for nombre, rect in reversed(list(cuadros.items())):
        if rect.collidepoint(mouse_pos):
            return nombre
                
    return None


def string_to_card(card_string_or_object):
    """
    Si recibe string como 'A♥' o 'Joker', devuelve Card(...).
    Si recibe lista con strings, intenta convertir cada elemento.
    Si recibe ya un Card, lo devuelve.
    """
    if isinstance(card_string_or_object, Card):
        return card_string_or_object
    if isinstance(card_string_or_object, list):
        # retorna lista de Card o lista original si ya son Card
        return [string_to_card(c) for c in card_string_or_object]
    if not isinstance(card_string_or_object, str):
        return card_string_or_object

    # es str
    if card_string_or_object == "Joker":
        return Card("Joker", "", joker=True)
    # valor == todo menos último char, palo == último char
    value = card_string_or_object[:-1]
    suit = card_string_or_object[-1]
    
    return Card(value, suit)

