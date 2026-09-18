import pygame
import os
import sys

# === 窗口与基础设置 ===
SCREEN_WIDTH = 400
SCREEN_HEIGHT = 600
FPS = 60

# === 莫兰迪配色方案 ===
BG_DARK = pygame.Color('#555555')
BG_LIGHT = pygame.Color("#FFFFFF")
BG_GRID = pygame.Color('#D6D6D6') 

# 箭头颜色
ARROW_UP = pygame.Color('#D4B0B5')
ARROW_DOWN = pygame.Color('#98A9BD')
ARROW_LEFT = pygame.Color('#9CAF88')
ARROW_RIGHT = pygame.Color('#E8D9B9')
ARROW_START = pygame.Color('#B5A89C')
ARROW_TARGET = pygame.Color('#E07A5F')

# 按钮颜色
BTN_NEXT = pygame.Color('#8BB4D4') 
BTN_RETRY = pygame.Color('#E8B4B8')   
BTN_RESTART = pygame.Color('#B5A89C') 
BTN_BACK = pygame.Color('#779c66')    
# 文字颜色
TEXT_DARK_BG = pygame.Color('#F2EFE4')
TEXT_LIGHT_BG = pygame.Color('#3C3C3C')

# 方向编码
DIR_UP = 1
DIR_DOWN = 2
DIR_LEFT = 3
DIR_RIGHT = 4

# 网格布局常量
GRID_PADDING = 20
CELL_GAP = 2
ARROW_RATIO = 0.6

GRID_BG_COLOR = pygame.Color('#FFFFFF')
CELL_BG_COLOR = pygame.Color('#FFFFFF')
CELL_BG_ALT = pygame.Color('#F6F6F6')
CELL_BORDER_COLOR = pygame.Color('#E8E8E8')
BORDER_LINE_COLOR = pygame.Color('#000000')

# === UI 布局数值常量 ===
TOP_BAR_HEIGHT = 70
BOTTOM_BAR_HEIGHT = 60
UI_FONT_SIZE = 24
BTN_FONT_SIZE = 22
TITLE_FONT_SIZE = 52

# === 字体配置 ===
if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FONT_PATH = os.path.join(BASE_DIR, 'assets', 'fonts', 'Nunito-VariableFont_wght.ttf')
if not os.path.exists(FONT_PATH):
    print(f"警告: 字体文件未找到 -> {FONT_PATH}")
    FONT_PATH = None

LEVELS_FILE = os.path.join(BASE_DIR, 'data', 'levels.json')

# === 背景与粒子配置 ===
BG_MENU = (245, 245, 245)

FLOATING_ARROW_COLORS = [
    ARROW_UP, ARROW_DOWN, ARROW_LEFT, ARROW_RIGHT, ARROW_START,
]

# === 图标配置 ===
ICON_SIZE = 26
ICON_SPACING = 8
STATUS_BAR_COLOR = pygame.Color("#F5F2EC") 
STATUS_TEXT_COLOR = pygame.Color('#5A5348')
HEART_EMPTY_COLOR = pygame.Color('#C8BFB4') 
BOTTOM_BORDER_COLOR = pygame.Color('#D8D0C5')

# 弹窗标题颜色
POPUP_TITLE_WON = pygame.Color("#517d74")      # 通关 - 灰豆绿
POPUP_TITLE_LOST = pygame.Color('#D4A5A5')     # 失败 - 灰粉
POPUP_TITLE_ALL_COMPLETED = pygame.Color('#e0be9a')  # 全通关 - 灰棕

# --- 关卡选择界面配置 ---
LEVEL_SELECT_TITLE_FONT_SIZE = 40
LEVEL_BTN_FONT_SIZE = 28
LEVEL_BTN_WIDTH = 100
LEVEL_BTN_HEIGHT = 80
LEVEL_BTN_GAP = 15
LEVEL_BTN_COLS = 3
BTN_LEVEL = pygame.Color('#B8C4B0')       # 莫兰迪绿 - 关卡按钮底色
BTN_LEVEL_HOVER = pygame.Color('#A3B29A') # 深一点的莫兰迪绿 - 悬停效果
BTN_BACK_HOVER = pygame.Color('#668855') 

# 开始界面按钮颜色
BTN_START = pygame.Color('#A9C2A8')
BTN_START_HOVER = pygame.Color('#86aa9a')    # 比 BTN_START 稍浅，用于悬停效果
BTN_SELECT_LEVEL = pygame.Color('#A9C2A8')   # 暖灰棕 - Select Level 按钮底色
BTN_SELECT_LEVEL_HOVER = pygame.Color('#86aa9a')  # 稍浅的暖灰棕 - 悬停效果
