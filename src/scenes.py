import pygame
import os
import math
import copy
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
    def __init__(self, game, font):
        super().__init__(game)
        self.font = font
        if FONT_PATH and os.path.exists(FONT_PATH):
            self.small_font = pygame.font.Font(FONT_PATH, 30)
        else:
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
    
    def __init__(self, game, font):
        super().__init__(game)
        self.level_index = 0
        
        # 1. 初始化所有需要的字体
        self.font = font
        if FONT_PATH and os.path.exists(FONT_PATH):
            self.ui_font = pygame.font.Font(FONT_PATH, UI_FONT_SIZE)
            self.btn_font = pygame.font.Font(FONT_PATH, BTN_FONT_SIZE)
        else:
            self.ui_font = pygame.font.Font(None, UI_FONT_SIZE)
            self.btn_font = pygame.font.Font(None, BTN_FONT_SIZE)

        # 2. 初始化重新开始按钮区域
        btn_w, btn_h = 140, 40
        self.restart_btn = pygame.Rect(0, 0, btn_w, btn_h)
        
        # === 晃动动画状态 ===
        self.shaking_arrow = None      # 当前晃动的箭头坐标 (row, col)
        self.shake_timer = 0           # 晃动剩余时间（秒）
        self.shake_intensity = 4       # 晃动幅度（像素）
        self.shake_frequency = 30      # 晃动频率（Hz，控制正弦波速度）

        # === 游戏状态管理 ===
        # 状态分为 'playing' (游戏中), 'won' (通关), 'lost' (失败)
        self.game_state = 'playing'

        # === 新增：弹窗按钮 Rect ===
        # 弹窗尺寸
        self.popup_width = 300
        self.popup_height = 200
        # 弹窗居中坐标
        self.popup_x = (SCREEN_WIDTH - self.popup_width) // 2
        self.popup_y = (SCREEN_HEIGHT - self.popup_height) // 2
        
        # 弹窗按钮尺寸
        popup_btn_w = 120
        popup_btn_h = 40
        # "Retry" 按钮居中偏左
        self.popup_retry_btn = pygame.Rect(
            self.popup_x + (self.popup_width - popup_btn_w * 2 - 20) // 2,
            self.popup_y + self.popup_height - 60,
            popup_btn_w, popup_btn_h
        )
        # "Next Level" 按钮居中偏右
        self.popup_next_btn = pygame.Rect(
            self.popup_x + (self.popup_width - popup_btn_w * 2 - 20) // 2 + popup_btn_w + 20,
            self.popup_y + self.popup_height - 60,
            popup_btn_w, popup_btn_h
        )

        # 初始化关卡数据
        self.load_level_data()

    def load_level_data(self):
        """提取当前关卡的网格和尺寸，并计算布局参数"""
        if self.level_index >= len(self.game.levels):
            self.level_index = 0
            
        self.level_data = self.game.levels[self.level_index]
        
        self.rows, self.cols = self.level_data['grid_size']
        self.grid_map = copy.deepcopy(self.level_data['map'])
        
        # 动态计算棋盘大小
        available_w = SCREEN_WIDTH - GRID_PADDING * 2
        available_h = SCREEN_HEIGHT - GRID_PADDING * 2 - TOP_BAR_HEIGHT - BOTTOM_BAR_HEIGHT
        self.cell_size = min(available_w // self.cols, available_h // self.rows)
        
        # 计算棋盘居中偏移量
        grid_w = self.cols * self.cell_size + (self.cols - 1) * CELL_GAP
        grid_h = self.rows * self.cell_size + (self.rows - 1) * CELL_GAP
        self.offset_x = (SCREEN_WIDTH - grid_w) // 2
        self.offset_y = TOP_BAR_HEIGHT + (SCREEN_HEIGHT - TOP_BAR_HEIGHT - BOTTOM_BAR_HEIGHT - grid_h) // 2

        # === 在此处加载并缩放箭头图片 ===
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        icon_dir = os.path.join(project_root, 'assets', 'icons')
        
        self.arrow_images = {}
        target_size = int(self.cell_size * ARROW_RATIO)
        target_size = max(target_size, 10)

        for direction, name in [(DIR_UP, 'up'), (DIR_DOWN, 'down'), (DIR_LEFT, 'left'), (DIR_RIGHT, 'right')]:
            path = os.path.join(icon_dir, f'arrow-{name}.png')
            if os.path.exists(path):
                img = pygame.image.load(path).convert_alpha()
                self.arrow_images[direction] = pygame.transform.smoothscale(img, (target_size, target_size))
            else:
                print(f"⚠️ 未找到图标: {path}")
        
        # 初始化状态
        self.max_arrows = self.level_data.get('arrows_left', 0)
        self.max_mistakes = self.level_data.get('max_failures', 0)
        self.placed_arrows = []
        self.mistake_count = 0

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos

            # 1. 底部"Restart"按钮（始终有效）
            if self.restart_btn.collidepoint(event.pos):
                self.load_level_data()
                self.game_state = 'playing'
                return

            # 2. 游戏未结束时，处理棋盘点击
            if self.game_state == 'playing':
                rel_x = mx - self.offset_x
                rel_y = my - self.offset_y
                if 0 <= rel_x < self.cols * (self.cell_size + CELL_GAP) and \
                   0 <= rel_y < self.rows * (self.cell_size + CELL_GAP):
                    grid_col = rel_x // (self.cell_size + CELL_GAP)
                    grid_row = rel_y // (self.cell_size + CELL_GAP)
                    self.check_arrow_path(grid_row, grid_col)
                return

            # 3. === 弹窗按钮处理（仅在 won/lost 状态下有效）===
            if self.game_state in ('won', 'lost'):
                # Retry 按钮：重新加载当前关卡
                if self.popup_retry_btn.collidepoint(event.pos):
                    self.load_level_data()
                    self.game_state = 'playing'
                    return

                # 第二个按钮：won → 下一关，lost → 返回主菜单
                if self.popup_next_btn.collidepoint(event.pos):
                    if self.game_state == 'won':
                        self.level_index += 1
                        self.load_level_data()
                        self.game_state = 'playing'
                    else:
                        # 返回开始界面
                        self.game.scene_manager.reset_to_start()
                    return

    def check_arrow_path(self, row, col):
        """检查点击箭头的路径是否畅通"""
        if self.grid_map[row][col] == 0:
            return
            
        direction = self.grid_map[row][col]
        dr = {DIR_UP: -1, DIR_DOWN: 1, DIR_LEFT: 0, DIR_RIGHT: 0}
        dc = {DIR_UP: 0, DIR_DOWN: 0, DIR_LEFT: -1, DIR_RIGHT: 1}
        
        current_r = row + dr[direction]
        current_c = col + dc[direction]
        
        while 0 <= current_r < self.rows and 0 <= current_c < self.cols:
            if self.grid_map[current_r][current_c] != 0:
                # --- 路径被阻挡：触发晃动 + 计数 ---
                self.shaking_arrow = (row, col)
                self.shake_timer = 0.3
                self.mistake_count += 1
                
                # 判定失败：不再自动重置，而是切换到 'lost' 状态
                if self.mistake_count >= self.max_mistakes:
                    print("❌ 游戏失败！等待玩家操作。")
                    self.game_state = 'lost'
                return # 无论是否失败，都直接返回，不再继续执行
            
            current_r += dr[direction]
            current_c += dc[direction]
            
        # --- 路径畅通：消除箭头 ---
        self.grid_map[row][col] = 0
        print(f"✅ 消除！({row},{col}) 方向{direction} 飞出棋盘。")
        
        # 判定胜利：不再自动跳关，而是切换到 'won' 状态
        arrows_remaining = any(cell != 0 for row_data in self.grid_map for cell in row_data)
        if not arrows_remaining:
            print("🎉 恭喜通关本关！等待玩家操作。")
            self.game_state = 'won'

    def update(self, dt):
        """每帧更新逻辑"""
        # 更新晃动动画计时器
        if self.shake_timer > 0:
            self.shake_timer -= dt
            if self.shake_timer <= 0:
                self.shake_timer = 0
                self.shaking_arrow = None


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

                # === 弹窗绘制（仅在 won 或 lost 状态下显示）===
        if self.game_state in ('won', 'lost'):
            # 1. 半透明遮罩
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.set_alpha(150)
            overlay.fill((0, 0, 0))
            self.screen.blit(overlay, (0, 0))

            # 2. 弹窗背景
            popup_rect = pygame.Rect(self.popup_x, self.popup_y, self.popup_width, self.popup_height)
            pygame.draw.rect(self.screen, BG_LIGHT, popup_rect, border_radius=12)
            pygame.draw.rect(self.screen, BG_DARK, popup_rect, width=2, border_radius=12)

            # 3. 标题
            title_text = "Level Complete!" if self.game_state == 'won' else "Game Over"
            title_color = ARROW_TARGET if self.game_state == 'won' else BTN_RETRY
            title = self.font.render(title_text, True, title_color)
            title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, self.popup_y + 50))
            self.screen.blit(title, title_rect)

            # 4. 按钮
            # Retry 按钮（两种状态都显示）
            pygame.draw.rect(self.screen, BTN_RETRY, self.popup_retry_btn, border_radius=8)
            retry_text = self.btn_font.render("Retry", True, TEXT_DARK_BG)
            retry_text_rect = retry_text.get_rect(center=self.popup_retry_btn.center)
            self.screen.blit(retry_text, retry_text_rect)

            # 第二个按钮：won 显示 Next Level，lost 显示 Back to Menu
            if self.game_state == 'won':
                pygame.draw.rect(self.screen, BTN_NEXT, self.popup_next_btn, border_radius=8)
                next_text = self.btn_font.render("Next", True, TEXT_DARK_BG)
                next_text_rect = next_text.get_rect(center=self.popup_next_btn.center)
                self.screen.blit(next_text, next_text_rect)
            else:
                pygame.draw.rect(self.screen, BTN_BACK, self.popup_next_btn, border_radius=8)
                back_text = self.btn_font.render("Return", True, TEXT_DARK_BG)
                back_text_rect = back_text.get_rect(center=self.popup_next_btn.center)
                self.screen.blit(back_text, back_text_rect)

    def _draw_board(self):
        """绘制棋盘网格及箭头"""
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
                    self._draw_arrow(x, y, self.grid_map[r][c], row=r, col=c)

    def _draw_arrow(self, x, y, direction, row=None, col=None):
        """使用PNG图标绘制箭头，支持晃动效果"""
        img = self.arrow_images.get(direction)
        if img is None:
            return
        
        # 计算中心坐标
        center_x = x + self.cell_size // 2
        center_y = y + self.cell_size // 2
        
        # 如果当前箭头正在晃动，计算水平偏移量
        offset_x = 0
        if (self.shaking_arrow is not None and 
            row is not None and col is not None and
            self.shaking_arrow == (row, col) and
            self.shake_timer > 0):
            # 使用正弦波产生周期性偏移
            
            progress = 1.0 - (self.shake_timer / 0.3)  # 0 → 1
            # 衰减因子：晃动逐渐减弱
            decay = 1.0 - progress
            offset_x = int(math.sin(progress * math.pi * self.shake_frequency * 0.3) 
                        * self.shake_intensity * decay)
        
        img_rect = img.get_rect(center=(center_x + offset_x, center_y))
        self.screen.blit(img, img_rect)

class SceneManager:
    """场景管理器：负责切换和更新当前场景"""
    def __init__(self, game):
        self.game = game
        self.game_font = None

        if FONT_PATH and os.path.exists(FONT_PATH):
            self.game_font = pygame.font.Font(FONT_PATH, TITLE_FONT_SIZE)
            print(f"✅ SceneManager: 成功加载全局字体 -> {FONT_PATH}")

        self.scenes = {
            'start': StartScene(game, self.game_font),
            'game': GameScene(game, self.game_font),
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

    def reset_to_start(self):
        """返回开始界面并完全重置游戏进度"""
        self.current_scene_name = 'start'
        # 获取游戏场景实例，重置关卡索引并重新加载关卡数据
        game_scene = self.scenes['game']
        game_scene.level_index = 0
        game_scene.load_level_data()
        game_scene.game_state = 'playing'
