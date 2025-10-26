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

    PLAYER_DRAW_NOTIFY = 6
    PLAYER_DRAW = 7
    PLAYER_DISCARD_NOTIFY = 8
    PLAYER_DISCARD = 9

    DECIDE_WHOSE_TURN = 10
    WHOSE_NEXT_TURN = 11

    PLAYER_HU = 13
    PLAYER_KONG = 14
    PLAYER_PONG = 15
    PLAYER_CHOW = 16
    PLAYER_PASS = 17

    DRAW_GAME = 20
    END_ROUND = 36
    END_GAME = 37


# 負責串聯所有邏輯：管理回合、處理動作優先級 (吃/碰/槓/胡)
# Game controller
class Controller:
    IsStart: bool = False
    Players: dict[WIND, Player] = {}
    DeckRef: Deck = None
    RoundWind: WIND = WIND.EAST # 局風位
    ActiveWind: WIND = WIND.EAST # 當前活動的玩家

    # 處理活動玩家出牌之後其他閒家過牌(碰/槓/胡)，
    # 在Next決定輸誰活動時以先前出牌的人為主
    OldWind: WIND = None

    DealerWind: WIND = WIND.EAST # 莊家風位
    RoundNum: int = 0 # 局數 (東南西北)
    DealerNum: int = 0 # 第幾莊

    Exit:bool = False
    State = {
        "dice":False, "drawing":False, "discard":False,
        "hu":False, "kong":False, "pong":False, "chow":False, "pass":False
    }
    ActionState:dict[WIND, dict] = {}
    Pass:dict[WIND, bool] = {}

    StepEvent = None
    StepWorker:Thread = None
    StepAction:Step = 0

    Msg:list = None

    def __init__(self):

        self.StepEvent = Event()
        self.Msg = []
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

    def GetHandAndOutHandDict(self, wind:WIND) -> dict:
        player = self.Players[wind]
        tiles = Tile.List2StrList(player.Hand)
        flower = Tile.List2StrList(player.Flowers)
        discard = Tile.List2StrList(self.DeckRef.Discard[player.Wind])
        meld, hide = Meld.List2StrList(player.Melds)

        hand = {
            "notify":player.Wind.name.lower(),
            "hand_tiles":[{
                "hand":tiles,
                "drawed":'' if player.LastDraw == None else str(player.LastDraw)
            }],
            "out_tiles":[{
                "seat":player.Wind.name.lower(),
                "meld":meld,
                "hide":hide,
                "flower":flower,
                "discard":discard
            }]
        }
        return hand

    def GetHandDict(self, wind:WIND) -> dict:
        player = self.Players[wind]
        tiles = Tile.List2StrList(player.Hand)

        hand = {
            "notify":player.Wind.name.lower(),
            "hand_tiles":[{
                "hand":tiles,
                "drawed":'' if player.LastDraw == None else str(player.LastDraw)
            }]
        }
        return hand

    def GetOutHandDict(self, wind:WIND, notify:WIND = None, showhide:bool = True) -> dict:
        #
        # if notify=None, denote notify for 'all'
        #
        player = self.Players[wind]
        flower = Tile.List2StrList(player.Flowers)
        discard = Tile.List2StrList(self.DeckRef.Discard[player.Wind])
        meld, hide = Meld.List2StrList(player.Melds, showhide)
        target = 'all' if notify == None else notify.name.lower()

        hand = {
            "notify":target,
            "out_tiles":[{
                "seat":player.Wind.name.lower(),
                "meld":meld,
                "hide":hide,
                "flower":flower,
                "discard":discard
            }]
        }
        return hand

    def GetHuTilesDict(self, wind:WIND) -> dict:
        player = self.Players[wind]
        tiles = Tile.List2StrList(player.Hand)
        flower = Tile.List2StrList(player.Flowers)
        meld, hide = Meld.List2StrList(player.Melds)

        DrawedWin, DiscardWin, DiscardSeat = '', '', ''
        # 自摸
        if player.LastDraw != None:
            DrawedWin = str(player.LastDraw)
        # 放槍
        else:
            DiscardWin = str(self.DeckRef.LastDiscard)
            DiscardSeat = self.DeckRef.LastWind.name.lower()

        hand = {
            "notify":"all",
            "hu_tiles":[{
                "seat":player.Wind.name.lower(),
                "discard_seat":DiscardSeat,
                "hand":tiles,
                # 自摸
                "drawed_win":DrawedWin,
                # 放槍
                "discard_win":DiscardWin,
                "meld":meld,
                "hide":hide,
                "flower":flower
            }]
        }
        return hand

    def UpdatePlayerState(self, action:str = ''):
        # 通知所有玩家換誰進行活動
        data = {
            "notify":'all',
            "player_state":{
                "whoes_turn":self.ActiveWind.name.lower(),
                "action":action
            }
        }
        self.Notify(data)

    def UpdatePlayerHandState(self):
        # 通知閒家，當前玩家 暗槓/明槓,碰/吃 的牌
        for w in self.ActiveWind.Other():
            hand = self.GetOutHandDict(self.ActiveWind, notify=w, showhide=False)
            self.Notify(hand)

        # 通知當前玩家 手牌 和 外露牌 情況
        hand = self.GetHandAndOutHandDict(self.ActiveWind)
        self.Notify(hand)

        # 因前一個玩家所丟出的牌被當前玩家 槓/碰/吃 走
        # 通知前一個玩家 外露牌 情況
        hand = self.GetOutHandDict(self.DeckRef.LastWind, notify=self.DeckRef.LastWind)
        self.Notify(hand)

        # 通知所有玩家，前一個玩家的牌被 槓/碰/吃 掉了
        for w in self.DeckRef.LastWind.Other():
            hand = self.GetOutHandDict(self.DeckRef.LastWind, notify=w, showhide=False)
            self.Notify(hand)

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
                        # 通知所有玩家換誰進行活動
                        self.UpdatePlayerState('dice')

                        self.ClearActionState(self.ActiveWind)
                        state = self.ActionState[self.ActiveWind]
                        state['dice'] = True
                        action = {
                            "notify":self.ActiveWind.name.lower(),
                            "action_state":state
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
                        PrintLog("state:" + str(state))
                        self.StepAction = Step.START_ROUND
                        self.StepEvent.set()

                    case Step.START_ROUND:
                        self.StartRound()
                        self.StepAction = Step.PLAYER_DRAW_NOTIFY
                        self.StepEvent.set()

                    # C. 牌局循環
                    case Step.PLAYER_DRAW_NOTIFY:
                        # 通知所有玩家換誰進行活動
                        self.UpdatePlayerState('drawing')

                        self.ClearActionState(self.ActiveWind)
                        state = self.ActionState[self.ActiveWind]
                        state['drawing'] = True

                        action = {
                            "notify":self.ActiveWind.name.lower(),
                            "action_state":state
                        }
                        self.Notify(action)

                    # 玩家決定進行摸牌動作
                    case Step.PLAYER_DRAW:
                        player = self.Players[self.ActiveWind]
                        player.Actions = Action.DRAWING
                        player.Notify()
                        player.Wait()

                        hand = self.GetHandDict(self.ActiveWind)
                        # 通知玩家摸到的牌
                        self.Notify(hand)

                        # 檢查手牌狀態(滿17張,16張手牌+摸1張牌) 胡牌/槓牌/出牌
                        self.CheckHandState()
                        # 通知所有玩家換誰進行活動
                        self.UpdatePlayerState()

                        # 通知玩家進行動作
                        state = self.ActionState[self.ActiveWind]
                        action = {
                            "notify":self.ActiveWind.name.lower(),
                            "action_state":state
                        }
                        self.Notify(action)

                    # 進行碰/吃後，通知玩家出牌
                    case Step.PLAYER_DISCARD_NOTIFY:
                        # 通知所有玩家換誰進行活動
                        self.UpdatePlayerState('discard')

                        self.ClearActionState(self.ActiveWind)
                        state = self.ActionState[self.ActiveWind]
                        state['discard'] = True

                        action = {
                            "notify":self.ActiveWind.name.lower(),
                            "action_state":state
                        }
                        self.Notify(action)

                    # 玩家決定進行出牌動作
                    case Step.PLAYER_DISCARD:
                        # {'player': 'east', 'action': 'discard', 'tiles': ['2S']}
                        msg = self.Msg.pop()
                        tile = msg['tiles'].pop()
                        player = self.Players[self.ActiveWind]
                        player.Actions = Action.DISCARD
                        player.LastDiscard = Tile.Str2Tile(tile)
                        player.Notify()
                        player.Wait()
                        player.LastDiscard = None

                        # 解除過水
                        if player.PassHu:
                            player.PassHu = False

                        # 通知所有玩家，當前玩家打出的牌
                        for w in self.ActiveWind.Other():
                            hand = self.GetOutHandDict(self.ActiveWind, notify=w, showhide=False)
                            self.Notify(hand)

                        # 通知當前玩家 手牌 和 外露牌 情況
                        hand = self.GetHandAndOutHandDict(self.ActiveWind)
                        self.Notify(hand)

                        self.StepAction = Step.DECIDE_WHOSE_TURN
                        self.StepEvent.set()

                    case Step.DECIDE_WHOSE_TURN:
                        self.ActiveWind = self.DecideWhoseTurn()

                        # 通知所有玩家換誰進行活動
                        self.UpdatePlayerState()

                        # 通知玩家進行動作
                        player = self.Players[self.ActiveWind]
                        state = self.ActionState[self.ActiveWind]
                        # 玩家放棄胡牌，需等下一次打出牌後解除過水，才能再胡牌
                        if state['hu'] and player.PassHu:
                            state['hu'] = False
                        action = {
                            "notify":self.ActiveWind.name.lower(),
                            "action_state":state
                        }
                        self.Notify(action)

                    case Step.WHOSE_NEXT_TURN:
                        self.ActiveWind = self.DecideWhoseTurn(True)

                        # 通知所有玩家換誰進行活動
                        self.UpdatePlayerState()

                        # 通知玩家進行動作
                        player = self.Players[self.ActiveWind]
                        state = self.ActionState[self.ActiveWind]
                        # 玩家放棄胡牌，需等下一次打出牌後解除過水，才能再胡牌
                        if state['hu'] and player.PassHu:
                            state['hu'] = False
                        action = {
                            "notify":self.ActiveWind.name.lower(),
                            "action_state":state
                        }
                        self.Notify(action)

                    #
                    # 玩家決定進行 pass/hu/kong/pong/chow 動作
                    #
                    case Step.PLAYER_PASS:
                        state = self.ActionState[self.ActiveWind]
                        # 玩家放棄胡牌，需等下一次打出牌後解除過水，才能再胡牌
                        if state['hu']:
                            player = self.Players[self.ActiveWind]
                            player.PassHu = True

                        self.Pass[self.ActiveWind] = True
                        self.StepAction = Step.WHOSE_NEXT_TURN
                        self.StepEvent.set()
                    case Step.PLAYER_HU:
                        # 自摸/閒家放槍胡
                        # {'player': 'east', 'action': 'hu'}
                        player = self.Players[self.ActiveWind]
                        player.Actions = Action.HU
                        player.Notify()
                        player.Wait()
                        player.LastHu = None

                        # 通知所有玩家，當前玩家胡的牌
                        hand = self.GetHuTilesDict(self.ActiveWind)
                        self.Notify(hand)

                        # round/wind count

                        # self.RoundNum += 1
                        # self.DealerNum += 1
                        # if self.DealerNum == 4:
                        #     self.DealerNum = 0
                        #     self.RoundWind = self.RoundWind.Other()

                        self.StepAction = Step.END_ROUND
                        self.StepEvent.set()
                        pass
                    case Step.PLAYER_KONG:
                        # 暗槓/明槓
                        # 明槓:{'player': 'east', 'action': 'kong', 'tiles': ['2S','2S','2S']}
                        # 暗槓:{'player': 'east', 'action': 'kong', 'tiles': ['2S','2S','2S','2S']}
                        # 摸槓:{'player': 'east', 'action': 'kong', 'tiles': ['2S','2S','2S','2S']]}
                        # 加槓:{'player': 'east', 'action': 'kong', 'tiles': ['2S']}
                        player = self.Players[self.ActiveWind]
                        player.Actions = Action.KONG
                        # 兩種明槓情況:
                        # 1.明槓:手牌中有碰塔，加上閒家打出一張可組成碰槓
                        #   self.DeckRef.LastDraw is same as tiles and pick up 3 tiles
                        # 2.加槓:外露牌的碰塔，加上後來摸進一張可組成加槓
                        #   player.LastDraw is same as meld and pick up 1 tile
                        # 兩種暗槓情況:
                        # 1.暗槓:一開局抓進來的手牌中就有4張一樣的牌
                        #   player.LastDraw is different and pick up 4 tiles
                        # 2.摸槓:手牌中有碰塔，加上後來摸進一張可組成暗槓
                        #   player.LastDraw is same as tiles and pick up 4 tiles

                        msg = self.Msg.pop()
                        tiles = msg['tiles']
                        # 明槓
                        if len(tiles) == (MELD.KONG_LEN.value - 1) and str(self.DeckRef.LastDiscard) == tiles[0]:
                            # player.LastDraw == None 
                            player.ConcealedKong = False

                        # 摸槓
                        elif len(tiles) == MELD.KONG_LEN.value and str(player.LastDraw) == tiles[0]:
                            player.ConcealedKong = True

                        # 暗槓
                        elif len(tiles) == MELD.KONG_LEN.value and str(player.LastDraw) != tiles[0]:
                            player.ConcealedKong = True

                        #加槓
                        elif len(tiles) == 1 and str(player.LastDraw) == tiles[0]:
                            # 檢查是否加槓(外露塔有明碰)
                            if Rule.CanAddKong(player.Melds, player.LastDraw):
                                player.Actions = Action.ADD_KONG
                                player.ConcealedKong = False

                        player.LastKong = Tile.Str2Tile(tiles[0])
                        player.Notify()
                        player.Wait()

                        player.ConcealedKong = False

                        # 不可清掉LastKong，是用來決定從死牆摸一張牌
                        # player.LastKong = None

                        # 通知閒家，當前玩家暗槓/明槓的牌
                        for w in self.ActiveWind.Other():
                            hand = self.GetOutHandDict(self.ActiveWind, notify=w, showhide=False)
                            self.Notify(hand)

                        # 通知所有玩家更新 手牌 和 外露牌 情況
                        self.UpdatePlayerHandState()

                        # 通知玩家從死牆摸一張牌(然後通知玩家打一張)
                        self.StepAction = Step.PLAYER_DRAW_NOTIFY
                        self.StepEvent.set()
                    case Step.PLAYER_PONG:
                        # {'player': 'east', 'action': 'pong', 'tiles': ['2S','2S']}
                        msg = self.Msg.pop()
                        tile = msg['tiles'].pop()
                        player = self.Players[self.ActiveWind]
                        player.Actions = Action.PONG
                        # 碰閒家的牌放 player.LastPong
                        player.LastPong = Tile.Str2Tile(tile)
                        player.Notify()
                        player.Wait()
                        player.LastPong = None

                        # 通知所有玩家，當前玩家碰的牌
                        for w in self.ActiveWind.Other():
                            hand = self.GetOutHandDict(self.ActiveWind, notify=w, showhide=False)
                            self.Notify(hand)

                        # 通知所有玩家更新 手牌 和 外露牌 情況
                        self.UpdatePlayerHandState()

                        # 通知玩家打一張牌
                        self.StepAction = Step.PLAYER_DISCARD_NOTIFY
                        self.StepEvent.set()
                    case Step.PLAYER_CHOW:
                        # {'player': 'east', 'action': 'chow', 'tiles': ['1S','3S']}
                        msg = self.Msg.pop()
                        tiles = msg['tiles']
                        player = self.Players[self.ActiveWind]
                        player.Actions = Action.CHOW
                        # 吃上家的牌放 self.DeckRef.LastDiscard
                        player.LastChows = [Tile.Str2Tile(t) for t in tiles]
                        player.Notify()
                        player.Wait()
                        player.LastChows.clear()

                        # 通知所有玩家，當前玩家吃的牌
                        for w in self.ActiveWind.Other():
                            hand = self.GetOutHandDict(self.ActiveWind, notify=w, showhide=False)
                            self.Notify(hand)

                        # 通知所有玩家更新 手牌 和 外露牌 情況
                        self.UpdatePlayerHandState()

                        # 通知玩家打一張牌
                        self.StepAction = Step.PLAYER_DISCARD_NOTIFY
                        self.StepEvent.set()

                    case _:
                        pass
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

        # 5. 根據骰子點數切牌牆
        # diceScore = random.randint(3,18)
        diceScore = sum(self.DeckRef.Dice)
        PrintLog("骰子:" + str(diceScore))
        self.DeckRef.BreakingWall(self.DealerWind, diceScore)

        # 6. 玩家抓牌並完成補花
        handTiles = {WIND.EAST:[], WIND.SOUTH:[], WIND.WEST:[], WIND.NORTH:[]}
        self.DeckRef.DealTiles(handTiles)
        for key,val in handTiles.items():
            self.Players[key].SetHandTile(val)

        self.DeckRef.ReplaceFlowers(self.Players)

        # 7. 通知玩家開局手牌/外露牌
        for player in self.Players.values():
            hand = self.GetHandDict(player.Wind)
            self.Notify(hand)

            # 外露牌
            hand = self.GetOutHandDict(player.Wind, player.Wind)
            self.Notify(hand)

            # 通知所有玩家外露牌
            hand = self.GetOutHandDict(player.Wind, showhide=False)
            self.Notify(hand)

    def EndRound(self):
        pass

    # CheckHandState()決定當前玩家下一步的動作
    # 處理動作優先級 (胡牌/槓牌/出牌)
    def CheckHandState(self):
        # 當前玩家
        wind = self.ActiveWind
        player = self.Players[wind]

        self.ClearActionState(wind)

        # 判斷玩家對摸到的牌具有哪些動作
        hand = player.Hand
        tile = player.LastDraw
        CanHu, melds = Rule.CanHu(hand + [tile])
        CanKong = Rule.CanKong(hand, tile)
        # 手牌中已有4張相同的牌
        CanConcealKong = Rule.CanConcealKong(hand)
        CanAddKong = Rule.CanAddKong(player.Melds, tile)

        self.ActionState[wind]['hu'] = CanHu
        self.ActionState[wind]['kong'] = (CanKong or CanAddKong or CanConcealKong)
        self.ActionState[wind]['discard'] = True

    # 打出牌後，叫用DecideWhoseTurn()決定閒家優先權
    # 處理動作優先級 (吃/碰/槓/胡)
    # 決定閒家(1.下家right 2.對家opposite 3.上家left)優先權
    # 參數next:下家決定pass，換對家或上家，無需重新確認手牌動作
    def DecideWhoseTurn(self, next:bool = False) -> WIND:
        # 找出閒家
        if next:
            other = self.OldWind.Other()
        else:
            other = self.ActiveWind.Other()
            self.OldWind = self.ActiveWind

        # 下家
        right = other[0]
        # 判斷閒家對打出的牌具有哪些動作
        tile = self.DeckRef.LastDiscard
        if not next:
            self.ClearActionState()
            for w in other:
                hand = self.Players[w].Hand
                CanHu, melds = Rule.CanHu(hand + [tile])
                CanKong = Rule.CanKong(hand, tile)
                # 手牌中已有4張相同的牌
                # 需輪到自已才能執行暗槓
                # 4張一樣的，不能直接放進優先權檢查
                # CanConcealKong = Rule.CanConcealKong(hand)
                CanAddKong = False
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

        self.ActionState[right]['drawing'] = True
        # 預設換下家摸牌
        return right

    def ClearActionState(self, wind:WIND = None):
        if wind != None:
            for key in self.State.keys():
                self.ActionState[wind][key] = False
            self.Pass[wind] = False
        else:
            for w in WIND:
                for key in self.State.keys():
                    self.ActionState[w][key] = False
                self.Pass[w] = False

    # 通知 client 進行活動
    # controller -> web app
    def Notify(self, msg:str):
        Publisher.sendMessage('webapp', msg=msg)

    # web app -> controller
    def OnMessage(self, msg:dict):
        PrintLog('controller received message:')
        PrintLog(msg)
        if 'action' in msg:
            if msg['action'] != 'get_hand' and msg['player'] != self.ActiveWind.name.lower():
                PrintLog(f'{msg['player']}, not your turn!')
                return

            match msg['action']:
                case 'dice':
                    self.StepAction = Step.ROLL_DICE
                    self.StepEvent.set()
                    # 通知所有玩家換誰進行活動
                    self.UpdatePlayerState('dice')
                case 'drawing':
                    self.StepAction = Step.PLAYER_DRAW
                    self.StepEvent.set()
                    # 通知所有玩家換誰進行活動
                    self.UpdatePlayerState('drawing')
                case 'discard':
                    # 通知所有玩家換誰進行活動
                    self.UpdatePlayerState('discard')
                    self.StepAction = Step.PLAYER_DISCARD
                    self.Msg.append(msg)
                    self.StepEvent.set()

                case 'pass':
                    self.StepAction = Step.PLAYER_PASS
                    self.StepEvent.set()
                    # 通知所有玩家換誰進行活動
                    self.UpdatePlayerState('pass')
                case 'hu':
                    self.StepAction = Step.PLAYER_HU
                    # self.Msg.append(msg)
                    self.StepEvent.set()
                    # 通知所有玩家換誰進行活動
                    self.UpdatePlayerState('hu')
                case 'kong':
                    self.StepAction = Step.PLAYER_KONG
                    self.Msg.append(msg)
                    self.StepEvent.set()
                    # 通知所有玩家換誰進行活動
                    self.UpdatePlayerState('kong')
                case 'pong':
                    self.StepAction = Step.PLAYER_PONG
                    self.Msg.append(msg)
                    self.StepEvent.set()
                    # 通知所有玩家換誰進行活動
                    self.UpdatePlayerState('pong')
                case 'chow':
                    self.StepAction = Step.PLAYER_CHOW
                    self.Msg.append(msg)
                    self.StepEvent.set()
                    # 通知所有玩家換誰進行活動
                    self.UpdatePlayerState('chow')

                case 'get_hand':
                    # for client reconnect to get hand tiles
                    for w in WIND:
                        if w.name.lower() == msg['player']:
                            hand = self.GetHandDict(w)
                            self.Notify(hand)
                            break

if __name__ == '__main__':
    hand1 = Tile.Alias2Tile(["東","東","東"])
    hand2 = Tile.Alias2Tile(["南","南","南"])
    hand3 = Tile.Alias2Tile(["西","西","西"])
    melds = []
    melds.append(Meld(False, hand1))
    melds.append(Meld(True, hand2))
    melds.append(Meld(False, hand3))
    meld, hide = Meld.List2StrList(melds)
    print(meld)
    print(hide)
    print(Tile.List2StrList(hand1))

    ctrl = Controller()
    # ctrl.StartGame({1:"小東", 2:"小南", 3:"小西", 4:"小北"})
    PrintLog('Finish')