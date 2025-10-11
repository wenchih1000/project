#
# define Taiwan Mahjong tile class
#

from Tile import *
from Deck import *
from Player import *
from Rule import *

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
    players = {
        WIND.EAST:Player('小東', WIND.EAST, deck), 
        WIND.SOUTH:Player('小南', WIND.SOUTH, deck), 
        WIND.WEST:Player('小西', WIND.WEST, deck), 
        WIND.NORTH:Player('小北', WIND.NORTH, deck)
    }

    for key,val in handTiles.items():
        players[key].SetHandTile(val)
        for i in val:
            PrintLog(i.toStr(), end=' ')
    PrintLog()

    # 所有玩家補花
    deck.ReplaceFlowers(players)

def DemoDealerDrawAndDiscard():
    deck = Deck()
    diceScore = random.randint(3,18)
    wind = WIND.EAST
    deck.BreakingWall(wind, diceScore)
    handTiles = {WIND.EAST:[], WIND.SOUTH:[], WIND.WEST:[], WIND.NORTH:[]}
    deck.DealTiles(handTiles)
    player = Player('小東', WIND.EAST, deck)
    # player.SetHandTile(handTiles[WIND.EAST])

    hand = Tile.Alias2Tile(["1萬","2萬","3萬","3索","3索","3索","5筒","6筒","7筒","東","東","東","南","南","南","南","中"])
    player.SetHandTile(hand)
    
    player.daemon = True
    player.start()
    # 莊家開門
    player.Actions = Action.DRAWING
    player.Notify()
    player.Wait()

    # time.sleep(1)
    # player.Hand
    rule = Rule()
    ret = rule.CanHu(player.Hand)
    PrintLog("胡:"+str(ret))

    ret = rule.CanKong(player.Hand)
    PrintLog("槓:"+str(ret))
    if ret:
        kong = rule.GetKongTile(player.Hand)
        # 模擬玩家選槓牌
        player.LastKong = kong[0]
        player.Actions = Action.KONG
        player.Notify()
        player.Wait()

        # 從死牆抓牌
        player.Actions = Action.DRAWING
        player.Notify()
        player.Wait()

    # 莊家出第一張牌
    # 摸擬玩家出牌(從UI)
    rand = random.randrange(0, len(player.Hand))
    tile = player.Hand[rand]

    player.LastDiscard = tile
    player.Actions = Action.DISCARD
    player.Notify()
    player.Wait()

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
    # for i in range(len(WIND), 0, -1):
    #     print(i%4+1, WIND(i%4+1))

    # DemoTiles()

    # DemoAlias2Tile()

    #
    # test deck
    #
    # DemoReplaceFlowersWhenStartGame()

    DemoDealerDrawAndDiscard()


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

        