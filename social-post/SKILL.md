---
name: social-post
description: 學使用者的 Facebook 個人貼文語氣，依 14 天內容策略日曆，自動產出並發佈到 FB / Instagram / Threads / X。使用時機：使用者說「發文」、「幫我寫一篇貼文」、「用我的風格發」、「今天發一篇」、「PO 一下」、「學我的語氣」、「分析我的貼文風格」、「重新規劃內容」、「排貼文」、「查流量」、「review」時一律觸發；即使只說「發一篇」、「PO 文」、「PO 個廢文」也要觸發。
---

<!--
  social-post skill — Created by 駱君昊 (Hao)
  Repo: https://github.com/Hao0321/claude-skill-social-post
  Companion skill: https://github.com/Hao0321/claude-skill-code-cleanup
  Facebook: https://www.facebook.com/lo.jain.hao
  Claude Code 台灣交流討論區： https://line.me/ti/g2/DPTQR_XE6IYP8c5lBxsbRwsvEUsxI-70p1jWoA
  License: MIT — 保留此標註即可修改、使用、商用
-->

# social-post

三階段工作流。**依使用者意圖路由，只讀必要 reference**（省 token）。

## 階段路由

| 觸發 | 階段 | 讀 |
|---|---|---|
| `style_profile.md` 不存在 / 說「重新學風格」 | **P1** | `references/learn_style.md` |
| `content_plan.md` 不存在 / 說「重新規劃」「排新 14 天」 | **P0** | `references/phase0_plan.md` + `formulas.md` |
| 說「發文」「今天發一篇」「PO」 | **P2** | `references/generate_and_publish.md` + `style_profile.md` + `content_plan.md` + `formulas.md`（目標公式段）+ `rules.md`（相關規則）+ 目標平台 ref |
| 說「這篇好不好」「查流量」「分析」 | **診斷** | `references/evaluation.md` + `rules.md`（R6/R23/R39/R40）+ 目標 post 戰績 |
| 說「歷史怎麼樣」「Day X 發生什麼」 | **案例** | `references/case_studies.md` |
| 想查某條規則細節 | **規則** | `references/rules.md`（R1-R42 完整版）|

路由前用一句話告知使用者要做哪階段，給糾正機會。

## 先決條件

- `mcp__Claude_in_Chrome__*` 可用（否則停、不模擬）
- 使用者已登入目標平台（登入牆出現請使用者手動登，不自動化）

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
- **🚨 FB / Threads 正文附外部連結（R25 硬規則，絕對禁止）**
- **🚨 AI 腔抽象空詞（護城河／本質／真正的 X）+ staged 開場 + over-narrate（R34 硬規則，要真實不要像 AI 文；日常標點 ，、，── 與 ！ hype 是 proven 裝置照用）**

## 📋 核心規則速查（R1-R42，完整定義見 `references/rules.md`）

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
| **R17** 🧪 | 短影音**養成期**：+50% 是未驗證外部宣稱；實測看鉤住率／完播曲線（Case 46）| 練短影音 |
| **R18** | 儲存 = 次強信號（索取物/framework/清單）| 生成 |
| **R19** ⭐ | Thread ≠ FB；Thread 最強 = 轉發 + keyword | 發 Thread |
| **R20** 🧪 | 漸進改進（**Threads**，F4 → F19 五階；含預估階非全實測）| 過渡升級 |
| ~~R21~~ | 撤回（廢除理由待重驗，見 R24）| — |
| ~~R22~~ | 部分撤回（keyword peak 非主因）| — |
| **R23** | per-view 追蹤轉化率（新評估指標）| 看戰績 |
| **R24** 🧪 | 純血可連發但主題須各換（原量化階梯 2026-07 刪除：無出處）| 連發規劃 |
| **R25** 🚨 | FB/Threads 正文絕不附連結 | 每篇必檢 |
| **R26** | ── 分隔符（Mode C 長文視覺切分）| 生成 Mode C |
| **R27** ⭐ | 個人脆弱 confess = broke 鐵粉圈 90%+ | 生成 Mode C |
| **R28** 🏆 | 行業反主流 framing（Mode C 最強）| 生成 Mode C |
| **R29** | Mode C 同日連發（同 niche + 互補 framing）| 雙篇排程 |
| **R30** 🏆 | FB 社團 cross-post = 留言 5-10x 放大 | 主帳號發完後 |
| **R31** 🛡️ | F24 Brand 邊界澄清時機（月 1 次，trust reset）| 私訊爆/誤解時 |
| **R32** 🌟 | 集體 framing「我們 / 一起」= broke 鐵粉圈 +30-50% | 缺 mega hook 時 |
| **R33** 🧪 | FB 週任務情報：Reels 額度 = 蓋章 R17 該週排；量任務 = 陷阱不追；連 3 指標↑ = 廣推窗口 | 看分析面板時 |
| **R34** 🚨 | 真實 voice：元兇是「詞」不是標點 ── 禁抽象空詞（護城河/本質/真正的X）+staged+over-narrate；日常標點 ，、，proven 裝置（──分隔符/！hype）照公式用；標點一律全形 | 每篇必檢 |
| **R35** 🏆 | keyword CTA「留言『X』」= broke 引擎（6/9：959 留言→93.1% mega 42K）；**預設公開 link 自助**（精選留言，無 DM 天花板+account-safe），DM 只小量高觸用；絕不導 GitHub 正文 | giveaway CTA |
| **R36** 🏆🏆 | demo > claim 母規律：具體成品/可驗證數字碾壓抽象「我很強」；comments ≠ broke | 每篇必檢 / intent 疲勞救援 |
| **R37** 🏆 | value-prop-lead 開場：「它幫你做什麼」碾壓 meta 故事（8x 觀眾 / 21x 儲存）| giveaway/工具 ship |
| **R38** 🧪 | 第三方具體戰績 social proof（works-for-others > I'm great）| 有夥伴用你東西做出成績 |
| **R39** ⭐ | 分享 = 20x 讚跨粉絲圈最強引擎；內容強時走反摩擦 CTA 分享路徑 | 生成 CTA / 看戰績 |
| **R40** 🧪 | Dwell time = 第三廣推信號隱形王牌（查看更多/截圖/revisit）| 設計結構 / 評估 |
| **R41** 🧪 | superlative 放大器：「台灣最大/史上最/破紀錄」掛上去 milestone broke 暴增 | milestone/破紀錄文 |
| **R42** 🧪 | archetype 飽和天花板：連 6+ 篇 F6b 必換 archetype，強化 hook 救不了 | 4 條件全綠仍 fail |

**⭐ = 高頻必讀 / 🚨 = 硬規則 / 🏆 = 最強觸發 / 🧪 = 候選待實證**

### 🎯 Viral 4 條件公式（**平台：FB 文字 Mode B** ／ 成熟度：proven）

```
viral = 4 段 4 句結構 + 純血 voice + 全新敘事意圖 + 黃金時段
```

4 個 AND，任一缺 = 死。**Readability 是隱藏第 5 條件**（meta ≤ 1 層 / 數字 ≤ 3 個/段 / 5 秒讀懂）。詳見 `rules.md`。

⚠️ **這條是 FB Mode B 專用**。Thread 的對應式完全不同：`viral = 1 段不換行 60-150 字 + 敵人／英雄 stance + stance 綁具體當紅 artifact + 熱門 keyword ≥ 2`（R19 ／ F19）—— 不挑時段、不用 4 段 4 句、「！」最多兩個。短影音又是第三套（鉤住率 ／ 完播曲線，見 R17）。

### 🕰️ 三個引擎時代（先認時代，再挑公式）

這個 skill 的規則不是同一個時代、同一個平台長出來的。**同一句話在不同時代會是相反的建議**，先看這段再選公式。

**時代一｜F6b ＝ FB 破圈引擎（2026-04～05，proven，可重複但要換燃料）**

兩顆 mega 都出自這裡，而且**都在星期二 02:13**：4/21 變體 A（meta 自證鉤子）80,050 瀏覽 ／ 94.1% 非追蹤 ／ Line +1,319；5/5 變體 D（社群 social proof）73,622 ／ Line +1,239。**5/5 是月內第 5 個 F6b，照樣打同一級** —— 所以 F6b 不是一次性的，**會膩的是敘事意圖，不是公式**（R5：月配額單位是意圖不是公式）。

⚠️ 但意圖有大小之分：4/28 同樣星期二 02:13、也換了意圖（演算法復盤），只有 2,049 ／ 57%。同意圖重複則直接死：4/22 767、4/25 152、4/29 263。連發同時受 **R5**（同意圖月 ≤ 2）與 **R42**（archetype 飽和）管轄，兩軸取較嚴者。

**時代二｜F19 ＝ Thread 可攜成長引擎（2026-06-25 起，proven，現役導流主力）**

6/25 那篇 plateau 51 萬 ／ 轉發 1,260 ／ 貼文帶來追蹤 4,491 ／ 90.77% 流量來自首頁（純演算法推）。Case 47 樓中樓第二則掛連結 → repo 2k stars ／ 269 forks，對照 FB 端 7/20 四萬瀏覽只換到 **2 個連結點擊**。**而且可攜**：五個獨立夥伴帳號（~100 ／ ~140 ／ ~160 ／ 568 ／ 5,400 粉）各自複製成功，生態轉發紀錄 1,689 還在夥伴手上 —— 格式驅動，不是 charisma。

**今天要導流、要漲追蹤，預設用這個。** ⚠️ 射程：proven 範圍 = **溫熱話題波內可攜**，冷話題未證。⚠️ Thread 不吃 FB 那套：1 段不換行、60-150 字、「！」最多兩個、不挑時段；F4 ／ F6b ／ F14 ／ F15 ／ F16 搬 Thread 必死（R19）。

**時代三｜短影音（FB Reels ／ IG Reels ／ YT Shorts）＝ 養成期新技能（2026-07-30 起，🧪 訓練中）**

**這一層跟上面兩層不同層** —— 它不是公式，是還沒練起來的技能。第一批六支（Case 46）：IG 略過率 72-83%、平均觀看 2-5 秒、分享儲存近 0；同一支竹林秘境 **IG 209 vs FB 1,040**（投錯平台比內容還致命）；三支鉤住率一致 28.8-29.8%、留存全在前 2 秒斷崖；同批連發有順位懲罰（第 2 名 1,040 vs 第 10 名 114）。

**KPI 換一套**：鉤住率 ／ 略過率 ／ 平均觀看秒數 ／ 完播曲線，不是 FB 的非追蹤比例。**YT Shorts 至今零資料**，Meta 那套數字不可外推。這一層所有結論一律 🧪，不進 R 編號、不寫成鐵則。

**常備盤（跨時代）**：Mode A 日常與 Mode C 深度反思是 FB 文字的全期 proven 打法，不屬於任何破圈時代，節奏照 R1 走。

**今天該用哪個**

| 你要什麼 | 用哪個 |
|---|---|
| 導流 ／ 漲追蹤 | **時代二 F19（Thread）** |
| 維持節奏 ／ 深化信任 | Mode A ／ Mode C（FB 文字）|
| 再破一次 FB | **F6b + 全新的大意圖**，排星期二 02:13（先過 R5 ＋ R42）|
| 練短影音 | 時代三 —— 目標是練鉤住率 ／ 完播曲線，**只跟自己上一批比** |

### 🎭 Hao 4 個 Mode（funnel 互補）

| Mode | 公式 | funnel | 鐵粉/廣推 |
|---|---|---|---|
| **A 日常** | 短句吐槽 | 鐵粉黏著 | 90% 鐵粉 |
| **B 純血** | F6b / F15 mini | 擴散 + Line 群 | 90%+ 廣推 |
| **C 深度反思** | F20/F21/F22/F23/F24/**F25a/b/c**/**F26**/**F27**/**F28**/**F29** | 信任深化 + 儲存 + trust reset + 集體 framing + 作品集 reveal + 單品 giveaway + 第三方戰績 + 再ship揭露 | 可 broke 94.5% |
| **Thread F19** | 立場宣言 | Thread 轉發 | Thread 廣推 |
| **活動宣傳** 🧪 | F30 | 報名轉化（**KPI 不是觸及**）| 天生 niche 封頂，不歸 broke 型 |

## 💡 實用技巧

- **作者精選留言**：留言 > 50 時用單則精選留言放 CTA（FB 可放 1 個 URL，正文不行）
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
| R1-R42 規則完整定義 | `references/rules.md` |
| FB 2026 演算法權重 + 4 指標 | `references/evaluation.md` |
| 案例解剖（Cases 1-44 + 開頭 📅 貼文索引）| `references/case_studies.md` |
| F1-F30 公式（開頭有 🧭 分類導航：萬用／推廣／破圈／心得／社群／活動／句式庫）| `references/formulas.md` |
| F19 部署包（工坊使者 Threads 破圈手冊）| `F19_DEPLOYMENT_KIT.md` |
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
