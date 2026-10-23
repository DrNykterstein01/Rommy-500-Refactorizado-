"""
ui_widgets.py
=============
Widgets genéricos de interfaz reutilizados en todas las pantallas de
ui.py: el botón con imagen/hover (Button) y la caja de texto editable
(InputBox). Son clases totalmente autocontenidas -no dependen de nada de
UIManager-, así que se extrajeron tal cual, sin cambiar ninguna lógica,
simplemente para que ui.py sea más corto y más fácil de navegar.
"""
import pygame


class Button:
    def __init__(self, image, pos, text_input, font, base_color, hovering_color, size=(250, 100), scale_factor=1.1):
        self.image = image
        self.original_image = image
        self.x_pos = pos[0]
        self.y_pos = pos[1]
        self.font = font
        self.base_color = base_color
        self.hovering_color = hovering_color
        self.text_input = text_input
        self.base_size = size
        self.scale_factor = scale_factor
        self.current_size = list(size)
        self.is_hovering = False
        try:
            self.text = self.font.render(self.text_input, True, pygame.Color(self.base_color))
        except Exception:
            self.text = self.font.render(self.text_input, True, (255,255,255))
        if self.image is not None:
            self.image = pygame.transform.scale(self.original_image, self.current_size)
            self.rect = self.image.get_rect(center=(self.x_pos, self.y_pos))
        else:
            self.rect = pygame.Rect(0, 0, *self.current_size)
            self.rect.center = (self.x_pos, self.y_pos)
        self.text_rect = self.text.get_rect(center=(self.x_pos, self.y_pos))

    def _current_rect(self):
        r = pygame.Rect(0, 0, int(self.current_size[0]), int(self.current_size[1]))
        r.center = (int(self.x_pos), int(self.y_pos))
        return r

    def update(self, screen):
        target_size = [int(self.base_size[0] * (self.scale_factor if self.is_hovering else 1)),
                       int(self.base_size[1] * (self.scale_factor if self.is_hovering else 1))]
        for i in range(2):
            if abs(self.current_size[i] - target_size[i]) > 1:
                self.current_size[i] += (target_size[i] - self.current_size[i]) * 0.2
            else:
                self.current_size[i] = target_size[i]

        if self.original_image is not None:
            scaled_image = pygame.transform.scale(self.original_image, [int(x) for x in self.current_size])
            scaled_rect = scaled_image.get_rect(center=(self.x_pos, self.y_pos))
            screen.blit(scaled_image, scaled_rect)
            self.rect = scaled_rect
        else:
            self.rect = self._current_rect()
            pygame.draw.rect(screen, (255,255,255), self.rect, border_radius=8)
            pygame.draw.rect(screen, (100,100,100), self.rect, 2, border_radius=8)

        self.text_rect = self.text.get_rect(center=self.rect.center)
        screen.blit(self.text, self.text_rect)

    def checkForInput(self, position):
        try:
            return self.rect.collidepoint(position)
        except Exception:
            return False

    def changeColor(self, position):
        try:
            if self._current_rect().collidepoint(position):
                self.text = self.font.render(self.text_input, True, pygame.Color(self.hovering_color))
            else:
                self.text = self.font.render(self.text_input, True, pygame.Color(self.base_color))
        except Exception:
            if self._current_rect().collidepoint(position):
                self.text = self.font.render(self.text_input, True, (255,255,255))
            else:
                self.text = self.font.render(self.text_input, True, (200,200,200))

    def check_hover(self, position):
        was = self.is_hovering
        self.is_hovering = self._current_rect().collidepoint(position)
        if was != self.is_hovering:
            self.changeColor(position)

class InputBox:
    def __init__(self, x, y, w, h, font, text=""):
        self.rect = pygame.Rect(x, y, w, h)
        self.base_width = w
        self.color_inactive = pygame.Color("#e35d59")
        self.color_active = pygame.Color("#F9AA33")
        self.color = self.color_inactive
        self.text = text
        self.font = font
        self.padding_x = 8
        self.txt_surface = font.render(text, True, pygame.Color("#000000"))
        self.active = False
        self.clock = None

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.active = not self.active
            else:
                self.active = False
            self.color = self.color_active if self.active else self.color_inactive

        if event.type == pygame.KEYDOWN:
            if self.active:
                if event.key == pygame.K_RETURN:
                    temp_text = self.text
                    return temp_text

                elif event.key == pygame.K_BACKSPACE:
                    self.text = self.text[:-1]

                else:
                    if event.unicode:
                        self.text += event.unicode

                self.txt_surface = self.font.render(self.text, True, (0, 0, 0))

        return None

    def update(self):
        self.rect.w = self.base_width
        return

    def draw(self, screen):
        pygame.draw.rect(screen, pygame.Color("#FFFFFF"), self.rect, border_radius=12)
        pygame.draw.rect(screen, self.color, self.rect, 2, border_radius=12)
        inner_w = max(0, self.rect.w - (self.padding_x * 2))
        visible_text = self.text
        while visible_text and self.font.size(visible_text)[0] > inner_w:
            visible_text = visible_text[1:]

        text_surf = self.font.render(visible_text, True, (0, 0, 0))
        old_clip = screen.get_clip()
        screen.set_clip(self.rect)
        screen.blit(
            text_surf,
            (self.rect.x + self.padding_x, self.rect.y + (self.rect.h - text_surf.get_height()) // 2),
        )
        screen.set_clip(old_clip)

