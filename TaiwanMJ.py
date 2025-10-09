#
# define Taiwan Mahjong tile class
#
from Tile import *

from collections import Counter
from enum import Enum
import random

class Action(Enum):
    HU = 4
    KONG = 3
    PONG = 2
    CHOW = 1
    PASS = 0

# Player 類別：管理手牌與公開牌
class Player: # thread.Thread
    Name:str = ''
    Money:int = 3000

    # 是否為莊家
    IsDealer:bool = False
    # wind seat
    Wind:WIND = None
    # 存放明搭 <=5 搭
    ExposedMelds:list[Meld] = None
    # 存放花牌
    Flowers:list[Tile] = None
    # 存放摸進的牌 <= 17
    Hand:list[Tile] = None

    def __init__(self, name:str, wind:WIND):
        self.Name = name
        self.Wind = wind

        # 東風玩家預設起始為莊家
        if self.Wind == WIND.EAST:
            self.IsDealer = True

        # 玩家手牌 (16 或 17 張) 
        self.Hand = []
        # 已亮出的花牌 Exposed Flowers
        self.Flowers = []
        # 已完成的搭子 (吃/碰/槓/暗槓) Exposed Melds
        self.ExposedMelds = []

    def SetHandTile(self, hand:list[Tile]):
        for _ in range(len(hand)):
            self.Hand.append(hand.pop(0))
        self.Hand.sort()

    def ReturnAllTile(self) -> list[Tile]:
        hand = [] #list[Tile]
        for _ in range(len(self.Hand)):
            hand.append(self.Hand.pop(0))
        for _ in range(len(self.Flowers)):
            hand.append(self.Flowers.pop(0))
        for meld in self.ExposedMelds:
            for _ in range(len(meld.Tiles)):
                hand.append(meld.Tiles.pop(0))
        return hand

    # 該玩家當莊
    def SetDealer(self, dealer:bool = True):
        self.IsDealer = dealer

    # 用於開局時檢查手上所有花牌
    def CheckFlowers(self) -> list[Tile]:
        """
        檢查並從手牌中取出所有花牌。

        Returns:
            這一輪從手牌中取出的花牌列表。
        """
        # 從手牌中移除花牌
        count = 0
        tmp = []
        for tile in self.Hand:
            if tile.IsFlower():
                count += 1
                self.Flowers.append(tile)
                tmp.append(tile)

        # remove flower from player hand
        # PrintLog([h.toStr() for h in self.Hand])
        for t in tmp:
            self.Hand.remove(t)

        PrintLog(f"玩家 {self.Wind.name} 摸到{count}張花牌：{[i.toStr() for i in tmp]}")
        return tmp

    def HandCounts(self) -> Counter:
        return Counter(self.Hand)

    # 新增明搭
    def AddMeld(self, tiles: list[Tile], action: MELD, concealed: bool = False):
        self.ExposedMelds.append(Meld(not concealed, tiles))

    # def NumExposedMelds(self) -> int:
    #     """計算玩家外露搭子（碰、吃、明槓）的總數。"""
    #     # 暗槓不算外露搭子
    #     return sum(1 for meld in self.ExposedMelds if meld.Exposed)

    def NumMelds(self) -> int:
        """計算玩家外露搭子（吃/碰/槓/暗槓）的總數。"""
        return len(self.ExposedMelds)

    def RemoveTiles(self, tiles:list[str]):
        for tile in tiles:
            self.Hand.remove(tile)

# 牌組
# 管理麻將牌堆的洗牌、切牌和摸牌操作
class Deck:
    DICE_SCORE_MAX = 18
    DICE_SCORE_MIN = 3
    TILES_SIZE = 144
    ONE_WALL_SIZE = 36
    DEAD_WALL_SIZE = 16
    WALL_SIZE = TILES_SIZE - DEAD_WALL_SIZE

    # 牌堆
    Tiles:list[Tile] = []
    # 牌牆（未被摸走的牌）
    Wall:list[Tile] = []
    # 牌尾（死牌區，用於補牌）
    DeadWall:list[Tile] = []
    # 棄牌區 / 河區
    Discard:dict = {WIND.EAST:list[Tile], WIND.SOUTH:list[Tile], WIND.WEST:list[Tile], WIND.NORTH:list[Tile]}

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

        #  洗牌 (Shuffle)
        random.shuffle(self.Tiles)
        # self.BuildWall()

    # def BuildWall(self) -> bool:
    #     if len(self.Tiles) != self.TILES_SIZE:
    #         PrintLog(f"牌數錯誤：應為 {self.TILES_SIZE} 張，實際為 {len(self.Tiles)}")
    #         return False

    #     """將所有牌洗亂並建立牌牆。"""
    #     # 1. 洗牌 (Shuffle)
    #     random.shuffle(self.Tiles)
    #     return True

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

    # 處理玩家的棄牌
    def DiscardTile(self, wind:int, tile:Tile):
        self.Discard[wind].append(tile)

    # 當局結束時，回收玩家手牌
    def FlushTiles(self, handTiles:dict) -> bool:
        for key,val in handTiles.items():
            for i in val:
                self.Tiles.append(i.pop(0))
        # 回收牆區
        for _ in range(len(self.Wall)):
            self.Tiles.append(self.Wall.pop(0))
        # 回收死牆區
        for _ in range(len(self.DeadWall)):
            self.Tiles.append(self.DeadWall.pop(0))
        # 回收棄牌區
        for key,val in self.Discard.items():
            for i in range(len(val)):
                self.Tiles.append(val.pop(0))

        # 檢查總牌數
        if len(self.Tiles) != self.TILES_SIZE:
            PrintLog(f"牌數錯誤：應為 {self.TILES_SIZE} 張，實際為 {len(self.Tiles)}")
            return False

        random.shuffle(self.Tiles)
        return True

    #
    # 開局呼叫 function
    #

    # 開局發牌給所有玩家完時叫用
    def ReplaceFlowers(self, players:list[Player]) -> bool:
        """
        執行完整的補花程序，直到所有玩家手牌中不再有花牌。

        Args:
            players: 包含所有 Player 物件的字典。
            deck: 遊戲牌堆，用於提供補牌。
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
                player = players[index%num]

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

# ------------------------------------------------------------------------------------------------
# debug testing
# ------------------------------------------------------------------------------------------------

def DemoTiles():
    tiles = []
    times = 4
    for i in range(TileRange.CharMin.value, TileRange.CharMax.value + 1):
        tiles.extend([Tile({'suit':SUIT.CHAR, 'num':i})]*times)
    # for i in range(TileRange.DotMin.value, TileRange.DotMax.value + 1):
        tiles.extend([Tile({'suit':SUIT.DOT, 'num':i})]*times)
    # for i in range(TileRange.StickMin.value, TileRange.StickMax.value + 1):
        tiles.extend([Tile({'suit':SUIT.STICK, 'num':i})]*times)
    for i in range(TileRange.HonorMin.value, TileRange.HonorMax.value + 1):
        tiles.extend([Tile({'suit':SUIT.HONOR, 'num':i})]*times)
    for i in range(TileRange.FlowerMin.value, TileRange.FlowerMax.value + 1):
        tiles.append(Tile({'suit':SUIT.FLOWER, 'num':i}))

    random.shuffle(tiles)
    # for t in tiles:
    #     PrintLog(t, end=',')
    # PrintLog('\r\n\r\n')

    players = []
    for i in range(4):
        player = []
        for i in range(16):
            t = tiles.pop()
            while t.Suit == SUIT.FLOWER:
                player.append(t)
                t = tiles.pop()
            player.append(t)
        player.sort()
        players.append(player)

    for p in players:
        for t in p:
            PrintLog(t.toStr(), end=' ')
        PrintLog()

def DemoReplaceFlowersWhenStartGame():
    # 簡易開局，玩家抓牌並完成補花
    deck = Deck()
    diceScore = random.randint(3,18)
    wind = WIND.EAST
    deck.BreakingWall(wind, diceScore)
    handTiles = {WIND.EAST:[], WIND.SOUTH:[], WIND.WEST:[], WIND.NORTH:[]}
    deck.DealTiles(handTiles)
    players = [Player('東', WIND.EAST), Player('南', WIND.SOUTH), Player('西', WIND.WEST), Player('北', WIND.NORTH)]

    for key,val in handTiles.items():
        players[key.value-1].SetHandTile(val)
        for i in val:
            PrintLog(i.toStr(), end=' ')
    PrintLog()

    # 所有玩家補花
    deck.ReplaceFlowers(players)

    # 莊家開門
    tile = deck.DrawWallTile()
    player = players[WIND.EAST.value-1]
    player.SetHandTile([tile])
    if tile.IsFlower():
        deck.ReplaceFlowers([player])

    # 確認莊家手牌是否胡牌
    # GameDesc notify player to do action
    # ex: Player turn/Hu/Kong/Pong/Chow/Pass
    print(player.HandCounts().values())

    # 莊家出第一張牌

def DemoAlias2Tile():
    #
    #  Alias text to tile
    #

    tmp = ["1萬","3索","5筒","中","發","白","梅","春","竹","冬"] 
    tmp = ["東","南","西","北","中","發","白","梅","蘭","竹","菊","春","夏","秋","冬"]
    for i in tmp:
        t = Tile({'alias':i})
        # PrintLog(t, end=' ')
        PrintLog(t, t.toStr(), t.IsFlower(), t.IsHonor())

    tmp = []
    for i in range(TileRange.CharMin.value, TileRange.CharMax.value + 1):
        tmp.extend([Tile({'suit':SUIT.CHAR, 'num':i})])
    # for i in range(TileRange.DotMin.value, TileRange.DotMax.value + 1):
        tmp.extend([Tile({'suit':SUIT.DOT, 'num':i})])
    # for i in range(TileRange.StickMin.value, TileRange.StickMax.value + 1):
        tmp.extend([Tile({'suit':SUIT.STICK, 'num':i})])
    for i in range(TileRange.HonorMin.value, TileRange.HonorMax.value + 1):
        tmp.extend([Tile({'suit':SUIT.HONOR, 'num':i})])
    for i in range(TileRange.FlowerMin.value, TileRange.FlowerMax.value + 1):
        tmp.append(Tile({'suit':SUIT.FLOWER, 'num':i}))
    for t in tmp:
        # PrintLog(t, end=' ')
        PrintLog(t, t.toStr(), t.IsFlower(), t.IsHonor())

if __name__ == '__main__':
    
    # DemoTiles()

    # DemoAlias2Tile()

    #
    # test deck
    #
    DemoReplaceFlowersWhenStartGame()

    # for index in range(3, -1, -1)L:
    #     print((index+1)%4)

    # for index in range(3, -1, -1):
    #     print((index+1)%4)

    # for index in range(4, 0, -1):
    #     print(index%4)


    # count = players[1].HandCounts()
    # for c in count:
    #     PrintLog(c.toStr(), count[c], end=' ')
    # PrintLog()

    # for i in range(Deck.WALL_SIZE):
    #     PrintLog(deck.DrawWallTile().toStr(), end=' ')
    # PrintLog()
    # for i in range(Deck.DEAD_WALL_SIZE):
    #     PrintLog(deck.DrawDeadWallTile().toStr(), end=' ')
    # PrintLog()

        