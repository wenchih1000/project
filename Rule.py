from Tile import *

from dataclasses import dataclass

@dataclass
class GameContext:
    is_exposed: bool = False         # 標誌是否吃碰過
    # 保持原樣，結構清晰
    is_dealer: bool = False          # 莊家
    is_self_draw: bool = False       # 自摸
    is_robbing_gong: bool = False    # 搶槓胡牌
    is_gong_kai: bool = False        # 槓上開花
    is_last_tile_draw: bool = False  # 海底自摸
    is_first_turn_win: bool = False  # 開局胡牌
    # 新增的聽牌型態旗標 (假設這些情況互斥，且只算最高的一種)
    is_single_wait: bool = False     # 獨聽/單吊 (1台)
    is_edge_wait: bool = False       # 邊張 (1台)
    is_center_wait: bool = False     # 中洞/崁張 (1台)
    # is_pair_wait: bool = False     # 兩面聽/對倒/複合聽 (通常不計台，是平胡的必要條件)
    player_wind: int = 0             # 玩家風台
    round_wind: int = 0              # 風局台
    dealer_streak: int = 0           # 連莊/連拉
    flower_tiles: list[Tile] = None  # 花牌

@dataclass
class Partition:
    # 保持原樣
    pair: tuple[Tile, Tile]                    # 1對
    pungs: list[tuple[Tile, Tile, Tile]]       # 碰
    kongs: list[tuple[Tile, Tile, Tile, Tile]] # 槓
    chows: list[tuple[Tile, Tile, Tile]]       # 吃
    concealed_pungs: int = 0                   # 暗刻
    concealed_kongs: int = 0                   # 暗槓
    # 增加一個屬性來標記哪些搭子是吃/碰/明槓來的 (exposed)
    exposed_melds: int = 0 # 明搭:假設這代表吃/碰/明槓的總組數 (Partition應負責計算)

# 定義Taiwan麻將規則
class Rule:
    def __init__(self):
        pass