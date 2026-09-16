import pygame
import json
import os
import sys
from settings import *
from scenes import SceneManager

# 获取项目根目录的绝对路径（跨平台兼容）
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEVELS_FILE = os.path.join(BASE_DIR, 'data', 'levels.json')


def load_levels():
    """读取关卡数据"""
    try:
        with open(LEVELS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get("levels", [])
    except FileNotFoundError:
        print("错误：找不到 levels.json 文件！")
        return []
    except json.JSONDecodeError:
        print("错误：levels.json 格式有误！")
        return []


class Game:
    """游戏主类"""
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Arrow Puzzle - 箭头消消乐")
        self.clock = pygame.time.Clock()
        self.running = True

        # 加载关卡数据
        self.levels = load_levels()
        if not self.levels:
            print("未加载到关卡数据，程序退出。")
            self.running = False
            return

        print(f"成功加载 {len(self.levels)} 个关卡！")

        # 初始化场景管理器
        self.scene_manager = SceneManager(self)

    def switch_scene(self, scene_name):
        """供场景调用的切换方法"""
        self.scene_manager.switch_scene(scene_name)

    def run(self):
        """游戏主循环"""
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0  # 帧间隔时间（秒）

            # 1. 事件处理
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                self.scene_manager.handle_event(event)

            # 2. 逻辑更新
            self.scene_manager.update(dt)

            # 3. 画面渲染
            self.scene_manager.draw()
            pygame.display.flip()

        pygame.quit()
        sys.exit()


if __name__ == '__main__':
    game = Game()
    if game.running:
        game.run()
