from Tile import *
from Rule import *
# from Deck import *
# import Deck

import time
from enum import Enum
from collections import Counter
import random
from threading import Thread, Event

class Action(Enum):
    HU = 5
    KONG = 4
    ADD_KONG = 3
    PONG = 2
    CHOW = 1
    PASS = 0

    DRAWING = -1
    DISCARD = -2

# Player 類別：管理手牌與公開牌
class Player(Thread):
    import Deck
    # from Deck import Deck

    ExitEvent = Event()
    ActionEvent = Event()
    FinishEvent = Event()
    #Player 當前要執行的動作
    Actions:Action = None
    Name:str = ''
    Money:int = 3000

    # 是否為莊家
    IsDealer:bool = False
    # 風位
    Wind:WIND = None
    # 存放明搭 <=5 搭
    ExposedMelds:list[Meld] = None
    # 存放花牌
    Flowers:list[Tile] = None
    # 存放摸進的牌 <= 17
    Hand:list[Tile] = None

    # UI玩家選擇的暫存牌
    LastDiscard:Tile = None
    LastKong:Tile = None
    ConcealedKong:bool = False

    LastPong:Tile = None
    # 存放手牌預被吃成搭的2張牌
    LastChows:list[Tile] = None
    LastHu:Tile = None

    DeckRef:Deck = None
    # 給UI對應操作的狀態
    ActionState:dict = None

    def __init__(self, name:str, wind:WIND, deck:Deck):
        super().__init__()
        self.Name = name
        self.Wind = wind
        self.DeckRef = deck

        # 東風玩家預設起始為莊家
        if self.Wind == WIND.EAST:
            self.IsDealer = True

        self.Reset()

    def Reset(self):
        # 玩家手牌 (16 或 17 張)
        self.Hand = []
        # 已亮出的花牌 Exposed Flowers
        self.Flowers = []
        # 已完成的搭子 (吃/碰/槓/暗槓) Exposed Melds
        self.ExposedMelds = []
        # 上次出的牌
        self.LastDiscard = None
        self.LastKong = None
        self.ConcealedKong = False
        self.LastPong = None
        self.LastChows = []
        self.LastHu = None

        # Game Deck 檢查後，通知玩家目前可操作的狀態
        self.ActionState = {
            # 摸牌, 出牌
            Action.DRAWING:False, Action.DISCARD:False, 
            # 胡/槓/碰/吃/過
            Action.HU:False, Action.KONG:False, Action.PONG:False, Action.CHOW:False, Action.PASS:False
        }
        self.Actions = None
        self.EventClear()

    def run(self):
        while not self.ExitEvent.is_set():
            # 執行UI玩家所下的命令
            if self.ActionEvent.is_set():
                # 胡/吃/碰/槓/Pass
                match self.Actions:
                    case Action.HU:
                        # 暗胡(自摸) or 明胡(其他家放槍)
                        hu = self.LastHu
                        PrintLog(self.Name + ' 胡牌: ' + hu.toStr())
                        # 確認玩家手牌所有情況
                        # HandCondition
                        # 下一步計算玩家台數
                        self.FinishEvent.set()
                    case Action.KONG:
                        kong = self.LastKong
                        tiles = [kong]*(Rule.KongLen-1)
                        PrintLog(self.Name + ' 槓牌: ' + kong.toStr())
                        # 將手牌的槓搭複制進Meld list
                        self.AddMeld(tiles+[kong], self.ConcealedKong)
                        # 清除手牌的槓搭
                        self.ConcealedKong = False
                        self.RemoveTiles(tiles)
                        # 下一步通知玩家摸一打一
                        self.FinishEvent.set()
                    case Action.ADD_KONG:
                        # 將明搭裡的碰搭變更成槓搭
                        tile = self.LastKong
                        for meld in self.ExposedMelds:
                            if meld.Type == MELD.PONG and tile in meld.Tiles:
                                meld.Type = MELD.KONG
                                meld.Tiles.append(tile)
                                PrintLog(self.Name + ' 加槓牌: ' + tile.toStr())
                                break
                        # 下一步通知玩家摸一打一
                        self.FinishEvent.set()
                    case Action.PONG:
                        pong = self.LastPong
                        tiles = [pong]*(Rule.PongLen-1)
                        PrintLog(self.Name + ' 碰牌: ' + pong.toStr())
                        # 將手牌的碰搭複制進Meld list
                        self.AddMeld(tiles+[pong])
                        # 清除手牌的碰搭
                        self.RemoveTiles(tiles)
                        # 下一步通知玩家出牌
                        self.FinishEvent.set()
                    case Action.CHOW:
                        # 玩家指家吃的牌型
                        # ex: 6 in LastDiscard
                        chow = self.DeckRef.LastDiscard
                        # ex: 5,7 in LastChows
                        tiles = self.LastChows
                        # 將手牌的碰搭複制進Meld list
                        self.AddMeld(tiles+[chow])
                        # 清除手牌的碰搭
                        self.RemoveTiles(tiles)
                        # 下一步通知玩家出牌
                        self.FinishEvent.set()
                    case Action.PASS:
                        # 放棄胡/槓/碰/吃的機會
                        PrintLog(self.Name + ' 跳過')
                        self.FinishEvent.set()
                    case Action.DRAWING:
                        if self.LastKong != None:
                            fromEnd = True
                            self.LastKong = None
                        else:
                            fromEnd = False

                        tile = self.DeckRef.DrawWallTile(fromEnd)
                        PrintLog(self.Name + ' 摸牌: ' + tile.toStr())
                        self.SetHandTile([tile])
                        if tile.IsFlower():
                            self.DeckRef.ReplaceFlowers({self.Wind:self})
                        self.FinishEvent.set()
                    case Action.DISCARD:
                        self.Hand.remove(self.LastDiscard)
                        PrintLog(self.Name + ' 出牌: ' + self.LastDiscard.toStr())
                        self.DeckRef.DiscardTile(self.Wind, self.LastDiscard)
                        self.FinishEvent.set()
                    case _:
                        pass
                self.Actions = None
                self.ActionEvent.clear()
            else:
                time.sleep(0.1)
                # print('sleep')

    def Wait(self):
        PrintLog('Action waiting')
        self.FinishEvent.wait()
        self.FinishEvent.clear()
        PrintLog('Action finish')

    def Notify(self):
        self.ActionEvent.set()

    def EventClear(self):
        self.ActionEvent.clear()
        self.FinishEvent.clear()

    def Exit(self):
        self.ExitEvent.set()

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
    def AddMeld(self, tiles: list[Tile], concealed: bool = False):
        self.ExposedMelds.append(Meld(not concealed, tiles))

    # def NumExposedMelds(self) -> int:
    #     """計算玩家外露搭子（碰、吃、明槓）的總數。"""
    #     # 暗槓不算外露搭子
    #     return sum(1 for meld in self.ExposedMelds if meld.Exposed)

    def NumMelds(self) -> int:
        """計算玩家外露搭子（吃/碰/槓/暗槓）的總數。"""
        return len(self.ExposedMelds)

    def RemoveTiles(self, tiles:list[Tile]):
        for tile in tiles:
            self.Hand.remove(tile)

if __name__ == '__main__':

    tile = Tile({'alias':'東'})
    hand = Tile.Alias2Tile(["東","東","東"])
    print(hand+[tile])

