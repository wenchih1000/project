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
    PlayerWind: int = 0             # 玩家風台 (1:東 2:南 3:西 4:北)
    RoundWind: int = 0              # 風局台   (1:東 2:南 3:西 4:北)
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

        # FirstTile = None
        # for key, val in hand.items():
        #     if val > 0:
        #         FirstTile = key
        #         break
        # if FirstTile == None:
        #     return False # 應該在第一個檢查點就返回

        FirstTile = sorted(hand.keys())[0]
        if not FirstTile:
            return False # 應該在第一個檢查點就返回

        # 1. 嘗試以這張牌作為「眼」
        if pairsNum < 1 and hand[FirstTile] >= 2:
            hand[FirstTile] -= 2

            if hand[FirstTile] == 0:
                del hand[FirstTile]
            if self.CanWin(hand, pairsNum + 1):
                return True
            hand[FirstTile] += 2 # 回溯
            
        # 2. 嘗試以這張牌組成「刻子」
        if hand[FirstTile] >= 3:
            hand[FirstTile] -= 3

            if hand[FirstTile] == 0:
                del hand[FirstTile]
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

                # 清理計數為 0 的牌
                hand = Counter({k: v for k, v in hand.items() if v > 0})
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


    def Calculate(self, partition: Partition, context: RuleContext) -> tuple[int, list[Tile]]:
        """
        計算台灣16張麻將的總台數。

        返回: (總台數, [台數名稱列表])
        """
        Score = 0
        ScoreNameList = []

        # 1. 數據預處理
        AllMelds = partition.Pongs + partition.Kongs + partition.Chows
        AllTiles = [tile for meld in AllMelds for tile in meld] + list(partition.Pair)
        PongsKongs = partition.Pongs + partition.Kongs # 所有的刻子和槓子

        # 門清判斷：exposed_melds 應為 0 
        # 由於 Partition 結構沒有提供每個 meld 的 exposed 狀態，我們依賴 Partition.exposed_melds (假設已從外部計算好)
        IsMenqing = partition.ExposedMelds == 0

        # 2. 字牌刻子計數
        HonorPongsKongs = [meld for meld in PongsKongs if meld[0].IsHonor()]
        WindPongsCount = sum(1 for meld in HonorPongsKongs if meld[0].IsWind())
        ArrowPongsCount = sum(1 for meld in HonorPongsKongs if meld[0].IsArrow())

        # --- A. 極致牌型 (最高層級，可能需互斥或包含) ---

        # 天胡/地胡 (16台，最高優先)
        if context.IsHeavenlyHand:
            Name = "天胡" if context.IsDealer else "地胡"
            ScoreNameList.append(f"{Name} (16台)")
            return 16, ScoreNameList

        # 大四喜 (16台)
        IsBigWind = False
        if WindPongsCount == 4:
            IsBigWind = True
            ScoreNameList.append("大四喜 (16台)"); Score += 16

        # --- B. 花色/結構牌型 (次高層級，互相獨立或包含) ---

        IsAllHonor = all(t.IsHonor() for t in AllTiles)

        # 字一色 (8台)
        if IsAllHonor and WindPongsCount != 4: # "大四喜" not in ScoreNameList:
            ScoreNameList.append("字一色 (8台)"); Score += 8

        # 大三元 (8台)
        IsBigArrow = False
        if ArrowPongsCount == 3:
            IsBigArrow = True
            ScoreNameList.append("大三元 (8台)"); Score += 8

        # 清一色 (8台) / 混一色 (4台)
        SuitTiles = [t for t in AllTiles if not t.IsHonor()]
        NumSuits = len({t.Suit for t in SuitTiles})

        if NumSuits <= 1 and not IsAllHonor:
            if not SuitTiles: # 避免牌組全為字牌但無字一色的情況
                pass
            elif not any(t.IsHonor() for t in AllTiles):
                ScoreNameList.append("清一色 (8台)"); Score += 8
            elif any(t.IsHonor() for t in AllTiles):
                ScoreNameList.append("混一色 (4台)"); Score += 4

        # 小四喜 (8台)
        IsWindPair = partition.Pair[0].IsWind()
        IsSmallWind = False
        if WindPongsCount == 3 and IsWindPair: #"大四喜" not in ScoreNameList:
            IsSmallWind = True
            ScoreNameList.append("小四喜 (8台)"); Score += 8

        # 小三元 (4台)
        IsArrowPair = partition.Pair[0].IsArrow()
        IsSmallArrow = False
        if ArrowPongsCount == 2 and IsArrowPair:# and "大三元" not in ScoreNameList:
            IsSmallArrow = True
            ScoreNameList.append("小三元 (4台)"); Score += 4

        # 碰碰胡 (4台) - 結構台
        if not partition.Chows:
            ScoreNameList.append("碰碰胡 (4台)"); Score += 4

        # --- C. 暗刻/順子牌型 (最低層級，可疊加於花色台，互斥於同結構高台) ---

        # 五暗刻 (8台) / 四暗刻 (5台) / 三暗刻 (2台)
        ConcealedCount = partition.ConcealedPongs + partition.ConcealedKongs

        if ConcealedCount == 5:
            ScoreNameList.append("五暗刻 (8台)"); Score += 8
        elif ConcealedCount == 4:
            ScoreNameList.append("四暗刻 (5台)"); Score += 5 
        elif ConcealedCount == 3:
            ScoreNameList.append("三暗刻 (2台)"); Score += 2

        # 平胡 (2台) - 結構台，與刻子牌型互斥
        IsPureChow = len(partition.Chows) == 5 and not PongsKongs
        IsValidPlainHand = IsPureChow and not partition.Pair[0].IsHonor()

        # 平胡必須無其他刻子結構台 (如三暗刻/碰碰胡) 且花色台數不宜過高
        if IsValidPlainHand and ConcealedCount < 3:#not any(p in ScoreNameList for p in ["碰碰胡", "五暗刻", "四暗刻", "三暗刻"]):
            # 嚴格來說平胡與清一色/混一色可疊加，但各地規則不同，這裡假設可疊加
            ScoreNameList.append("平胡 (2台)"); Score += 2

        # --- D. 基礎與加成台數 (獨立加總) ---

        # 莊家與連莊
        if context.IsDealer:
            Score += 1
            ScoreNameList.append("莊家 (+1台)")

        # 門清與自摸 (門清一摸三)
        if IsMenqing and context.IsSelfDraw:
            Score += 3
            ScoreNameList.append("門清一摸三 (3台)")
        elif IsMenqing:
            Score += 1
            ScoreNameList.append("門清 (1台)")
        elif context.IsSelfDraw:
            Score += 1
            ScoreNameList.append("自摸 (1台)")

        # ** 新增：聽牌型態 (1 台)**
        # 這些台數通常是互斥的，且只計算最高的或其中一個。
        if context.IsSingleWait:
            Score += 1; ScoreNameList.append("獨聽/單吊 (+1台)")
        elif context.IsEdgeWait:
            Score += 1; ScoreNameList.append("邊張 (+1台)")
        elif context.IsCenterWait:
            Score += 1; ScoreNameList.append("中洞/崁張 (+1台)")

        # 風牌與三元牌 (單獨計算，避免被大小四喜/三元完全覆蓋)
        for meld in HonorPongsKongs:
            #HonorMin, HonorMax = 1, 7
            rank = meld[0].Num

            # 三元牌 (中發白)
            if rank in ARROW and not not IsSmallArrow and not IsBigArrow:#any(p in ScoreNameList for p in ["大三元", "小三元"]):
                Score += 1
                ScoreNameList.append(f"{meld[0].toStr()} (+1台)")

            # 風牌 (圈風、門風)
            if rank in WIND:
                WindValue = rank
                # 圈風牌
                if WindValue == context.RoundWind and not IsBigWind: #"大四喜" not in ScoreNameList:
                    Score += 1
                    ScoreNameList.append(f"圈風牌({meld[0].toStr()}) (+1台)")
                # 門風牌
                if WindValue == context.PlayerWind and not IsSmallWind and not IsBigWind:#any(p in ScoreNameList for p in ["大四喜", "小四喜"]):
                    # 小四喜已涵蓋門風刻，故不重複計
                    Score += 1
                    ScoreNameList.append(f"門風牌({meld[0].toStr()}) (+1台)")

        # 花牌與正花
        for flower in context.FlowerTiles:
            Score += 1 # 每一張花牌算 1 台
            ScoreNameList.append(f"花牌 ({flower.toStr()}) (+1台)")
            if flower.Num == context.PlayerWind:
                Score += 1
                ScoreNameList.append(f"正花 (+1台)")

        # 額外事件台 (已在前面計算，這裡是為了保持邏輯完整性)
        if context.IsGongOnFlower: ScoreNameList.append("槓上開花 (+1台)")
        if context.IsLastTileDraw: ScoreNameList.append("海底撈月 (+1台)")
        if context.IsRobbingGong: ScoreNameList.append("搶槓 (+1台)")

        return Score, ScoreNameList

if __name__ == '__main__':

    # 測試1
    hand = Tile.Alias2Tile(["1萬","2萬","3萬","3索","3索","3索","5筒","6筒","7筒","5筒","6筒","7筒","南","南","南","中","中"])
    rule = Rule()
    ret = rule.IsHu(hand)
    PrintLog("胡:"+str(ret))

    # 測試2
    hand = Tile.Alias2Tile(["2萬","3萬","3索","3索","3索","5筒","6筒","7筒","5筒","6筒","7筒","南","南","南","中","中"])
    ret = rule.FindAllWaits(hand)
    tmp = ""
    for t in ret:
        tmp += f"{t.toStr()} "
    PrintLog("聽:"+tmp)

    # #
    # # 計算台數
    # #

    # 測試3: 莊家連一，門清自摸，混一色碰碰胡帶門風
    
    # 假設 is_hu 函式回傳了這個牌組結構
    partition = Partition(
        Pair=Tile.Alias2Tile(['東', '東']), # 東風對
        Pongs=[],
        Kongs=[
            Tile.Alias2Tile(['1萬', '1萬', '1萬', '1萬']), 
            Tile.Alias2Tile(['2萬', '2萬', '2萬', '2萬']),
            Tile.Alias2Tile(['3萬', '3萬', '3萬', '3萬']), 
            Tile.Alias2Tile(['5萬', '5萬', '5萬', '5萬'])
        ],
        Chows=[],
        ConcealedPongs=0,
        ConcealedKongs=4 # 假設四個暗槓
    )

    context = RuleContext(
        IsDealer=True,
        IsSelfDraw=True,
        DealerStreak=2,
        PlayerWind=0, # 東風
        RoundWind=0,  # 東風圈
        FlowerTiles=Tile.Alias2Tile(['梅', '蘭', '竹', '菊', '春', '夏', '秋', '冬'])
    )

    total, breakdown = rule.Calculate(partition, context)
    
    print(f"胡牌牌型:\n\t{'\n\t'.join(breakdown)}")
    print(f"總台數: {total} 台")