from Tile import *
from Deck import *
from Score import HandCondition
# import Deck

import time
from enum import Enum
from collections import Counter
from threading import Thread, Event

class Action(Enum):
    HU = 4
    KONG = 3
    # ADD_KONG = 3
    PONG = 2
    CHOW = 1
    PASS = 0

    DICE    = 10 # roll dice
    DRAWING = 11
    DISCARD = 12

class KongType(Enum):
    EXPOSED_KONG = 1 # 明槓
    DRAW_KONG = 2    # 摸槓
    HIDE_KONG = 3    # 暗槓
    ADD_KONG = 4     # 加槓
    ADD_EXPOSED_KONG = 5 # 加明槓

class Result(Enum):
    NONE = 0
    OK = 1
    WALL_EMPTY = 3
    DEAD_WALL_EMPTY = 4


# Player 類別：管理手牌與公開牌
class Player(Thread):
    # import Deck
    # from Deck import Deck

    ExitEvent = None
    ActionEvent = None
    FinishEvent = None
    #Player 當前要執行的動作
    Actions:Action = None
    Name:str = ''
    # Client ID
    CId:int = 0
    Money:int = 3000

    # 是否為莊家
    IsDealer:bool = False
    # 風位
    Wind:WIND = None
    # 存放明搭 <=5 搭
    Melds:list[Meld] = None
    # 存放花牌
    Flowers:list[Tile] = None
    # 存放摸進的牌 <= 17
    Hand:list[Tile] = None

    # UI玩家選擇的暫存牌
    LastDraw:Tile = None
    LastDiscard:Tile = None
    LastKong:Tile = None
    DrawFromEnd:bool = False
    KongMode:KongType = None

    LastPong:Tile = None
    # 存放手牌預被吃成搭的2張牌
    LastChows:list[Tile] = None
    LastHu:Tile = None

    DeckRef:Deck = None
    # 給UI對應操作的狀態
    ActionState:dict = None
    ActionResult:Result = None

    # 檢查過水
    PassHu:bool = False

    # 胡牌結算
    Condition:HandCondition = None

    def __init__(self, name:str, wind:WIND, deck:Deck):
        super().__init__(name=wind.name)
        self.Name = name
        self.Wind = wind
        self.DeckRef = deck

        # 東風玩家預設起始為莊家
        if self.Wind == WIND.EAST:
            self.IsDealer = True

        self.ExitEvent = Event()
        self.ActionEvent = Event()
        self.FinishEvent = Event()
        self.Condition = HandCondition()
        self.Reset()

    def Reset(self):
        # 玩家手牌 (16 或 17 張)
        self.Hand = []
        # 已亮出的花牌 Exposed Flowers
        self.Flowers = []
        # 已完成的搭子 (吃/碰/槓/暗槓) Exposed Melds
        self.Melds = []
        # 上次出的牌
        self.LastDiscard = None
        self.LastDraw = None
        self.LastKong = None
        self.DrawFromEnd = False
        self.KongMode = None
        self.LastPong = None
        self.LastChows = []
        self.LastHu = None

        # # Game Deck 檢查後，通知玩家目前可操作的狀態
        # self.ActionState = {
        #     # 摸牌, 出牌
        #     Action.DRAWING:False, Action.DISCARD:False, 
        #     # 胡/槓/碰/吃/過
        #     Action.HU:False, Action.KONG:False, Action.PONG:False, Action.CHOW:False, Action.PASS:False
        # }
        self.Actions = None
        self.ActionResult = Result.NONE
        self.PassHu = False

        self.Condition.Reset()
        self.EventClear()

    def run(self):
        while not self.ExitEvent.is_set():
            # 執行UI玩家所下的命令
            if self.ActionEvent.is_set():
                self.ActionResult = Result.OK
                # 胡/吃/碰/槓/Pass
                match self.Actions:
                    case Action.HU:
                        # 暗胡(自摸) or 明胡(其他家放槍)
                        # 玩家進行胡牌

                        # 搶槓胡
                        if self.DeckRef.LastAddKong != None:
                            self.LastHu = self.DeckRef.LastAddKong
                        # 自摸
                        elif self.LastDraw != None:
                            self.LastHu = self.LastDraw
                        # 其他家放槍
                        else:
                            self.LastHu = self.DeckRef.LastDiscard

                        hu = self.LastHu
                        PrintLog(self.Name + ' 胡牌: ' + hu.toStr())
                        if self.DeckRef.LastDiscard == hu:
                            self.DeckRef.DiscardWin = hu
                            # 當丟出的牌被3家其中一家拿去，則從棄牌區取回
                            self.DeckRef.PickUPDiscardTile()

                        # 確認玩家手牌所有情況
                        # HandCondition
                        # 下一步計算玩家台數
                        self.FinishEvent.set()
                    case Action.KONG:
                        # 玩家進行槓牌
                        kong = self.LastKong
                        tiles = []

                        match self.KongMode:
                            # 明槓, 3 tiles in hand and 1 tile is DeckRef.LastDiscard
                            case KongType.EXPOSED_KONG:
                                tiles.extend([kong]*(MELD.KONG_LEN.value-1))
                                # 將手牌的槓搭複制進Meld list
                                self.AddMeld(tiles+[kong], False)
                                # 閒家丟出的牌被當前玩家拿去，則從棄牌區取回
                                self.DeckRef.PickUPDiscardTile()
                            # 摸槓, 3 tiles in hand and 1 tile is LastDraw
                            case KongType.DRAW_KONG:
                                tiles.extend([kong]*(MELD.KONG_LEN.value-1))
                                # 將手牌的槓搭複制進Meld list
                                self.AddMeld(tiles+[kong], True)
                            # 暗槓, 4 tiles in hand and 1 tile is LastDraw
                            case KongType.HIDE_KONG:
                                #摸進牌先放進手牌裡
                                self.SetHandTile([self.LastDraw])
                                tiles.extend([kong]*MELD.KONG_LEN.value)
                                # 將手牌的槓搭複制進Meld list
                                self.AddMeld(tiles, True)
                            # 加槓, 3 tiles in melds and 1 tile is LastDraw
                            case KongType.ADD_KONG:
                                # 將摸進的牌與碰塔組成加槓，然後清掉摸進的牌
                                # 將明搭裡的碰搭變更成槓搭
                                self.Pong2Kong(kong)
                            case KongType.ADD_EXPOSED_KONG:
                                #摸進牌先放進手牌裡
                                self.SetHandTile([self.LastDraw])
                                tiles.extend([kong])
                                # 將手牌裡的牌與碰塔組成加槓，然後清掉手牌進的牌
                                # 將明搭裡的碰搭變更成槓搭
                                self.Pong2Kong(kong)
                            case _:
                                pass

                        PrintLog(self.Name + f' 槓牌({self.KongMode.name}): ' + kong.toStr() + ", " + ",".join(Tile.List2StrList(tiles)))

                        # 清除手牌的槓搭
                        self.LastDraw = None
                        if len(tiles):
                            self.RemoveTiles(tiles)

                        self.DrawFromEnd = True
                        # 下一步通知玩家摸一打一
                        self.FinishEvent.set()
                    case Action.PONG:
                        # 玩家進行碰牌
                        # 碰閒家牌
                        self.LastPong = self.DeckRef.LastDiscard
                        pong = self.LastPong
                        tiles = [pong]*(MELD.PONG_LEN.value-1)
                        # 將手牌的碰搭複制進Meld list
                        self.AddMeld(tiles+[pong])
                        PrintLog(self.Name + ' 碰牌: ' + pong.toStr() + ", " + ",".join(Tile.List2StrList(tiles)))
                        # 當丟出的牌被3家其中一家拿去，則從棄牌區取回
                        self.DeckRef.PickUPDiscardTile()
                        # 清除手牌的碰搭
                        self.RemoveTiles(tiles)
                        # 下一步通知玩家出牌
                        self.FinishEvent.set()
                    case Action.CHOW:
                        # 玩家指家吃的牌型
                        # 吃上家牌
                        # ex: 6 in LastDiscard
                        chow = self.DeckRef.LastDiscard
                        # ex: 5,7 in LastChows
                        tiles = self.LastChows.copy()
                        # 吃到的牌放中間
                        tiles.insert(1,chow)
                        # 將手牌的碰搭複制進Meld list
                        self.AddMeld(tiles)
                        PrintLog(self.Name + ' 吃牌: ' + chow.toStr() + ", " + ", ".join(Tile.List2StrList(self.LastChows)))
                        # 當丟出的牌被3家其中一家拿去，則從棄牌區取回
                        self.DeckRef.PickUPDiscardTile()
                        # 清除手牌的碰搭
                        self.RemoveTiles(self.LastChows)
                        # 下一步通知玩家出牌
                        self.FinishEvent.set()
                    case Action.PASS:
                        # 放棄胡/槓/碰/吃的機會
                        PrintLog(self.Name + ' 跳過')
                        self.FinishEvent.set()

                    case Action.DICE:
                        # 玩家進行擲骰子
                        dice = self.DeckRef.RollDice()
                        PrintLog(self.Name + ' 擲骰子: ' + str(dice))
                        self.FinishEvent.set()
                    case Action.DRAWING:
                        # 玩家進行摸牌
                        fromEnd = self.DrawFromEnd
                        if self.DrawFromEnd:
                            self.DrawFromEnd = False

                        tile = self.DeckRef.DrawWallTile(fromEnd)
                        if tile == None:
                            self.ActionResult = Result.WALL_EMPTY
                            PrintLog(self.Name + ' 牆區沒牌可以摸了！')
                            self.FinishEvent.set()
                            continue

                        self.LastDraw = tile
                        if tile.IsFlower():
                            ret = self.DeckRef.PatchFlower(self)
                            if not ret:
                                self.ActionResult = Result.DEAD_WALL_EMPTY
                                PrintLog(self.Name + ' 死牆區沒牌可以摸了！')
                                self.FinishEvent.set()
                                continue

                        PrintLog(self.Name + ' 摸牌: ' + self.LastDraw.toStr())
                        self.FinishEvent.set()
                    case Action.DISCARD:
                        # 摸/吃/碰時需出牌
                        # 玩家進行 摸牌/吃牌/碰牌
                        # 摸牌
                        if self.LastDraw != None:
                            #摸進牌先放進手牌裡
                            self.SetHandTile([self.LastDraw])
                            # 玩家決定出牌，最後放進 self.LastDiscard
                            self.LastDraw = None

                        # 吃牌/碰牌
                        # else:
                        # 玩家決定出牌，最後放進 self.LastDiscard

                        # 玩家進行出牌
                        self.Hand.remove(self.LastDiscard)
                        PrintLog(self.Name + ' 出牌: ' + self.LastDiscard.toStr())
                        self.DeckRef.DiscardTile(self.Wind, self.LastDiscard)
                        self.FinishEvent.set()
                    case _:
                        pass

                self.Actions = None
                self.ActionEvent.clear()
            else:
                time.sleep(0.2)
                # PrintLog('sleep:'+self.Wind.name)

    def Wait(self) -> Result:
        PrintLog('Action waiting\n')
        self.FinishEvent.wait()
        self.FinishEvent.clear()
        PrintLog('Action finish')
        return self.ActionResult

    def Notify(self):
        self.ActionEvent.set()

    def EventClear(self):
        self.ActionEvent.clear()
        self.FinishEvent.clear()

    def Exit(self):
        self.ExitEvent.set()

    def SetHandTile(self, hand:list[Tile]):
        PrintLog('SetHandTile:'+", ".join(Tile.List2StrList(hand)))
        # for _ in range(len(hand)):
        #     self.Hand.append(hand.pop(0))
        self.Hand.extend(hand)#.copy())
        self.Hand.sort()

    def SetFlowerTile(self, tile:Tile):
        if tile.IsFlower():
            self.Flowers.append(tile)
            self.Flowers.sort()

    def ReturnAllTile(self) -> list[Tile]:
        hand = [] #list[Tile]
        for _ in range(len(self.Hand)):
            hand.append(self.Hand.pop(0))
        for _ in range(len(self.Flowers)):
            hand.append(self.Flowers.pop(0))
        for meld in self.Melds:
            for _ in range(len(meld.Tiles)):
                hand.append(meld.Tiles.pop(0))
        if self.LastDraw != None:
            hand.append(self.LastDraw)

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
        self.Melds.append(Meld(not concealed, tiles.copy()))

    def Pong2Kong(self, kong:Tile):
        for meld in self.Melds:
            if meld.Type == MELD.PONG and kong in meld.Tiles:
                meld.Type = MELD.KONG
                meld.Tiles.append(kong)
                break

    # def NumMelds(self) -> int:
    #     """計算玩家外露搭子（碰、吃、明槓）的總數。"""
    #     # 暗槓不算外露搭子
    #     return sum(1 for meld in self.Melds if meld.Exposed)

    def NumMelds(self) -> int:
        """計算玩家外露搭子（吃/碰/槓/暗槓）的總數。"""
        return len(self.Melds)

    def RemoveTiles(self, tiles:list[Tile]):
        for tile in tiles:
            self.Hand.remove(tile)
        self.Hand.sort()

if __name__ == '__main__':

    tile = Tile({'alias':'東'})
    hand = Tile.Alias2Tile(["東","東","東"])
    for tile in (hand+[tile]):
        print(tile)
