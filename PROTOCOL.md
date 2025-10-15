# Client 與 Server 通訊協議

### 目的
讓 client 知道目前玩家當前的狀態，Server會主動告知Client，各玩家目前手牌情況和當前遊戲狀態，  
玩家當前可以做什麼動作。例如:胡/槓/碰/吃/過、摸牌/出牌。 

### Server 檢查後，通知Client該玩家目前可操作的狀態和手牌情況
1. Server 傳送的JSON格式  

        {
            "game_state":{
                "round_wind":"east",
                "dealer_wind":"east",
                "current_player":"north",
                "dealer_num":0,
                "dice_score":9
            },
            "action_state":{
                "player":"east",
                "drawing":False, "discard":False,
                "hu":False, "kong":False, "pong":False, "chow":False, "pass":False
            },
            "hand_tiles":{
                "east":{
                    "hand":["1C", "2C", "3C", "3D", "4D", "5D", "6D", "7D", "8D", "1A"],
                    "meld":[],
                    "conceal":[["9C", "9C", "9C", "9C"], ["1W", "1W", "1W", "1W"]],
                    "flower":["1G", "3G"],
                    "discard":["6s", "3W"],
                    "drawed":"3A"
                }, 
                "south":{
                    "hand":["3C", "4C", "5C", "3S", "4S", "5S", "6S", "7S", "8S", "4W", "2A", "2A", "2A"],
                    "meld":[["2W", "2W", "2W"]],
                    "conceal":[],
                    "flower":[ "2G"],
                    "discard":["3W"],
                    "drawed":""
                }, 
                "west":{
                    "hand":["5C", "6C", "7C", "8C", "8C", "8C", "2S", "3S", "4S", "6S", "7S", "8S", "4W", "4W", "4W", "3A"],
                    "meld":[],
                    "conceal":[],
                    "flower":["1P", "2P"],
                    "discard":["1A", "2W"],
                    "drawed":""
                }, 
                "north":{
                    "hand":["2D", "3D", "4D", "6S", "7S", "8S", "9S", "9S", "9S", "3W"],
                    "meld":[["6D", "7D", "8D"],["9D", "9D", "9D", "9D"]],
                    "conceal":[],
                    "flower":[],
                    "discard":[],
                    "drawed":""
                }
            }
        }

2. 遊戲狀態(game_state)

| 欄位 | 型別 | 說明 | 備註 |
|:--|:--|:--|:--|
| round_wind | str | 局風位 | east, south, west, north |
| dealer_wind | str | 莊家風位 | east, south, west, north |
| current_player | str | 當前回合的玩家 | east, south, west, north |
| dealer_num | int | 第幾莊 | 莊家連莊 |
| dice_score | int | 莊家擲骰子點數 | 共3顆骰子:3~18點 |

3. 活動狀態(action_state)

| 欄位 | 說明 | 備註 |
|:--|:--|:--|
| player | 當前玩家 | east, south, west, north |
| drawing | 摸牌  | false:按鈕disable, true:按鈕enable |
| discard | 出牌  | false:按鈕disable, true:按鈕enable |
| hu | 胡牌  | false:按鈕disable, true:按鈕enable |
| kong | 槓牌  | false:按鈕disable, true:按鈕enable |
| pong | 碰牌  | false:按鈕disable, true:按鈕enable |
| chow | 吃牌  | false:按鈕disable, true:按鈕enable |
| pass | 過牌  | false:按鈕disable, true:按鈕enable |

4. 手牌(hand_tiles)

| 欄位 | 型別 | 說明 | 備註 |
|:--|:--|:--|:--|
| east | dict | 東風玩家 | |
| south | dict | 南風玩家 | |
| west | dict | 西風玩家 | |
| north | dict | 北風玩家 | |
| hand | list | 玩家手牌 | 玩家自已看的牌 |
| meld | list | 玩家的搭子 | 玩家外露的搭(吃/碰/槓) |
| conceal | list | 玩家暗槓 | 玩家暗槓的搭組 |
| flower | list | 玩家花牌 |  |
| discard | list | 玩家棄牌 | 玩家丟棄在牌桌上的牌 |
| drawed | str | 玩家摸到的牌 | |

5. 牌的字串格式

| 字串 | 牌名 | 備註 |  
|:--|:--|:--|  
| 1C~9C | 1萬~9萬 | Char 萬牌  |  
| 1D~9D | 1筒~9筒 | Dot 筒牌 |  
| 1S~9S | 1索~9索 | Stick 索牌 |  
| 1W~4W | 東南西北 | Wind 風牌 |  
| 1A~3A | 中發白 | Arrow 箭牌/三元牌 |  
| 1G~4G | 梅蘭竹菊 | Gentlemen 花牌/四君子 |  
| 1P~4P | 春夏秋冬 | Period 花牌/四季牌 |  

  
### Client 回應 Server 玩家決定要做的動作
1. Client 傳送的JSON格式  

        // 過
        {
            "action_state":{
                "player":"east",
                "drawing":False, "discard":False,
                "hu":False, "kong":False, "pong":False, "chow":False, "pass":True
            },
            "tiles":[]
        }

        // 吃牌
        {
            "action_state":{
                "player":"east",
                "drawing":False, "discard":False,
                "hu":False, "kong":False, "pong":False, "chow":True, "pass":False
            },
            "tiles":["5D", "7D"]
        }

        // 碰牌
        {
            "action_state":{
                "player":"east",
                "drawing":False, "discard":False,
                "hu":False, "kong":False, "pong":True, "chow":False, "pass":False
            },
            "tiles":["2A", "2A"]
        }

        // 槓牌
        {
            "action_state":{
                "player":"east",
                "drawing":False, "discard":False,
                "hu":False, "kong":True, "pong":False, "chow":False, "pass":False
            },
            "tiles":["2W", "2W", "2W"]
        }

        // 胡牌
        {
            "action_state":{
                "player":"east",
                "drawing":False, "discard":False,
                "hu":True, "kong":False, "pong":False, "chow":False, "pass":False
            },
            "tiles":[]
        }

        // 出牌
        {
            "action_state":{
                "player":"east",
                "drawing":False, "discard":True,
                "hu":False, "kong":False, "pong":False, "chow":False, "pass":False
            },
            "tiles":["9D"]
        }

        // 摸牌
        {
            "action_state":{
                "player":"east",
                "drawing":True, "discard":False,
                "hu":False, "kong":False, "pong":False, "chow":False, "pass":False
            },
            "tiles":[]
        }

2. 活動狀態(action_state)

| 欄位 | 說明 | 備註 |
|:--|:--|:--|
| player | 當前玩家 | east, south, west, north |
| drawing | 摸牌  | 玩家決定摸牌 |
| discard | 出牌  | 玩家決定出牌 |
| hu | 胡牌  | 玩家決定胡牌 |
| kong | 槓牌  | 玩家決定槓牌 |
| pong | 碰牌  | 玩家決定碰牌 |
| chow | 吃牌  | 玩家決定吃牌 |
| pass | 過牌  | 玩家決定過牌 |
| tiles | 玩家手中要組成的牌 | 槓/碰/吃, 出牌的牌 |


### 玩家胡牌時 Server 計算台數後，通知 Client 計算結果

1. Server 傳送的JSON格式

        "result":{
            "player":"south",
            "hand":["3C", "4C", "5C", "3S", "4S", "5S", "6S", "7S", "8S", "4W", "4W", "4W", "2A", "2A", "2A", "1A", "1A"],
            "round_wind":"east",
            "dealer_wind":"east",
            "win_type":"self-drawn" //discard-win
            "dealer_num":3,
            "score_list":[
                {"name":"三暗刻", value:2},
                {"name":"莊家", value:1},
                {"name":"連莊(連3拉3)", value:6},
                {"name":"門清自摸", value:3},
                {"name":"獨聽(中洞)", value:1},
                {"name":"圈風(南風)", value:1},
                {"name":"門風(東風)", value:1},
                {"name":"正花(蘭)", value:1},
                {"name":"花槓(梅蘭竹菊)", value:1},
                {"name":"正花(夏)", value:1},
                {"name":"花槓(春夏秋冬)", value:1}
            ],
            "total_score":19,
            "before_money":[8000, 6000, 9000, 5000],
            "after_money":[1000, 6000, 9000, 12000]
        }

2. 結果(result)

| 欄位 | 型別 | 說明 | 備註 |
|:--|:--|:--|:--|
| player | str | 胡牌玩家 | east, south, west, north |
| hand | list | 手牌 | 玩家胡的牌型 |
| round_wind | str | 局風位 | east, south, west, north |
| dealer_wind | str | 莊家風位 | east, south, west, north |
| win_type | str | 胡牌牌型 | self-drawn(自摸), discard-win(放槍) |
| dealer_num | int | 第幾莊 | 莊家連莊 |
| score_list | dict | 玩家胡牌台型 | name獲得的台型，value獲得的台數 |
| total_score | int | 玩家獲得的總台數 | |
| before_money | list | 4位玩家原本的金額 | east, south, west, north |
| after_money | list | 4位玩家計算後的金額 | east, south, west, north |
