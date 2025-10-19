from Tile import *

from collections import Counter

# 定義Taiwan 16張麻將規則
# 檢查手上牌符合哪些胡牌情況
# 包含:聽牌、胡牌，吃、碰、槓
class Rule16:
    HandLen = 17
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

    # 確認手牌是否可槓牌
    @staticmethod
    def CanConcealKong(hand: list[Tile]) -> bool:
        HandCounts = Counter(hand)
        for tile in HandCounts:
            if HandCounts[tile] >= MELD.KONG_LEN.value:
                return True
        return False

    @staticmethod
    def CanKong(hand: list[Tile], discard: Tile) -> bool:
        HandCounts = Counter(hand)
        for tile in HandCounts:
            if HandCounts[tile] >= MELD.KONG_LEN.value-1 and tile == discard:
                return True
        return False

    @staticmethod
    def CanAddKong(melds: list[Meld], discard: Tile) -> bool:
        for meld in melds:
            if meld.Type == MELD.PONG and discard in meld.Tiles:
                return True
        return False

    @staticmethod
    def CanPong(hand: list[Tile], discard: Tile) -> bool:
        HandCounts = Counter(hand)
        for tile in HandCounts:
            if HandCounts[tile] >= MELD.PONG_LEN.value-1 and tile == discard:
                return True
        return False

    @staticmethod
    def CanChow(hand: list[Tile], discard: Tile) -> bool:
        if discard.IsHonor() or discard.IsFlower():
            return False

        t1, t2 = None, None
        # 邊張 1
        if discard.Num == Tile.NumMin:
            # 2 and 3, lack 1
            t1, t2 = discard + 1, discard + 2
        # 邊張 9
        elif discard.Num == Tile.NumMax:
            # 8 and 9, lack 9
            t1, t2 = discard - 1, discard - 2
        # 中洞
        else:
            # ex: 3 and 5, lack 4
            t1, t2 = discard - 1, discard + 1

        if t1 in hand and t2 in hand:
            return True
        return False

    @staticmethod
    def GetKongTile(hand: list[Tile]) -> list[Tile]:
        HandCounts = Counter(hand)
        tmp = []
        for tile in HandCounts:
            if HandCounts[tile] >= MELD.KONG_LEN.value:
                tmp.append(tile)
        return tmp

    # 確認手牌是否可胡牌
    @staticmethod
    def CanHu(hand: list[Tile]) -> tuple[bool, list[Meld]]:
        melds:list[Meld] = []
        """
        主函式：判斷牌組是否胡牌
        hand: e.g., ['1p','1p','1m', '2m', '3m', ...]
        """
        ValidLen = [i for i in range(MELD.PAIR_LEN.value, Rule16.HandLen+1, MELD.CHOW_LEN.value)]
        if len(hand) not in ValidLen:
            return (False, [])

        # 1. 前置檢查特殊牌型
        # 使用 Counter來計算每一種牌重複數量 key:tile, val:num
        HandCounts = Counter(hand)
        # 16張麻將沒有七對子台
        # if IsSevenPairs(HandCounts):
        #     return True

        # 2. 遍歷所有可能的眼睛
        for tile in HandCounts:
            # 假設為對牌
            if HandCounts[tile] >= MELD.PAIR_LEN.value:
                # 複製一份手牌來操作，避免影響原始資料
                TempCounts = HandCounts.copy()

                # 移除眼睛
                TempCounts[tile] -= MELD.PAIR_LEN.value
                if TempCounts[tile] == 0:
                    del TempCounts[tile]

                # 3. 遞迴拆解剩下的 15 張牌
                if Rule16.CanBeMelds(TempCounts, melds):
                    #新增對子
                    melds.append(Meld(False, [tile, tile]))
                    return (True, melds) # 只要有一種組合成功，就是胡牌

        return (False,[])

    # 驗證手牌全部是否都可成為搭(順子或刻子)
    @staticmethod
    def CanBeMelds(hand: Counter, melds:list[Meld]) -> bool:
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
            if Rule16.CanBeMelds(hand.copy(), melds): # 傳遞副本
                #新增刻子
                melds.append(Meld(False, [FirstTile, FirstTile, FirstTile]))
                return True

            # 回溯 (Backtrack)
            hand[FirstTile] += 3

        # Recursive Step 2: 嘗試組順子 (字牌,花牌無法組順子)
        # 順子:7,8,9
        if FirstTile.Suit != SUIT.HONOR and FirstTile.Suit != SUIT.FLOWER and FirstTile.Num <= Rule16.NumHiLimit:
            t1, t2, t3 = FirstTile, FirstTile + 1, FirstTile + 2
            if t1 in hand and t2 in hand and t3 in hand:
                # 移除順子
                hand[t1] -= 1;hand[t2] -= 1;hand[t3] -= 1

                # 清理計數為 0 的牌
                hand = Counter({k: v for k, v in hand.items() if v > 0})

                # 遞迴移除順子
                if Rule16.CanBeMelds(hand.copy(), melds): # 傳遞副本
                    #新增順子
                    melds.append(Meld(False, [t1, t2, t3]))
                    return True

                # 回溯 (Backtrack)
                hand[t1] += 1;hand[t2] += 1;hand[t3] += 1

        # 如果所有組合都失敗
        return False

    # @staticmethod
    # def GetMelds() -> list[Meld]:
    #     return Rule16.Melds

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

if __name__ == '__main__':

    # 測試1-1
    # 假設從玩家取得牌組
    hand = Tile.Alias2Tile(["1萬","2萬","3萬","3索","3索","3索","5筒","6筒","7筒","東","東","東","南","南","南","中","中"])
    # Rule16 = Rule16()
    ret, melds = Rule16.CanHu(hand)
    PrintLog("胡:"+str(ret))