from Tile import *

import random

# 牌組
# 管理麻將牌堆的洗牌、切牌和摸牌操作
class Deck:
    DICE_SCORE_MAX = 18
    DICE_SCORE_MIN = 3
    DICE_NUM = 3

    TILES_SIZE = 144
    ONE_WALL_SIZE = 36
    DEAD_WALL_SIZE = 16
    WALL_SIZE = TILES_SIZE - DEAD_WALL_SIZE

    # 擲骰子
    Dice:list[int] = [1,1,1]

    # 牌堆
    Tiles:list[Tile] = []
    # 牌牆（未被摸走的牌）
    Wall:list[Tile] = []
    # 牌尾（死牌區，用於補牌）
    DeadWall:list[Tile] = []
    # 棄牌區 / 河區
    Discard:dict = {WIND.EAST:[], WIND.SOUTH:[], WIND.WEST:[], WIND.NORTH:[]}
    LastWind:WIND = None
    LastDiscard:Tile = None

    #放槍牌
    DiscardWin:Tile = None

    def __init__(self):
        # initial all tiles
        times = 4
        for i in range(TileRange.CharMin.value, TileRange.CharMax.value + 1):
            self.Tiles.extend([Tile({'suit':SUIT.CHAR, 'num':i})]*times)
        # for i in range(TileRange.DotMin.value, TileRange.DotMax.value + 1):
            self.Tiles.extend([Tile({'suit':SUIT.DOT, 'num':i})]*times)
        # for i in range(TileRange.StickMin.value, TileRange.StickMax.value + 1):
            self.Tiles.extend([Tile({'suit':SUIT.STICK, 'num':i})]*times)
        for i in range(TileRange.HonorMin.value, TileRange.HonorMax.value + 1):
            self.Tiles.extend([Tile({'suit':SUIT.HONOR, 'num':i})]*times)
        for i in range(TileRange.FlowerMin.value, TileRange.FlowerMax.value + 1):
            self.Tiles.append(Tile({'suit':SUIT.FLOWER, 'num':i}))

        # #  洗牌 (Shuffle)
        # random.shuffle(self.Tiles)
        # self.BuildWall()

    # def BuildWall(self) -> bool:
    #     if len(self.Tiles) != self.TILES_SIZE:
    #         PrintLog(f"牌數錯誤：應為 {self.TILES_SIZE} 張，實際為 {len(self.Tiles)}")
    #         return False

    #     """將所有牌洗亂並建立牌牆。"""
    #     # 1. 洗牌 (Shuffle)
    #     random.shuffle(self.Tiles)
    #     return True

    def RollDice(self) -> list[int]:
        # return [1,1,1]
        for i in range(self.DICE_NUM):
            self.Dice[i] = random.randint(1,6)
        return self.Dice

    def Shuffle(self):
        #  洗牌 (Shuffle)
        random.shuffle(self.Tiles)
        # self.DebugTiles()

    # for debug
    def DebugTiles(self):
        # tmp = ['1S','2S','3S','4S','5S','6S']
        tiles = ['1C','1C','1C','1C']
        for i,t in enumerate(tiles):
            self.Tiles[6+i] = Tile.Str2Tile(t)

        tiles = ['1S','1S','1S','1S']
        for i,t in enumerate(tiles):
            self.Tiles[10+i] = Tile.Str2Tile(t)

    # 切牌
    # wind: Dealer wind index, scoe: Total score of 3 dices
    def BreakingWall(self, wind:WIND = WIND.EAST, score:int = 3) -> bool:
        if score > self.DICE_SCORE_MAX:
            score = self.DICE_SCORE_MAX
        elif score < self.DICE_SCORE_MIN:
            score = self.DICE_SCORE_MIN

        # 從目前莊家位置開始(牆數)
        index = (wind.value + score) % 4
        if index == 0:
            index = 4

        # 順數骼子的點數，從點數後第1張開始抓牌，1點是2張牌，點數前為死牆區
        offset = ((index - 1) * self.ONE_WALL_SIZE) + ((score + 1) * 2 - 1)
        # 超過1整圈，從頭開始抓
        if offset > self.TILES_SIZE:
            offset = offset - self.TILES_SIZE - 1

        remain = 0
        count = Deck.TILES_SIZE - offset + 1
        if count < Deck.WALL_SIZE:
            remain = Deck.WALL_SIZE - count
            count = Deck.TILES_SIZE + 1
        else:
            count = Deck.TILES_SIZE - Deck.DEAD_WALL_SIZE + offset

        # 從切牌位置開始放到牌牆
        for i in range(offset, count):
            self.Wall.append(self.Tiles.pop(offset-1))

        # 從切牌位置取到尾巴還不夠，則從頭取足放到牌牆
        for i in range(remain):    
            self.Wall.append(self.Tiles.pop(0))

        # 剩餘的牌作為死牌區，共16張
        for i in range(Deck.DEAD_WALL_SIZE):    
            self.DeadWall.append(self.Tiles.pop(0))

        PrintLog(f"牌牆初始化完成。牌牆張數: {len(self.Wall)}, 死牌區張數: {len(self.DeadWall)}")

    def DrawWallTile(self, fromEnd: bool = False) -> Tile:
        """從牌牆摸牌 (from_end=True 表示從嶺上牌區補牌)。"""
        if fromEnd:
            return self.DrawDeadWallTile() # 從牌尾取牌
        else:
            if len(self.Wall) <= 0:
                # 牌牆已空，流局判斷
                PrintLog("可摸牌區已空，牌局應流局！")
                return None
            return self.Wall.pop(0) # 從牌頭摸牌

    def CheckDeadWallCanGang(self) -> bool:
        """檢查是否還有嶺上牌可補。"""
        return len(self.DeadWall) > 0

    def DrawDeadWallTile(self) -> Tile:
        """從牌尾（死牌區）補一張牌 (Draw from the dead wall)。"""
        if len(self.DeadWall) <= 0:
            PrintLog("死牌區已空，無法補牌。")
            return None
        # 槓牌補牌通常是從牌尾取牌，所以我們從 dead_wall 的最右邊 pop()
        return self.DeadWall.pop()

    # 放置玩家的棄牌
    def DiscardTile(self, wind:WIND, tile:Tile):
        self.Discard[wind].append(tile)
        self.LastWind = wind
        self.LastDiscard = tile

    def PickUPDiscardTile(self) -> Tile:
        return self.Discard[self.LastWind].pop()

    # 當局結束時，回收玩家手牌
    def FlushTiles(self, handTiles:dict) -> bool:
        # handTiles: {
        #     WIND.EAST:[],WIND.SOUTH:[],WIND.WEST:[],WIND.NORTH:[]
        # }

        for _,val in handTiles.items():
            for _ in range(len(val)):
                self.Tiles.append(val.pop(0))
        # 回收牆區
        for _ in range(len(self.Wall)):
            self.Tiles.append(self.Wall.pop(0))
        # 回收死牆區
        for _ in range(len(self.DeadWall)):
            self.Tiles.append(self.DeadWall.pop(0))
        # 回收棄牌區
        for _,val in self.Discard.items():
            for i in range(len(val)):
                self.Tiles.append(val.pop(0))

        # 回收放槍牌
        if self.DiscardWin != None:
            self.Tiles.append(self.DiscardWin)
            self.DiscardWin = None

        # debug all tiles
        # self.Tiles.sort()
        # tmp = []
        # for t in self.Tiles:
        #     tmp.append(str(t))
        # PrintLog(','.join(tmp))

        # 檢查總牌數
        if len(self.Tiles) != self.TILES_SIZE:
            PrintLog(f"牌數錯誤：應為 {self.TILES_SIZE} 張，實際為 {len(self.Tiles)}")
            return False

        PrintLog(f"牌數回收完成：共 {len(self.Tiles)} 張牌")
        return True

    def PatchFlower(self, player:any) -> bool:
        """
        執行單一張牌的補花程序，直到所有玩家手牌中不再有花牌。

        Args:
            player: Player
        """

        # 順抓逆打:玩家逆向打牌，順向從牆牌抓牌
        PrintLog("--- 開始補花程序 ---")

        # 使用迴圈迭代，直到所有玩家的本輪補花都結束且沒有新花牌
        while True:
            # 標記本輪是否有玩家補到了新的花牌
            # new flower drawn in this round
            IsFlower = False
            if not player.LastDraw.IsFlower():
                return False

            # 1. 檢查並從手牌中移除花牌 (第一次或補牌後)
            tile = player.LastDraw
            player.SetFlowerTile(tile)

            # 2. 執行補牌
            PrintLog(f"玩家 {player.Name} 需要補 1 張牌。")
            try:
                NewTile = self.DrawDeadWallTile()
                if NewTile == None:
                    return False
                player.LastDraw = NewTile

                # 檢查補到的牌是否又是花牌
                if NewTile.IsFlower():
                    IsFlower = True
                    PrintLog(f"   --> 補到新花牌：{NewTile.toStr()} (將於下輪處理)")
                else:
                    PrintLog(f"   --> 補到牌：{NewTile.toStr()}")

            except IndexError:
                PrintLog("!!! 錯誤：死牌區已空，無法補牌。遊戲將流局。")
                return False

            # 如果本輪沒有任何玩家補到新的花牌，則補花程序結束
            if not IsFlower:
                break

            PrintLog("\n--> 偵測到玩家補到新的花牌，進行下一輪補花...")
        PrintLog("--- 補花程序完成 ---")
        return True

    #
    # 開局呼叫 function
    #

    # 開局發牌給所有玩家完時叫用
    def ReplaceFlowers(self, players:dict[WIND,any]) -> bool:
        """
        執行完整的補花程序，直到所有玩家手牌中不再有花牌。

        Args:
            players: key:WIND, value:Player 物件的字典。
        """

        # 順抓逆打:玩家逆向打牌，順向從牆牌抓牌
        # 莊家 (Player 0) 開始，逆時針 (0:東 -> 3:北 -> 2:西 -> 1:南)
        PrintLog("--- 開始補花程序 ---")

        # 使用迴圈迭代，直到所有玩家的本輪補花都結束且沒有新花牌
        num = len(players)
        while True:
            # 標記本輪是否有玩家補到了新的花牌
            # new flower drawn in this round
            IsFlower = False

            # 玩家逆時針補花 (0:東 -> 3:北 -> 2:西 -> 1:南)
            # for index in range(num):
            for index in range(num, 0, -1):
                wind = WIND(index%num+1)
                if num == 1:
                    player = next(iter(players.values()))
                else:
                    player = players[wind]

                # 1. 檢查並從手牌中移除花牌 (第一次或補牌後)
                # num of flowers to replace
                FlowerList = player.CheckFlowers()

                # 2. 執行補牌 num to draw based on the num of flower tiles
                NumDraw = len(FlowerList)

                if NumDraw > 0:
                    PrintLog(f"玩家 {player.Name} 需要補 {NumDraw} 張牌。")

                    for i in range(NumDraw):
                        try:
                            NewTile = self.DrawDeadWallTile()
                            player.SetHandTile([NewTile])

                            # 檢查補到的牌是否又是花牌
                            if NewTile.IsFlower():
                                IsFlower = True
                                PrintLog(f"   --> 補到新花牌：{NewTile.toStr()} (將於下輪處理)")
                            else:
                                # player.LastDraw = NewTile
                                PrintLog(f"   --> 補到牌：{NewTile.toStr()}")

                        except IndexError:
                            PrintLog("!!! 錯誤：死牌區已空，無法補牌。遊戲將流局。")
                            return False

            # 如果本輪沒有任何玩家補到新的花牌，則補花程序結束
            if not IsFlower:
                break

            PrintLog("\n--> 偵測到有玩家補到新的花牌，進行下一輪補花...")
        PrintLog("--- 補花程序完成 ---")
        return True

    # 開局發牌叫用
    def DealTiles(self, handTiles:dict):
        # 發牌
        # 每人抓4次，1次4張
        times,pcs = 4,4
        for _ in range(times):
            for key,val in handTiles.items():
                val.extend([self.Wall.pop(0) for _ in range(pcs)])

        # # 莊家開門
        # handTiles[WIND.EAST].append(self.Wall.pop(0))

if __name__ == '__main__':
    deck = Deck()
    dice = deck.RollDice()
    print(dice)