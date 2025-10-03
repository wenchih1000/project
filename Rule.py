from Tile import *

from dataclasses import dataclass
from collections import Counter

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
    # 風台
    PlayerWind: int = 0             # 玩家風台
    RoundWind: int = 0              # 風局台
    #莊家台
    DealerStreak: int = 0           # 連莊/連拉
    # 花台
    FlowerTiles: list[Tile] = None  # 花牌

# 檢查手牌組了幾個搭
# 滿足胡牌條件:5搭x3 + 1對x2 = 17張
# 滿足聽牌條件:4搭x3 + 缺1張組成搭 + 1對x2 = 16張
#             4搭x3 + 2對x2 = 16張
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
# 檢查手上牌符合哪些胡牌情況
# 包含:聽牌、胡牌，吃、碰、槓
class Rule:
    HandLen = 17
    PairLen = 2
    NumHiLimit = 7 # ex:7,8,9
    AllTiles:list[Tile] = None

    def __init__(self):
        self.AllTiles = []
        for i in range(TileRange.CharMin.value, TileRange.CharMax.value + 1):
            self.AllTiles.extend([Tile({'suit':SUIT.CHAR, 'num':i})])
            self.AllTiles.extend([Tile({'suit':SUIT.DOT, 'num':i})])
            self.AllTiles.extend([Tile({'suit':SUIT.STICK, 'num':i})])
        for i in range(TileRange.HonorMin.value, TileRange.HonorMax.value + 1):
            self.AllTiles.extend([Tile({'suit':SUIT.HONOR, 'num':i})])

    def IsHu(self, hand: list[Tile]) -> bool:
        """
        主函式：判斷 17 張牌是否胡牌
        hand: e.g., ['1p','1p','1m', '2m', '3m', ...]
        """
        if len(hand) != self.HandLen:
            return False

        # 1. 前置檢查特殊牌型
        # 使用 Counter來計算每一種牌重複數量 key:tile, val:num
        HandCounts = Counter(hand)
        # 16張麻將沒有七對子台
        # if IsSevenPairs(HandCounts):
        #     return True

        # 2. 遍歷所有可能的眼睛
        for tile in HandCounts:
            # 假設為對牌
            if HandCounts[tile] >= self.PairLen:
                # 複製一份手牌來操作，避免影響原始資料
                TempCounts = HandCounts.copy()

                # 移除眼睛
                TempCounts[tile] -= self.PairLen
                if TempCounts[tile] == 0:
                    del TempCounts[tile]

                # 3. 遞迴拆解剩下的 15 張牌
                if self.CanBeMelds(TempCounts):
                    return True # 只要有一種組合成功，就是胡牌

        return False

    # 驗證手牌全部是否都可成為搭(順子或刻子)
    def CanBeMelds(self, hand: Counter) -> bool:
        """
        遞迴函式：判斷手牌是否能被拆解成 5 組順子或刻子
                 5搭x3 = 15張
        """
        # Base Case: 手牌都拆完了，成功！
        if not hand:
            return True

        # 排序後取第一張牌開始拆解:遞迴移除刻子,遞迴移除順子
        FirstTile = sorted(hand.keys())[0]

        # Recursive Step 1: 嘗試組刻子(3張同樣牌)
        if hand[FirstTile] >= 3:
            # 移除刻子
            hand[FirstTile] -= 3
            if hand[FirstTile] == 0:
                del hand[FirstTile]

            # 遞迴移除刻子
            if self.CanBeMelds(hand.copy()): # 傳遞副本
                return True

            # 回溯 (Backtrack)
            hand[FirstTile] += 3

        # Recursive Step 2: 嘗試組順子 (字牌,花牌無法組順子)
        # 順子:7,8,9
        if FirstTile.Suit != SUIT.HONOR and FirstTile.Suit != SUIT.FLOWER and FirstTile.Num <= self.NumHiLimit:
            t1, t2, t3 = FirstTile, FirstTile + 1, FirstTile + 2
            if t1 in hand and t2 in hand and t3 in hand:
                # 移除順子
                hand[t1] -= 1
                hand[t2] -= 1
                hand[t3] -= 1

                # 清理計數為 0 的牌
                hand = Counter({k: v for k, v in hand.items() if v > 0})

                # 遞迴移除順子
                if self.CanBeMelds(hand.copy()): # 傳遞副本
                    return True

                # 回溯 (Backtrack)
                hand[t1] += 1
                hand[t2] += 1
                hand[t3] += 1

        # 如果所有組合都失敗
        return False

    # 遞歸核心：胡牌判斷 (Can Win) ---
    def CanWin(self, hand: Counter, pairsNum: int = 0) -> bool:
        """
        遞歸檢查一個牌組是否能分解成 N 組順子/刻子 (N=4, 14張牌時) 或 N-1 組 (13張牌時)。
        這個函數是麻將演算法的核心。
        """
        # 檢查是否已分解完成：牌堆已經空了 (count 都是 0)
        if not any(hand.values()):
            # 成功分解！
            return True

        # 排序後取第一張牌開始拆解:遞迴移除刻子,遞迴移除順子
        if len(hand) == 0:
            return False

        FirstTile = sorted(hand.keys())[0]
        if not FirstTile:
            return False # 應該在第一個檢查點就返回

        # 1. 嘗試以這張牌作為「眼」
        if pairsNum < 1 and hand[FirstTile] >= 2:
            hand[FirstTile] -= 2
            if self.CanWin(hand, pairsNum + 1):
                return True
            hand[FirstTile] += 2 # 回溯
            
        # 2. 嘗試以這張牌組成「刻子」
        if hand[FirstTile] >= 3:
            hand[FirstTile] -= 3
            if self.CanWin(hand, pairsNum):
                return True
            hand[FirstTile] += 3 # 回溯

        # 3. 嘗試以這張牌組成「順子」 (只對數字牌有效)
        if FirstTile.Suit != SUIT.HONOR and FirstTile.Suit != SUIT.FLOWER and FirstTile.Num <= self.NumHiLimit:
            t1, t2, t3 = FirstTile, FirstTile + 1, FirstTile + 2

            # 確保順子中的三張牌都存在
            if t1 in hand and t2 in hand and t3 in hand:
                hand[t1] -= 1
                hand[t2] -= 1
                hand[t3] -= 1
                if self.CanWin(hand, pairsNum):
                    return True
                hand[t1] += 1
                hand[t2] += 1
                hand[t3] += 1

        return False

    # --- 聽牌演算法主函數 (Find All Waits) ---
    def FindAllWaits(self, concealedHand: list[Tile]) -> list[Tile]:
        """
        找出所有能讓當前手牌胡牌的牌 (聽牌列表)。
        concealedHand: 玩家尚未公開的手牌 (通常是 16 張牌，但演算法只處理組成 4*3+2 的牌)
        返回: 聽牌列表 (e.g., ['2m', '5m', '8p'])
        """

        waits: list[Tile] = []
        # 計算基礎牌數 (台灣麻將 16 張，但胡牌分解是 4*3+2缺1張組成順或刻，即 14 張，省掉對牌)
        # 我們假設 concealedHand 已經是準備胡牌的 16 張手牌，但分解時只需檢查 14 張的結構
        # 為了簡化，我們只檢查手牌數量是否滿足 16 張牌的結構 (4個搭子和1個眼)

        # 註：這裡假設傳入的 concealedHand 是玩家的「手牌」，不含吃、碰、明槓的牌。
        # 實際計台時，需要將所有牌（包含吃、碰、槓）加起來，總共是 16 張。
        # 為符合 14 張牌的核心分解邏輯，我們假設傳入的手牌是 N=14 的牌型。

        # 步驟 1: 遍歷 34 種牌
        for tile in self.AllTiles:
            # 步驟 2: 試著將這張牌加入手牌
            HandCounts = Counter(concealedHand)

            # 如果試聽的牌在手牌中已經有 4 張了 (無法再摸第 5 張)，則跳過
            if HandCounts[tile] == 4:
                continue

            HandCounts[tile] += 1

            # 步驟 3: 檢查加入試聽牌後，牌組總數是否滿足胡牌條件 (4組搭子+1眼 = 14張)
            if sum(HandCounts.values()) % 3 == 2:
                # 步驟 4: 使用遞歸函數判斷是否胡牌
                if self.CanWin(HandCounts):
                    waits.append(tile)

        return waits

if __name__ == '__main__':

    tmp = ["1萬","2萬","3萬","3索","3索","3索","5筒","6筒","7筒","5筒","6筒","7筒","南","南","南","中","中"] 
    hand = []
    for i in tmp:
        hand.append(Tile({'alias':i}))

    rule = Rule()
    ret = rule.IsHu(hand)
    print(ret)

    # ret = rule.IsHu(['3m', '3m', '3m', '4m', '5m', '6m', '7m', '7m', '7m', '1p', '1p', '3p', '4p', '5p', '6p', '7p', '8p'])
    # print(ret)

    # player = ['2m', '2m', '4m', '5m', '6m', '6m', '7m', '8m', '1p', '2p', '3p', '4p', '5p', '6p', 'F', 'F']
    hand.pop(0)
    ret = rule.FindAllWaits(hand)
    print(ret)