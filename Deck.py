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
    # 牌尾（死牌區，用於補牌)
    DeadWall:list[Tile] = []
    # 棄牌區 / 河區
    Discard:dict = {WIND.EAST:[], WIND.SOUTH:[], WIND.WEST:[], WIND.NORTH:[]}

    LastWind:WIND = None
    LastDiscard:Tile = None
    # 確認閒家搶槓胡
    LastAddKong:Tile = None

    #放槍牌
    DiscardWin:Tile = None

    DrawByKong:bool = False
    DrawByFlower:bool = False


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

    def Reset(self):
        self.LastWind = None
        self.LastDiscard = None
        # 確認閒家搶槓胡
        self.LastAddKong = None
        #放槍牌
        self.DiscardWin = None
        self.DrawByFlower = False
        self.DrawByKong = False

    def RollDice(self) -> list[int]:
        for i in range(self.DICE_NUM):
            self.Dice[i] = random.randint(1,6)
        return self.Dice

    def Shuffle(self):
        #  洗牌 (Shuffle)
        random.shuffle(self.Tiles)

    # for debug
    def DebugTiles(self):

        alls = {
            WIND.EAST:['1C','1C','1C','1S','2S','3S','1D','1D','1D','1W','1W','1W','1A','1A','1A', '5S'], 
            WIND.SOUTH:['2C','2C','2C','4S','5S','6S','2D','2D','2D','2W','2W','2W','2A','2A','2A', '6S'], 
            WIND.WEST:['3C','3C','3C','7S','8S','9S','3D','3D','3D','3W','3W','3W','3A','3A','3A', '7S'], 
            WIND.NORTH:['4C','4C','4C','1S','2S','3S','4D','4D','4D','4W','4W','4W','9C','9C','9C', '8S']
        }

        offset = 16 # 4人
        con = 0
        for i in range(4):
            for j in range(4):
                # EAST
                self.Wall[i*offset+j] = Tile.Str2Tile(alls[WIND.EAST][con])
                # SOUTH
                # self.Wall[i*offset+4+j] = Tile.Str2Tile(alls[WIND.SOUTH][con])
                # WEST
                # self.Wall[i*offset+8+j] = Tile.Str2Tile(alls[WIND.WEST][con])
                # NORTH
                # self.Wall[i*offset+12+j] = Tile.Str2Tile(alls[WIND.NORTH][con])
                con += 1

        tmp = ['5C','5C','5C','5C']
        offset *= 4
        for i in range(len(tmp)):
            self.Wall[offset+i] = Tile.Str2Tile(tmp[i])

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

        # self.DebugTiles()
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

    def IsWallEmpty(self) -> bool:
        """檢查牌牆是否為空。"""
        return len(self.Wall) == 0

    def RemainingWallTiles(self) -> int:
        return len(self.Wall)

    def CheckDeadWallCanGang(self) -> bool:
        """檢查是否還有嶺上牌可補。"""
        return len(self.DeadWall) > 0

    def DrawDeadWallTile(self) -> Tile:
        """從牌尾（死牌區）補一張牌 (Draw from the dead wall)。"""
        if self.IsWallEmpty():
            PrintLog("牆牌區已空，無法補牌。")
            return None
        # if len(self.DeadWall) <= 0:
        #     PrintLog("死牌區已空，無法補牌。")
        #     return None

        # 槓牌補牌通常是從牌尾取牌，所以我們從 dead_wall 的最右邊 pop()
        tile = self.DeadWall.pop()
        # 從牆牌尾取牌補到死牌首張
        # 死牌區保持16張牌
        self.DeadWall.insert(0, self.Wall.pop())
        return tile

    # 放置玩家的棄牌
    def DiscardTile(self, wind:WIND, tile:Tile):
        self.Discard[wind].append(tile)
        self.LastWind = wind
        self.LastDiscard = tile

    def PickUPDiscardTile(self) -> Tile:
        return self.Discard[self.LastWind].pop()

    def HuTile(self, lastdraw:Tile) -> Tile:
        LastHu = None
        # 搶槓胡
        if self.LastAddKong != None:
            LastHu = self.LastAddKong
        # 自摸
        elif lastdraw != None:
            LastHu = lastdraw
        # 其他家放槍
        else:
            LastHu = self.LastDiscard
        return LastHu

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

    # 開局發牌叫用
    def DealTiles(self, handTiles:dict):
        # PrintLog('SetHandTile:'+", ".join(Tile.List2StrList(self.Wall)))
        # 發牌
        # 每人抓4次，1次4張
        times,pcs = 4,4
        for _ in range(times):
            for key,val in handTiles.items():
                val.extend([self.Wall.pop(0) for _ in range(pcs)])

if __name__ == '__main__':
    deck = Deck()
    dice = deck.RollDice()
    print(dice)