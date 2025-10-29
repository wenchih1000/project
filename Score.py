from Tile import *
from Model import *

# @dataclass
class HandCondition:
    IsExposed: bool = False         # 標誌是否吃碰過
    IsDealer: bool = False          # 莊家
    IsSelfDraw: bool = False        # 自摸
    IsRobbingGong: bool = False     # 搶槓胡牌
    IsGongOnFlower: bool = False    # 槓上開花
    IsLastTileDraw: bool = False    # 海底自摸
    IsLastTileDiscard: bool = False # 河底撈魚
    IsHeavenlyHand: bool = False    # 天胡
    IsEarthlyHand: bool = False     # 地胡
    # IsWinningHand: bool = False     # 地胡
    IsHumanlyHand: bool = False     # 人胡
    IsPlainHand: bool = False       # 平胡

    IsSingleWait: bool = False      # 獨聽/單吊 (1台)
    IsEdgeWait: bool = False        # 邊張 (1台)
    IsCenterWait: bool = False      # 中洞/崁張 (1台)
    IsPairWait: bool = False        # 眼張

    IsMultiWait: bool = False       # 多聽 兩面聽/對倒/複合聽 (通常不計台，是平胡的必要條件)

    # 風台
    SeatWind: WIND = None           # 玩家門風台 (1:東 2:南 3:西 4:北)
    RoundWind: WIND = None          # 圈風台     (1:東 2:南 3:西 4:北)
    #莊家台
    DealerStreak: int = 0           # 連莊/連拉
    # 花台
    SeatFlower: WIND = None         # 玩家正花台 (1:梅/春 2:蘭/夏 3:竹/秋 4:菊/冬)
    # RoundFlower: int = 0          # 圈花台     (5:春 6:夏 7:秋 8:冬)

    def __init__(self):
        pass

    def Reset(self):
        self.IsExposed = False
        self.IsDealer = False
        self.IsSelfDraw = False
        self.IsRobbingGong = False
        self.IsGongOnFlower = False
        self.IsLastTileDraw = False
        self.IsLastTileDiscard = False
        self.IsHeavenlyHand = False
        self.IsEarthlyHand = False
        self.IsHumanlyHand = False
        self.CanHumanlyHand = False
        self.IsPlainHand = False

        self.IsSingleWait = False
        self.IsEdgeWait = False
        self.IsCenterWait = False
        self.IsPairWait = False
        self.IsMultiWait = False

        self.SeatWind = None
        self.RoundWind = None
        self.DealerStreak = 0
        self.SeatFlower = None
        # self.RoundFlower = 0

# 檢查手牌組了幾個明/暗搭
# 對子/順子/刻子/槓子
# 滿足胡牌條件:5搭x3 + 1對x2 = 17張
# 滿足聽牌條件:4搭x3 + 缺1張組成搭 + 1對x2 = 16張
#             4搭x3 + 2對x2 = 16張

# 胡牌至少5組(順/刻/槓搭)+1組(對搭) = 6 Meld
class HandClassify:
    Pair: Meld = None           #   1組對子/眼
    Pongs: list[Meld]   = None    # 0~n組碰子/刻
    Kongs: list[Meld]   = None    # 0~n組槓子/槓
    Chows: list[Meld]   = None    # 0~n組吃子/順
    Flowers: list[Tile] = None    # 0~n張花牌

    IsValid:bool = True
    MeldLen = 5

    def __init__(self, melds:tuple[Meld], flowers:tuple[Tile]):
        self.Pair = None
        self.Pongs = []
        self.Kongs = []
        self.Chows = []
        self.Flowers = []

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

class TaiScore:
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
        if self.condition.IsHeavenlyHand and self.condition.IsDealer:
            # 天胡
            Name = TaiID.HeavenlyHand
            ScoreNameList.append(Name); Score = Name.Score
            return Score, ScoreNameList
        # 地胡 16台
        elif self.condition.IsEarthlyHand and not self.condition.IsDealer:
            Name = TaiID.EarthlyHand
            ScoreNameList.append(Name); Score = Name.Score
            return Score, ScoreNameList
        # 人胡 16台
        elif self.condition.IsHumanlyHand:
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

        # 屁胡
        if Score == 0:
            Name = TaiID.BaseHand
            ScoreNameList.append(Name); Score += Name.Score

        return Score, ScoreNameList

if __name__ == '__main__':

    # 測試1-1
    # 假設從玩家取得牌組
    hand = Tile.Alias2Tile(["1萬","2萬","3萬","3索","3索","3索","5筒","6筒","7筒","東","東","東","南","南","南","中","中"])
    # rule = Rule()
    ret, melds = Rule16.CanHu(hand)
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
    # melds = Rule.GetMelds()
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
    condition = HandCondition()
    condition.IsSingleWait=False
    condition.IsEdgeWait=False
    condition.IsCenterWait=True
    # condition.IsPairWait=False
    condition.IsDealer=True
    condition.IsSelfDraw=True
    condition.DealerStreak=3
    condition.SeatWind=WIND.EAST # 東 門風
    condition.RoundWind=WIND.SOUTH  # 南 圈風
    condition.SeatFlower=WIND.SOUTH # 蘭 正花

    score = TaiScore(classify, condition)
    total, breakdown = score.Calculate()
    PrintLog("胡牌牌型:")
    tmp = ""
    for tai in breakdown:
        tab = '\t\t' if len(tai.Name) <= 3 else '\t'
        tmp += f"\t{tai.Name}{tab}{tai.Score}台\n"
    PrintLog(tmp)
    PrintLog(f"總台數: {total} 台")