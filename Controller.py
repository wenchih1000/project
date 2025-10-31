from Tile import *
from Deck import Deck
from Player import *
from Model import Rule16 as Rule
from Score import *

from pubsub import pub as Publisher

class Step(Enum):
    INIT = 0

    START_GAME = 1
    START_HAND = 2

    PLAYER_SEAT_NOTIFY = 5
    PLAYER_ROLL_DICE_NOTIFY = 6
    PLAYER_DRAW_NOTIFY = 7
    PLAYER_DISCARD_NOTIFY = 8

    PLAYER_ROLL_DICE = 9
    PLAYER_HU = 10
    PLAYER_KONG = 11
    PLAYER_PONG = 12
    PLAYER_CHOW = 13
    PLAYER_DRAW = 14
    PLAYER_DISCARD = 15
    PLAYER_PASS = 16

    DECIDE_WHOSE_TURN = 20
    WHOSE_NEXT_TURN = 21
    CHECK_ROBBING_GONG = 22

    CALCULATE_SCORE = 23
    CALCULATE_CASH = 24

    TIMEOUT = 30    # 超時
    DRAW_GAME = 31  # 流局
    END_HAND = 32   # 一局
    END_ROUND = 33  # 一圈
    END_GAME = 34   # 一雀

# 負責串聯所有邏輯：管理回合、處理動作優先級 (吃/碰/槓/胡)
# Game controller
class Controller:
    Condition = HandCondition()
    IsStart: bool = False
    Players: dict[WIND, Player] = {}
    DeckRef: Deck = None
    RoundWind: WIND = WIND.EAST # 局風位
    ActiveWind: WIND = WIND.EAST # 當前活動的玩家

    # 處理活動玩家出牌之後其他閒家過牌(碰/槓/胡)，
    # 在Next決定輸誰活動時以先前出牌的人為主
    OldWind: WIND = None
    CheckNext: bool = False

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
    DelayAction:Step = 0

    Msg:list = None
    StartTime:float = 0
    DelayTime:float = 0
    IsDrawGame:bool = False

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

    #
    # Protocol communication
    #

    def GetHandAndOutHandDict(self, wind:WIND, notify:WIND = None) -> dict:
        #
        # if notify=None, denote notify for 'all'
        #
        player = self.Players[wind]
        tiles = Tile.List2StrList(player.Hand)
        flower = Tile.List2StrList(player.Flowers)
        discard = Tile.List2StrList(self.DeckRef.Discard[player.Wind])
        meld, hide = Meld.List2StrList(player.Melds)
        target = 'all' if notify == None else notify.name.lower()
        wait = Tile.List2StrList(Rule.FindAllWaits(player.Hand))

        hand = {
            "notify":target,
            "hand_tiles":[{
                "hand":tiles,
                "drawed":'' if player.LastDraw == None else str(player.LastDraw),
                "wait":wait
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

        DrawedWin, DiscardWin, RobWin, DiscardSeat = '', '', '', ''
        # 自摸
        if player.LastDraw != None:
            DrawedWin = str(player.LastDraw)
        # 搶槓胡
        elif self.DeckRef.LastAddKong != None:
            RobWin = str(self.DeckRef.LastAddKong)
            DiscardSeat = self.DeckRef.LastWind.name.lower()
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
                # 搶槓胡
                "rob_win":RobWin,
                "meld":meld,
                "hide":hide,
                "flower":flower
            }]
        }
        return hand

    def GetHuName(self) -> str:
        player = self.Players[self.ActiveWind]

        # 放槍
        result = 'discard_win'
        # 搶槓胡
        if self.DeckRef.LastAddKong != None:
            result = 'rob_win'
        # 自摸
        elif player.LastDraw != None:
            result = 'draw_win'
        return result

    def UpdateGameState(self):
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

    def UpdateGameResult(self, state:str, result:str):
        state = {
            "game_result":{
                "state":state,
                "result":result
            }
        }
        self.Notify(state)

    def UpdateActionState(self, state:str):
        action = {
            "notify":self.ActiveWind.name.lower(),
            "action_state":state
        }
        self.Notify(action)

    def UpdatePlayerSeat(self):
        seat = {
            "player_seat":{"east":"","south":"","west":"","north":""}
        }
        for w, p in self.Players.items():
            seat["player_seat"][w.name.lower()] = p.Name
        self.Notify(seat)

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

    def UpdateScoreResult(self, result:list[ScoreName], score:int):
        player = self.Players[self.ActiveWind]
        hand = Tile.List2StrList(player.Hand)
        flower = Tile.List2StrList(player.Flowers)
        meld, hide = Meld.List2StrList(player.Melds)
        win = self.GetHuName()

        info = []
        for tai in result:
            info.append({"name":tai.Name, "value":tai.Score})

        state = {
            "score_result":{
                "player":self.ActiveWind.name.lower(),
                "hand":hand,
                "meld":meld,
                "hide":hide,
                "flower":flower,
                "round_wind":self.RoundWind.name.lower(),
                "dealer_wind":self.DealerWind.name.lower(),
                "win_type":win,
                "dealer_num":self.DealerNum,
                "score_list":info,
                "total_score":score,
                "before_money":[8000, 6000, 9000, 5000],
                "after_money":[1000, 6000, 9000, 12000]
            }
        }
        self.Notify(state)

    def UpdatePlayerHandState(self):
        # 通知閒家，當前玩家 暗槓/明槓,碰/吃 的牌
        for w in self.ActiveWind.Other():
            hand = self.GetOutHandDict(self.ActiveWind, notify=w, showhide=False)
            self.Notify(hand)

        # 通知當前玩家 手牌 和 外露牌 情況
        hand = self.GetHandAndOutHandDict(self.ActiveWind, self.ActiveWind)
        self.Notify(hand)

        # 因前一個玩家所丟出的牌被當前玩家 槓/碰/吃 走
        # 通知前一個玩家 外露牌 情況
        if self.DeckRef.LastWind != None:
            hand = self.GetOutHandDict(self.DeckRef.LastWind, notify=self.DeckRef.LastWind)
            self.Notify(hand)

            # 通知所有玩家，前一個玩家的牌被 槓/碰/吃 掉了
            for w in self.DeckRef.LastWind.Other():
                hand = self.GetOutHandDict(self.DeckRef.LastWind, notify=w, showhide=False)
                self.Notify(hand)

    #
    # Process Step Flow
    #

    def StepFlow(self):
        while not self.Exit:
            if self.StepEvent.is_set():
                self.StepEvent.clear()
                match self.StepAction:
                    case Step.INIT:
                        pass

                    # B. 開局自動流程
                    # B.1. 開始遊戲
                    case Step.START_GAME:
                        self.IsStart = True
                        self.RoundWind = WIND.EAST # 局風位
                        self.ActiveWind = WIND.EAST # 當前活動的玩家
                        self.DealerWind = WIND.EAST # 莊家風位

                        # 玩家風位
                        self.StepAction = Step.PLAYER_SEAT_NOTIFY
                        self.StepEvent.set()

                    # B.3. 通知玩家自已的風位
                    case Step.PLAYER_SEAT_NOTIFY:
                        # 通知玩家自已的風位
                        self.UpdatePlayerSeat()
                        self.StepAction = Step.PLAYER_ROLL_DICE_NOTIFY
                        self.StepEvent.set()

                    # B.4. 通知莊家擲骰子
                    case Step.PLAYER_ROLL_DICE_NOTIFY:
                        # 通知所有玩家換誰進行活動
                        self.UpdatePlayerState('dice')

                        self.ClearActionState(self.ActiveWind)
                        state = self.ActionState[self.ActiveWind]
                        state['dice'] = True
                        self.UpdateActionState(state)

                    # B.5~7. 開局5~7流程
                    case Step.START_HAND:
                        self.StartHand()
                        self.StepAction = Step.PLAYER_DRAW_NOTIFY
                        self.StepEvent.set()

                    # C. 牌局循環
                    # C.1. 通知玩家摸牌
                    case Step.PLAYER_DRAW_NOTIFY:
                        # 通知所有玩家換誰進行活動
                        self.UpdatePlayerState('drawing')

                        self.ClearActionState(self.ActiveWind)
                        state = self.ActionState[self.ActiveWind]
                        state['drawing'] = True
                        self.UpdateActionState(state)

                    # 進行碰/吃後，通知玩家出牌
                    case Step.PLAYER_DISCARD_NOTIFY:
                        # 通知所有玩家換誰進行活動
                        self.UpdatePlayerState('discard')

                        self.ClearActionState(self.ActiveWind)
                        state = self.ActionState[self.ActiveWind]
                        state['discard'] = True
                        self.UpdateActionState(state)

                    # C.2. 玩家出牌後，確認閒家(三人)手牌
                    case Step.DECIDE_WHOSE_TURN:
                        self.ActiveWind = self.DecideWhoseTurn(self.CheckNext)
                        self.CheckNext = False

                        # 通知所有玩家換誰進行活動
                        self.UpdatePlayerState()

                        # 通知玩家進行動作
                        player = self.Players[self.ActiveWind]
                        state = self.ActionState[self.ActiveWind]
                        # 玩家放棄胡牌，需等下一次打出牌後解除過水，才能再胡牌
                        if state['hu'] and player.PassHu:
                            state['hu'] = False
                        self.UpdateActionState(state)

                    case Step.CHECK_ROBBING_GONG:
                        self.ActiveWind = self.CheckRobbingGong(self.CheckNext)
                        self.CheckNext = False

                        # 通知所有玩家換誰進行活動
                        self.UpdatePlayerState()

                        # 通知玩家進行動作
                        player = self.Players[self.ActiveWind]
                        state = self.ActionState[self.ActiveWind]
                        # 玩家放棄胡牌，需等下一次打出牌後解除過水，才能再胡牌
                        if state['hu'] and player.PassHu:
                            state['hu'] = False
                        self.UpdateActionState(state)

                    #
                    # 玩家決定進行 roll dice/hu/kong/pong/chow/draw/discard/pass 動作
                    #

                    # D 0. 骰子流程
                    case Step.PLAYER_ROLL_DICE:
                        player = self.Players[self.DealerWind]
                        player.Actions = Action.DICE
                        player.Notify()
                        player.Wait()

                        self.UpdateGameState()
                        PrintLog("state:" + str(state))
                        self.DelayRunAction(3, Step.START_HAND)

                    # D 1.胡牌流程
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

                        # 通知所有玩家，此局結果
                        result = self.GetHuName()

                        self.UpdateGameResult('win_game', result)

                        # delay to show message
                        self.DelayRunAction(3, Step.CALCULATE_SCORE)

                    # D.2 槓牌流程
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
                        kong = None

                        # 暗槓
                        # 檢查手牌是否有4張一樣的牌
                        HideTiles = Rule.GetKongTile(player.Hand)
                        if len(HideTiles) > 0:
                            tile = Tile.Str2Tile(tiles[0])
                            if tile in HideTiles:
                                player.KongMode = KongType.HIDE_KONG
                                kong = tile

                        # 明槓
                        if Rule.CanKong(player.Hand, self.DeckRef.LastDiscard):
                            player.KongMode = KongType.EXPOSED_KONG
                            kong = self.DeckRef.LastDiscard

                        # 摸槓
                        elif Rule.CanKong(player.Hand, player.LastDraw):
                            player.KongMode = KongType.DRAW_KONG
                            kong = player.LastDraw

                        # 加槓
                        # 檢查是否加槓(外露塔有明碰)
                        elif Rule.CanAddKong(player.Melds, player.LastDraw):
                            player.KongMode = KongType.ADD_KONG
                            kong = player.LastDraw
                            self.DeckRef.LastAddKong = kong
                            self.DeckRef.LastWind = self.ActiveWind

                        # 加明槓
                        elif Rule.CanAddKongByHand(player.Melds, player.Hand):
                            tile = Tile.Str2Tile(tiles[0])
                            PongTile = Rule.GetPongTile(player.Melds)
                            if tile in PongTile:
                                player.KongMode = KongType.ADD_EXPOSED_KONG
                                kong = tile
                                self.DeckRef.LastAddKong = tile
                                self.DeckRef.LastWind = self.ActiveWind

                        player.LastKong = kong
                        player.Notify()
                        player.Wait()

                        # 通知閒家，當前玩家暗槓/明槓的牌
                        for w in self.ActiveWind.Other():
                            hand = self.GetOutHandDict(self.ActiveWind, notify=w, showhide=False)
                            self.Notify(hand)

                        # 通知所有玩家更新 手牌 和 外露牌 情況
                        self.UpdatePlayerHandState()

                        if player.KongMode == KongType.ADD_KONG or player.KongMode == KongType.ADD_EXPOSED_KONG:
                            self.OldWind = None
                            self.StepAction = Step.CHECK_ROBBING_GONG
                        else:
                            # 通知玩家從死牆摸一張牌(然後通知玩家打一張)
                            self.StepAction = Step.PLAYER_DRAW_NOTIFY
                        player.KongMode = None
                        player.LastKong = None
                        self.StepEvent.set()

                    # D.3 碰牌流程
                    case Step.PLAYER_PONG:
                        # {'player': 'east', 'action': 'pong', 'tiles': ['2S','2S']}
                        msg = self.Msg.pop()
                        tiles = msg['tiles']
                        player = self.Players[self.ActiveWind]
                        player.Actions = Action.PONG

                        if Rule.CanPong(player.Hand, self.DeckRef.LastDiscard):
                            player.LastPong = self.DeckRef.LastDiscard

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

                    # D.4 吃牌流程
                    case Step.PLAYER_CHOW:
                        # {'player': 'east', 'action': 'chow', 'tiles': ['1S','3S']}
                        msg = self.Msg.pop()
                        tiles = msg['tiles']
                        player = self.Players[self.ActiveWind]
                        player.Actions = Action.CHOW
                        # 吃上家的牌放 self.DeckRef.LastDiscard
                        desired = Pair(Tile.Str2Tile(tiles[0]), Tile.Str2Tile(tiles[1]))
                        pairs = Rule.GetChowTile(self.DeckRef.LastDiscard)
                        for pair in pairs:
                            if pair == desired:
                                player.LastChows.extend(pair.ToList())
                                break

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

                    # D.5. 摸牌流程
                    # 玩家決定進行摸牌動作
                    case Step.PLAYER_DRAW:
                        # C.3. 牌牆區已空
                        if self.DeckRef.IsWallEmpty():
                            # 通知所有玩家牌牆已空，流局結算
                            self.UpdateGameResult('draw_game', 'wall_empty')
                            self.DelayRunAction(5, Step.DRAW_GAME)
                            continue

                        player = self.Players[self.ActiveWind]
                        player.Actions = Action.DRAWING
                        player.Notify()
                        ret = player.Wait()

                        # # C.3. 牌牆區已空 或 死牆區16張已空
                        # if ret == Result.WALL_EMPTY or ret == Result.DEAD_WALL_EMPTY:
                        #     # 通知所有玩家牌牆已空，流局結算
                        #     result = ('dead_wall_empty','wall_empty')[ret == Result.WALL_EMPTY]
                        #     self.UpdateGameResult('draw_game', result)
                        #     # self.StepAction = Step.DRAW_GAME
                        #     self.DelayRunAction(5, Step.DRAW_GAME)
                        #     continue

                        hand = self.GetHandDict(self.ActiveWind)
                        # 通知玩家摸到的牌
                        self.Notify(hand)

                        # 檢查手牌狀態(滿17張,16張手牌+摸1張牌) 胡牌/槓牌/出牌
                        self.CheckHandState()
                        # 通知所有玩家換誰進行活動
                        self.UpdatePlayerState()

                        # 通知玩家進行動作
                        state = self.ActionState[self.ActiveWind]
                        self.UpdateActionState(state)

                    # D.6. 出牌流程
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
                        hand = self.GetHandAndOutHandDict(self.ActiveWind, self.ActiveWind)
                        self.Notify(hand)

                        self.OldWind = None
                        self.StepAction = Step.DECIDE_WHOSE_TURN
                        self.StepEvent.set()

                    # D.7. PASS流程
                    case Step.PLAYER_PASS:
                        state = self.ActionState[self.ActiveWind]
                        # 玩家放棄胡牌，需等下一次打出牌後解除過水，才能再胡牌
                        if state['hu']:
                            player = self.Players[self.ActiveWind]
                            player.PassHu = True

                        self.Pass[self.ActiveWind] = True
                        self.CheckNext = True

                        # in add kong state
                        if self.DeckRef.LastAddKong != None:
                            self.StepAction = Step.CHECK_ROBBING_GONG
                        else:
                            self.StepAction = Step.DECIDE_WHOSE_TURN
                        self.StepEvent.set()

                    case Step.TIMEOUT:
                        # 超時結算
                        self.StepAction = self.DelayAction
                        self.DelayAction  = 0
                        self.StepEvent.set()

                    # D 1.* 計算胡牌台數
                    case Step.CALCULATE_SCORE:
                        # * 結算金額
                        # * 通知玩家結果
                        self.CalculateScore()

                        # delay to show message
                        self.DelayRunAction(5, Step.END_HAND)

                    # D 1.* 結算金額
                    case Step.CALCULATE_CASH:
                        pass

                    # E. 流局結算
                    case Step.DRAW_GAME:
                        # 確認4位玩家是否有/無聽牌(16張)
                        # 將4位玩家手牌顯示出來並標示有/無聽牌(16張)
                        # 此局為臭莊，連莊次數+1

                        # 通知所有玩家，把所有牌都翻開
                        for w in len(WIND):
                            hand = self.GetHandAndOutHandDict(w)
                            self.Notify(hand)

                        self.IsDrawGame = True
                        # delay to show message
                        self.DelayRunAction(5, Step.END_HAND)

                    # 一局結束 (One Hand)
                    case Step.END_HAND:
                        self.EndHand()
                        action = self.NextHand()
                        if action == Step.END_ROUND or action == Step.END_GAME:
                            self.StepAction = action
                        else:
                            self.StepAction = Step.PLAYER_ROLL_DICE_NOTIFY
                        self.StepEvent.set()

                    # 一圈結束 (One Round)
                    case Step.END_ROUND:
                        self.StepAction = Step.PLAYER_ROLL_DICE_NOTIFY
                        self.StepEvent.set()

                    # F. 雀局結束
                    # 一雀結束 (One Game)
                    case Step.END_GAME:
                        # 通知 web app 中斷 client連線
                        # self.Exit = True
                        self.IsStart = False
                        self.Notify({'disconnect':True})
                        self.StepAction = Step.INIT
                        self.StepEvent.set()
                    case _:
                        pass
            else:
                time.sleep(0.1)
                if self.StepAction == Step.TIMEOUT and time.time() - self.StartTime > self.DelayTime:
                    self.StepEvent.set()
                    PrintLog('timeout')

    def CalculateScore(self):
        player = self.Players[self.ActiveWind]
        # 取出玩家胡的牌張
        HuTile = self.DeckRef.HuTile(player.LastDraw)
        # 搶槓胡
        if self.DeckRef.LastAddKong != None:
            self.Condition.IsRobbingKong = True
        # 自模
        elif player.LastDraw != None:
            self.Condition.IsSelfDraw = True
            # 因槓牌或摸花補牌後自摸胡牌
            if self.DeckRef.DrawByFlower or self.DeckRef.DrawByKong:
                self.Condition.IsKongOnFlower = True
            # 摸牌牆最後一張牌自摸胡牌
            if self.DeckRef.IsWallEmpty():
                self.Condition.IsLastTileDraw = True
        # 放槍
        else:
            # 胡別人打出的最後一張牌
            if self.DeckRef.IsWallEmpty():
                self.Condition.IsLastTileDiscard = True

        ActionLen, DiscardLen, MLen = 0, 0, 0
        for p in self.Players.values():
            MLen +=len(p.Melds)
        for t in self.DeckRef.Discard.values():
            DiscardLen += len(t)
        ActionLen = MLen + DiscardLen

        # 莊家起手第 17 張牌已胡牌
        if player.IsDealer and self.Condition.IsSelfDraw and ActionLen == 0 and self.DeckRef.LastDiscard == None:
            self.Condition.IsHeavenlyHand = True
        # 閒家起手第 17 張牌已胡牌且首輪內無任何人吃/碰/槓
        elif not player.IsDealer and self.Condition.IsSelfDraw and MLen == 0 and DiscardLen < len(WIND):
            self.Condition.IsEarthlyHand = True
        # 閒家胡莊家打出的第 1 張牌
        elif not player.IsDealer and not self.Condition.IsSelfDraw and ActionLen == 0 and self.DeckRef.LastDiscard != None:
            self.Condition.IsHumanlyHand = True

        # 取出玩家未明牌的Melds
        _, melds = Rule.CanHu(player.Hand+[HuTile])

        # 玩家胡牌所有的塔，包含眼塔 共5塔+1眼塔
        AllMelds = []
        AllMelds.extend(melds)
        AllMelds.extend(player.Melds)

        # 標誌是否吃碰明槓過
        for m in player.Melds:
            if m.Exposed:
                self.Condition.IsExposed = True
                break

        # 檢查是否獨聽
        WaitTiles = Rule.FindAllWaits(player.Hand)
        if len(WaitTiles) == 1:
            # 單吊
            self.Condition.IsSingleWait = True

            # 聽眼塔, ex:1 聽 1
            for m in melds:
                if m.Type == MELD.PAIR and m.Tiles[0] == HuTile:
                    self.Condition.IsPairWait = True
                    break

            # 聽邊張 or 聽中洞(崁張)
            if not self.Condition.IsPairWait and not HuTile.IsHonor():
                for m in melds:
                    # 數字牌, 且皆是順塔
                    if m.Type == MELD.CHOW and HuTile in m.Tiles:
                        # 聽邊張, ex: 1, 2 聽 3 or 8, 9 聽 7
                        if HuTile.Num == 3 or HuTile.Num == 7:
                            self.Condition.IsEdgeWait = True
                            break
                        # 聽中洞, ex:1, 3 聽 2
                        if m.Tiles[1] == HuTile:
                            self.Condition.IsCenterWait = True
                            break
        # 聽多洞
        else:
            # 聽兩面/對倒/複合聽
            # ex:4, 5 聽 3 或 6 or 眼對 22, 55, 聽 2 或 5
            self.Condition.IsMultiWait = True

        self.Condition.IsDealer = player.IsDealer
        self.Condition.DealerStreak = self.DealerNum
        self.Condition.SeatWind = player.Wind
        self.Condition.RoundWind = self.RoundWind
        self.Condition.SeatFlower = player.Wind

        classify = HandClassify(AllMelds, player.Flowers)
        score = TaiScore(classify, self.Condition)
        total, breakdown = score.Calculate()
        self.UpdateScoreResult(breakdown, total)

        PrintLog("胡牌牌型:")
        tmp = ""
        for tai in breakdown:
            tab = '\t\t' if len(tai.Name) <= 3 else '\t'
            tmp += f"\t{tai.Name}{tab}{tai.Score}台\n"
        PrintLog(tmp)
        PrintLog(f"總台數: {total} 台")

    def DelayRunAction(self, delay:int, action:Step):
        self.StepAction = Step.TIMEOUT
        self.DelayTime = delay
        self.DelayAction  = action
        self.StartTime = time.time()

    def ResetGame(self):
        # 回收所有牌
        hands = {}
        for wind, player in self.Players.items():
            hands[wind] = player.ReturnAllTile()
            player.Reset()

         # 清空所有牌堆
        self.DeckRef.FlushTiles(hands)
        self.DeckRef.Reset()
        self.Condition.Reset()

    def Seat(self, name:str) -> str:
        for w, p in self.Players.items():
            if p.Name == name:
                return w.name.lower()
        return ''

    # WebApp 通知 Controller
    # A. 遊戲準備階段
    # A.1. 等待加入遊戲人數
    # A.2. 滿4人自動進入牌桌
    def StartGame(self, names:dict[int,str]):
        # names:dict[int,str]
        # key:client id, value:name

        # 隨機抽風位
        # B.2. 幫玩家隨機抽風位(東、南、西、北)
        seat = [WIND.EAST, WIND.SOUTH, WIND.WEST, WIND.NORTH]
        random.shuffle(seat)
        i = iter(names.items())
        for w in seat:
            cid, names = next(i)
            self.Players[w].CId = cid
            self.Players[w].Name = names

        # START_GAME
        self.StepAction = Step.START_GAME
        self.StepEvent.set()

    def StartHand(self):
        # B.0. 洗牌
        self.DeckRef.Shuffle()

        # B.5. 根據骰子點數切牌牆
        # diceScore = random.randint(3,18)
        diceScore = sum(self.DeckRef.Dice)
        PrintLog("骰子:" + str(diceScore))
        self.DeckRef.BreakingWall(self.DealerWind, diceScore)

        # B.6. 玩家抓牌並完成補花
        handTiles = {WIND.EAST:[], WIND.SOUTH:[], WIND.WEST:[], WIND.NORTH:[]}
        self.DeckRef.DealTiles(handTiles)
        for key,val in handTiles.items():
            self.Players[key].SetHandTile(val)

        self.DeckRef.ReplaceFlowers(self.Players)

        # B.7. 通知玩家開局手牌/外露牌
        for player in self.Players.values():
            hand = self.GetHandDict(player.Wind)
            self.Notify(hand)

            # 外露牌
            hand = self.GetOutHandDict(player.Wind, player.Wind)
            self.Notify(hand)

            # 通知所有玩家外露牌
            hand = self.GetOutHandDict(player.Wind, showhide=False)
            self.Notify(hand)

    def NextHand(self) -> Step:
        player = self.Players[self.ActiveWind]

        # 臭莊
        if self.IsDrawGame:
            self.DealerNum += 1
            self.IsDrawGame = False
            return Step.END_HAND

        # count next the round wind and wind seat
        # D.1.* 若是莊家胡牌則連莊次數+1，否則連莊次數歸零
        action = Step.END_HAND
        # 玩家繼續當莊
        if player.IsDealer:
            self.DealerNum += 1
        # 莊家換人
        else:
            self.DealerNum = 0
            # END_GAME
            if self.RoundWind == WIND.NORTH and self.DealerWind == WIND.NORTH:
                self.RoundWind = self.RoundWind.Next()
                self.DealerWind = self.DealerWind.Next()
                action = Step.END_GAME
            # END_ROUND
            elif self.DealerWind == WIND.NORTH:
                self.RoundWind = self.RoundWind.Next()
                self.DealerWind = self.DealerWind.Next()
                action = Step.END_ROUND
            # END_HAND
            else:
                self.DealerWind = self.DealerWind.Next()
                action = Step.END_HAND

            # 換莊
            for w in WIND:
                if w == self.DealerWind:
                    self.Players[w].IsDealer = True
                else:
                    self.Players[w].IsDealer = False

        # 下局從莊家開始
        self.ActiveWind = self.DealerWind
        return action

    def EndHand(self):
        self.ResetGame()

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
        CanAddKongByHand = Rule.CanAddKongByHand(player.Melds, hand)

        self.ActionState[wind]['hu'] = CanHu
        self.ActionState[wind]['kong'] = (CanKong or CanAddKong or CanAddKongByHand or CanConcealKong)
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

    def CheckRobbingGong(self, next:bool = False) -> WIND:
        # 找出閒家
        if next:
            other = self.OldWind.Other()
        else:
            other = self.ActiveWind.Other()
            self.OldWind = self.ActiveWind

        # 判斷閒家對打出的牌具有哪些動作
        tile = self.DeckRef.LastAddKong
        if not next:
            self.ClearActionState()
            for w in other:
                hand = self.Players[w].Hand
                CanHu, melds = Rule.CanHu(hand + [tile])
                if CanHu:
                    self.ActionState[w]['hu'] = CanHu
                    self.ActionState[w]['pass'] = True

        # check priority
        for w in other:
            if not self.Pass[w] and self.ActionState[w]['hu']:
                return w

        # 解除加槓後被搶槓胡
        # 加槓後，摸一打一
        self.ActionState[self.OldWind]['drawing'] = True
        self.DeckRef.LastAddKong = None
        return self.OldWind

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
                    self.StepAction = Step.PLAYER_ROLL_DICE
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