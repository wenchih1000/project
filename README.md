### 前言
開發此遊戲主要是教育性旨為目的，讓 DDE330 軟體人員可以藉由此架構學習到軟體相關開發模式。  

1. 資料結構
2. 物件導向
3. 設計模式(MVC 架構)
4. 多人連線(SockIO)
5. 前端/後端基礎應用架構

---
  
### 遊戲架構職責劃分

| 職責 | 類別 / 模塊 | 英文名稱 | 說明 |
|:--|:--|:--:|:--|
| 牌 | Tile  | Mahjong Tile | 負責定義麻將牌的種類:萬、筒、索、風牌、三元牌、花牌。  |
| 牌組 | Deck |	Mahjong Deck | 負責牌牆的生成、洗牌、發牌、摸牌（包括死牌區/嶺上牌）等管理。 |
| 玩家手牌 | Player / Hand | Mahjong Player | 負責追蹤單個玩家的狀態：手牌、外露的吃/碰/槓搭子、分數、花牌、過水狀態等。 |
| 規則 | Rule | Mahjong Rule | 定義Taiwan麻將規則，檢查手上牌符合哪些胡牌情況，包含:聽牌、胡牌，吃、碰、槓 |
| 計算台數 | Score / Calculate | Tai Calculator | 專門負責判斷牌型（如清一色、天胡）以及計算最終的台數和結算金額。 |
| 流程控制 | Controller | Game Controller | 負責串聯所有邏輯：管理回合、處理動作優先級 (吃/碰/槓/胡)、呼叫 MahjongDeck 摸牌、呼叫 TaiCalculator 結算。 | 
| 圖形介面 | View | templates/*.html & static/*.js/css | flask 負責視覺呈現。 接收 Controller 傳來的遊戲狀態數據，使用 HTML 結構、CSS 樣式和 JavaScript 動態渲染出您設計的麻將牌桌 UI。 |
  
### 詳細職責對應
| 核心元件 | 所屬層 | 具體職責 |
|:--|:--:|:--|
| MahjongDeck | Model | 牌牆生成、洗牌、摸牌 (含嶺上牌)。 |
| Player | Model | 追蹤手牌、外露搭子、分數、過水狀態。 |
| TaiCalculator | Model | 胡牌結構解析、台數計算、流局結算。 |
| MahjongGame | Controller | 回合管理、動作優先級判斷 (resolve_claims)、遊戲流程控制。 |
| app.py 路由 | Controller | 處理 /get_state、/action/discard 等 API，橋接前後端。 |
| templates/game.html | View | 包含牌桌的靜態 HTML 結構和 Jinja2 模板變量。 |
| static/game.js | View	| 接收 JSON 數據，呼叫 Flask API，動態渲染牌張、處理點擊事件 (打牌、碰、吃)。 |
| static/style.css | View | 處理牌桌的佈局、牌張的樣式、四方對稱排版。 |

---