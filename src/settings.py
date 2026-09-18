import pygame
import os
import sys

# 获取项目根目录的绝对路径（跨平台兼容）
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEVELS_FILE = os.path.join(BASE_DIR, 'data', 'levels.json')


# 窗口设置
SCREEN_WIDTH = 400
SCREEN_HEIGHT = 600
FPS = 60

# 莫兰迪配色方案 (RGB)
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
BTN_START = pygame.Color('#9CAF88')
BTN_NEXT = pygame.Color('#98A9BD')
BTN_RETRY = pygame.Color('#D4B0B5')
BTN_RESTART = pygame.Color('#B5A89C')
BTN_BACK = pygame.Color('#9E9E9E')

# 文字颜色
TEXT_DARK_BG = pygame.Color('#F2EFE4')
TEXT_LIGHT_BG = pygame.Color('#3C3C3C')

# 方向编码
DIR_UP = 1
DIR_DOWN = 2
DIR_LEFT = 3
DIR_RIGHT = 4

# 网格布局常量
GRID_PADDING = 20       # 网格距离屏幕边缘的间距
CELL_GAP = 2            # 单元格之间的间距
ARROW_RATIO = 0.6       # 箭头大小占单元格的比例

GRID_BG_COLOR = pygame.Color('#FFFFFF')  # 棋盘大底板的颜色（纯白，与开始界面统一）
CELL_BG_COLOR = pygame.Color('#FFFFFF')  # 单元格浅色格（纯白）
CELL_BG_ALT = pygame.Color('#F6F6F6')    # 单元格深色格（极浅灰，形成棋盘格）
CELL_BORDER_COLOR = pygame.Color('#E8E8E8')  # 棋盘外边框颜色（浅灰）
BORDER_LINE_COLOR = pygame.Color('#000000')

# === UI 布局数值常量 ===
TOP_BAR_HEIGHT = 50
BOTTOM_BAR_HEIGHT = 60
UI_FONT_SIZE = 24
BTN_FONT_SIZE = 22
TITLE_FONT_SIZE = 52    # 大标题字号

# === 字体配置常量 ===

# 1. 获取项目根目录的绝对路径，确保在任何系统下都能正确找到
if getattr(sys, 'frozen', False):
    # 当程序被打包成 .exe 后，运行时的目录
    BASE_DIR = sys._MEIPASS
else:
    # 开发时，当前脚本所在目录的上一级（即项目根目录）
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 2. 拼接字体文件的完整路径
FONT_PATH = os.path.join(BASE_DIR, 'assets', 'fonts', 'Nunito-VariableFont_wght.ttf')

# 3. 检查字体文件是否存在
if not os.path.exists(FONT_PATH):
    print(f"警告: 字体文件未找到 -> {FONT_PATH}")
    FONT_PATH = None  # 如果找不到，后面会使用系统默认字体作为兜底

# === 背景与粒子配置 ===
BG_MENU = (245, 245, 245)  # 极浅灰白，作为开始界面的底纹，比纯白更有质感

# 飘动箭头的颜色池（从现有莫兰迪配色中挑选柔和的颜色）
FLOATING_ARROW_COLORS = [
    ARROW_UP,     # 淡红
    ARROW_DOWN,   # 灰蓝
    ARROW_LEFT,   # 草绿
    ARROW_RIGHT,  # 米黄
    ARROW_START,  # 灰褐
]
