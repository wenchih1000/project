// 假設這個函數能將牌張代碼 ('1m', 'We') 轉換為 HTML 圖像或樣式
function getTileHtml(tileCode, isSelectable = false) {
    // 實際應用中，這裡會返回 <img src="images/1m.png"> 或帶有 CSS 樣式的 <div>
    let className = isSelectable ? 'tile selectable' : 'tile';
    return `<div class="${className}" data-tile="${tileCode}">${tileCode}</div>`;
}

async function updateUI() {
    // 1. 呼叫 Flask API 獲取最新狀態
    console.log("updateUI");
    const response = await fetch('/get_state');
    const state = await response.json();

    if (state.error) {
        console.error(state.error);
        return;
    }

    // 2. 渲染當前玩家的手牌
    const myPlayer = state.players.find(p => p.id === state.current_turn);
    const handDiv = document.getElementById('my-hand-area');
    handDiv.innerHTML = ''; // 清空

    if (myPlayer) {
        myPlayer.hand.forEach(tile => {
            // 讓當前回合的玩家手牌可點擊打出
            const tileHtml = getTileHtml(tile, true);
            const tileElement = document.createElement('div');
            tileElement.innerHTML = tileHtml;
            tileElement.querySelector('.tile').addEventListener('click', () => handleTileClick(tile));
            handDiv.appendChild(tileElement);
        });
    }

    // 3. 渲染棄牌區
    const riverDiv = document.getElementById('discard-pile');
    riverDiv.innerHTML = state.discard_pile.map(tile => getTileHtml(tile, false)).join('');

    // 4. 根據遊戲狀態顯示或隱藏動作按鈕
    // ... 檢查是否可碰/吃，然後顯示相關按鈕 ...
}

function handleTileClick(tile) {
    // 呼叫 Flask 處理打牌動作
    fetch('/action/discard', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tile: tile, player_id: 0 }) // 假設玩家 ID 是 0
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            // 打牌成功後，立即更新 UI 顯示最新的狀態
            updateUI(); 
        } else {
            alert(data.message || "打牌失敗");
        }
    });
}

function renderWall() {
    const totalStacks = 18; // 每面牌牆 18 疊

    const wallTop = document.getElementById('wall-top');
    const wallBottom = document.getElementById('wall-bottom');
    const wallLeft = document.getElementById('wall-left');
    const wallRight = document.getElementById('wall-right');

    const stackHtml = `
        <div class="tile-stack">
            <div class="tile-back"></div>
            <div class="tile-back"></div>
        </div>
    `;

    let htmlContent = '';
    for (let i = 0; i < totalStacks; i++) {
        htmlContent += stackHtml;
    }

    wallTop.innerHTML = htmlContent;
    wallBottom.innerHTML = htmlContent;
    wallLeft.innerHTML = htmlContent;
    wallRight.innerHTML = htmlContent;
    
    // 注意: 實際應用中，您可能需要根據剩餘牌數來隱藏或改變某些牌疊的樣式。
    // 例如，當牌牆剩下 55 張 (約 14 疊) 時，您應該只渲染那些未被摸走的牌疊。
}

// 在您的 startGame 函式或頁面載入時呼叫
// renderWall();

// 遊戲啟動和定時刷新
function startGame() {
    fetch('/start_game', { method: 'POST' })
        .then(() => {
            updateUI();
            // 設置定時器，模擬多玩家遊戲時的狀態刷新
            setInterval(updateUI, 1000); 
        });

    renderWall();
}