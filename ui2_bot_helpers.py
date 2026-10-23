"""
ui2_bot_helpers.py
====================
Lógica de apoyo para los bots de IA: heurísticas para decidir si un
descarte es genuinamente útil para el rival, si conviene saltar el ciclo
de compra, si una carta ayuda a otro jugador, si sirve para insertarla en
una jugada ya bajada en la mesa, la función que efectivamente inserta una
carta en la mesa (safe_insert_card), y la carga de los modelos entrenados
(cargar_bots_ia). Extraído tal cual de ui2.py.
"""
import os
import pygame
from ui2_cards_render import string_to_card


def _descarte_es_genuinamente_util(bot, carta):
    """
    Chequeo más preciso que AIBot._evaluate_card_usefulness() para decidir si
    vale la pena tomar un descarte. _evaluate_card_usefulness cuenta "comparte
    el mismo palo" como algo útil SIN importar qué tan lejos esté el rango
    (p. ej. un 7♦ y un 9♦ en mano hacían que una Q♦ pareciera "útil", aunque
    esté lejísimos en rango y no forme nada real). Aquí sí se exige cercanía
    de rango real para el caso de seguidilla.
    """
    if carta.joker:
        return True  # un Joker casi siempre vale la pena tomarlo
    # ¿Aporta a un posible trío? (mismo valor que otra carta en mano)
    if any((not c.joker) and c.value == carta.value for c in bot.playerHand):
        return True
    # ¿Aporta a una posible seguidilla? Mismo palo Y a poca distancia de
    # rango (cubrible con 1-2 Jokers razonablemente), no solo "mismo palo".
    try:
        rango_carta = carta.numValue()
    except Exception:
        rango_carta = None
    if rango_carta is not None:
        for c in bot.playerHand:
            if c.joker or c.type != carta.type:
                continue
            try:
                if abs(rango_carta - c.numValue()) <= 2:
                    return True
            except Exception:
                continue
    return False


def _debe_saltar_ciclo_compra(players, mazo_descarte, cont):
    """
    Con exactamente 2 jugadores activos, la compra solo puede ocurrir
    lógicamente en el primerísimo turno de la ronda (cuando el tope del
    descarte es la carta inicial, que nadie descartó). De ahí en adelante,
    el tope del descarte SIEMPRE será lo que el otro jugador acaba de
    descartar, y un jugador nunca puede comprar su propio descarte -así que
    el ciclo de compra jamás tendría a nadie elegible para comprar-. Activar
    de todas formas la espera de 8s en ese caso solo hace la partida más
    lenta sin ningún propósito real, así que se salta directo a robar del
    mazo. Con 3+ jugadores activos, el ciclo de compra se deja tal cual.
    """
    activos = [p for p in players if not getattr(p, "isSpectator", False)]
    return len(activos) == 2 and len(mazo_descarte) >= 1 and cont > 0


def _carta_ayuda_a_otro_jugador(bot_en_turno, carta, players):
    """
    True si algún OTRO jugador que ya se bajó podría insertar esta carta de
    inmediato en alguna jugada de la mesa (propia o ajena) apenas la tenga
    en mano. Se usa para evitar descartar justo la carta que le hace falta a
    un rival (o a ti, si eres tú quien juega contra el bot).
    """
    tabla = []
    for p in players:
        if getattr(p, "isSpectator", False):
            continue
        for idx_j, jugada in enumerate(getattr(p, "playMade", None) or []):
            tabla.append({"owner": p, "play_index": idx_j, "play": jugada})
    if not tabla:
        return False
    for p in players:
        if p is bot_en_turno or getattr(p, "isSpectator", False) or not getattr(p, "downHand", False):
            continue
        if _carta_sirve_para_insertar(p, carta, tabla):
            return True
    return False


def _carta_sirve_para_insertar(bot, carta, tabla_jugadas):
    """
    True si `carta` podría insertarse de inmediato en alguna jugada de la
    mesa (propia o de otro jugador) -ya sea extendiendo una seguidilla,
    completando un trío, o sustituyendo un Joker presente en una
    seguidilla-. Reutiliza los mismos chequeos que usa
    AIBot.decide_insert_card internamente, así que el criterio de "encaja o
    no" es exactamente el mismo que usa el bot al insertar de verdad.
    """
    for entry in tabla_jugadas:
        jugada = entry["play"]
        tipo = bot._get_play_type(jugada)
        if tipo == "sequence":
            if bot._get_insertion_positions(carta, jugada):
                return True
            if bot._find_joker_substitution(carta, jugada) is not None:
                return True
        elif tipo == "trio":
            if bot._can_insert_into_trio(carta, jugada) is not None:
                return True
    return False


def safe_insert_card(jugador, target_player, idx_jugada, card_to_insert, position, target_subtype=None,joker_index=None):
    """
    Valida tipos y que la jugada objetivo tenga objetos Card.
    target_subtype: "trio" | "straight" | None (None -> intenta inferir)
    """
    from Card import Card
    objeto_carta = string_to_card(card_to_insert)
    print(f"Objeto de carta: {objeto_carta}")
    print(f"String de carta: {card_to_insert}")
    # normaliza carta
    if not isinstance(card_to_insert, Card):
        print("safe_insert_card: card_to_insert NO es Card:", type(card_to_insert), repr(card_to_insert))
        return False

    plays = getattr(target_player, "playMade", [])
    if idx_jugada < 0 or idx_jugada >= len(plays):
        print("safe_insert_card: idx_jugada fuera de rango:", idx_jugada, "len(playMade)=", len(plays))
        return False

    target_play = plays[idx_jugada]

    # si target_play es dict, elegimos la sublista correcta
    if isinstance(target_play, dict):
        if target_subtype == "trio":
            cartas_jugada = target_play.get("trio", [])
        elif target_subtype == "straight":
            cartas_jugada = target_play.get("straight", [])
        else:
            # intentar inferir: preferir straight si existe no vacío
            cartas_jugada = target_play.get("straight") or target_play.get("trio") or []
    else:
        cartas_jugada = target_play or []

    # Validar que cartas_jugada sean objetos Card
    for c in cartas_jugada:
        string_to_card(c)
        if not isinstance(c, Card):
            print("safe_insert_card: elemento en la jugada objetivo NO es Card:", type(c), repr(c))
            print("target_player.playMade[{}] = {}".format(idx_jugada, target_play))
            return False

    # Todo bien: llamar al método real. Importante: aquí llamamos con idx_jugada (índice en playMade).
    try:
        # Si tu Player.insertCard espera trabajar con dict y asume 'straight' por defecto,
        # esto funcionará. Si insertCard necesita un subtype explícito, habría que pasarlo.
        result  = jugador.insertCard(
            targetPlayer=target_player, 
            targetPlayIndex=idx_jugada, 
            cardToInsert=card_to_insert, 
            position=position, 
            jokerIndex=joker_index
        )
        if result:
            return True
        else:
            return False
    except Exception as e:
        print("safe_insert_card: excepción al llamar insertCard:", e)
        return False


def cargar_bots_ia(network_manager, players_reales_count):
    """
    Carga (o crea con heurística base, si no hay modelo entrenado) los bots
    de IA configurados por el host, según `network_manager.num_bots` y
    `network_manager.bot_duel_config`. Devuelve una lista de instancias
    `AIBot` ya listas para sumarse a `players`.

    Se separó de main() a propósito: cargar los modelos (.pt) es la parte
    lenta/bloqueante de iniciar una partida contra bots (deja la ventana en
    negro y en silencio un rato). Al vivir en una función aparte, se puede
    llamar DESDE UN HILO en segundo plano mientras se muestra una pantalla
    de carga animada (ver main.py / loading_screen.py), y el resultado se
    le pasa a main() mediante el parámetro `bots_precargados` para que no
    se repita la carga.
    """
    num_bots = getattr(network_manager, 'num_bots', 0)
    bots = []
    if num_bots <= 0:
        return bots

    from AIBot import AIBot
    # "Sala de Bots": duelo 1vs1 contra un bot ESPECÍFICO elegido por el
    # usuario (LouisBot o GeniBot), cada uno con su propio archivo .pt.
    # Si no viene seteado, se usa el comportamiento genérico de siempre
    # (num_bots bots llamados "LouisBot", cargando LouisBot.pt).
    bot_duel_config = getattr(network_manager, 'bot_duel_config', None)
    try:
        from rummy_env import RummyEnv
        bot_action_dim = RummyEnv.ACTION_SPACE
    except Exception as e:
        print(f"[BOTS] No se pudo importar RummyEnv para action_dim, usando 3 por defecto: {e}")
        bot_action_dim = 3

    # El tamaño del estado que espera la red depende de CUÁNTOS jugadores
    # había en total durante el entrenamiento (encode_state incluye un
    # bloque de features por cada oponente). Si esta partida tiene un
    # número distinto de jugadores al usado para entrenar el modelo, la
    # carga de pesos fallará por mismatch de tamaño -por eso todo esto va
    # en un try/except: si falla, el bot simplemente juega con su
    # heurística base en vez de la red entrenada, en lugar de romper la
    # partida-.
    total_players_final = players_reales_count + num_bots
    bot_id_base = 1000  # bien por encima de cualquier player_id real (1, 2, 3...)

    for i in range(num_bots):
        if bot_duel_config and num_bots == 1:
            # Duelo específico desde "Sala de Bots".
            bot_name = bot_duel_config.get('name', 'LouisBot')
            model_filename = bot_duel_config.get('model_file', f"{bot_name}.pt")
        else:
            # Comportamiento genérico existente (crear sala + bots).
            bot_name = "LouisBot"
            model_filename = "LouisBot.pt"

        model_path = os.path.join(os.path.dirname(__file__), model_filename)
        bot = AIBot(bot_id_base + i, bot_name)
        try:
            dummy_players_info = [{'hand_size': 0} for _ in range(total_players_final)]
            dummy_state = bot.encode_state(None, 0, dummy_players_info, 1, phase=0)
            bot.rl_state_dim = len(dummy_state)
            bot.rl_action_dim = bot_action_dim
            bot.load_rl_model(model_path)
            if bot.rl_enabled and os.path.exists(model_path):
                bot.rl_epsilon = 0.0  # sin exploración aleatoria: juega lo mejor que aprendió
                print(f"[BOTS] {bot.playerName}: modelo entrenado ({model_filename}) cargado correctamente.")
            else:
                bot.rl_enabled = False
                print(f"[BOTS] {bot.playerName}: no se encontró '{model_filename}', jugará con la heurística base.")
        except Exception as e:
            bot.rl_enabled = False
            print(f"[BOTS] {bot.playerName}: no se pudo cargar '{model_filename}' ({e}). "
                  f"Probablemente esta partida tiene distinta cantidad de jugadores a la del "
                  f"entrenamiento. Jugará con la heurística base igualmente.")
        bots.append(bot)

    print(f"[BOTS] Se cargaron {len(bots)} bot(s) de IA.")
    return bots


