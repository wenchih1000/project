from Tile import *

from dataclasses import dataclass
from collections import Counter

@dataclass
class HandCondition:
    IsExposed: bool = False         # 標誌是否吃碰過
    IsDealer: bool = False          # 莊家
    IsSelfDraw: bool = False        # 自摸
    IsRobbingGong: bool = False     # 搶槓胡牌
    IsGongOnFlower: bool = False    # 槓上開花
    IsLastTileDraw: bool = False    # 海底自摸
    IsLastTileDiscard: bool = False # 河底撈魚
    IsHeavenlyHand: bool = False    # 天胡
    IsWinningHand: bool = False     # 地胡
    CanHumanlyHand: bool = False     # 人胡
    IsPlainHand: bool = False       # 平胡
    # 新增的聽牌型態旗標 (假設這些情況互斥，且只算最高的一種)
    IsSingleWait: bool = False      # 獨聽/單吊 (1台)
    IsEdgeWait: bool = False        # 邊張 (1台)
    IsCenterWait: bool = False      # 中洞/崁張 (1台)

    IsPairWait: bool = False        # 兩面聽/對倒/複合聽 (通常不計台，是平胡的必要條件)
    # 風台
    SeatWind: WIND = None           # 玩家門風台 (1:東 2:南 3:西 4:北)
    RoundWind: WIND = None          # 圈風台     (1:東 2:南 3:西 4:北)
    #莊家台
    DealerStreak: int = 0           # 連莊/連拉
    # 花台
    SeatFlower: WIND = None         # 玩家正花台 (1:梅/春 2:蘭/夏 3:竹/秋 4:菊/冬)
    # RoundFlower: int = 0          # 圈花台     (5:春 6:夏 7:秋 8:冬)

# 檢查手牌組了幾個明/暗搭
# 對子/順子/刻子/槓子
# 滿足胡牌條件:5搭x3 + 1對x2 = 17張
# 滿足聽牌條件:4搭x3 + 缺1張組成搭 + 1對x2 = 16張
#             4搭x3 + 2對x2 = 16張

# 胡牌至少5組(順/刻/槓搭)+1組(對搭) = 6 Meld
class HandClassify:
    Pair: Meld = None           #   1組對子/眼
    Pongs: list[Meld]   = []    # 0~n組碰子/刻
    Kongs: list[Meld]   = []    # 0~n組槓子/槓
    Chows: list[Meld]   = []    # 0~n組吃子/順
    Flowers: list[Tile] = []    # 0~n張花牌

    IsValid:bool = True
    MeldLen = 5

    def __init__(self, melds:tuple[Meld], flowers:tuple[Tile]):
        for meld in melds:
            if meld.Type == MELD.PAIR:
                self.Pair = meld
            elif meld.Type == MELD.PONG:
                self.Pongs.append(meld)
            elif meld.Type == MELD.KONG:
                self.Kongs.append(meld)
            elif meld.Type == MELD.CHOW:
                self.Chows.append(meld)
        for f in flowers:
            self.Flowers.append(f)

        if self.Pair == None:
            self.IsValid = False
        if len(self.Pongs) + len(self.Kongs) + len(self.Chows) < self.MeldLen:
            self.IsValid = False

# 定義Taiwan麻將規則
# 檢查手上牌符合哪些胡牌情況
# 包含:聽牌、胡牌，吃、碰、槓
class Rule:
    HandLen = 17
    PairLen = 2
    MeldLen = 3
    KongLen = 4
    PongLen = 3
    NumHiLimit = 7 # ex:7,8,9
    AllTiles:list[Tile] = None
    Melds:list[Meld] = None

    def __init__(self):
        self.AllTiles = []
        for i in range(TileRange.CharMin.value, TileRange.CharMax.value + 1):
            self.AllTiles.extend([Tile({'suit':SUIT.CHAR, 'num':i})])
            self.AllTiles.extend([Tile({'suit':SUIT.DOT, 'num':i})])
            self.AllTiles.extend([Tile({'suit':SUIT.STICK, 'num':i})])
        for i in range(TileRange.HonorMin.value, TileRange.HonorMax.value + 1):
            self.AllTiles.extend([Tile({'suit':SUIT.HONOR, 'num':i})])

    # 確認手牌是否可槓牌
    @staticmethod
    def CanConcealKong(hand: list[Tile]) -> bool:
        HandCounts = Counter(hand)
        for tile in HandCounts:
            if HandCounts[tile] >= Rule.KongLen:
                return True
        return False

    @staticmethod
    def CanKong(hand: list[Tile], discard: Tile) -> bool:
        HandCounts = Counter(hand)
        for tile in HandCounts:
            if HandCounts[tile] >= Rule.KongLen-1 and tile == discard:
                return True
        return False

    @staticmethod
    def CanPong(hand: list[Tile], discard: Tile) -> bool:
        HandCounts = Counter(hand)
        for tile in HandCounts:
            if HandCounts[tile] >= Rule.PongLen-1 and tile == discard:
                return True
        return False

    @staticmethod
    def CanChow(hand: list[Tile], discard: Tile) -> bool:
        if discard.IsHonor() or discard.IsFlower():
            return False

        t1, t2 = None, None
        # 邊張
        if discard.Num == 1:
            t1, t2 = discard + 1, discard + 2
        elif discard.Num == 9:
            t1, t2 = discard - 1, discard - 2
        # 中洞
        else:
            t1, t2 = discard - 1, discard + 1

        if t1 in hand and t2 in hand:
            return True
        return False

    @staticmethod
    def GetKongTile(hand: list[Tile]) -> list[Tile]:
        HandCounts = Counter(hand)
        tmp = []
        for tile in HandCounts:
            if HandCounts[tile] >= Rule.KongLen:
                tmp.append(tile)
        return tmp

    # 確認手牌是否可胡牌
    def CanHu(self, hand: list[Tile]) -> bool:
        self.Melds = []
        """
        主函式：判斷牌組是否胡牌
        hand: e.g., ['1p','1p','1m', '2m', '3m', ...]
        """
        ValidLen = [i for i in range(self.PairLen, self.HandLen+1, self.MeldLen)]
        if len(hand) not in ValidLen:
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
                    #新增對子
                    self.Melds.append(Meld(False, [tile, tile]))
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
                #新增刻子
                self.Melds.append(Meld(False, [FirstTile, FirstTile, FirstTile]))
                return True

            # 回溯 (Backtrack)
            hand[FirstTile] += 3

        # Recursive Step 2: 嘗試組順子 (字牌,花牌無法組順子)
        # 順子:7,8,9
        if FirstTile.Suit != SUIT.HONOR and FirstTile.Suit != SUIT.FLOWER and FirstTile.Num <= self.NumHiLimit:
            t1, t2, t3 = FirstTile, FirstTile + 1, FirstTile + 2
            if t1 in hand and t2 in hand and t3 in hand:
                # 移除順子
                hand[t1] -= 1;hand[t2] -= 1;hand[t3] -= 1

                # 清理計數為 0 的牌
                hand = Counter({k: v for k, v in hand.items() if v > 0})

                # 遞迴移除順子
                if self.CanBeMelds(hand.copy()): # 傳遞副本
                    #新增順子
                    self.Melds.append(Meld(False, [t1, t2, t3]))
                    return True

                # 回溯 (Backtrack)
                hand[t1] += 1;hand[t2] += 1;hand[t3] += 1

        # 如果所有組合都失敗
        return False
    
    def GetMelds(self) -> list[Meld]:
        return self.Melds

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
            # 移除
            hand[FirstTile] -= 2
            if hand[FirstTile] == 0:
                del hand[FirstTile]
            if self.CanWin(hand, pairsNum + 1):
                return True
            # 回溯
            hand[FirstTile] += 2 
            
        # 2. 嘗試以這張牌組成「刻子」
        if hand[FirstTile] >= 3:
            # 移除
            hand[FirstTile] -= 3
            if hand[FirstTile] == 0:
                del hand[FirstTile]
            if self.CanWin(hand, pairsNum):
                return True
            # 回溯
            hand[FirstTile] += 3 

        # 3. 嘗試以這張牌組成「順子」 (只對數字牌有效)
        if FirstTile.Suit != SUIT.HONOR and FirstTile.Suit != SUIT.FLOWER and FirstTile.Num <= self.NumHiLimit:
            t1, t2, t3 = FirstTile, FirstTile + 1, FirstTile + 2

            # 確保順子中的三張牌都存在
            if t1 in hand and t2 in hand and t3 in hand:
                # 移除
                hand[t1] -= 1;hand[t2] -= 1;hand[t3] -= 1

                # 清理計數為 0 的牌
                hand = Counter({k: v for k, v in hand.items() if v > 0})
                if self.CanWin(hand, pairsNum):
                    return True
                # 回溯
                hand[t1] += 1;hand[t2] += 1;hand[t3] += 1

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

#
# 定義台數
#
class ScoreName:
    __Name:str = ''
    __Score:int = 0
    __TileName:str = ''

    @property
    def Name(self) -> str:
        if self.__TileName != '':
            return self.__Name + f"({self.__TileName})"
        return self.__Name

    @property
    def TileName(self) -> str:
        return self.__TileName

    @TileName.setter
    def TileName(self, name: str):
        self.__TileName = name

    @property
    def Score(self) -> int:
        return self.__Score
    @Score.setter
    def Score(self, score: int):
        self.__Score = score

    def __init__(self, name: str, score: int, tileName: str = ''):
        self.__Name = name
        self.__Score = score
        self.__TileName = tileName

    def __str__(self) -> str:
        return self.__Name

    def __int__(self) -> int:
        return self.__Score

    def __add__(self, other:'ScoreName') -> int:
        return self.Score + other.Score

# --- 計算台數 ---
class TaiID:
    HeavenlyHand = ScoreName('天胡', 24)
    EarthlyHand = ScoreName('地胡', 16) # WinningHand
    HumanlyHand = ScoreName('人胡', 16)
    PlainHand = ScoreName('平胡', 2)
    BaseHand = ScoreName('屁胡', 0)
    ConcealedHand = ScoreName('門清', 1)

    AllHonors = ScoreName('字一色', 16)
    Big4Winds = ScoreName('大四喜', 16)
    Big3Dragons = ScoreName('大三元', 8)
    Little4Winds = ScoreName('小四喜', 8)
    Little3Dragons = ScoreName('小三元', 4)

    AllSuit = ScoreName('清一色', 8)
    MixedSuit = ScoreName('混一色', 4)
    N8Immortals = ScoreName('八仙過海', 8)
    N7Grab1 = ScoreName('七搶一', 8)

    N5ConcealedPongs = ScoreName('五暗刻', 8)
    N4ConcealedPongs = ScoreName('四暗刻', 5)
    N3ConcealedPongs = ScoreName('三暗刻', 2)
    DragonPong = ScoreName('三元刻', 1) # 中/發/白
    AllPongs = ScoreName('碰碰胡', 4)

    ConcealedSelfDrawn = ScoreName('門清自摸', 3)
    CompleteDiscard = ScoreName('全求人', 2)
    Dealer = ScoreName('莊家', 1)
    SelfDraw = ScoreName('自摸', 1)

    FlowerKong = ScoreName('花槓', 1) # 梅蘭竹菊/春夏秋冬
    # Flowers = ScoreName('花牌', 1)
    RoundFlower = ScoreName('圈花', 1)
    SeatFlower = ScoreName('正花', 1)
    # Winds = ScoreName('風牌', 1)
    RoundWind = ScoreName('圈風', 1)
    SeatWind = ScoreName('門風', 1)

    SingleWait = ScoreName('獨聽', 1)  # 邊張/中洞/單吊眼睛
    EdgeWait = ScoreName('邊張', 1)
    CenterWait = ScoreName('中洞', 1)
    PairWait = ScoreName('單吊', 1)

    KongOnFlower = ScoreName('槓上開花', 1)
    RobbingKong = ScoreName('搶槓', 1)
    LastTileDraw = ScoreName('海底撈月', 1)
    LastTileDiscard = ScoreName('河底撈魚', 1)
    DealerStreak = ScoreName('連莊', 2)

    @staticmethod
    def GetScoreName(name:ScoreName, tileName:str) -> ScoreName:
        return ScoreName(name.Name, name.Score, tileName)

class Score:
    classify:HandClassify = None 
    condition:HandCondition = None

    def __init__(self, classify: HandClassify, condition: HandCondition):
        self.classify = classify
        self.condition = condition

    def Calculate(self) -> tuple[int, list[ScoreName]]:
        """
        計算台灣16張麻將的總台數。

        返回: (總台數, [台數名稱列表])
        """
        Score = 0
        ScoreNameList = []

        # 1. 數據預處理
        AllMelds = self.classify.Pongs + self.classify.Kongs + self.classify.Chows
        AllTiles = [tile for meld in AllMelds for tile in meld.Tiles] + list(self.classify.Pair.Tiles)
        PongsKongs = self.classify.Pongs + self.classify.Kongs # 所有的刻子和槓子

        # 門清判斷：exposed_melds 應為 0 
        IsMenqing = True
        if self.classify.Pair.Exposed:
            IsMenqing = False
        for meld in AllMelds:
            if meld.Exposed:
                IsMenqing = False
                break

        # 2. 字牌刻子計數
        HonorPongsKongs = [meld for meld in PongsKongs if meld.Tiles[0].IsHonor()]
        WindPongsCount = sum(1 for meld in HonorPongsKongs if meld.Tiles[0].IsWind())
        ArrowPongsCount = sum(1 for meld in HonorPongsKongs if meld.Tiles[0].IsArrow())

        # --- A. 極致牌型 (最高層級，可能需互斥或包含) ---

        # 天胡/地胡/人胡 (24台/16台，最高優先)
        if self.condition.IsHeavenlyHand:
            # 天胡
            if self.condition.IsDealer:
                Name = TaiID.HeavenlyHand
            # 地胡
            else:
                Name = TaiID.EarthlyHand

            ScoreNameList.append(Name); Score = Name.Score
            return Score, ScoreNameList
        # 人胡 16台
        elif self.condition.CanHumanlyHand:
            Name = TaiID.HumanlyHand
            ScoreNameList.append(Name); Score = Name.Score
            return Score, ScoreNameList

        # 大四喜 (16台)
        IsBigWind = False
        if WindPongsCount == 4:
            IsBigWind = True
            Name = TaiID.Big4Winds
            ScoreNameList.append(Name); Score += Name.Score

        # --- B. 花色/結構牌型 (次高層級，互相獨立或包含) ---

        IsAllHonor = all(t.IsHonor() for t in AllTiles)

        # 字一色 (8台)
        if IsAllHonor and WindPongsCount != 4: # "大四喜" not in ScoreNameList:
            Name = TaiID.AllHonors
            ScoreNameList.append(Name); Score += Name.Score

        # 大三元 (8台)
        IsBigArrow = False
        if ArrowPongsCount == 3:
            IsBigArrow = True
            Name = TaiID.Big3Dragons
            ScoreNameList.append(Name); Score += Name.Score

        # 清一色 (8台) / 混一色 (4台)
        SuitTiles = [t for t in AllTiles if not t.IsHonor()]
        NumSuits = len({t.Suit for t in SuitTiles})

        if NumSuits <= 1 and not IsAllHonor:
            if not SuitTiles: # 避免牌組全為字牌但無字一色的情況
                pass
            elif not any(t.IsHonor() for t in AllTiles):
                Name = TaiID.AllSuit
                ScoreNameList.append(Name); Score += Name.Score
            elif any(t.IsHonor() for t in AllTiles):
                Name = TaiID.MixedSuit
                ScoreNameList.append(Name); Score += Name.Score

        # 小四喜 (8台)
        IsWindPair = self.classify.Pair.Tiles[0].IsWind()
        IsSmallWind = False
        if WindPongsCount == 3 and IsWindPair: #"大四喜" not in ScoreNameList:
            IsSmallWind = True
            Name = TaiID.Little4Winds
            ScoreNameList.append(Name); Score += Name.Score

        # 小三元 (4台)
        IsArrowPair = self.classify.Pair.Tiles[0].IsArrow()
        IsSmallArrow = False
        if ArrowPongsCount == 2 and IsArrowPair:# and "大三元" not in ScoreNameList:
            IsSmallArrow = True
            Name = TaiID.Little3Dragons
            ScoreNameList.append(Name); Score += Name.Score

        # 碰碰胡 (4台) - 結構台
        if not self.classify.Chows:
            Name = TaiID.AllPongs
            ScoreNameList.append(Name); Score += Name.Score

        # --- C. 暗刻/順子牌型 (最低層級，可疊加於花色台，互斥於同結構高台) ---

        # 五暗刻 (8台) / 四暗刻 (5台) / 三暗刻 (2台)
        ConcealedCount = 0
        for meld in PongsKongs:
            if not meld.Exposed:
                ConcealedCount += 1

        if ConcealedCount == 5:
            Name = TaiID.N5ConcealedPongs
            ScoreNameList.append(Name); Score += Name.Score
        elif ConcealedCount == 4:
            Name = TaiID.N4ConcealedPongs
            ScoreNameList.append(Name); Score += Name.Score 
        elif ConcealedCount == 3:
            Name = TaiID.N3ConcealedPongs
            ScoreNameList.append(Name); Score += Name.Score

        # 平胡 (2台) - 結構台，與刻子牌型互斥
        IsPureChow = len(self.classify.Chows) == 5 and not PongsKongs
        IsValidPlainHand = IsPureChow and not self.classify.Pair.Tiles[0].IsHonor()

        # 平胡必須無其他刻子結構台 (如三暗刻/四暗刻/五暗刻/碰碰胡) 且花色台數不宜過高
        if IsValidPlainHand and ConcealedCount < 3:
            # 嚴格來說平胡與清一色/混一色可疊加，但各地規則不同，這裡假設可疊加
            Name = TaiID.PlainHand
            ScoreNameList.append(Name); Score += Name.Score

        # --- D. 基礎與加成台數 (獨立加總) ---

        # 莊家與連莊
        if self.condition.IsDealer:
            Name = TaiID.Dealer
            ScoreNameList.append(Name); Score += Name.Score

        if self.condition.DealerStreak > 0:
            Streak = self.condition.DealerStreak
            Name = TaiID.GetScoreName(TaiID.DealerStreak, f'連{Streak}拉{Streak}')
            # Name = TaiID.DealerStreak
            Name.Score *= self.condition.DealerStreak
            ScoreNameList.append(Name); Score += Name.Score

        # 門清與自摸 (門清一摸三)
        if IsMenqing and self.condition.IsSelfDraw:
            Name = TaiID.ConcealedSelfDrawn
            ScoreNameList.append(Name); Score += Name.Score
        elif IsMenqing:
            Name = TaiID.ConcealedHand
            ScoreNameList.append(Name); Score += Name.Score
        elif self.condition.IsSelfDraw:
            Name = TaiID.SelfDraw
            ScoreNameList.append(Name); Score += Name.Score

        # ** 新增：聽牌型態 (1 台)**
        # 這些台數通常是互斥的，且只計算最高的或其中一個。
        # 獨聽/單吊
        if self.condition.IsSingleWait:
            Name = TaiID.GetScoreName(TaiID.SingleWait, TaiID.PairWait.Name)
            # Name = TaiID.PairWait
            ScoreNameList.append(Name); Score += Name.Score
        # 邊張
        elif self.condition.IsEdgeWait:
            Name = TaiID.GetScoreName(TaiID.SingleWait, TaiID.EdgeWait.Name)
            # Name = TaiID.EdgeWait
            ScoreNameList.append(Name); Score += Name.Score
        # 中洞/崁張
        elif self.condition.IsCenterWait:
            Name = TaiID.GetScoreName(TaiID.SingleWait, TaiID.CenterWait.Name)
            # Name = TaiID.CenterWait
            ScoreNameList.append(Name); Score += Name.Score

        # 風牌與三元牌 (單獨計算，避免被大小四喜/三元完全覆蓋)
        for meld in HonorPongsKongs:
            rank = meld.Tiles[0].Num

            # 三元牌 (中發白) 必須無大三元/小三元
            if rank in ARROW and not IsSmallArrow and not IsBigArrow:

                Name = TaiID.GetScoreName(TaiID.DragonPong, meld.Tiles[0].toStr())
                # Name.TileName = meld[0].toStr()
                # meld[0].toStr()
                ScoreNameList.append(Name); Score += Name.Score

            # 風牌 (圈風、門風)
            if rank in WIND:
                WindValue = rank
                # 圈風牌 必須無大四喜
                if WindValue == self.condition.RoundWind.value and not IsBigWind:
                    Name = TaiID.GetScoreName(TaiID.RoundWind, meld.Tiles[0].toStr())
                    # meld[0].toStr()
                    ScoreNameList.append(Name); Score += Name.Score
                # 門風牌 必須無大四喜/小四喜
                if WindValue == self.condition.SeatWind.value and not IsSmallWind and not IsBigWind:
                    # 小四喜已涵蓋門風刻，故不重複計
                    Name = TaiID.GetScoreName(TaiID.SeatWind, meld.Tiles[0].toStr())
                    # meld[0].toStr()
                    ScoreNameList.append(Name); Score += Name.Score

        # 正花
        PeriodCount,PeriodName = 0,''
        GentlemenCount,GentlemenName = 0,''
        for flower in self.classify.Flowers:
            # 正花牌, 確認四君子和四季是否為正花
            Num = flower.Num if flower.Num <= 4 else flower.Num - 4
            if Num == self.condition.SeatFlower.value:
                Name = TaiID.GetScoreName(TaiID.SeatFlower, flower.toStr())
                # flower.toStr()
                ScoreNameList.append(Name); Score += Name.Score
            # 花槓
            if flower.Num in PERIOD:
                PeriodCount += 1
                PeriodName += flower.toStr()
                if PeriodCount == 4:
                    Name = TaiID.GetScoreName(TaiID.FlowerKong, PeriodName)
                    ScoreNameList.append(Name); Score += Name.Score
            if flower.Num in GENTLEMEN:
                GentlemenCount += 1
                GentlemenName += flower.toStr()
                if GentlemenCount == 4:
                    Name = TaiID.GetScoreName(TaiID.FlowerKong, GentlemenName)
                    ScoreNameList.append(Name); Score += Name.Score

        # 額外事件台 (已在前面計算，這裡是為了保持邏輯完整性)
        if self.condition.IsGongOnFlower:
            Name = TaiID.KongOnFlower
            ScoreNameList.append(Name); Score += Name.Score
        if self.condition.IsLastTileDraw:
            Name = TaiID.LastTileDraw
            ScoreNameList.append(Name); Score += Name.Score
        if self.condition.IsRobbingGong:
            Name = TaiID.RobbingKong
            ScoreNameList.append(Name); Score += Name.Score

        return Score, ScoreNameList

if __name__ == '__main__':

    # 測試1-1
    # 假設從玩家取得牌組
    hand = Tile.Alias2Tile(["1萬","2萬","3萬","3索","3索","3索","5筒","6筒","7筒","東","東","東","南","南","南","中","中"])
    rule = Rule()
    ret = rule.CanHu(hand)
    PrintLog("胡:"+str(ret))

    # # 測試1-2
    # hand = Tile.Alias2Tile(["3索","3索","3索","5筒","6筒","7筒","5筒","6筒","7筒","南","南","南","白","白"])
    # ret = rule.CanHu(hand)
    # PrintLog("胡:"+str(ret))
    # melds = rule.GetMelds()
    # for meld in melds:
    #     tmp = ""
    #     for tile in meld.Tiles:
    #         tmp += tile.toStr()
    #     PrintLog(tmp)

    # # 測試2
    # hand = Tile.Alias2Tile(["2萬","3萬","3索","3索","3索","5筒","6筒","7筒","5筒","6筒","7筒","南","南","南","中","中"])
    # ret = rule.FindAllWaits(hand)
    # tmp = ""
    # for t in ret:
    #     tmp += f"{t.toStr()} "
    # PrintLog("聽:"+tmp)
    # PrintLog()

    #
    # 計算台數
    #

    # # 測試3: 莊家連一，門清自摸，混一色碰碰胡帶門風

    # CanHu() 回傳True, 代表牌組可以胡，並可透過GetMelds，取出未明牌的Melds
    melds = rule.GetMelds()
    # 需在加入手牌明搭的牌組:明吃/明碰/明槓
    # melds.append((Meld(True, [t1, t2, t3]))

    for meld in melds:
        tmp = meld.Type.name + ": "
        for tile in meld.Tiles:
            tmp += tile.toStr()
        PrintLog(tmp)
    flowers = Tile.Alias2Tile(['梅', '蘭', '竹', '菊', '春', '夏', '秋', '冬'])

    classify = HandClassify(melds, flowers)
    # print(classify.IsValid)

    # 胡牌後，可由GameDesc 產生HandCondition所有參數
    condition = HandCondition(
        IsSingleWait=False,
        IsEdgeWait=False,
        IsCenterWait=True,
        # IsPairWait=False,
        IsDealer=True,
        IsSelfDraw=True,
        DealerStreak=3,
        SeatWind=WIND.EAST, # 東 門風
        RoundWind=WIND.SOUTH,  # 南 圈風
        SeatFlower=WIND.SOUTH, # 蘭 正花
    )

    score = Score(classify, condition)
    total, breakdown = score.Calculate()
    PrintLog("胡牌牌型:")
    tmp = ""
    for tai in breakdown:
        tab = '\t\t' if len(tai.Name) <= 3 else '\t'
        tmp += f"\t{tai.Name}{tab}{tai.Score}台\n"
    PrintLog(tmp)
    PrintLog(f"總台數: {total} 台")