from typing import List, Dict
from collections import Counter
from typing import List, Dict, Tuple, Optional, Set

class TaiInfo:
    """胡牌所需的所有核心資訊。"""
    def __init__(self, 
                 hand_counts: Counter, 
                 exposed_melds: List[Dict], # 外露搭子列表
                 flowers: List[str], 
                 is_self_draw: bool, 
                 is_concealed: bool,        # 是否門清
                 is_first_round_win: bool,  # 判斷地胡/人胡/天胡
                 round_wind: str,           # 圈風
                 seat_wind: str,            # 門風
                 is_last_tile: bool,        # 海底撈月/魚
                 is_gang_draw: bool,        # 槓上開花
                 is_robbing_gang: bool      # 搶槓
                ):
        self.counts = hand_counts
        self.exposed_melds = exposed_melds
        self.flowers = flowers
        self.is_self_draw = is_self_draw
        self.is_concealed = is_concealed
        self.is_first_round_win = is_first_round_win
        self.round_wind = round_wind
        self.seat_wind = seat_wind
        self.is_last_tile = is_last_tile
        self.is_gang_draw = is_gang_draw
        self.is_robbing_gang = is_robbing_gang

class TaiCalculator:
    def __init__(self, info: TaiInfo):
        self.info = info
        self.tai_results: Dict[str, int] = {}
        self.total_tai = 0

        # 建立牌張分類 (用於快速檢查花色和字牌)
        self.honor_tiles = {'We', 'Ws', 'Ww', 'Wn', 'R', 'G', 'B'}
        self.suit_tiles = [t for t in info.counts.keys() if t not in self.honor_tiles]

    def calculate_all(self, is_dealer: bool, dealer_streak: int) -> Tuple[int, Dict[str, int]]:
        """執行所有台數檢查，並返回總台數和明細。"""

        # 1. 天地人胡檢查 (最高優先級，互斥於基礎台)
        if self._check_heavenly_earthly_humanly(is_dealer):
             # 天胡、地胡、人胡成立，不繼續檢查基礎台
             pass
        else:
             # 2. 基礎與特殊動作台
             self._check_basic_tai()
             self._check_action_tai()

             # 3. 牌型台 (從高台開始檢查)
             self._check_high_honors_tai()  # 大四喜、大三元、字一色
             self._check_high_suit_tai()    # 清一色、混一色
             self._check_mid_tai()          # 碰碰胡、四暗刻、五暗刻、小三元、小四喜
             self._check_low_tai()          # 平胡、三暗刻、全求人

             # 4. 風箭花牌台 (通常可疊加)
             self._check_wind_dragon_tai()
             self._check_flower_tai()
    
        # 5. 莊家台 (獨立計算，通常疊加)
        self._check_dealer_tai(is_dealer, dealer_streak)
        
        self.total_tai = sum(self.tai_results.values())
        return self.total_tai, self.tai_results

    # --------------------------------------------------------------------
    # 各類台數檢查方法
    # --------------------------------------------------------------------

    def _add_tai(self, name: str, tai: int):
        """輔助函式：新增台數，處理重複或互斥邏輯。"""
        # 在這裡可以定義互斥邏輯 (例如：大三元成立，則移除所有三元刻)
        if name in self.tai_results:
             self.tai_results[name] += tai
        else:
             self.tai_results[name] = tai
             
        # 處理門清一摸三 (這是最常見的互斥邏輯之一)
        if '門清' in self.tai_results and '自摸' in self.tai_results:
            if self.info.is_concealed and self.info.is_self_draw:
                self.tai_results['門清一摸三'] = 3
                del self.tai_results['門清']
                del self.tai_results['自摸']
    
    def _check_heavenly_earthly_humanly(self, is_dealer: bool) -> bool:
        """檢查天胡、地胡、人胡 (最高台，通常互斥於基礎台)。"""
        if not self.info.is_first_round_win:
            return False
            
        if is_dealer and self.info.is_self_draw:
            self._add_tai("天胡", 24)
            return True
        elif not is_dealer and self.info.is_self_draw:
            self._add_tai("地胡", 16)
            return True
        elif not is_dealer and not self.info.is_self_draw:
            self._add_tai("人胡", 16)
            return True
        return False
        
    def _check_basic_tai(self):
        """檢查自摸、門清、不求人等基礎台。"""
        if self.info.is_self_draw:
            self._add_tai("自摸", 1)
        
        if self.info.is_concealed:
            self._add_tai("門清", 1)
            # 門清自摸會觸發 門清一摸三，已在 _add_tai 中處理

    def _check_action_tai(self):
        """檢查槓上開花、海底、搶槓等動作台。"""
        if self.info.is_gang_draw and self.info.is_self_draw:
            self._add_tai("槓上開花", 1)
            
        if self.info.is_last_tile:
            if self.info.is_self_draw:
                self._add_tai("海底撈月", 1)
            else:
                self._add_tai("河底撈魚", 1)
                
        if self.info.is_robbing_gang and not self.info.is_self_draw:
            self._add_tai("搶槓", 1)

    # --------------------------------------------------------------------
    # 牌型台 (僅列舉幾個關鍵，實作需要大量的結構檢查)
    # --------------------------------------------------------------------

    def _check_high_honors_tai(self):
        """檢查大四喜、大三元、字一色。"""
        # 簡化檢查：檢查所有牌是否都是字牌
        if all(tile in self.honor_tiles for tile, count in self.info.counts.items()):
            self._add_tai("字一色", 16)

        # 實際應呼叫更複雜的檢查函式來判斷大三元、大四喜、小三元、小四喜...

    def _check_high_suit_tai(self):
        """檢查清一色、混一色。"""
        num_suits = len({tile[-1] for tile in self.info.counts.keys() if tile in 'mps'})
        
        has_honors = any(tile in self.honor_tiles for tile in self.info.counts.keys())
        
        if num_suits == 1 and not has_honors:
            self._add_tai("清一色", 8)
        elif num_suits == 1 and has_honors:
            self._add_tai("混一色", 4)

    # --------------------------------------------------------------------
    # 風箭花牌台 (假設牌型已經組成刻子)
    # --------------------------------------------------------------------
    
    def _check_wind_dragon_tai(self):
        """檢查圈風、門風、三元刻。"""
        # 檢查所有已完成的刻子/槓子 (melds 和暗刻)
        all_melds = self.info.exposed_melds + self._find_concealed_melds(self.info.counts)
        
        for meld in all_melds:
            tile = meld['tiles'][0]
            
            # 三元刻 (紅中/發財/白板)
            if tile in ['R', 'G', 'B']:
                self._add_tai("三元刻", 1)
            
            # 圈風/門風
            if tile in ['We', 'Ws', 'Ww', 'Wn']:
                if tile == self.info.round_wind:
                    self._add_tai("圈風台", 1)
                if tile == self.info.seat_wind:
                    self._add_tai("門風台", 1)
                    
    def _check_flower_tai(self):
        """檢查正花、八仙過海、七搶一。"""
        num_flowers = len(self.info.flowers)
        
        # 八仙過海 (湊齊 8 張花牌)
        if num_flowers == 8:
            self._add_tai("八仙過海", 8) # 通常直接結算
            return
            
        # 正花 (檢查花牌與座位的匹配)
        seat_index = {'We': 0, 'Ws': 1, 'Ww': 2, 'Wn': 3}[self.info.seat_wind]
        expected_flowers = [['F1', 'H1'], ['F2', 'H2'], ['F3', 'H3'], ['F4', 'H4']][seat_index]
        
        for flower in self.info.flowers:
            if flower in expected_flowers:
                self._add_tai("正花", 1)
            
        # 檢查花槓 (春夏秋冬或梅蘭竹菊)
        
    def _check_dealer_tai(self, is_dealer: bool, dealer_streak: int):
        """檢查莊家台與連莊台。"""
        if is_dealer:
            self._add_tai("莊家", 1)
            if dealer_streak > 0:
                # 連 N 拉 N 公式: 2N + 1 (莊家本身 1 台 + 連 N 拉 N 共 2N 台)
                self._add_tai(f"連{dealer_streak}拉{dealer_streak}", dealer_streak * 2)

    # --------------------------------------------------------------------
    # 輔助函式 (僅為簡化結構)
    # --------------------------------------------------------------------
    def _find_concealed_melds(self, counts: Counter) -> List[Dict]:
        """簡化：從手牌中找出所有暗刻 (未碰出的 3 張相同牌)。"""
        concealed_melds = []
        for tile, count in counts.items():
            # 找出暗刻和暗槓
            if count >= 3:
                # 這裡需要更精確的遞迴判斷，以避免將順子中的刻子算進來
                # 簡單來說，如果牌型結構是五搭一對，則可以找出暗刻
                pass 
        return concealed_melds