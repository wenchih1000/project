import pygame
from pygame import Rect

pygame.init()
W, H = 960, 800
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("台灣16張麻將 - 風格排版示範")

# 字型（Windows 可用 "標楷體" 或 "PMingLiU"；跨平台退回預設）
def try_font(name, size):
    # print(pygame.font.get_fonts())
    try:
        return pygame.font.SysFont(name, size)
    except:
        return pygame.font.SysFont("SimHei", size)

font_ui = try_font("PMingLiU", 20)
font_mid = try_font("PMingLiU", 28)
font_big = try_font("PMingLiU", 44) # 標楷體, SimHei

# 顏色
GREEN = (10, 90, 50)
TABLE_DK = (6, 70, 40)
WHITE = (250, 250, 250)
BLACK = (15, 15, 15)
INK = (30, 30, 30)
ACCENT = (230, 200, 90)
GOLD = (200, 150, 20)
BACK = (196, 160, 112)
FRAME = (40, 40, 40)
SILVER = (210, 210, 210)

# 牌尺寸與間距
TILE_W, TILE_H = 44, 64
TILE_GAP = 0

# 背面牌在左右家轉向，採橫向（寬=高，高=寬）
def tile_rect(x, y, w=TILE_W, h=TILE_H):
    return Rect(x, y, w, h)

# 畫正面牌（簡化：用字串代表牌面）
def draw_front_tile(surface, x, y, text, highlight=False):
    r = tile_rect(x, y)
    pygame.draw.rect(surface, WHITE, r, border_radius=6)
    pygame.draw.rect(surface, FRAME, r, 2, border_radius=6)
    if highlight:
        pygame.draw.rect(surface, ACCENT, r.inflate(6, 6), 3, border_radius=8)
    img = font_ui.render(text, True, INK)
    surface.blit(img, (x + (TILE_W - img.get_width()) // 2, y + (TILE_H - img.get_height()) // 2))

# 畫背面牌（直立或橫放）
def draw_back_tile(surface, x, y, vertical=True):
    if vertical:
        r = tile_rect(x, y)
    else:
        r = tile_rect(x, y, TILE_H, TILE_W)  # 橫放
    pygame.draw.rect(surface, BACK, r, border_radius=6)
    pygame.draw.rect(surface, FRAME, r, 2, border_radius=6)
    # 背面花紋
    inner = r.inflate(-10, -10)
    pygame.draw.rect(surface, TABLE_DK, inner, border_radius=4)
    pygame.draw.rect(surface, FRAME, inner, 1, border_radius=4)

# 封裝座標計算
def line_positions_horizontal(center_x, y, count=16, w=TILE_W, gap=TILE_GAP):
    total_w = count * w + (count - 1) * gap
    start_x = int(center_x - total_w / 2)
    return [(start_x + i * (w + gap), y) for i in range(count)]

def line_positions_vertical(x, center_y, count=16, h=TILE_H, gap=TILE_GAP):
    gap = -20
    center_y += 10
    total_h = count * h + (count - 1) * gap
    start_y = int(center_y - total_h / 2)
    return [(x, start_y + i * (h + gap)) for i in range(count)]

# 版面基準
CENTER_X, CENTER_Y = W // 2, H // 2
MARGIN = 20

# 四家牌列座標
bottom_y = H - MARGIN - TILE_H
top_y    = MARGIN
left_x   = MARGIN
right_x  = W - MARGIN - TILE_H  # 橫放背面牌的寬度用 TILE_H

pos_bottom = line_positions_horizontal(CENTER_X, bottom_y, count=16)
pos_top    = line_positions_horizontal(CENTER_X,  top_y,    count=16)
pos_left   = line_positions_vertical(left_x,     CENTER_Y,  count=16)
pos_right  = line_positions_vertical(right_x,    CENTER_Y,  count=16)

# 自家16張示例（替換成你的實際牌）
my_tiles = [
    "1萬","1萬","1萬","2萬","2萬","3萬","4萬","5萬",
    "2筒","2筒","3筒","3筒","北","北","中","白"
]

# 中央牌河網格（6x6）
RIVER_COLS, RIVER_ROWS = 6, 6
RIVER_CELL_W, RIVER_CELL_H = TILE_W + 4, TILE_H + 4
river_origin = (CENTER_X - (RIVER_COLS * RIVER_CELL_W) // 2, CENTER_Y - (RIVER_ROWS * RIVER_CELL_H) // 2 - 120)

# 假資料：放一些已打出的牌（最多 20 張示意）
river_tiles = ["5萬","7筒","白","發","2條","3萬","9筒","東","1萬","8條","4筒","南","中","6筒","2萬"]

def draw_river(surface):
    x0, y0 = river_origin
    for i, t in enumerate(river_tiles):
        row = i // RIVER_COLS
        col = i % RIVER_COLS
        x = x0 + col * RIVER_CELL_W
        y = y0 + row * RIVER_CELL_H
        draw_front_tile(surface, x, y, t)

# 摸牌牆：右上區塊兩層堆疊視覺
def draw_wall(surface, stacks=18):
    # 兩層交錯
    base_x, base_y = CENTER_X + 180, CENTER_Y - 60
    dx, dy = 2, -1
    for i in range(stacks):
        x = base_x + i * dx
        y = base_y + i * dy
        draw_back_tile(surface, x, y, vertical=True)
    # 第二層
    base_x2, base_y2 = base_x, base_y + 10
    for i in range(stacks):
        x = base_x2 + i * dx
        y = base_y2 + i * dy
        draw_back_tile(surface, x, y, vertical=True)

# 中央風位與剩餘張數
def draw_center_info(surface, wind="北", remain=55):
    # 風位徽章
    badge = Rect(CENTER_X - 36, CENTER_Y - 110, 72, 72)
    pygame.draw.rect(surface, GOLD, badge, border_radius=12)
    pygame.draw.rect(surface, FRAME, badge, 3, border_radius=12)
    img_wind = font_big.render(wind, True, BLACK)
    surface.blit(img_wind, (badge.centerx - img_wind.get_width() // 2, badge.centery - img_wind.get_height() // 2))

    # 剩餘張數
    info = f"剩餘張數: {remain}"
    img_info = font_mid.render(info, True, SILVER)
    surface.blit(img_info, (CENTER_X - img_info.get_width() // 2, badge.bottom + 8))

# 頭像與分數（四角）
def draw_avatar(surface, cx, cy, name="玩家", score=18888):
    r = Rect(0,0,120,66)
    r.center = (cx, cy)
    pygame.draw.rect(surface, (70, 70, 90), r, border_radius=10)
    pygame.draw.rect(surface, (30, 30, 40), r, 2, border_radius=10)
    # 頭像圓框
    pygame.draw.circle(surface, (200, 200, 220), (r.left + 34, r.centery), 22)
    pygame.draw.circle(surface, (70, 70, 90), (r.left + 34, r.centery), 20)
    # 名稱與分數
    img_name = font_ui.render(name, True, WHITE)
    img_score = font_ui.render(str(score), True, ACCENT)
    surface.blit(img_name,  (r.left + 64, r.top + 10))
    surface.blit(img_score, (r.left + 64, r.top + 36))

def draw_all_avatars(surface):
    pad = 80#18
    # 左上
    draw_avatar(surface, 80 + pad, 60 + pad, "玩家", 1000)
    # 右上
    draw_avatar(surface, W - 80 - pad, 60 + pad, "玩家", 6000)
    # 左下
    draw_avatar(surface, 80 + pad, H - 60 - pad, "玩家", 3000)
    # 右下
    draw_avatar(surface, W - 80 - pad, H - 60 - pad, "玩家", 18800)

# 聽牌提示＆操作按鈕（底部中偏左）
def draw_ui_panel(surface):
    # 聽牌提示
    tip = "聽牌提示：3筒 → 混一色；白 → 對對胡"
    img_tip = font_ui.render(tip, True, ACCENT)
    surface.blit(img_tip, (MARGIN + 210, H - 120))

    # 操作按鈕
    labels = ["吃", "碰", "槓", "胡", "跳過"]
    x, y = MARGIN + 200, H - 200
    for lab in labels:
        r = Rect(x, y, 84, 36)
        pygame.draw.rect(surface, (180, 140, 40), r, border_radius=8)
        pygame.draw.rect(surface, FRAME, r, 2, border_radius=8)
        img = font_ui.render(lab, True, BLACK)
        surface.blit(img, (r.centerx - img.get_width()//2, r.centery - img.get_height()//2))
        x += 92

clock = pygame.time.Clock()
running = True
while running:
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False

    screen.fill(GREEN)

    # 中央區塊
    draw_center_info(screen, wind="北", remain=55)
    draw_river(screen)
    draw_wall(screen, stacks=18)

    # 四家手牌
    # 自家（底部）正面 16 張
    for (x, y), t in zip(pos_bottom, my_tiles):
        draw_front_tile(screen, x, y, t)
    # 對家（頂部）背面橫排 16 張
    for (x, y) in pos_top:
        draw_back_tile(screen, x, y, vertical=True)
    # 左側（上家）背面直排 16 張（橫放圖塊）
    for (x, y) in pos_left:
        draw_back_tile(screen, x, y, vertical=False)
    # 右側（下家）背面直排 16 張（橫放圖塊）
    for (x, y) in pos_right:
        draw_back_tile(screen, x, y, vertical=False)

    # 四角頭像＋分數
    draw_all_avatars(screen)

    # 底部 UI
    draw_ui_panel(screen)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()