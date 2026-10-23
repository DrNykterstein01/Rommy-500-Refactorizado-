"""
ui2_end_screens.py
===================
Pantallas de resultados: puntuaciones al terminar cada ronda, la
puntuación final detallada (1er/2do/3er lugar...) y el anuncio del
ganador de la partida completa. Extraído tal cual de ui2.py.
"""
import os
import pygame
import ui2


def mostrar_puntuaciones_final(screen, fondo_img, players, WIDTH, HEIGHT, ASSETS_PATH, round_number=None):
    """
    Muestra un panel centrado que diga:
    PUNTUACIONES FINALES
    Ronda: <n>        (si round_number no es None)
    y debajo, la lista de jugadores en el orden dado.
    Ajustes: mayor espaciado y mejor centrado para que no se corte abajo.
    """
    jugadores = list(players)  # respetar orden de juego

    filas = max(1, len(jugadores))
    espacio_entre = 52        # un poco más de separación entre filas
    top_padding = 36
    bottom_padding = 40
    header_h = 120            # más espacio para título + subtítulo

    alto_rect = header_h + filas * espacio_entre + top_padding + bottom_padding
    ancho_rect = min(WIDTH - 140, 820)

    # evitar que el rect se salga de la pantalla; reducir si es necesario
    if alto_rect + 80 > HEIGHT:
        alto_rect = HEIGHT - 80
        espacio_entre = max(36, (alto_rect - header_h - top_padding - bottom_padding) // max(1, filas))

    x_rect = (WIDTH - ancho_rect) // 2
    y_rect = max(40, (HEIGHT - alto_rect) // 2)

    rect_fondo = pygame.Rect(x_rect, y_rect, ancho_rect, alto_rect)

    # Fondo semitransparente + borde
    overlay = pygame.Surface((rect_fondo.width, rect_fondo.height), pygame.SRCALPHA)
    overlay.fill((18, 18, 18, 200))
    screen.blit(overlay, rect_fondo.topleft)
    pygame.draw.rect(screen, (180, 180, 180), rect_fondo, 2, border_radius=12)

    # Fuentes (usar la fuente del juego si existe)
    title_font = ui2.get_game_font(34)
    subtitle_font = ui2.get_game_font(18)
    player_font = ui2.get_game_font(22)
    info_font = ui2.get_game_font(12)
    center_x = x_rect + ancho_rect // 2

    # Título grande centrado (con borde para legibilidad)
    title_txt = "Puntuaciones Finales"
    title_surf = title_font.render(title_txt, True, (255, 255, 255))
    title_pos = (center_x - title_surf.get_width() // 2, y_rect + 18)
    # borde simple
    for ox, oy in [(-1,0),(1,0),(0,-1),(0,1)]:
        screen.blit(title_font.render(title_txt, True, (0,0,0)), (title_pos[0] + ox, title_pos[1] + oy))
    screen.blit(title_surf, title_pos)

    # Subtítulo Ronda (si aplica) — centrado, con margen extra debajo
    players_start_y = title_pos[1] + title_surf.get_height() + 12
    if round_number is not None:
        sub_txt = f"Ronda: {round_number}"
        sub_surf = subtitle_font.render(sub_txt, True, (220, 220, 220))
        sub_pos = (center_x - sub_surf.get_width() // 2, players_start_y)
        screen.blit(sub_surf, sub_pos)
        players_start_y = sub_pos[1] + sub_surf.get_height() + 18
    else:
        players_start_y += 8

    # Lista de jugadores (centrada horizontalmente, más abajo)
    max_players_display = (alto_rect - (players_start_y - y_rect) - bottom_padding) // espacio_entre
    # si hay demasiados jugadores, ajustar espacio para que entren
    if filas > max_players_display and max_players_display > 0:
        espacio_entre = max(32, (alto_rect - (players_start_y - y_rect) - bottom_padding) // filas)

    for i, jugador in enumerate(jugadores):
        is_spec = getattr(jugador, "isSpectator", False)
        nombre = getattr(jugador, "playerName", f"Jugador {i+1}")
        puntos = getattr(jugador, "playerPoints", 0)
        
        status_text = " (ESPECTADOR)" if is_spec else ""
        color_texto = (200, 200, 200) if is_spec else (240, 240, 220)
        
        linea = f"{i+1}. {nombre}{status_text}  —  {puntos} pts"
        y_line = players_start_y + i * espacio_entre
        # centrar la línea
        surf = player_font.render(linea, True, color_texto)
        x_line = center_x - surf.get_width() // 2
        # borde ligero para contraste sin tapar fondo
        for ox, oy in [(-1,0),(1,0),(0,-1),(0,1)]:
            screen.blit(player_font.render(linea, True, (0,0,0)), (x_line + ox, y_line + oy))
        screen.blit(surf, (x_line, y_line))

    # Mensaje de instrucción al final (más abajo con margen)
    info_txt = "Iniciando Siguiente Ronda..."
    info_surf = info_font.render(info_txt, True, (190,190,190))
    info_rect = info_surf.get_rect(center=(center_x, y_rect + alto_rect - 22))
    screen.blit(info_surf, info_rect.topleft)



def mostrar_puntuacion_final_detallada(screen, fondo_img, players, WIDTH, HEIGHT, ASSETS_PATH, round_number=None):
    """
    Muestra pantalla de 'Puntuación final' con:
      1er Lugar, 2do Lugar, ...
    Ahora el 1er lugar será el jugador con MENOS puntos (orden ascendente).
    round_number: opcional, muestra "Ronda: <n>" debajo del título si se pasa.
    """
    if not players:
        return

    # ordenar por puntos ASCENDENTE => primero = menor puntaje
    jugadores_ordenados = sorted(players, key=lambda j: getattr(j, "playerPoints", 0))

    # Helper para ordinales simples en español
    def ordinal_es(n):
        if n == 1:
            return "1er"
        if n == 2:
            return "2do"
        if n == 3:
            return "3er"
        return f"{n}º"

    filas = len(jugadores_ordenados)
    padding_y = 28
    espacio_linea = 44
    header_h = 84
    alto_rect = header_h + filas * espacio_linea + padding_y * 2
    ancho_rect = min(WIDTH - 120, 720 + max(0, (filas - 4) * 24))

    x_rect = (WIDTH - ancho_rect) // 2
    y_rect = max(40, (HEIGHT - alto_rect) // 2)

    rect_fondo = pygame.Rect(x_rect, y_rect, ancho_rect, alto_rect)

    # Fondo semitransparente + borde
    overlay = pygame.Surface((rect_fondo.width, rect_fondo.height), pygame.SRCALPHA)
    overlay.fill((16, 16, 16, 220))
    screen.blit(overlay, rect_fondo.topleft)
    pygame.draw.rect(screen, (200, 200, 200), rect_fondo, 2, border_radius=10)

    # Fuentes (usar la fuente del juego)
    title_font = ui2.get_game_font(28)
    place_font = ui2.get_game_font(20)
    info_font = ui2.get_game_font(12)

    # Dibuja título con borde simple
    title_txt = "Puntuación final"
    title_surf = title_font.render(title_txt, True, (255, 255, 255))
    tx, ty = x_rect + ancho_rect // 2, y_rect + 20
    # borde
    for ox, oy in [(-1,0),(1,0),(0,-1),(0,1)]:
        screen.blit(title_font.render(title_txt, True, (0,0,0)), (tx - title_surf.get_width()//2 + ox, ty + oy))
    screen.blit(title_surf, (tx - title_surf.get_width()//2, ty))

    # Subtítulo: Ronda si se pasó
    players_start_y = ty + title_surf.get_height() + 10
    if round_number is not None:
        sub_txt = f"Ronda: {round_number}"
        sub_surf = info_font.render(sub_txt, True, (220, 220, 220))
        sub_x = x_rect + ancho_rect // 2 - sub_surf.get_width() // 2
        sub_y = players_start_y
        screen.blit(sub_surf, (sub_x, sub_y))
        players_start_y = sub_y + sub_surf.get_height() + 12

    # Listado de lugares (primero = menor puntaje)
    for i, jugador in enumerate(jugadores_ordenados):
        lugar = i + 1
        is_spec = getattr(jugador, "isSpectator", False)
        nombre = getattr(jugador, "playerName", f"Jugador {lugar}")
        puntos = getattr(jugador, "playerPoints", 0)
        
        status_text = " (ESPECTADOR)" if is_spec else ""
        color_texto = (180, 180, 180) if is_spec else (240, 240, 200)
        
        linea = f"{ordinal_es(lugar)} Lugar: {nombre}{status_text} — {puntos} pts"
        y_line = players_start_y + i * espacio_linea

        surf = place_font.render(linea, True, color_texto)
        rx = x_rect + ancho_rect // 2 - surf.get_width() // 2
        ry = y_line
        # borde ligero
        for ox, oy in [(-1,0),(1,0),(0,-1),(0,1)]:
            screen.blit(place_font.render(linea, True, (0,0,0)), (rx+ox, ry+oy))
        screen.blit(surf, (rx, ry))

    # Info para continuar (vacío o personalizado)
    info_txt = ""
    info_surf = info_font.render(info_txt, True, (200,200,200))
    info_rect = info_surf.get_rect(center=(x_rect + ancho_rect//2, y_rect + alto_rect - 18))
    screen.blit(info_surf, info_rect.topleft)


def mostrar_ganador_final(screen, fondo_img, players, WIDTH, HEIGHT, ASSETS_PATH):
    """
    Muestra una pantalla especial de 'Fin de Partida' declarando al ganador absoluto.
    """
    if not players:
        return

    # Clasificar jugadores
    activos = [p for p in players if not getattr(p, "isSpectator", False)]
    jugadores_ordenados = sorted(players, key=lambda j: getattr(j, "playerPoints", 0))

    if activos:
        ganador = sorted(activos, key=lambda j: getattr(j, "playerPoints", 0))[0]
    else:
        ganador = jugadores_ordenados[0]

    ancho_rect = min(WIDTH - 100, 850)
    alto_rect = min(HEIGHT - 100, 500)
    x_rect = (WIDTH - ancho_rect) // 2
    y_rect = (HEIGHT - alto_rect) // 2

    rect_fondo = pygame.Rect(x_rect, y_rect, ancho_rect, alto_rect)
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))
    screen.blit(overlay, (0,0))

    panel = pygame.Surface((ancho_rect, alto_rect), pygame.SRCALPHA)
    panel.fill((20, 20, 30, 230))
    screen.blit(panel, (x_rect, y_rect))
    pygame.draw.rect(screen, (255, 215, 0), rect_fondo, 4, border_radius=15)

    winner_font = ui2.get_game_font(40)
    name_font = ui2.get_game_font(30)
    ranking_font = ui2.get_game_font(18)
    info_font = ui2.get_game_font(12)
    center_x = WIDTH // 2

    title_txt = "¡GANADOR ABSOLUTO!"
    title_surf = winner_font.render(title_txt, True, (255, 255, 0))
    screen.blit(title_surf, (center_x - title_surf.get_width()//2, y_rect + 40))

    winner_name = getattr(ganador, "playerName", "Desconocido")
    name_surf = name_font.render(winner_name, True, (255, 255, 255))
    screen.blit(name_surf, (center_x - name_surf.get_width()//2, y_rect + 110))

    start_y_ranking = y_rect + 230
    for i, p in enumerate(jugadores_ordenados[:4]):
        p_name = getattr(p, "playerName", "???")
        p_pts = getattr(p, "playerPoints", 0)
        is_spec = getattr(p, "isSpectator", False)
        linea = f"{i+1}) {p_name}: {p_pts} pts"
        if is_spec: linea += " (Expulsado)"
        
        color = (255, 255, 255) if p == ganador else (180, 180, 180)
        r_surf = ranking_font.render(linea, True, color)
        screen.blit(r_surf, (center_x - r_surf.get_width()//2, start_y_ranking + i * 35))

    msg_final = "Gracias por jugar Rommy 500"
    msg_surf = info_font.render(msg_final, True, (150, 150, 150))
    screen.blit(msg_surf, (center_x - msg_surf.get_width()//2, y_rect + alto_rect - 30))

    # Botón "Salir" (mismo diseño que el del modal de Menú), justo encima del mensaje final
    btn_w, btn_h = min(ancho_rect - 40, 240), 60
    img_salir = pygame.image.load(ui2.ruta_asset_modo("salir_btn.png", ASSETS_PATH)).convert_alpha()
    img_salir = pygame.transform.smoothscale(img_salir, (btn_w, btn_h))
    btn_exit = pygame.Rect(center_x - btn_w // 2, y_rect + alto_rect - 110, btn_w, btn_h)
    screen.blit(img_salir, btn_exit.topleft)
    return btn_exit

