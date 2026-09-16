import pygame

# 窗口设置
SCREEN_WIDTH = 400
SCREEN_HEIGHT = 600
FPS = 60

# 莫兰迪配色方案 (RGB)
BG_DARK = pygame.Color('#555555')
BG_LIGHT = pygame.Color('#F2EFE4')
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
GRID_BG_COLOR = pygame.Color('#E8E8E8')  # 棋盘大底板的颜色（浅灰）
CELL_BG_COLOR = pygame.Color('#FFFFFF')  # 单元格内部的颜色（纯白）

# === UI 布局数值常量 ===
TOP_BAR_HEIGHT = 50
BOTTOM_BAR_HEIGHT = 60
UI_FONT_SIZE = 24
BTN_FONT_SIZE = 22
