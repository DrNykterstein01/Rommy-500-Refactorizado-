"""
ui2_eventos.py
===============
Manejadores de los eventos de pygame del bucle principal de ui2.py (fase 2b de
la refactorización de main()). Cada función es el cuerpo de una rama del
`for event in pygame.event.get():` de siempre, movido sin cambiar la lógica.
El estado compartido con main() se lee y escribe como `ui2.NOMBRE`.
"""
import pygame

import ui2


def manejar_quit():
    """Cierre de la ventana (QUIT): avisa por red que este jugador se va."""
    if ui2.network_manager.is_host:
        msgHostLeft = {
            "type": "DESCONEXION",
            "playerId": ui2.network_manager.player_id,
            "playerName": ui2.network_manager.playerName,
            "reason": "HOST_LEFT"
        }
        ui2.network_manager.broadcast_message(msgHostLeft)
        ui2.network_manager.stop()
    else:
        if ui2.network_manager.player:
            msgSalir = {
                "type": "SALIR",
                "playerId": ui2.jugador_local.playerId,
                "playerName": ui2.jugador_local.playerName
            }
            ui2.network_manager.sendData(msgSalir)
            ui2.network_manager.stop()


def manejar_videoresize(event):
    """La ventana cambió de tamaño: recrea la superficie y reescala el fondo."""
    ui2.WIDTH, ui2.HEIGHT = event.w, event.h
    ui2.screen = pygame.display.set_mode((ui2.WIDTH, ui2.HEIGHT), pygame.RESIZABLE)
    ui2.fondo_img = ui2.cargar_fondo_juego(ui2.WIDTH, ui2.HEIGHT)


def manejar_click_derecho():
    """Click derecho: devuelve a la mano todas las cartas colocadas en las zonas."""
    for zona in ui2.zona_cartas:
        for carta in zona:
            if carta not in ui2.visual_hand:
                ui2.visual_hand.append(carta)
    ui2.zona_cartas = [[], [], [],[]]
    ui2.cartas_ocultas.clear()
    ui2.organizar_habilitado = True  # Vuelve a habilitar organización
