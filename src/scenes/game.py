# src/scenes/game.py
"""游戏主界面。"""
import copy
import math
import os

import pygame

from settings import *
from ui import Button, load_font
from .base import BaseScene


class GameScene(BaseScene):
    """游戏主界面"""

    @property
    def scene_manager(self):
        # Game.scene_manager 在 SceneManager 构造完成后才存在，故运行时惰性访问
        return self.game.scene_manager

    def __init__(self, game, font_bold, font_regular):
        super().__init__(game)
        self.level_index = 0
        self.pending_click = None

        self._init_fonts(font_bold, font_regular)
        self._init_buttons()
        self._init_icons()
        self._init_state()

        self.load_level_data()
        self._build_arrow_masks()

    # === 初始化 ===

    def _init_fonts(self, font_bold, font_regular):
        self.font_bold = font_bold
        self.font_regular = font_regular

        self.popup_title_font = load_font(36, bold=True)
        self.time_bold_font = load_font(POPUP_TIME_BOLD_FONT_SIZE, bold=True)
        self.ui_font = load_font(UI_FONT_SIZE)
        self.btn_font = load_font(BTN_FONT_SIZE)
        self.small_font = load_font(24)

    def _init_buttons(self):
        # 弹窗尺寸（弹窗按钮位置依赖它，先计算）
        self.popup_width = 300
        self.popup_height = 200
        self.popup_x = (SCREEN_WIDTH - self.popup_width) // 2
        self.popup_y = (SCREEN_HEIGHT - self.popup_height) // 2

        # 底部控制按钮
        btn_w, btn_h = 100, 40
        btn_y = SCREEN_HEIGHT - 60
        gap = 5
        total_width = btn_w * 3 + gap * 2
        start_x = (SCREEN_WIDTH - total_width) // 2

        self.return_btn = Button(
            pygame.Rect(start_x, btn_y, btn_w, btn_h),
            "Return", self.btn_font, BTN_BACK, TEXT_LIGHT_BG,
            border_color=pygame.Color('#C0C0C0'),
        )
        self.restart_btn = Button(
            pygame.Rect(start_x + btn_w + gap, btn_y, btn_w, btn_h),
            "Restart", self.btn_font, BTN_RESTART, TEXT_LIGHT_BG,
            border_color=pygame.Color('#C0C0C0'),
        )
        self.select_btn = Button(
            pygame.Rect(start_x + (btn_w + gap) * 2, btn_y, btn_w, btn_h),
            "Select", self.btn_font, BTN_SELECT_LEVEL, TEXT_LIGHT_BG,
            border_color=pygame.Color('#C0C0C0'),
        )

        # 弹窗按钮（文字与底色在绘制时按状态更新）
        self.popup_left_btn = Button(
            self._popup_btn_rect(left=True),
            "Return", self.small_font, BTN_BACK, TEXT_DARK_BG,
            border_color=pygame.Color('#C0C0C0'),
        )
        self.popup_right_btn = Button(
            self._popup_btn_rect(left=False),
            "Next", self.small_font, BTN_NEXT, TEXT_DARK_BG,
            border_color=pygame.Color('#C0C0C0'),
        )

    def _popup_btn_rect(self, left):
        btn_width = 130
        btn_height = 45
        center_x = SCREEN_WIDTH // 2
        gap = 5
        y = self.popup_y + self.popup_height - btn_height - 20
        if left:
            return pygame.Rect(center_x - gap - btn_width, y, btn_width, btn_height)
        return pygame.Rect(center_x + gap, y, btn_width, btn_height)

    def _init_icons(self):
        icon_names = {
            'icon_level': 'flag.png',
            'icon_arrow': 'arrow.png',
            'icon_heart': 'heart-full.png',
            'icon_heart_empty': 'heart-empty.png',
            'icon_clock': 'clock.png',
        }
        for attr, filename in icon_names.items():
            img = pygame.image.load(os.path.join(ICONS_DIR, filename)).convert_alpha()
            setattr(self, attr, pygame.transform.scale(img, (ICON_SIZE, ICON_SIZE)))

    def _init_state(self):
        # 晃动动画状态
        self.shaking_arrow = None
        self.shake_timer = 0
        self.shake_intensity = 4
        self.shake_frequency = 30
        self.shake_should_check_game_over = False

        # 游戏状态：playing / won / lost / all_completed
        self.game_state = STATE_PLAYING

        # 计时器
        self.time_limit = 0
        self.time_remaining = 0.0
        self.timer_running = False
        self.level_time_used = 0

        # 移动动画
        self.move_speed = 600  # 像素/秒
        self.moving_arrow = None
        self.hover_cell = None

    def _build_arrow_masks(self):
        """预生成每种方向箭头的碰撞掩码（需在 load_level_data 之后调用）。"""
        self.arrow_masks = {}
        for direction in [DIR_UP, DIR_DOWN, DIR_LEFT, DIR_RIGHT]:
            self.arrow_masks[direction] = pygame.mask.from_surface(self.arrow_images[direction])

    # === 关卡数据加载 ===

    def load_level_data(self):
        """加载当前关卡并重置状态。"""
        if self.level_index >= len(self.game.levels):
            self.level_index = len(self.game.levels) - 1

        self._load_level()
        self._compute_layout()
        self._load_arrow_images()
        self._reset_level_state()

    def _load_level(self):
        self.level_data = self.game.levels[self.level_index]
        self.rows, self.cols = self.level_data['grid_size']
        self.grid_map = copy.deepcopy(self.level_data['map'])

    def _compute_layout(self):
        # 动态计算棋盘大小
        available_w = SCREEN_WIDTH - GRID_PADDING * 2
        available_h = SCREEN_HEIGHT - GRID_PADDING * 2 - TOP_BAR_HEIGHT - BOTTOM_BAR_HEIGHT
        self.cell_size = min(available_w // self.cols, available_h // self.rows)

        # 计算棋盘居中偏移量
        grid_w = self.cols * self.cell_size + (self.cols - 1) * CELL_GAP
        grid_h = self.rows * self.cell_size + (self.rows - 1) * CELL_GAP
        self.offset_x = (SCREEN_WIDTH - grid_w) // 2
        self.offset_y = TOP_BAR_HEIGHT + (SCREEN_HEIGHT - TOP_BAR_HEIGHT - BOTTOM_BAR_HEIGHT - grid_h) // 2

    def _load_arrow_images(self):
        self.arrow_images = {}
        target_size = max(int(self.cell_size * ARROW_RATIO), 10)

        for direction, name in [(DIR_UP, 'up'), (DIR_DOWN, 'down'),
                                (DIR_LEFT, 'left'), (DIR_RIGHT, 'right')]:
            path = os.path.join(ICONS_DIR, f'arrow-{name}.png')
            if os.path.exists(path):
                img = pygame.image.load(path).convert_alpha()
                self.arrow_images[direction] = pygame.transform.smoothscale(img, (target_size, target_size))
            else:
                print(f"⚠️ 未找到图标: {path}")

    def _reset_level_state(self):
        self.max_arrows = self.level_data.get('arrows_left', 0)
        self.max_mistakes = self.level_data.get('max_failures', 0)
        self.cleared_count = 0
        self.mistake_count = 0

        self.time_limit = self.level_data.get('time_limit', 60)
        self.time_remaining = float(self.time_limit)
        self.timer_running = True

    # === 几何 / 方向工具 ===

    def _cell_rect(self, r, c):
        x = self.offset_x + c * (self.cell_size + CELL_GAP)
        y = self.offset_y + r * (self.cell_size + CELL_GAP)
        return pygame.Rect(x, y, self.cell_size, self.cell_size)

    def _cell_center(self, r, c):
        rect = self._cell_rect(r, c)
        return rect.centerx, rect.centery

    def _direction_delta(self, direction):
        return DIRECTION_DELTAS[direction]

    # === 事件处理 ===

    def handle_event(self, event):
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return
        pos = event.pos

        # 弹窗状态：仅处理弹窗按钮，其余点击忽略
        if self.game_state in (STATE_WON, STATE_LOST, STATE_ALL_COMPLETED):
            self._handle_popup_click(pos)
            return

        if self._handle_bottom_click(pos):
            return

        self._handle_board_click(pos)

    def _handle_popup_click(self, pos):
        if self.popup_left_btn.is_clicked(pos):
            if self.game_state == STATE_ALL_COMPLETED:
                self.scene_manager.switch_scene(SCENE_LEVEL_SELECT)
            else:  # won / lost 左键均为返回开始
                self.scene_manager.reset_to_start()
            return

        if self.popup_right_btn.is_clicked(pos):
            if self.game_state == STATE_WON:
                self.level_index += 1
                self.load_level_data()
                self.game_state = STATE_PLAYING
            elif self.game_state == STATE_LOST:
                self.load_level_data()
                self.game_state = STATE_PLAYING
            else:  # all_completed 右键为返回开始
                self.scene_manager.reset_to_start()

    def _handle_bottom_click(self, pos):
        if self.return_btn.is_clicked(pos):
            self.scene_manager.switch_scene(SCENE_START)
            return True

        if self.restart_btn.is_clicked(pos):
            self.load_level_data()
            self.game_state = STATE_PLAYING
            return True

        if self.select_btn.is_clicked(pos):
            self.scene_manager.open_level_select(SCENE_GAME)
            return True

        return False

    def _handle_board_click(self, pos):
        for r in range(self.rows):
            for c in range(self.cols):
                if not self._cell_rect(r, c).collidepoint(pos):
                    continue
                if self.grid_map[r][c] != 0:
                    if self.moving_arrow is None:
                        self._launch_arrow(r, c)
                    else:
                        # 有动画播放中，排队等待（只保留最后一次点击）
                        self.pending_click = (r, c)
                return

    def _launch_arrow(self, r, c):
        start_px, start_py = self._cell_center(r, c)
        self.moving_arrow = {
            'start_pos': (r, c),
            'current_pos': (start_px, start_py),
            'direction': self.grid_map[r][c],
        }

    # === 判定逻辑 ===

    def check_arrow_path(self, status, row, col):
        """根据路径状态执行消除、晃动与胜负判定。"""
        if status == 'clear':
            self.grid_map[row][col] = 0
            print(f"✅ 消除！({row},{col}) 飞出棋盘。")

            arrows_remaining = any(cell != 0 for row_data in self.grid_map for cell in row_data)
            if not arrows_remaining:
                print("🎉 恭喜通关本关！等待玩家操作。")
                self.game_state = STATE_WON

        elif status == 'blocked':
            self.shaking_arrow = (row, col)
            self.shake_timer = 0.3
            self.mistake_count += 1
            print(f"❌ 碰撞！({row},{col}) 路径被阻挡。")

            # 先不切 game_state，等晃动播完再判定
            self.shake_should_check_game_over = True

    def check_level_target(self):
        """通关条件：所有箭头都已发出且时间未耗尽。"""
        arrows_cleared = self.cleared_count >= self.max_arrows
        time_up = self.time_remaining <= 0
        return arrows_cleared and not time_up

    # === 更新 ===

    def update(self, dt):
        self.mouse_pos = pygame.mouse.get_pos()

        # 计时器
        if self.timer_running and self.game_state == STATE_PLAYING:
            self.time_remaining -= dt
            if self.time_remaining <= 0:
                self.time_remaining = 0
                self.timer_running = False
                self.game_state = STATE_LOST
                print("⏰ 时间到！游戏失败。")

        # 悬停检测
        self.hover_cell = None
        if self.game_state == STATE_PLAYING:
            mx, my = self.mouse_pos
            for r in range(self.rows):
                for c in range(self.cols):
                    if self._cell_rect(r, c).collidepoint(mx, my):
                        self.hover_cell = (r, c)
                        break
                if self.hover_cell is not None:
                    break

        # 箭头移动动画
        if self.moving_arrow is not None and self.game_state == STATE_PLAYING:
            self._update_moving_arrow(dt)

        # 晃动动画计时
        if self.shake_timer > 0:
            self.shake_timer -= dt
            if self.shake_timer <= 0:
                self.shake_timer = 0
                self.shaking_arrow = None

                if self.shake_should_check_game_over:
                    self.shake_should_check_game_over = False
                    if self.mistake_count >= self.max_mistakes:
                        print("❌ 游戏失败！等待玩家操作。")
                        self.game_state = STATE_LOST

        # 通关判定
        if self.check_level_target():
            self.timer_running = False
            self.level_time_used = self.time_limit - int(self.time_remaining)
            if self.level_index >= len(self.game.levels) - 1:
                self.game_state = STATE_ALL_COMPLETED
            else:
                self.game_state = STATE_WON

    def _update_moving_arrow(self, dt):
        arrow = self.moving_arrow
        start_row, start_col = arrow['start_pos']
        direction = arrow['direction']

        # 1. 更新位置
        move_distance = self.move_speed * dt
        curr_x, curr_y = arrow['current_pos']
        dr, dc = self._direction_delta(direction)
        curr_x += dc * move_distance
        curr_y += dr * move_distance
        arrow['current_pos'] = (curr_x, curr_y)

        moving_img = self.arrow_images[direction]
        moving_mask = self.arrow_masks[direction]
        moving_w, moving_h = moving_img.get_size()
        moving_left = curr_x - moving_w // 2
        moving_top = curr_y - moving_h // 2

        # 2. 沿方向找到第一个有箭头的格子
        target_r, target_c = self._find_blocking_cell(start_row, start_col, direction)

        # 3. 像素级碰撞检测
        if target_r is not None and self._check_pixel_collision(
                moving_mask, moving_left, moving_top, target_r, target_c):
            self.check_arrow_path('blocked', start_row, start_col)
            self._try_next_pending_arrow()
            return

        # 4. 边界检测：完全飞出屏幕
        if self._check_offscreen(curr_x, curr_y, moving_w, moving_h, direction):
            self.cleared_count += 1
            self.check_arrow_path('clear', start_row, start_col)
            self._try_next_pending_arrow()

    def _find_blocking_cell(self, start_row, start_col, direction):
        dr, dc = self._direction_delta(direction)
        for step in range(1, max(self.rows, self.cols)):
            check_r = start_row + dr * step
            check_c = start_col + dc * step
            if not (0 <= check_r < self.rows and 0 <= check_c < self.cols):
                break
            if self.grid_map[check_r][check_c] != 0:
                return check_r, check_c
        return None, None

    def _check_pixel_collision(self, moving_mask, moving_left, moving_top, target_r, target_c):
        other_dir = self.grid_map[target_r][target_c]
        other_x, other_y = self._cell_center(target_r, target_c)

        other_img = self.arrow_images[other_dir]
        other_mask = self.arrow_masks[other_dir]
        other_w, other_h = other_img.get_size()
        other_left = other_x - other_w // 2
        other_top = other_y - other_h // 2

        offset_x = int(moving_left - other_left)
        offset_y = int(moving_top - other_top)
        overlap_point = moving_mask.overlap(other_mask, (offset_x, offset_y))
        return overlap_point is not None

    def _check_offscreen(self, curr_x, curr_y, w, h, direction):
        half_w = w // 2
        half_h = h // 2
        arrow_left = curr_x - half_w
        arrow_right = curr_x + half_w
        arrow_top = curr_y - half_h
        arrow_bottom = curr_y + half_h

        if direction == DIR_UP:
            return arrow_bottom < 0
        if direction == DIR_DOWN:
            return arrow_top > SCREEN_HEIGHT
        if direction == DIR_LEFT:
            return arrow_right < 0
        if direction == DIR_RIGHT:
            return arrow_left > SCREEN_WIDTH
        return False

    def _try_next_pending_arrow(self):
        """尝试触发排队的箭头，或清除 moving_arrow。"""
        if self.pending_click:
            r, c = self.pending_click
            self.pending_click = None
            if self.grid_map[r][c] != 0:
                self._launch_arrow(r, c)
                return
        self.moving_arrow = None

    # === 绘制 ===

    def draw(self):
        self.game.screen.fill(BG_LIGHT)
        self._draw_board()

        # 悬停阴影
        if self.hover_cell is not None and self.game_state == STATE_PLAYING:
            r, c = self.hover_cell
            hover_rect = self._cell_rect(r, c)
            shadow_surface = pygame.Surface((self.cell_size, self.cell_size), pygame.SRCALPHA)
            shadow_surface.fill((100, 100, 100, 40))
            self.game.screen.blit(shadow_surface, hover_rect.topleft)

        # 移动中的箭头
        if self.moving_arrow is not None:
            arrow = self.moving_arrow
            temp_rect = pygame.Rect(0, 0, self.cell_size, self.cell_size)
            self._draw_arrow(temp_rect, arrow['direction'], pos=arrow['current_pos'])

        self.draw_top_bar()
        self.draw_bottom_buttons()

        if self.game_state in (STATE_WON, STATE_LOST, STATE_ALL_COMPLETED):
            self._draw_popup_overlay(is_success=self.game_state in (STATE_WON, STATE_ALL_COMPLETED))

    def _draw_board(self):
        for r in range(self.rows):
            for c in range(self.cols):
                cell_rect = self._cell_rect(r, c)

                color = CELL_BG_COLOR if (r + c) % 2 == 0 else CELL_BG_ALT
                pygame.draw.rect(self.screen, color, cell_rect)

                arrow_dir = self.grid_map[r][c]
                if arrow_dir != 0:
                    # 跳过正在移动的箭头所在格子，避免重影
                    if (self.moving_arrow is not None and
                            self.moving_arrow['start_pos'] == (r, c)):
                        continue
                    self._draw_arrow(cell_rect, arrow_dir, row=r, col=c)

        board_rect = pygame.Rect(
            self.offset_x - CELL_GAP,
            self.offset_y - CELL_GAP,
            self.cols * (self.cell_size + CELL_GAP) + CELL_GAP,
            self.rows * (self.cell_size + CELL_GAP) + CELL_GAP,
        )
        outer_rect = board_rect.inflate(10, 10)
        pygame.draw.rect(self.screen, BORDER_LINE_COLOR, outer_rect, width=2, border_radius=8)
        inner_rect = board_rect.inflate(0, 0)
        pygame.draw.rect(self.screen, BORDER_LINE_COLOR, inner_rect, width=2, border_radius=8)

    def _draw_arrow(self, rect, direction, row=None, col=None, pos=None):
        """使用 PNG 图标绘制箭头，支持晃动效果并自动上色。"""
        img = self.arrow_images.get(direction)
        if img is None:
            return

        if pos is not None:
            center_x, center_y = pos
        else:
            center_x = rect.centerx
            center_y = rect.centery

        # 晃动水平偏移
        offset_x = 0
        if (self.shaking_arrow is not None and
                row is not None and col is not None and
                self.shaking_arrow == (row, col) and
                self.shake_timer > 0):
            progress = 1.0 - (self.shake_timer / 0.3)  # 0 → 1
            decay = 1.0 - progress  # 晃动逐渐减弱
            offset_x = int(math.sin(progress * math.pi * self.shake_frequency * 0.3)
                           * self.shake_intensity * decay)

        img_rect = img.get_rect(center=(center_x + offset_x, center_y))

        color = ARROW_COLORS.get(direction)
        if color:
            # 给白色箭头图片上莫兰迪色
            temp_surface = pygame.Surface(img.get_size(), pygame.SRCALPHA)
            temp_surface.blit(img, (0, 0))
            temp_surface.fill(color, special_flags=pygame.BLEND_RGB_MULT)
            self.screen.blit(temp_surface, img_rect)
        else:
            self.screen.blit(img, img_rect)

    def draw_top_bar(self):
        top_rect = pygame.Rect(0, 0, SCREEN_WIDTH, TOP_BAR_HEIGHT)
        pygame.draw.rect(self.game.screen, STATUS_BAR_COLOR, top_rect)

        section_width = SCREEN_WIDTH // 4
        y_center = TOP_BAR_HEIGHT // 2

        # 左侧：关卡进度
        level_text = self.ui_font.render(f"{self.level_index + 1}", True, STATUS_TEXT_COLOR)
        self._draw_stat_item(self.icon_level, level_text, section_width // 2, y_center)

        # 倒计时
        minutes = int(self.time_remaining) // 60
        seconds = int(self.time_remaining) % 60
        time_str = f"{minutes:02d}:{seconds:02d}"
        time_color = TIME_WARNING_COLOR if self.time_remaining <= TIME_WARNING_THRESHOLD else STATUS_TEXT_COLOR
        time_text = self.ui_font.render(time_str, True, time_color)
        self._draw_stat_item(self.icon_clock, time_text, SCREEN_WIDTH // 2 - 60, y_center)

        # 剩余步数
        arrows_left = self.max_arrows - self.cleared_count
        arrow_text = self.ui_font.render(f"{arrows_left}", True, STATUS_TEXT_COLOR)
        self._draw_stat_item(self.icon_arrow, arrow_text, SCREEN_WIDTH // 2 + 40, y_center)

        # 右侧：生命值（实心/空心爱心）
        hearts_container_w = self.max_mistakes * (self.icon_heart.get_width() + 4)
        x_hearts_start = SCREEN_WIDTH - 20 - hearts_container_w
        for i in range(self.max_mistakes):
            pos_x = x_hearts_start + i * (self.icon_heart.get_width() + 4)
            pos_y = y_center - self.icon_heart.get_height() // 2
            if i < (self.max_mistakes - self.mistake_count):
                self.game.screen.blit(self.icon_heart, (pos_x, pos_y))
            else:
                self.game.screen.blit(self.icon_heart_empty, (pos_x, pos_y))

    def _draw_stat_item(self, icon, text_surface, center_x, y_center):
        """在指定中心 x 处绘制「图标 + 文字」组合。"""
        group_width = icon.get_width() + ICON_SPACING + text_surface.get_width()
        x = center_x - group_width // 2
        self.game.screen.blit(icon, (x, y_center - icon.get_height() // 2))
        self.game.screen.blit(
            text_surface,
            (x + icon.get_width() + ICON_SPACING, y_center - text_surface.get_height() // 2),
        )

    def draw_bottom_buttons(self):
        bottom_rect = pygame.Rect(0, SCREEN_HEIGHT - BOTTOM_BAR_HEIGHT, SCREEN_WIDTH, BOTTOM_BAR_HEIGHT)
        pygame.draw.rect(self.game.screen, STATUS_BAR_COLOR, bottom_rect)

        # 水平居中排列三个按钮
        btn_w, btn_h = self.restart_btn.rect.size
        gap = 15
        total_width = btn_w * 3 + gap * 2
        start_x = (SCREEN_WIDTH - total_width) // 2
        btn_y = SCREEN_HEIGHT - BOTTOM_BAR_HEIGHT + (BOTTOM_BAR_HEIGHT - btn_h) // 2

        self.return_btn.rect.topleft = (start_x, btn_y)
        self.restart_btn.rect.topleft = (start_x + btn_w + gap, btn_y)
        self.select_btn.rect.topleft = (start_x + (btn_w + gap) * 2, btn_y)

        is_disabled = self.game_state != STATE_PLAYING
        self.return_btn.draw(self.game.screen, disabled=is_disabled)
        self.restart_btn.draw(self.game.screen, disabled=is_disabled)
        self.select_btn.draw(self.game.screen, disabled=is_disabled)

    def _draw_popup_overlay(self, is_success=True):
        self._draw_overlay(is_success)
        self._draw_beam_effect(is_success)
        self._draw_popup_body()
        self._draw_popup_buttons()

    def _draw_overlay(self, is_success):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        if is_success:
            overlay.fill((111, 119, 136))
            overlay.set_alpha(160)
        else:
            overlay.fill((100, 100, 100))
            overlay.set_alpha(180)
        self.screen.blit(overlay, (0, 0))

    def _draw_beam_effect(self, is_success):
        fx_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)

        if is_success:
            max_beam_length = 200
            beam_color = BEAM_CENTER_COLOR
        else:
            max_beam_length = 200
            beam_color = (210, 210, 210)

        num_beams = 16
        for i in range(num_beams):
            angle_rad = math.radians((i / num_beams) * 360)
            segments = 40

            for j in range(segments):
                ratio_start = j / segments
                ratio_end = (j + 1) / segments
                dist_start = max_beam_length * ratio_start
                dist_end = max_beam_length * ratio_end

                current_alpha = int(180 * (1 - ratio_end))
                if current_alpha <= 0:
                    continue

                width_start = 2 + 25 * ratio_start
                width_end = 2 + 25 * ratio_start

                cos_a = math.cos(angle_rad)
                sin_a = math.sin(angle_rad)

                px_start = -width_start * sin_a
                py_start = width_start * cos_a
                p1 = (center[0] + dist_start * cos_a + px_start, center[1] + dist_start * sin_a + py_start)
                p2 = (center[0] + dist_start * cos_a - px_start, center[1] + dist_start * sin_a - py_start)

                px_end = -width_end * sin_a
                py_end = width_end * cos_a
                p3 = (center[0] + dist_end * cos_a + px_end, center[1] + dist_end * sin_a + py_end)
                p4 = (center[0] + dist_end * cos_a - px_end, center[1] + dist_end * sin_a - py_end)

                pygame.draw.polygon(fx_surface, (*beam_color, current_alpha), [p1, p3, p4, p2])

        self.screen.blit(fx_surface, (0, 0))

    def _draw_popup_body(self):
        popup_rect = pygame.Rect(self.popup_x, self.popup_y, self.popup_width, self.popup_height)
        pygame.draw.rect(self.screen, BG_LIGHT, popup_rect, border_radius=16)
        pygame.draw.rect(self.screen, BG_DARK, popup_rect, width=2, border_radius=16)

        if self.game_state == STATE_ALL_COMPLETED:
            title_text = "Level Complete!!"
            title_color = POPUP_TITLE_ALL_COMPLETED
        elif self.game_state == STATE_WON:
            title_text = "Level Complete!"
            title_color = POPUP_TITLE_WON
        else:
            title_text = "Game Over"
            title_color = POPUP_TITLE_LOST

        title_surface = self.popup_title_font.render(title_text, True, title_color)
        title_rect = title_surface.get_rect(center=(SCREEN_WIDTH // 2, self.popup_y + 45))
        self.screen.blit(title_surface, title_rect)

        if self.game_state == STATE_LOST:
            subtitle_surface = self.small_font.render(
                "Don't give up, try again!", True, STATUS_TEXT_COLOR)
            subtitle_rect = subtitle_surface.get_rect(center=(SCREEN_WIDTH // 2, title_rect.bottom + 15))
            self.screen.blit(subtitle_surface, subtitle_rect)
        else:
            # 通关 / 全通关：整体居中 + 垂直重心对齐
            time_str = f"{self.level_time_used}s"
            label_surface = self.popup_title_font.render("Time:", True, title_color)
            time_surface = self.time_bold_font.render(time_str, True, title_color)

            gap = 10
            total_width = label_surface.get_width() + gap + time_surface.get_width()
            start_x = (SCREEN_WIDTH - total_width) // 2
            center_y = title_rect.bottom + 30

            label_rect = label_surface.get_rect(topleft=(start_x, 0))
            label_rect.centery = center_y
            self.screen.blit(label_surface, label_rect)

            time_rect = time_surface.get_rect(topleft=(label_rect.right + gap, 0))
            time_rect.centery = center_y
            self.screen.blit(time_surface, time_rect)

    def _draw_popup_buttons(self):
        # 同步按钮位置（确保点击区域与视觉一致）
        btn_width = 130
        btn_height = 45
        center_x = SCREEN_WIDTH // 2
        gap = 5
        self.popup_left_btn.rect.topleft = (
            center_x - gap - btn_width,
            self.popup_y + self.popup_height - btn_height - 20,
        )
        self.popup_right_btn.rect.topleft = (
            center_x + gap,
            self.popup_y + self.popup_height - btn_height - 20,
        )

        if self.game_state == STATE_ALL_COMPLETED:
            left_text, left_color = "Select", BTN_SELECT_LEVEL
            right_text, right_color = "Return", BTN_BACK
        elif self.game_state == STATE_WON:
            left_text, left_color = "Return", BTN_BACK
            right_text, right_color = "Next", BTN_NEXT
        else:  # lost
            left_text, left_color = "Return", BTN_BACK
            right_text, right_color = "Retry", BTN_RETRY

        self.popup_left_btn.text = left_text
        self.popup_left_btn.base_color = left_color
        self.popup_right_btn.text = right_text
        self.popup_right_btn.base_color = right_color

        self.popup_left_btn.draw(self.screen)
        self.popup_right_btn.draw(self.screen)
