"""
ui2_bot_turn.py
================
Lógica automática de turno de los bots de IA (LouisBot, GeniBot, Gaster):
una máquina de estados que, mientras es el turno de un bot, decide de dónde
robar (mazo/descarte), si se baja, si inserta cartas en jugadas de la mesa y
qué descartar, con pausas entre cada acción para que no juegue instantáneo.

Antes vivía como un bloque de ~460 líneas dentro del bucle principal de
main() en ui2.py. Se movió acá SIN cambiar nada de la lógica: todo el
estado compartido con main() (jugadores, ronda, flags de compra, mensajes,
etc.) se lee y escribe a través de `ui2.NOMBRE`, que apunta exactamente a
las mismas variables de siempre (ver las declaraciones `global` al inicio de
main()). Lo único que se recibe por parámetro son los sonidos, que son
variables locales de main() y no cambian durante la partida.
"""
import time
import pygame

import ui2
from Turn import drawCard
from ui2_bot_helpers import (
    _descarte_es_genuinamente_util, _debe_saltar_ciclo_compra,
    _carta_ayuda_a_otro_jugador, _carta_sirve_para_insertar, safe_insert_card,
)
from ui2_state_tracking import can_discard, register_taken_card, mostrar_toast_compra

BOT_DELAY_PENSAR = 1.4          # "piensa" antes de decidir de dónde robar
BOT_DELAY_ENTRE_ACCIONES = 1.3  # pausa entre robar -> bajarse -> descartar


def procesar_turno_bots(voz_turno, voz_bajarse, voz_end, voz_insert, voz_substitute, bajarse_sound):
    """Avanza un paso la máquina de estados del bot que tenga el turno (si hay uno). Se llama una vez por frame."""
    # ============================================================
    # === LÓGICA AUTOMÁTICA DE TURNO PARA LOS BOTS DE IA (LouisBot) ===
    # Sólo el HOST controla a los bots (viven únicamente en players[] del
    # host). Reutiliza exactamente los mismos mensajes/variables que un
    # humano generaría al hacer click, para que la sincronización con el
    # resto del juego (y con otros clientes reales, si los hubiera) no
    # cambie en nada.
    # ============================================================
    if ui2.network_manager.is_host and ui2.pausa_fin_ronda_hasta is None and ui2.fase in ("ronda1", "ronda2", "ronda3", "ronda4"):
        bot_en_turno = next(
            (p for p in ui2.players
             if hasattr(p, "decide_draw_source")
             and getattr(p, "isHand", False)
             and not getattr(p, "isSpectator", False)),
            None
        )
    else:
        bot_en_turno = None

    if bot_en_turno is None:
        ui2.bot_turno_estado["bot_id"] = None
        ui2.bot_turno_estado["fase_accion"] = None
    else:
        ronda_actual_bot = 1 if ui2.roundOne else 2 if ui2.roundTwo else 3 if ui2.roundThree else 4

        # Nuevo turno de bot (o cambió de bot): reiniciar la máquina de estados.
        if ui2.bot_turno_estado.get("bot_id") != bot_en_turno.playerId:
            ui2.bot_turno_estado["bot_id"] = bot_en_turno.playerId
            ui2.bot_turno_estado["fase_accion"] = "pensando_robo"
            ui2.bot_turno_estado["t"] = time.time() + BOT_DELAY_PENSAR
            ui2.bot_turno_estado["intentos_insercion"] = 0

            # La voz de "es tu turno" del bot debe sonar apenas el juego
            # determina que le toca a él -no cuando el humano descarta-,
            # así que se dispara justo aquí, en el mismo instante en que
            # se detecta el inicio de un turno nuevo del bot.
            if len(ui2.players) == 2 and any(hasattr(p, "is_ai") for p in ui2.players) and voz_turno:
                voz_turno.play()


        ahora = time.time()
        accion = ui2.bot_turno_estado.get("fase_accion")

        # --- Si estábamos esperando la ventana de compra (8s) y ya se tomó la carta
        #     (ya sea porque el temporizador la robó del mazo o porque el humano la
        #     compró), avanzamos a la fase de decidir la jugada. ---
        if accion == "esperando_para_robar_mazo" and bot_en_turno.cardDrawn:
            ui2.bot_turno_estado["fase_accion"] = "pensando_jugada"
            ui2.bot_turno_estado["t"] = ahora + BOT_DELAY_ENTRE_ACCIONES
            accion = "pensando_jugada"

        # --- PASO 1: decidir de dónde robar (mazo o descarte) ---
        if (accion == "pensando_robo" and ahora >= ui2.bot_turno_estado["t"]
                and not bot_en_turno.cardDrawn and not ui2.waiting):
            discard_top = ui2.mazo_descarte[-1] if ui2.mazo_descarte else None
            es_propio_descarte = bool(discard_top) and getattr(discard_top, "discarded_by", None) == bot_en_turno.playerId
            players_info_bot = [{"hand_size": len(p.playerHand)} for p in ui2.players if p.playerId != bot_en_turno.playerId]

            quiere_descarte = False
            if discard_top and not es_propio_descarte:
                # Si ya se bajó, primero revisa si esta carta encaja de
                # inmediato en alguna jugada de la mesa (propia o ajena).
                # La red entrenada nunca vio esta señal durante el
                # entrenamiento (solo conoce su propia mano), así que sin
                # este chequeo el bot ignoraba descartes clarísimamente
                # útiles para insertar. Si encaja, se prioriza tomarla
                # sin ni siquiera consultar la decisión normal.
                insertable_de_inmediato = False
                if bot_en_turno.downHand:
                    try:
                        tabla_para_insercion = []
                        for p in ui2.players:
                            if getattr(p, "isSpectator", False):
                                continue
                            for idx_j, jugada in enumerate(getattr(p, "playMade", None) or []):
                                tabla_para_insercion.append({"owner": p, "play_index": idx_j, "play": jugada})
                        insertable_de_inmediato = _carta_sirve_para_insertar(bot_en_turno, discard_top, tabla_para_insercion)
                    except Exception as e:
                        print(f"[BOTS] {bot_en_turno.playerName}: error revisando si el descarte es insertable ({e}).")
                        insertable_de_inmediato = False

                if insertable_de_inmediato:
                    quiere_descarte = True
                else:
                    try:
                        quiere_descarte = bool(bot_en_turno.decide_draw_source(discard_top, len(ui2.deckForRound), players_info_bot))
                    except Exception as e:
                        print(f"[BOTS] {bot_en_turno.playerName}: error decidiendo el robo ({e}). Robará del mazo.")
                        quiere_descarte = False

                    # Red de seguridad: la red entrenada a veces sigue con el
                    # hábito de "tomar del descarte casi siempre" (residuo de
                    # antes de corregir la recompensa de esta decisión durante
                    # el entrenamiento). Si quiere tomarla pero la carta es
                    # CLARAMENTE inútil para la mano actual, se corrige la
                    # decisión aquí mismo en vez de esperar a que un
                    # reentrenamiento termine de quitarle el hábito.
                    if quiere_descarte:
                        try:
                            if not _descarte_es_genuinamente_util(bot_en_turno, discard_top):
                                quiere_descarte = False
                        except Exception as e:
                            print(f"[BOTS] {bot_en_turno.playerName}: error evaluando utilidad del descarte ({e}).")

            if quiere_descarte:
                # --- Equivalente a hacer click en "Tomar descarte" ---
                cardTakenD = drawCard(bot_en_turno, ui2.round, True)
                bot_en_turno.playerHand = ui2.round.hands[bot_en_turno.playerId]
                ui2.mazo_descarte = list(ui2.round.discards)
                ui2.bought = True
                # Igual que con el humano: registra que esta carta específica
                # se acaba de tomar del descarte, para que no pueda
                # descartarla de vuelta este mismo turno (ver can_discard).
                register_taken_card(bot_en_turno, cardTakenD)

                msgTomarDescarte = {
                    "type": "TOMAR_DESCARTE",
                    "cardTakenD": cardTakenD,
                    "playerHand": bot_en_turno.playerHand,
                    "playerId": bot_en_turno.playerId,
                    "mazo_descarte": ui2.mazo_descarte,
                    "round": ui2.round
                }
                ui2.network_manager.broadcast_message(msgTomarDescarte)
                try:
                    mostrar_toast_compra(bot_en_turno.playerName, "descarte")
                except Exception:
                    pass
                ui2.mensaje_temporal = f"{bot_en_turno.playerName} tomó una carta del descarte."
                ui2.mensaje_tiempo = time.time()

                ui2.bot_turno_estado["fase_accion"] = "pensando_jugada"
                ui2.bot_turno_estado["t"] = time.time() + BOT_DELAY_ENTRE_ACCIONES
            else:
                # --- Equivalente a hacer click en "Tomar carta" (pasa del descarte
                #     e inicia la ventana de compra de 8s antes de robar del mazo) ---
                msgPasarD = {
                    "type": "PASAR_DESCARTE",
                    "playerId": bot_en_turno.playerId,
                    "playerName": bot_en_turno.playerName
                }
                ui2.waiting = True
                ui2.time_waiting = time.time()
                saltar_compra = _debe_saltar_ciclo_compra(ui2.players, ui2.mazo_descarte, ui2.cont_turnos)
                if saltar_compra:
                    # 2 jugadores activos y ya no es el primer turno de la
                    # ronda: nadie puede comprar de todas formas (ver
                    # _debe_saltar_ciclo_compra), así que se "vence" la
                    # ventana de 8s al instante en vez de esperarla de verdad.
                    ui2.time_waiting = time.time() - 9
                bot_en_turno.playerPass = True
                ui2.network_manager.broadcast_message(msgPasarD)

                # Como el bot vive en el mismo proceso que jugador_local (el host),
                # no "recibe" su propio mensaje por red, así que aplicamos aquí
                # mismo el mismo efecto que tendría jugador_local al recibirlo:
                # habilitar el botón "Comprar carta" si corresponde.
                if saltar_compra:
                    pass  # nada que comprar: ni botón ni mensaje de compra
                elif ui2.jugador_local and ui2.mazo_descarte and getattr(ui2.mazo_descarte[-1], "discarded_by", None) == ui2.jugador_local.playerId:
                    ui2.mensaje_temporal = f"{bot_en_turno.playerName} pasó del descarte. Ha iniciado un ciclo de compra."
                    ui2.mensaje_tiempo = time.time()
                elif ui2.jugador_local and not ui2.jugador_local.isHand:
                    ui2.mostrar_boton_comprar = True
                    ui2.mensaje_temporal = f"{bot_en_turno.playerName} pasó del descarte. Compra habilitada temporalmente. Presiona 'COMPRAR CARTA' si deseas comprar."
                    ui2.mensaje_tiempo = time.time()

                ui2.bot_turno_estado["fase_accion"] = "esperando_para_robar_mazo"
                # (el robo automático del mazo lo dispara el temporizador de 8s
                #  compartido con el flujo humano, ver más abajo en el bucle)

        # --- PASO 2: intentar bajar jugadas (tríos/seguidillas) ---
        elif accion == "pensando_jugada" and ahora >= ui2.bot_turno_estado["t"] and bot_en_turno.cardDrawn:
            try:
                jugada = None if bot_en_turno.downHand else bot_en_turno.decide_play_cards(ronda_actual_bot)
            except Exception as e:
                print(f"[BOTS] {bot_en_turno.playerName}: error decidiendo la jugada ({e}). No se baja este turno.")
                jugada = None

            if jugada:
                try:
                    grupos_finales = []
                    jugada_valida = True
                    for grupo in jugada:
                        grupo = list(grupo)
                        tipo_grupo = bot_en_turno._get_play_type(grupo)
                        if tipo_grupo == "sequence":
                            ordenado = bot_en_turno.sortedStraight(grupo)
                            if ordenado and ordenado is not True:
                                grupo = ordenado
                            # Salvaguarda: nunca confiar ciegamente en lo que
                            # devuelve decide_play_cards. Antes de bajar
                            # nada a la mesa, se revalida cada grupo con las
                            # mismas reglas que usa el resto del juego
                            # (mínimo 4 cartas, mismo palo, consecutivas).
                            if not bot_en_turno.isValidStraightF(grupo):
                                jugada_valida = False
                                print(f"[BOTS] {bot_en_turno.playerName}: JUGADA INVÁLIDA DETECTADA Y BLOQUEADA "
                                      f"(seguidilla con {len(grupo)} cartas: {[str(c) for c in grupo]}). "
                                      f"Se cancela la bajada completa de este turno.")
                        elif tipo_grupo == "trio":
                            if not bot_en_turno.isValidTrioF(grupo):
                                jugada_valida = False
                                print(f"[BOTS] {bot_en_turno.playerName}: JUGADA INVÁLIDA DETECTADA Y BLOQUEADA "
                                      f"(trío con {len(grupo)} cartas: {[str(c) for c in grupo]}). "
                                      f"Se cancela la bajada completa de este turno.")
                        else:
                            jugada_valida = False
                            print(f"[BOTS] {bot_en_turno.playerName}: JUGADA INVÁLIDA DETECTADA Y BLOQUEADA "
                                  f"(grupo de tipo desconocido: {[str(c) for c in grupo]}). "
                                  f"Se cancela la bajada completa de este turno.")
                        grupos_finales.append(grupo)

                    if not jugada_valida:
                        # No se toca la mano ni la mesa: es como si el bot
                        # hubiera decidido no bajarse este turno. Pasa
                        # directo a intentar descartar.
                        grupos_finales = []

                    if grupos_finales:
                        if not getattr(bot_en_turno, "jugadas_bajadas", None):
                            bot_en_turno.jugadas_bajadas = []
                        if not getattr(bot_en_turno, "playMade", None):
                            bot_en_turno.playMade = []

                        for grupo in grupos_finales:
                            bot_en_turno.jugadas_bajadas.append(grupo)
                            bot_en_turno.playMade.append(grupo)
                            for carta in grupo:
                                if carta in bot_en_turno.playerHand:
                                    bot_en_turno.playerHand.remove(carta)

                        bot_en_turno.downHand = True

                        msgBajarse = {
                            "type": "BAJARSE",
                            "playerHand": bot_en_turno.playerHand,
                            "jugadas_bajadas": bot_en_turno.jugadas_bajadas,
                            "playMade": bot_en_turno.playMade,
                            "playerId": bot_en_turno.playerId,
                            "round": ui2.round
                        }
                        ui2.network_manager.broadcast_message(msgBajarse)
                        try:
                            bajarse_sound.play()
                        except Exception as e:
                            print(f"[BOTS] {bot_en_turno.playerName}: error al reproducir sonidos de bajarse ({e}).")
                            pass
                        try:
                            voz_bajarse.play()
                        except Exception as e:
                            print(f"[BOTS] {bot_en_turno.playerName}: error al reproducir voz de bajarse ({e}).")
                            pass
                        ui2.mensaje_temporal = f"{bot_en_turno.playerName} se bajó."
                        ui2.mensaje_tiempo = time.time()
                except Exception as e:
                    print(f"[BOTS] {bot_en_turno.playerName}: error al bajarse ({e}). Se omite la bajada este turno.")

            ui2.bot_turno_estado["fase_accion"] = "pensando_insercion"
            ui2.bot_turno_estado["t"] = time.time() + BOT_DELAY_ENTRE_ACCIONES

        # --- PASO 2.5: insertar cartas en jugadas de la mesa (propias o ajenas),
        #     si el bot ya está bajado. UNA inserción por paso (no todas de
        #     golpe): así se nota visualmente cada acción por separado -por
        #     ejemplo, cuando sustituye un Joker y luego, en el SIGUIENTE
        #     paso (con su propio delay), inserta ese mismo Joker recuperado
        #     en otra jugada-. Se mantiene en esta fase, con un pequeño
        #     descanso entre intentos, hasta que ya no encuentre más
        #     inserciones válidas. ---
        elif accion == "pensando_insercion" and ahora >= ui2.bot_turno_estado["t"] and bot_en_turno.cardDrawn:
            hizo_insercion = False
            ui2.bot_turno_estado["intentos_insercion"] = ui2.bot_turno_estado.get("intentos_insercion", 0) + 1
            tope_intentos = len(bot_en_turno.playerHand) + 5  # cota de seguridad para todo el turno

            if bot_en_turno.downHand and bot_en_turno.playerHand and ui2.bot_turno_estado["intentos_insercion"] <= tope_intentos:
                try:
                    tabla = []
                    for p in ui2.players:
                        if getattr(p, "isSpectator", False):
                            continue
                        for idx_jugada, jugada in enumerate(getattr(p, "playMade", None) or []):
                            tabla.append({"owner": p, "play_index": idx_jugada, "play": jugada})

                    if tabla:
                        insercion = bot_en_turno.decide_insert_card([t["play"] for t in tabla])
                        if insercion:
                            idx_rel, carta_insertar, posicion, joker_index = insercion
                            if 0 <= idx_rel < len(tabla):
                                destino = tabla[idx_rel]
                                target_player = destino["owner"]
                                idx_jugada_real = destino["play_index"]
                                tipo_jugada = bot_en_turno._get_play_type(destino["play"])
                                subtype = "straight" if tipo_jugada == "sequence" else ("trio" if tipo_jugada == "trio" else None)

                                ok = safe_insert_card(bot_en_turno, target_player, idx_jugada_real, carta_insertar, posicion, subtype, joker_index=joker_index)
                                if ok:
                                    hizo_insercion = True
                                    ui2.mensaje_temporal = f"{bot_en_turno.playerName} insertó una carta en la mesa."
                                    ui2.mensaje_tiempo = time.time()
                                    if getattr(carta_insertar, "joker", False):
                                        if target_player.playerId not in ui2.jokers_insertados_este_turno:
                                            ui2.jokers_insertados_este_turno.append(target_player.playerId)

                                    msgInsertar = {
                                        "type": "INSERTAR_CARTA",
                                        "playerHand": bot_en_turno.playerHand,
                                        "jugadas_bajadas": getattr(target_player, "jugadas_bajadas", None),
                                        "playMade": target_player.playMade,
                                        "playerId": target_player.playerId,
                                        "playerId2": bot_en_turno.playerId,
                                        "round": ui2.round
                                    }
                                    try:
                                        if posicion is None:
                                            voz_substitute.play()
                                        else:
                                            voz_insert.play()
                                    except Exception as e:
                                        print(f"[BOTS] {bot_en_turno.playerName}: error reproduciendo sonido de inserción ({e}).")
                                    ui2.network_manager.broadcast_message(msgInsertar)
                except Exception as e:
                    print(f"[BOTS] {bot_en_turno.playerName}: error insertando cartas en la mesa ({e}).")

            if hizo_insercion:
                # Se hizo UNA inserción en este paso; se espera antes de
                # intentar la siguiente (se queda en esta misma fase).
                ui2.bot_turno_estado["t"] = time.time() + BOT_DELAY_ENTRE_ACCIONES
            else:
                ui2.bot_turno_estado["fase_accion"] = "pensando_descarte"
                ui2.bot_turno_estado["t"] = time.time() + BOT_DELAY_ENTRE_ACCIONES

        # --- PASO 3: descartar y ceder el turno al siguiente jugador ---
        elif accion == "pensando_descarte" and ahora >= ui2.bot_turno_estado["t"] and bot_en_turno.cardDrawn:
            if not bot_en_turno.playerHand:
                # Se quedó sin cartas al bajarse (p.ej. Ronda 4): no hay nada que
                # descartar, el fin de ronda se detecta solo más abajo en el bucle.
                ui2.bot_turno_estado["fase_accion"] = None
                ui2.bot_turno_estado["bot_id"] = None
            else:
                try:
                    decision = bot_en_turno.decide_discard()
                except Exception as e:
                    print(f"[BOTS] {bot_en_turno.playerName}: error decidiendo el descarte ({e}).")
                    decision = None

                seleccion = []
                if decision is not None:
                    seleccion = list(decision) if isinstance(decision, list) else [decision]
                seleccion = [c for c in seleccion if c in bot_en_turno.playerHand]
                # OJO: antes esto llamaba a can_discard(jugador_local, ...) -con el
                # jugador HUMANO en vez del bot-, así que la protección "no
                # descartar la carta que acabas de tomar del descarte" nunca
                # aplicaba de verdad para los bots (comparaba contra la
                # identidad equivocada). Ahora sí se valida contra bot_en_turno.
                if not can_discard(bot_en_turno, seleccion):
                    print(f"[BOTS] {bot_en_turno.playerName}: intentó descartar la carta que acaba de tomar del descarte. Elegirá otra.")
                    seleccion = []
                # Salvaguarda: nunca descartar un solo Joker suelto (regla del juego).
                if len(seleccion) == 1 and getattr(seleccion[0], "joker", False):
                    pareja = bot_en_turno._find_joker_burn_pair()
                    if pareja and all(c in bot_en_turno.playerHand for c in pareja) and bot_en_turno.downHand:
                        seleccion = pareja
                    else:
                        no_jokers = [c for c in bot_en_turno.playerHand if not getattr(c, "joker", False)]
                        seleccion = [min(no_jokers, key=lambda c: bot_en_turno._get_card_point_value(c))] if no_jokers else []

                if not seleccion:
                    # Al armar el respaldo, excluye la carta protegida (la que se
                    # acaba de tomar del descarte) si hay alguna otra opción,
                    # para no volver a chocar con can_discard.
                    protegida = ui2.last_taken_card if ui2.last_taken_player is bot_en_turno else None
                    no_jokers = [c for c in bot_en_turno.playerHand if not getattr(c, "joker", False)]
                    candidatos = [c for c in no_jokers if c is not protegida] or no_jokers
                    if candidatos:
                        seleccion = [min(candidatos, key=lambda c: bot_en_turno._get_card_point_value(c))]

                # Si la carta elegida le serviría a OTRO jugador ya bajado para
                # insertar de inmediato (a ti o a otro bot), busca una
                # alternativa más segura en mano antes de descartarla -no
                # tiene sentido regalar justo la carta que le hace falta a un
                # rival si hay otra opción razonable-. Se salta este chequeo
                # para el descarte doble de "quemar Joker" (seleccion de 2
                # cartas), ya que ese Joker queda fuera de alcance de todas
                # formas.
                if len(seleccion) == 1 and not getattr(seleccion[0], "joker", False):
                    try:
                        if _carta_ayuda_a_otro_jugador(bot_en_turno, seleccion[0], ui2.players):
                            protegida = ui2.last_taken_card if ui2.last_taken_player is bot_en_turno else None
                            alternativas = [
                                c for c in bot_en_turno.playerHand
                                if c is not seleccion[0] and c is not protegida
                                and not getattr(c, "joker", False)
                                and not _carta_ayuda_a_otro_jugador(bot_en_turno, c, ui2.players)
                            ]
                            if alternativas:
                                seleccion = [min(alternativas, key=lambda c: bot_en_turno._get_card_point_value(c))]
                    except Exception as e:
                        print(f"[BOTS] {bot_en_turno.playerName}: error revisando si el descarte ayuda a otro jugador ({e}).")

                cartas_descartadas_bot = bot_en_turno.discardCard(seleccion, ui2.round) if seleccion else None

                if isinstance(cartas_descartadas_bot, list) and cartas_descartadas_bot:
                    ui2.mazo_descarte = list(ui2.round.discards)

                    next_idx = None
                    for idx, p in enumerate(ui2.players):
                        if p.playerId == bot_en_turno.playerId:
                            next_idx = (idx + 1) % len(ui2.players)
                            while ui2.players[next_idx].isSpectator:
                                next_idx = (next_idx + 1) % len(ui2.players)
                                if next_idx == idx:
                                    break
                            break

                    bot_en_turno.isHand = False
                    if next_idx is not None:
                        ui2.players[next_idx].isHand = True

                    ui2.jokers_insertados_este_turno.clear()
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

                    for idx, p in enumerate(ui2.players):
                        ui2.players[idx].playerTurn = False
                        ui2.players[idx].playerPass = False
                        ui2.players[idx].cardDrawn = False
                        ui2.players[idx].discarded = False

                    ui2.cont_turnos += 1
                    msgDescarte = {
                        "type": "DESCARTE",
                        "cartas_descartadas": cartas_descartadas_bot,
                        "playerHand": bot_en_turno.playerHand,
                        "playerId": bot_en_turno.playerId,
                        "mazo_descarte": ui2.mazo_descarte,
                        "players": ui2.players,
                        "deckForRound": ui2.deckForRound,
                        "round": ui2.round
                    }
                    ui2.network_manager.broadcast_message(msgDescarte)
                    try:
                        voz_end.play()
                    except Exception as e:
                        print(f"ERROR CON LA VOZ DEL BOT EN VOZ_END: {e}")
                    ui2.mensaje_temporal = f"{bot_en_turno.playerName} descartó. Es tu turno."
                    ui2.mensaje_tiempo = time.time()

                    ui2.bot_turno_estado["fase_accion"] = None
                    ui2.bot_turno_estado["bot_id"] = None
                else:
                    print(f"[BOTS] {bot_en_turno.playerName}: no pudo descartar ({cartas_descartadas_bot}). Reintentará.")
                    # Reintenta la próxima vuelta del bucle en vez de quedar atascado.
                    ui2.bot_turno_estado["t"] = time.time() + BOT_DELAY_ENTRE_ACCIONES
    # === FIN LÓGICA AUTOMÁTICA DE TURNO PARA LOS BOTS DE IA ===

    return bot_en_turno
