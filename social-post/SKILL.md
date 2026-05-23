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
| 說「發文」「今天發一篇」「PO」 | **P2** | `references/generate_and_publish.md` + `style_profile.md` + `content_plan.md` + `formulas.md`（目標公式段）+ 目標平台 ref；若 X 需要搜尋 / 監控 / reply / DM / 匯出 / Hermes Agent 工具，另讀 `references/hermes_tweet.md` |
| 說「這篇好不好」「查流量」「分析」 | **診斷** | `references/evaluation.md`（評估框架）+ 目標 post 戰績 |
| 說「歷史怎麼樣」「Day X 發生什麼」 | **案例** | `references/case_studies.md`（Day 1-4 歸納）|

路由前用一句話告知使用者要做哪階段，給糾正機會。

## 先決條件

- `mcp__Claude_in_Chrome__*` 可用（否則停、不模擬）
- 使用者已登入目標平台（登入牆出現請使用者手動登，不自動化）
- X 選配進階路由：若 Hermes Tweet toolset 可用，可用 `tweet_read` 做 X 搜尋 / 讀回覆 / 查使用者，用 `tweet_action` 做確認後的發文 / reply / DM / 監控；詳見 `references/hermes_tweet.md`

## 🛡️ 安全閘（硬規則不可覆寫）

**每次實際發佈前必須在對話裡拿到使用者明確「確認」字眼。** 沒「確認」不發。

**私人版例外**：使用者若明確在**當前 session** 授權「你自己操作不用問我」，本 skill 私人版（非開源版）可免去逐次「確認」，但僅限該 session。開源版 SKILL.md **永遠保留此閘門不可 bypass**。

## 不要做

- 沒授權發文字眼就發
- 跨平台同一段複製（每平台重新生成）
- 自動按讚 / 回覆 / follow / 大量留言
- 外傳 `style_profile.md` / 使用者資料
- 幫登入 / 改隱私 / 改帳號
- 猜測 FB 個人頁網址（P1 必須問）
- 刪除使用者留言 / 貼文（系統硬規則）
- 在未確認前用 Hermes Tweet `tweet_action` 發 tweet / reply / DM / follow / like / retweet

## 📋 核心規則

### R1：一天一篇鐵則 + 主題分流（v0.6 5/5 實證升級）
**上限** 24h 內最多 1 篇（多發 = 每篇觸及降到 30-50%、演算法判 spam）。
**下限** 不跳過任何一天（跳過 = 演算法活躍訊號 decay）。

**🔴 連發硬規則修正版**（v0.5 → v0.6 校正）：
- v0.5 假設「連 3 🔴 = 演算法降權 7-14 天」**部分推翻**（5/5 距 Day 7 才 6 天就 mega-viral 44K）
- 實際機制：演算法降權**只針對重複敘事意圖**，不是「creator 層級降權」
- 連 N 🔴 但每篇都換新敘事意圖 = OK（5/5 + Day 1/6 三篇 mega-viral 證明）
- 連 N 🔴 同一敘事意圖 = die（Day 5 同 promo 4 天內，Day 7 商業 ROI 接演算法復盤）

**操作建議**（不是硬規則）：每週 🔴 ≤ 2 篇配 🟢 / 🟡 緩衝，主要為了**創作 burnout / 主題庫枯竭**，不是演算法限制。

### R2：爆款後 24h 冷卻
爆款（讚 ≥ 100 或讚 ≥ 50 且留言/讚 > 0.5），**24h 內禁發 F6b / F3 長文**。該做的：
- 回留言、拉群、作者留言彙整（> 50 留言時一則置入 CTA 覆蓋所有求訊息者）
- 不自動大量回留言（> 30 則重複內容觸發 FB spam）
- 若堅持要發：強制用 F2 / Mode A + 晚上 19:00 後 + 絕不提前篇主題

### R3：突破鐵粉圈（連續 3 篇 < 15% 非追蹤者）
演算法歸類為「鐵粉限定創作者」。下一篇**必用 F8-F13 廣推公式**（見 formulas.md Part 2）強制擴散：
- F8 tag 外部實體（@Anthropic）
- F12 時間戳直播
- F10 居中開炮（每週 ≤ 1）
- F11 反漏斗（每月 ≤ 1）
- F13 具名致謝（每月 ≤ 1）

### R4：時段按受眾分流
**AI/tech 創作者受眾是夜貓族**，FB 黃金時段 **22:00-01:00**，不是傳統 9-11AM（實戰對比：02:13=72K、02:16=767、09:48=373）。

其他受眾見 `style_profile.md` 的「受眾 FB 活躍時段」段。

### R5：敘事意圖冷卻（Day 1/5/6/7/5-5 五案例升級為 v0.6）

**核心定義**：「主題」= **敘事意圖**（promo / 演算法復盤 / 商業 ROI / 社群 social proof / 教學 / 合作達成 / 預告 / 抱怨...），不是公式 / hook 詞 / noun phrase。

**冷卻硬規則**：
- **同敘事意圖 4 天內不重複**（4 天內第 2 次同意圖 = 演算法判 self-promo 疲勞）
- **同敘事意圖每月最多 2 次**（月內第 3 次同意圖即使距前次 > 4 天也降權）
- **不同敘事意圖完全不限頻率**（5/5 實證：月內第 5 個 F6b 但是第 1 個「社群 social proof」意圖 → mega-viral，瀏覽者 44K / +1,239 Line 群）

**月配額計算單位 = 敘事意圖，不是 F6b 公式總數**（v0.6 推翻 v0.5 R9 假設）。

**5 個案例對照**（敘事意圖視角）：
| 貼文 | 敘事意圖 | 月內第幾次 | 距前次 | 結果 |
|---|---|---|---|---|
| Day 1 | promo | 1/2 | — | mega-viral 75K |
| Day 5 | promo | **2/2** | **4 天** | flop 0.13%（4 天內重複）|
| Day 6 | 演算法復盤 | 1/2 | — | mega-viral 17K |
| Day 7 | 商業 ROI | 1/2 | — | 鎖鐵粉 11.5%（voice OOC 主因，非 R5）|
| 5/5 | 社群 social proof | 1/2 | — | mega-viral 44K（+1,239 Line 群）|

**違反成本實證**：Day 5 同意圖 4 天內第 2 次 → 觸及 Day 1 的 0.13%。

使用者要「複製爆款」 → skill 必檢查敘事意圖月配額 + 4 天冷卻，建議切新意圖或等冷卻過。

### R6：評估看 4 指標 + **必須 48-72h plateau 才判定**（2026-04-27 實證升級）
詳見 `references/evaluation.md`。

**重要：早期判斷規則**
- **1-6h 數據**：完全不要下結論（會 underestimate 60-80%）
- **6-24h 數據**：只能說「目前趨勢」不能說「成功 / 失敗」
- **48-72h plateau**：**才能用 4 指標判定**

**4 指標**（看 plateau 後的）：
1. 連結點擊率 > 1%
2. 追蹤者比例
3. 互動率 > 15%
4. 下游轉化（社群入群 / GitHub star / 付費）

**多次實證** Day 1 / Day 2 / Day 4 / Day 5 都是後期才看出真實表現：
- Day 1: 早期看似 mega-viral，72h 後才看到 +1,150 社群（真正 ROI）
- Day 4: 1h 看似鐵粉限定 6%，58h 後 29% 非追蹤者突破鐵粉圈
- Day 5: 19h 看似 fail，58h 後連結點擊率 4.6% 是 deep conversion 鐵粉文

### R7：真正的 KPI 是社群轉化，不是讚
Day 1 實證：380 讚只是表面，**Line 社群 ~800→2,119（+1,319 成員）**才是真 ROI。評估爆款值不值得看 downstream：社群人數、star 數、付費學員。

**注意**：社群成長含**多平台貢獻**（FB 主導 + Threads 補強）。歸因時不要把全部漲幅歸給單一貼文。

### R8：Voice Lock — **僅** Mode B 爆款型必用 Day 1 純血格式（範圍限縮 2026-04-29）
**範圍校正**（Day 7 實證）：R8 voice lock **只適用 Mode B 爆款型**（每月 1-2 篇）。**Mode A 日常 80% 用🟢自然口語**（「今天一早」「好久沒來」「嗯…剛看了一下」），不能整週純血。

**Mode B 爆款型 = Day 1 純血格式鎖死**。

**F6b meta-ship 結構（Day 1 75K 觸及實證範本）**：
```
[段 1 成果炸場+meta 鉤子] ＜AI＞這次真的殺瘋了，我直接做了一個＜產品＞能＜能力敘述＞！！！你沒看錯！！＜自證懸念＞！！真的太神啦！！！

[段 2 過程數字] 剛剛花＜時間＞讓它＜具體動作＞，＜量化成果＞

[段 3 使用體驗敘事] 現在我說「＜指令＞」它就＜動作＞

[段 4 社群召集 CTA] ＜未來計畫＞，沒入群的留言我拉你
```

**關鍵 layout 規則**（看 `style_profile.md` Mode B Day 1 完整範本）：
- **！！！只在段 1 密集**（連續 3-5 個），段 2/3/4 完全不用
- 段 2/3 是**平靜敘述**（句尾不加標點不加 emoji）
- 段 4 收尾**完全無 emoji 無標點留白**
- **絕不用 numbered / bullet list**（這不是 Day 1 風格）
- 每段 1-2 句，不是三連發子彈
- 4 段就是 4 段，**不要加第 5 段收尾**

**F6a 邀請碼版**（OiiOii 風）= 不同變體，4 段是「成果炸場 / 教學引流 / 邀請碼 CTA / 可選合作」，emoji 用 🎉 / 😂。看 `style_profile.md` F6a 段。

**Mode A 日常碎念不在此規則範圍**（用🟢日常開頭如「今天一早」「好久沒來」「嗯…剛看了一下」）。

**草稿生成檢查表**（生成 Mode B / F6b 時必跑）：
1. **是否 4 段 4 句（剛好不多不少）**？✅ → 過 ⭐ 鐵則（使用者 2026-04-28 lock）
   - 「段」= paragraph，用空行分；「句」= sentence，1 段 1 句
   - **不是螢幕視覺 4 行字**（手機 wrap 後一句佔 2-4 行字是正常）
2. **每段就是一個 sentence**（不是 1 段多句、不是 numbered list）？✅ → 過
3. ！！！只集中在第 1 段？✅ → 過
4. 段 2/3 結尾無標點無 emoji？✅ → 過
5. 段 4 結尾留白無 emoji？✅ → 過
6. 沒用 numbered / bullet list？✅ → 過
7. 主題與 4 天內貼文不重複（R5，promo vs 復盤算不同主題）？✅ → 過
8. 第 1 段有 meta 鉤子（self-evident 或 self-experimental）？✅ → 過

任一條 ❌ → 重生成，**不要出草稿**。

**已實證 4 段 4 句範本**（看 `style_profile.md` Mode B）：
- Day 1 promo 型 → 75K 觸及 mega-viral
- Day 6 復盤型 → 19h 17K 觀眾 / 92.9% 非追蹤者 mega-viral

### R9：~~Mode B 月配額硬限 1-2 篇~~ → **廢除**（5/5 實證推翻，併入 R5 敘事意圖月配額）

v0.5 R9 假設「Mode B 公式總篇數每月 1-2」是錯的。5/5 實證：月內第 5 個 F6b 但敘事意圖全新 → mega-viral 44K / +1,239 Line 群。

正確規則 → R5：**月配額計算單位 = 敘事意圖，不是 F6b 公式總數**。

### R11：金句密度（v0.7，從 F14 偷學）
**Mode B 每段至少 1 個可截圖金句**（不是「！！！」hype，是 reusable 觀察 / identity signal）。F14 範例每篇 8 個截圖入口 → 分享率 0.46-0.64。Hao v0.6 只 2 個（殺瘋了 / 太神啦） → 分享率 0.05-0.21（弱 4 倍）。

**4 段 4 句的 4 個 punch**：
- 段 1 punch：hype 詞 + meta 鉤子（已有）
- 段 2 punch：**反差數字 / reusable 觀察**（新增）— 例「同公式 5 次：3 mega 1 flop 1 鎖鐵粉」
- 段 3 punch：**具體 use case 句**（升級）— 例「現在我說 X 它就 Y」結尾必有反差或意外
- 段 4 punch：**明確 CTA + 稀缺感**（升級）— 例「全部 1700 行規則開源，沒入群留言我拉你」

任一段純敘述沒 punch → 重寫該段。

### R12：量化稀缺 hook（v0.7，從 F15 + F17 偷學）
段 1 開頭**塞具體數字堆疊**而非抽象 framing。對演算法跟人類都加分（具體 = 可信）。

| ❌ 抽象 | ✅ 量化稀缺 |
|---|---|
| 「我自己訓練的 skill 公開」 | **「14 天 14 篇 75K 觀眾 1700 行 SKILL.md 公開」** |
| 「Line 社群成長很多」 | **「Line 群 800→3,575 兩週 +2,775 人」** |
| 「演算法打臉我」 | **「5 篇對照組打臉我 3 件以為對的事」** |

數字越具體 + 反差越大 = hook 越強。

### R13：反命題 hook（v0.7，從 F14 偷學）
中段或 hook 用「大家以為 X，其實 Y」frame。F14 兩篇都用反命題撐起整篇（specs to code 反對 / YouTube 不是排名系統）。

**Hao 已知反命題庫**（R1-R10 都可變反命題 hook）：
- 「大家以為 viral = 好內容，其實 = 好內容 × 飢餓度 × 主題冷卻」（R5）
- 「大家以為 voice 一致 = brand，其實連 hype 詞重複 = 套路」（R10）
- 「大家以為讚多 = 成功，其實分享多才是」（R6）
- 「大家以為 02:13 是黃金時段，其實 4 天內重複會把 buff 燒光」（R5+R4）
- 「大家以為 4 段 4 句結構是 viral 主因，其實是 4 個 AND（結構/voice/意圖/時段）」

### R14：Hook punch 詞庫（v0.7，從 F17 偷學）

**絕對化定位句式**（FOMO trigger）：
- 「如果只能看一個 X，那就是 Y」
- 「Claude Code 跑兩週 14 篇，總結 5 個沒人說的事」
- 「整套規則濃縮成 4 段 4 句」

**權威 stacking 三層**（每段 1 個 = punch）：
- L1 稱號：之父 / 親授 / Co-Founder / 第 N 屆冠軍 / 1700 行 SKILL.md 作者
- L2 量化資歷：14 天 / 75K 觀眾 / 1,319 入群 / 1700 行 / 3 個 mega-viral
- L3 反差成就：最低 95 觀眾 vs 最高 75K（**800x**）/ Day 1 380 讚帶 1,319 入群 vs Day 5 9 讚帶 0

**反差數字 pattern**（從 F14 偷學）：
F14 開頭就丟：「10% CTR 死 3000 觀看 / 6% CTR 爆 40 萬」
Hao 適配版：「Day 1 380 讚帶 +1,319 入群 / Day 5 9 讚帶 0 入群」「同公式 5 次 3 mega 1 flop」

每篇 Mode B 至少 1 個反差數字寫進段 1 或段 2。

### 🚨 R25：FB / Threads 貼文絕不附外部連結（v0.8.6，使用者 5/19 lock）

**所有 Hao viral 篇都沒附連結**：
- Day 1 / Day 6 / 5/5 mega-viral 三篇 ✅ 沒連結
- OiiOii 系列 F6a 爆款 ✅ 沒連結
- 25/7 三篇 F19 純血 Thread ✅ 沒連結
- 5/12 F19「FB 營利」mid-viral ✅ 沒連結（「歡迎自行索取」純留言 trigger）

**為什麼絕不附連結**：

1. **FB / Thread 演算法降權外部連結**：附連結觸及衰退 30-50%
2. **「留言我拉你」/「歡迎索取」funnel 比連結點擊強 100x**（R7 真 KPI）
3. **Day 1 實證連結點擊率 = 0.0097%**（7/74K 觀眾）= 連結沒實際 ROI
4. **留言區互動是 viral 引擎**，連結會分流走觀眾
5. **私訊 trigger R15** 比 click trigger 強得多

**硬規則**：

| 平台 | 正文 URL | 留言區 URL | 留言區拉群 |
|---|---|---|---|
| FB | ❌ 絕對禁止 | ✅ 可用「精選留言」放 1 個 URL | ✅ 「沒入群留言我拉你」優先 |
| Thread | ❌ 絕對禁止 | ⚠️ 慎用 | ✅ 「歡迎索取」優先 |

**生成 Mode B 草稿時必檢**：
- 段 4 有 https://... 嗎？→ **❌ 不要發**，移到留言區
- 段 4 結尾必須留白（無 URL / 無 emoji / 無標點）

**我之前犯這個錯的紀錄**（v0.8.5 之前）：
- V2 真 KPI 復盤草稿：誤加 GitHub 連結 ❌（5/19 撤回）
- V7c FB F15 mini「cleanup-helper」plan：加 GitHub 連結 ❌
- 5/17 副帳號 F19「AI 取代論」：加 social-post GitHub 連結 ❌

→ **永遠不准再犯**。

### R19：Threads 轉發權重 + Keyword 機制（v0.8，2025-07 實證）

**Thread 演算法跟 FB 完全不同 axis**：
- FB 最強信號 = **私訊分享**（Messenger / WhatsApp）
- Thread 最強信號 = **轉發（repost）** + **keyword detection**

**Hao 帳號 hao0321_studio 2025-07 實證**：
- 400 粉 → 10K 粉 / 7 天（+9,600）
- 3 篇 F19 立場宣言文都用熱門 keyword + 敵人/英雄敘事
- 詳見 `references/case_studies.md` Case 11

**Thread viral 配方**：
1. **F19 立場宣言型公式**（詳見 `formulas.md`）
2. **熱門 keyword 命中 ≥ 2 個**：免費 / 付費 / 韭菜 / 賺錢 / 幹翻 / TM 做真的
3. **敵人 / 英雄敘事**讓讀者站隊
4. **無 CTA 無連結**（純情緒，演算法判 meaningful conversation）
5. **1 段不換行 / 連續逗號流 / 60-150 字**（v0.8.1 修正：不是 3-5 段，是 1 段內 3-5 句）
6. **「！」單個或「！！」最多**（絕對不用「！！！」— FB F6b 才用）

### ⚠️ Thread 排版鐵則（v0.8.1 從 3 篇真實爆款反向工程）

| 鐵則 | 規格 |
|---|---|
| 段落 | **1 段不換行** |
| 句數 | 2-5 句 |
| 分隔 | **連續逗號 + 「！」分隔**（不用空行）|
| ！級 | 「！」或「！！」（永遠不「！！！」）|
| 字數 | 60-150 字 |
| emoji | 可有可無 |

**vs FB F6b 對照**：
- FB F6b = 4 段空行 + ！！！3 個 + 200-400 字
- Thread F19 = **1 段不換行 + ！1-2 個 + 60-150 字**

兩個物種，公式不能照搬。

**Hao 雙 brand 雙 funnel 整合戰略**：

| brand | 平台 | 公式 | funnel |
|---|---|---|---|
| **social-post brand**（@lo.jain.hao）| FB 主 | F6b / F15 mini / 演算法復盤 | FB → 私訊 → Line 群 |
| **AI 教學分享 brand**（@hao0321_studio）| **Thread 主** | **F19 立場宣言** | **Thread → 帳號追蹤** |

**規則**：兩 brand 內容不交叉（F6b 別發 Thread / F19 別發 FB），互補不互搶。

### R15：私訊分享 trigger 設計（v0.7.2，2026-05 web 大數據驗證）

**2026 演算法最強信號 = 私訊分享**（Messenger / WhatsApp）。比公開分享更強，立刻 trigger「essential 內容」標籤 + broader distribution。

**Hao funnel implications**：
- R7「真 KPI 是 Line 群」對應「留言我拉你」CTA → 加入「**分享給朋友**」混用
- F19「我有開源歡迎自取」自帶私訊分享 trigger（朋友間「你要的」）
- 不只設計「公開互動」，也設計「私下傳閱」價值（cheat sheet / tool / 範本 / 教學）

**CTA 句式升級庫**：
- 「分享給寫 code 的朋友 / 工作上的同事 / 想學 AI 的人」
- 「這篇你朋友也該看到」（identity signal）
- 「丟給你那個 always asking how to use Claude 的朋友」（具體 use case）

實證：F19「FB 營利 + skill 開源」隱含 trigger 朋友間私訊（「你不是說想 monetize FB 嗎？這個」）。

### R16：5 字以上留言 trigger（v0.7.2，3× 權重）

**5 字以上「meaningful comment」 = 3× 一般留言權重**（[Buffer 2026 / SocialPilot 2026](https://buffer.com/resources/facebook-algorithm/)）。Hao 留言區「+1」「拉我」「我要」短留言雖多但**演算法權重低**。

**Hook 設計引發長留言**：
- ❌ Yes/No 問題：「同意嗎？」「有用嗎？」
- ✅ 開放式提問：「你跑同樣 skill 結果差很多嗎？」「你 funnel 真 KPI 是什麼？」
- ✅ 觀點挑戰：「我覺得 X，你覺得呢？為什麼？」
- ✅ 經驗分享請求：「你有沒有過 X 的經驗？分享一下」

**5/19 F15 SKILL.md 公開 hook 升級**：CTA 不只「Line 群留言我拉你」，加「Star repo 後留言告訴我你想 fork 來做什麼」 → trigger 5 字 + 具體留言。

### R17：Reels 策略（v0.7.2，2026 演算法 +50% 同日加成）

**2026 演算法給 Reels 同日上傳 +50% 觸及**（[Meta 2025-10 update](https://about.fb.com/news/2026/03/rewarding-original-creators-on-facebook/)）+ 比 photo 觸及 +135% + 比一般 video +22% 互動。

**Hao 適配**：
- F18 作品 demo（GPT Image / Seedance / OiiOii）**改用 Reels 格式**
- 15-30 秒最佳完成率（+45%）
- 同日上傳：早上拍 → 中午剪 → 晚上發
- F6b 純血長文 + F18 Reels 作品同日跨 audience bucket OK

**Reels content idea 庫**：
- 15 秒作品 demo（GPT Image x Seedance 對比）
- 30 秒 skill 操作流程（speedrun 風）
- 15 秒 before/after（手動 vs Claude Code）

### R18：儲存（Save）指標重視（v0.7.2，新權重信號）

**儲存 = 「revisit 信號」**，2026 演算法權重僅次於私訊分享。F19 mid-viral 4 個儲存 = 強信號（內容值得回看）。

**設計儲存 trigger**：
- 提供「索取 / 自取」明確物品（repo / cheat sheet / 教學 / 範本）
- 包含 reusable framework（讀者想「我之後也要這樣做」會 save）
- 列點 / 清單 / SOP（save 後可以分批 read）

**戰績追蹤新增儲存欄位**：之前 content_plan.md 戰績表只記讚/留言/分享，**v0.7.2 起加儲存數**。

### R1 校準（v0.7.2，2026 web 大數據對照）

**工業 baseline 3-5 篇 / 週 = 中位數**（[WordStream 2026 / SocialPilot 2026](https://www.wordstream.com/blog/facebook-algorithm)）：
- Hao 14 篇 / 14 天 = 7 篇/週 = **2x 工業 baseline**
- 不到 fatal 但**有過頻 risk**（「過頻 = noise 標籤 = 全帳號降權」）

**修正 R1**：
- 每天 1 篇仍 OK（你已驗證）
- 但需配合**audience bucket 多樣化**（不能全 AI/skill）
- 每週至少 2 篇是「非 AI 主題」（純作品 / 旅遊 / 日常 / 食物）

### ⚠️ R11-R14 重要警告（v0.7.1 補丁，2026-05-13 實證升級）

**R11-R14 是 hook 強化裝飾品，不是 archetype swap**。5/12 實證：F6b 跑全綠 v0.7 升級版仍 plateau 在 219 觀眾 / 0 分享 / 88.7% 鐵粉鎖死。

**核心 lesson**：
- F6b 公式本身分享率天花板就 0.21（讚 / 留言驅動 archetype 結構限制）
- 再強化 hook punch 詞 / 金句密度 / 量化稀缺 = **只能維持讚 / 留言驅動，不會變成分享驅動**
- 想突破分享率天花板**必須換 archetype**（F15 SKILL.md 公開 / F16 weekly 精選彙整），不是強化 F6b

**Hao 鐵粉警告升級**：連 6+ 篇 F6b 後，**鐵粉對 voice 整體疲勞**（不只 hype 詞），R11-R14 改善有限。即使主題完全新（5/12「self-criticism via AI」距 5/5「社群 social proof」7 天 + 完全不同意圖）也仍 plateau。

### 📝 Readability 三項硬檢查（v0.7.1 新增）

每篇 Mode B 草稿生成後必跑：

1. **5 秒非追蹤者讀懂測試**：段 1 給沒看過你貼文的人，5 秒內懂主題嗎？
   - ❌ 失敗例（5/12）：「skill 訓練 AI → 學我語氣 → 鐵粉留言警告 → R10 輪替」4 層 meta，非追蹤者看不懂
   - ✅ 成功例（Day 1）：「skill 自己發貼文」1 層 meta，5 秒懂

2. **meta 層數 ≤ 2**：
   - 第 1 層 = 你做了什麼
   - 第 2 層 = AI / skill 怎麼參與
   - **第 3 層以上禁止**（鐵粉懂，新觀眾爬不過）

3. **數字密度 ≤ 3 個 / 段**：
   - 段 1 最多塞 3 個關鍵數字
   - 超過就是 dashboard report 不是貼文
   - ❌ 失敗例（5/12）段 1：「14 天 / 14 篇 / 75K / 4 次 / 12 個」5 個 → 大腦超載
   - ✅ 成功例（Day 1）段 1：「3 小時 / 13 篇 / 4 個驚嘆號」3 個 → 剛好

任一條 ❌ → 重寫該段。

### 📦 FB compose 段落硬規則（v0.7.1 新增）

**4 段 4 句草稿貼到 FB 必須手動兩次 Enter 保段落**（FB compose 預設會把單 Enter 變空白，必須手動雙 Enter）。

實證 5/12：使用者直接複製貼上 → markdown 空行被壓掉 → 4 段變一坨字 → 散文 readability 直接 fail。

**規則**：
- 給草稿時必明確標註「段間請按兩次 Enter」
- 或用 markdown horizontal rule（---）替代空行
- 或直接寫成圖片版排程貼上

### 🎯 Viral 4 條件公式（v0.6 核心，5 案例實證）

```
viral = 4 段 4 句結構
      + 純血 voice
      + 全新敘事意圖（4 天內不重複 + 月內 ≤ 2 同意圖）
      + 黃金時段（02:13 / 22:00-01:00）
```

**4 個 AND 不是 OR，任一條缺 = 死**：

| 貼文 | 結構 | voice | 新意圖 | 時段 | 結果 |
|---|---|---|---|---|---|
| Day 1 | ✅ | ✅ | ✅（promo 1/2）| ✅ | mega-viral 75K |
| Day 5 | ✅ | ✅ | ❌（promo 2/2 距 4 天）| ✅ | flop 0.13% |
| Day 6 | ✅ | ✅ | ✅（演算法復盤 1/2）| ✅ | mega-viral 17K |
| Day 7 | ✅ | ❌ | ✅（商業 ROI 1/2）| ✅ | 鎖鐵粉（voice OOC 單因）|
| **5/5** | ✅ | ✅ | ✅（**社群 social proof 1/2**）| ✅ | **mega-viral 44K / +1,239 Line 群** |

**生成 Mode B 草稿時必跑此 4 條件 AND 檢查表**，任一條 ❌ → 不要發。

### 📚 已知 viral 敘事意圖庫（v0.6 實證 + 待測）

實證 mega-viral 的意圖：
- **promo**（產品 ship）— Day 1
- **演算法復盤**（self-experimental analysis）— Day 6
- **社群 social proof**（pitch 群價值）— 5/5

待測但理論可行：
- 教學型（step-by-step share）
- 合作達成（公開合作 announcement）
- 預告型（即將 ship 的東西）
- 反思型（meta meta — 跨 N 篇貼文反思）

意圖種類愈多 → 月內可發的 F6b 數愈多（理論上 7 種 × 每月 2 = 14 篇/月，但操作上每週 2 篇就夠）。

## 💡 實用發文技巧

### 作者留言策略（高留言爆款後）
留言 > 50 時用**單則作者留言**（FB 可設「精選」置頂）包含連結 + CTA 覆蓋所有求訊息者，比逐條個別回更好也更安全。

### 留言框 Enter = 送出
FB / Threads 留言框 `\n` 會被當送出。**留言永遠壓成單行**用 `→` `，` `／` 分隔，不用換行（compose modal 才可多行）。

### FB 原生排程取代 cron
夜貓時段想發 + 不熬夜 = 用 FB「貼文設定 → 排程選項」。細節見 `references/facebook.md`。

## 🔄 持續優化

### 開發原則（2026-04-25 立規）

**P0：私人版先行**
- 所有新 SKILL 規則、新公式、新 reference、任何邏輯修改 → **先寫進 `social-post/`**（私人版）
- 在真實發文中實戰**驗證有效**後，再同步到 `../public/social-post/`
- **不要拿開源版當 sandbox**（會把未驗證規則推給世界）

**P1：語氣永遠套用**
- 所有生成的貼文草稿 **必須先 Read `style_profile.md`**（全文當 system-level voice 指引）
- 草稿生成後自我檢查：是否使用 `style_profile.md` 的招牌開頭 / 收尾 / emoji 偏好 / 標點風格？
- 若草稿不像使用者 voice（例：用了衰減開頭、標點偏離、太長 / 太短不符合 profile）→ **重新生成**
- 這條比公式結構優先：公式骨架 < 使用者實際語氣

**P2：同步到開源版的時機**
- 私人版跑至少 **3-5 篇實戰** + 有正面戰績 → 才同步到開源版
- 同步時只搬**通用邏輯檔案**：`SKILL.md`、`references/*.md`
- **絕不搬**：`style_profile.md`（個人語氣）、`content_plan.md`（個人戰績）
- 每次同步 = 新版號 + `CHANGELOG.md` 說明 + git push

### 戰績追蹤

發文後使用者回報實績 → **立刻**追加到 `content_plan.md` 戰績備註（不新建 row，更新同筆）。

每兩週說「review」時：讀戰績 → 找表現最好/最差公式 → 新日曆寫回上方 → 舊日曆搬「歷史日曆」段存檔。

## 📌 快速查詢

| 需要 | 去 |
|---|---|
| FB 2026 演算法訊號權重 | `references/evaluation.md` |
| 4 指標評估框架 | `references/evaluation.md` |
| Day 1-4 實戰案例解剖 | `references/case_studies.md` |
| 13 個公式（F1-F13）| `references/formulas.md` |
| X Hermes Tweet 進階路由 | `references/hermes_tweet.md` |
| 受眾畫像 + 活躍時段 | `style_profile.md` |
| 今天是 Day N + 戰績 | `content_plan.md` |

## 常見踩雷

- FB DOM 常變，選擇器失效用 `get_page_text` fallback
- FB 個人頁虛擬化，邊捲邊抓（見 `learn_style.md`）
- IG 要圖，純文字改 Threads
- X 是 `x.com`
- Threads 桌面版無帳號切換
- **Chrome MCP 突然斷線**（實戰遇過）：
  - 立即重試 2-3 次，通常幾秒自動恢復
  - 仍斷 → 告知使用者「Chrome extension 可能登出/Chrome 視窗全關」，等使用者修
  - 使用者時段急迫（如要準點發文）→ 提供純文字草稿 + 發文步驟，由使用者手動完成
  - 不要乾等，切換到「純文字協助」模式繼續工作
- **使用者 override 規則**（實戰遇過）：
  - 使用者明確 override（例：「一樣 2:13 發」即使 R5 禁 F6b 7 天內）→ **執行 + 標記 override 在戰績備註** + 降風險策略（如混搭 F11 / 換新 hook）
  - 不重複爭論 risk（已說過一次即可）
  - 戰績出來後實證該次 override 的後果（成功/失敗都是 skill 學習材料）
