from Tile import *
from Deck import Deck
from Player import *
from Model import Rule16 as Rule

from pubsub import pub as Publisher
import json

class Step(Enum):
    INIT = 0
    START_GAME = 1
    PLAYER_SEAT = 2
    ROLL_DICE_NOTIFY = 3
    ROLL_DICE = 4
    START_ROUND = 5

    # DEAL_TILES = 6
    # REPLACE_FLOWERS = 5
    PLAYER_DRAW_NOTIFY = 6
    PLAYER_DRAW = 7
    PLAYER_DISCARD = 8
    PLAYER_ACTION = 9
    NEXT_TURN = 9
    END_ROUND = 10
    END_GAME = 11


# 負責串聯所有邏輯：管理回合、處理動作優先級 (吃/碰/槓/胡)
# Game controller
class Controller:
    IsStart: bool = False
    Players: dict[WIND, Player] = {}
    DeckRef: Deck = None
    RoundWind: WIND = WIND.EAST # 局風位
    ActiveWind: WIND = WIND.EAST # 當前活動的玩家
    DealerWind: WIND = WIND.EAST # 莊家風位
    RoundNum: int = 0 # 局數 (東南西北)
    DealerNum: int = 0 # 第幾莊

    Exit:bool = False
    State = {
        "player":"",
        "dice":False, "drawing":False, "discard":False,
        "hu":False, "kong":False, "pong":False, "chow":False, "pass":False
    }
    ActionState:dict[WIND, dict] = {}
    Pass:dict[WIND, bool] = {}

    StepEvent = Event()
    StepWorker:Thread = None
    StepAction:Step = 0

    def __init__(self):
        # internal communication
        # web app send message to controller
        Publisher.subscribe(self.OnMessage, "controller")

        self.DeckRef = Deck()
        self.Players = {
            WIND.EAST: Player('', WIND.EAST, self.DeckRef), 
            WIND.SOUTH: Player('', WIND.SOUTH, self.DeckRef), 
            WIND.WEST: Player('', WIND.WEST, self.DeckRef), 
            WIND.NORTH: Player('', WIND.NORTH, self.DeckRef)
        }
        for player in self.Players.values():
            player.daemon = True
            player.start()

        for w in WIND:
            self.ActionState[w] = self.State.copy()
            self.ActionState[w]["player"] = w.name.lower()
            self.Pass[w] = False

        # 用來處理步驟流程
        self.StepWorker = Thread(target=self.StepFlow)
        self.StepWorker.daemon = True
        self.StepWorker.start()

    def Seat(self, name:str) -> str:
        for w, p in self.Players.items():
            if p.Name == name:
                return w.name.lower()
        return ''

    def StepFlow(self):
        while not self.Exit:
            if self.StepEvent.is_set():
                self.StepEvent.clear()
                match self.StepAction:
                    case Step.INIT:
                        pass
                    case Step.START_GAME:
                        pass
                    case Step.PLAYER_SEAT:
                        seat = {
                            "player_seat":{"east":"","south":"","west":"","north":""}
                        }
                        for w, p in self.Players.items():
                            seat["player_seat"][w.name.lower()] = p.Name
                        self.Notify(seat)
                        time.sleep(2)
                        # self.Notify(json.dumps(seat))
                        self.StepAction = Step.ROLL_DICE_NOTIFY
                        self.StepEvent.set()
                    case Step.ROLL_DICE_NOTIFY:
                        action = {
                            "notify":self.ActiveWind.name.lower(),
                            "action_state":{
                                "dice":True, "drawing":False, "discard":False,
                                "hu":False, "kong":False, "pong":False, "chow":False, "pass":False
                            }
                        }
                        self.Notify(action)
                    case Step.ROLL_DICE:
                        player = self.Players[self.DealerWind]
                        player.Actions = Action.DICE
                        player.Notify()
                        player.Wait()
                        state = {
                            "game_state":{
                                "round_wind":self.RoundWind.name.lower(),
                                "dealer_wind":self.DealerWind.name.lower(),
                                "current_player":self.ActiveWind.name.lower(),
                                "dealer_num":self.DealerNum,
                                "dice_score":self.DeckRef.Dice
                            }
                        }
                        self.Notify(state)
                        # PrintLog("骰子:" + str(self.DeckRef.Dice))
                        self.StepAction = Step.START_ROUND
                        self.StepEvent.set()

                    case Step.START_ROUND:
                        self.StartRound()
                        self.StepAction = Step.PLAYER_DRAW_NOTIFY
                        self.StepEvent.set()
                    case Step.PLAYER_DRAW_NOTIFY:
                        action = {
                            "notify":self.ActiveWind.name.lower(),
                            "action_state":{
                                "dice":False, "drawing":True, "discard":False,
                                "hu":False, "kong":False, "pong":False, "chow":False, "pass":False
                            }
                        }
                        self.Notify(action)

                    case Step.PLAYER_DRAW:
                        player = self.Players[self.ActiveWind]
                        player.Actions = Action.DRAWING
                        player.Notify()
                        player.Wait()

                        tiles = []
                        for t in player.Hand:
                            tiles.append(t.Name)

                        flower = []
                        for f in player.Flowers:
                            flower.append(f.Name)

                        hand = {
                            "notify":self.ActiveWind.name.lower(), # all, east, south, west, north
                            "hand_tiles":{
                                "east":{
                                    "hand":tiles,
                                    "meld":[],
                                    "hide":[],
                                    "flower":flower,
                                    "discard":[],
                                    "drawed":player.LastDraw.Name
                                }
                            }
                        }
                        self.Notify(hand)
                    case Step.PLAYER_DISCARD:
                        self.StepAction = Step.PLAYER_ACTION
            else:
                time.sleep(0.1)

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
        self.ActiveWind = self.DealerWind # 回合從莊家開始

    # WebApp 通知 Controller
    # 4位client到齊，開桌
    # 直到玩完一雀
    def StartGame(self, names:dict[int,str]):
        # names:dict[int,str]
        # key:client id, value:name
        self.IsStart = True

        # 隨機抽風位
        seat = [WIND.EAST, WIND.SOUTH, WIND.WEST, WIND.NORTH]
        random.shuffle(seat)
        i = iter(names.items())
        for w in seat:
            cid, names = next(i)
            self.Players[w].CId = cid
            self.Players[w].Name = names

        self.RoundWind = WIND.EAST # 局風位
        self.ActiveWind = WIND.EAST # 當前活動的玩家
        self.DealerWind = WIND.EAST # 莊家風位

        # 通知玩家自已的風位
        self.StepAction = Step.PLAYER_SEAT
        self.StepEvent.set()

    def StartRound(self):
        # 1. 洗牌
        self.DeckRef.Shuffle()

        # 2. 切牌
        # diceScore = random.randint(3,18)
        diceScore = sum(self.DeckRef.Dice)
        PrintLog("骰子:" + str(diceScore))
        self.DeckRef.BreakingWall(self.DealerWind, diceScore)

        # 2. 發牌
        handTiles = {WIND.EAST:[], WIND.SOUTH:[], WIND.WEST:[], WIND.NORTH:[]}
        self.DeckRef.DealTiles(handTiles)
        for key,val in handTiles.items():
            self.Players[key].SetHandTile(val)

        # 3. 所有玩家補花
        self.DeckRef.ReplaceFlowers(self.Players)

    def EndRound(self):
        pass

    # 打出牌後，叫用DecideWhoseTurn()決定閒家優先權
    # 處理動作優先級 (吃/碰/槓/胡)
    # 決定閒家(1.下家right 2.對家opposite 3.上家left)優先權
    # 參數next:下家決定pass，換對家或上家，無需重新確認手牌動作
    def DecideWhoseTurn(self, next:bool = False) -> WIND:
        # 找出閒家
        other = self.ActiveWind.Other()
        # 下家
        right = other[0]
        # 判斷閒家對打出的牌具有哪些動作
        tile = self.DeckRef.LastDiscard
        if not next:
            self.ClearActionState()
            for w in other:
                hand = self.Players[w].Hand
                CanHu = Rule.CanHu(hand, tile)
                CanKong = Rule.CanKong(hand, tile)
                CanAddKong = Rule.CanAddKong(self.Players[w].Melds, tile)
                CanPong = Rule.CanPong(hand, tile)
                CanChow = False
                CanDrawing = False
                CanPass = False

                # 只有下家具有吃/摸的動作
                if w == right:
                    CanChow = Rule.CanChow(hand, tile)
                    CanDrawing = True
                # 只有下家沒有pass的動作
                elif CanHu or CanKong or CanAddKong or CanPong:
                    CanPass = True

                self.ActionState[w]['hu'] = CanHu
                self.ActionState[w]['kong'] = (CanKong or CanAddKong)
                self.ActionState[w]['pong'] = CanPong
                self.ActionState[w]['chow'] = CanChow
                self.ActionState[w]['drawing'] = CanDrawing
                self.ActionState[w]['pass'] = CanPass

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

        # 只有下家具有吃/摸的動作，但沒有pass的動作
        if self.ActionState[right]['chow']:
            return right
        if self.ActionState[right]['drawing']:
            return right

        # 預設換下家摸牌
        return right

    def ClearActionState(self):
        for w in WIND:
            for key in self.State.keys():
                if key == 'player':
                    continue
                self.ActionState[w][key] = False
            self.Pass[w] = False

    # 通知 client 進行活動
    # controller -> web app
    def Notify(self, msg:str):
        Publisher.sendMessage('webapp', msg=msg)

    # web app -> controller
    def OnMessage(self, msg):
        PrintLog('controller received message:')
        PrintLog(msg)
        if 'action' in msg:
            if msg['action'] == 'dice':
                self.StepAction = Step.ROLL_DICE
                self.StepEvent.set()
            elif msg['action'] == 'drawing':
                self.StepAction = Step.PLAYER_DRAW
                self.StepEvent.set()

if __name__ == '__main__':

    ctrl = Controller()
    ctrl.StartGame({1:"小東", 2:"小南", 3:"小西", 4:"小北"})
    PrintLog('Finish')