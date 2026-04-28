---
name: social-post
description: 學使用者的 Facebook 個人貼文語氣，依 14 天內容策略日曆，自動產出並發佈到 FB / Instagram / Threads / X。使用時機：使用者說「發文」、「幫我寫一篇貼文」、「用我的風格發」、「今天發一篇」、「PO 一下」、「學我的語氣」、「分析我的貼文風格」、「重新規劃內容」、「排貼文」、「查流量」、「review」時一律觸發；即使只說「發一篇」、「PO 文」、「PO 個廢文」也要觸發。
---

<!--
  social-post skill — Created by 駱君昊 (Hao)
  Repo: https://github.com/Hao0321/claude-skill-social-post
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
| 說「發文」「今天發一篇」「PO」 | **P2** | `references/generate_and_publish.md` + `style_profile.md` + `content_plan.md` + `formulas.md`（目標公式段）+ 目標平台 ref |
| 說「這篇好不好」「查流量」「分析」 | **診斷** | `references/evaluation.md`（評估框架）+ 目標 post 戰績 |
| 說「歷史怎麼樣」「Day X 發生什麼」 | **案例** | `references/case_studies.md`（Day 1-4 歸納）|

路由前用一句話告知使用者要做哪階段，給糾正機會。

## 先決條件

- `mcp__Claude_in_Chrome__*` 可用（否則停、不模擬）
- 使用者已登入目標平台（登入牆出現請使用者手動登，不自動化）

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

## 📋 核心規則

### R1：一天一篇鐵則
**上限** 24h 內最多 1 篇（多發 = 每篇觸及降到 30-50%、演算法判 spam）。
**下限** 不跳過任何一天（跳過 = 演算法活躍訊號 decay）。
**輕重交替**：🔴 高強度（F3/F5/F6）每週 ≤ 2 篇，🔴 後必接 🟢 恢復。

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

### R5：爆款節奏 + 主題冷卻（Day 5 實證升級）
小創作者（<10K 粉）節奏：日常 20-40 讚 × N 天 → 偶爾爆款 → 回到日常。**每月 1-2 個 F6b 就夠**。

**主題冷卻硬規則**（2026-04-25 Day 5 實證）：
- **同一「主題」4 天內不重複**（不是公式，是主題！換公式換時段換 hook 都救不了）
- **主題 = 標題或第一段核心 noun phrase**（例：「skill」「開源」「爆款公式」「社群」）
- **違反成本實證**：Day 5 距 Day 1 只 4 天用相關主題（promo skill 開源）→ 觸及只剩 Day 1 的 0.13%（74K → 95）
- 使用者要「複製爆款」 → skill 必警告 + 建議「換主題或等 7 天後」

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

### R8：Voice Lock — 爆款型必用 Day 1 純血格式（2026-04-28 使用者 override）
**所有 ship / viral / 認真貼文（Mode B）= Day 1 純血格式鎖死**。

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
- Day 6 復盤型 → 7h 57% 非追蹤者突破鐵粉圈

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
