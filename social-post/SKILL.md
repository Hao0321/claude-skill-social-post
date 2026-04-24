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

### R5：爆款節奏
小創作者（<10K 粉）節奏：日常 20-40 讚 × N 天 → 偶爾爆款 → 回到日常。**每月 1-2 個 F6b 就夠**，連發想爆 = 觀眾反感 + 演算法判 self-promo。

### R6：評估看 4 指標，不看絕對讚數
詳見 `references/evaluation.md`。不要用「讚數多少」判貼文好壞，要看：
1. 連結點擊率 > 1%
2. 追蹤者比例
3. 互動率 > 15% 
4. 下游轉化（社群入群 / GitHub star / 付費）

### R7：真正的 KPI 是社群轉化，不是讚
Day 1 實證：374 讚只是表面，**+1,150 Line 社群成員**才是真 ROI。評估爆款值不值得看 downstream：社群人數、star 數、付費學員。

## 💡 實用發文技巧

### 作者留言策略（高留言爆款後）
留言 > 50 時用**單則作者留言**（FB 可設「精選」置頂）包含連結 + CTA 覆蓋所有求訊息者，比逐條個別回更好也更安全。

### 留言框 Enter = 送出
FB / Threads 留言框 `\n` 會被當送出。**留言永遠壓成單行**用 `→` `，` `／` 分隔，不用換行（compose modal 才可多行）。

### FB 原生排程取代 cron
夜貓時段想發 + 不熬夜 = 用 FB「貼文設定 → 排程選項」。細節見 `references/facebook.md`。

## 🔄 持續優化

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
