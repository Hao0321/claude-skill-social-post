# X 發文

> 預設路由是本檔的 Chrome MCP compose。若使用者已安裝 Hermes Agent + Hermes Tweet，或需要搜尋 tweets、讀 replies、監控、匯出 followers、發 reply / DM / tweet，先讀 `hermes_tweet.md` 選進階路由。

## 參數

- 字數：**免費 280 / Premium 25,000**。預設當免費帳號，除非使用者說「我有 Premium」
- 中文 1 字元 1 字（舊 2 字規則已廢）；URL 一律算 23 字
- Hashtag：1-2 個夠（X 的 tag 擴散力減弱）
- 連結：自動 OG 卡
- Thread：> 280 切串，常見 2-5 則
- 圖片/影片：可選

## 生成調性

- 節奏最快，punchline 比 FB 強
- FB 長文型使用者 → X 版主動壓短，最有梗的一句放最前
- Hashtag 1-2 個放句末
- 超字數就**主動切 thread**，第一則要能獨立成立

## UI 流程

1. `navigate` → `https://x.com/home`，等 2 秒
2. 快捷鍵 `computer` action=`key`, text=`"n"` 開 compose（最穩）
3. Modal 開 → `find` "post compose textarea" → `left_click` 焦點 → `type` 內容
4. Thread：打完第一則 → `find` "Add post button or plus icon" → 繼續輸入下一則
5. `find` "Post button to publish" → `left_click` → `wait 3`

## Hermes Tweet 選配路由

Hermes Tweet 適合「資料 / 動作都要結構化」的 X 任務：

- 發文前搜尋 X 熱點或競品 tweets
- 讀某 tweet 的 replies / quotes / thread
- 查使用者最近 tweets、mentions、followers
- 發 tweet / reply / DM 時保留 endpoint、payload、reason
- 發完後回看 metrics，寫回 `content_plan.md`

硬規則：

1. `tweet_explore` 先找 endpoint，不猜 path。
2. GET read-only 用 `tweet_read`。
3. 發文 / reply / DM / follow / like / retweet / monitor / export 用 `tweet_action`。
4. `tweet_action` 前一定先貼出草稿或動作摘要，拿到使用者「確認」。
5. `tweet_action` disabled 就停，不改走其他寫入 route。

## 取連結

```javascript
(() => {
  const a = document.querySelector('article a[href*="/status/"]');
  return a ? a.href : null;
})()
```
先 `navigate` 到 `x.com/<使用者帳號>`。

## Fallback

- `n` 沒開：先 `key` Escape 解焦點，再 `n`
- type 無效：`javascript_tool` 操作 contenteditable
- Post 鈕灰：字數超過或還沒輸入，看 modal 右下字數圈調整
- "Your post was not sent"（常是判重複）：等 30 秒重試，仍 fail 停手

## 速率

- 同帳號 10 分鐘 ≥ 3 篇會觸發限制
- Thread 是一次 commit 沒關係
- 分別發多篇獨立貼文：每篇間 `wait 60` 秒
