---
name: social-post
description: 學使用者的 Facebook 個人貼文語氣，依 14 天內容策略日曆，自動產出並發佈到 FB / Instagram / Threads / X。使用時機：使用者說「發文」、「幫我寫一篇貼文」、「用我的風格發」、「今天發一篇」、「PO 一下」、「學我的語氣」、「分析我的貼文風格」、「重新規劃內容」、「排貼文」、「查流量」、「review」時一律觸發；即使只說「發一篇」、「PO 文」、「PO 個廢文」也要觸發。
---

<!--
  social-post skill — Created by 駱君昊 (Hao)
  Repo: https://github.com/Hao0321/claude-skill-social-post
  Companion skill: https://github.com/Hao0321/claude-skill-code-cleanup
  Facebook: https://www.facebook.com/lo.jain.hao
  Claude Code 台灣交流討論區: https://line.me/ti/g2/DPTQR_XE6IYP8c5lBxsbRwsvEUsxI-70p1jWoA
  License: MIT — 保留此標註即可修改、使用、商用
-->

# social-post

三階段工作流。**依使用者意圖路由，只讀必要 reference**（省 token）。

## 階段路由

| 觸發 | 階段 | 讀 |
|---|---|---|
| `style_profile.md` 不存在 / 說「重新學風格」 | **P1** | `references/learn_style.md` |
| `content_plan.md` 不存在 / 說「重新規劃」「排新的 14 天」 | **P0** | `references/phase0_plan.md` + `formulas.md` |
| 說「發文」「今天發一篇」「PO」 | **P2** | `references/generate_and_publish.md` + `style_profile.md` + `content_plan.md` + `formulas.md`（目標公式段）+ `rules.md`（相關規則）+ 目標平台 ref；若 X 需要搜尋 / 監控 / reply / DM / 匯出 / Hermes Agent 工具，另讀 `references/hermes_tweet.md` |
| 說「這篇好不好」「查流量」「分析」 | **診斷** | `references/evaluation.md` + `rules.md`（R6/R23）+ 目標 post 戰績 |
| 說「歷史怎麼樣」「Day X 發生什麼」 | **案例** | `references/case_studies.md` |
| 想查某條規則細節 | **規則** | `references/rules.md`（R1-R35 完整版）|

路由前用一句話告知使用者要做哪階段，給糾正機會。

## 先決條件

- `mcp__Claude_in_Chrome__*` 可用（否則停、不模擬）
- 使用者已登入目標平台（登入牆出現請使用者手動登，不自動化）
- X 選配進階路由：若 Hermes Tweet toolset 可用，可用 `tweet_read` 做 X 搜尋 / 讀回覆 / 查使用者，用 `tweet_action` 做確認後的發文 / reply / DM / 監控；詳見 `references/hermes_tweet.md`

## 🛡️ 安全閘（硬規則不可覆寫）

**每次實際發佈前必須在對話裡拿到使用者明確「確認」字眼。** 沒「確認」不發。

**私人版例外**：使用者若明確在**當前 session** 授權「你自己操作不用問我」，私人版可免逐次確認，僅限該 session。開源版 SKILL.md **永遠保留此閘門不可 bypass**。

## 不要做

- 沒授權發文字眼就發
- 跨平台同一段複製（每平台重新生成）
- 自動按讚 / 回覆 / follow / 大量留言
- 外傳 `style_profile.md` / 使用者資料
- 幫登入 / 改隱私 / 改帳號
- 猜測 FB 個人頁網址（P1 必須問）
- 刪除使用者留言 / 貼文（系統硬規則）
- 在未確認前用 Hermes Tweet `tweet_action` 發 tweet / reply / DM / follow / like / retweet
- **🚨 FB / Threads 正文附外部連結（R25 硬規則，絕對禁止）**
- **🚨 AI 腔抽象空詞（護城河／本質／真正的 X）+ staged 開場 + over-narrate（R34 硬規則，要真實不要像 AI 文；日常標點 ，、，── 與 ！ hype 是 proven 裝置照用）**

## 📋 核心規則速查（R1-R35，完整定義見 `references/rules.md`）

| R | 一句話 | 何時關鍵 |
|---|---|---|
| **R1** | 一天一篇 + Mode B 嚴格 1/天 / Mode C 可 2/天 + 每週 ≥ 2 篇非 AI | 排程 |
| **R2** | 爆款後 24h 冷卻禁 F6b/F3 長文 | 爆款後 |
| **R3** | 連 3 篇 < 15% 非追蹤 → 必用 F8-F13 或 Mode C | 鎖鐵粉時 |
| **R4** | AI 受眾夜貓 22:00-01:00；Mode A/Thread 不挑時段 | 排時段 |
| **R5** ⭐ | 主題 = 敘事意圖；同意圖 4 天內不重複 + 月 ≤ 2 次 | 每篇必檢 |
| **R6** ⭐ | 必 48-72h plateau 才判定；1-19h 不下定論 | 看戰績 |
| **R7** ⭐ | 真 KPI 是社群轉化不是讚 | 評估價值 |
| **R8** ⭐ | Voice Lock：僅 Mode B 用 Day 1 純血 4 段 4 句 | 生成 Mode B |
| ~~R9~~ | 廢除（併入 R5）| — |
| **R10** | Hype 詞輪替（連 2 篇不重複開頭/結尾詞）| 生成 Mode B |
| **R11** | 金句密度：4 段 4 punch | 生成 Mode B |
| **R12** | 量化稀缺 hook（段 1 數字 stacking，≤ 3 個/段）| 生成 Mode B |
| **R13** | 反命題 hook（「大家以為 X，其實 Y」）| 生成 |
| **R14** | Hook punch 詞庫（絕對化 + 權威 stacking + 反差數字）| 生成 |
| **R15** ⭐ | 私訊分享 = 2026 最強信號（CTA 加「分享給朋友」）| 生成 CTA |
| **R16** | 5 字長留言 = 3× 權重（開放式提問）| 生成 hook |
| **R17** | Reels 同日 +50% 觸及（F18 改 15-30 秒）| 作品 demo |
| **R18** | 儲存 = 次強信號（索取物/framework/清單）| 生成 |
| **R19** ⭐ | Thread ≠ FB；Thread 最強 = 轉發 + keyword | 發 Thread |
| **R20** | 漸進改進（不能一次純血時每篇加 1-2 元素）| 過渡升級 |
| ~~R21~~ | 撤回（不是跨年衰退，是沒連發累積）| — |
| ~~R22~~ | 部分撤回（keyword peak 非主因）| — |
| **R23** | per-view 追蹤轉化率（新評估指標）| 看戰績 |
| **R24** | 純血連發累積（≤ 5 天連 2-3 篇才 mega-viral）| 衝 mega |
| **R25** 🚨 | FB/Threads 正文絕不附連結 | 每篇必檢 |
| **R26** | ── 分隔符（Mode C 長文視覺切分）| 生成 Mode C |
| **R27** ⭐ | 個人脆弱 confess = broke 鐵粉圈 90%+ | 生成 Mode C |
| **R28** 🏆 | 行業反主流 framing（Mode C 最強）| 生成 Mode C |
| **R29** | Mode C 同日連發（同 niche + 互補 framing）| 雙篇排程 |
| **R30** 🏆 | FB 社團 cross-post = 留言 5-10x 放大 | 主帳號發完後 |
| **R31** 🛡️ | F24 Brand 邊界澄清時機（月 1 次，trust reset）| 私訊爆/誤解時 |
| **R32** 🌟 | 集體 framing「我們 / 一起」= broke 鐵粉圈 +30-50% | 缺 mega hook 時 |
| **R33** 🧪 | FB 週任務情報：Reels 額度 = 蓋章 R17 該週排；量任務 = 陷阱不追；連 3 指標↑ = 廣推窗口 | 看分析面板時 |
| **R34** 🚨 | 真實 voice：元兇是「詞」不是標點 ── 禁抽象空詞(護城河/本質/真正的X)+staged+over-narrate；日常標點 ，、，proven 裝置(──分隔符/！hype)照公式用 | 每篇必檢 |
| **R35** 🏆 | keyword CTA「留言『X』」= broke 引擎(6/9：959 留言→93.1% mega 42K)；**預設公開 link 自助**(精選留言,無 DM 天花板+account-safe)，DM 只小量高觸用；絕不導 GitHub 正文 | giveaway CTA |

**⭐ = 高頻必讀 / 🚨 = 硬規則 / 🏆 = 最強觸發 / 🧪 = 候選待實證**

### 🎯 Viral 4 條件公式（核心）

```
viral = 4 段 4 句結構 + 純血 voice + 全新敘事意圖 + 黃金時段
```

4 個 AND，任一缺 = 死。**Readability 是隱藏第 5 條件**（meta ≤ 2 層 / 數字 ≤ 3 個/段 / 5 秒讀懂）。詳見 `rules.md`。

### 🎭 Hao 4 個 Mode（funnel 互補）

| Mode | 公式 | funnel | 鐵粉/廣推 |
|---|---|---|---|
| **A 日常** | 短句吐槽 | 鐵粉黏著 | 90% 鐵粉 |
| **B 純血** | F6b / F15 mini | 擴散 + Line 群 | 90%+ 廣推 |
| **C 深度反思** | F20/F21/F22/F23/F24/**F25a/b/c**/**F26**/**F27** | 信任深化 + 儲存 + trust reset + 集體 framing + 作品集 reveal + 單品 giveaway | 可 broke 94.5% |
| **Thread F19** | 立場宣言 | Thread 轉發 | Thread 廣推 |

## 💡 實用技巧

- **作者精選留言**：留言 > 50 時用單則精選留言置 CTA（FB 可放 1 個 URL，正文不行）
- **留言框 Enter = 送出**：留言壓成單行用 `→ ，／` 分隔
- **FB 原生排程**：夜貓時段用「貼文設定 → 排程選項」，細節見 `facebook.md`

## 🔄 持續優化（開發原則）

- **P0 私人版先行**：新規則先寫 `social-post/`，實證有效再同步 `../public/social-post/`
- **P1 語氣永遠套用**：生成草稿必先讀 `style_profile.md`，不像 voice 重生成（公式 < 語氣）
- **P2 同步開源時機**：跑 3-5 篇實戰 + 正面戰績 → 同步通用檔（`SKILL.md` `references/*.md`）；**絕不搬** `style_profile.md` `content_plan.md`；每次 = 新版號 + CHANGELOG + push
- **戰績追蹤**：發完使用者回報 → 立刻更新 `content_plan.md` 同筆（不新建 row）
- **review 節奏**：每兩週說「review」→ 讀戰績 → 找最好/最差公式 → 新日曆寫回 + 舊的搬歷史段

## 📌 快速查詢

| 需要 | 去 |
|---|---|
| R1-R35 規則完整定義 | `references/rules.md` |
| FB 2026 演算法權重 + 4 指標 | `references/evaluation.md` |
| 案例解剖（Day 1-7 + 5 月 Mode C）| `references/case_studies.md` |
| F1-F27 公式 | `references/formulas.md` |
| X Hermes Tweet 進階路由 | `references/hermes_tweet.md` |
| 受眾畫像 + 活躍時段 | `style_profile.md` |
| 今天 Day N + 戰績 | `content_plan.md` |

## 常見踩雷

- FB DOM 常變，選擇器失效用 `get_page_text` fallback
- FB 個人頁虛擬化，邊捲邊抓（見 `learn_style.md`）
- IG 要圖，純文字改 Threads / X 是 `x.com` / Threads 桌面版無帳號切換
- **Chrome MCP 斷線**：重試 2-3 次 → 仍斷告知使用者修（extension 登出/視窗全關）→ 急迫時切純文字草稿 + 手動步驟，不乾等
- **Chrome MCP permission**：FB 寫入操作要使用者 grant facebook.com 權限（read 級 navigate 自動過，write 級 click/type 要授權）
- **🛡️ 帳號封號防護**：keyword CTA（R35）爆量 > 100 留言別手動私訊全部（FB 判私訊異常 → 限制 / 封號），改精選留言公開 link + Discord；開藍勾勾驗證（R35 天花板，Case 29 血淚）
- **使用者 override 規則**：明確 override → 執行 + 標記戰績備註 + 降風險（不重複爭論），戰績出來實證後果
