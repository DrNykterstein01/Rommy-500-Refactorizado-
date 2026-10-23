"""
ui2_eleccion.py
================
Fase de "elección": determina el orden de turno al empezar cada ronda
(quién es MANO), reparte las cartas de la ronda (vía Game.startRound) y
aplica la ventaja inicial de Gaster si corresponde. Antes vivía como un
bloque de ~260 líneas dentro de main() en ui2.py; se movió acá tal cual,
sin cambiar la lógica. El estado compartido con main() se lee/escribe como
`ui2.NOMBRE` (ver los comentarios junto a las declaraciones `global` al
principio de main() en ui2.py).

main() sigue haciendo el `continue` después de llamar a esta función -eso
no se movió, ya que un `continue` no puede "escapar" de una función.
"""
import os
import time
import pygame

import ui2
from Card import Card
from Game import startRound
from Round import Round
from Turn import drawCard, refillDeck
from ui2_bot_helpers import cargar_bots_ia
from ui2_round_helpers import mostrar_cartas_eleccion
from ui2_state_tracking import update_descartar_visibility, update_bajarse_visibility, update_comprar_visibility


def procesar_fase_eleccion():
    """Cuerpo completo de `if fase == "eleccion":`. Se llama una vez por frame; main() hace el `continue` después."""
    ui2.screen.blit(ui2.fondo_img, (0, 0))  # Nuevo pero se puede quedar :)

    # Procesando mensaje con datos de seleccion de cartas y la lista de jugadores...
    if not ui2.network_manager.is_host:
        # Recuperar los mensajes recibidos del buffer de red
        if ui2.roundOne:
            msg = ui2.network_manager.get_game_state() 
            # Verificar si el mensaje contiene los datos esperados
            if isinstance(msg, dict) and msg.get("type") == "ELECTION_CARDS":
                print(f"Este es el mensaje recibido en fase eleccion  {type(msg)} {msg}{msg.get('type')}")
                ui2.players[:] = msg.get("players")
                ui2.cartas_eleccion = msg.get("election_cards")
                ui2.player1 = ui2.players[0]  

        # Procesar mensajes entrantes para actualizaciones de elecciones o orden
        msgList = ui2.network_manager.get_incoming_messages()
        #print(f"Este es el mensaje recibido en fase eleccion ORDENNNN  {type(msgList)} {msgList}")
        for msg in msgList:
            if isinstance(msg[1], dict):
                if msg[1].get("type") == "DESCONEXION":
                    reason = msg[1].get("reason", "")
                    if reason == "HOST_LEFT":
                        ui2.mensaje_temporal = "El host abandonó la partida. El juego finalizará."
                    else:
                        ui2.mensaje_temporal = "Se perdió la conexión con el host. El juego finalizará."
                    ui2.mensaje_tiempo = time.time()
                    ui2.running = False
                    try:
                        ui2.network_manager.stop()
                    except Exception:
                        pass
                    break
                if msg[1].get("type") == "PLAYER_ORDER":
                    ui2.just_went_down_this_turn = False
                    ui2.last_inserted_card_data = None
                    ui2.dragging_board_joker = False
                    ui2.board_joker_data = None
                    # --- INICIO CORRECCIÓN: RESETEAR VARIABLES DE ESTADO ---
                    ui2.bought = False
                    ui2.noBuy = True
                    ui2.waiting = False
                    ui2.time_waiting = None
                    ui2.players_for_buy_ids = []
                    ui2.player_in_turn_id = None
                    ui2.player_init_buy_id = None
                    ui2.buy_finished = False
                    ui2.list_confirm_ids = []
                    ui2.mostrar_boton_comprar = False
                    # --- FIN CORRECCIÓN ---
                    print("Jugador: Recibido orden de jugadores")
                    ui2.players[:] = msg[1].get("players", [])
                    ui2.deckForRound = msg[1].get("deckForRound")
                    ui2.mazo_descarte = msg[1].get("mazo_descarte")
                    hands = msg[1].get("hands")
                    ui2.round = msg[1].get("round")
                    received_round = msg[1].get("round")
                    
                    if received_round:
                        ui2.round = received_round
                        ui2.deckForRound = ui2.round.pile
                        ui2.mazo_descarte = ui2.round.discards
                    else:
                        # Crear una instancia mínima de Round y rellenar pilas si vienen en el mensaje
                        ui2.round = Round(ui2.players)
                        deck_for_round = msg[1].get("deckForRound")
                        mazo_descarte_msg = msg[1].get("mazo_descarte")
                        if deck_for_round is not None:
                            ui2.round.pile = list(deck_for_round)
                        if mazo_descarte_msg is not None:
                            ui2.round.discards = list(mazo_descarte_msg)
                        # asegurar que round.players apunte a la lista de objetos Player
                        ui2.round.players = ui2.players
                        print("Jugador: creado Round local con pile/discards recibidos.NO DEBERIA...")
                    # Buscar y actualizar jugador local
                    #puerto_local = network_manager.player.getsockname()[1]
                    id_local = ui2.network_manager.player_id
                    print(f"id_local: {id_local}")
                    for p in ui2.players:
                        if p.playerId == id_local: #puerto_local:
                            ui2.jugador_local = p
                            break

                    ui2.jugador_local.playerHand = hands[ui2.jugador_local.playerId] 
                    ui2.visual_hand = list(ui2.jugador_local.playerHand)  # Copia inicial para el orden visual
                    # Limpiar zonas de cartas para todas las rondas
                    ui2.zona_cartas[0] = []
                    ui2.zona_cartas[0].clear()
                    ui2.zona_cartas[1] = []
                    ui2.zona_cartas[1].clear()
                    if ui2.roundThree or ui2.roundFour:
                        ui2.zona_cartas[2] = []
                        ui2.zona_cartas[2].clear()
                    for idx, carta in enumerate(ui2.visual_hand):
                        if not hasattr(carta, "id_visual"):
                            carta.id_visual = id(carta)  # O usa idx para algo más simple

                    # Cambiar fase
                    # FIX: antes estas dos asignaciones eran locales de esta
                    # función (y antes de la refactorización, locales de
                    # main(), que era donde también vivía el bloque de
                    # "mostrar_orden"). main() lee `ui2.mensaje_orden` y
                    # `ui2.tiempo_inicio_orden` (los globales del módulo), así
                    # que sin esto el temporizador quedaba en 0 y la pantalla
                    # del orden se saltaba en el primer frame directo a ronda1.
                    ui2.mensaje_orden = msg[1].get("orden_str", "")
                    ui2.tiempo_inicio_orden = time.time()
                    
                    if ui2.roundOne:
                        ui2.fase = "mostrar_orden"
                    elif ui2.roundTwo:
                        ui2.fase = "ronda2" 
                    elif ui2.roundThree:
                        ui2.fase = "ronda3"
                    elif ui2.roundFour:
                        ui2.fase = "ronda4"
        # Fin procesar Mensajes de INICIO----  Cargar Mazos, Mano, e isHand... PARA EL JUGADOR...       
    if ui2.network_manager.is_host:
        if ui2.roundOne:
            from Game import electionPhase
            playerOrder = electionPhase(ui2.players, ui2.deck)
            # Lista de jugadores Ordenada
            ui2.players[:] = playerOrder
            ui2.players[0].isHand = True    # El primer jugador es mano
            ui2.player1 = None
        elif ui2.roundTwo or ui2.roundThree or ui2.roundFour:
            # sacando al desconcectado
            for player in ui2.players:
                if player.disconnected == True:
                    ui2.players.remove(player)
            # Rotar la lista: el primero pasa al final
            ui2.players.append(ui2.players.pop(0))

            # Reiniciar la bandera de 'isHand' para todos
            for player in ui2.players:
                player.isHand = False
            

            # El nuevo primer jugador es la nueva mano
            lista_activos = [p for p in ui2.players if not p.isSpectator]
            idx_siguiente_Mano = ui2.players.index(lista_activos[0])
            ui2.players[idx_siguiente_Mano].isHand = True

        #for p in players:
        # El jugador local del host SIEMPRE es el Player cuyo playerId ==
        # host_id, sin importar en qué posición quede en el orden de la ronda.
        # Antes solo se reasignaba cuando era players[0]; si un bot ganaba la
        # fase de elección (orden al azar), ui2.jugador_local se quedaba None
        # y el print de "Mano del jugador" reventaba con AttributeError.
        ui2.jugador_local = next(
            (p for p in ui2.players if p.playerId == ui2.host_id),
            ui2.jugador_local,
        )
        if ui2.jugador_local is not None:
            print(f"nombre del jugador_local   {ui2.jugador_local.playerName}")  

        # Construir mensaje de orden
        orden_str = "Orden de juego:\n"
        for idx, jugador in enumerate(ui2.players):
            orden_str += f"{idx+1}. {jugador.playerName}\n"
        
        # Limpiar bajadas/parametros de los jagadores para cada ronda
        for p in ui2.players:
            p.jugadas_bajadas = []
            p.playMade = []
            p.playerHand = []
            p.downHand = False
            p.cardDrawn = False
            p.discarded = False       # ### NUEVO: Asegurar que discarded sea False
            p.playerPass = False      # ### NUEVO: Asegurar que nadie haya "pasado"
            p.playerBuy = False
        ui2.cont_turnos = 0
        # Inicializacion del mazo...
        ui2.round = startRound(ui2.players, ui2.screen)[0]
        print(f"deck para la ronda: {[str(c) for c in ui2.round.pile]}")
        print(f"descartes de la ronda: {[str(c) for c in ui2.round.discards]}")
        for c in ui2.round.discards:
            ui2.mazo_descarte.append(c)
        ui2.deckForRound = ui2.round.pile
        print(f"Las manos a repartir ...... ID: CARTAS")#{ui2.round.hands}")
        ui2.network_manager.dprint(ui2.round.hands)

        # --- ENCUENTRO OCULTO: ventaja inicial de mano para Gaster ---
        if ui2.MODO_OCULTO_GASTER:
            _gaster_jugador = next((p for p in ui2.players if getattr(p, "playerName", None) == "W.D Gaster"), None)
            if _gaster_jugador is not None:
                _numero_ronda_deal = 1 if ui2.roundOne else 2 if ui2.roundTwo else 3 if ui2.roundThree else 4
                ui2.aplicar_ventaja_inicial_gaster(
                    _gaster_jugador,
                    [p for p in ui2.players if p is not _gaster_jugador],
                    ui2.round,
                    _numero_ronda_deal
                )
        # Enviar orden a todos
        
        # PARA PRUEBA...
        # (defensivo: un print de depuración nunca debe tumbar la partida)
        if ui2.jugador_local is not None:
            print(f" Mano del jugador... {ui2.jugador_local.playerHand}")
        '''if ui2.roundOne:
                ui2.players[0].playerHand = [Card("2","♥"), Card("3","♥"), Card("4","♥"), 
                                            Card("5","♥"),Card("6","♥"),
                                            Card("9","♦"),Card("9","♦"),Card("9","♦"),Card("9","♦")]
                ui2.round.hands[ui2.players[0].playerId] = ui2.players[0].playerHand   # Solo una carta para prueba,
                ui2.players[1].playerHand = [Card("2","♥"), Card("3","♥"), Card("4","♥"), 
                                            Card("5","♥"),Card("6","♥"),Card("7","♥"),Card("8","♥"),Card("9","♥"),Card("10","♥"),
                                            Card("9","♦"), Card("9","♦"), 
                                            Card("9","♦"),Card("9","♦"),Card("Joker","", True), Card("9","♦"),Card("Joker","", True,)
                                            ]
                ui2.round.hands[ui2.players[1].playerId] = ui2.players[1].playerHand   # Solo una carta para prueba,
        if ui2.roundTwo:
                ui2.jugador_local.playerHand = [Card("2","♥"), Card("3","♥"), Card("4","♥"), 
                                        Card("5","♥"),
                                        Card("2","♠"), Card("3","♠"), Card("4","♠"), 
                                        Card("5","♠")]  # Solo una carta para prueba
                ui2.round.hands[ui2.jugador_local.playerId] = ui2.jugador_local.playerHand''' 
        # --------------
        '''if ui2.roundThree:
            ui2.jugador_local.playerHand = [Card("9","♥"), Card("9","♠"), Card("9","♦"), Card("9","♦"),
                                        Card("8","♥"), Card("8","♠"), Card("8","♦"), 
                                        Card("7","♥"),Card("7","♦"),Card("7","♠")]  # Solo una carta para prueba
            ui2.round.hands[ui2.jugador_local.playerId] = ui2.jugador_local.playerHand'''
        '''if ui2.roundFour:
            ui2.jugador_local.playerHand = [Card("9","♥"), Card("9","♠"), Card("9","♦"), 
                                        Card("8","♥"), Card("8","♠"), Card("8","♦"), 
                                        Card("2","♥"), Card("3","♥"), Card("4","♥"), 
                                        Card("5","♥")]  # Solo una carta para prueba
            ui2.round.hands[ui2.jugador_local.playerId] = ui2.jugador_local.playerHand'''
        # Limpiar zonas de cartas para todas las rondas
        ui2.zona_cartas[0] = []
        ui2.zona_cartas[0].clear()
        ui2.zona_cartas[1] = []
        ui2.zona_cartas[1].clear()
        if ui2.roundThree or ui2.roundFour:
            ui2.zona_cartas[2] = []
            ui2.zona_cartas[2].clear()
        # --- INICIO CORRECCIÓN: RESETEAR VARIABLES DE ESTADO EN EL HOST ---
        ui2.bought = False
        ui2.noBuy = True
        ui2.waiting = False
        ui2.time_waiting = None
        ui2.players_for_buy_ids = []
        ui2.player_in_turn_id = None
        ui2.player_init_buy_id = None
        ui2.buy_finished = False
        ui2.list_confirm_ids = []
        ui2.mostrar_boton_comprar = False
        # --- FIN CORRECCIÓN ---'''
        msgOrden = {
            "type": "PLAYER_ORDER",
            "players": ui2.players,
            "orden_str": orden_str,
            "round": ui2.round,
            "hands":ui2.round.hands,
            "deckForRound": ui2.deckForRound,
            "mazo_descarte": ui2.mazo_descarte
        }
        ui2.network_manager.broadcast_message(msgOrden)
        # Cambiar fase
        # FIX: mismo fix que en la rama del cliente: escribir en los globales
        # del módulo que lee el bloque "mostrar_orden" de main() en ui2.py
        # (si quedan como variables locales de acá, el temporizador de
        # mostrar_orden arranca en 0 y la pantalla del orden se salta).
        ui2.mensaje_orden = orden_str.strip()
        ui2.tiempo_inicio_orden = time.time()
        if ui2.roundOne:
            ui2.fase = "mostrar_orden"
        elif ui2.roundTwo:
            ui2.fase = "ronda2"
        elif ui2.roundThree:
            ui2.fase = "ronda3"
        elif ui2.roundFour:
            ui2.fase = "ronda4"

        print(f" fase del juego>>> Ronda en realidad :)   {ui2.fase}")

    # Dibujar
    ui2.screen.blit(ui2.fondo_img, (0, 0))
    #mostrar_cartas_eleccion(screen, cartas_eleccion)
    pygame.display.flip()