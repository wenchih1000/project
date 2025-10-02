from flask import Flask, render_template, request, jsonify
# 假設您的 MahjongGame 類別已在 mahjong_logic.py 中
# from .mahjong_logic import MahjongGame, Player, MahjongDeck 
from deck import MahjongGame, Player, MahjongDeck, deal_taiwan_mahjong
app = Flask(__name__)
game = None # 全域變數來儲存遊戲實例

@app.route('/')
def index():
    """主頁面：顯示遊戲介面。"""
    return render_template('game.html')

@app.route('/start_game', methods=['POST'])
def start_game_route():
    """開始一局新的遊戲，初始化 MahjongGame。"""
    global game
    # 假設您有牌堆和玩家資料
    deck = MahjongDeck() 
    dictData = deal_taiwan_mahjong(deck,4)
    players = {i: Player(i, dictData[i].hand) for i in range(4)}
    game = MahjongGame(deck, players)
    
    # 初始化發牌和補花（簡化）
    # game.initialize_hands() 
    game.start_game() 

    return jsonify({"success": True, "message": "遊戲已啟動"})

@app.route('/get_state')
def get_game_state():
    """獲取當前遊戲狀態（供前端渲染）。"""
    if not game:
        return jsonify({"error": "遊戲尚未開始"}), 400

    # 這裡需要將複雜的 Python 對象轉換為 JSON 可序列化的數據結構
    player_hand_data = [
        {"id": p.player_id, "hand": p.hand, "melds": p.melds} 
        for p in game.players.values()
    ]

    return jsonify({
        "current_turn": game.current_turn,
        "discard_pile": game.discard_pile,
        "players": player_hand_data,
        "is_game_over": game.game_over
    })

@app.route('/action/discard', methods=['POST'])
def handle_discard():
    """處理玩家打牌的請求。"""
    if not game or game.game_over:
        return jsonify({"error": "遊戲無效"}), 400
        
    data = request.json
    tile = data.get('tile')
    player_id = data.get('player_id', game.current_turn)

    # 執行您的核心遊戲邏輯
    success = game.play_turn(tile)
    
    # 這裡可以加入檢查是否有人胡牌、碰、槓、吃等邏輯反饋
    
    return jsonify({
        "success": success,
        "message": f"玩家 {player_id} 打出 {tile}",
        "new_state": game.get_state_for_json() # 獲取更新後的狀態
    })

# ... 其他路由，如 /action/pong, /action/chow ...
if __name__ == '__main__':
    app.run()