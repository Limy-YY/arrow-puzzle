import pygame
import os
import math
import copy
from settings import *
from background import FloatingArrows 

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

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.scene_manager.switch_scene('game')

    def draw(self):
        # 1. 先填充新的浅色背景
        self.screen.fill(BG_MENU)
        # 2. 更新并绘制飘动的彩色箭头
        self.bg_arrows.update()
        self.bg_arrows.draw(self.screen)
        # 3. 最后绘制标题和提示文字，确保文字在最上层
        title = self.font_bold.render('Arrow Puzzle', True, TEXT_LIGHT_BG)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 40))
        self.screen.blit(title, title_rect)
        hint = self.small_font.render('Click anywhere to start', True, TEXT_LIGHT_BG)
        hint_rect = hint.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 40))
        self.screen.blit(hint, hint_rect)

class GameScene(BaseScene):
    """游戏主界面"""
    
    def __init__(self, game, font_bold, font_regular):
        super().__init__(game)
        self.level_index = 0
        self.game = game
        
        # 1. 初始化所有需要的字体
        self.font_bold = font_bold
        self.font_regular = font_regular

        font_path = FONT_PATH if (FONT_PATH and os.path.exists(FONT_PATH)) else None
        self.popup_title_font = pygame.font.Font(font_path, 36)
        self.popup_title_font.set_bold(True)
        self.ui_font = pygame.font.Font(font_path, UI_FONT_SIZE)
        self.btn_font = pygame.font.Font(font_path, BTN_FONT_SIZE)

        # 2. 初始化重新开始按钮区域
        btn_w, btn_h = 140, 40
        self.restart_btn = pygame.Rect(0, 0, btn_w, btn_h)
        
        # === 晃动动画状态 ===
        self.shaking_arrow = None      # 当前晃动的箭头坐标 (row, col)
        self.shake_timer = 0           # 晃动剩余时间（秒）
        self.shake_intensity = 4       # 晃动幅度（像素）
        self.shake_frequency = 30      # 晃动频率（Hz，控制正弦波速度）
        self.shake_should_check_game_over = False

        # === 游戏状态管理 ===
        # 状态分为 'playing' (游戏中), 'won' (通关), 'lost' (失败)
        self.game_state = 'playing'

        # === 弹窗按钮 Rect ===
        # 弹窗尺寸
        self.popup_width = 300
        self.popup_height = 200
        # 弹窗居中坐标
        self.popup_x = (SCREEN_WIDTH - self.popup_width) // 2
        self.popup_y = (SCREEN_HEIGHT - self.popup_height) // 2

        # 弹窗按钮尺寸
        popup_btn_w = 120
        popup_btn_h = 40
        # "左侧" 按钮
        self.popup_left_btn = pygame.Rect(
            self.popup_x + (self.popup_width - popup_btn_w * 2 - 20) // 2,
            self.popup_y + self.popup_height - 60,
            popup_btn_w, popup_btn_h
        )
        # "右侧" 按钮
        self.popup_right_btn = pygame.Rect(
            self.popup_x + (self.popup_width - popup_btn_w * 2 - 20) // 2 + popup_btn_w + 20,
            self.popup_y + self.popup_height - 60,
            popup_btn_w, popup_btn_h
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

        # === 移动动画配置 ===
        self.move_speed = 600  # 像素/秒，可以调整这个值来改变箭头飞行速度

        # === 移动状态追踪 ===
        # 用于存储正在移动的箭头信息，结构为：
        # {'start_pos': (row, col), 'current_pos': (x, y), 'direction': dir}
        self.moving_arrow = None

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

    def check_level_target(self):
        """
        检查当前关卡目标是否达成
        通关条件：所有箭头都已发出
        """
        return len(self.placed_arrows) >= self.max_arrows

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
                # 如果已经有箭头在移动，则忽略新的点击
                if self.moving_arrow is not None:
                    return

                rel_x = mx - self.offset_x
                rel_y = my - self.offset_y
                
                # 遍历所有格子，用 collidepoint 精确检测点击了哪个格子
                for r in range(self.rows):
                    for c in range(self.cols):
                        cell_x = self.offset_x + c * (self.cell_size + CELL_GAP)
                        cell_y = self.offset_y + r * (self.cell_size + CELL_GAP)
                        cell_rect = pygame.Rect(cell_x, cell_y, self.cell_size, self.cell_size)
                        
                        if cell_rect.collidepoint(mx, my):
                            # 点击的格子有箭头，启动移动动画
                            if self.grid_map[r][c] != 0:
                                # 计算箭头的初始屏幕坐标（中心点）
                                start_px = cell_x + self.cell_size // 2
                                start_py = cell_y + self.cell_size // 2
                                
                                self.moving_arrow = {
                                    'start_pos': (r, c),
                                    'current_pos': (start_px, start_py),
                                    'direction': self.grid_map[r][c]
                                }
                            return
                        
            # 3. === 弹窗按钮处理（仅在 won/lost/all_completed 状态下有效）===
            if self.game_state in ('won', 'lost', 'all_completed'):
                # 点击左侧按钮
                if self.popup_left_btn.collidepoint(event.pos):
                    if self.game_state == 'won':
                        # 胜利时，左侧按钮是 "Return"
                        self.game.scene_manager.reset_to_start()
                    else:
                        # 失败或全通关时，左侧按钮是 "Return"
                        self.game.scene_manager.reset_to_start()
                    return

                # 点击右侧按钮
                if self.popup_right_btn.collidepoint(event.pos):
                    if self.game_state == 'won':
                        # 胜利时，右侧按钮是 "Next"
                        self.level_index += 1
                        self.load_level_data()
                        self.game_state = 'playing'
                    elif self.game_state == 'lost':
                        # 失败时，右侧按钮是 "Retry"
                        self.load_level_data()
                        self.game_state = 'playing'
                    else:
                        # 全通关时，右侧按钮也是 "Return"
                        self.game.scene_manager.reset_to_start()
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
                self.moving_arrow = None
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
            self.moving_arrow = None
        elif direction == DIR_DOWN and arrow_top > SCREEN_HEIGHT:
            self.placed_arrows.append((start_row, start_col, direction))
            self.check_arrow_path('clear', start_row, start_col)
            self.moving_arrow = None
        elif direction == DIR_LEFT and arrow_right < 0:
            self.placed_arrows.append((start_row, start_col, direction))
            self.check_arrow_path('clear', start_row, start_col)
            self.moving_arrow = None
        elif direction == DIR_RIGHT and arrow_left > SCREEN_WIDTH:
            self.placed_arrows.append((start_row, start_col, direction))
            self.check_arrow_path('clear', start_row, start_col)
            self.moving_arrow = None

    def draw(self):
        screen_w, screen_h = self.screen.get_size()
        self.screen.fill(BG_LIGHT)
        
        # --- 绘制棋盘 ---
        self._draw_board()
        
        # === 新增：绘制正在移动的箭头 ===
        if self.moving_arrow is not None:
            arrow = self.moving_arrow
            direction = arrow['direction']
            pos = arrow['current_pos']
            # 创建一个临时 rect 仅用于确定箭头大小，位置由 pos 参数决定
            temp_rect = pygame.Rect(0, 0, self.cell_size, self.cell_size)
            self._draw_arrow(temp_rect, direction, pos=pos)

        self.draw_top_bar()

        self.draw_restart_btn()

        # === 弹窗绘制（仅在 won 或 lost 或 all_completed 状态下显示）===
        if self.game_state in ('won', 'lost', 'all_completed'):
            # 1. 半透明遮罩
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.set_alpha(150)
            overlay.fill((0, 0, 0))
            self.screen.blit(overlay, (0, 0))

            # 2. 弹窗背景
            popup_rect = pygame.Rect(self.popup_x, self.popup_y, self.popup_width, self.popup_height)
            pygame.draw.rect(self.screen, BG_LIGHT, popup_rect, border_radius=12)
            pygame.draw.rect(self.screen, BG_DARK, popup_rect, width=2, border_radius=12)

            # 3. 标题（大标题 + 副标题）
            if self.game_state == 'all_completed':
                title_text = "Congratulations!"
                subtitle_text = "You've cleared all levels!"
                title_color = POPUP_TITLE_ALL_COMPLETED
            elif self.game_state == 'won':
                title_text = "Level Complete!"
                subtitle_text = "Good job!"
                title_color = POPUP_TITLE_WON
            else:  # lost
                title_text = "Game Over"
                subtitle_text = "Don't give up, try again!"
                title_color = POPUP_TITLE_LOST

            # 渲染大标题（粗体）
            title_surface = self.popup_title_font.render(title_text, True, title_color)
            title_rect = title_surface.get_rect(center=(SCREEN_WIDTH // 2, self.popup_y + 45))
            self.screen.blit(title_surface, title_rect)

            # 渲染副标题（小字号，间距15px）
            subtitle_font = pygame.font.Font(FONT_PATH, 22) if FONT_PATH else pygame.font.Font(None, 22)
            subtitle_surface = subtitle_font.render(subtitle_text, True, STATUS_TEXT_COLOR)
            subtitle_rect = subtitle_surface.get_rect(center=(SCREEN_WIDTH // 2, title_rect.bottom + 15))
            self.screen.blit(subtitle_surface, subtitle_rect)
            # 4. 按钮
            if self.game_state == 'all_completed':
                # --- 全通关状态 ---
                # 左侧按钮: Return
                pygame.draw.rect(self.screen, BTN_BACK, self.popup_left_btn, border_radius=8)
                return_text = self.btn_font.render("Return", True, TEXT_DARK_BG)
                return_text_rect = return_text.get_rect(center=self.popup_left_btn.center)
                self.screen.blit(return_text, return_text_rect)

                # 右侧按钮: Return
                pygame.draw.rect(self.screen, BTN_BACK, self.popup_right_btn, border_radius=8)
                return_text = self.btn_font.render("Return", True, TEXT_DARK_BG)
                return_text_rect = return_text.get_rect(center=self.popup_right_btn.center)
                self.screen.blit(return_text, return_text_rect)

            elif self.game_state == 'won':
                # --- 胜利状态 ---
                # 左侧按钮: Return
                pygame.draw.rect(self.screen, BTN_BACK, self.popup_left_btn, border_radius=8)
                return_text = self.btn_font.render("Return", True, TEXT_DARK_BG)
                return_text_rect = return_text.get_rect(center=self.popup_left_btn.center)
                self.screen.blit(return_text, return_text_rect)

                # 右侧按钮: Next
                pygame.draw.rect(self.screen, BTN_NEXT, self.popup_right_btn, border_radius=8)
                next_text = self.btn_font.render("Next", True, TEXT_DARK_BG)
                next_text_rect = next_text.get_rect(center=self.popup_right_btn.center)
                self.screen.blit(next_text, next_text_rect)


            else:  # self.game_state == 'lost'
                # --- 失败状态 ---
                # 左侧按钮: Return
                pygame.draw.rect(self.screen, BTN_BACK, self.popup_left_btn, border_radius=8)
                return_text = self.btn_font.render("Return", True, TEXT_DARK_BG)
                return_text_rect = return_text.get_rect(center=self.popup_left_btn.center)
                self.screen.blit(return_text, return_text_rect)

                # 右侧按钮: Retry
                pygame.draw.rect(self.screen, BTN_RETRY, self.popup_right_btn, border_radius=8)
                retry_text = self.btn_font.render("Retry", True, TEXT_DARK_BG)
                retry_text_rect = retry_text.get_rect(center=self.popup_right_btn.center)
                self.screen.blit(retry_text, retry_text_rect)

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
        
        # 状态栏总宽度，分为三等份
        section_width = SCREEN_WIDTH // 3
        y_center = TOP_BAR_HEIGHT // 2
        
        # === 左侧：绘制关卡进度 (旗子 + 数字) ===
        current_level = self.level_index + 1
        level_text = self.ui_font.render(f"{current_level}", True, STATUS_TEXT_COLOR)
        x_level = section_width // 2 - (self.icon_level.get_width() + ICON_SPACING + level_text.get_width()) // 2
        self.game.screen.blit(self.icon_level, (x_level, y_center - self.icon_level.get_height() // 2))
        self.game.screen.blit(level_text, (x_level + self.icon_level.get_width() + ICON_SPACING, y_center - level_text.get_height() // 2))

        # === 中间：绘制剩余步数 (箭头 + 数字) ===
        arrows_left = self.max_arrows - len(self.placed_arrows)
        arrow_text = self.ui_font.render(f"{arrows_left}", True, STATUS_TEXT_COLOR)
        x_arrow = SCREEN_WIDTH // 2 - (self.icon_arrow.get_width() + ICON_SPACING + arrow_text.get_width()) // 2
        # 直接绘制原图，不进行任何染色
        self.game.screen.blit(self.icon_arrow, (x_arrow, y_center - self.icon_arrow.get_height() // 2))
        self.game.screen.blit(arrow_text, (x_arrow + self.icon_arrow.get_width() + ICON_SPACING, y_center - arrow_text.get_height() // 2))

        # === 右侧：绘制生命值 (实心/空心爱心) ===
        hearts_container_w = self.max_mistakes * (self.icon_heart.get_width() + 4)
        x_hearts_start = SCREEN_WIDTH - section_width // 2 - hearts_container_w // 2
        
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

    def draw_restart_btn(self):
        """绘制底部重新开始按钮"""
        # 1. 绘制底部浅灰背景
        bottom_rect = pygame.Rect(0, SCREEN_HEIGHT - BOTTOM_BAR_HEIGHT, SCREEN_WIDTH, BOTTOM_BAR_HEIGHT)
        pygame.draw.rect(self.game.screen, STATUS_BAR_COLOR, bottom_rect)
        
        # 2. 更新 restart_btn 的位置以适配底部栏（水平垂直居中）
        btn_w, btn_h = self.restart_btn.size
        self.restart_btn.topleft = (
            SCREEN_WIDTH // 2 - btn_w // 2, 
            SCREEN_HEIGHT - BOTTOM_BAR_HEIGHT + (BOTTOM_BAR_HEIGHT - btn_h) // 2
        )
        
        # 3. 绘制按钮底色（使用 settings.py 中已定义的 BTN_RESTART）
        pygame.draw.rect(self.game.screen, BTN_RESTART, self.restart_btn, border_radius=8)
        
        # 4. 绘制按钮边框（可选：用浅灰色描边，或者干脆不要边框更简洁）
        pygame.draw.rect(self.game.screen, pygame.Color('#C0C0C0'), self.restart_btn, 2, border_radius=8)
        
        # 5. 绘制按钮文字
        btn_text = self.btn_font.render("Restart", True, TEXT_LIGHT_BG)
        text_rect = btn_text.get_rect(center=self.restart_btn.center)
        self.game.screen.blit(btn_text, text_rect)

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
