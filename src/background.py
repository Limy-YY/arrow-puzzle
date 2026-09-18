# src/background.py
import pygame
import random
import os 
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, FLOATING_ARROW_COLORS, BASE_DIR # ✅ 新增：导入 BASE_DIR

class FloatingArrows:
    def __init__(self, count=25):
        self.count = count
        self.arrows = []
        
        # ✅ 新增：加载白色箭头素材
        self.arrow_image = self._load_arrow_image()

        for _ in range(count):
            self.arrows.append(self._create_arrow(random_start=True))

    def _load_arrow_image(self):
        """加载并缩放白色箭头素材"""
        # 拼接图片路径
        icon_path = os.path.join(BASE_DIR, 'assets', 'icons', 'arrow-icon-white.png')
        
        if os.path.exists(icon_path):
            # 加载图片并转换格式（保留透明通道）
            image = pygame.image.load(icon_path).convert_alpha()
            # 缩放到一个合适的大小，比如 30x30，你可以根据喜好调整
            return pygame.transform.smoothscale(image, (50, 50))
        else:
            print(f"⚠️ 警告：未找到箭头素材 {icon_path}，将回退到绘制三角形")
            return None

    def _create_arrow(self, random_start=False):
        size = random.randint(15, 35) # 大小可以稍微调整一下
        speed = random.uniform(0.3, 1.0)
        
        if random_start:
            x = random.randint(0, SCREEN_WIDTH)
            y = random.randint(0, SCREEN_HEIGHT)
        else:
            x = random.randint(0, SCREEN_WIDTH)
            y = SCREEN_HEIGHT + 50
            
        return {
            'pos': pygame.Vector2(x, y),
            'size': size,
            'speed': speed,
            'color': random.choice(FLOATING_ARROW_COLORS),
            # 给每个箭头一个随机旋转角度，让动态更自然
            'angle': random.randint(0, 360) 
        }

    def update(self):
        for arrow in self.arrows:
            arrow['pos'].y -= arrow['speed']
            # 让箭头在飘动时缓慢旋转
            arrow['angle'] += 0.2 
            
            if arrow['pos'].y < -50:
                new_arrow = self._create_arrow(random_start=False)
                arrow['pos'] = new_arrow['pos']
                arrow['size'] = new_arrow['size']
                arrow['speed'] = new_arrow['speed']
                arrow['color'] = new_arrow['color']
                arrow['angle'] = new_arrow['angle']

    def draw(self, surface):
        for arrow in self.arrows:
            if self.arrow_image:
                
                # 1. 创建一个和原图一样大小的临时 Surface
                temp_surface = pygame.Surface((arrow['size'], arrow['size']), pygame.SRCALPHA)
                
                # 2. 将白色箭头图片缩放后绘制到临时 Surface 上
                scaled_image = pygame.transform.smoothscale(self.arrow_image, (arrow['size'], arrow['size']))
                temp_surface.blit(scaled_image, (0, 0))
                
                # 3. 关键一步：使用 BLEND_RGB_MULT 模式进行着色
                temp_surface.fill(arrow['color'], special_flags=pygame.BLEND_RGB_MULT)
                
                # 4. 旋转图片
                rotated_image = pygame.transform.rotate(temp_surface, arrow['angle'])
                rect = rotated_image.get_rect(center=arrow['pos'])
                
                # 5. 绘制到屏幕上
                surface.blit(rotated_image, rect)
