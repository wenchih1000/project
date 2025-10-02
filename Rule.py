from Tile import *

from dataclasses import dataclass

@dataclass
class RuleContext:
    IsExposed: bool = False         # 標誌是否吃碰過
    IsDealer: bool = False          # 莊家
    IsSelfDraw: bool = False        # 自摸
    IsRobbingGong: bool = False     # 搶槓胡牌
    IsGongOnFlower: bool = False    # 槓上開花
    IsLastTileDraw: bool = False    # 海底自摸
    IsLastTileDiscard: bool = False # 河底撈魚
    IsHeavenlyHand: bool = False    # 天胡
    IsWinningHand: bool = False     # 地胡
    IsHumanlyHand: bool = False     # 人胡
    IsPlainHand: bool = False       # 平胡
    # 新增的聽牌型態旗標 (假設這些情況互斥，且只算最高的一種)
    IsSingleWait: bool = False      # 獨聽/單吊 (1台)
    IsEdgeWait: bool = False        # 邊張 (1台)
    IsCenterWait: bool = False      # 中洞/崁張 (1台)
    IsPairWait: bool = False        # 兩面聽/對倒/複合聽 (通常不計台，是平胡的必要條件)
    PlayerWind: int = 0             # 玩家風台
    RoundWind: int = 0              # 風局台
    DealerStreak: int = 0           # 連莊/連拉
    FlowerTiles: list[Tile] = []    # 花牌

@dataclass
class Partition:
    Pair: tuple[Tile, Tile]                    # 1對
    Pongs: list[tuple[Tile, Tile, Tile]]       # 碰
    Kongs: list[tuple[Tile, Tile, Tile, Tile]] # 槓
    Chows: list[tuple[Tile, Tile, Tile]]       # 吃

    ConcealedPongs: int = 0                    # 暗刻
    ConcealedKongs: int = 0                    # 暗槓
    # 增加一個屬性來標記哪些搭子是吃/碰/明槓來的 (exposed)
    ExposedMelds: int = 0 # 明搭:假設這代表吃/碰/明槓的總組數 (Partition應負責計算)

# 定義Taiwan麻將規則
class Rule:
    def __init__(self):
        pass