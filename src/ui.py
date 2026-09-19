# src/ui.py
"""可复用的 UI 原语：字体加载与按钮组件。"""
import os
import pygame

from settings import FONT_PATH, HEART_EMPTY_COLOR, TEXT_DARK_BG


def load_font(size, bold=False):
    """加载 Nunito 字体，找不到时回退到系统默认字体。"""
    path = FONT_PATH if (FONT_PATH and os.path.exists(FONT_PATH)) else None
    font = pygame.font.Font(path, size)
    if bold:
        font.set_bold(True)
    return font


class Button:
    """封装矩形、文字、颜色与悬停/点击/绘制逻辑的按钮组件。

    hover_color 为 None 时，悬停效果采用 base_color 向白色渐变（lerp）；
    否则使用指定的悬停色。disabled=True 时统一绘制为灰色禁用态。
    """

    def __init__(self, rect, text, font, base_color, text_color,
                 border_color=None, hover_color=None, radius=8):
        self.rect = rect
        self.text = text
        self.font = font
        self.base_color = base_color
        self.text_color = text_color
        self.border_color = border_color
        self.hover_color = hover_color
        self.radius = radius

    def is_hovered(self):
        return self.rect.collidepoint(pygame.mouse.get_pos())

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)

    def _current_color(self):
        if self.is_hovered():
            if self.hover_color is not None:
                return self.hover_color
            return self.base_color.lerp(pygame.Color('white'), 0.2)
        return self.base_color

    def draw(self, surface, disabled=False):
        if disabled:
            pygame.draw.rect(surface, HEART_EMPTY_COLOR, self.rect, border_radius=self.radius)
            text_surf = self.font.render(self.text, True, TEXT_DARK_BG)
            surface.blit(text_surf, text_surf.get_rect(center=self.rect.center))
            return

        pygame.draw.rect(surface, self._current_color(), self.rect, border_radius=self.radius)
        if self.border_color is not None:
            pygame.draw.rect(surface, self.border_color, self.rect, width=2, border_radius=self.radius)

        text_surf = self.font.render(self.text, True, self.text_color)
        surface.blit(text_surf, text_surf.get_rect(center=self.rect.center))
