#
# define Taiwan Mahjong tile class
#

from collections import Counter
from enum import Enum
import random

TILE_DEBUG = False
HIDE_LOG = False
def PrintLog(msg:str = ""):
    if not HIDE_LOG:
        print(msg)

# Mahjong SUIT
class SUIT(Enum):
    CHAR = 0    # 萬牌 Character (1~9)
    DOT = 1     # 筒牌 or Circle (1~9)
    STICK = 2   # 索牌 or Bamboo (1~9)
    HONOR = 3   # 字牌 (風牌:東南西北 + 三元牌:中發白:1~7)
    FLOWER = 4  # 花牌 (花牌:梅蘭竹菊 + 季節牌:春夏秋冬:1~8)
    INVISIBLE = 5 # 蓋牌

# 風牌
class WIND(Enum):
    # 風牌:東南西北
    EAST, SOUTH, WEST, NORTH = 1,2,3,4

    def Next(self) -> 'WIND':
        v = (self.value + 1) % len(WIND)
        v = (v,len(WIND))[v==0]
        return WIND(v)

    def Prev(self) -> 'WIND':
        v = (self.value - 1) % len(WIND)
        v = (v,len(WIND))[v==0]
        return WIND(v)

    # 下家
    def Right(self) -> 'WIND':
        return self.Next()

    # 上家
    def Left(self) -> 'WIND':
        return self.Prev()

    # 對家
    def Opposite(self) -> 'WIND':
        return self.Next().Next()

    # get other winds in order
    def Other(self) -> list['WIND']:
        other = []
        wind = self
        for _ in range(len(WIND)-1):
            wind = wind.Next()
            other.append(wind)
        return other

# 三元牌 or 箭牌
class ARROW(Enum):
    # 三元牌(or 箭牌):中發白
    RED, GREEN, WHITE = 5,6,7
# 字牌
class HONOR:#(WIND, ARROW):
    Num:int = 0
    def __init__(self, num:int = 0):
        super().__init__()
        # maping H1 to H7 to self name
        self.Num = num

    # W:Wind, A:Arrow
    # HonorMap = {'1H':'1W', '2H':'2W', '3H':'3W', '4H':'4W', '5H':'1A', '6H':'2A', '7H':'3A'}
    def __str__(self) -> str:
        if self.Num in WIND:
            return f'{self.Num}W'
        elif self.Num in ARROW:
            return f'{self.Num - 4}A'
        return ''

# 四君子牌
class GENTLEMEN(Enum):
    # 梅蘭竹菊
    PLUM, ORCHID, BAMBOO, CHRYSANTHEMUM = 1,2,3,4
class PERIOD(Enum):
    # 季節牌:春夏秋冬
    SPRING, SUMMER, AUTUMN, WINTER = 5,6,7,8
# 花牌
class FLOWER:#(GENTLEMEN, PERIOD):
    Num:int = 0
    def __init__(self, num:int = 0):
        super().__init__()
        # maping F1 to F8 to self name
        self.Num = num

    # FlowerMap = {'1F':'1G', '2F':'2G', '3F':'3G', '4F':'4G', '5F':'1P', '6F':'2P', '7F':'3P', '8F':'4P'}
    def __str__(self) -> str:
        if self.Num in GENTLEMEN:
            return f'{self.Num}G'
        elif self.Num in PERIOD:
            return f'{self.Num - 4}P'
        return ''

# 搭的組成
class MELD(Enum):
    PAIR = 0 #對
    CHOW = 1 #吃
    PONG = 2 #碰
    KONG = 3 #槓
    ADD_KONG = 4 #先碰後摸到第四張變槓

    PAIR_LEN = 2
    CHOW_LEN = 3
    PONG_LEN = 3
    KONG_LEN = 4

# for console display
class TileAlias:
    DigiList:tuple = ('1', '2', '3', '4', '5', '6', '7', '8', '9')
    NumList:tuple = ('一', '二', '三', '四', '五', '六', '七', '八', '九')
    CharList:tuple = ('萬', '筒', '條')
    CharList2:tuple = ('萬', '餅', '索')
    HonorList:tuple = ('東', '南', '西', '北', '中', '發', '白')
    HonorList2:tuple = ('東風', '南風', '西風', '北風', '紅中', '青發', '白板')
    FlowerList:tuple = ('梅', '蘭', '竹', '菊', '春', '夏', '秋', '冬')
    InvisibleList:tuple = ('蓋',)

class TileRange(Enum):
    CharMin,CharMax = 1, 9
    DotMin, DotMax = 1, 9
    StickMin, StickMax = 1, 9
    HonorMin, HonorMax = 1, 7
    FlowerMin, FlowerMax = 1, 8

# 定義麻將牌
class Tile(object):
    __Suit:SUIT = None
    __Num:int = 0
    NumMin, NumMax = 1, 9

    # for operation
    __Name:str = ''
    __SubName:str = ''

    # for console display
    __Alias:str = ''

    @property
    def Suit(self) -> SUIT:
        return self.__Suit
    @property
    def Num(self) -> int:
        return self.__Num
    @property
    def Name(self) -> str:
        return self.__Name
    @property
    def SubName(self) -> str:
        return self.__SubName
    @property
    def Alias(self) -> str:
        return self.__Alias
    @property
    def HideName(self) -> str:
        return f'{1}X'

    def __init__(self, args:dict):
        # {'suit':SUIT.CHAR, 'num':1}
        # {'alias':'1萬'} or {'alias':'一萬'}

        num = 0
        suit = None
        if 'alias' in args:
            suit, num = Tile.parse(args['alias'])
        elif 'suit' in args and 'num' in args:
            suit = args['suit']
            num = args['num']
        else:
            return

        # ex: Name = 1C, dentes '1萬'
        self.__Suit = suit
        self.__Num = Tile.NumVerify(self.Suit, num)
        self.__Name = f'{self.Num}{self.Suit.name[0]}'

        # list index start from 0
        NumOffset = self.Num - 1
        if self.Suit == SUIT.HONOR:
            self.__Alias = TileAlias.HonorList[NumOffset]
            self.__SubName = str(HONOR(self.Num))
        elif self.Suit == SUIT.FLOWER:
            self.__Alias = TileAlias.FlowerList[NumOffset]
            self.__SubName = str(FLOWER(self.Num))
        elif self.Suit == SUIT.INVISIBLE:
            self.__Alias = TileAlias.InvisibleList[NumOffset]
            self.__Name = f'{self.Num}X'
        else:
            self.__Alias = TileAlias.NumList[NumOffset] + TileAlias.CharList[self.Suit.value]

    def __int__(self) -> int:
        return self.Num

    def __str__(self) -> str:
        if TILE_DEBUG:
            return self.Alias
        if self.Suit == SUIT.HONOR or self.Suit == SUIT.FLOWER:
            return self.SubName
        else:
            return self.Name

    def __add__(self, num:int) -> 'Tile':
        val = self.Num + num
        if val > self.NumMax:
            val = self.NumMax

        return Tile({'suit':self.Suit, 'num':val})

    def __sub__(self, num:int) -> 'Tile':
        val = self.Num - num
        if val < self.NumMin:
            val = self.NumMin

        return Tile({'suit':self.Suit, 'num':val})

    # for sorting
    def __lt__(self, other:'Tile') -> bool:
        if self.Suit == other.Suit:
            return self.Num < other.Num
        else:
            return self.Suit.value < other.Suit.value

    def __eq__(self, other:'Tile') -> bool:
        if isinstance(other, Tile):
            return self.Suit == other.Suit and self.Num == other.Num
        else:
            return False

    # for Counter to hash match
    def __hash__(self):
        return hash((self.Suit, self.Num))

    # for console display
    def toStr(self) -> str:
        return self.Alias

    # 判斷是否為花牌 (梅/蘭/竹/菊,春/夏/秋/冬)
    def IsFlower(self) -> bool:
        return self.Suit == SUIT.FLOWER

    # 判斷是否為字牌 (風牌/三元牌)
    def IsHonor(self) -> bool:
        return self.Suit == SUIT.HONOR

    # 判斷是否為風牌 (東/南/西/北)
    def IsWind(self) -> bool:
        if self.Suit != SUIT.HONOR:
            return False
        return self.Num in WIND

    # 判斷是否為三元牌 (中/發/白)
    def IsArrow(self) -> bool:
        if self.Suit != SUIT.HONOR:
            return False
        return self.Num in ARROW

    @staticmethod
    def parse(alias:str) -> tuple:
        # '1萬' or '一萬' or 東
        num = 0
        Suit = None

        # CHAR or DOT or STICK
        if len(alias) == 2:
            if alias[0] in TileAlias.DigiList:
                num = int(alias[0])
            elif alias[0] in TileAlias.NumList:
                num = TileAlias.NumList.index(alias[0]) + 1
            if alias[1] in TileAlias.CharList:
                i = TileAlias.CharList.index(alias[1])
                Suit = SUIT(i)
        # HONOR or FLOWER
        elif len(alias) == 1:
            if alias in str(TileAlias.HonorList):
                num = next(i for i, tile in enumerate(TileAlias.HonorList) if alias in tile) + 1
                Suit = SUIT.HONOR
            elif alias in TileAlias.FlowerList:
                num = TileAlias.FlowerList.index(alias) + 1
                Suit = SUIT.FLOWER

        return (Suit, num)

    @staticmethod
    def NumVerify(Suit:SUIT, num:int) -> int:
        if Suit == SUIT.HONOR:
            if num < TileRange.HonorMin.value:
                num = TileRange.HonorMin.value
            elif num > TileRange.HonorMax.value:
                num = TileRange.HonorMax.value
        elif Suit == SUIT.FLOWER:
            if num < TileRange.FlowerMin.value:
                num = TileRange.FlowerMin.value
            elif num > TileRange.FlowerMax.value:
                num = TileRange.FlowerMax.value
        else:
            if num < TileRange.CharMin.value:
                num = TileRange.CharMin.value
            elif num > TileRange.CharMax.value:
                num = TileRange.CharMax.value
        return num

    @staticmethod
    def Alias2Tile(alias:list[str]) -> list['Tile']:
        tiles = []
        for a in alias:
            tiles.append(Tile({'alias':a}))
        return tiles

    @staticmethod
    def List2StrList(tiles:list['Tile'], show:bool = True) -> list[str]:
        data = []
        for t in tiles:
            if show:
                data.append(str(t))
            else:
                data.append(t.HideName)
        return data

    @staticmethod
    def StrList2Tiles(tiles:list[str]) -> list['Tile']:
        data = []
        for t in tiles:
            data.append(Tile.Str2Tile(t))
        return data

    @staticmethod
    def NameList2Tiles(tiles:list[str]) -> list['Tile']:
        data = []
        for t in tiles:
            data.append(Tile.Name2Tile(t))
        return data

    @staticmethod
    def Str2Tile(name:str) -> 'Tile':
        if TILE_DEBUG:
            return Tile({'alias':name})
        # ex: 3S -> Tile
        num = int(name[0])
        sign = name[1]
        suit = None

        match sign:
            case 'G':
                sign = 'F'
            case 'P':
                sign = 'F'
                num += len(GENTLEMEN)
            case 'W':
                sign = 'H'
            case 'A':
                sign = 'H'
                num += len(WIND)
            case 'X':
                sign = 'I'

        for s in SUIT:
            if s.name[0] == sign:
                suit = s
                break

        return Tile({'suit':suit, 'num':num})

    @staticmethod
    def Name2Tile(name:str) -> 'Tile':
        # ex: 3S -> Tile
        num = int(name[0])
        sign = name[1]
        suit = None
        if sign == 'X':
            sign = 'I'

        for s in SUIT:
            if s.name[0] == sign:
                suit = s
                break

        return Tile({'suit':suit, 'num':num})

# 定義搭(Meld), 用來形成 對子/順子/刻子/槓子
# 並標註此搭為明搭或暗搭
class Meld:
    Type: MELD = None
    Exposed: bool = False
    Tiles: list[Tile] = None

    def __init__(self, exposed: bool, tiles: list[Tile]):
        self.Exposed = exposed
        self.Tiles = tiles
        if len(tiles) == MELD.PAIR_LEN.value:
            self.Type = MELD.PAIR
        elif len(tiles) == MELD.CHOW_LEN.value or len(tiles) == MELD.PONG_LEN.value:
            count = Counter(tiles)
            self.Type = MELD.CHOW if len(count) == 3 else MELD.PONG
        elif len(tiles) == MELD.KONG_LEN.value:
            self.Type = MELD.KONG

    @staticmethod
    def List2StrList(melds:list['Meld'], show:bool = True) -> tuple[list[str],list[str]]:
        meld, hide = [], []
        for m in melds:
            if m.Exposed:
                meld.append(Tile.List2StrList(m.Tiles))
            else:
                if show:
                    tmp = Tile.List2StrList(m.Tiles, False)
                    tmp[0] = str(m.Tiles[0])
                    # 3S,1X,1X,1X
                    meld.append(tmp)
                else:
                    # 1X,1X,1X,1X
                    hide.append(Tile.List2StrList(m.Tiles, show))

        return (meld, hide)

class Pair:
    Tile1: Tile = None
    Tile2: Tile = None

    def __init__(self, tile1: Tile, tile2: Tile):
        self.Tile1 = tile1
        self.Tile2 = tile2

    def ToList(self) -> list[Tile]:
        return [self.Tile1, self.Tile2]

    def __eq__(self, other:'Pair') -> bool:
        if isinstance(other, Pair):
            return (self.Tile1 == other.Tile1 and self.Tile2 == other.Tile2) or (self.Tile1 == other.Tile2 and self.Tile2 == other.Tile1)
        else:
            return False

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
        msg = ""
        for t in p:
            msg += t.toStr() + " "
        PrintLog(msg)

def DemoAlias2Tile():
    #
    #  Alias text to tile
    #

    # tmp = ["1萬","3索","5筒","中","發","白","梅","春","竹","冬"] 
    # tmp = ["東","南","西","北","中","發","白","梅","蘭","竹","菊","春","夏","秋","冬"]
    # for i in tmp:
    #     t = Tile({'alias':i})
    #     # PrintLog(t, end=' ')
    #     PrintLog(f"{t}, {t.toStr()}, {t.IsFlower()}, {t.IsHonor()}")

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
    
    tmp2 = []
    tmp3 = []
    for t in tmp:
        # print(t, end=',')
        tmp2.append(Tile.Str2Tile(str(t)))
        tmp3.append(Tile.Name2Tile(t.Name))
    tmp.sort()
    for t in tmp:
        print(t.Name, end=',')
    print()
    for t in tmp2:
        print(t, end=',')
    print()
    for t in tmp3:
        print(t, end=',')

        # PrintLog(f"{t}, {t.toStr()}, {t.IsFlower()}, {t.IsHonor()}")

if __name__ == '__main__':
    # wind = WIND.SOUTH
    # print(wind.Next())

    # winds = wind.Other()
    # print(winds)

    # t1 = Tile({'suit':SUIT.CHAR, 'num':7})
    # t2 = Tile({'suit':SUIT.CHAR, 'num':7})
    # print(t1 == t2)
    # print(t1)
    # print(t1+1)
    # print(t1+2)


    # DemoTiles()
    DemoAlias2Tile()