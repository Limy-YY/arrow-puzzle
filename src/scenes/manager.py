# src/scenes/manager.py
"""场景管理器：负责切换与更新当前场景。"""
import os

import pygame

from settings import FONT_PATH, TITLE_FONT_SIZE, STATE_PLAYING, SCENE_START, SCENE_GAME, SCENE_LEVEL_SELECT
from .start import StartScene
from .level_select import LevelSelectScene
from .game import GameScene


class SceneManager:
    def __init__(self, game):
        self.game = game

        self.game_font_regular = None
        self.game_font_bold = None
        if FONT_PATH and os.path.exists(FONT_PATH):
            self.game_font_regular = pygame.font.Font(FONT_PATH, TITLE_FONT_SIZE)
            self.game_font_bold = pygame.font.Font(FONT_PATH, TITLE_FONT_SIZE)
            self.game_font_bold.set_bold(True)

        self.scenes = {
            SCENE_START: StartScene(game, self, self.game_font_bold, self.game_font_regular),
            SCENE_LEVEL_SELECT: LevelSelectScene(game, self, self.game_font_bold, self.game_font_regular),
            SCENE_GAME: GameScene(game, self.game_font_bold, self.game_font_regular),
        }
        self.current_scene_name = SCENE_START

    @property
    def current_scene(self):
        return self.scenes[self.current_scene_name]

    def switch_scene(self, scene_name):
        if scene_name in self.scenes:
            self.current_scene_name = scene_name

    def play_level(self, level_index):
        """进入指定关卡（从第一关或关卡选择界面调用）。"""
        game_scene = self.scenes[SCENE_GAME]
        game_scene.level_index = level_index
        game_scene.load_level_data()
        game_scene.game_state = STATE_PLAYING
        self.switch_scene(SCENE_GAME)

    def open_level_select(self, prev_scene):
        """打开关卡选择界面，并记录返回来源。"""
        self.scenes[SCENE_LEVEL_SELECT].prev_scene = prev_scene
        self.switch_scene(SCENE_LEVEL_SELECT)

    def handle_event(self, event):
        self.current_scene.handle_event(event)

    def update(self, dt):
        self.current_scene.update(dt)

    def draw(self):
        self.current_scene.draw()

    def reset_to_start(self):
        """返回开始界面并完全重置游戏进度。"""
        self.switch_scene(SCENE_START)
        game_scene = self.scenes[SCENE_GAME]
        game_scene.level_index = 0
        game_scene.load_level_data()
        game_scene.game_state = STATE_PLAYING
