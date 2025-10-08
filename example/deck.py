import random
from typing import List, Dict
from collections import Counter
from typing import List, Dict, Tuple, Set
from calc import *

# --- 1. 牌的定義與初始化 ---
def initialize_all_tiles() -> List[str]:
    """
    初始化一整副 144 張台灣麻將牌（含花牌）。
    """
    tiles = []
    
    # 數牌 (Suits: 萬, 筒, 索) - 各 36 張 (1-9 * 4)
    # 'm' (萬/Characters), 'p' (筒/Dots), 's' (索/Bamboos)
    for suit in ['m', 'p', 's']:
        for i in range(1, 10):
            tiles.extend([f'{i}{suit}'] * 4)  # 每個數牌有 4 張

    # 字牌 (Honors: 風, 三元牌) - 各 4 張 (7 種 * 4)
    # 東南西北 (Winds): 'E', 'S', 'W', 'N'
    # 中發白 (Dragons): 'R' (Red), 'G' (Green), 'Wb' (White)
    # for honor in ['E', 'S', 'W', 'N', 'R', 'G', 'Wb']:
    for honor in ['We', 'Ws', 'Ww', 'Wn', 'R', 'G', 'Wb']:
        tiles.extend([honor] * 4)

    # 花牌 (Flowers/Seasons) - 各 1 張 (8 種)
    # 花: 梅蘭竹菊 (Plum, Orchid, Bamboo, Chrysanthemum) - 'F1', 'F2', 'F3', 'F4'
    # 季: 春夏秋冬 (Spring, Summer, Autumn, Winter) - 'S1', 'S2', 'S3', 'S4'
    for i in range(1, 5):
        tiles.append(f'F{i}')
        tiles.append(f'S{i}')
        
    # 總數檢查：108 + 28 + 8 = 144
    if len(tiles) != 144:
        raise ValueError(f"牌數錯誤：應為 144 張，實際為 {len(tiles)}")
        
    return tiles

# --- 2. 牌組 (Deck) 類別 ---
class MahjongDeck:
    """管理麻將牌堆的洗牌、切牌和摸牌操作。"""
    
    def __init__(self):
        self.all_tiles = initialize_all_tiles()
        self.wall: List[str] = [] # 牌牆（未被摸走的牌）
        self.dead_wall: List[str] = [] # 牌尾（死牌區，用於補牌）
        self.initialize_wall()

    def initialize_wall(self):
        """將所有牌洗亂並建立牌牆。"""
        # 1. 洗牌 (Shuffle)
        random.shuffle(self.all_tiles)
        
        # 2. 台灣麻將通常會保留牌尾 16 張（8 墩）作為死牌區
        DEAD_WALL_SIZE = 16 
        
        self.wall = self.all_tiles[:-DEAD_WALL_SIZE]
        self.dead_wall = self.all_tiles[-DEAD_WALL_SIZE:]
        print(f"牌牆初始化完成。牌牆張數: {len(self.wall)}, 死牌區張數: {len(self.dead_wall)}")

    def draw_tile(self, from_end: bool = False) -> str:
        """從牌牆摸牌 (from_end=True 表示從嶺上牌區補牌)。"""
        if from_end:
            if not self.dead_wall:
                # 牌牆已空，無法補牌
                raise IndexError("死牌區已空，無法執行槓上補牌！")
            return self.wall.pop(0) # 從牌尾取牌
        else:
            if not self.wall:
                # 牌牆已空，流局判斷
                raise IndexError("可摸牌區已空，牌局應流局！")
            return self.wall.pop(0) # 從牌頭摸牌
            
    def check_can_gang(self) -> bool:
        """檢查是否還有嶺上牌可補。"""
        return len(self.dead_wall) > 0

    def draw_replacement_tile(self) -> str:
        """從牌尾（死牌區）補一張牌 (Draw from the dead wall)。"""
        if not self.dead_wall:
            raise IndexError("死牌區已空，無法補牌。")
        # 槓牌補牌通常是從牌尾取牌，所以我們從 dead_wall 的最右邊 pop()
        return self.dead_wall.pop()

# --- 3. 發牌邏輯 ---

def deal_taiwan_mahjong(deck: MahjongDeck, num_players: int = 4) -> Dict[int, List[str]]:
    """
    執行台灣麻將的發牌程序。
    
    Args:
        deck: 已洗好的牌堆。
        num_players: 玩家人數（台灣麻將固定為 4）。
        
    Returns:
        一個字典，鍵為玩家編號 (0=莊家, 1, 2, 3)，值為該玩家的起始手牌。
    """
    if num_players != 4:
        raise ValueError("台灣麻將需要 4 位玩家。")
        
    hands: Dict[int, List[str]] = {i: [] for i in range(num_players)}
    
    # 1. 執行配牌 (Dealing 16 tiles to each player)
    # 依序每次發 4 張，共發 4 輪 (4 * 4 = 16 張)
    for _ in range(4):
        for player_id in range(num_players): # 逆時針順序發牌 (莊家開始)
            # 一次摸兩墩 (四張牌)
            hands[player_id].extend(deck.wall.pop(0) for _ in range(4))
            
    # 2. 莊家開門 (Dealer gets the 17th tile)
    # 莊家 (Player 0) 多拿一張牌作為開門牌
    hands[0].append(deck.wall.pop(0))
    
    # 3. 檢查牌數
    for player_id, hand in hands.items():
        expected_count = 17 if player_id == 0 else 16
        if len(hand) != expected_count:
            raise RuntimeError(f"發牌錯誤，玩家 {player_id} 牌數為 {len(hand)}，應為 {expected_count}")
    
    return hands

### 4. 執行與測試

# ```python
# # 創建牌堆
# game_deck = MahjongDeck()

# # 發牌
# player_hands = deal_taiwan_mahjong(game_deck)

# # 整理手牌 (排序，以便查看和補花)
# for player_id, hand in player_hands.items():
#     hand.sort() # 簡單排序，實際遊戲中通常會按花色排序
    
#     is_dealer = "莊家" if player_id == 0 else "閒家"
#     print(f"\n--- 玩家 {player_id} ({is_dealer}) 的起手牌 ({len(hand)} 張) ---")
#     print(hand)
    
# # 驗證牌牆剩餘張數
# remaining_wall = len(game_deck.wall)
# remaining_dead_wall = len(game_deck.dead_wall)
# total_dealt = 17 + 16 * 3
# total_remaining = remaining_wall + remaining_dead_wall

# print(f"\n--- 牌堆狀態檢查 ---")
# print(f"總共發出牌數: {total_dealt} 張")
# print(f"牌牆剩餘張數: {remaining_wall} 張")
# print(f"死牌區剩餘張數: {remaining_dead_wall} 張")
# print(f"發牌後的牌堆總張數: {total_remaining} 張 (144 - {total_dealt})")

# ----------------------------------------------------------------------
# 輔助函式：判斷牌型
# ----------------------------------------------------------------------
def is_flower_tile(tile: str) -> bool:
    """判斷一張牌是否為花牌 (F1-F4, S1-S4)。"""
    return tile.startswith('F') or tile.startswith('S')

def is_simple_tile(tile: str) -> bool:
    """判斷是否為 1-9 的萬、筒、索牌"""
    return len(tile) == 2 and tile[0].isdigit() and tile[1] in 'mps'

def get_next_tile(tile: str) -> str:
    """取得順子的下一張牌"""
    if is_simple_tile(tile):
        num = int(tile[0])
        suit = tile[1]
        if num < 9: return str(num + 1) + suit
    return None

def get_prev_tile(tile: str) -> str:
    """取得順子的前一張牌"""
    if is_simple_tile(tile):
        num = int(tile[0])
        suit = tile[1]
        if num > 1: return str(num - 1) + suit
    return None

# 吃、碰、槓 檢查邏輯
def check_pong(hand_counts: Counter, discarded_tile: str) -> bool:
    """檢查是否能碰牌 (手牌中有 2 張一樣的)。"""
    return hand_counts[discarded_tile] >= 2

def check_exposed_gang(hand_counts: Counter, discarded_tile: str) -> bool:
    """檢查是否能明槓 (手牌中有 3 張一樣的)。"""
    return hand_counts[discarded_tile] == 3

def check_chow(hand_counts: Counter, discarded_tile: str) -> List[Tuple[str, str]]:
    """
    檢查是否能吃牌，並返回所有可能的「兩張手牌」組合。
    
    Args:
        hand_counts: 玩家手牌的計數。
        discarded_tile: 被打出的牌。
        
    Returns:
        List[Tuple[str, str]]: 兩張手牌，與棄牌組合成順子。
    """
    if not is_simple_tile(discarded_tile): return []

    possible_chows = []
    
    # 1. 檢查 '中洞'：需要 (X-1) 和 (X+1)
    prev = get_prev_tile(discarded_tile)
    next_t = get_next_tile(discarded_tile)
    if prev and next_t and hand_counts[prev] >= 1 and hand_counts[next_t] >= 1:
        possible_chows.append((prev, next_t))
        
    # 2. 檢查 '上家'：需要 (X+1) 和 (X+2)
    t1 = get_next_tile(discarded_tile)
    t2 = t1 and get_next_tile(t1)
    if t1 and t2 and hand_counts[t1] >= 1 and hand_counts[t2] >= 1:
        possible_chows.append((t1, t2))

    # 3. 檢查 '下家'：需要 (X-2) 和 (X-1)
    t1 = get_prev_tile(discarded_tile)
    t2 = t1 and get_prev_tile(t1)
    if t1 and t2 and hand_counts[t2] >= 1 and hand_counts[t1] >= 1:
        possible_chows.append((t2, t1))
        
    return possible_chows

# ----------------------------------------------------------------------
# Player 類別：管理手牌與公開牌
# ----------------------------------------------------------------------
class Player:
    pass_status = {'HU':False, 'KONG':False, 'CHOW':False, 'PONG':False, 'GANG':False}

    def __init__(self, player_id: int, hand: List[str]):
        self.player_id = player_id
        self.hand = hand  # 玩家手牌 (16 或 17 張)
        self.exposed_flowers: List[str] = [] # 已亮出的花牌
        self.melds = []       # 已完成的搭子 (碰/槓/吃)

    def check_for_flowers(self) -> List[str]:
        """
        檢查並從手牌中取出所有花牌。
        
        Returns:
            這一輪從手牌中取出的花牌列表。
        """
        new_flowers = [tile for tile in self.hand if is_flower_tile(tile)]
        
        # 從手牌中移除花牌
        self.hand = [tile for tile in self.hand if not is_flower_tile(tile)]
        
        if new_flowers:
            self.exposed_flowers.extend(new_flowers)
            print(f"玩家 {self.player_id} 摸到 {len(new_flowers)} 張花牌：{new_flowers}")
            
        return new_flowers

    def get_hand_counts(self) -> Counter:
        return Counter(self.hand)

    def add_meld(self, meld: List[str], meld_type: str, is_concealed: bool = False):
        self.melds.append({'tiles': meld, 'type': meld_type, 'concealed': is_concealed})

    def get_num_exposed_melds(self) -> int:
        """計算玩家外露搭子（碰、吃、明槓）的總數。"""
        # 暗槓不算外露搭子
        return sum(1 for meld in self.melds if not meld.get('concealed', False))

    def remove_tiles(self, tiles: List[str]):
        for tile in tiles:
            try: self.hand.remove(tile)
            except ValueError: pass

    def clear_pass_status(self):
        for key in self.pass_status.keys():
            self.pass_status[key] = False

# ----------------------------------------------------------------------
# MahjongDeck 類別 (沿用，確保有 draw_replacement_tile 方法)
# ----------------------------------------------------------------------
# ... (這裡省略 MahjongDeck 類別的定義，假設它已包含 initialize_wall 和 draw_replacement_tile)
# 確保 draw_replacement_tile 是從 dead_wall 取牌
# ...


def replace_flowers(players: Dict[int, Player], deck: MahjongDeck):
    """
    執行完整的補花程序，直到所有玩家手牌中不再有花牌。
    
    Args:
        players: 包含所有 Player 物件的字典。
        deck: 遊戲牌堆，用於提供補牌。
    """
    num_players = len(players)
    # 莊家 (Player 0) 開始，逆時針 (0 -> 1 -> 2 -> 3)
    player_order = range(num_players) 
    
    print("\n--- 開始補花程序 ---")
    
    # 使用迴圈迭代，直到所有玩家的本輪補花都結束且沒有新花牌
    while True:
        # 標記本輪是否有玩家補到了新的花牌
        new_flower_drawn_in_round = False
        
        for player_id in player_order:
            player = players[player_id]
            
            # 1. 檢查並從手牌中移除花牌 (第一次或補牌後)
            flowers_to_replace = player.check_for_flowers()
            
            # 2. 執行補牌
            num_to_draw = len(flowers_to_replace)
            
            if num_to_draw > 0:
                print(f"玩家 {player_id} 需要補 {num_to_draw} 張牌。")
                
                for i in range(num_to_draw):
                    try:
                        new_tile = deck.draw_replacement_tile()
                        player.hand.append(new_tile)
                        
                        # 檢查補到的牌是否又是花牌
                        if is_flower_tile(new_tile):
                            new_flower_drawn_in_round = True
                            print(f"   --> 補到新花牌：{new_tile} (將於下輪處理)")
                        else:
                            print(f"   --> 補到牌：{new_tile}")
                            
                    except IndexError:
                        print("!!! 錯誤：死牌區已空，無法補牌。遊戲將流局。")
                        return

        # 如果本輪沒有任何玩家補到新的花牌，則補花程序結束
        if not new_flower_drawn_in_round:
            break
            
        print("\n--> 偵測到有玩家補到新的花牌，進行下一輪補花...")
        
    print("\n--- 補花程序完成 ---")


### 3. 整合與測試

# 我們將使用之前定義的 `initialize_all_tiles` 和 `deal_taiwan_mahjong` 函式來測試這個補花邏輯。

# ```python
# 由於程式碼太長，我們需要在這裡重新定義之前的 Deck 和 Deal 函式，或者假設它們已經在一個模組中導入。
# 為了測試，這裡精簡定義一下 Deck 和 Deal


def deal_taiwan_mahjong(deck: MahjongDeck, num_players: int = 4) -> Dict[int, Player]:
    # 簡化版的發牌，直接使用 Player 物件
    hands_raw: Dict[int, List[str]] = {i: [] for i in range(num_players)}
    
    # 模擬配牌
    for _ in range(4):
        for player_id in range(num_players):
            hands_raw[player_id].extend(deck.wall.pop(0) for _ in range(4))
            
    # 莊家開門
    hands_raw[0].append(deck.wall.pop(0))
    
    players = {i: Player(i, hands_raw[i]) for i in range(num_players)}
    return players


# --- 測試流程 ---

# 1. 創建並初始化牌堆
game_deck = MahjongDeck()

# 2. 發牌給 4 個玩家
players = deal_taiwan_mahjong(game_deck)

# 3. 執行補花
replace_flowers(players, game_deck)


# 4. 補花結果檢查
# print("\n--- 補花後玩家手牌與花牌檢查 ---")
# for player_id, player in players.items():
#     player.hand.sort()
#     print(f"玩家 {player_id} 手牌數: {len(player.hand)} (應為 16/17)：{player.hand}")
#     print(f"玩家 {player_id} 花牌區 ({len(player.exposed_flowers)} 張)：{player.exposed_flowers}")
#     if any(is_flower_tile(tile) for tile in player.hand):
#         print("!!! 警告：手牌中仍有花牌，邏輯錯誤。")


# 聽牌分析


# --- 牌型輔助判斷 ---

def get_all_tiles() -> List[str]:
    """返回所有 34 種不重複的牌（萬、筒、索、字牌）。"""
    tiles = []
    for suit in ['m', 'p', 's']:
        for i in range(1, 10):
            tiles.append(f'{i}{suit}')
    for honor in ['We', 'Ws', 'Ww', 'Wn', 'R', 'G', 'Wb']:
        tiles.append(honor)
    return tiles

def is_honor_tile(tile: str) -> bool:
    """判斷是否為字牌 (Honor Tile)。"""
    return not (tile.endswith('m') or tile.endswith('p') or tile.endswith('s'))

def get_suit_and_rank(tile: str) -> Tuple[str, int]:
    """從簡寫中獲取花色和點數 (字牌返回 'Z', 0)。"""
    if is_honor_tile(tile):
        return 'Z', 0
    suit = tile[-1]
    rank = int(tile[:-1])
    return suit, rank

# --- 聽牌檢查的核心遞迴函式 ---

def can_form_target_melds(counts: Dict[str, int], target_melds: int, target_pairs: int) -> bool:
    """
    遞迴檢查給定的牌計數能否組成目標數量的搭子和將牌。
    
    Args:
        counts: 當前手牌的計數 (Counter 物件)。
        target_melds: 還需要組成的搭子數量 (順子/刻子)。
        target_pairs: 還需要組成的將牌數量 (只能是 0 或 1)。
    """
    
    # 遞迴終止條件
    if target_melds == 0 and target_pairs == 0:
        return True

    # 如果還有牌，但目標已達成，代表有多餘的牌，不胡
    if target_melds == 0 and target_pairs == 0 and any(v > 0 for v in counts.values()):
        return False

    if all(v == 0 for v in counts.values()):
        return False # 牌用完了但目標未達成

    # 1. 找到 counts 中第一張還有牌的牌 (作為本次嘗試的起頭牌)
    tile_names = sorted([t for t, c in counts.items() if c > 0])
    if not tile_names:
        return False

    current_tile = tile_names[0]
    
    # 2. 嘗試組成將牌 (Pair, 眼睛)
    if target_pairs == 1 and counts[current_tile] >= 2:
        # 嘗試將 current_tile 作為將牌
        counts[current_tile] -= 2
        if can_form_target_melds(counts, target_melds, 0):
            return True
        counts[current_tile] += 2 # 回溯 (Backtrack)

    # 3. 嘗試組成刻子 (Pung)
    if target_melds > 0 and counts[current_tile] >= 3:
        # 嘗試將 current_tile 組成刻子
        counts[current_tile] -= 3
        if can_form_target_melds(counts, target_melds - 1, target_pairs):
            return True
        counts[current_tile] += 3 # 回溯

    # 4. 嘗試組成順子 (Chow) - 僅適用於數牌
    suit, rank = get_suit_and_rank(current_tile)
    if target_melds > 0 and suit != 'Z': # 字牌不能組順子
        next_tile = f'{rank + 1}{suit}'
        next_next_tile = f'{rank + 2}{suit}'

        if rank <= 7 and counts.get(next_tile, 0) > 0 and counts.get(next_next_tile, 0) > 0:
            # 嘗試組成順子 (current_tile, next_tile, next_next_tile)
            counts[current_tile] -= 1
            counts[next_tile] -= 1
            counts[next_next_tile] -= 1
            
            if can_form_target_melds(counts, target_melds - 1, target_pairs):
                return True
                
            counts[current_tile] += 1
            counts[next_tile] += 1
            counts[next_next_tile] += 1 # 回溯

    # 5. 跳過 current_tile (必須是數量大於 0 的牌，如已組成刻子或順子後)
    # 由於我們每次都從 counts 中第一個有牌的 tile 開始，
    # 只要我們沒有成功利用 current_tile 繼續遞迴，就意味著它不能作為搭子的起點。
    # 如果 count[current_tile] > 0，但所有搭法都失敗，則此路不通，直接返回 False。
    
    # 如果 current_tile 數量不夠組成任何搭子，且不是將牌 (只剩 1 張)，
    # 這裡的邏輯是，如果 count[current_tile] == 1 且 target_pairs == 0，則此張牌是多餘的，必須跳過。
    # 但在嚴格胡牌檢查中，我們要求所有牌必須被用完。
    
    return False

# --- 聽牌檢查的主函式 ---

def find_what_tiles_to_win(
    hand: List[str], 
    known_discards: Set[str], # 已知打出的牌，用於判斷可胡的張數
    num_exposed_melds: int = 0
) -> Set[str]:
    """
    檢查玩家手牌（16 張）聽哪些牌。
    
    Args:
        hand: 玩家的 16 張手牌。
        known_discards: 桌面上所有玩家打過的牌，用於計算剩餘可胡張數。
        num_exposed_melds: 已經公開的搭子數（碰/吃/明槓）。
        
    Returns:
        一個集合，包含所有聽的牌的簡寫。
    """
    
    if len(hand) != 16:
        raise ValueError("聽牌檢查必須從 16 張手牌開始。")
        
    waiting_tiles: Set[str] = set()
    
    # 計算需要多少搭子和將牌
    # 台灣麻將目標：5 搭 + 1 對 = 6 組
    required_melds = 5 - num_exposed_melds
    required_pairs = 1

    # 迭代所有 34 種可能的胡牌
    all_possible_winning_tiles = get_all_tiles()
    
    for winning_tile in all_possible_winning_tiles:
        
        # 1. 模擬將這張牌加入手牌 (16 + 1 = 17 張)
        simulated_hand = hand + [winning_tile]
        
        # 2. 計算牌的計數
        counts = Counter(simulated_hand)
        
        # 3. 執行胡牌檢查
        # 複製 counts，避免遞迴時修改原始數據
        if can_form_target_melds(counts.copy(), required_melds, required_pairs):
            waiting_tiles.add(winning_tile)

    return waiting_tiles


### 2. 天胡檢查主函式
def check_heavenly_hand(hand: List[str]) -> bool:
    """
    檢查莊家起手 17 張牌是否已滿足五搭一對的胡牌結構 (天胡)。
    *天胡條件：17 張牌必須能夠完全組成 5 搭 1 對，且手牌中不能有花牌。*
    Args:
        hand: 莊家起手未補花的 17 張手牌。
        
    Returns:
        True 如果牌型為五搭一對，False 則否。
    """
    
    # 1. 基本檢查：確認張數
    if len(hand) != 17:
        print(f"錯誤：莊家手牌張數為 {len(hand)}，天胡檢查需要 17 張。")
        return False

    # 2. 花牌檢查：天胡發生時，花牌需要先計算並補牌。
    # 由於天胡是極特殊情況，一般規則是在 "補花動作前" 檢查是否已胡牌。
    # 如果手牌中包含花牌，根據某些規則，天胡不成立，或必須先補花。
    # 這裡假設傳入的 hand 尚未補花，但我們只檢查結構。
    
    # 1. 天胡的嚴格條件：不能有花牌 (花牌不構成搭子，且破壞天胡的完整性)
    flower_tiles = [tile for tile in hand if is_flower_tile(tile)]
    if len(flower_tiles) > 0:
        # print(f"天胡不成立：手牌中包含 {len(flower_tiles)} 張花牌。")
        return False
    
    # 2. 結構檢查：五搭一對
    # 計算牌張計數
    # 執行胡牌判斷：需要組成 5 組搭子 (刻子/順子) 和 1 組將牌 (眼睛)
    counts = Counter(hand)
    required_melds = 5
    required_pairs = 1
    
    # 將牌計數傳給遞迴函式
    return can_form_target_melds(counts.copy(), required_melds, required_pairs)

### 3. 地胡檢查主函式
def check_winning_hand(hand: List[str], win_tile: str, num_exposed_melds: int = 0) -> bool:
    """
    檢查任意 17 張牌（手牌 + 胡牌）是否構成五搭一對。
    
    Args:
        hand: 玩家的 16 張手牌（已補花、無花牌）。
        win_tile: 摸進或打出的胡牌。
        num_exposed_melds: 玩家已碰/吃了幾組搭子。
    """
    
    # 組合 16 張手牌 + 1 張胡牌 = 17 張
    current_hand = hand + [win_tile]
    
    if len(current_hand) != 17:
        # 理論上應該要是 17 張，如果不是則不進行檢查
        return False
        
    # 檢查是否還有花牌 (理論上補花後應該沒有)
    if any(is_flower_tile(tile) for tile in current_hand):
        return False
        
    counts = Counter(current_hand)
    
    # 標準五搭一對
    required_melds = 5 - num_exposed_melds
    required_pairs = 1

    return can_form_target_melds(counts.copy(), required_melds, required_pairs)

### 4. 人胡檢查主函式
def check_humanly_hand(player_hand: List[str], discarded_tile: str, is_first_discard: bool,  has_claimed_before: bool) -> bool:
    """
    檢查閒家是否符合人胡的條件。
    
    Args:
        player_hand: 閒家的 16 張手牌（已補花）。
        discarded_tile: 莊家打出的第一張牌。
        is_first_discard: 確定這是本局打出的第一張牌 (莊家第一張)。
        has_claimed_before: 確定牌局中尚未發生任何吃、碰、明槓。
        
    Returns:
        True 如果滿足人胡條件且牌型正確。
    """
    
    # 1. 觸發時機檢查：必須是莊家的第一張牌，且牌局乾淨
    if not is_first_discard or has_claimed_before:
        return False
        
    # 2. 結構檢查：判斷是否能胡這張牌
    # 閒家手牌必須是「門清」狀態，所以 num_exposed_melds 永遠是 0
    if check_winning_hand(player_hand, discarded_tile, num_exposed_melds=0):
        # 3. 額外的人胡條件：閒家必須是第一次胡牌判定，且手牌不能有花牌（已在 check_winning_hand 中涵蓋）
        return True
    
    return False

# ----------------------------------------------------------------------
# 假設我們已經有了 MahjongDeck 類別和 Player 類別
# 以及 initialize_all_tiles, deal_taiwan_mahjong, replace_flowers 函式
# ----------------------------------------------------------------------

def start_game_deal_and_check(deck: 'MahjongDeck') -> Tuple[bool, Dict[int, 'Player']]:
    """
    執行遊戲起始流程：發牌、天胡檢查、補花。
    
    Returns:
        (is_heavenly_hand, players)
    """
    print("--- 遊戲開始：執行發牌 ---")
    
    # 1. 發牌給所有玩家
    players = deal_taiwan_mahjong(deck, num_players=4)
    
    dealer_id = 0
    dealer = players[dealer_id]
    
    # 2. 莊家天胡檢查
    print(f"\n--- 莊家 {dealer_id} 檢查天胡 (17 張) ---")
    
    # 在檢查天胡時，我們必須排除花牌。如果排除花牌後，剩餘的牌數不是 17 張，則天胡失敗。
    # heavenly_tiles = [
    # '1m', '1m', '1m', '2p', '2p', '2p', '3s', '3s', '3s', 
    # 'R', 'R', 'R', 'Wb', 'Wb', 'Wb', 'We', 'We'
    # ]
    # regular_start_tiles = [
    # '1m', '2m', '3m', '4p', '5p', '6p', '7s', '8s', '9s', 
    # 'R', 'R', 'G', 'G', 'Wb', 'Wb', 'F1', 'S1' # 17 張 (F1, S1 是花牌)
    # ]
    # is_heavenly_hand = check_heavenly_hand(regular_start_tiles)
    is_heavenly_hand = check_heavenly_hand(dealer.hand)
    
    if is_heavenly_hand:
        print("🎉🎉🎉 **天胡成功！莊家胡牌！** 🎉🎉🎉")
        # 遊戲直接結束，無需補花
        return True, players
        
    print("天胡檢查：未胡牌，進入補花流程。")
    
    # 3. 執行補花流程 (所有人依序進行)
    replace_flowers(players, deck)
    
    # 4. 閒家地胡檢查 (在莊家打出第一張牌前，閒家摸到補花牌的瞬間，或閒家摸到第一張牌)
    # 由於地胡發生在莊家打第一張牌之後，這裡我們只檢查起手狀態。
    
    return False, players

# --- 測試與示範 ---

# 執行分析
# 為了讓範例正確運作，我們必須移除一張牌讓它變成 16 張手牌
# 移除 '1p' 讓它變成聽牌狀態
test_hand_1 = [
    '1s', '1s', '1s',       # 刻子 (Pung)
    '2m', '3m', '4m',       # 順子 (Chow)
    '5m', '6m', '7m',       # 順子 (Chow)
    'R', 'R', 'R',          # 刻子 (Pung)
    'Wb', 'Wb',             # 將牌 (Pair)
    '4p', '5p',             # 聽 3p 或 6p 
] 

test_hand = [
    '2m', '3m', '4m', '5m', '6m', '5p', '6p', '7p', 
    'R', 'R', 'R', 'Wb', 'Wb','7s', '8s', '9s']
# 執行聽牌分析
what_to_win = find_what_tiles_to_win(test_hand, set(), 0)

print(f"\n--- 範例手牌：{sorted(test_hand)} ---")
print(f"\n玩家聽牌結果 (5搭1對):")
if what_to_win:
    print(f"可胡的牌: {what_to_win}")
else:
    print("目前手牌尚未聽牌或牌型不對。")

# --- 測試案例 ---

# 1. 【天胡範例】 (5 刻子 + 1 對將牌 = 17 張)
# 111m, 222p, 333s, RRR, WbWbWb, EE
heavenly_hand = [
    '1m', '1m', '1m', '2p', '2p', '2p', '3s', '3s', '3s', 
    'R', 'R', 'R', 'Wb', 'Wb', 'Wb', 'We', 'We'
] # 17 張牌

# 2. 【非天胡範例】 (差一張牌)
not_heavenly_hand = [
    '1m', '1m', '1m', '2p', '2p', '2p', '3s', '3s', '3s', 
    'R', 'R', 'R', 'Wb', 'Wb', 'Wb', 'We', 'Ww'
] # 17 張牌，但最後兩張 'We', 'Ww' 無法成對

# 3. 【順子天胡範例】 (5 順子 + 1 對將牌 = 17 張)
chow_heavenly_hand = [
    '1m', '2m', '3m', '4m', '5m', '6m', '7m', '8m', '9m', 
    '1p', '2p', '3p', '1s', '2s', '3s', 'R', 'R'
] # 17 張牌 (注意：這裡只有 4 組順子，不足 5 組。需要重排)

# 順子天胡範例修正：5 組順子 + 1 對
chow_heavenly_hand_fixed = [
    '1m', '2m', '3m',      # 順子 1
    '4m', '5m', '6m',      # 順子 2
    '7m', '8m', '9m',      # 順子 3
    '1p', '2p', '3p',      # 順子 4
    '4p', '5p', '6p',      # 順子 5
    'R', 'R'               # 將牌
] # 17 張牌


# --- 執行檢查 ---
print("--- 莊家天胡 (Heavenly Hand) 檢查 ---")

result_1 = check_heavenly_hand(heavenly_hand)
print(f"天胡範例 (全刻子)：{'胡牌' if result_1 else '未胡牌'}")

result_2 = check_heavenly_hand(not_heavenly_hand)
print(f"非天胡範例 (亂牌)：{'胡牌' if result_2 else '未胡牌'}")

result_3 = check_heavenly_hand(chow_heavenly_hand_fixed)
print(f"順子天胡範例：{'胡牌' if result_3 else '未胡牌'}")


# ----------------------------------------------------------------------
# 測試情境一：天胡成功 (莊家牌組為 5 刻子 + 1 將牌，無花牌)
# ----------------------------------------------------------------------

# 17 張天胡牌：111m, 222p, 333s, RRR, WbWbWb, EE
heavenly_tiles = [
    '1m', '1m', '1m', '2p', '2p', '2p', '3s', '3s', '3s', 
    'R', 'R', 'R', 'Wb', 'Wb', 'Wb', 'We', 'We'
]

# 模擬一個牌堆，確保莊家拿到天胡牌
# 莊家拿前 17 張 (4*4 + 1)，其餘牌隨意填充

test_deck_1 = MahjongDeck()
is_win_1, players_1 = start_game_deal_and_check(test_deck_1)
if is_win_1:
    dealer = players_1[0]
    print(f"\n莊家天胡: {is_win_1}")
    print(f"\n莊家 (0) 補花後手牌數: {len(dealer.hand)}")
    print(f"莊家 (0) 花牌區: {dealer.exposed_flowers}")

# 假設 LogicHelpers 是一個包含靜態檢查方法的類
class LogicHelpers:
    @staticmethod
    def check_pong(counts: Counter, tile: str) -> bool:
        """檢查手牌中是否有兩張相同的牌，足以組成刻子。"""
        return counts.get(tile, 0) >= 2

    @staticmethod
    def check_gang(counts: Counter, tile: str) -> bool:
        """檢查手牌中是否有三張相同的牌，足以組成明槓。"""
        return counts.get(tile, 0) >= 3
        
    @staticmethod
    def check_chow(player_hand: List[str], claimed_tile: str, player_seat_position: str) -> list[Tuple[str, str]]:
        """
        檢查是否可吃牌。
        返回所有可能的順子組合，如果不能吃則返回 None。
        """
        # 由於吃牌只能吃上家，這裡假設已經在 resolve_claims 中檢查了 player_seat_position 是否是上家。
        
        # 這裡需要複雜的邏輯來檢查手牌中是否有順子缺張。
        # 簡化為：如果 claimed_tile 是數牌，檢查 player_hand 是否包含 (claimed_tile-2, claimed_tile-1) 或 (claimed_tile-1, claimed_tile+1) 等。
        
        # 由於此邏輯複雜且非本次核心，我們假設它能正確返回 [('2m', '3m'), ('4m', '5m'), ...]
        return [('2m', '3m')] # 示例返回值

class MahjongGame:
    def __init__(self, deck: MahjongDeck, players: Dict[int, Player]):
        self.deck = deck
        self.players = players
        self.discard_count = 0        # 記錄打出牌的總次數
        self.dealer_discards = []     # 莊家打出的牌
        self.current_turn = 0         # 當前回合的玩家 (0=莊家)
        self.has_dealer_discarded = False # 莊家是否已打出第一張牌
        self.num_players = len(players)

        # 遊戲狀態追蹤
        self.round_wind = 'E'            # 當前圈風，預設東風圈
        self.current_turn = 0            # 當前輪到打牌的玩家ID (0=莊家)
        self.has_claimed_yet = False     # 牌局中是否有發生吃/碰/明槓
        self.is_first_round = True       # 判斷是否為牌局的第一輪 (用於地胡/人胡)
        self.game_over = False           # 遊戲是否結束

        self.discard_pile: List[str] = [] # 追蹤所有玩家打出的牌，依序排列

    def start_game(self) -> bool:
        """執行遊戲起始流程：天胡檢查與補花。"""
        dealer = self.players[0]
        
        print("\n--- 遊戲開始：檢查莊家天胡 ---")
        
        # 1. 執行天胡檢查 (莊家 17 張牌，必須無花牌且結構為 5 搭 1 對)
        if self.check_heavenly_hand(dealer.hand):
            self.game_over = True
            print("🎉🎉🎉 **天胡！遊戲結束。** 🎉🎉🎉")
            return True
        
        print("天胡檢查：未胡牌，進入補花流程。")
        
        # 2. 執行補花流程 (所有玩家，從莊家開始)
        self.replace_all_flowers() # 假設這是封裝好的補花方法
        
        # 3. 進入莊家打牌流程
        return False

    def check_heavenly_hand(self, hand: List[str]) -> bool:
        """判斷是否天胡：17 張牌無花牌且結構為五搭一對。"""
        # 莊家手牌必須是 17 張且無花牌
        if len(hand) != 17 or any(is_flower_tile(tile) for tile in hand):
            return False
        
        return check_winning_hand(hand[:-1], hand[-1], num_exposed_melds=0)
        # 註：這裡假設 check_winning_hand(16張手牌, 1張胡牌) 的呼叫方式
        
    def replace_all_flowers(self):
        """簡化呼叫之前的補花邏輯。"""
        print("\n--- 執行全體玩家補花程序 ---")
        # 這裡需要呼叫您之前寫好的 replace_flowers(self.players, self.deck)
        # 執行補花流程 (所有人依序進行)
        replace_flowers(self.players, self.deck)
        # 確保補花完成後，所有玩家手牌都是 16/17 張且無花牌。

    def get_player_seat_wind(self, player_id: int) -> str:
        """根據玩家 ID 取得門風 (0=E, 1=S, 2=W, 3=N)"""
        winds = ['We', 'Ws', 'Ww', 'Wn']
        return winds[player_id]

    def dealer_makes_first_discard(self, tile_discarded: str):
        """模擬莊家打出第一張牌。"""
        self.discard_count = 1
        self.dealer_discards.append(tile_discarded)
        self.has_dealer_discarded = True
        print(f"\n--- 莊家 ({self.current_turn}) 打出第一張牌：{tile_discarded} ---")
        
        # 閒家的人胡檢查 (依逆時針順序：南家 -> 西家 -> 北家)
        for player_id in [1, 2, 3]:
            player = self.players[player_id]

            # 人胡檢查：必須是莊家第一張牌，且牌局乾淨 (has_claimed_yet = False)
            if check_humanly_hand(player.hand, tile_discarded):
                self.game_over = True
                print(f"🎉🎉🎉 **閒家 {player_id} 人胡成功 (接莊家第一張)！** 🎉🎉🎉")
                return True

        # 檢查是否有閒家接地胡 (地胡階段 2)
        for player_id in [1, 2, 3]:
            player = self.players[player_id]
            # 必須是門清狀態才能判定為地胡 (如果閒家沒有吃/碰)
            # 這裡假設 Player 類別有 is_exposed 屬性，我們簡化為 0 暴露
            
            if check_winning_hand(player.hand, tile_discarded, num_exposed_melds=0):
                print(f"🎉🎉🎉 **閒家 {player_id} 地胡成功 (接砲胡)！** 🎉🎉🎉")
                return True
                
        # 如果沒人接砲胡，輪到下一位玩家摸牌
        self.current_turn = 1 # 南家開始摸牌
        return False

    def player_draws_tile(self, player_id: int):
        """模擬閒家摸牌，並檢查是否地胡 (地胡階段 1)。"""
        if player_id == 0 or not self.is_first_round:
             # 莊家摸牌不是地胡
             return False 

        player = self.players[player_id]
        
        # 閒家必須是第一次摸牌（或補牌）且是從牌牆摸牌。
        # 這裡我們簡化為：只要是莊家打牌後閒家第一次摸牌，都檢查地胡。
        
        # 1. 摸牌
        try:
            new_tile = self.deck.draw_tile()
            player.hand.append(new_tile)
            print(f"\n玩家 {player_id} 摸牌：{new_tile}")
            
            # 2. 地胡檢查：必須是第一輪摸牌，且牌局乾淨
            # 檢查摸牌後是否胡牌
            # if check_winning_hand(player.hand[:-1], new_tile, num_exposed_melds=0):
            if self.check_earthly_hand(player.hand, new_tile):
                print(f"🎉🎉🎉 **閒家 {player_id} 地胡成功 (自摸)！** 🎉🎉🎉")
                return True
            
            # 如果不是地胡，則繼續遊戲（玩家打牌）
            # player.hand.pop() # 假設玩家打出牌，這裡只是還原手牌，實際應呼叫 discard 函式
            
            # 3. 如果沒有胡，則進入打牌階段
            # ... 接著是玩家打牌流程
            return False

        except IndexError:
            print("牌牆已空。")
            return False

    def check_earthly_hand(self, hand: List[str], win_tile: str) -> bool:
        """判斷是否地胡：閒家在牌局第一輪第一次摸牌自摸，且牌局乾淨。"""
        # 必須是第一輪，且牌局乾淨 (has_claimed_yet = False)
        # 必須是自摸，且手牌結構正確 (17張)
        
        # 我們需要確保這是閒家的「第一次摸牌」
        # 最簡單的方法是追蹤 round_number 或 discard_count
        
        # 判斷標準：牌局在莊家打第一張牌後，牌局尚未有吃碰，且玩家第一次摸牌
        if self.is_first_round and self.has_dealer_discarded and not self.has_claimed_yet:
            # 地胡必須是門清 (num_exposed_melds=0)
            # hand 已經是 17 張 (16 張手牌 + 1 張摸牌)
            return check_winning_hand(hand[:-1], win_tile, num_exposed_melds=0)
        return False
    
    def _draw_gang_tile(self, player_id: int):
        """處理槓牌後的補牌 (嶺上牌) 及槓上開花檢查。"""
        try:
            # 假設 self.deck.draw_tile(from_end=True) 從牌牆尾部補牌
            new_tile = self.deck.draw_tile(from_end=True) 
            player = self.players[player_id]
            player.hand.append(new_tile)
            
            print(f"玩家 {player_id} 槓上補牌：{new_tile}")
            
            # 檢查槓上開花 (自摸胡)
            # 假設 check_winning_hand 可用
            # if check_winning_hand(player.hand[:-1], new_tile, num_exposed_melds=len(player.melds)):
            #      print(f"🎉🎉🎉 玩家 {player_id} 槓上開花！")
            #      self.game_over = True
            
            # 槓上補花檢查
            if is_flower_tile(new_tile):
                # 這裡需要一個補花的機制，簡化為移除花牌並再次呼叫補牌
                player.remove_tiles([new_tile])
                player.flowers.append(new_tile)
                print(f"玩家 {player_id} 槓上摸到花牌 {new_tile}，繼續補牌。")
                self._draw_gang_tile(player_id) # 遞迴補花
                
        except Exception as e:
            print(f"❌ 補嶺上牌失敗: 牌牆已空。{e}")


    def execute_claim(self, claimant_id: int, discarded_tile: str, discarder_id: int, action: str, claim_details: Tuple[str, str] = None) -> bool:
        """
        處理玩家對於最新一張棄牌的請求 (吃、碰、明槓)。
        
        Args:
            claimant_id: 宣告動作的玩家 ID。
            discarded_tile: 被宣告的牌。
            discarder_id: 打出這張牌的玩家 ID。
            action: 'PONG', 'EXPOSED_GANG', 或 'CHOW'。
            claim_details: 僅用於 CHOW，指定組合成順子的兩張手牌 (tile_1, tile_2)。
        """
        
        # 1. 遊戲狀態更新: 牌局已不乾淨，終止地胡/人胡資格
        self.has_claimed_yet = True
        
        player = self.players[claimant_id]
        
        if action == 'PONG':
            if check_pong(player.get_hand_counts(), discarded_tile):
                tiles_to_remove = [discarded_tile, discarded_tile]
                player.remove_tiles(tiles_to_remove)
                player.add_meld([discarded_tile] * 3, 'PONG', is_concealed=False)
                print(f"✅ 玩家 {claimant_id} 碰牌：{discarded_tile} x 3")
                self.current_turn = claimant_id # 碰完由碰牌者打牌
                return True
            
        elif action == 'EXPOSED_GANG':
            if check_exposed_gang(player.get_hand_counts(), discarded_tile):
                tiles_to_remove = [discarded_tile] * 3
                player.remove_tiles(tiles_to_remove)
                player.add_meld([discarded_tile] * 4, 'EXPOSED_GANG', is_concealed=False)
                print(f"✅ 玩家 {claimant_id} 明槓：{discarded_tile} x 4")
                self._draw_gang_tile(claimant_id) # 槓上補牌
                self.current_turn = claimant_id # 槓完由槓牌者打牌
                return True
                
        elif action == 'CHOW':
            # 檢查是否為上家 (只有上家能吃)
            if claimant_id != (discarder_id + 1) % self.num_players:
                print("❌ 吃牌失敗：只有打牌者的上家才能吃。")
                return False

            if claim_details:
                tile_1, tile_2 = claim_details
                # 再次確認玩家手牌是否持有這兩張牌
                if player.get_hand_counts()[tile_1] >= 1 and player.get_hand_counts()[tile_2] >= 1:
                    player.remove_tiles([tile_1, tile_2])
                    chow_meld = sorted([tile_1, tile_2, discarded_tile]) # 假設牌有排序鍵
                    player.add_meld(chow_meld, 'CHOW', is_concealed=False)
                    print(f"✅ 玩家 {claimant_id} 吃牌：順子 {chow_meld}")
                    self.current_turn = claimant_id # 吃完由吃牌者打牌
                    return True
                
        print(f"❌ 玩家 {claimant_id} 執行 {action} 失敗或不符合規則。")
        return False
        
    
    # -----------------------------------------------------------
    # 玩家主動執行的槓 (非對棄牌的響應)
    # -----------------------------------------------------------
    
    def execute_concealed_gang(self, player_id: int, gang_tile: str) -> bool:
        """處理玩家的暗槓 (自己摸牌後，手牌中有四張)。"""
        player = self.players[player_id]
        if player.get_hand_counts()[gang_tile] == 4:
            player.remove_tiles([gang_tile] * 4)
            player.add_meld([gang_tile] * 4, 'CONCEALED_GANG', is_concealed=True)
            print(f"✅ 玩家 {player_id} 暗槓：{gang_tile} x 4")
            self._draw_gang_tile(player_id) # 槓上補牌
            return True
        return False
        
    def execute_add_on_gang(self, player_id: int, gang_tile: str) -> bool:
        """處理玩家的加槓/補槓 (有碰子後摸到第四張，對碰子升級)。"""
        player = self.players[player_id]
        
        # 1. 檢查是否有該牌的碰子
        pong_meld = next((meld for meld in player.melds 
                          if meld['type'] == 'PONG' and meld['tiles'][0] == gang_tile), None)
        
        if pong_meld and player.get_hand_counts()[gang_tile] >= 1:
            # 2. 移除手牌中的那張牌
            player.remove_tiles([gang_tile])
            # 3. 更新 meld 類型
            pong_meld['tiles'].append(gang_tile)
            pong_meld['type'] = 'EXPOSED_GANG' # 碰子升級的槓也是外露
            print(f"✅ 玩家 {player_id} 加槓：{gang_tile} x 4 (從碰子升級)")
            
            # 4. 槓上補牌 (注意：加槓可能被其他玩家搶槓胡)
            self._draw_gang_tile(player_id)
            return True
        return False
    
    def check_for_win(
        self, 
        current_hand: List[str], 
        win_tile: str, 
        num_exposed_melds: int
    ) -> bool:
        """
        檢查玩家手牌是否能胡特定的 win_tile。
        
        Args:
            current_hand: 玩家的當前手牌 (通常是 16 張，已補花)。
            win_tile: 摸進或打出的胡牌。
            num_exposed_melds: 玩家已公開的搭子數量 (碰/吃/明槓)。
            
        Returns:
            True 如果胡牌結構成立，False 否則。
        """
        
        # 1. 總牌張數檢查
        # 台灣麻將胡牌總數為 17 張 (五搭一對)
        if len(current_hand) + 1 != 17:
            return False 

        # 2. 準備完整的 17 張牌計數
        full_hand_counts = Counter(current_hand)
        full_hand_counts[win_tile] += 1
        
        # 3. 判斷需要完成的暗搭子數量
        # 總搭子數必須是 5 組。
        # 已公開的搭子 (num_exposed_melds) 可能來自於 player.melds 的長度。
        required_concealed_melds = 5 - num_exposed_melds
        
        if required_concealed_melds < 0:
            # 這是防止錯誤的防禦性檢查，因為不可能有超過 5 個搭子
            return False 

        # 4. 呼叫核心遞迴判斷
        # 必須從 17 張牌中組成 required_concealed_melds 個搭子 和 1 個將牌 (對子)。
        
        # 註：這裡我們假設 can_form_target_melds 已經能處理將牌的尋找和搭子的組成。
        return can_form_target_melds(
            full_hand_counts, 
            required_melds=required_concealed_melds, 
            required_pairs=1
        )

    def play_turn(self, discarded_tile: str) -> bool:
        """
        處理當前玩家打出牌的完整回合邏輯。
        
        Args:
            discarded_tile: 當前玩家選擇打出的牌。
            
        Returns:
            True 如果成功處理了回合，False 如果遊戲已結束或流程錯誤。
        """
        if self.game_over:
            print("遊戲已結束，無法繼續回合。")
            return False

        discarder_id = self.current_turn
        discarder = self.players[discarder_id]
        self.current_discarder = discarder_id
        
        # 1. 執行打牌：將牌從手牌中移除
        try:
            discarder.hand.remove(discarded_tile)
            # 實際應用中，這張牌會被加入到公共牌區 (self.discarded_tiles)
             # *** 新增：將牌加入到棄牌區 ***
            self.discard_pile.append(discarded_tile) 
            print(f"\n--- 玩家 {discarder_id} 打出牌：{discarded_tile} ---")
        except ValueError:
            print(f"錯誤：玩家 {discarder_id} 手中沒有牌 {discarded_tile}。")
            return False

        # 2. 核心：處理所有玩家的叫牌請求 (胡 > 碰/槓 > 吃)
        claim_resolved = self.resolve_claims(discarded_tile, discarder_id)

        # 3. 判斷後續流程
        if claim_resolved:
            # 如果有動作發生（胡/碰/槓/吃），current_turn 已經被更新到下一位打牌者
            # 遊戲將等待新的 current_turn 玩家執行打牌動作
            return True
        else:
            # 無任何動作發生，則輪到下一位玩家摸牌
            # current_turn 已在 resolve_claims 中更新為下一位摸牌者
            self.draw_tile_phase()
            return True

    def resolve_claims(self, discarded_tile: str, discarder_id: int) -> bool:
        """
        處理棄牌後的動作宣告與優先級。
        
        Args:
            discarded_tile: 被打出的牌。
            discarder_id: 打出這張牌的玩家 ID。
            
        Returns: 
            True 如果有動作發生 (胡牌/碰/槓/吃)，False 則輪到下一家摸牌。
        """
        
        # ----------------------------------------------------
        # 1. 胡牌檢查 (最高優先級)
        # ----------------------------------------------------
        winning_players = []
        for player_id in range(len(self.players)):
            if player_id == discarder_id: continue
            
            player = self.players[player_id]
            # 假設 check_for_win 會根據當前手牌和贏牌判斷是否胡牌
            if self.check_for_win(player.hand, discarded_tile, len(player.melds)):
                winning_players.append(player_id)
                
        if winning_players:
            print(f"🎉 **胡牌！** 玩家 {winning_players} 胡了 {discarder_id} 的牌！")
            # 處理多響 (一炮多響) 結算
            self.score_final_hand(winning_players, discarder_id, discarded_tile)
            self.game_over = True
            return True # 遊戲結束
            
        # ----------------------------------------------------
        # 2. 碰/明槓檢查 (次高優先級)
        # ----------------------------------------------------
        can_pong_or_gang = []
        for player_id in range(len(self.players)):
            if player_id == discarder_id: continue
            
            player = self.players[player_id]
            
            # **碰** 的優先級高於 **明槓**，但兩個都高於 **吃**
            if check_pong(player.get_hand_counts(), discarded_tile):
                can_pong_or_gang.append({'id': player_id, 'action': 'PONG'})
            elif check_exposed_gang(player.get_hand_counts(), discarded_tile):
                can_pong_or_gang.append({'id': player_id, 'action': 'EXPOSED_GANG'})
                
        if can_pong_or_gang:
            # 實戰：詢問玩家選擇。程式：通常選擇離打牌者最近的玩家（逆時針方向：ID 越大越優先）
            # 為了簡化，我們只取第一個能宣告的動作。
            chosen_claim = can_pong_or_gang[0]
            action = chosen_claim['action']
            claimant_id = chosen_claim['id']
            
            # 執行碰或槓的邏輯 (這會更新 current_turn 到 claimant_id)
            if self.execute_claim(claimant_id, discarded_tile, discarder_id, action):
                print(f"📣 玩家 {claimant_id} 執行了 {action}，輪到他打牌。")
                return True
            
        # ----------------------------------------------------
        # 3. 吃牌檢查 (最低優先級，僅限上家)
        # ----------------------------------------------------
        next_player_id = (discarder_id + 1) % len(self.players)
        next_player = self.players[next_player_id]
        
        possible_chows = check_chow(next_player.get_hand_counts(), discarded_tile)
        
        if possible_chows:
            # 實戰：詢問上家是否吃，及選擇哪種吃法
            # 程式：假設上家選擇吃第一個可行的順子組合
            chosen_chow = possible_chows[0] 
            
            # 執行吃牌邏輯 (這會更新 current_turn 到 next_player_id)
            if self.execute_claim(next_player_id, discarded_tile, discarder_id, 'CHOW', chosen_chow):
                print(f"🍚 玩家 {next_player_id} 執行了 CHOW，輪到他打牌。")
                return True

        # 4. 無任何動作，將下一回合的玩家設定為摸牌者
        self.current_turn = next_player_id
        return False

    def check_available_claims(self, player_id: int, tile: str, from_discard: bool) -> List[Tuple[str, Optional[List]]]:
        """檢查玩家對給定牌張可做的所有合法宣告。"""

        player = self.players[player_id]
        available_claims = []
        hand_counts = Counter(player.hand)

        # --- 1. 胡牌 (HU) ---
        if self.check_for_win(player.hand, tile, len(player.melds)):
            # 必須檢查是否有過水限制 (您之前討論的規則)
            if not player.pass_status.get('HU', False):
                 available_claims.append(('HU', None))

        # 動作優先級：胡 > 槓/碰 > 吃
        if from_discard:

            # --- 2. 槓 (KONG) ---
            if LogicHelpers.check_gang(hand_counts, tile):
                # 必須檢查是否有過水限制
                if not player.pass_status.get('KONG', False):
                    available_claims.append(('KONG', None))

            # --- 3. 碰 (PONG) ---
            elif LogicHelpers.check_pong(hand_counts, tile):
                if not player.pass_status.get('PONG', False):
                    available_claims.append(('PONG', None))

            # --- 4. 吃 (CHOW) ---
            # 吃牌只能對上家 (Player to the Left) 進行
            if self.is_player_to_left(player_id, self.current_discarder):
                chow_combinations = LogicHelpers.check_chow(player.hand, tile, 'left')
                if chow_combinations:
                    available_claims.append(('CHOW', chow_combinations))

        else: # 來自自己摸牌 (From self-draw)
             # --- 5. 暗槓/加槓 (CONCEALED/ADDON KONG) ---
             # 這裡檢查的是手牌中的四張牌，無需外來 tile
             concealed_kongs = self.check_concealed_kongs(player_id)
             if concealed_kongs:
                 available_claims.append(('CONCEALED_KONG', concealed_kongs))
                 
             addon_kongs = self.check_addon_kongs(player_id)
             if addon_kongs:
                 available_claims.append(('ADDON_KONG', addon_kongs))

        return available_claims

    def is_player_to_left(self, player_a: int, player_b: int) -> bool:
        """檢查 A 是否是 B 的上家 (左手邊)。"""
        return (player_a - 1) % self.num_players == player_b
        
    def check_concealed_kongs(self, player_id: int) -> Optional[List[str]]:
        """檢查手牌中是否有四張一樣的牌可暗槓。"""
        # ... 實作邏輯 ...
        return None
        
    def check_addon_kongs(self, player_id: int) -> Optional[List[str]]:
        """檢查玩家的外露碰牌中是否有可加槓的牌。"""
        # ... 實作邏輯 ...
        return None

    # 3. 摸牌後流程 (draw_tile_phase)
    def draw_tile_phase(self):
        """處理當前玩家的摸牌流程。"""
        #  處理玩當前家摸牌、補花、自摸、暗槓、加槓、流程。

        player_id = self.current_turn
        player = self.players[player_id]

        # 關鍵：進入自己回合，清除自己的過水狀態
        player.clear_pass_status()
        try:
            # 1. 摸牌
            new_tile = self.deck.draw_tile(from_end=False) # 從牌牆抽取
            player.hand.append(new_tile)
            print(f"🃏 玩家 {player_id} 摸牌：{new_tile}")

            # 2. 檢查摸牌後是否為花牌 (需補牌)
            if is_flower_tile(new_tile):
                # 執行補花邏輯 (假設已定義)
                # player.handle_flower_tile(new_tile, self.deck) 
                replace_flowers({player_id: player}, self.deck)

            # 3. 檢查自摸 / 槓
            claims = self.check_available_claims(player_id, new_tile, from_discard=False)

            # 4. 處理動作優先級：胡 > 槓 > 打牌
            if ('HU', None) in claims:
                # 執行自摸胡牌結算
                print(f"🎉 **玩家 {player_id} 自摸胡牌！**")
                self.score_final_hand([player_id], player_id, new_tile)
                return
            
            # 檢查摸牌後是否要槓牌 (暗槓/加槓)
            # 這裡需要詢問玩家是否執行 execute_concealed_gang 或 execute_add_on_gang
            # 如果執行槓牌，則進入 _draw_gang_tile 流程，然後再次詢問打牌
            
            # 檢查是否有暗槓或加槓
            kong_claims = [c for c in claims if c[0] in ['CONCEALED_KONG', 'ADDON_KONG']]
            if kong_claims:
                # 實戰中需要詢問玩家是否執行槓牌 (UI 互動)
                # 這裡我們假設玩家選擇執行第一個槓
                action, tiles = kong_claims[0]
                # self.execute_kong_claim(player_id, action, tiles)
                self.execute_concealed_gang(player_id, tiles[0]) if action == 'CONCEALED_KONG' else self.execute_add_on_gang(player_id, tiles[0])
                return

            # 5. 如果沒有胡牌或槓牌，玩家必須打出一張牌
            # 進入 UI 階段，讓玩家選擇打出哪張牌
            # 最終：玩家必須打牌
            print(f"▶️ 玩家 {player_id} 必須從牌中選擇一張打出。")

        except Exception as e:
            # 牌牆已空，檢查流局 or 執行流局
            print("牌牆已空，執行流局檢查。")
            # self.check_for_draw()
            self.end_game_draw()

    def draw_kong_phase(self, claimant_id: int):
        """處理槓上補牌流程。"""

        # 1. 從嶺上牌區摸牌
        try:
            drawn_tile = self.deck.draw_tile(from_end=True) # 從牌牆尾部摸牌
        except IndexError:
            # 死牌區已空，可能導致特殊流局，但此處僅處理補牌失敗
            print("⚠️ 槓上無牌可補！")
            return

        player = self.players[claimant_id]
        player.hand.append(drawn_tile)

        # 2. 檢查槓上開花 (自摸)
        if self.check_for_win(player.hand, drawn_tile, len(player.melds)):
            # 執行槓上開花結算
            self.score_final_hand([claimant_id], None, drawn_tile, is_kong_draw=True)
            return

        # 3. 槓後打牌：如果沒有胡牌，玩家必須打出一張牌
        # 回到 UI 階段，讓玩家選擇打出哪張牌
        print(f"玩家 {claimant_id} 槓上補牌後，必須選擇一張牌打出。")

    # 假設 get_tai_info 函式能從遊戲狀態中準備 TaiInfo 物件
    def get_tai_info(self, player_id: int, win_tile: str, is_self_draw: bool) -> TaiInfo:
        # 這裡需要從 self.players[player_id] 和遊戲狀態 (self.is_last_tile, self.has_claimed_yet 等)
        # 收集所有資訊，並構建 TaiInfo 實例。
        # ... 實作細節 ...
        return TaiInfo(...)
    
    def get_dealer_streak(self) -> int:
        """獲取當前莊家的連莊次數 (假設遊戲狀態中儲存了這個資訊)。"""
        # return self.dealer_streak_count 
        return 0 # 暫時返回 0
    
    def score_final_hand(self, winning_players: List[int], discarder_id: int, win_tile: str):
        """計算並結算胡牌玩家的台數。"""
        
        for winner_id in winning_players:
            is_self_draw = (winner_id == discarder_id)
            is_dealer = (winner_id == 0) # 假設莊家 ID 為 0
            
            # 1. 準備資訊包
            info = self.get_tai_info(winner_id, win_tile, is_self_draw)
            
            # 2. 計算台數
            calculator = TaiCalculator(info)
            total_tai, breakdown = calculator.calculate_all(
                is_dealer=is_dealer, 
                dealer_streak=self.get_dealer_streak()
            )

            # 3. 結算 (範例)
            print("====================================")
            print(f"**玩家 {winner_id} 胡牌！** (自摸: {is_self_draw})")
            print(f"總台數: {total_tai} 台")
            print("--- 台數明細 ---")
            for name, tai in breakdown.items():
                print(f"  {name.ljust(10)}: {tai} 台")
            print("====================================")
            
            # 4. 實際結算金額 (底金+台金) 邏輯將在這裡執行
            # self.settle_payments(winner_id, total_tai, discarder_id)
    
    #
    # 流局結算函式 (end_game_draw)
    #
    def end_game_draw(self, draw_reason: str = "Deck Empty"):
        """
        執行流局結算，處理不聽牌的包賠規則。

        Args:
            draw_reason: 流局的原因 ('Deck Empty', 'No More Kong Tile', etc.)
        """
        print(f"\n======== 遊戲流局：{draw_reason} ========")
        self.game_over = True

        # 1. 檢查並宣告聽牌玩家 (Ting/Waiting Status)
        # 在流局時，所有玩家必須公開手牌，證明自己是否處於聽牌狀態。
        waiting_players = []
        non_waiting_players = []

        for player_id, player in self.players.items():
            # 輔助函式：檢查玩家是否處於聽牌狀態
            # 這裡需要遍歷所有可能胡牌的牌張 (總共 34 種牌)
            is_waiting = self.check_if_player_is_waiting(player) 
            
            if is_waiting:
                waiting_players.append(player_id)
                print(f"✅ 玩家 {player_id} (聽牌)")
            else:
                non_waiting_players.append(player_id)
                print(f"❌ 玩家 {player_id} (未聽牌)")

        # 2. 執行流局結算 (不聽牌包賠 / 公平分配)
        if not waiting_players:
            print("所有玩家皆未聽牌，本局無輸贏，莊家繼續。")
            self.end_round_no_score()
            return

        if not non_waiting_players:
             print("所有玩家皆聽牌，本局無輸贏，莊家繼續。")
             self.end_round_no_score()
             return

        # 3. 處理不聽牌的包賠規則 (主流台灣麻將規則)
        # 規則：未聽牌的玩家必須付錢給所有聽牌的玩家。
        
        # 流局的基礎分數 (可設定為遊戲參數)
        base_fine = 16  # 假設一個基礎罰分值 (例如 16 台對應的底金)
        
        num_waiting = len(waiting_players)
        num_non_waiting = len(non_waiting_players)
        
        total_payment_per_non_waiting = base_fine * num_waiting
        
        settlements = {pid: 0 for pid in range(self.num_players)}
        
        print("\n--- 流局金結算 ---")
        
        # 未聽牌玩家的支出
        for nwp_id in non_waiting_players:
            # 支付給每個聽牌玩家 base_fine 的罰金
            settlements[nwp_id] -= total_payment_per_non_waiting
            print(f"玩家 {nwp_id} 須支付：{total_payment_per_non_waiting}")
            
            # 聽牌玩家的收入
            payment_from_nwp = base_fine
            for wp_id in waiting_players:
                 settlements[wp_id] += payment_from_nwp
                 
        # 4. 顯示最終結算
        for pid, amount in settlements.items():
            action = "贏得" if amount > 0 else "支付"
            print(f"玩家 {pid} 最終結算：{action} {abs(amount)}")
            # self.players[pid].score += amount # 實際更新分數

        # 5. 結束本局並準備下一局 (莊家續莊)
        self.end_round_dealer_continues()
        
    def check_if_player_is_waiting(self, player) -> bool:
        """
        核心輔助函式：檢查玩家手牌是否只需要一張牌即可胡牌。
        遍歷 34 種牌，將其加到手牌中，檢查是否胡牌。
        """
        # 假設我們已經知道所有 34 種牌的列表
        all_34_tiles = self.get_all_34_tiles_types() 
        
        hand_counts = Counter(player.hand)
        
        for check_tile in all_34_tiles:
            # 嘗試加入這張牌
            hand_counts[check_tile] += 1
            
            # 檢查是否能組成胡牌結構 (5搭1對)
            # 這裡 target_melds=5, target_pairs=1，因為總張數是 17
            is_hu = self.can_form_target_melds(hand_counts, 5, 1) 
            
            # 移除這張牌，準備檢查下一張
            hand_counts[check_tile] -= 1
            
            if is_hu:
                return True # 只要能胡其中任何一張牌，即為聽牌
                
        return False

    def end_round_no_score(self):
        """流局但無輸贏，莊家繼續坐莊。"""
        # 這裡可以加入連莊計數的邏輯
        pass
        
    def end_round_dealer_continues(self):
        """流局後莊家繼續坐莊。"""
        # 這裡可以加入連莊計數的邏輯
        pass
        
    def get_all_34_tiles_types(self) -> List[str]:
        """返回所有 34 種牌的列表，用於遍歷檢查。"""
        # 示例：['1m', '2m', ..., '9m', '1p', ..., 'White', 'Red']
        return [] # 實作此列表