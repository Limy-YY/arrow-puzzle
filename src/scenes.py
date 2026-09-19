import pygame
import os
import math
import copy
from settings import *
from background import FloatingArrows 
import numpy as np
import random

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
    def __init__(self, game, scene_manager, font_bold, font_regular):
        super().__init__(game)
        self.scene_manager = scene_manager
        self.font_regular = font_regular
        self.font_bold = font_bold
        if FONT_PATH and os.path.exists(FONT_PATH):
            self.small_font = pygame.font.Font(FONT_PATH, 22)
        else:
            self.small_font = pygame.font.Font(None, 22)

        self.bg_arrows = FloatingArrows(count=30) 

        # 按钮区域
        self.start_btn = pygame.Rect(
            SCREEN_WIDTH // 2 - 100,
            SCREEN_HEIGHT // 2 + 20,
            200, 50
        )
        self.select_level_btn = pygame.Rect(
            SCREEN_WIDTH // 2 - 100,
            SCREEN_HEIGHT // 2 + 85,
            200, 50
        )

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.start_btn.collidepoint(event.pos):
                # 开始第一关
                game_scene = self.scene_manager.scenes['game']
                game_scene.level_index = 0
                game_scene.load_level_data()
                game_scene.game_state = 'playing'
                self.scene_manager.switch_scene('game')
            elif self.select_level_btn.collidepoint(event.pos):
                level_select_scene = self.game.scene_manager.scenes['level_select']
                level_select_scene.prev_scene = 'start'
                self.scene_manager.switch_scene('level_select')

    def draw(self):
        # 1. 先填充新的浅色背景
        self.screen.fill(BG_MENU)
        # 2. 更新并绘制飘动的彩色箭头
        self.bg_arrows.update()
        self.bg_arrows.draw(self.screen)
        # 3. 最后绘制标题，确保文字在最上层
        title = self.font_bold.render('Arrow Puzzle', True, TEXT_LIGHT_BG)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 40))
        self.screen.blit(title, title_rect)

        # 绘制按钮
        mouse_pos = pygame.mouse.get_pos()

        # --- Start 按钮 ---
        start_color = BTN_START
        if self.start_btn.collidepoint(mouse_pos):
            start_color = BTN_START_HOVER
        pygame.draw.rect(self.screen, start_color, self.start_btn, border_radius=8)
        pygame.draw.rect(self.screen, TEXT_LIGHT_BG, self.start_btn, width=2, border_radius=8)
        start_text = self.small_font.render("Start", True, TEXT_DARK_BG)
        start_text_rect = start_text.get_rect(center=self.start_btn.center)
        self.screen.blit(start_text, start_text_rect)

        # --- Select Level 按钮 ---
        select_color = BTN_SELECT_LEVEL
        if self.select_level_btn.collidepoint(mouse_pos):
            select_color = BTN_SELECT_LEVEL_HOVER
        pygame.draw.rect(self.screen, select_color, self.select_level_btn, border_radius=8)
        pygame.draw.rect(self.screen, TEXT_LIGHT_BG, self.select_level_btn, width=2, border_radius=8)
        select_text = self.small_font.render("Select Level", True, TEXT_DARK_BG)
        select_text_rect = select_text.get_rect(center=self.select_level_btn.center)
        self.screen.blit(select_text, select_text_rect)

class LevelSelectScene(BaseScene):
    """关卡选择界面"""
    def __init__(self, game, scene_manager, font_bold, font_regular):
        super().__init__(game)
        self.scene_manager = scene_manager
        self.prev_scene = 'start'

        self.font_bold = font_bold
        self.font_regular = font_regular
        
        # 使用 settings 中的配置
        self.num_cols = LEVEL_BTN_COLS
        self.btn_width = LEVEL_BTN_WIDTH
        self.btn_height = LEVEL_BTN_HEIGHT
        self.btn_gap = LEVEL_BTN_GAP
        
        # 创建专用字体
        font_path = FONT_PATH if (FONT_PATH and os.path.exists(FONT_PATH)) else None
        self.title_font = pygame.font.Font(font_path, LEVEL_SELECT_TITLE_FONT_SIZE)
        self.btn_font = pygame.font.Font(font_path, LEVEL_BTN_FONT_SIZE)
        
        # 计算按钮布局
        self.level_buttons = [] # 存储 (rect, level_index) 元组
        self._calculate_button_layout()
        
        # 创建返回按钮
        self.back_btn = pygame.Rect(
            SCREEN_WIDTH // 2 - 100,
            SCREEN_HEIGHT - 80,
            200, 50
        )

    def _calculate_button_layout(self):
        """根据关卡数量动态计算按钮网格布局"""
        self.level_buttons = []
        total_levels = len(self.game.levels)
        num_rows = math.ceil(total_levels / self.num_cols)
        
        # 计算网格起始位置，使其居中
        grid_width = self.num_cols * self.btn_width + (self.num_cols - 1) * self.btn_gap
        start_x = (SCREEN_WIDTH - grid_width) // 2
        start_y = 120 # 标题下方留白
        
        for i in range(total_levels):
            row, col = divmod(i, self.num_cols)
            x = start_x + col * (self.btn_width + self.btn_gap)
            y = start_y + row * (self.btn_height + self.btn_gap)
            btn_rect = pygame.Rect(x, y, self.btn_width, self.btn_height)
            self.level_buttons.append((btn_rect, i))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = event.pos
            
            # 检查是否点击了返回按钮
            if self.back_btn.collidepoint(mouse_pos):
                self.scene_manager.switch_scene(self.prev_scene)  # 返回上一个页面
                return
            
            # 检查是否点击了某个关卡按钮
            for btn_rect, level_index in self.level_buttons:
                if btn_rect.collidepoint(mouse_pos):
                    game_scene = self.scene_manager.scenes['game']
                    game_scene.level_index = level_index
                    game_scene.load_level_data()
                    game_scene.game_state = 'playing'
                    self.scene_manager.switch_scene('game')
                    return

    def draw(self):
        # 1. 绘制背景
        self.screen.fill(BG_MENU)
        
        # 2. 绘制标题
        title_text = self.title_font.render("Select Level", True, TEXT_LIGHT_BG)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, 60))
        self.screen.blit(title_text, title_rect)
        
        # 3. 绘制关卡按钮
        mouse_pos = pygame.mouse.get_pos()
        for btn_rect, level_index in self.level_buttons:
            # 悬停效果：使用预设的悬停色
            color = BTN_LEVEL
            if btn_rect.collidepoint(mouse_pos):
                color = BTN_LEVEL_HOVER
            
            pygame.draw.rect(self.screen, color, btn_rect, border_radius=8)
            pygame.draw.rect(self.screen, TEXT_LIGHT_BG, btn_rect, width=2, border_radius=8)
            
            # 绘制关卡数字
            level_num = level_index + 1
            text_surface = self.btn_font.render(str(level_num), True, TEXT_DARK_BG)
            text_rect = text_surface.get_rect(center=btn_rect.center)
            self.screen.blit(text_surface, text_rect)
            
        # 4. 绘制返回按钮
        color = BTN_BACK
        if self.back_btn.collidepoint(mouse_pos):
            color = BTN_BACK_HOVER # 使用预设的悬停色
            
        pygame.draw.rect(self.screen, color, self.back_btn, border_radius=8)
        pygame.draw.rect(self.screen, TEXT_LIGHT_BG, self.back_btn, width=2, border_radius=8)

        back_text = self.btn_font.render("Back", True, TEXT_LIGHT_BG)
        back_text_rect = back_text.get_rect(center=self.back_btn.center)
        self.screen.blit(back_text, back_text_rect)

class GameScene(BaseScene):
    """游戏主界面"""
    
    def __init__(self, game, font_bold, font_regular):
        super().__init__(game)
        self.level_index = 0
        self.game = game
        self.pending_click = None
        
        # 1. 初始化所有需要的字体
        self.font_bold = font_bold
        self.font_regular = font_regular

        font_path = FONT_PATH if (FONT_PATH and os.path.exists(FONT_PATH)) else None
        self.popup_title_font = pygame.font.Font(font_path, 36)
        self.popup_title_font.set_bold(True)
        self.time_bold_font = pygame.font.Font(FONT_PATH, POPUP_TIME_BOLD_FONT_SIZE)
        self.time_bold_font.set_bold(True)  # 开启加粗
        self.ui_font = pygame.font.Font(font_path, UI_FONT_SIZE)
        self.btn_font = pygame.font.Font(font_path, BTN_FONT_SIZE)
        self.small_font = pygame.font.Font(font_path, 24) 

        # === 底部控制按钮 ===
        btn_w, btn_h = 140, 40
        btn_y = SCREEN_HEIGHT - 60
        btn_w = 100
        btn_h = 40
        gap = 5  # 按钮间距

        # 计算三个按钮的总宽度和起始 x 坐标
        total_width = btn_w * 3 + gap * 2
        start_x = (SCREEN_WIDTH - total_width) // 2

        self.return_btn = pygame.Rect(start_x, btn_y, btn_w, btn_h)
        self.restart_btn = pygame.Rect(start_x + btn_w + gap, btn_y, btn_w, btn_h)
        self.select_btn = pygame.Rect(start_x + (btn_w + gap) * 2, btn_y, btn_w, btn_h)

        # === 晃动动画状态 ===
        self.shaking_arrow = None      # 当前晃动的箭头坐标 (row, col)
        self.shake_timer = 0           # 晃动剩余时间（秒）
        self.shake_intensity = 4       # 晃动幅度（像素）
        self.shake_frequency = 30      # 晃动频率（Hz，控制正弦波速度）
        self.shake_should_check_game_over = False

        # === 游戏状态管理 ===
        # 状态分为 'playing' (游戏中), 'won' (通关), 'lost' (失败)
        self.game_state = 'playing'

        # === 计时器相关属性 ===
        self.time_limit = 0          # 关卡总时间限制（秒）
        self.time_remaining = 0.0    # 剩余时间（秒）
        self.timer_running = False   # 计时器是否正在运行
        self.level_time_used = 0     # 本关通关用时（秒）

        # === 弹窗按钮 Rect ===
        # 弹窗尺寸
        self.popup_width = 300
        self.popup_height = 200
        # 弹窗居中坐标
        self.popup_x = (SCREEN_WIDTH - self.popup_width) // 2
        self.popup_y = (SCREEN_HEIGHT - self.popup_height) // 2

        btn_width = 130
        btn_height = 45
        center_x = SCREEN_WIDTH // 2
        gap = 5  # 两个按钮之间的间距
        self.popup_left_btn = pygame.Rect(
            center_x - gap - btn_width,
            self.popup_y + self.popup_height - btn_height - 20,
            btn_width,
            btn_height
        )
        self.popup_right_btn = pygame.Rect(
            center_x + gap,
            self.popup_y + self.popup_height - btn_height - 20,
            btn_width,
            btn_height
        )

        # === 加载顶部状态栏图标 ===
        self.icon_level = pygame.image.load(os.path.join(BASE_DIR, 'assets', 'icons', 'flag.png')).convert_alpha()
        self.icon_level = pygame.transform.scale(self.icon_level, (ICON_SIZE, ICON_SIZE))
        
        self.icon_arrow = pygame.image.load(os.path.join(BASE_DIR, 'assets', 'icons', 'arrow.png')).convert_alpha()
        self.icon_arrow = pygame.transform.scale(self.icon_arrow, (ICON_SIZE, ICON_SIZE))
        
        self.icon_heart = pygame.image.load(os.path.join(BASE_DIR, 'assets', 'icons', 'heart-full.png')).convert_alpha()
        self.icon_heart = pygame.transform.scale(self.icon_heart, (ICON_SIZE, ICON_SIZE))

        self.icon_heart_empty = pygame.image.load(os.path.join(BASE_DIR, 'assets', 'icons', 'heart-empty.png')).convert_alpha()
        self.icon_heart_empty = pygame.transform.scale(self.icon_heart_empty, (ICON_SIZE, ICON_SIZE))

        self.icon_clock = pygame.image.load(os.path.join(BASE_DIR, 'assets', 'icons', 'clock.png')).convert_alpha()
        self.icon_clock = pygame.transform.scale(self.icon_clock, (ICON_SIZE, ICON_SIZE))

        # === 移动动画配置 ===
        self.move_speed = 600  # 像素/秒，可以调整这个值来改变箭头飞行速度

        # === 移动状态追踪 ===
        # 用于存储正在移动的箭头信息，结构为：
        # {'start_pos': (row, col), 'current_pos': (x, y), 'direction': dir}
        self.moving_arrow = None
        self.hover_cell = None

        # 初始化关卡数据
        self.load_level_data()

        # 预生成每种方向箭头的碰撞掩码（必须在 load_level_data 之后，确保 arrow_images 已加载）
        self.arrow_masks = {}
        for direction in [DIR_UP, DIR_DOWN, DIR_LEFT, DIR_RIGHT]:
            self.arrow_masks[direction] = pygame.mask.from_surface(self.arrow_images[direction])

    def load_level_data(self):
        """提取当前关卡的网格和尺寸，并计算布局参数"""
        if self.level_index >= len(self.game.levels):
            self.level_index = len(self.game.levels) - 1
            
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

        # 初始化计时器
        self.time_limit = self.level_data.get('time_limit', 60)  # 默认60秒
        self.time_remaining = float(self.time_limit)
        self.timer_running = True

    def check_level_target(self):
        """
        检查当前关卡目标是否达成
        通关条件：所有箭头都已发出
        """
        # 1. 检查所有箭头是否都已消除
        arrows_cleared = len(self.placed_arrows) >= self.max_arrows
        
        # 2. 检查时间是否耗尽
        time_up = self.time_remaining <= 0
        
        # 只有当箭头全部消除且时间未耗尽时，才算达成目标
        return arrows_cleared and not time_up
    
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos

            # 1. === 弹窗按钮优先处理 ===
            if self.game_state in ('won', 'lost', 'all_completed'):
                if self.popup_left_btn.collidepoint(event.pos):
                    if self.game_state == 'won':
                        self.game.scene_manager.reset_to_start()
                    elif self.game_state == 'all_completed':
                        self.game.scene_manager.switch_scene('level_select')
                    else:
                        self.game.scene_manager.reset_to_start()
                    return

                if self.popup_right_btn.collidepoint(event.pos):
                    if self.game_state == 'won':
                        self.level_index += 1
                        self.load_level_data()
                        self.game_state = 'playing'
                    elif self.game_state == 'lost':
                        self.load_level_data()
                        self.game_state = 'playing'
                    else:
                        self.game.scene_manager.reset_to_start()
                    return

                # 弹窗状态下，非弹窗按钮区域点击全部忽略
                return

            # 2. === 底部按钮处理（仅在 playing 状态下有效）===
            if self.return_btn.collidepoint(event.pos):
                self.game.scene_manager.switch_scene('start')
                return

            if self.restart_btn.collidepoint(event.pos):
                self.load_level_data()
                self.game_state = 'playing'
                return

            if self.select_btn.collidepoint(event.pos):
                level_select_scene = self.game.scene_manager.scenes['level_select']
                level_select_scene.prev_scene = 'game'
                self.game.scene_manager.switch_scene('level_select')
                return

            # 3. 游戏未结束时，处理棋盘点击
            for r in range(self.rows):
                for c in range(self.cols):
                    cell_x = self.offset_x + c * (self.cell_size + CELL_GAP)
                    cell_y = self.offset_y + r * (self.cell_size + CELL_GAP)
                    cell_rect = pygame.Rect(cell_x, cell_y, self.cell_size, self.cell_size)

                    if cell_rect.collidepoint(mx, my):
                        if self.grid_map[r][c] != 0:
                            if self.moving_arrow is None:
                                # 当前无动画，直接放置
                                start_px = cell_x + self.cell_size // 2
                                start_py = cell_y + self.cell_size // 2
                                self.moving_arrow = {
                                    'start_pos': (r, c),
                                    'current_pos': (start_px, start_py),
                                    'direction': self.grid_map[r][c]
                                }
                            else:
                                # 有动画正在播放，排队等待（只保留最后一次点击）
                                self.pending_click = (r, c)
                            return

    def get_arrow_status(self, row, col):
        """
        【侦探】检查指定位置箭头的路径状态。
        只负责检测，不修改任何游戏状态。
        返回: 'clear' (路径畅通), 'blocked' (路径被阻挡), 'invalid' (空格子)
        """
        if self.grid_map[row][col] == 0:
            return 'invalid'
            
        direction = self.grid_map[row][col]
        dr = {DIR_UP: -1, DIR_DOWN: 1, DIR_LEFT: 0, DIR_RIGHT: 0}
        dc = {DIR_UP: 0, DIR_DOWN: 0, DIR_LEFT: -1, DIR_RIGHT: 1}
        
        current_r = row + dr[direction]
        current_c = col + dc[direction]
        
        # 沿着方向检查路径
        while 0 <= current_r < self.rows and 0 <= current_c < self.cols:
            if self.grid_map[current_r][current_c] != 0:
                # 发现前方有箭头阻挡
                return 'blocked'
            current_r += dr[direction]
            current_c += dc[direction]
            
        # 成功飞出棋盘边界
        return 'clear'

    def check_arrow_path(self, status, row, col):
        """
        【执行官】根据路径状态执行相应的逻辑（消除、晃动、判定胜负）。
        参数:
            status: 'clear' 或 'blocked'
            row, col: 箭头的起始坐标
        """
        if status == 'clear':
            # --- 路径畅通：消除箭头 ---
            self.grid_map[row][col] = 0
            print(f"✅ 消除！({row},{col}) 飞出棋盘。")
            
            # 判定胜利
            arrows_remaining = any(cell != 0 for row_data in self.grid_map for cell in row_data)
            if not arrows_remaining:
                print("🎉 恭喜通关本关！等待玩家操作。")
                self.game_state = 'won'
                
        elif status == 'blocked':
            # --- 路径被阻挡：触发晃动 + 计数 ---
            self.shaking_arrow = (row, col)
            self.shake_timer = 0.3
            self.mistake_count += 1
            print(f"❌ 碰撞！({row},{col}) 路径被阻挡。")
            
            # 修改：先不切 game_state，等晃动播完再判定
            self.shake_should_check_game_over = True

    def update(self, dt):
        """更新场景逻辑"""
        # 获取鼠标绝对坐标
        self.mouse_pos = pygame.mouse.get_pos()

        # === 新增：计时器逻辑 ===
        if self.timer_running and self.game_state == 'playing':
            self.time_remaining -= dt
            if self.time_remaining <= 0:
                self.time_remaining = 0
                self.timer_running = False
                self.game_state = 'lost'
                print("⏰ 时间到！游戏失败。")

        # === 检测鼠标悬停的单元格 ===
        self.hover_cell = None
        if self.game_state == 'playing':
            mx, my = self.mouse_pos
            for r in range(self.rows):
                for c in range(self.cols):
                    cell_x = self.offset_x + c * (self.cell_size + CELL_GAP)
                    cell_y = self.offset_y + r * (self.cell_size + CELL_GAP)
                    cell_rect = pygame.Rect(cell_x, cell_y, self.cell_size, self.cell_size)
                    if cell_rect.collidepoint(mx, my):
                        self.hover_cell = (r, c)
                        break
                if self.hover_cell is not None:
                    break

        # 处理箭头移动动画
        if self.moving_arrow is not None and self.game_state == 'playing':
            self._update_moving_arrow(dt)

        # 更新晃动动画计时器
        if self.shake_timer > 0:
            self.shake_timer -= dt
            if self.shake_timer <= 0:
                self.shake_timer = 0

                # 晃动播完后，再判定是否 Game Over
                if getattr(self, "shaking_arrow", None) is not None:
                    self.shaking_arrow = None

                if getattr(self, "shake_should_check_game_over", False):
                    self.shake_should_check_game_over = False

                    if self.mistake_count >= self.max_mistakes:
                        print("❌ 游戏失败！等待玩家操作。")
                        self.game_state = 'lost'

        # 1. 检查关卡目标是否达成
        level_target_met = self.check_level_target()
        
        # 2. 根据目标达成情况判定游戏状态
        if level_target_met:
            # 目标达成，玩家胜利
            self.timer_running = False  # 停止计时
            self.level_time_used = self.time_limit - int(self.time_remaining)  # 记录用时
            if self.level_index >= len(self.game.levels) - 1:
                self.game_state = 'all_completed'  # 最后一关，特殊通关状态
            else:
                self.game_state = 'won'  # 普通通关状态

    def _update_moving_arrow(self, dt):
        """处理移动中箭头的逻辑"""
        arrow = self.moving_arrow
        start_row, start_col = arrow['start_pos']
        direction = arrow['direction']
        
        # 1. 更新位置
        move_distance = self.move_speed * dt
        curr_x, curr_y = arrow['current_pos']
        
        if direction == DIR_UP:
            curr_y -= move_distance
        elif direction == DIR_DOWN:
            curr_y += move_distance
        elif direction == DIR_LEFT:
            curr_x -= move_distance
        elif direction == DIR_RIGHT:
            curr_x += move_distance
            
        arrow['current_pos'] = (curr_x, curr_y)

        # 2. 计算移动箭头的包围盒和掩码
        moving_img = self.arrow_images[direction]
        moving_mask = self.arrow_masks[direction]
        moving_w, moving_h = moving_img.get_size()
        moving_left = curr_x - moving_w // 2
        moving_top = curr_y - moving_h // 2

        # 3. 沿移动方向扫描，找到第一个有箭头的格子
        dr = {DIR_UP: -1, DIR_DOWN: 1, DIR_LEFT: 0, DIR_RIGHT: 0}
        dc = {DIR_UP: 0, DIR_DOWN: 0, DIR_LEFT: -1, DIR_RIGHT: 1}
        
        target_r, target_c = None, None
        for step in range(1, max(self.rows, self.cols)):
            check_r = start_row + dr[direction] * step
            check_c = start_col + dc[direction] * step
            
            # 超出棋盘边界，停止扫描
            if not (0 <= check_r < self.rows and 0 <= check_c < self.cols):
                break
            
            # 找到第一个有箭头的格子
            if self.grid_map[check_r][check_c] != 0:
                target_r, target_c = check_r, check_c
                break
        
        # 4. 如果找到了目标箭头，做像素级碰撞检测
        if target_r is not None:
            other_dir = self.grid_map[target_r][target_c]
            
            # 计算静止箭头的像素位置
            other_x = self.offset_x + target_c * (self.cell_size + CELL_GAP) + self.cell_size // 2
            other_y = self.offset_y + target_r * (self.cell_size + CELL_GAP) + self.cell_size // 2
            
            other_img = self.arrow_images[other_dir]
            other_mask = self.arrow_masks[other_dir]
            other_w, other_h = other_img.get_size()
            other_left = other_x - other_w // 2
            other_top = other_y - other_h // 2
            
            # 像素级碰撞检测
            offset_x = int(moving_left - other_left)
            offset_y = int(moving_top - other_top)
            
            overlap_point = moving_mask.overlap(other_mask, (offset_x, offset_y))
            
            if overlap_point is not None:
                self.check_arrow_path('blocked', start_row, start_col)
                self._try_next_pending_arrow()
                return

        # 5. 边界检测：判断是否完全飞出屏幕
        half_w = moving_w // 2
        half_h = moving_h // 2
        arrow_left = curr_x - half_w
        arrow_right = curr_x + half_w
        arrow_top = curr_y - half_h
        arrow_bottom = curr_y + half_h
        
        if direction == DIR_UP and arrow_bottom < 0:
            self.placed_arrows.append((start_row, start_col, direction))  # 改为增加已放置计数
            self.check_arrow_path('clear', start_row, start_col)
            self._try_next_pending_arrow()
        elif direction == DIR_DOWN and arrow_top > SCREEN_HEIGHT:
            self.placed_arrows.append((start_row, start_col, direction))
            self.check_arrow_path('clear', start_row, start_col)
            self._try_next_pending_arrow()
        elif direction == DIR_LEFT and arrow_right < 0:
            self.placed_arrows.append((start_row, start_col, direction))
            self.check_arrow_path('clear', start_row, start_col)
            self._try_next_pending_arrow()
        elif direction == DIR_RIGHT and arrow_left > SCREEN_WIDTH:
            self.placed_arrows.append((start_row, start_col, direction))
            self.check_arrow_path('clear', start_row, start_col)
            self._try_next_pending_arrow()

    def draw(self):
        """清屏 -> 绘制背景 -> 绘制棋盘 -> 绘制UI -> 绘制弹窗"""
        # 1. 仅清屏一次，使用统一的基础背景色
        self.game.screen.fill(BG_LIGHT)
        
        # 2. 绘制棋盘
        self._draw_board()

        # 3. 绘制悬停阴影 (保留你原有的优秀细节)
        if self.hover_cell is not None and self.game_state == 'playing':
            r, c = self.hover_cell
            cell_x = self.offset_x + c * (self.cell_size + CELL_GAP)
            cell_y = self.offset_y + r * (self.cell_size + CELL_GAP)
            hover_rect = pygame.Rect(cell_x, cell_y, self.cell_size, self.cell_size)
            
            shadow_surface = pygame.Surface((self.cell_size, self.cell_size), pygame.SRCALPHA)
            shadow_surface.fill((100, 100, 100, 40))
            self.game.screen.blit(shadow_surface, hover_rect.topleft)
        
        # 4. 绘制正在移动的箭头 (保留你原有的平滑移动绘制逻辑)
        if self.moving_arrow is not None:
            arrow = self.moving_arrow
            direction = arrow['direction']
            pos = arrow['current_pos']
            temp_rect = pygame.Rect(0, 0, self.cell_size, self.cell_size)
            self._draw_arrow(temp_rect, direction, pos=pos)

        # 5. 绘制顶部状态栏与底部按钮
        self.draw_top_bar()
        self.draw_bottom_buttons()

        # 6. 仅在特定状态下绘制新弹窗
        if self.game_state in ('won', 'lost', 'all_completed'):
            # 通关和全通关传 True，失败传 False
            is_success = self.game_state in ('won', 'all_completed')
            self._draw_popup_overlay(is_success=is_success)

    def _draw_board(self):
        """绘制棋盘网格及箭头"""
        for r in range(self.rows):
            for c in range(self.cols):
                x = self.offset_x + c * (self.cell_size + CELL_GAP)
                y = self.offset_y + r * (self.cell_size + CELL_GAP)
                cell_rect = pygame.Rect(x, y, self.cell_size, self.cell_size)
                
                # 1. 根据行列之和判断是否绘制交替颜色，实现棋盘格效果
                if (r + c) % 2 == 0:
                    color = CELL_BG_COLOR
                else:
                    color = CELL_BG_ALT
                pygame.draw.rect(self.screen, color, cell_rect)
                
                # 2. 绘制当前格子里的箭头
                arrow_dir = self.grid_map[r][c]
                if arrow_dir != 0:
                    # === 新增：跳过正在移动的箭头所在的格子，避免重影 ===
                    if (self.moving_arrow is not None and 
                        self.moving_arrow['start_pos'] == (r, c)):
                        continue
                    # 传入 rect，让箭头绘制方法能够根据格子大小缩放
                    self._draw_arrow(cell_rect, arrow_dir, row=r, col=c)

        # 在循环结束后，绘制棋盘外边框
        board_rect = pygame.Rect(
            self.offset_x - CELL_GAP,
            self.offset_y - CELL_GAP,
            self.cols * (self.cell_size + CELL_GAP) + CELL_GAP,
            self.rows * (self.cell_size + CELL_GAP) + CELL_GAP
        )
        # 2. 绘制外层大圆角线（向外扩 3 像素，完全在棋盘外部）
        outer_rect = board_rect.inflate(10, 10)
        pygame.draw.rect(self.screen, BORDER_LINE_COLOR, outer_rect, width=2, border_radius=8)
        
        # 3. 绘制内层圆角线（紧贴棋盘边缘，同样不侵入棋盘内部）
        inner_rect = board_rect.inflate(0, 0) 
        pygame.draw.rect(self.screen, BORDER_LINE_COLOR, inner_rect, width=2, border_radius=8)

    def _draw_arrow(self, rect, direction, row=None, col=None, pos=None):
        """使用PNG图标绘制箭头，支持晃动效果并自动上色"""
        img = self.arrow_images.get(direction)
        if img is None:
            return
        
        # 计算中心坐标
        if pos is not None:
            # 如果提供了像素坐标，则使用该坐标作为中心点（用于移动动画）
            center_x, center_y = pos
        else:
            center_x = rect.centerx
            center_y = rect.centery
        
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
        
        # --- 给白色箭头图片上莫兰迪色 ---
        # 映射方向与对应的莫兰迪颜色 (复用你 settings.py 里定义的)
        color_map = {
            DIR_UP: ARROW_UP,
            DIR_DOWN: ARROW_DOWN,
            DIR_LEFT: ARROW_LEFT,
            DIR_RIGHT: ARROW_RIGHT
        }
        color = color_map.get(direction)
        
        if color:
            # 创建一个临时 Surface 用于填色
            temp_surface = pygame.Surface(img.get_size(), pygame.SRCALPHA)
            temp_surface.blit(img, (0, 0))
            # 关键步骤：使用 BLEND_RGB_MULT 模式给白色/灰色的原始图片填上莫兰迪颜色
            temp_surface.fill(color, special_flags=pygame.BLEND_RGB_MULT)
            self.screen.blit(temp_surface, img_rect)
        else:
            # 如果没有定义颜色，直接绘制原图
            self.screen.blit(img, img_rect)

    def draw_top_bar(self):
        """绘制新的浅灰色状态栏"""
        # 1. 绘制顶部浅灰背景
        top_rect = pygame.Rect(0, 0, SCREEN_WIDTH, TOP_BAR_HEIGHT)
        pygame.draw.rect(self.game.screen, STATUS_BAR_COLOR, top_rect)

        # 状态栏总宽度，分为四等份
        section_width = SCREEN_WIDTH // 4
        y_center = TOP_BAR_HEIGHT // 2

        # === 左侧：绘制关卡进度 (旗子 + 数字) ===
        current_level = self.level_index + 1
        level_text = self.ui_font.render(f"{current_level}", True, STATUS_TEXT_COLOR)
        x_level = section_width // 2 - (self.icon_level.get_width() + ICON_SPACING + level_text.get_width()) // 2
        self.game.screen.blit(self.icon_level, (x_level, y_center - self.icon_level.get_height() // 2))
        self.game.screen.blit(level_text, (x_level + self.icon_level.get_width() + ICON_SPACING, y_center - level_text.get_height() // 2))

        # === 中间偏左：绘制倒计时 (时钟图标 + 时间) ===
        # 格式化时间为 MM:SS
        minutes = int(self.time_remaining) // 60
        seconds = int(self.time_remaining) % 60
        time_str = f"{minutes:02d}:{seconds:02d}"
        
        # 根据剩余时间判断颜色
        if self.time_remaining <= TIME_WARNING_THRESHOLD:
            time_color = TIME_WARNING_COLOR
        else:
            time_color = STATUS_TEXT_COLOR
            
        time_text = self.ui_font.render(time_str, True, time_color)
        
        # 使用加载好的 clock.png 图标
        clock_icon = self.icon_clock
        
        # 计算倒计时组合的总宽度
        time_group_width = clock_icon.get_width() + ICON_SPACING + time_text.get_width()
        
        # 将倒计时区域放置在屏幕中线偏左的位置
        x_time = SCREEN_WIDTH // 2 - 60 - time_group_width // 2
        
        self.game.screen.blit(clock_icon, (x_time, y_center - clock_icon.get_height() // 2))
        self.game.screen.blit(time_text, (x_time + clock_icon.get_width() + ICON_SPACING, y_center - time_text.get_height() // 2))

        # === 中间偏右：绘制剩余步数 (箭头 + 数字) ===
        arrows_left = self.max_arrows - len(self.placed_arrows)
        arrow_text = self.ui_font.render(f"{arrows_left}", True, STATUS_TEXT_COLOR)
        x_arrow = (SCREEN_WIDTH // 2 + 40) - (self.icon_arrow.get_width() + ICON_SPACING + arrow_text.get_width()) // 2
        # 直接绘制原图，不进行任何染色
        self.game.screen.blit(self.icon_arrow, (x_arrow, y_center - self.icon_arrow.get_height() // 2))
        self.game.screen.blit(arrow_text, (x_arrow + self.icon_arrow.get_width() + ICON_SPACING, y_center - arrow_text.get_height() // 2))

        # === 右侧：绘制生命值 (实心/空心爱心) ===
        hearts_container_w = self.max_mistakes * (self.icon_heart.get_width() + 4)
        
        # 将生命值区域放置在屏幕最右侧，留出 20 像素的右边距
        x_hearts_start = SCREEN_WIDTH - 20 - hearts_container_w
        
        for i in range(self.max_mistakes):
            pos_x = x_hearts_start + i * (self.icon_heart.get_width() + 4)
            pos_y = y_center - self.icon_heart.get_height() // 2
            # 判断绘制实心还是空心爱心
            if i < (self.max_mistakes - self.mistake_count):
                # 剩余生命，绘制实心爱心
                self.game.screen.blit(self.icon_heart, (pos_x, pos_y))
            else:
                # 已失去生命，绘制空心爱心
                if hasattr(self, 'icon_heart_empty'):
                    self.game.screen.blit(self.icon_heart_empty, (pos_x, pos_y))

    def draw_bottom_buttons(self):
        """绘制底部控制按钮（Return + Restart + Select）"""
        # 1. 绘制底部浅灰背景
        bottom_rect = pygame.Rect(0, SCREEN_HEIGHT - BOTTOM_BAR_HEIGHT, SCREEN_WIDTH, BOTTOM_BAR_HEIGHT)
        pygame.draw.rect(self.game.screen, STATUS_BAR_COLOR, bottom_rect)

        # 2. 更新三个按钮的位置（水平居中排列）
        btn_w, btn_h = self.restart_btn.size
        gap = 15
        total_width = btn_w * 3 + gap * 2
        start_x = (SCREEN_WIDTH - total_width) // 2
        btn_y = SCREEN_HEIGHT - BOTTOM_BAR_HEIGHT + (BOTTOM_BAR_HEIGHT - btn_h) // 2

        self.return_btn.topleft = (start_x, btn_y)
        self.restart_btn.topleft = (start_x + btn_w + gap, btn_y)
        self.select_btn.topleft = (start_x + (btn_w + gap) * 2, btn_y)

        # 3. 弹窗状态下，所有按钮显示为禁用态
        is_disabled = self.game_state != 'playing'

        if is_disabled:
            # 禁用态：统一灰色，无悬停、无边框
            disabled_color = HEART_EMPTY_COLOR
            disabled_text_color = TEXT_DARK_BG

            for btn, text in [(self.return_btn, "Return"),
                            (self.restart_btn, "Restart"),
                            (self.select_btn, "Select")]:
                pygame.draw.rect(self.game.screen, disabled_color, btn, border_radius=8)
                btn_text = self.btn_font.render(text, True, disabled_text_color)
                btn_text_rect = btn_text.get_rect(center=btn.center)
                self.game.screen.blit(btn_text, btn_text_rect)
            return  # 禁用态直接返回，不执行后续正常态绘制

        # 4. 获取鼠标位置用于悬停检测
        mouse_pos = pygame.mouse.get_pos()

        # 5. 绘制 Return 按钮
        return_color = BTN_BACK
        if self.return_btn.collidepoint(mouse_pos):
            return_color = return_color.lerp(pygame.Color('white'), 0.2)
        pygame.draw.rect(self.game.screen, return_color, self.return_btn, border_radius=8)
        pygame.draw.rect(self.game.screen, pygame.Color('#C0C0C0'), self.return_btn, 2, border_radius=8)
        return_text = self.btn_font.render("Return", True, TEXT_LIGHT_BG)
        return_text_rect = return_text.get_rect(center=self.return_btn.center)
        self.game.screen.blit(return_text, return_text_rect)

        # 6. 绘制 Restart 按钮
        restart_color = BTN_RESTART
        if self.restart_btn.collidepoint(mouse_pos):
            restart_color = restart_color.lerp(pygame.Color('white'), 0.2)
        pygame.draw.rect(self.game.screen, restart_color, self.restart_btn, border_radius=8)
        pygame.draw.rect(self.game.screen, pygame.Color('#C0C0C0'), self.restart_btn, 2, border_radius=8)
        restart_text = self.btn_font.render("Restart", True, TEXT_LIGHT_BG)
        restart_text_rect = restart_text.get_rect(center=self.restart_btn.center)
        self.game.screen.blit(restart_text, restart_text_rect)

        # 7. 绘制 Select 按钮
        select_color = BTN_SELECT_LEVEL
        if self.select_btn.collidepoint(mouse_pos):
            select_color = select_color.lerp(pygame.Color('white'), 0.2)
        pygame.draw.rect(self.game.screen, select_color, self.select_btn, border_radius=8)
        pygame.draw.rect(self.game.screen, pygame.Color('#C0C0C0'), self.select_btn, 2, border_radius=8)
        select_text = self.btn_font.render("Select", True, TEXT_LIGHT_BG)
        select_text_rect = select_text.get_rect(center=self.select_btn.center)
        self.game.screen.blit(select_text, select_text_rect)

    def _draw_popup_overlay(self, is_success=True):
        """
        极简氛围版：半透明遮罩 + 中心放射柔光
        参数 is_success: True为通关(暖色光), False为失败(灰色光)
        """
        # 0. 绘制半透明遮罩（根据状态切换颜色）
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        if is_success:
            # 通关：保留之前的灰蓝色
            overlay.fill((111, 119, 136)) 
            overlay.set_alpha(160)
        else:
            # 失败：压暗的冷灰色，营造遗憾感
            overlay.fill((100, 100, 100)) 
            overlay.set_alpha(180)
        
        self.screen.blit(overlay, (0, 0))

        # 1. 创建独立的光效图层
        fx_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)

        # 2. 绘制中心放射光束（根据状态切换颜色和长度）
        center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        
        if is_success:
            max_beam_length = 200
            beam_color = BEAM_CENTER_COLOR  # 使用原定的通关暖色
        else:
            max_beam_length = 200           # 失败时缩短光束长度
            beam_color = (210, 210, 210)    # 设置为清冷的灰色
        
        num_beams = 16         # 光束数量
        
        # 使用三角函数计算每一道光束的形状
        for i in range(num_beams):
            angle_rad = math.radians((i / num_beams) * 360)
            segments = 40  # 将每道光束切分成40段，实现平滑渐变
            
            for j in range(segments):
                ratio_start = j / segments
                ratio_end = (j + 1) / segments
                dist_start = max_beam_length * ratio_start
                dist_end = max_beam_length * ratio_end

                # 从中心向外，透明度逐渐降低至完全透明
                current_alpha = int(180 * (1 - ratio_end)) 
                if current_alpha <= 0: 
                    continue

                # 从中心向外，光束逐渐变宽
                width_start = 2 + 25 * ratio_start 
                width_end = 2 + 25 * ratio_start
                
                cos_a = math.cos(angle_rad)
                sin_a = math.sin(angle_rad)

                # 计算四边形的四个顶点
                px_start = -width_start * sin_a
                py_start = width_start * cos_a
                p1 = (center[0] + dist_start * cos_a + px_start, center[1] + dist_start * sin_a + py_start)
                p2 = (center[0] + dist_start * cos_a - px_start, center[1] + dist_start * sin_a - py_start)

                px_end = -width_end * sin_a
                py_end = width_end * cos_a
                p3 = (center[0] + dist_end * cos_a + px_end, center[1] + dist_end * sin_a + py_end)
                p4 = (center[0] + dist_end * cos_a - px_end, center[1] + dist_end * sin_a - py_end)

                # 使用对应的颜色绘制光束
                pygame.draw.polygon(fx_surface, (*beam_color, current_alpha), [p1, p3, p4, p2])

        # 3. 将绘制好的光效图层一次性贴到主屏幕
        self.screen.blit(fx_surface, (0, 0))

        # 3. 绘制弹窗主体
        popup_rect = pygame.Rect(self.popup_x, self.popup_y, self.popup_width, self.popup_height)

        # 绘制白底和边框
        pygame.draw.rect(self.screen, BG_LIGHT, popup_rect, border_radius=16)
        pygame.draw.rect(self.screen, BG_DARK, popup_rect, width=2, border_radius=16)

        # 4. 绘制文本内容（保留原有的动态逻辑）
        if self.game_state == 'all_completed':
            title_text = "Level Complete!!"
            subtitle_text = f"Time: {self.level_time_used}s!"
            title_color = POPUP_TITLE_ALL_COMPLETED
        elif self.game_state == 'won':
            title_text = "Level Complete!"
            subtitle_text = f"Time: {self.level_time_used}s"
            title_color = POPUP_TITLE_WON
        else:  # lost
            title_text = "Game Over"
            subtitle_text = "Don't give up, try again!"
            title_color = POPUP_TITLE_LOST

        title_surface = self.popup_title_font.render(title_text, True, title_color)
        title_rect = title_surface.get_rect(center=(SCREEN_WIDTH // 2, self.popup_y + 45))
        self.screen.blit(title_surface, title_rect)

        # 失败界面：保持原样，一行小字
        if self.game_state == 'lost':
            subtitle_surface = self.small_font.render(subtitle_text, True, STATUS_TEXT_COLOR)
            subtitle_rect = subtitle_surface.get_rect(center=(SCREEN_WIDTH // 2, title_rect.bottom + 15))
            self.screen.blit(subtitle_surface, subtitle_rect)
        else:
            # 通关 / 全通关界面：整体居中 + 垂直重心对齐
            time_str = f"{self.level_time_used}s"

            # 1. 渲染两部分文字
            label_surface = self.popup_title_font.render("Time:", True, title_color)
            time_surface = self.time_bold_font.render(time_str, True, title_color)

            # 2. 计算组合后的总宽度和起始 X 坐标（实现整体水平居中）
            gap = 10  # "Time:" 和数字之间的间距
            total_width = label_surface.get_width() + gap + time_surface.get_width()
            start_x = (SCREEN_WIDTH - total_width) // 2

            # 3. 确定垂直中心线（在大标题下方 60px 处）
            center_y = title_rect.bottom + 30 

            # 4. 绘制 "Time:"（从计算好的 start_x 开始，垂直中心对齐）
            label_rect = label_surface.get_rect(topleft=(start_x, 0))
            label_rect.centery = center_y  # 强制垂直居中
            self.screen.blit(label_surface, label_rect)

            # 5. 绘制数字（紧跟在 Time: 右侧，垂直中心对齐）
            time_rect = time_surface.get_rect(topleft=(label_rect.right + gap, 0))
            time_rect.centery = center_y  # 确保与 Time: 共用同一个垂直中心线
            self.screen.blit(time_surface, time_rect)

        # 5. 同步按钮位置（确保点击区域与视觉一致）
        btn_width = 130
        btn_height = 45
        center_x = SCREEN_WIDTH // 2
        gap = 5
        self.popup_left_btn.topleft = (
            center_x - gap - btn_width,
            self.popup_y + self.popup_height - btn_height - 20
        )
        self.popup_right_btn.topleft = (
            center_x + gap,
            self.popup_y + self.popup_height - btn_height - 20
        )

        # 辅助函数：绘制带悬停交互的圆角按钮
        def draw_interactive_button(rect, text, base_color):
            color = base_color
            mouse_pos = pygame.mouse.get_pos()
            if rect.collidepoint(mouse_pos):
                # 悬停时变亮
                color = color.lerp(pygame.Color('white'), 0.2)
            pygame.draw.rect(self.screen, color, rect, border_radius=8)
            pygame.draw.rect(self.screen, pygame.Color('#C0C0C0'), rect, 2, border_radius=8)
            
            btn_text_surface = self.small_font.render(text, True, TEXT_DARK_BG)
            btn_text_rect = btn_text_surface.get_rect(center=rect.center)
            self.screen.blit(btn_text_surface, btn_text_rect)

        # 6. 根据不同游戏状态绘制对应的按钮
        if self.game_state == 'all_completed':
            draw_interactive_button(self.popup_left_btn, "Select", BTN_SELECT_LEVEL)
            draw_interactive_button(self.popup_right_btn, "Return", BTN_BACK)
        elif self.game_state == 'won':
            draw_interactive_button(self.popup_left_btn, "Return", BTN_BACK)
            draw_interactive_button(self.popup_right_btn, "Next", BTN_NEXT)
        else:  # lost
            draw_interactive_button(self.popup_left_btn, "Return", BTN_BACK)
            draw_interactive_button(self.popup_right_btn, "Retry", BTN_RETRY)

    def _try_next_pending_arrow(self):
        """尝试触发排队的箭头，或清除 moving_arrow"""
        if self.pending_click:
            r, c = self.pending_click
            self.pending_click = None
            if self.grid_map[r][c] != 0:
                cell_x = self.offset_x + c * (self.cell_size + CELL_GAP)
                cell_y = self.offset_y + r * (self.cell_size + CELL_GAP)
                start_px = cell_x + self.cell_size // 2
                start_py = cell_y + self.cell_size // 2
                self.moving_arrow = {
                    'start_pos': (r, c),
                    'current_pos': (start_px, start_py),
                    'direction': self.grid_map[r][c]
                }
                return
        self.moving_arrow = None

class SceneManager:
    """场景管理器：负责切换和更新当前场景"""
    def __init__(self, game):
        self.game = game

        self.game_font_regular = None
        self.game_font_bold = None

        if FONT_PATH and os.path.exists(FONT_PATH):
            self.game_font_regular = pygame.font.Font(FONT_PATH, TITLE_FONT_SIZE)
            self.game_font_bold = pygame.font.Font(FONT_PATH, TITLE_FONT_SIZE)
            self.game_font_bold.set_bold(True)
        
        self.scenes = {
            'start': StartScene(self.game, self, self.game_font_bold, self.game_font_regular),
            'level_select': LevelSelectScene(self.game, self, self.game_font_bold, self.game_font_regular), 
            'game': GameScene(game, self.game_font_bold, self.game_font_regular),
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
