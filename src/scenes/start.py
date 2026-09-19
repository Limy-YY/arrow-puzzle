# src/scenes/start.py
"""开始界面。"""
import pygame

from settings import *
from background import FloatingArrows
from ui import Button, load_font
from .base import BaseScene


class StartScene(BaseScene):
    def __init__(self, game, scene_manager, font_bold, font_regular):
        super().__init__(game)
        self.scene_manager = scene_manager
        self.font_regular = font_regular
        self.font_bold = font_bold
        self.small_font = load_font(22)

        self.bg_arrows = FloatingArrows(count=30)

        self.start_btn = Button(
            pygame.Rect(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 20, 200, 50),
            "Start", self.small_font, BTN_START, TEXT_DARK_BG,
            border_color=TEXT_LIGHT_BG, hover_color=BTN_START_HOVER,
        )
        self.select_level_btn = Button(
            pygame.Rect(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 85, 200, 50),
            "Select Level", self.small_font, BTN_SELECT_LEVEL, TEXT_DARK_BG,
            border_color=TEXT_LIGHT_BG, hover_color=BTN_SELECT_LEVEL_HOVER,
        )

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.start_btn.is_clicked(event.pos):
                self.scene_manager.play_level(0)
            elif self.select_level_btn.is_clicked(event.pos):
                self.scene_manager.open_level_select(SCENE_START)

    def draw(self):
        self.screen.fill(BG_MENU)
        self.bg_arrows.update()
        self.bg_arrows.draw(self.screen)

        title = self.font_bold.render('Arrow Puzzle', True, TEXT_LIGHT_BG)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 40))
        self.screen.blit(title, title_rect)

        self.start_btn.draw(self.screen)
        self.select_level_btn.draw(self.screen)
