# src/scenes/level_select.py
"""关卡选择界面。"""
import math

import pygame

from settings import *
from ui import Button, load_font
from .base import BaseScene


class LevelSelectScene(BaseScene):
    def __init__(self, game, scene_manager, font_bold, font_regular):
        super().__init__(game)
        self.scene_manager = scene_manager
        self.prev_scene = SCENE_START

        self.font_bold = font_bold
        self.font_regular = font_regular

        self.num_cols = LEVEL_BTN_COLS
        self.btn_width = LEVEL_BTN_WIDTH
        self.btn_height = LEVEL_BTN_HEIGHT
        self.btn_gap = LEVEL_BTN_GAP

        self.title_font = load_font(LEVEL_SELECT_TITLE_FONT_SIZE)
        self.btn_font = load_font(LEVEL_BTN_FONT_SIZE)

        self.level_buttons = []  # 存储 (Button, level_index) 元组
        self._calculate_button_layout()

        self.back_btn = Button(
            pygame.Rect(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT - 80, 200, 50),
            "Back", self.btn_font, BTN_BACK, TEXT_LIGHT_BG,
            border_color=TEXT_LIGHT_BG, hover_color=BTN_BACK_HOVER,
        )

    def _calculate_button_layout(self):
        """根据关卡数量动态计算按钮网格布局。"""
        self.level_buttons = []
        total_levels = len(self.game.levels)
        num_rows = math.ceil(total_levels / self.num_cols)

        grid_width = self.num_cols * self.btn_width + (self.num_cols - 1) * self.btn_gap
        start_x = (SCREEN_WIDTH - grid_width) // 2
        start_y = 120  # 标题下方留白

        for i in range(total_levels):
            row, col = divmod(i, self.num_cols)
            x = start_x + col * (self.btn_width + self.btn_gap)
            y = start_y + row * (self.btn_height + self.btn_gap)
            btn_rect = pygame.Rect(x, y, self.btn_width, self.btn_height)
            button = Button(
                btn_rect, str(i + 1), self.btn_font, BTN_LEVEL, TEXT_DARK_BG,
                border_color=TEXT_LIGHT_BG, hover_color=BTN_LEVEL_HOVER,
            )
            self.level_buttons.append((button, i))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = event.pos

            if self.back_btn.is_clicked(mouse_pos):
                self.scene_manager.switch_scene(self.prev_scene)
                return

            for button, level_index in self.level_buttons:
                if button.is_clicked(mouse_pos):
                    self.scene_manager.play_level(level_index)
                    return

    def draw(self):
        self.screen.fill(BG_MENU)

        title_text = self.title_font.render("Select Level", True, TEXT_LIGHT_BG)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, 60))
        self.screen.blit(title_text, title_rect)

        for button, _ in self.level_buttons:
            button.draw(self.screen)

        self.back_btn.draw(self.screen)
