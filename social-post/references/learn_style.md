# Phase 1：學風格（FB 爬取 + 分析）

## 1. 問網址

問使用者 FB 個人頁網址（`facebook.com/username` 或 `facebook.com/profile.php?id=...`）。**不要猜、不要搜尋**。拿到後確認是 `facebook.com` 開頭。

## 2. 導航 + 捲動（重要：FB 個人頁虛擬化）

`navigate` 到使用者網址，等 2 秒。**FB 個人頁會虛擬化捲過的貼文（從 DOM 卸載），要邊捲邊抓，不能先滾完再抓。**

捲動要**滑鼠 hover 在右欄 compose/貼文區**（座標大約 `x=985, y=500`），而不是左欄（左欄是個人資料/朋友/相片，不會觸發 posts 載入）。

```
computer(action="scroll", coordinate=[985, 500], scroll_direction="down", scroll_amount=10)
wait 2 秒
```

## 3. 抓貼文（優先 JS，fallback `get_page_text`）

### 踩過的雷

- `[role="article"]` **同時 match 貼文和留言**，不能當唯一選擇器
- 連續 `a[href*="/posts/"]` 會抓到 comment permalink（`?comment_id=` 參數）
- FB class name 已 obfuscated，不可靠
- 時間戳文字被 obfuscate 成亂碼（例：`sdSntoroep41tu363hf0a午5ci0663ml451...`），但正文還是乾淨的

### 可用策略（邊捲邊抓 + 去重）

**每捲 10-15 ticks，執行一次**：

```javascript
(() => {
  const out = [];
  document.querySelectorAll('[role="article"]').forEach(el => {
    const msgEl = el.querySelector('[data-ad-preview="message"], [data-ad-comet-preview="message"]');
    if (!msgEl) return;  // 沒訊息容器的（多半是留言）跳過
    const body = msgEl.innerText.trim();
    if (body.length < 8) return;  // 太短多半是系統訊息
    const authorEl = el.querySelector('h2 a, h3 a, h4 a, strong a');
    const author = authorEl ? authorEl.innerText.trim() : '';
    out.push({ author, body: body.slice(0, 500) });
  });
  return JSON.stringify(out);
})()
```

把結果累積到記憶體集合（用 body 前 50 字當 key 去重）。**只保留 author === 使用者名字 的貼文**（被 tag / 分享 / 別人牆貼都跳過）。

### Fallback：JS 拿空陣列 / 少於預期

改用 `get_page_text(tabId)`。FB 會把貼文內容連在一起回傳，但**時間戳被 obfuscate 成亂碼**，只要抓正文即可。用「駱君昊」（或使用者名字）重複出現當貼文分界。

### 載不動的情況

docH 不再變大、底部出現 skeleton 但不解析 → FB 停止 feed 投放（可能虛擬化邊界、也可能 rate limit）。連續兩次 scroll 後 article 數不增加就停手，改用目前已收的樣本分析。

## 4. 目標數

**≥ 20 篇乾淨貼文**。若載不到，以實際收到的數量為準，在 `style_profile.md` 註明。

## 5. 分析面向

逐篇讀，不要只看字頻。要萃取：

| 面向 | 關鍵提問 |
|---|---|
| 語氣 | 正式/口語/幽默/抒情/碎念？混幾種？ |
| 句長 | 短/中/長？混搭比例？ |
| 標點 | 驚嘆號連發？全/半形？省略號是 `…` 還是 `....` 還是 `⋯⋯`？|
| 開頭 | 公告型/時間錨/反思/情緒爆點/問句？ |
| 收尾 | 問句/emoji/召集/punchline？ |
| Emoji | 頻率、偏好組合、位置 |
| 主題 | 比例 |
| Hashtag | 用/不用/怎麼用 |
| 人稱 | 我/我們的使用 |
| 禁忌 | 沒出現什麼 |
| **高參與度模式** | 讚數明顯高的幾篇有沒有共同結構？ → 寫成 Mode B 模板 |

## 6. 寫入 `style_profile.md`

完整覆寫，但**保留 `<!-- user-edit -->` 以下的使用者自訂段**（如果既有檔案有）。

格式參考 `style_profile.example.md`：一句話語氣、句式、標點、開頭/收尾、emoji、主題、hashtag、人稱、避免領域、兩種模式的 few-shot 原文、身分線索。

## 7. 給使用者 3 條確認重點

用 3 個 bullet 摘要最顯著特徵，問「準嗎？哪裡歪了直接說。」

- 「準」→ 結束
- 「A 不對應該是 B」→ 對應段落改寫再存
- 「樣本太舊」→ 建議重抓
