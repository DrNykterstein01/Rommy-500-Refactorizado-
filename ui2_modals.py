"""
ui2_modals.py
=============
Ventanas modales del juego (confirmaciones y menú de pausa): confirmar
salida, confirmar compra de una carta, confirmar sustitución de Joker, y el
menú de pausa (Reanudar/Salir). Cada una es su propio mini-loop bloqueante
(igual que antes de la refactorización), así que el resto del juego se
congela mientras están abiertas -mismo comportamiento de siempre-.

Extraído tal cual de ui2.py, sin cambiar lógica.
"""
import os
import time
import pygame
import ui2
from ui2_cards_render import get_card_image, draw_simple_button


def show_exit_confirmation_modal(screen, WIDTH, HEIGHT, ASSETS_PATH): 
    import pygame
    import os
    clock = pygame.time.Clock()
    
    # Capturar la pantalla de fondo para el efecto de pausa
    try:
        background_snapshot = screen.copy()
    except Exception:
        background_snapshot = pygame.Surface((WIDTH, HEIGHT))
        background_snapshot.blit(screen, (0, 0))

    # Oscurecer un poco el fondo
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 140))

    # Medidas de la ventanita de confirmación
    w, h = 500, 200
    x = (WIDTH - w) // 2
    y = (HEIGHT - h) // 2
    modal_rect = pygame.Rect(x, y, w, h)

    # Configurar botones "SÍ" y "NO"
    btn_w, btn_h = 120, 40
    btn_yes = pygame.Rect(x + 80, y + 120, btn_w, btn_h)
    btn_no = pygame.Rect(x + w - 80 - btn_w, y + 120, btn_w, btn_h)

    # Cargar la fuente pixelada del proyecto
    font_path = os.path.join(ASSETS_PATH, "PressStart2P-Regular.ttf")
    font_text = pygame.font.Font(font_path, 14)
    font_btn = pygame.font.Font(font_path, 14)

    while True:
        mouse_pos = pygame.mouse.get_pos()
        
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                return False
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                return False  # Si presiona ESC, cancela la salida
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                if btn_yes.collidepoint(mouse_pos):
                    return True   # Confirmado: quiere salir
                if btn_no.collidepoint(mouse_pos):
                    return False  # Cancelado: se queda en el juego

        # Dibujar elementos
        screen.blit(background_snapshot, (0, 0))
        screen.blit(overlay, (0, 0))

        # Cuadro base del modal
        pygame.draw.rect(screen, (40, 40, 40), modal_rect, border_radius=12)
        pygame.draw.rect(screen, (150, 150, 150), modal_rect, 2, border_radius=12)

        # Texto solicitado por el profesor (Centrado horizontalmente)
        text_surf = font_text.render(chr(191) + "Estas seguro de salir del juego?", True, (230, 230, 230))
        screen.blit(text_surf, (x + (w - text_surf.get_width()) // 2, y + 45))

        # --- BOTÓN SÍ ---
        color_yes = (192, 57, 43) if btn_yes.collidepoint(mouse_pos) else (150, 40, 40) # Hover rojo brillante
        pygame.draw.rect(screen, color_yes, btn_yes, border_radius=6)
        text_yes = font_btn.render("SI", True, (255, 255, 255))
        screen.blit(text_yes, (btn_yes.x + (btn_w - text_yes.get_width()) // 2, btn_yes.y + (btn_h - text_yes.get_height()) // 2))

        # --- BOTÓN NO ---
        color_no = (52, 152, 219) if btn_no.collidepoint(mouse_pos) else (40, 120, 180) # Hover azul brillante
        pygame.draw.rect(screen, color_no, btn_no, border_radius=6)
        text_no = font_btn.render("NO", True, (255, 255, 255))
        screen.blit(text_no, (btn_no.x + (btn_w - text_no.get_width()) // 2, btn_no.y + (btn_h - text_no.get_height()) // 2))

        pygame.display.flip()
        clock.tick(60) 


def show_menu_modal(screen, WIDTH, HEIGHT, ASSETS_PATH, ctrl_volumen):
    import pygame
    import os
    clock = pygame.time.Clock()
    
    # 1. Cargar las imágenes
    img_reanudar = pygame.image.load(ui2.ruta_asset_modo("renaudar_btn.png", ASSETS_PATH)).convert_alpha()
    img_salir = pygame.image.load(ui2.ruta_asset_modo("salir_btn.png", ASSETS_PATH)).convert_alpha()
    
    # 2. Unificar el tamaño de los botones
    btn_w, btn_h = 240, 60 
    img_reanudar = pygame.transform.smoothscale(img_reanudar, (btn_w, btn_h))
    img_salir = pygame.transform.smoothscale(img_salir, (btn_w, btn_h))

    try:
        background_snapshot = screen.copy()
    except Exception:
        background_snapshot = pygame.Surface((WIDTH, HEIGHT))
        background_snapshot.blit(screen, (0, 0))

    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 140))

    # 3. Hacer el modal más grande (400 de ancho x 360 de alto)
    w, h = 400, 360 
    x = (WIDTH - w) // 2
    y = (HEIGHT - h) // 2
    modal_rect = pygame.Rect(x, y, w, h)
    padding = 16

    # 4. Posicionar los botones centrados
    inicio_y = y + 40
    btn_resume = pygame.Rect(x + (w - btn_w) // 2, inicio_y, btn_w, btn_h)
    btn_exit = pygame.Rect(x + (w - btn_w) // 2, inicio_y + 190, btn_w, btn_h)

    # 5. DEFINIR LAS FUENTES CORRECTAMENTE (Aquí estaba el bug)
    font_path = os.path.join(ASSETS_PATH, "PressStart2P-Regular.ttf")
    title_font = pygame.font.Font(font_path, 16)
    vol_font = pygame.font.Font(font_path, 12) # <--- Variable agregada

    # 6. Centrar el control de volumen dinámicamente dentro del modal
    ancho_total_volumen = (len(ctrl_volumen.rects) * ctrl_volumen.ancho_btn) + ((len(ctrl_volumen.rects) - 1) * ctrl_volumen.espacio)
    vol_x = x + (w - ancho_total_volumen) // 2
    vol_y = inicio_y + 120
    # Actualizamos las posiciones de las barritas de volumen
    for i, rect in enumerate(ctrl_volumen.rects):
        rect.x = vol_x + (i * (ctrl_volumen.ancho_btn + ctrl_volumen.espacio))
        rect.y = vol_y

    while True:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                return "exit"
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                return "resume"
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                mx, my = ev.pos
                if btn_resume.collidepoint(mx, my):
                    return "resume"
                if btn_exit.collidepoint(mx, my):
                    return "exit"

        screen.blit(background_snapshot, (0, 0))
        screen.blit(overlay, (0, 0))

        # Dibujar caja del modal
        if ui2.MODO_OCULTO_GASTER:
            ruta_cuadro_bw = os.path.join(ASSETS_PATH, "cuadro_bw.png")
            if os.path.exists(ruta_cuadro_bw):
                cuadro_img = pygame.transform.smoothscale(pygame.image.load(ruta_cuadro_bw).convert_alpha(), (w, h))
                screen.blit(cuadro_img, modal_rect.topleft)
            else:
                pygame.draw.rect(screen, (40, 40, 40), modal_rect, border_radius=12)
        else:
            pygame.draw.rect(screen, (40, 40, 40), modal_rect, border_radius=12)
        pygame.draw.rect(screen, (150, 150, 150), modal_rect, 2, border_radius=12)

        # Dibujar Título
        title = title_font.render("Menú de Pausa", True, (230, 230, 230))
        screen.blit(title, (x + (w - title.get_width()) // 2, y + padding))

        # Dibujar Botón Reanudar
        screen.blit(img_reanudar, btn_resume.topleft)
        
        # Dibujar Texto de Volumen
        vol_text = vol_font.render("Volumen de Música", True, (200, 200, 200))
        screen.blit(vol_text, (x + (w - vol_text.get_width()) // 2, inicio_y + 90))

        # Actualizar y dibujar las barritas de volumen
        ctrl_volumen.actualizar_y_dibujar()
        
        # Dibujar Botón Salir
        screen.blit(img_salir, btn_exit.topleft)
        
        pygame.display.flip()
        clock.tick(60)

#Cambio Boton Menu / Salir


def confirm_buy_card(screen, card, WIDTH, HEIGHT, ASSETS_PATH, font):
    #def confirm_replace_joker(screen, WIDTH, HEIGHT, ASSETS_PATH):
    """
    Muestra una ventana modal que pregunta si el jugador quiere comprar la carta.
    - card: objeto Card (puede ser None para mostrar reverso).
    - Devuelve True si pulsa SI, False si pulsa NO o cierra.
    Bloqueante: procesa su propio loop hasta respuesta.
    """
    clock = pygame.time.Clock()
    # Captura del fondo actual para mostrarlo detrás del modal (asegura transparencia visual)
    try:
        background_snapshot = screen.copy()
    except Exception:
        background_snapshot = pygame.Surface((WIDTH, HEIGHT))
        background_snapshot.blit(screen, (0, 0))

    # Overlay semi-transparente (creado una vez)
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 140))  # ajuste alpha aquí (0=totalmente transparente, 255=opaco)


    #Cambio 3 (Tamaño del Rectángulo de 420,240 a 330,320)
    # Tamaños y rects
    w, h = 330, 320
    #Cambio 3

    x = (WIDTH - w)//2
    y = (HEIGHT - h)//2
    modal_rect = pygame.Rect(x, y, w, h)
    padding = 16


    #Cambio 4 (Centrar Carta)
    # Rect para imagen de carta
    card_w, card_h = 100, 150
    card_rect = pygame.Rect(x + (w - card_w)//2, y + (h - card_h)//2, card_w, card_h)
    #Cambio 4


    # Botones SI / NO
    btn_w, btn_h = 120, 44
    btn_yes = pygame.Rect(x + w - padding - btn_w, y + h - padding - btn_h, btn_w, btn_h)
    btn_no = pygame.Rect(x + w - padding - 2*btn_w - 12, y + h - padding - btn_h, btn_w, btn_h)

    # Preparar imagen de carta (usar get_card_image existente)
    try:
        if card is None:
            card_img = get_card_image("back")
        else:
            card_img = get_card_image(card)
    except Exception:
        card_img = pygame.Surface((card_w, card_h))
        card_img.fill((200,200,200))
    card_img = pygame.transform.smoothscale(card_img, (card_w, card_h))

    #Cambio 5 (Tipografía)
    #Descartamos: title_font = pygame.font.SysFont("arial", 20, bold=True)
    font_path = os.path.join(ASSETS_PATH, "PressStart2P-Regular.ttf")
    title_font = pygame.font.Font(font_path, 16)
    info_font = pygame.font.Font(font_path, 12)
    #Cambio 5


    while True:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                return False
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                return False
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                mx, my = ev.pos
                if btn_yes.collidepoint(mx, my):
                    return True
                if btn_no.collidepoint(mx, my):
                    return False

        # Dibujo del modal: primero el fondo capturado, luego overlay semi-transparente
        screen.blit(background_snapshot, (0, 0))
        screen.blit(overlay, (0, 0))

        pygame.draw.rect(screen, (40,40,40), modal_rect, border_radius=12)
        pygame.draw.rect(screen, (150,150,150), modal_rect, 2, border_radius=12)

        # Texto
        title = title_font.render("Comprar carta", True, (230,230,230))
        screen.blit(title, (x + padding, y + padding))

        
        #Cambio 6 (Separar Texto)
        info = info_font.render("¿Deseas comprar esta carta", True, (200,200,200))
        screen.blit(info, (x + padding, y + padding + 30))
        info2 = info_font.render("del descarte?", True, (200,200,200))
        screen.blit(info2, (x + padding, y + padding + 50))
        #Cambio 6


        # Dibuja la carta
        screen.blit(card_img, card_rect.topleft)
        # Mostrar nombre de carta debajo
        name_txt = info_font.render(str(card) if card is not None else "?", True, (230,230,230))
        nt = name_txt.get_rect(midtop=(card_rect.centerx, card_rect.bottom + 6))
        screen.blit(name_txt, nt)

        # Botones
        draw_simple_button(screen, btn_no, "No", info_font, bg=(120,40,40))
        draw_simple_button(screen, btn_yes, "Si", info_font, bg=(40,120,40))

        pygame.display.flip()
        clock.tick(60)
#COMPRAR CARTA'''


def confirm_exit_modal(screen, WIDTH, HEIGHT):
    clock = pygame.time.Clock()
    try:
        snapshot = screen.copy()
    except:
        snapshot = pygame.Surface((WIDTH, HEIGHT))
        
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    
    w, h = 560, 260
    x = (WIDTH - w) // 2
    y = (HEIGHT - h) // 2
    modal_rect = pygame.Rect(x, y, w, h)
    
    btn_w, btn_h = 130, 50
    btn_si = pygame.Rect(x + 80, y + 160, btn_w, btn_h)
    btn_no = pygame.Rect(x + w - btn_w - 80, y + 160, btn_w, btn_h)
    
    font_title = ui2.get_game_font(38)
    font_text = ui2.get_game_font(20)
    
    while True:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                return False
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                if btn_si.collidepoint(ev.pos):
                    return True
                if btn_no.collidepoint(ev.pos):
                    return False
                    
        screen.blit(snapshot, (0, 0))
        screen.blit(overlay, (0, 0))
        
        pygame.draw.rect(screen, (40, 40, 40), modal_rect, border_radius=12)
        pygame.draw.rect(screen, (200, 50, 50), modal_rect, 3, border_radius=12)
        
        title = font_title.render("¿SALIR?", True, (255, 255, 255))
        screen.blit(title, (x + (w - title.get_width())//2, y + 30))
        
        info = font_text.render("¿Seguro quieres salir?", True, (200, 200, 200))
        screen.blit(info, (x + (w - info.get_width())//2, y + 95))
        
        pygame.draw.rect(screen, (50, 180, 50), btn_si, border_radius=8)
        lbl_si = font_text.render("SÍ", True, (255, 255, 255))
        screen.blit(lbl_si, lbl_si.get_rect(center=btn_si.center))
        
        pygame.draw.rect(screen, (180, 50, 50), btn_no, border_radius=8)
        lbl_no = font_text.render("NO", True, (255, 255, 255))
        screen.blit(lbl_no, lbl_no.get_rect(center=btn_no.center))
        
        pygame.display.flip()
        clock.tick(60)

#CambioJoker #WhySoSerious


def confirm_joker(screen, card, WIDTH, HEIGHT, ASSETS_PATH, font):
    #def confirm_replace_joker(screen, WIDTH, HEIGHT, ASSETS_PATH):
    """
    Muestra una ventana modal que pregunta si el jugador quiere comprar la carta.
    - card: objeto Card (puede ser None para mostrar reverso).
    - font: pygame.font.Font ya creado para renderizar texto.
    Devuelve True si pulsa Si, False si pulsa No o cierra.
    Bloqueante: procesa su propio loop hasta respuesta.
    """
    clock = pygame.time.Clock()
    try:
        background_snapshot = screen.copy()
    except Exception:
        background_snapshot = pygame.Surface((WIDTH, HEIGHT))
        background_snapshot.blit(screen, (0, 0))

    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 140))

    w, h = 330, 370
    x = (WIDTH - w)//2
    y = (HEIGHT - h)//2
    modal_rect = pygame.Rect(x, y, w, h)
    padding = 16

    card_w, card_h = 100, 150
    card_rect = pygame.Rect(x + (w - card_w)//2, y + (h - card_h)//2, card_w, card_h)

    btn_w, btn_h = 140, 44
    btn_replace = pygame.Rect(x + w - padding - btn_w, y + h - padding - btn_h, btn_w, btn_h)
    btn_continue = pygame.Rect(x + w - padding - 2*btn_w - 12, y + h - padding - btn_h, btn_w, btn_h)

    # Mostrar siempre la imagen del Joker
    try:
        card_img = get_card_image(Card("Joker", "", joker=True))
    except Exception:
        card_img = pygame.Surface((card_w, card_h))
        card_img.fill((200,200,200))
    card_img = pygame.transform.smoothscale(card_img, (card_w, card_h))
    font_path = os.path.join(ASSETS_PATH, "PressStart2P-Regular.ttf")
    title_font = pygame.font.Font(font_path, 16)
    info_font = pygame.font.Font(font_path, 12)

    while True:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                return False
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                return False
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                mx, my = ev.pos
                if btn_replace.collidepoint(mx, my):
                    return True
                if btn_continue.collidepoint(mx, my):
                    return False

        screen.blit(background_snapshot, (0, 0))
        screen.blit(overlay, (0, 0))

        pygame.draw.rect(screen, (40,40,40), modal_rect, border_radius=12)
        pygame.draw.rect(screen, (150,150,150), modal_rect, 2, border_radius=12)

        title = title_font.render("Jugada con Joker", True, (230,230,230))
        screen.blit(title, (x + padding, y + padding))

        info1 = info_font.render("¿Deseas continuar la", True, (200,200,200))
        info2 = info_font.render("secuencia o reemplazar", True, (200,200,200))
        info3 = info_font.render("al Joker?", True, (200,200,200))
        screen.blit(info1, (x + padding, y + padding + 30))
        screen.blit(info2, (x + padding, y + padding + 50))
        screen.blit(info3, (x + padding, y + padding + 70))

        screen.blit(card_img, card_rect.topleft)
        name_txt = info_font.render("Joker", True, (230,230,230))
        nt = name_txt.get_rect(midtop=(card_rect.centerx, card_rect.bottom + 6))
        screen.blit(name_txt, nt)

        draw_simple_button(screen, btn_continue, "Seguir", info_font, bg=(120,40,40))
        draw_simple_button(screen, btn_replace, "Reemplazar", info_font, bg=(40,120,40))

        pygame.display.flip()
        clock.tick(60)
#CambioJoker #WhySoSerious
    
#CAMBIO 1