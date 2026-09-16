import pygame
import os
from settings import *


class BaseScene:
    """场景基类：所有场景都要继承它"""
    def __init__(self, game):
        self.game = game
        self.screen = game.screen

    def handle_event(self, event):
        pass

    def update(self, dt):
        pass

    def draw(self):
        pass


class StartScene(BaseScene):
    """开始界面"""
    def __init__(self, game):
        super().__init__(game)
        self.font = pygame.font.Font(None, 60)
        self.small_font = pygame.font.Font(None, 30)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.game.switch_scene('game')

    def draw(self):
        self.screen.fill(BG_DARK)
        title = self.font.render('Arrow Puzzle', True, TEXT_DARK_BG)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 40))
        self.screen.blit(title, title_rect)
        hint = self.small_font.render('Click anywhere to start', True, TEXT_DARK_BG)
        hint_rect = hint.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 40))
        self.screen.blit(hint, hint_rect)

class GameScene(BaseScene):
    """游戏主界面"""
    
    def __init__(self, game):
        super().__init__(game)
        self.level_index = 0
        
        # 1. 初始化所有需要的字体
        self.title_font = pygame.font.Font(None, 36)
        self.ui_font = pygame.font.Font(None, UI_FONT_SIZE)
        self.btn_font = pygame.font.Font(None, BTN_FONT_SIZE)
        
        # 2. 初始化重新开始按钮区域
        btn_w, btn_h = 140, 40
        self.restart_btn = pygame.Rect(0, 0, btn_w, btn_h)
        
        # 初始化关卡数据
        self.load_level_data()

        # === 预加载箭头图标 ===
        self.arrow_images = {}
        icon_dir = os.path.join(os.path.dirname(__file__), '..', 'assets', 'icons')
        target_size = int(self.cell_size * ARROW_RATIO)
        
        for direction, name in [(DIR_UP, 'up'), (DIR_DOWN, 'down'), 
                                 (DIR_LEFT, 'left'), (DIR_RIGHT, 'right')]:
            path = os.path.join(icon_dir, f'arrow-{name}.png')
            if os.path.exists(path):
                img = pygame.image.load(path).convert_alpha()
                self.arrow_images[direction] = pygame.transform.smoothscale(
                    img, (target_size, target_size)
                )
            else:
                print(f"⚠️ 未找到图标: {path}")
        # =====================

    def load_level_data(self):
        """提取当前关卡的网格和尺寸，并计算布局参数"""
        if self.level_index >= len(self.game.levels):
            self.level_index = 0
            
        self.level_data = self.game.levels[self.level_index]
        self.cols, self.rows = self.level_data['grid_size']
        self.grid_map = self.level_data['map']
        
        # 动态计算棋盘大小（为顶部和底部UI留出空间）
        available_w = SCREEN_WIDTH - GRID_PADDING * 2
        available_h = SCREEN_HEIGHT - GRID_PADDING * 2 - TOP_BAR_HEIGHT - BOTTOM_BAR_HEIGHT
        self.cell_size = min(available_w // self.cols, available_h // self.rows)
        
        # 计算棋盘居中偏移量
        grid_w = self.cols * self.cell_size + (self.cols - 1) * CELL_GAP
        grid_h = self.rows * self.cell_size + (self.rows - 1) * CELL_GAP
        self.offset_x = (SCREEN_WIDTH - grid_w) // 2

        # 先确定可用区域的顶部和高度
        middle_area_top = TOP_BAR_HEIGHT
        middle_area_height = SCREEN_HEIGHT - TOP_BAR_HEIGHT - BOTTOM_BAR_HEIGHT

        # 在可用区域内垂直居中
        self.offset_y = middle_area_top + (middle_area_height - grid_h) // 2
        
        # 初始化游戏状态变量
        self.max_arrows = self.level_data.get('max_arrows', 0)
        self.max_mistakes = self.level_data.get('max_mistakes', 0)
        self.placed_arrows = []
        self.mistake_count = 0

    def handle_event(self, event):
        # 处理点击重新开始按钮
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.restart_btn.collidepoint(event.pos):
                self.level_index = 0
                self.load_level_data()
        pass

    def draw(self):
        screen_w, screen_h = self.screen.get_size()
        self.screen.fill(BG_LIGHT)
        
        # --- 顶部信息栏 ---
        top_bar = pygame.Rect(0, 0, screen_w, TOP_BAR_HEIGHT)
        pygame.draw.rect(self.screen, BG_DARK, top_bar)
        
        # 获取当前实时数据
        arrows_left = max(0, self.max_arrows - len(self.placed_arrows))
        mistakes_left = max(0, self.max_mistakes - self.mistake_count)
        
        # 渲染文本
        level_surf = self.ui_font.render(f"Level: {self.level_index + 1}", True, TEXT_DARK_BG)
        arrow_surf = self.ui_font.render(f"Arrows: {arrows_left}", True, TEXT_DARK_BG)
        mistake_surf = self.ui_font.render(f"Lives: {mistakes_left}", True, TEXT_DARK_BG)
        
        # 居中绘制
        bar_y = (TOP_BAR_HEIGHT - level_surf.get_height()) // 2
        self.screen.blit(level_surf, (20, bar_y))
        self.screen.blit(arrow_surf, ((screen_w - arrow_surf.get_width()) // 2, bar_y))
        self.screen.blit(mistake_surf, (screen_w - mistake_surf.get_width() - 20, bar_y))
        
        # --- 绘制棋盘 ---
        self._draw_board()
        
        # --- 底部按钮栏 ---
        bottom_bar = pygame.Rect(0, screen_h - BOTTOM_BAR_HEIGHT, screen_w, BOTTOM_BAR_HEIGHT)
        pygame.draw.rect(self.screen, BG_DARK, bottom_bar)
        
        # 动态计算按钮位置并居中
        self.restart_btn.centerx = screen_w // 2
        self.restart_btn.centery = screen_h - (BOTTOM_BAR_HEIGHT // 2)
        
        # 绘制按钮（带悬停变色效果）
        mouse_pos = pygame.mouse.get_pos()
        btn_color = BTN_NEXT if self.restart_btn.collidepoint(mouse_pos) else BTN_RESTART
        pygame.draw.rect(self.screen, btn_color, self.restart_btn, border_radius=6)
        
        btn_text = self.btn_font.render("Restart", True, TEXT_DARK_BG)
        btn_text_rect = btn_text.get_rect(center=self.restart_btn.center)
        self.screen.blit(btn_text, btn_text_rect)

    def _draw_board(self):
        """绘制棋盘网格及箭头"""
        # 绘制网格底板
        grid_w = self.cols * self.cell_size + (self.cols - 1) * CELL_GAP
        grid_h = self.rows * self.cell_size + (self.rows - 1) * CELL_GAP
        
        for r in range(self.rows):
            for c in range(self.cols):
                x = self.offset_x + c * (self.cell_size + CELL_GAP)
                y = self.offset_y + r * (self.cell_size + CELL_GAP)
                cell_rect = pygame.Rect(x, y, self.cell_size, self.cell_size)
                
                # 绘制单元格底色和边框
                pygame.draw.rect(self.screen, CELL_BG_COLOR, cell_rect)
                pygame.draw.rect(self.screen, BG_GRID, cell_rect, 1)
                
                # 绘制当前格子里的箭头
                if self.grid_map[r][c] != 0:
                    self._draw_arrow(x, y, self.grid_map[r][c])

    def _draw_arrow(self, x, y, direction):
        """使用PNG图标绘制箭头"""
        img = self.arrow_images.get(direction)
        if img is None:
            return
        
        img_rect = img.get_rect(center=(
            x + self.cell_size // 2,
            y + self.cell_size // 2
        ))
        self.screen.blit(img, img_rect)

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
        if scene_name in self.scenes:
            self.current_scene_name = scene_name

    def handle_event(self, event):
        self.current_scene.handle_event(event)

    def update(self, dt):
        self.current_scene.update(dt)

    def draw(self):
        self.current_scene.draw()
