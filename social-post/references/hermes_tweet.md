# Hermes Tweet X 路由

這是 **X 的選配進階路由**。預設仍可照 `x.md` 用 Chrome MCP 發文；當使用者已安裝 Hermes Agent + Hermes Tweet，或需要結構化搜尋、監控、讀回覆、匯出 followers、發 reply / DM / tweet 時，改讀本檔。

## 何時用

| 使用者需求 | 路由 |
|---|---|
| 只要手動填 X compose | `x.md` Chrome MCP |
| 搜尋 tweets / social listening | Hermes Tweet `tweet_read` |
| 查 tweet 詳情、回覆、quote、retweeter | Hermes Tweet `tweet_read` |
| 查使用者、最近 tweets、mentions、followers | Hermes Tweet `tweet_read` |
| 建監控、匯出、抽獎、下載 media | Hermes Tweet `tweet_action`（需確認）|
| 發 tweet / reply / DM / follow / like / retweet | Hermes Tweet `tweet_action`（需確認）|

## 安裝

使用者在 Hermes Agent 裝 plugin：

```bash
hermes plugins install Xquik-dev/hermes-tweet --enable
hermes tools list
```

互動安裝會提示 `XQUIK_API_KEY`。非互動環境要先把 key 放在 Hermes runtime environment 或 `~/.hermes/.env`。

不要叫使用者把 API key 貼到對話。只提醒：

```bash
export XQUIK_API_KEY="..."
export HERMES_TWEET_ENABLE_ACTIONS="false"
```

要允許發文、回覆、DM、監控、匯出等 action 時，才在**有明確確認閘的互動 session** 設：

```bash
export HERMES_TWEET_ENABLE_ACTIONS="true"
```

## 工具心法

1. 先用 `tweet_explore` 找 endpoint，不猜 path。
2. GET 且 read-only → `tweet_read`。
3. POST / DELETE / private read / monitor / webhook / export / draw / media → `tweet_action`。
4. 發文、回覆、DM、follow、like、retweet 前，必須沿用 social-post 的「確認」安全閘。
5. `tweet_action` 不可用時，不要 fallback 到其他寫入路由；改請使用者啟用 action 或走 `x.md` 手動 compose。

## Social Listening

用途：找 X 上正在討論的題材，補 `content_plan.md` 的題材提示。

先找搜尋 endpoint：

```json
{"query":"tweet search","method":"GET"}
```

再讀結果：

```json
{"path":"/api/v1/x/tweets/search","query":{"q":"Claude Code skill OR AI agent min_faves:10","limit":25}}
```

整理給使用者時只輸出：

- 3-5 個可用題材
- 每個題材為什麼適合今天公式
- 建議用哪個 platform voice（X thread / Thread / FB 長文）
- 不貼大量原文，不外傳使用者 profile

## 讀 Tweet / Replies / Quotes

使用者貼 tweet URL，先抽最後的 status id。常用探索詞：

```json
{"query":"tweet replies","method":"GET"}
{"query":"tweet quotes","method":"GET"}
{"query":"tweet thread","method":"GET"}
{"query":"retweeters","method":"GET"}
```

讀完後用 `evaluation.md` 的診斷框架整理：

- hook 是否清楚
- 回覆區在討論什麼
- quote / repost 的 identity signal
- 是否值得延伸成 F5 / F10 / F14 / F19

## 查使用者 / Followers

用於：

- 找競品 / 創作者最近 tweets
- 分析目標受眾語氣
- 匯出 followers 做人工分群
- 檢查使用者自己的 X 帳號近期主題

常用探索詞：

```json
{"query":"user lookup","method":"GET"}
{"query":"user tweets","method":"GET"}
{"query":"followers export","include_actions":true}
```

Followers export 屬於 action。執行前要說清楚帳號、數量、用途，拿到「確認」才跑。

## 發 Tweet

先照 `generate_and_publish.md` 產生 X 版草稿。使用者回「確認」後，才探索 action：

```json
{"query":"post tweet","include_actions":true}
```

再送：

```json
{"path":"/api/v1/x/tweets","method":"POST","body":{"account":"@example","text":"草稿全文"},"reason":"Post the user-approved social-post X draft."}
```

發完要把回傳連結或 tweet id 寫回 `content_plan.md`。

## 發 Reply

Reply 比新 tweet 更容易誤傷 context。執行前必做：

1. 讀原 tweet。
2. 讀主要 replies 或 thread context。
3. 草稿只回使用者要求的角度，不自動 tag、挑釁、引戰。
4. 預覽 reply 全文，拿「確認」。

探索：

```json
{"query":"reply tweet","include_actions":true}
```

Body 要包含目標 tweet id / URL、account、text。使用 catalog 回傳的 schema，不自己猜欄位名。

## 發 DM

DM 是最高風險路由。只用於使用者明確指定收件人與內容的情境。

硬規則：

- 不批量 DM。
- 不自動追蹤後 DM。
- 不把 `style_profile.md` 或私密資料貼給第三方。
- 不替使用者編造關係。
- 必須完整預覽，拿「確認」。

探索：

```json
{"query":"send DM","include_actions":true}
```

## 監控

用於「這篇發完 2 小時後幫我看數據」或「監控某 keyword」。

探索：

```json
{"query":"monitor tweets","include_actions":true}
{"query":"monitor account","include_actions":true}
```

建立前先問：

- 監控 tweet / account / keyword
- 頻率
- 停止時間
- 要寫回 `content_plan.md` 的欄位
- 是否只通知顯著變化

Cron / unattended session 建議保持 `HERMES_TWEET_ENABLE_ACTIONS=false`，只讀資料；建立或修改 monitor 時再用互動 session。

## 失敗處理

- `XQUIK_API_KEY` missing：請使用者設定到 Hermes runtime，不要貼 key。
- `tweet_action` disabled：說明需要 `HERMES_TWEET_ENABLE_ACTIONS=true`，不要繞過。
- endpoint 找不到：回到 `tweet_explore` 換 query，不猜 path。
- 寫入失敗：停止，回報錯誤類型與已完成動作，不重試不同路由。
- rate / policy / account state error：停止等使用者指示。

## 寫回 Content Plan

發文後同一筆戰績備註加：

```text
X: <tweet URL or id> / route=Hermes Tweet / initial metrics pending
```

回看數據時更新同一筆：

```text
X 2h: impressions=?, likes=?, replies=?, reposts=?, quotes=?, followers_delta=?
```

不要新建散落檔案。
