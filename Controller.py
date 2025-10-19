from Tile import *
from Deck import Deck
from Player import *
from Model import Rule16 as Rule

from pubsub import pub as Publisher

# 負責串聯所有邏輯：管理回合、處理動作優先級 (吃/碰/槓/胡)
# Game controller
class Controller:
    IsStart: bool = False
    Players: dict[WIND, Player] = {}
    DeckRef: Deck = None
    RoundWind: WIND = WIND.EAST # 局風位
    CurrentWind: WIND = WIND.EAST # 當前回合的玩家
    DealerWind: WIND = WIND.EAST # 莊家風位
    RoundNum: int = 0 # 局數 (東南西北)
    GameNum: int = 0 # 第幾莊

    Exit:bool = False
    State = {
        "player":"",
        "dice":False, "drawing":False, "discard":False,
        "hu":False, "kong":False, "pong":False, "chow":False, "pass":False
    }
    ActionState:dict[WIND, dict] = {}
    Pass:dict[WIND, bool] = {}

    def __init__(self):
        # internal communication
        # web app send message to controller
        Publisher.subscribe(self.OnMessage, "controller")

        self.DeckRef = Deck()
        self.Players = {
            WIND.EAST: Player('小東', WIND.EAST, self.DeckRef), 
            WIND.SOUTH: Player('小南', WIND.SOUTH, self.DeckRef), 
            WIND.WEST: Player('小西', WIND.WEST, self.DeckRef), 
            WIND.NORTH: Player('小北', WIND.NORTH, self.DeckRef)
        }
        for player in self.Players.values():
            player.daemon = True
            player.start()

        for w in WIND:
            self.ActionState[w] = self.State.copy()
            self.ActionState[w]["player"] = w.name.lower()
            self.Pass[w] = False


    # def Start(self):
    #     self.MsgThread = Thread(target=self.PutMsg)
    #     self.MsgThread.start()

    # def PutMsg(self):
    #     while not self.Exit:
    #         cmd = {
    #             "join_game":{
    #                 "state":"waiting",
    #                 "wait_num":4
    #             },
    #             "action_state":{
    #                 "player":"east",
    #                 "dice":True, "drawing":False, "discard":False,
    #                 "hu":False, "kong":False, "pong":False, "chow":False, "pass":False
    #             }
    #         }
    #         # print('PutMsg')
    #         self.Notify(cmd)
    #         time.sleep(2)
    #     print('End PutMsg')

    def ResetGame(self):
        # 回收所有牌
        all_tiles = []
        for player in self.Players.values():
            all_tiles.extend(player.ReturnAllTile())
        all_tiles.extend(self.DeckRef.Wall)
        all_tiles.extend(self.DeckRef.DeadWall)
        for discard_pile in self.DeckRef.Discard.values():
            all_tiles.extend(discard_pile)
        self.DeckRef.Tiles = all_tiles
        self.DeckRef.FlushTiles({}) # 清空所有牌堆

        # 重置玩家狀態
        for player in self.Players.values():
            player.Reset()

        # 重置牌堆
        self.DeckRef = Deck()
        self.CurrentWind = self.DealerWind # 回合從莊家開始

    # 4位client到齊，開桌
    # 直到玩完一雀
    def StartGame(self):
        self.IsStart = True
        self.StartRound()

    def StartRound(self):
        # 1. 洗牌、切牌
        diceScore = random.randint(3,18)
        self.DeckRef.BreakingWall(self.DealerWind, diceScore)

        # 2. 發牌
        handTiles = {WIND.EAST:[], WIND.SOUTH:[], WIND.WEST:[], WIND.NORTH:[]}
        self.DeckRef.DealTiles(handTiles)
        for key,val in handTiles.items():
            self.Players[key].SetHandTile(val)

        # 所有玩家補花
        self.DeckRef.ReplaceFlowers(self.Players)

    def EndRound(self):
        pass

    # 處理動作優先級 (吃/碰/槓/胡)
    # 決定閒家(1.下家/2.對家/3.上家)優先權
    def DecideWhoseTurn(self, next:bool = False) -> WIND:
        # 找出閒家
        other = self.CurrentWind.Other()
        # 下家
        right = other[0]
        # 判斷閒家對打出的牌具有哪些動作
        tile = self.DeckRef.LastDiscard
        if not next:
            for w in other:
                hand = self.Players[w].Hand
                self.ActionState[w]['hu'] = Rule.CanHu(hand, tile)
                self.ActionState[w]['kong'] = Rule.CanKong(hand, tile)
                self.ActionState[w]['pong'] = Rule.CanPong(hand, tile)
                # 只有下家具有吃的動作
                self.ActionState[w]['chow'] = False
                self.ActionState[w]['drawing'] = False
                if w == right:
                    self.ActionState[w]['chow'] = Rule.CanChow(hand, tile)
                    self.ActionState[w]['drawing']
                if self.ActionState[w]['hu'] or self.ActionState[w]['kong'] or self.ActionState[w]['pong'] or self.ActionState[w]['chow'] or self.ActionState[w]['drawing']:
                    self.ActionState[w]['pass'] = True

        # check priority
        for w in other:
            if not self.Pass[w] and self.ActionState[w]['hu']:
                return w
        for w in other:
            if not self.Pass[w] and self.ActionState[w]['kong']:
                return w
        for w in other:
            if not self.Pass[w] and self.ActionState[w]['pong']:
                return w
        for w in other:
            if not self.Pass[w] and self.ActionState[w]['chow']:
                return w
        for w in other:
            if not self.Pass[w] and self.ActionState[w]['drawing']:
                return w
        # 預設換下家
        return right

    # 通知 client 進行活動
    # controller -> web app
    def Notify(self, msg:str):
        Publisher.sendMessage('webapp', msg=msg)

    # web app -> controller
    def OnMessage(self, msg):
        print('controller received message:')
        print(msg)

if __name__ == '__main__':
    
    ctrl = Controller()
    ctrl.StartGame()
    PrintLog('Finish')    