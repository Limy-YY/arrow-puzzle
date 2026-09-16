import pygame
from settings import *


class BaseScene:
    """场景基类：所有场景都要继承它"""
    def __init__(self, game):
        self.game = game
        self.screen = game.screen

    def handle_event(self, event):
        """处理事件（鼠标点击、键盘按键等）"""
        pass

    def update(self, dt):
        """更新逻辑"""
        pass

    def draw(self):
        """绘制画面"""
        pass


class StartScene(BaseScene):
    """开始界面"""
    def __init__(self, game):
        super().__init__(game)
        self.font = pygame.font.Font(None, 60)
        self.small_font = pygame.font.Font(None, 30)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            # 点击任意位置切换到游戏场景（后续会改成点击按钮）
            self.game.switch_scene('game')

    def draw(self):
        # 填充深色背景
        self.screen.fill(BG_DARK)

        # 绘制标题
        title = self.font.render('Arrow Puzzle', True, TEXT_DARK_BG)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 40))
        self.screen.blit(title, title_rect)

        # 绘制提示文字
        hint = self.small_font.render('Click anywhere to start', True, TEXT_DARK_BG)
        hint_rect = hint.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 40))
        self.screen.blit(hint, hint_rect)


class GameScene(BaseScene):
    """游戏主界面（占位，后续填充）"""
    def __init__(self, game):
        super().__init__(game)
        self.font = pygame.font.Font(None, 40)

    def draw(self):
        self.screen.fill(BG_LIGHT)
        text = self.font.render('Game Scene (Coming Soon)', True, TEXT_LIGHT_BG)
        text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        self.screen.blit(text, text_rect)


class SceneManager:
    """场景管理器：负责切换和更新当前场景"""
    def __init__(self, game):
        self.game = game
        self.scenes = {
            'start': StartScene(game),
            'game': GameScene(game),
        }
        self.current_scene_name = 'start'

    @property
    def current_scene(self):
        return self.scenes[self.current_scene_name]

    def switch_scene(self, scene_name):
        """切换到指定场景"""
        if scene_name in self.scenes:
            self.current_scene_name = scene_name

    def handle_event(self, event):
        self.current_scene.handle_event(event)

    def update(self, dt):
        self.current_scene.update(dt)

    def draw(self):
        self.current_scene.draw()
