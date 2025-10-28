# Client 與 Server 通訊協議

### 目的
讓 client 知道目前玩家當前的狀態，Server會主動告知Client，各玩家目前手牌情況和當前遊戲狀態，  
玩家當前可以做什麼動作。例如:胡/槓/碰/吃/過、摸牌/出牌。 

### Client 傳送玩家加入遊戲的請求
1. Client 傳送的JSON格式
```JSON
    {
        "join_game":{
            "name":"阿土伯",
            "avatar":"26.png"
        }
    },
    {
        "get_info":true
    }
```
2. Server 回傳的JSON格式
```JSON
    {
        "join_game":{
            "state":"waiting",
            "wait_num":3
        }
    },
    {
        "info":[
            {
                "name":"阿土伯",
                "avatar":"26.png",
                "seat":"east",
                "cid":"123456"
            }
        ]
    }
```
3. 加入遊戲(join_game)JSON參數說明

| 欄位 | 型別 | 說明 | 備註 |
|:--|:--|:--|:--|
| name | str | 玩家名稱 | 中文名字長度最多10個字 |
| avatar | str | 玩家頭像 | 從 images 資料夾中選取 |
| state | str | 加入遊戲的狀態 |  waiting, full, playing |
| wait_num | int | 當前等待人數 | 0~3人 |

4. 玩家資訊(info)JSON參數說明

| 欄位 | 型別 | 說明 | 備註 |
|:--|:--|:--|:--|
| name | str | 玩家名稱 | 中文名字長度最多10個字 |
| avatar | str | 玩家頭像 | 從 images 資料夾中選取 |
| seat | str | 玩家座位 | east, south, west, north |
| cid | int | 玩家ID | Client ID |

5. 獲得所有玩家資訊(get_info)JSON參數

| 欄位 | 型別 | 說明 | 備註 |
|:--|:--|:--|:--|
| get_info | bool | 取得所有玩家資訊 | 在斷線重新連線時使用 |

### Server 檢查後，通知Client該玩家目前可操作的狀態和手牌情況
1. Server 傳送的JSON格式  
```JSON
    {
        {   // 通知遊戲開始時，隨機決定玩家座位
            "player_seat":{
                "east":"阿土伯","south":"柯南","west":"黑傑克","north":"一枝花"
            }
        },
        {   // 通知遊戲狀態
            "game_state":{
                "round_wind":"east",
                "dealer_wind":"east",
                "current_player":"north",
                "dealer_num":0,
                "dice_score":[1,1,1]
            },
            "game_result":{
                "state":"running", // running, waiting, draw_game, win_game, end_game
                "result":"wall_empty" // dead_wall_empty
            }
        },
        {   // 通知當前玩家進行什麼動作
            "notify":"east",
            "action_state":{
                "dice":false, "drawing":false, "discard":false,
                "hu":false, "kong":false, "pong":false, "chow":false, "pass":false
            }
        },
        {   // 通知所有玩家, 當前玩家活動在做什麼動作
            "notify":"all",
            "player_state":{
                "whoes_turn":"north",
                "action":"drawing"
            }
        },
        {   // 通知所有玩家手牌情況
            "notify":"all",
            "hand_tiles":[
                {
                    "seat":"east",
                    "hand":["1C", "2C", "3C", "3D", "4D", "5D", "6D", "7D", "8D", "1A"],
                    "drawed":"3A"
                }, 
                {
                    "seat":"south",
                    "hand":["3C", "4C", "5C", "3S", "4S", "5S", "6S", "7S", "8S", "4W", "2A", "2A", "2A"],
                    "drawed":""
                }, 
                {
                    "seat":"west",
                    "hand":["5C", "6C", "7C", "8C", "8C", "8C", "2S", "3S", "4S", "6S", "7S", "8S", "4W", "4W", "4W", "3A"],
                    "drawed":""
                }, 
                {
                    "seat":"north",
                    "hand":["2D", "3D", "4D", "6S", "7S", "8S", "9S", "9S", "9S", "3W"],
                    "drawed":""
                }
            ]
        },
        {   // 通知當前玩家手牌情況
            "notify":"east",
            "hand_tiles":[
                {
                    "hand":["1C", "2C", "3C", "3D", "4D", "5D", "6D", "7D", "8D", "1A"],
                    "drawed":"3A",
                    "wait":["1A"] // 聽牌中，單聽1A
                }
            ]
        }
        {   // 通知所有玩家外露牌情況, 在hide欄位1X代表蓋牌, 不讓其他玩家知道是蓋什麼牌
            "notify":"all",
            "out_tiles":[
                {
                    "seat":"east",
                    "meld":[],
                    "hide":[["1X","1X","1X","1X"],["1X","1X","1X","1X"]],
                    "flower":["1G", "3G"],
                    "discard":["6s", "3W"]
                }, 
                {
                    "seat":"south",
                    "meld":[["2W", "2W", "2W"]],
                    "hide":[],
                    "flower":[ "2G"],
                    "discard":["3W"]
                }, 
                {
                    "seat":"west",
                    "meld":[],
                    "hide":[],
                    "flower":["1P", "2P"],
                    "discard":["1A", "2W"]
                }, 
                {
                    "seat":"north",
                    "meld":[["6D", "7D", "8D"],["9D", "9D", "9D", "9D"]],
                    "hide":[],
                    "flower":[],
                    "discard":[]
                }
            ]
        },
        {   // 通知當前玩家外露牌情況
            "notify":"east",
            "out_tiles":[
                {
                    "meld":[],
                    "hide":[["9C","1X","1X","1X"], ["1W","1X","1X","1X"]],
                    "flower":["1G", "3G"],
                    "discard":["6s", "3W"]
                } 
            ]
        },
        {   // 通知所有玩家自摸胡牌情況
            "notify":"all",
            "hu_tiles":[
                {
                    "seat":"north",
                    "discard_seat":"",
                    "hand":["3D", "4D", "5D", "6D", "7D", "8D", "3A"],
                    "drawed_win":"3A",
                    "discard_win":"",
                    "rob_win":"",
                    "meld":[["1C", "2C", "3C"]],
                    "hide":[["9C","1X","1X","1X"], ["1W","1X","1X","1X"]],
                    "flower":["1G", "3G"]
                }
            ]
        },
        {   // 通知所有玩家吃胡牌(放槍)情況
            "notify":"all",
            "hu_tiles":[
                {
                    "seat":"north",
                    "discard_seat":"east",
                    "hand":["3D", "4D", "5D", "6D", "7D", "8D", "1A"],
                    "drawed_win":"",
                    "discard_win":"1A",
                    "rob_win":"",
                    "meld":[["1C", "2C", "3C"]],
                    "hide":[["9C","1X","1X","1X"], ["1W","1X","1X","1X"]],
                    "flower":["1G", "3G"]
                }
            ]
        },
        {   // 通知所有玩家搶槓胡牌情況
            "notify":"all",
            "hu_tiles":[
                {
                    "seat":"north",
                    "discard_seat":"east",
                    "hand":["3D", "4D", "5D", "6D", "7D", "8D", "1A"],
                    "drawed_win":"",
                    "discard_win":"",
                    "rob_win":"1A",
                    "meld":[["1C", "2C", "3C"]],
                    "hide":[["9C","1X","1X","1X"], ["1W","1X","1X","1X"]],
                    "flower":["1G", "3G"]
                }
            ]
        }
    }
```
 
2. 遊戲狀態(game_state)JSON參數說明

| 欄位 | 型別 | 說明 | 備註 |
|:--|:--|:--|:--|
| round_wind | str | 局風位 | east, south, west, north |
| dealer_wind | str | 莊家風位 | east, south, west, north |
| current_player | str | 當前回合的玩家 | east, south, west, north |
| dealer_num | int | 第幾莊 | 莊家連莊 |
| dice_score | list [ int ] | 莊家擲骰子點數 | 共3顆骰子:3~18點 |

3. 遊戲結果(game_result)JSON參數說明

| 欄位 | 型別 | 說明 | 備註 |
|:--|:--|:--|:--|
| state | str | 遊戲狀態 | running, waiting, draw_game, win_game, end_game |
| result | str | 遊戲結果 | wall_empty, dead_wall_empty, draw_win, discard_win |

3. 活動狀態(action_state)JSON參數說明

| 欄位 | 型別 | 說明 | 備註 |
|:--|:--|:--|:--|
| dice | bool | 擲骰子 | false:按鈕disable, true:按鈕enable |
| drawing | bool | 摸牌  | false:按鈕disable, true:按鈕enable |
| discard | bool | 出牌  | false:按鈕disable, true:按鈕enable |
| hu | bool | 胡牌  | false:按鈕disable, true:按鈕enable |
| kong | bool | 槓牌  | false:按鈕disable, true:按鈕enable |
| pong | bool | 碰牌  | false:按鈕disable, true:按鈕enable |
| chow | bool | 吃牌  | false:按鈕disable, true:按鈕enable |
| pass | bool | 過牌  | false:按鈕disable, true:按鈕enable |

4. 玩家狀態(player_state)JSON參數說明

| 欄位 | 型別 | 說明 | 備註 |
|:--|:--|:--|:--|
| whoes_turn | str | 當前回合的玩家 | east, south, west, north |
| action | str | 正在做的事 | dice, drawing, discard, hu, kong, pong, chow, pass |

5. 通知玩家(notify)JSON參數說明

| 欄位 | 型別 | 說明 | 備註 |
|:--|:--|:--|:--|
| notify | str | 通知對象, all:所有玩家 | all, east, south, west, north |

6. 手牌(hand_tiles)JSON參數說明

| 欄位 | 型別 | 說明 | 備註 |
|:--|:--|:--|:--|
| seat | str | 玩家座位 | east, south, west, north |
| hand | list [ str ]  | 玩家手牌 | 玩家自已看的牌 |
| drawed | str | 玩家摸到的牌 | |
| wait | list [ str ] | 聽牌清單 | 玩家聽哪些牌 |

7. 外露牌(out_tiles)JSON參數說明

| 欄位 | 型別 | 說明 | 備註 |
|:--|:--|:--|:--|
| seat | str | 玩家座位 | east, south, west, north |
| meld | list [ list [ str ] ] | 玩家的搭子 | 玩家外露的搭(吃/碰/槓) |
| hide | list [ list [ str ] ] | 玩家暗槓 | 玩家暗槓的搭組 |
| flower | list  [ str ] | 玩家花牌 |  |
| discard | list [ str ] | 玩家棄牌 | 玩家丟棄在牌桌上的牌 |

8. 胡牌(hu_tiles)JSON參數說明

| 欄位 | 型別 | 說明 | 備註 |
|:--|:--|:--|:--|
| seat | str | 胡牌玩家座位 | east, south, west, north |
| discard_seat | str | 放槍玩家座位 | east, south, west, north |
| hand | list [ str ] | 玩家手牌 | 玩家手上的牌 |
| drawed_win | str | 玩家自摸 | 玩家自已摸到的牌 |
| discard_win | str | 閒家放槍 | 閒家丟棄在牌桌上的牌 |
| meld | list [ list [ str ] ] | 玩家的搭子 | 玩家外露的搭(吃/碰/槓) |
| hide | list [ list [ str ] ] | 玩家暗槓 | 玩家暗槓的搭組 |
| flower | list  [ str ] | 玩家花牌 |  |

9. 牌的字串格式

| 字串 | 牌名 | 備註 |  
|:--|:--|:--|  
| 1C~9C | 1萬~9萬 | Char 萬牌  |  
| 1D~9D | 1筒~9筒 | Dot 筒牌 |  
| 1S~9S | 1索~9索 | Stick 索牌 |  
| 1W~4W | 東南西北 | Wind 風牌 |  
| 1A~3A | 中發白 | Arrow 箭牌/三元牌 |  
| 1G~4G | 梅蘭竹菊 | Gentlemen 花牌/四君子牌 |  
| 1P~4P | 春夏秋冬 | Period 花牌/四季牌 |
| 1X | 蓋 | Hide 蓋牌 |
  
### Client 回應 Server 玩家決定要做的動作
1. Client 傳送的JSON格式  
```JSON
    // 過
    {
        "player":"east",
        "action":"pass"
    }

    // 吃牌
    {
        "player":"east",
        "action":"chow",
        "tiles":["5D", "7D"]
    }

    // 碰牌
    {
        "player":"east",
        "action":"pong",
        "tiles":["2A", "2A"]
    }

    // 槓牌
    {
        "player":"east",
        "action":"kong",
        "tiles":["2W", "2W", "2W"]
    }

    // 胡牌
    {
        "player":"east",
        "action":"hu",
    }

    // 擲骰子
    {
        "player":"east",
        "action":"dice"
    }

    // 出牌
    {
        "player":"east",
        "action":"discard",
        "tiles":["9D"]
    }

    // 摸牌
    {
        "player":"east",
        "action":"drawing"
    }

    // 取手牌
    {
        "player":"east",
        "action":"get_hand"
    }
```
2. Client 回應 Server 玩家決定要做的動作

| 欄位 | 型別 | 說明 | 備註 |
|:--|:--|:--|:--|
| player | str | 當前玩家 | east, south, west, north |
| action | str | 要做的事 | dice, drawing, discard, hu, kong, pong, chow, pass |
| tiles | list [ str ] | 玩家手中要組成的牌 | 槓/碰/吃, 出牌的牌 |

### 玩家胡牌時 Server 計算台數後，通知 Client 計算結果

1. Server 傳送的JSON格式
```JSON
    {
        "result":{
            "player":"south",
            "hand":["3C", "4C", "5C", "3S", "4S", "5S", "6S", "7S", "8S", "4W", "4W", "4W", "2A", "2A", "2A", "1A", "1A"],
            "round_wind":"east",
            "dealer_wind":"east",
            "win_type":"自摸",
            "dealer_num":3,
            "score_list":[
                {"name":"三暗刻", "value":2},
                {"name":"莊家", "value":1},
                {"name":"連莊(連3拉3)", "value":6},
                {"name":"門清自摸", "value":3},
                {"name":"獨聽(中洞)", "value":1},
                {"name":"圈風(南風)", "value":1},
                {"name":"門風(東風)", "value":1},
                {"name":"正花(蘭)", "value":1},
                {"name":"花槓(梅蘭竹菊)", "value":1},
                {"name":"正花(夏)", "value":1},
                {"name":"花槓(春夏秋冬)", "value":1}
            ],
            "total_score":19,
            "before_money":[8000, 6000, 9000, 5000],
            "after_money":[1000, 6000, 9000, 12000]
        }
    }
```
2. 結果(result)JSON參數說明

| 欄位 | 型別 | 說明 | 備註 |
|:--|:--|:--|:--|
| player | str | 胡牌玩家 | east, south, west, north |
| hand | list [ str ] | 手牌 | 玩家胡的牌型 |
| round_wind | str | 局風位 | east, south, west, north |
| dealer_wind | str | 莊家風位 | east, south, west, north |
| win_type | str | 胡牌牌型 | self-drawn(自摸), discard-win(放槍) |
| dealer_num | int | 第幾莊 | 莊家連莊 |
| score_list | dict | 玩家胡牌台型 | name獲得的台型，value獲得的台數 |
| total_score | int | 玩家獲得的總台數 | |
| before_money | list [ int ] | 4位玩家原本的金額 | east, south, west, north |
| after_money | list [ int ] | 4位玩家計算後的金額 | east, south, west, north |
