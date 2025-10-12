from Tile import *
from Deck import *
from Player import *
from Rule import *

# 負責串聯所有邏輯：管理回合、處理動作優先級 (吃/碰/槓/胡)
# Game controller
class Controller:
    Players: dict[WIND, Player] = {}
    Deck: Deck = None
    CurrentWind: WIND = WIND.EAST # 當前回合的玩家
    DealerWind: WIND = WIND.EAST # 莊家風位
    RoundNum: int = 0 # 局數 (東南西北)
    GameNum: int = 0 # 第幾莊

    def __init__(self):
        self.Deck = Deck()
        self.Players = {
            WIND.EAST: Player('小東', WIND.EAST, self.Deck), 
            WIND.SOUTH: Player('小南', WIND.SOUTH, self.Deck), 
            WIND.WEST: Player('小西', WIND.WEST, self.Deck), 
            WIND.NORTH: Player('小北', WIND.NORTH, self.Deck)
        }
        for player in self.Players.values():
            player.daemon = True
            player.start()

    def ResetGame(self):
        # 回收所有牌
        all_tiles = []
        for player in self.Players.values():
            all_tiles.extend(player.ReturnAllTile())
        all_tiles.extend(self.Deck.Wall)
        all_tiles.extend(self.Deck.DeadWall)
        for discard_pile in self.Deck.Discard.values():
            all_tiles.extend(discard_pile)
        self.Deck.Tiles = all_tiles
        self.Deck.FlushTiles({}) # 清空所有牌堆

        # 重置玩家狀態
        for player in self.Players.values():
            player.Reset()

        # 重置牌堆
        self.Deck = Deck()
        self.CurrentWind = self.DealerWind # 回合從莊家開始

    def StartGame(self):
        # 1. 洗牌、切牌
        diceScore = random.randint(3,18)
        self.Deck.BreakingWall(self.DealerWind, diceScore)

        # 2. 發牌
        handTiles = {WIND.EAST:[], WIND.SOUTH:[], WIND.WEST:[], WIND.NORTH:[]}
        self.Deck.DealTiles(handTiles)
        for key,val in handTiles.items():
            self.Players[key].SetHandTile(val)


if __name__ == '__main__':
    pass