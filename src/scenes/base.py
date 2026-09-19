# src/scenes/base.py
"""场景基类：所有场景都要继承它。"""


class BaseScene:
    def __init__(self, game):
        self.game = game
        self.screen = game.screen

    def handle_event(self, event):
        pass

    def update(self, dt):
        pass

    def draw(self):
        pass
