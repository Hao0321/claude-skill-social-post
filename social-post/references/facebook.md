# Facebook 發文

## 參數

- 字數：實務 ≤ 500 字（超過折疊「顯示更多」）
- Hashtag：0-2 個（FB 氛圍不靠 tag 擴散）
- 圖片：0-多張，多張 ≤ 10
- 連結：自動抓 OG 預覽，可從文字刪除原 URL 只留預覽卡
- 排版：換行、emoji，**無 markdown**

## 生成調性

- 長敘事 OK，沿 `style_profile.md` 段落偏好
- 爆款 F6 用四段式（成果炸場 / 教學引流 / 邀請碼 / 合作）
- hashtag 少或無

## UI 流程（2026-04 實證：新版是三步式）

1. `navigate` → `https://www.facebook.com/`，等 2 秒
2. `find` "status update input that says 在想些什麼 / What's on your mind" → `left_click` 開 modal
3. 在 `建立貼文` modal 內 `find` "post compose textarea" → `left_click` 焦點 → `type` 內容（`\n` 換行，可連續 `！！！`）
4. 若有圖：告知使用者「請把圖拖進剛開的 compose modal，傳完回我『圖已加』」，等回應
5. **點「繼續」**（不是「發佈」！新版多一步）：`find` "繼續 Continue button" → `left_click`
6. 進到 `貼文設定` 頁（audience / 排程 / 分享到社團 / 加強推廣）。使用者沒特別要求就直接往下
7. 可能要 `scroll` 一下讓「發佈」鈕可見：`scroll` down 3 ticks
8. `find` "發佈 Publish button at bottom right" → `left_click` → `wait 4`
9. 回到動態牆，首頁第一篇即剛發

## 確認發佈成功

- **最可靠**：回首頁 `facebook.com/`，最新一篇應顯示「剛剛」時間戳
- **個人頁 profile 會延遲幾分鐘**才出現新貼文。有 Meta AI Manus 推廣框會把最新貼文當預覽（下方標「只有你可以看到這則貼文」）——那不是真貼文，只是 FB 的 ad preview
- 取 permalink：profile 同步後才能拿到；立即需要就跳過，回報「✓ 已發（permalink 尚未生成）」

## 取連結

```javascript
(() => {
  const a = document.querySelector('[role="article"] a[href*="/posts/"], [role="article"] a[href*="/permalink/"]');
  return a ? a.href.split('?')[0] : null;
})()
```

## Fallback

- `find` 失敗：換口語化 query（「where it asks what's happening」「publish button」），仍不行就 `read_page(filter="interactive")` 找 ref
- `type` 無效（contenteditable 沒吃）：`javascript_tool` 直接改 `innerText` + dispatch `input` event
- Modal 沒關：等 5 秒；有紅字錯誤就停手告知
- 蓋版彈窗（cookie / 生日 / 社團）：先 `read_page(filter="interactive")` 看有沒有，有就先關

## 留言輸入大雷（2026-04-21 翻車實證）

**FB 留言框的 Enter = 送出，不是換行**。使用 `type` 動作時：
- 內容含 `\n` → 每個 `\n` 都會觸發送出，一則想要分段的留言會被拆成 N 則獨立留言
- 一口氣貼多行內容 = 連續送出多則殘片，中間還會插入空留言

**正確做法（擇一）**：
- **單行輸入**：把想發的留言全部壓成一行，用 `，` 或 `／` 或 `→` 分隔不同段，不要用 `\n`
- **或**：每段內容分別用 `type`（不含換行）送出，之間 `wait 1` 秒。但這仍會產生多則留言，不建議
- **連結預覽**：FB 會自動抓 link preview 卡片，所以 URL 放同一行裡就好，不需要單獨一行

**範例**：

❌ 壞的：
```
嘿大家求連結的，我統一放在這裡 👇

Claude Code 台灣交流討論區：
https://line.me/ti/g2/...

加入後自我介紹一下
```

✅ 好的（單行版）：
```
嘿大家求連結的，統一放這裡 → Claude Code 台灣交流討論區：https://line.me/ti/g2/... ，加入後自我介紹，裡面很多大神在等你交流🔥
```

這個規則**同樣適用於 Threads / Instagram / X 的留言框**，compose modal 另論（compose 的 textbox 通常接受 `\n`，留言框不行）。

## 發前檢查

- Modal 右上隱私下拉：沿用預設，使用者沒明說就不改

## FB 原生排程（推薦用在 24h 冷卻卡點）

FB 的「貼文設定」頁有「排程選項」（預設：立即發佈）。**當使用者要在未來特定時間自動發**（例：爆款滿 24h 接演算法），用 FB 原生排程而非自己寫 cron。流程：

1. 打字完→點「繼續」進「貼文設定」頁
2. 點「排程選項」（顯示「立即發佈」）
3. 彈出「排程選項」dialog：
   - 日期預設明天，時間預設當前 +1h
   - 改時間：`triple_click` 時間欄 → `type` 「HH:MM」→ 從下拉建議點確認
4. 點「排定稍後通話」/「排定」按鈕（藍色；FB 中文顯示有時怪）
5. 回到「貼文設定」頁，排程選項顯示「明天上午 HH:MM」
6. 底部按鈕變「儲存 / **排定時間**」（不再是立即發佈）
7. 點「排定時間」→ 左下出「你的貼文已排定發佈時間」toast = 完成

**好處**：
- 不需要我的 cron / wake-up 腳本；FB 自己送出
- 使用者「確認」在設排程時給（符合 skill 硬規則），發佈行為在排定時間由 FB 執行
- 使用者不用熬夜、不用筆電一直開 Claude Code

**注意**：
- 首頁會看到「駱君昊 N 小時後」的排程預覽，只有自己看得到
- 排程後可在首頁左下的 toast「檢視」或個人頁「管理貼文」找到排程列表，可編輯或取消
