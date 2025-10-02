from dataclasses import dataclass, field
from typing import List, Tuple, Set, Dict

from collections import Counter

def is_hu(tiles: list[str]) -> bool:
    """
    主函式：判斷 17 張牌是否胡牌
    tiles: e.g., ['1m', '2m', '3m', ...]
    """
    if len(tiles) != 17:
        return False

    # 1. 前置檢查特殊牌型 (例如七對子)
    tile_counts = Counter(tiles)
    # if is_seven_pairs(tile_counts):
    #     return True

    # 2. 遍歷所有可能的眼睛
    for tile in tile_counts:
        if tile_counts[tile] >= 2:
            # 複製一份手牌來操作，避免影響原始資料
            remaining_tiles = tile_counts.copy()
            
            # 移除眼睛
            remaining_tiles[tile] -= 2
            if remaining_tiles[tile] == 0:
                del remaining_tiles[tile]

            # 3. 遞迴拆解剩下的 15 張牌
            if can_be_melds(remaining_tiles):
                return True # 只要有一種組合成功，就是胡牌

    return False

# 成為搭(順子或刻子)
def can_be_melds(hand: Counter) -> bool:
    """
    遞迴函式：判斷手牌是否能被拆解成 n 組順子或刻子
    """
    # Base Case: 手牌都拆完了，成功！
    if not hand:
        return True

    # 隨機取一張牌開始拆解
    first_tile = sorted(hand.keys())[0]

    # Recursive Step 1: 嘗試組刻子
    if hand[first_tile] >= 3:
        # 移除刻子
        hand[first_tile] -= 3
        if hand[first_tile] == 0:
            del hand[first_tile]
        
        if can_be_melds(hand.copy()): # 傳遞副本
            return True
        
        # 回溯 (Backtrack)
        hand[first_tile] += 3

    # Recursive Step 2: 嘗試組順子 (字牌無法組順子)
    if first_tile[1] not in 'z' and int(first_tile[0]) <= 7:
        suit = first_tile[1]
        rank = int(first_tile[0])
        
        c1 = f"{rank}{suit}"
        c2 = f"{rank+1}{suit}"
        c3 = f"{rank+2}{suit}"

        if c1 in hand and c2 in hand and c3 in hand:
            # 移除順子
            hand[c1] -= 1
            hand[c2] -= 1
            hand[c3] -= 1
            
            # 清理計數為 0 的牌
            hand = Counter({k: v for k, v in hand.items() if v > 0})

            if can_be_melds(hand.copy()): # 傳遞副本
                return True
            
            # 回溯 (Backtrack) - 這裡省略了加回的程式碼，但概念相同

    # 如果所有組合都失敗
    return False

# 註：is_seven_pairs 和牌的表示法 (e.g., '1m' for 一萬) 需要額外實作

# ret = is_hu(['1m', '2m', '3m', '4m', '5m', '6m', '7m', '8m', '9m', '1p', '2p', '3p', '4p', '5p', '6p', '7p', '7p'])
# print(ret)

# ret = is_hu(['3m', '3m', '3m', '4m', '5m', '6m', '7m', '7m', '7m', '1p', '1p', '3p', '4p', '5p', '6p', '7p', '8p'])
# print(ret)

# --- 牌面表示與輔助函式 (修正) ---

# 假設的牌面編碼：萬/m, 索/s, 筒/p, 字牌無花色尾碼 (E, S, W, N, C, F, P)
HONORS: Set[str] = set('ESWNCFP') # 字牌 (紅中/發財/白板/風牌)
DRAGONS: Set[str] = set('CFP')
WINDS: Set[str] = set('ESWN')
WIND_TO_NUM: Dict[str, int] = {'E': 0, 'S': 1, 'W': 2, 'N': 3}
FLOWER_WIND_MAP: Dict[str, int] = {f: i % 4 for i, f in enumerate("F1 F2 F3 F4 F5 F6 F7 F8".split())} 
# 假設花牌代碼為 F1, F2... 對應風位 (0=東, 1=南, 2=西, 3=北)

@dataclass
class GameContext:
    # is_exposed                     標誌是否吃碰過
    # 保持原樣，結構清晰
    is_dealer: bool = False          # 莊家
    is_self_draw: bool = False       # 自摸
    is_robbing_gong: bool = False    # 搶槓胡牌
    is_gong_kai: bool = False        # 槓上開花
    is_last_tile_draw: bool = False  # 海底自摸
    is_first_turn_win: bool = False  # 開局胡牌
    # 新增的聽牌型態旗標 (假設這些情況互斥，且只算最高的一種)
    is_single_wait: bool = False     # 獨聽/單吊 (1台)
    is_edge_wait: bool = False       # 邊張 (1台)
    is_center_wait: bool = False     # 中洞/崁張 (1台)
    # is_pair_wait: bool = False     # 兩面聽/對倒/複合聽 (通常不計台，是平胡的必要條件)
    player_wind: int = 0             # 玩家風台
    round_wind: int = 0              # 風局台
    dealer_streak: int = 0           # 連莊/連拉
    flower_tiles: List[str] = field(default_factory=list) # 花牌

@dataclass
class Partition:
    # 保持原樣
    pair: Tuple[str, str]                   # 1對
    pungs: List[Tuple[str, str, str]]       # 碰
    kongs: List[Tuple[str, str, str, str]]  # 槓
    chows: List[Tuple[str, str, str]]       # 吃
    concealed_pungs: int = 0                # 暗刻
    concealed_kongs: int = 0                # 暗槓
    # 增加一個屬性來標記哪些搭子是吃/碰/明槓來的 (exposed)
    exposed_melds: int = 0 # 明搭:假設這代表吃/碰/明槓的總組數 (Partition應負責計算)


def get_suit(tile: str) -> str:
    """ 取得牌的花色 (m, s, p) 或 'z' (字牌) """
    return tile[1] if len(tile) > 1 else 'z'

def get_rank(tile: str) -> str:
    """ 取得牌的等級/數字/字母 """
    return tile[0]

def is_honor(tile: str) -> bool:
    """ 判斷是否為字牌 (風牌或三元牌) """
    return tile in HONORS

def is_dragon(tile: str) -> bool:
    """ 判斷是否為三元牌 (中發白) """
    return get_rank(tile) in 'CFP'

def is_wind(tile: str) -> bool:
    """ 判斷是否為風牌 (東南西北) """
    return get_rank(tile) in 'ESWN'

# def is_plain_hand(hand, winning_tile, is_self_drawn, has_exposed_melds):
#     # 1. 檢查是否是「五搭一對」的基本胡牌型
#     if not is_valid_winning_hand(hand, winning_tile):
#         return False

#     # 2. 核心條件：所有搭子必須是順子
#     if any(meld.is_pung or meld.is_kong for meld in hand.melds):
#         return False

#     # 3. 檢查手牌中是否有字牌 (Wind/Dragon)
#     if hand.contains_honor_tiles():
#         return False

#     # 4. 檢查是否有花牌
#     if hand.contains_flower_tiles(): # 雖然花牌不影響手牌結構，但在台數計算時會破壞平胡
#         return False

#     # 5. 必須是門清 (沒有吃碰明槓)
#     if has_exposed_melds:
#         return False

#     # 6. 必須是胡別人的牌 (非自摸)
#     if is_self_drawn:
#         return False

#     # 7. 檢查聽牌型態是否為「雙頭聽」 (最難的判定，需解析聽牌邊張/中洞/單釣)
#     if hand.is_single_wait(): # 假設你有一個 is_single_wait 函式來檢查獨聽
#         return False

#     return True # 所有條件都滿足，才是平胡 (2 台)

def calculate_tai(partition: Partition, context: GameContext) -> Tuple[int, List[str]]:
    """
    計算台灣16張麻將的總台數。
    
    返回: (總台數, [台數名稱列表])
    """
    total_tai = 0
    patterns = []
    
    # 1. 數據預處理
    all_melds = partition.pungs + partition.kongs + partition.chows
    all_tiles = [tile for meld in all_melds for tile in meld] + list(partition.pair)
    pungs_kongs = partition.pungs + partition.kongs # 所有的刻子和槓子

    # 門清判斷：exposed_melds 應為 0 
    # 由於 Partition 結構沒有提供每個 meld 的 exposed 狀態，我們依賴 Partition.exposed_melds (假設已從外部計算好)
    is_menqing = partition.exposed_melds == 0 
    
    # 2. 字牌刻子計數
    honor_pungs_kongs = [meld for meld in pungs_kongs if is_honor(meld[0])]
    wind_pungs_count = sum(1 for meld in honor_pungs_kongs if meld[0] in WINDS)
    dragon_pungs_count = sum(1 for meld in honor_pungs_kongs if meld[0] in DRAGONS)
    
    # --- A. 極致牌型 (最高層級，可能需互斥或包含) ---
    
    # 天胡/地胡 (16台，最高優先)
    if context.is_first_turn_win:
        tai_name = "天胡" if context.is_dealer else "地胡"
        patterns.append(f"{tai_name} (16台)")
        return 16, patterns 

    # 大四喜 (16台)
    if wind_pungs_count == 4:
        patterns.append("大四喜 (16台)"); total_tai += 16

    # --- B. 花色/結構牌型 (次高層級，互相獨立或包含) ---
    
    is_all_honor = all(is_honor(t) for t in all_tiles)

    # 字一色 (8台)
    if is_all_honor and "大四喜" not in patterns:
        patterns.append("字一色 (8台)"); total_tai += 8
    
    # 大三元 (8台)
    if dragon_pungs_count == 3:
        patterns.append("大三元 (8台)"); total_tai += 8
    
    # 清一色 (8台) / 混一色 (4台)
    suit_tiles = [t for t in all_tiles if not is_honor(t)]
    num_suits = len({get_suit(t) for t in suit_tiles})
    
    if num_suits <= 1 and not is_all_honor:
        if not suit_tiles: # 避免牌組全為字牌但無字一色的情況
            pass
        elif not any(is_honor(t) for t in all_tiles):
            patterns.append("清一色 (8台)"); total_tai += 8
        elif any(is_honor(t) for t in all_tiles):
            patterns.append("混一色 (4台)"); total_tai += 4
            
    # 小四喜 (8台)
    is_wind_pair = is_wind(partition.pair[0])
    if wind_pungs_count == 3 and is_wind_pair and "大四喜" not in patterns:
        patterns.append("小四喜 (8台)"); total_tai += 8

    # 小三元 (4台)
    is_dragon_pair = is_dragon(partition.pair[0])
    if dragon_pungs_count == 2 and is_dragon_pair and "大三元" not in patterns:
        patterns.append("小三元 (4台)"); total_tai += 4

    # 碰碰胡 (4台) - 結構台
    if not partition.chows:
        patterns.append("碰碰胡 (4台)"); total_tai += 4


    # --- C. 暗刻/順子牌型 (最低層級，可疊加於花色台，互斥於同結構高台) ---
    
    # 五暗刻 (8台) / 四暗刻 (5台) / 三暗刻 (2台)
    concealed_count = partition.concealed_pungs + partition.concealed_kongs
    
    if concealed_count == 5:
        patterns.append("五暗刻 (8台)"); total_tai += 8
    elif concealed_count == 4:
        patterns.append("四暗刻 (5台)"); total_tai += 5 
    elif concealed_count == 3:
        patterns.append("三暗刻 (2台)"); total_tai += 2
    
    # 平胡 (2台) - 結構台，與刻子牌型互斥
    is_pure_chow = len(partition.chows) == 5 and not pungs_kongs
    is_valid_plain_hand = is_pure_chow and not is_honor(partition.pair[0])
    
    # 平胡必須無其他刻子結構台 (如三暗刻/碰碰胡) 且花色台數不宜過高
    if is_valid_plain_hand and not any(p in patterns for p in ["碰碰胡", "五暗刻", "四暗刻", "三暗刻"]):
        # 嚴格來說平胡與清一色/混一色可疊加，但各地規則不同，這裡假設可疊加
        patterns.append("平胡 (2台)"); total_tai += 2

    # --- D. 基礎與加成台數 (獨立加總) ---

    # 莊家與連莊
    if context.is_dealer:
        total_tai += 1
        patterns.append("莊家 (+1台)")
    
    # 門清與自摸 (門清一摸三)
    if is_menqing and context.is_self_draw:
        total_tai += 3
        patterns.append("門清一摸三 (3台)")
    elif is_menqing:
        total_tai += 1
        patterns.append("門清 (1台)")
    elif context.is_self_draw:
        total_tai += 1
        patterns.append("自摸 (1台)")

    # ** 新增：聽牌型態 (1 台)**
    # 這些台數通常是互斥的，且只計算最高的或其中一個。
    if context.is_single_wait:
        total_tai += 1; patterns.append("獨聽/單吊 (+1台)")
    elif context.is_edge_wait:
        total_tai += 1; patterns.append("邊張 (+1台)")
    elif context.is_center_wait:
        total_tai += 1; patterns.append("中洞/崁張 (+1台)")

    dragons_map = {'C': '中', 'F': '發', 'P': '白'}
    # 風牌與三元牌 (單獨計算，避免被大小四喜/三元完全覆蓋)
    for meld in honor_pungs_kongs:
        rank = get_rank(meld[0])
        
        # 三元牌 (中發白)
        if rank in DRAGONS and not any(p in patterns for p in ["大三元", "小三元"]):
            total_tai += 1
            patterns.append(f"{dragons_map[rank]} (+1台)")

        # 風牌 (圈風、門風)
        if rank in WINDS:
            wind_value = WIND_TO_NUM[rank]
            # 圈風牌
            if wind_value == context.round_wind and "大四喜" not in patterns:
                total_tai += 1
                patterns.append(f"圈風牌({rank}) (+1台)")
            # 門風牌
            if wind_value == context.player_wind and not any(p in patterns for p in ["大四喜", "小四喜"]):
                # 小四喜已涵蓋門風刻，故不重複計
                total_tai += 1
                patterns.append(f"門風牌({rank}) (+1台)")

    # 花牌與正花
    for flower in context.flower_tiles:
        total_tai += 1 # 每一張花牌算 1 台
        patterns.append(f"花牌 ({flower}) (+1台)")
        if FLOWER_WIND_MAP.get(flower, -1) == context.player_wind:
            total_tai += 1
            patterns.append(f"正花 (+1台)")

    # 額外事件台 (已在前面計算，這裡是為了保持邏輯完整性)
    if context.is_gong_kai: patterns.append("槓上開花 (+1台)")
    if context.is_last_tile_draw: patterns.append("海底撈月 (+1台)")
    if context.is_robbing_gong: patterns.append("搶槓 (+1台)")

    return total_tai, patterns

ALL_TILES: List[str] = [
    '1m', '2m', '3m', '4m', '5m', '6m', '7m', '8m', '9m', 
    '1s', '2s', '3s', '4s', '5s', '6s', '7s', '8s', '9s', 
    '1p', '2p', '3p', '4p', '5p', '6p', '7p', '8p', '9p', 
    'E', 'S', 'W', 'N', 'C', 'F', 'P'
]

def get_next_tile(tile: str) -> str:
    """ 取得數字牌的下一張 (例如 '3m' -> '4m') """
    if is_honor(tile):
        return ""
    suit = get_suit(tile)
    rank = int(get_rank(tile))
    return f"{rank + 1}{suit}" if rank < 9 else ""
# --- 遞歸核心：胡牌判斷 (Can Win) ---

def can_win(hand: Counter, pairs_found: int = 0) -> bool:
    """
    遞歸檢查一個牌組是否能分解成 N 組順子/刻子 (N=4, 14張牌時) 或 N-1 組 (13張牌時)。
    這個函數是麻將演算法的核心。
    """
    # 檢查是否已分解完成：牌堆已經空了 (count 都是 0)
    if not any(hand.values()):
        # 成功分解！
        return True

    # 找到牌堆中數量>0的第一張牌 (作為當前處理的起點)
    first_tile: str = ""
    for tile in ALL_TILES:
        if hand[tile] > 0:
            first_tile = tile
            break
    
    if not first_tile:
        return False # 應該在第一個檢查點就返回

    # 1. 嘗試以這張牌作為「眼」
    if pairs_found < 1 and hand[first_tile] >= 2:
        hand[first_tile] -= 2
        if can_win(hand, pairs_found + 1):
            return True
        hand[first_tile] += 2 # 回溯
        
    # 2. 嘗試以這張牌組成「刻子」
    if hand[first_tile] >= 3:
        hand[first_tile] -= 3
        if can_win(hand, pairs_found):
            return True
        hand[first_tile] += 3 # 回溯

    # 3. 嘗試以這張牌組成「順子」 (只對數字牌有效)
    if not is_honor(first_tile):
        tile2 = get_next_tile(first_tile)
        if tile2 == '':
            return False
        tile3 = get_next_tile(tile2)
        if tile3 == '':
            return False
        
        # 確保順子中的三張牌都存在
        if tile2 and hand[tile2] > 0 and tile3 and hand[tile3] > 0:
            hand[first_tile] -= 1
            hand[tile2] -= 1
            hand[tile3] -= 1
            if can_win(hand, pairs_found):
                return True
            hand[first_tile] += 1 # 回溯
            hand[tile2] += 1
            hand[tile3] += 1
            
    return False

# --- 聽牌演算法主函數 (Find All Waits) ---
# from collections import Counter
def find_all_waits(concealed_hand: List[str]) -> List[str]:
    """
    找出所有能讓當前手牌胡牌的牌 (聽牌列表)。
    
    concealed_hand: 玩家尚未公開的手牌 (通常是 16 張牌，但演算法只處理組成 4*3+2 的牌)
    
    返回: 聽牌列表 (e.g., ['2m', '5m', '8p'])
    """
    
    waits: List[str] = []
    
    # 計算基礎牌數 (台灣麻將 16 張，但胡牌分解是 4*3+2缺1張組成順或刻，即 14 張，省掉對牌)
    # 我們假設 concealed_hand 已經是準備胡牌的 16 張手牌，但分解時只需檢查 14 張的結構
    # 為了簡化，我們只檢查手牌數量是否滿足 16 張牌的結構 (4個搭子和1個眼)
    
    # 註：這裡假設傳入的 concealed_hand 是玩家的「手牌」，不含吃、碰、明槓的牌。
    # 實際計台時，需要將所有牌（包含吃、碰、槓）加起來，總共是 16 張。
    # 為符合 14 張牌的核心分解邏輯，我們假設傳入的手牌是 N=14 的牌型。
    
    # 步驟 1: 遍歷 34 種牌
    for trial_tile in ALL_TILES:
        # 步驟 2: 試著將這張牌加入手牌
        current_hand = Counter(concealed_hand)
        
        # 如果試聽的牌在手牌中已經有 4 張了 (無法再摸第 5 張)，則跳過
        if current_hand[trial_tile] == 4:
            continue
            
        current_hand[trial_tile] += 1

        # 步驟 3: 檢查加入試聽牌後，牌組總數是否滿足胡牌條件 (4組搭子+1眼 = 14張)
        if sum(current_hand.values()) % 3 == 2:
            # 步驟 4: 使用遞歸函數判斷是否胡牌
            if can_win(current_hand):
                waits.append(trial_tile)

    return waits

if __name__ == '__main__':

    #
    # 找出聽哪些牌
    #

    player = ['2m', '2m', '4m', '5m', '6m', '6m', '7m', '8m', '1p', '2p', '3p', '4p', '5p', '6p', 'F', 'F']
    ret = find_all_waits(player)
    print(ret)

    # #
    # # 胡牌
    # #

    # ret = is_hu(['1m', '2m', '3m', '4m', '5m', '6m', '7m', '8m', '9m', '1p', '2p', '3p', '4p', '5p', '6p', '7p', '7p'])
    # print(ret)

    # ret = is_hu(['3m', '3m', '3m', '4m', '5m', '6m', '7m', '7m', '7m', '1p', '1p', '3p', '4p', '5p', '6p', '7p', '8p'])
    # print(ret)

    # #
    # # 計算台數
    # #

    # # 範例1: 莊家連一，門清自摸，混一色碰碰胡帶門風
    
    # # 假設 is_hu 函式回傳了這個牌組結構
    # win_partition = Partition(
    #     pair=('9m', '9m'), # 東風對
    #     pungs=[],
    #     kongs=[
    #         ('1m', '1m', '1m', '1m'), ('2m', '2m', '2m', '2m'),
    #         ('3m', '3m', '3m', '3m'), ('5m', '5m', '5m', '5m') #('Wz', 'Wz', 'Wz', 'Wz')
    #     ],
    #     chows=[],
    #     concealed_pungs=0,
    #     concealed_kongs=4 # 假設四個暗槓
    # )

    # game_context = GameContext(
    #     is_dealer=True,
    #     is_self_draw=True,
    #     dealer_streak=2,
    #     player_wind=0, # 東風
    #     round_wind=0,  # 東風圈
    #     flower_tiles=['F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7', 'F8']
    # )

    # total, breakdown = calculate_tai(win_partition, game_context)
    
    # print(f"胡牌牌型: {', '.join(breakdown)}")
    # print(f"總台數: {total} 台")