"""
ui2_red_mensajes.py
====================
Procesa los mensajes de red recibidos en cada vuelta del bucle principal
(BAJARSE, DESCARTE, TOMAR_CARTA, TOMAR_DESCARTE, el ciclo de compra
-INICIAR/PASAR/REALIZAR_COMPRA-, INSERTAR, abandono de jugadores,
desconexión, etc.), actualizando el estado del juego según lo que haya
hecho cada jugador. Antes vivía como un bloque de ~360 líneas dentro de
main() en ui2.py; se movió acá tal cual, sin cambiar la lógica.

El estado compartido con main() se lee/escribe como `ui2.NOMBRE` (ver los
comentarios junto a las declaraciones `global` al principio de main() en
ui2.py). `msgGame` (la lista de mensajes a procesar) y `bajarse_sound` son
locales de main() que no cambian de forma relevante para esta función, así
que se reciben por parámetro en vez de promoverlos a globales.
"""
import os
import time
import pygame

import ui2
from Round import Round
from ui2_state_tracking import mostrar_toast_compra


def procesar_mensajes_red(msgGame, bajarse_sound):
    """Procesa todos los mensajes de red pendientes de este frame (`for msg in msgGame:` de siempre)."""
    for msg in msgGame:
        if isinstance(msg,dict) and msg.get("type")=="BAJARSE":
            player_id_que_se_bajo = msg.get("playerId")
            mano_restante = msg.get("playerHand")  # Lista de objetos Card
            jugadas_en_mesa = msg.get("jugadas_bajadas")  # Lista con las combinaciones (tríos/escaleras)
            Jugadas_en_mesa2 = msg.get("playMade")    ## Lista con las combinaciones (tríos/escaleras) en INGLES :D
            ui2.round = msg.get("round")

            print(f"Mensaje de BAJARSE recibido del Player ID: {player_id_que_se_bajo}")
            for p in ui2.players:
                if p.playerId == player_id_que_se_bajo:
                    p.playerHand = mano_restante
                    p.jugadas_bajadas = jugadas_en_mesa
                    p.playMade = Jugadas_en_mesa2
                    try:
                        bajarse_sound.play()
                    except Exception as e:
                        print("Error al reproducir bajarse_sound:", e)
        
        elif isinstance(msg,dict) and msg.get("type")=="TOMAR_DESCARTE":
            player_id_que_tomoD = msg.get("playerId")
            mano_restante = msg.get("playerHand")  # Lista de objetos Card
            carta_tomada = msg.get("cardTakenD")  # Lista con las combinaciones (tríos/escaleras)
            mazo_de_descarte = msg.get("mazo_descarte")
            ui2.round = msg.get("round")
            
            ui2.bought = True

            print(f"Mensaje de TOMAR DESCARTE recibido del Player ID: {player_id_que_tomoD}")
            print(f" Probando.. Mazo de descarte {msg.get("mazo_descarte")}")
            print(f" Probando.. round.discart    {ui2.round.discards}")
            print(f" Probando.. mano_restante                    {msg.get("playerHand")}")
            print(f" Probando.. round.hands[player_id_que_tomoD] {ui2.round.hands[player_id_que_tomoD]}")
            for p in ui2.players:
                if p.playerId == player_id_que_tomoD:
                    p.playerHand = mano_restante
                    mostrar_toast_compra(p.playerName, "descarte")
                    #pass
            cardTakenD = carta_tomada
            ui2.mazo_descarte = mazo_de_descarte   #ui2.round.discards #mazo_de_descarte
            ui2.mazo_descarte = list(ui2.round.discards)#prueba

        elif isinstance(msg,dict) and msg.get("type")=="TOMAR_CARTA":
            player_id_que_tomoC = msg.get("playerId")
            mano_restante = msg.get("playerHand")  # Lista de objetos Card
            carta_tomada = msg.get("cardTaken")  # Lista con las combinaciones (tríos/escaleras)
            mazoBocaAbajo = msg.get("mazo")
            ui2.round = msg.get("round")

            ui2.mostrar_boton_comprar = False
            ui2.bought = True
            ui2.waiting = False
            ui2.time_waiting = None

            print(f"Mensaje de TOMAR CARTA recibido del Player ID: {player_id_que_tomoC}")
            for p in ui2.players:
                if p.playerId == player_id_que_tomoC:
                    p.playerHand = mano_restante
                    p.playerPass = False
                    mostrar_toast_compra(p.playerName, "mazo")
                    #pass
            cardTaken = carta_tomada
            ui2.deckForRound = mazoBocaAbajo #ui2.round.pile

            print(f"Waiting y time_waiting: ({ui2.waiting}, {ui2.time_waiting})")

            ui2.mensaje_temporal = "Tiempo de espera para compras finalizado."
            ui2.mensaje_tiempo = time.time()

        elif isinstance(msg,dict) and msg.get("type")=="PASAR_DESCARTE": 

            player_id_que_pasoD = msg.get("playerId")
            player_name_que_pasoD = msg.get("playerName")

            ui2.waiting = True
            ui2.time_waiting = time.time()
            print(f"Waiting y time_waiting: ({ui2.waiting}, {ui2.time_waiting})")

            
            print(f"Mensaje de PASAR DESCARTE recibido del Player ID: {player_id_que_pasoD}")
            for p in ui2.players:
                if p.playerId == player_id_que_pasoD:
                    p.playerPass = True
            
            if getattr(ui2.mazo_descarte[-1], "discarded_by", None) == ui2.jugador_local.playerId:
                ui2.mensaje_temporal = f"{player_name_que_pasoD} pasó del descarte. Ha iniciado un ciclo de compra."
                ui2.mensaje_tiempo = time.time()
            elif not ui2.jugador_local.isHand:
                ui2.mostrar_boton_comprar = True  
                ui2.mensaje_temporal = f"{player_name_que_pasoD} pasó del descarte. Compra habilitada temporalmente. Presiona 'COMPRAR CARTA' si deseas comprar."
                ui2.mensaje_tiempo = time.time()

        elif isinstance(msg,dict) and msg.get("type")=="INICIAR_COMPRA":
            player_id_que_compraC = msg.get("playerId")
            player_name_que_compraC = msg.get("playerName")
            ui2.players_for_buy_ids = msg.get("players_for_buy_ids")
            ui2.player_in_turn_id = msg.get("player_in_turn_id")
            ui2.player_init_buy_id = msg.get("player_init_buy_id") 
            print(f"Mensaje de INICIAR COMPRA recibido del Player ID: {player_id_que_compraC}")

            ui2.mostrar_boton_comprar = False ###############
            ui2.noBuy = False
            ui2.waiting = False
            ui2.time_waiting = None

            # players[player_in_turn_id].playerTurn = True
            for idx, p in enumerate(ui2.players):

                if p.playerId == ui2.player_in_turn_id:
                    ui2.players[idx].playerTurn = True
                    if p.playerId == ui2.jugador_local.playerId:
                        ui2.jugador_local.playerTurn = True   #mmmmmmmmmmmmm
                else:
                    ui2.players[idx].playerTurn = False

            print(f"Lista de jugadores para compra: {ui2.players_for_buy_ids}")
            print(f"Jugador en turno de compra: {[p for p in ui2.players if p.playerTurn]}")

            ui2.mensaje_temporal = f"{player_name_que_compraC} decide si compra la carta."
            ui2.mensaje_tiempo = time.time()
    
        elif isinstance(msg,dict) and msg.get("type")=="PASAR_COMPRA":
            player_id_que_pasarCompraC = msg.get("playerId")
            player_name_que_pasarCompraC = msg.get("playerName")
            current_buy_id = msg.get("current_buy_id")
            ui2.list_confirm_ids = msg.get("list_confirm_ids")
            ui2.mostrar_boton_comprar = False ###############
            print(f"Mensaje de PASAR COMPRA recibido del Player ID: {player_id_que_pasarCompraC}")

            current_buy_pos = ui2.players_for_buy_ids.index(current_buy_id)
            next_buy_id_pos = (current_buy_pos + 1) % len(ui2.players_for_buy_ids)
            next_buy_id = ui2.players_for_buy_ids[next_buy_id_pos]

            for idx, p in enumerate(ui2.players):

                if p.playerId == next_buy_id:
                    ui2.players[idx].playerTurn = True
                    if p.playerId == ui2.jugador_local.playerId:
                        ui2.jugador_local.playerTurn = True
                else:
                    ui2.players[idx].playerTurn = False
                    
            print(f"Lista de jugadores para compra: {ui2.players_for_buy_ids}")
            print(f"Jugador en turno de compra: {[p for p in ui2.players if p.playerTurn]}")

            ui2.mensaje_temporal = f"{player_name_que_pasarCompraC} paso de la compra."
            ui2.mensaje_tiempo = time.time()

        elif isinstance(msg,dict) and msg.get("type")=="REALIZAR_COMPRA":
            player_id_que_realizarCompraC = msg.get("playerId")
            player_name_que_realizarCompraC = msg.get("playerName")
            ui2.mostrar_boton_comprar = False ###############
            print(f"Mensaje de REALIZAR COMPRA recibido del Player ID: {player_id_que_realizarCompraC}")

            ui2.bought = False # Se cambio a False, estaba en True...
            ui2.player_in_turn_id = None
            ui2.player_init_buy_id = None
            ui2.buy_finished = True
            ui2.time_confirm = time.time()
            
            for idx, p in enumerate(ui2.players):
                ui2.players[idx].playerTurn = False
                    
            print(f"Lista de jugadores para compra: {ui2.players_for_buy_ids}")
            print(f"Jugador en turno de compra: {[p for p in ui2.players if p.playerTurn]}")

            ui2.mensaje_temporal = f"{player_name_que_realizarCompraC} realiza la compra."
            ui2.mensaje_tiempo = time.time()

        elif isinstance(msg,dict) and msg.get("type")=="DESCARTE":
            #print(f"Prueba de isHand ANTES JUGADOR: {[p.isHand for p in players]}")
            ui2.just_went_down_this_turn = False
            ui2.last_inserted_card_data = None
            ui2.jokers_insertados_este_turno.clear()
            player_id_que_descarto = msg.get("playerId")
            mano_restante = msg.get("playerHand")  # Lista de objetos Card
            cartasDescartadas = msg.get("cartas_descartadas")
            mazo_de_descarte = msg.get("mazo_descarte")
            ui2.players[:] = msg.get("players")
            deck_for_round = msg.get("deckForRound")
            ui2.round = msg.get("round")
            
            received_round = msg.get("round")
            
            ui2.noBuy = True
            ui2.bought = False
            ui2.waiting = False
            ui2.time_waiting = None
            ui2.players_for_buy_ids = []
            ui2.player_in_turn_id = None
            ui2.player_init_buy_id = None
            ui2.buy_finished = False
            ui2.time_confirm = None
            ui2.list_confirm_ids = []
            ui2.mostrar_boton_comprar = False
            # print(f"Valor de bought: {bought}")

            for idx, p in enumerate(ui2.players):
                ui2.players[idx].playerTurn = False
                ui2.players[idx].playerPass = False
                ui2.players[idx].cardDrawn = False

            if received_round:
                ui2.round = received_round
                ui2.deckForRound = ui2.round.pile
                ui2.mazo_descarte = list(ui2.round.discards)
            else:
                # Crear una instancia mínima de Round y rellenar pilas si vienen en el mensaje
                ui2.round = Round(ui2.players)
                deck_for_round = msg.get("deckForRound")
                mazo_descarte_msg = msg.get("mazo_descarte")
                if deck_for_round is not None:
                    ui2.round.pile = list(deck_for_round)
                if mazo_descarte_msg is not None:
                    ui2.round.discards = list(mazo_descarte_msg)
                ui2.round.players = ui2.players

            for p in ui2.players:
                if ui2.network_manager.is_host:
                    if p.isHand and p.playerId == ui2.host_id: 
                        ui2.jugador_local = p
                        break
                else:
                    #puerto_local = network_manager.player.getsockname()[1]
                    id_local = ui2.network_manager.player_id
                    if p.isHand and p.playerId == id_local: #puerto_local:
                        ui2.jugador_local = p
                        break

            cartas_descartadas = cartasDescartadas
            #mazo_descarte = mazo_de_descarte #prueba
            ui2.mazo_descarte = list(ui2.round.discards) #prueba
            
        elif isinstance(msg,dict) and msg.get("type")=="COMPRAR_CARTA":   # Revisar la lógica... No vi la función append>>> Por es lo digo
            mano_actualizada = msg.get("playerHand")
            player_id_que_compro = msg.get("playerId")
            player_name_que_compro = msg.get("playerName")
            mazo_de_descarte = msg.get("mazo_descarte")
            deck_for_round = msg.get("deckForRound")
            received_round = msg.get("round")

            # Datos nuevos para actualizar al MANO.
            player_id_MANO = msg.get("playerId_Hand")
            player_hand_MANO = msg.get("playerHand_Hand")

            ui2.mostrar_boton_comprar = False
            ui2.noBuy = True
            ui2.bought = True
            ui2.players_for_buy_ids = []
            ui2.player_in_turn_id = None
            ui2.player_init_buy_id = None
            ui2.buy_finished = False
            ui2.time_confirm = None
            ui2.list_confirm_ids = []
            ui2.waiting = False
            ui2.time_waiting = None

            for idx, p in enumerate(ui2.players):
                ui2.players[idx].playerTurn = False

            print(f"Mensaje de COMPRAR CARTA recibido del Player ID: {player_id_que_compro}")
            for p in ui2.players:
                if p.playerId == player_id_que_compro:
                    p.playerHand = mano_actualizada
                    
                elif p.playerId == player_id_MANO:
                    p.playerHand = player_hand_MANO
            
            if received_round:
                ui2.round = received_round
                ui2.deckForRound = ui2.round.pile
                ui2.mazo_descarte = ui2.round.discards
            else:
                print("Algo salio mal con la transmision de la compra, Houston...")

            if ui2.jugador_local.playerId == player_id_MANO:
                ui2.jugador_local.playerHand = player_hand_MANO
                ui2.jugador_local.cardDrawn = True
                ui2.jugador_local.playerPass = False
                ui2.mensaje_temporal = f"{player_name_que_compro} compro la carta. Continua tu jugada."
                ui2.mensaje_tiempo = time.time()
            else:
                ui2.mensaje_temporal = f"{player_name_que_compro} compro la carta."
                ui2.mensaje_tiempo = time.time()
            mostrar_toast_compra(player_name_que_compro, "descarte")
        
        elif isinstance(msg, dict) and msg.get("type") == "INSERTAR_CARTA":
            mano_restante = msg.get("playerHand")
            jugadas_visuales = msg.get("jugadas_bajadas")
            jugadas_logicas = msg.get("playMade")
            id_target_player = msg.get("playerId")
            id_jugador_que_inserto = msg.get("playerId2")
            received_round = msg.get("round")

            for p in ui2.players:
                if p.playerId == id_target_player:
                    p.jugadas_bajadas = jugadas_visuales
                    p.playMade = jugadas_logicas
                if p.playerId == id_jugador_que_inserto:
                    p.playerHand = mano_restante
        elif isinstance(msg, dict) and msg.get("type") == "SWAP_JOKER":
            p_id = msg.get("playerId")
            new_playMade = msg.get("playMade")
            new_visuals = msg.get("jugadas_bajadas")
            
            # Actualizar al jugador correspondiente
            for p in ui2.players:
                if p.playerId == p_id:
                    p.playMade = new_playMade
                    p.jugadas_bajadas = new_visuals
                    print(f"Jugador {p.playerName} movió un Joker en su mesa.")

        elif isinstance(msg, dict) and msg.get("type") == "SALIR":
            p_id = msg.get("playerId")
            p_name = msg.get("playerName")

            # Incluir cartas del jugador en el mazo de descarte
            for idx, p in enumerate(ui2.players):
                if p.playerId == p_id:
                    while p.playerHand != []:
                        for c in p.playerHand:
                            ui2.round.discards.insert(0,c)
                            p.playerHand.remove(c)
                    p.isSpectator = True
                    p.disconnected = True

                    if p.isHand == True:
                        p.isHand = False
                        #for idx, p in enumerate(players):
                        #        if p.playerId == jugador_local.playerId:
                        next_idx = (idx + 1) % len(ui2.players)
                        ui2.players[next_idx].isHand = True
                                    # Si el siguiente es espectador, seguimos buscando
                        #            while players[next_idx].isSpectator:
                        #                next_idx = (next_idx + 1) % len(players)
                                        # Seguridad para evitar bucle infinito si todos son espectadores (no debería pasar si el juego termina antes)
                        #                if next_idx == idx: 
                        #                    break 
                        break

                    
            ui2.mensaje_temporal = f"El jugador {p_name} abandonó la partida"
            ui2.mensaje_tiempo = time.time()

        elif isinstance(msg, dict) and msg.get("type") == "DESCONEXION":
            reason = msg.get("reason", "")
            if reason == "HOST_LEFT":
                ui2.mensaje_temporal = "El host abandonó la partida. El juego finalizará."
            else:
                ui2.mensaje_temporal = "Se perdió la conexión con el host. El juego finalizará."
            ui2.mensaje_tiempo = time.time()
            ui2.running = False
            try:
                if ui2.network_manager.player:
                    ui2.network_manager.stop()
            except Exception:
                pass
            break
