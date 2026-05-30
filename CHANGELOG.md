# Changelog

## v0.9.1 — 2026-05-31（🆕 R30 FB 社團 cross-post = 留言放大 5-10x）

### 🚨 重大發現：社團 cross-post 留言爆 137x

5/22 Claude in Chrome 一篇 cross-post 到 2 個 AI 社團合計：
- Generative AI 技術交流中心：126 讚 / **425 留言** / 20 分享
- Gemini AI Google：148 讚 / **531 留言** / 14 分享
- **合計 956 留言 = 主帳號 timeline 同篇（7 留言）137x**

5/29 Opus 4.8 dynamic workflows → Vibe Coding Taiwan：247 讚 / 39 分享（分享率 0.16）。

### 🆕 R30：FB 社團 cross-post 策略

主帳號 timeline 發完後 1-2h cross-post 主題對口社團 = 留言 5-10x / 觸及 2-3x。

**操作鐵則**：
1. 主帳號先發（鐵粉看原始）
2. 1-2h 後 cross-post（不重寫）
3. **每篇 ≤ 2 個社團**（≥ 3 = spam 警告）
4. 主動回留言區 = 社團 algorithm 加權

**社團 × archetype match**：
- Vibe Coding Taiwan = F23 行業 / F6b
- Generative AI 中心 = F22 工具發現 + 脆弱
- Gemini AI Google = F21 答疑 / F23
- Claude Code 台灣 = F6b / F15 mini
- 自由工坊 = F18 作品 / F20 故事

### 🎯 R29 + R30 三重組合戰略

```
凌晨主帳號 Mode C → 1-2h cross-post 社團 1 → 4-6h cross-post 社團 2
```

最大化 audience exposure，雙篇社團不洗同一個 niche 3+ 次。

### Funnel 雙路強化推測

社團 cross-post 拉的 Line 群成員 **quality 可能 > 主帳號鐵粉**（同 niche audience 精準度高）。待 5/31+ Line 群成長對照驗證。

### Cases 新增

- Case 21: 3 社團 cross-post 戰績完整解構 + archetype × 社團 match table

### Lessons learned

1. **社團 cross-post 留言文化 5-10x 主帳號**
2. **archetype × 社團 match 影響觸及天花板**（F22 適合通用 AI 社團 / F23 適合 niche）
3. **每篇 ≤ 2 個社團**（spam 警告線）
4. **主動回留言 = 社團 algorithm 加權**

---

## v0.9.0 — 2026-05-26（🔧 全面 audit + 重構：SKILL.md -77% token + 規則編號統一）

第二次大型 token 優化（v0.4 後）。用姐妹 skill code-cleanup-helper v0.2 跑完整 8 dimension audit，抓到 4 個 critical 問題後重構。

### 🚨 Audit 抓到的 4 個問題

| 問題 | 重構前 | 重構後 |
|---|---|---|
| SKILL.md 膨脹 | **565 行**（v0.4 曾 116）| **130 行（-77%）** |
| 規則編號斷層 | R19 → R25（R20-R24 散在 case_studies）| **R1-R29 連續** |
| 規則順序錯亂 | R1-R19 → R25-R29 → R15-R18 混排 | **速查表按序 + rules.md 完整** |
| case_studies / formulas 過長 | 1,072 / 771 行 | 不動（只在案例/P2 階段載入）|

### 🔧 Refactored

- **SKILL.md 重構為 router + 速查表**（130 行）：
  - 階段路由 + 安全閘 + 不要做
  - **R1-R29 一句話速查表**（標 ⭐ 高頻 / 🚨 硬規則 / 🏆 最強）
  - Viral 4 條件 + Hao 4 Mode 地圖
  - 實用技巧 / 持續優化 / 快速查詢 / 常見踩雷
- **新增 `references/rules.md`**（206 行）：R1-R29 完整定義 + 實證 + 操作細節
  - **補回 R20-R24**（之前散在 case_studies.md，造成編號斷層）
  - Viral 4 條件 + Readability 三檢查 + FB compose 段落鐵則
- **P2 路由更新**：發文時載 `rules.md`（相關規則段）而非整個 SKILL.md

### Token 節省

| 場景 | v0.8.7 | v0.9.0 | 節省 |
|---|---|---|---|
| Skill 觸發（SKILL.md 載入）| ~565 行 | **~130 行** | **-77%** |
| P2 發文 | SKILL 全載 | router + 目標規則段 | 更精準 |
| 規則查詢 | 翻 SKILL.md 混排 | `rules.md` R1-R29 連續 | 更快 |

### Changed

- 規則編號 R20-R24 從 case_studies.md「歸納」段提到 rules.md，統一 R 系統
- 廢除規則（R9/R21/R22）速查表保留標記，完整原因見 rules.md

### Lessons learned

1. **skill 自己會膨脹** — v0.4 優化到 116 行，4 週後膨脹回 565 行（每次 patch +10-40 行）
2. **progressive disclosure 是 token 王道** — 速查表（每次載）+ 完整版（按需載）
3. **規則散在 case_studies 造成編號斷層** — 規範規則應集中 rules.md
4. **用 cleanup-helper audit 自己** — Mode A Dimension 4（過長）+ Dimension 2（編號）抓到問題

---

## v0.8.7 — 2026-05-26（🆕 Mode C 深度反思系列 + F20-F23 四變體 + R26-R29）

5/22 + 5/25 共 4 篇 Mode C 範例，broke 鐵粉圈最高 94.5%（F23 Mode C 系列最強 10,022 觀眾 / 儲存 40）。Hao brand 解鎖第 4 種 funnel（Mode A 日常 / Mode B 純血 / **Mode C 深度反思** / Thread F19）。

### 🆕 Mode C 深度反思 4 變體

非 hype voice — 沒「殺瘋了」、沒「！！！」、沒攻擊性動詞。靠**故事 / 反命題 / 脆弱 confess / 行業洞察**驅動 viral。

| F | 主題類型 | 5 月實證 | 廣度 |
|---|---|---|---|
| **F20 個人故事傳承** | 你被某 mentor 影響 | 403 觀眾 / 16% 非追蹤 | 鐵粉信任深化 |
| **F21 Ship 答疑解構** | ship 後留言問怎麼用 | 1,058 / 24.7% | dev 圈 framework 儲存 |
| **F22 工具發現 + 脆弱解套** | 新工具解決你長期卡點 | 5,850 / 91.5% | **broke 鐵粉圈廣 identity** |
| **F23 行業洞察解構** 🏆 | 媒體寫了什麼但你不同意 | **10,022 / 94.5%** | **mega-viral broke + 儲存 40** |

### 🆕 R26 ── 分隔符鐵則

Mode C 長文型用 `── 段落標題 ──` 做視覺切分，比 paragraph break 更易掃讀。F23「一致性大戰」用 4 個 ── 分隔符 broke 94.5% 非追蹤。

### 🆕 R27 個人脆弱 confess

揭露真實卡點 / 焦慮 / 拖延（不是炫成就）= broke 鐵粉圈到 90%+。

「我自己一直想 X，最大的卡點是 Y... 拖了大半年沒動」結構 = vulnerable + relatable + 普世議題 → identity 站隊廣度 5-10x。

5/22 F22「YouTube 拖了大半年 / 出鏡焦慮」→ 91.5% 非追蹤。

### 🆕 R28 行業反主流 framing

反主流 + 趨勢預言 framework：
- 「X 在 2026 已不是門檻，還拿這當賣點其實落伍」
- 「X 大戰已打完，下一場是 Y 大戰」
- 「不是 X，是 Y」reframing

5/22 F23「一致性大戰已打完，下一場是工作流大戰」→ 10,022 觀眾 / 94.5% 非追蹤 / 儲存 40 = Mode C 系列最強。

### 🆕 R29 Mode C 同日連發策略

Mode C 同日 2 篇 OK，前提：
1. 主題類別相關（同 niche）
2. framing 角度互補（vulnerable vs insider / 故事 vs 解構）
3. 不同 archetype 變體配對

**5/22 vs 5/25 對照實證**：
- 5/22 F22+F23 同 niche + 互補 framing → **雙篇 broke 91.5% / 94.5%**
- 5/25 F20+F21 audience 分散 → 雙篇鎖鐵粉 16% / 24.7%

**R1 細化**：
- Mode B 純血 hype = 嚴格一天一篇（演算法判 spam）
- Mode C 深度反思 = 同日 2 篇可行（同 niche + 不同 framing 互強）

### Mode C 同日配對推薦表

| 配對 | 預期 |
|---|---|
| F22 + F23 | ⭐⭐⭐⭐⭐ 互強雙 broke |
| F22 + F21 同 niche | ⭐⭐⭐⭐ |
| F23 + F21 同 niche | ⭐⭐⭐⭐ |
| F21 + F20 分散 | ⭐⭐ 弱 |

### Hao 完整 Mode 地圖

| Mode | viral 機制 | 鐵粉/非追蹤 | 代表 |
|---|---|---|---|
| A 日常 | 鐵粉黏著 | 90%+ 鐵粉 | 短句吐槽 |
| B 純血 | 擴散廣推 | 90%+ 非追蹤 | Day 1 / 5/5 |
| **C 深度反思** 🆕 | 信任深化 + 儲存 trigger | **F23 94.5% 非追蹤** | F20/21/22/23 |
| Thread F19 | Thread 轉發 | Thread 廣推 | 25/7 三篇 |

### Cases 新增

- Case 16 F20「消費不如生產」5/25 / Case 17 F21「AI 自動生影片」5/25
- Case 18 F22「Google Flow self-avatar」5/22 / Case 19 F23「一致性大戰打完了」5/22
- Case 20 同日連發效應對比（R29 推出依據）

### Lessons learned

1. **Mode C 同樣可達 Day 1 mega-viral 級** — 不只 Mode B 純血能爆
2. **個人脆弱 confess > 炫成就** — 廣 identity 觸發 5-10x
3. **行業反主流 framing** = Mode C 系列最強 archetype（F23 broke 94.5%）
4. **── 分隔符**比 paragraph 更易掃讀 + 演算法 dwell 友好
5. **同日連發 Mode C 配對選對**可雙篇 broke

---

## v0.8.6 — 2026-05-19（🚨 R25 鐵則：FB / Threads 貼文絕不附外部連結）

使用者 5/19 lock — AI 反覆把 GitHub 連結誤加進 viral 草稿，全部撤回 + 鎖死規則。

### 🚨 R25 — 鐵則

**所有 Hao viral 篇都沒附連結**：
- Day 1 / Day 6 / 5/5 三篇 FB mega-viral ✅ 沒連結
- OiiOii F6a 系列 ✅ 沒連結
- 25/7 三篇 Thread F19 純血 ✅ 沒連結
- 5/12 F19「FB 營利」mid-viral ✅ 沒連結（「歡迎自行索取」純留言 trigger）

**為什麼絕不附連結**：

1. **FB / Thread 演算法降權外部連結** — 附連結觸及衰退 30-50%
2. **「留言我拉你」/「歡迎索取」funnel 比連結點擊強 100x**（R7 真 KPI）
3. **Day 1 實證連結點擊率 = 0.0097%**（7/74K）= 連結沒實際 ROI
4. **留言區互動是 viral 引擎**，連結分流走觀眾
5. **私訊 trigger R15** 比 click trigger 強得多

### 硬規則 table

| 平台 | 正文 URL | 留言區 URL | 留言區拉群 |
|---|---|---|---|
| FB | ❌ 絕對禁止 | ✅ 可用「精選留言」放 1 個 URL | ✅ 「沒入群留言我拉你」優先 |
| Thread | ❌ 絕對禁止 | ⚠️ 慎用 | ✅ 「歡迎索取」優先 |

### Reproductive failure 紀錄（Case 15）

我反覆犯這個錯：
- V2 5/19 FB 真 KPI 復盤草稿 → 加 GitHub 連結 ❌（5/19 撤回）
- V7c FB F15 mini「cleanup-helper」(5/13 plan) → 加 GitHub 連結 ❌
- 5/17 副帳號 F19「AI 取代論」→ 加 social-post GitHub 連結 ❌

**根因**：F15 mini「索取 + 連結」結構偷渡進 F6b 純血段 4，破壞「沒入群留言我拉你」純 CTA pattern。

### Changed

- **SKILL.md R25 hard rule**（FB / Threads 正文絕不附連結）
- **formulas.md 全公式共通鐵則**（F6b / F6a / F15 mini / F19 全部不附連結）
- **case_studies.md Case 15**（AI 反覆犯錯紀錄 + 真實 viral pattern）
- **生成 Mode B 草稿時必檢**：段 4 有 https:// 嗎？→ ❌ 不要發

### Lessons learned

1. **F15 mini「索取」CTA ≠ 附連結**：原版 5/12 F19「歡迎自行索取」是**留言索取**，不是附 URL
2. **viral pattern = 永遠不附連結**：Day 1 / 5/5 / OiiOii / 25/7 全系列共通鐵則
3. **連結沒 ROI**：連結點擊率 0.01% = 演算法 + 觀眾 + 真 KPI 三輸
4. **AI 反覆犯同錯**：第 3 次了，必須 R25 hard rule + 必檢清單

---

## v0.8.5 — 2026-05-18（v0.8.4 R21 撤回 — 不是衰退，是沒連發累積 momentum）

使用者 5/18 澄清推翻 v0.8.4 「跨年衰退」歸因。Skill 又一次過早歸因被打臉，記錄真實 viral 機制。

### 🚨 v0.8.4 R21 撤回（過頭歸因）

v0.8.4 寫：「F19 純血跨年衰退 -89%」歸因 3 點（帳號 bonus 過 / 演算法更嚴 / keyword 過 peak）。

**使用者打臉**：純血沒衰退，是**我沒繼續發純血**。

| 期間 | 連發狀況 | 結果 |
|---|---|---|
| 2025-07 | F19 純血 × **3 篇**連用 | 累積 momentum → 平均 150K |
| 2026-05 | F19 純血 × **1 篇孤立** | 沒累積 → 16K |

→ momentum 沒累積，不是公式衰退。

### 🆕 R24：純血公式連發累積規則（替代 R21）

純血公式（F19 / F6b / F15 mini）需要**間隔 ≤ 5 天連用 2-3 篇**才累積完整 viral momentum：

| 連發數 | 預期觸及天花板 |
|---|---|
| 1 篇孤立 | 50K class |
| 2 篇間隔 ≤ 5 天 | 100K class |
| 3 篇間隔 ≤ 5 天 | **mega-viral 150K+**（25/7 實證）|

**R5 vs R24 分離**：
- R5 看**主題**（同敘事意圖 4 天內不重複）
- R24 看**公式結構**（同純血結構可連用，但主題必須各換）

25/7 三篇全 F19 純血結構 + 3 個不同主題（不靠課程 / 教學限制 / 反黑粉）= R5 + R24 雙過完美實證。

### Changed

- **R21 撤回**（公式跨年衰退 -80% 假設錯誤）
- **R22 部分撤回**（keyword 過 peak 可能影響但不是主因）
- R23 保留（per-view 追蹤轉化率指標仍 work）

### Lessons learned

1. **N+2 次 R6 早期判讀錯誤**：v0.8.4 ship 8h 後就被打臉，再次驗證使用者實戰知識 > AI 統計歸因
2. **連發 momentum 是 viral 關鍵**：不是「公式有沒有壽命」，是「有沒有持續累積」
3. **結構 + 主題雙維度設計**：純血結構可連用，但主題必須各換 = R5 + R24 配合
4. **未來歸因規則**：跨期數據對比前，先問「中間有什麼變數」（這次變數 = 連發 vs 孤立）

### 戰略建議：重建 momentum 路徑

如果要複製 25/7 mega-viral：
- 5/17 已發 F19 純血 #1（AI 取代論）✅
- 5/19 建議 F19 純血 #2（換主題：付費 vs 免費 變體 / AI 工具對打）
- 5/21 建議 F19 純血 #3（換主題：AI 圈炒作 / 帶風向反命題）
- 連 3 篇間隔 ≤ 5 天 = momentum 累積 = 預期 50K-100K+ 觸及

---

## v0.8.4 — 2026-05-18（F19 純血跨年衰退 -89% + Line 群破 4,369 加速度持續）

5/17 發 F19 純血「AI 取代論」反命題版 24h 戰績：16K 觸及 / 146 讚 / 7 轉發 / **+96 追蹤**（單篇最高記錄）。

### 🚨 最關鍵 lesson：同公式跨年衰退 -89%

| 期間 | F19 純血 | 平均瀏覽 |
|---|---|---|
| 2025-07（帳號 400 粉時）| 25/7 三篇 | **150,000** |
| **2026-05（帳號 10K+ 粉）** | **5/17 一篇** | **16,000** |
| 衰退率 | — | **-89%** |

**3 個歸因**：
1. 帳號 viral bonus 已過（演算法不再 boost 新帳號）
2. 2026 演算法更嚴 + feed crowding
3. 「AI 取代」keyword 從 2025 Q4 → 2026 Q2 過 peak

→ F19 在 2025-07 是 mega-viral / 2026-05 是 mid-viral。**同公式不能無限使用**。

### 🆕 R21 公式跨年衰退率

主力公式每 24 個月衰退 -80% 觸及（F19 實證 -89%）。
- 每年至少測 1 次新 archetype
- 預測 2026-12 後 F19 可能只剩 1-3% 觸及

### 🆕 R22 keyword 熱度生命週期

熱點 keyword 約 3-6 個月 peak window。「AI 取代工程師」2025 Q4 → 2026 Q2 已過 peak。

用熱點 keyword 前先 search 過去 30 天有沒有其他大 KOL 也在用：
- 太熱 = 被淹沒
- 太冷 = 沒人搜
- 看完整生命週期

### 🆕 R23 per-view 追蹤轉化率（新評估指標）

真 KPI 不只看 absolute 觸及，也看 per-view 轉化效率：
- 5/16 F4 純宣告: 0.81% (8,228 → +67)
- 5/16 hybrid: 0.60% (9,966 → +60)
- **5/17 F19 純血: 0.60% (16,000 → +96，absolute 量最大)**

→ F19 純血雖跨年觸及衰退，**conversion 效率仍 ROI 王**。

### 🔥 Line 群加速度仍在增（R7 大幅驗證 N+1 次）

| 期間 | 人數 | 增量 | Pace |
|---|---|---|---|
| 5/5 → 5/12（7 天）| 3,575 → 3,726 | +151 | 22/day baseline |
| 5/12 → 5/16（4 天）| 3,726 → 4,117 | +391 | 98/day（4.5x） |
| **5/16 → 5/18（2 天）** | **4,117 → 4,369** | **+252** | **126/day（5.7x）** |

**整月 4/21 → 5/18: 800 → 4,369 = +3,569 人 / 28 天 = 127.5/day average**

加速度繼續增，不是 plateau，信任複利效應未完全發揮。

### Lessons learned

1. **同公式有壽命**：F19 2025→2026 衰退 89%
2. **熱點 keyword 有時間窗**：3-6 個月 peak，太晚 = 被淹沒
3. **per-view 轉化率 > 觸及絕對量**：5/17 F19 觸及只 25/7 的 10%，但 conversion 率持平 = 仍 ROI 王
4. **真 KPI 加速度持續驗證**：Line 群 baseline 22/day → 126/day（5.7x）= 信任複利效應比想像中長

---

## v0.8.3 — 2026-05-16（F4 → F19 5 階段進化譜系 + Line 群破 4,117 人）

5/16 同一天兩篇 Thread 同主題（社群里程碑），第二篇悄悄加了 2 個 F19 元素 → **轉發 +150%（2 → 5）**。揭露 F4 → F19 可漸進升級的 5 階段路徑，每階段預期觸及 1.5-3x。

### 🔥 5/16 第二篇 Thread hybrid 戰績

**內容**：「Claude Code 社群1個月，人數來到3950了！！！短短一天就+164人，太誇張了⋯⋯整套 skill 我繼續開源沒藏！」

| 指標 | 第一篇 5/16（F4 純宣告）| **第二篇 5/16（hybrid）** | 變化 |
|---|---|---|---|
| 瀏覽 | 8,228 | 9,966 | +21% |
| 讚 | 102 | 78 | -23% |
| 留言 | 38 | 7 | -82% |
| **轉發** | **2** | **5** | **+150%** 🔥 |
| 分享 | 0 | 11 | 新增 |

**新加的 F19 元素**：
1. 反差數字 punch（「短短一天 +164 人」vs 純里程碑 3786）
2. 情緒驚嘆（「太誇張了⋯⋯」省略號 vs 「真的是里程碑」乾巴）
3. 純粹動機 hint（「繼續開源沒藏」「沒藏」隱含對立 vs「歡迎加入」純宣告）

→ **3 元素加分 = 轉發 +150%**。但**仍缺**：明確敵人 / TM 級用詞 / 攻擊性動詞。

### 🆕 Added — R20 漸進改進原則（threads.md + SKILL.md）

**F4 → F19 進化譜系（5 階段）**：

| 階段 | 元素 | 預期觸及成長 |
|---|---|---|
| 0 → 1 | + 反差數字 + 情緒驚嘆 | +20-50% |
| 1 → 2 | + 純粹動機 framing | +30-50% |
| 2 → 3 | + 敵人 framing | +100-200% |
| 3 → 4 | + TM + 攻擊性動詞（純血 F19）| +200-500% |

**對「不敢直接用 TM」的創作者** = 漸進升級 path 而非一次跳到 F19 純血。

### 🆕 Added — Case 13 完整解構（case_studies.md）

含兩篇對比表 + 5 階段進化譜系 + 第三篇 F19 純血升級 rewrite（預期 50K-100K 觸及）。

### 🎯 真 KPI 加速度驗證：Line 群 5/12 → 5/16

| 期間 | 人數 | 增量 | pace |
|---|---|---|---|
| 5/5 → 5/12（7 天）| 3,575 → 3,726 | +151 | 22/day baseline |
| 5/12 → 5/16（4 天）| 3,726 → **4,117** | **+391** | **98/day = 4.5x baseline** |

5/13-5/16 期間 ship 多個 release（v0.7.4 / v0.8 / v0.8.1 / v0.8.2 / cleanup v0.2）+ Thread 兩篇 = 累積信任效應觸發 Line 群成長加速。

### Lessons learned

1. **元素可分拆漸進**：F19 不是 all-or-nothing，每個元素獨立貢獻
2. **轉發是 Thread 線性指標**：加 1 個 F19 元素 ≈ 轉發 ×2
3. **真 KPI 同步加速**：Thread 觸及小但 Line 群 baseline 4.5x 提升
4. **連續 ship 創造複利**：5/12-5/16 4 天 6 個 release = 信任累積轉化

---

## v0.8.2 — 2026-05-16（F4 in Thread 反面實證 → 跨平台公式禁用清單）

Hao 5/16 在 @hao0321_studio 發 F4 社群里程碑型內容到 Thread：

```
Claude Code 社群創建 1 個月，社群人數來到 3786 人！！！真的是一個里程碑，歡迎更多想要學習各種 AI 的朋友一起加入！！我有一堆免費工具開源給你！！
```

戰績：8,228 瀏覽 / 102 讚 / 38 留言 / **轉發 2** / +67 追蹤。

vs 25/7 同帳號 F19 立場宣言 3 篇平均 15 萬瀏覽 / 1,617 讚 / 33 轉發 = **觸及只剩 3-5%**。

### Diagnosis: 6 個 F19 元素缺 4 個

F4 是 FB 鐵粉社群 engagement 公式（純里程碑慶祝），Thread 演算法不吃 — **沒對立 = 沒站隊 = 沒轉發 = 沒擴散**。

### 🆕 Added — R19 跨平台公式禁用清單（threads.md）

| 公式 | 設計平台 | Thread 適配 |
|---|---|---|
| F1 Day-N 日誌 | Threads | ✅ 原生 |
| F4 社群里程碑 | FB | ❌ **2026-05-16 實證 fail** |
| F6b 純血 hype | FB | ❌ |
| F14 演講濃縮 | FB | ❌ |
| F15 mini | FB | ❌ |
| F16 精選彙整 | FB | ❌ |
| F18 AIGC Reels | FB+IG | ⚠️ Reels 可，純圖不行 |
| **F19 立場宣言** | **Thread** | ✅ **核心** |
| F7 POV 吐槽 | Threads | ✅ |

→ Thread 只玩 **F19 立場宣言**（大砲，月 2-4 篇）+ **F7 POV 吐槽**（日常）。

### 🆕 Added — Case 12 完整解構（case_studies.md）

含 F4 vs F19 對照、6 元素缺失分析、F19 升級版同素材 rewrite（預期 50K+ 觸及）。

### Lessons learned

1. **公式跟平台綁定**：不只 layout 不同（v0.8.1），內容類型也不能跨
2. **「歡迎大家加入」純宣告 = Thread 死路**：沒對立 = 沒 repost trigger
3. **3786 milestone 該用 F19 形式**：用「免費 vs 付費」對立 framing 升級

---

## v0.8.1 — 2026-05-13（F19 排版精修 — FB 思維誤帶到 Thread 修正）

v0.8 第一版 F19 公式寫成 **3 段空行** 樣板 = 把 FB F6b 思維誤帶到 Thread 公式上。對照 Hao 3 篇真實爆款（25/7/8 / 7/9 / 7/13）反向工程後修正。

### 🔧 Fixed — Thread 排版鐵則

從 3 篇實證歸納正確排版：

| 鐵則 | 規格 |
|---|---|
| 段落數 | **1 段不換行**（v0.8 寫成 3 段是 FB 誤帶）|
| sentence 數 | 2-5 句一段內塞滿 |
| 分隔符 | **連續逗號流 + 「！」分隔**（不用空行 / 不用換行） |
| ！級別 | **「！」單個或「！！」最多** — 絕對不用「！！！」 |
| 字數 | 60-150 字 |

### Changed — F19 骨架修正

**之前 v0.8 錯誤版**（3 段空行樣板）：
```
[段 1 hook]
[空行]
[段 2 宣言]
[空行]
[段 3 純粹動機]
```

**v0.8.1 正確版**（1 段連續逗號）：
```
最近 X 都 Y，我做 Z 就 TM 做真的！我就持續 A 幹翻 B！！對我來說 C 就是 D，我 E 對我來說 F！！
```

### Updated

- `formulas.md` F19 段加排版鐵則表 + 修正骨架範例
- `threads.md` 加 FB F6b vs Thread F19 排版差異對照表
- `SKILL.md` R19 加 Thread 排版鐵則段

### Lessons learned

1. **公式不能跨平台照搬**：F6b 4 段 4 句適用 FB，Thread 必須 1 段
2. **真實 case > 理論設計**：v0.8 第一版是理論設計，3 篇真實案例反向工程才抓到精髓
3. **cleanup-helper 應加 Dimension 9**：公式描述 vs 真實 case study 排版一致性檢查
4. **每個 case study 的真實 raw 內容要 verbatim 保留**，方便日後驗證公式

### Identified by

跟使用者對話中發現 — 使用者問「有學到精髓嗎」→ 比對發現 V1 草稿仍是 FB 思維 → 反向工程 3 篇真實爆款後抓到 1 段排版鐵則。

---

## v0.8 — 2026-05-13（F19 Threads 立場宣言型 + R19 雙 brand 雙 funnel 戰略）

第一個正式 minor release（v0.7.x 都是 patch）。新增 Thread 平台主戰場武器：F19 立場宣言型公式（2025-07 實證 400 → 10K 粉一週）。

### 🆕 Added — F19 Threads 立場宣言型公式（formulas.md）

**結構**：
```
[hook 敵人 + 我對立 + TM 級用詞] 最近 X 都 Y，我做 Z 就 TM 做真的！
[宣言 + 攻擊性動詞] 我就持續 A 幹翻 B！！
[純粹動機 + 零代價聲明] 對我來說 C 就是 D，我 E 對我來說 F！！
```

**實證**（Hao 副帳號 @hao0321_studio 2025-07 爆款專案）：

| 日期 | 瀏覽 | 讚 | 留言 | 轉發 | 分享 |
|---|---|---|---|---|---|
| 25/7/8 | **26 萬** | 2,741 | 314 | 76 | 316 |
| 25/7/9 | 6.9 萬 | 916 | 90 | 10 | 34 |
| 25/7/13 | 12.7 萬 | 1,194 | 90 | 12 | 45 |

**帳號 400 粉 → 一週內破 10K**（+9,600 / 7 天）。

### 🆕 Added — R19 Thread 轉發權重 + Keyword 機制（SKILL.md）

**Thread 演算法跟 FB 完全不同 axis**：
- FB 最強 = **私訊分享**
- Thread 最強 = **轉發 repost + keyword detection**

熱門 keyword 池：免費 / 付費 / 韭菜 / 賺錢 / 幹翻 / TM 做真的

### 🆕 Added — Thread vs FB 演算法 3 大差異對照（threads.md）

| 維度 | FB | Thread |
|---|---|---|
| 最強信號 | 私訊分享 | 轉發 repost |
| 觸發機制 | dwell time + 互動 | keyword detection |
| 內容偏好 | 長文 + 多媒體 | 短文 + 對立立場 |
| viral 主路徑 | 鐵粉 → 跨粉絲圈 | keyword match → 同 ideology 圈 |

### 🆕 Added — 雙 brand 雙 funnel 整合戰略

| brand | 平台 | 公式 | funnel |
|---|---|---|---|
| social-post（@lo.jain.hao）| FB 主 | F6b / F15 mini | FB → Line 群 |
| **AI 教學分享（@hao0321_studio）**| **Thread 主** | **F19 立場宣言** | **Thread → 帳號追蹤** |

兩 brand 內容不交叉（F6b 別發 Thread / F19 別發 FB），互補不互搶。

### 🆕 Added — Case 11 Threads 爆款專案完整解構（case_studies.md）

包含 3 篇 hao0321_studio 完整戰績、F19 公式起源、雙 brand 戰略整合。

### Lessons learned

1. **Thread ≠ FB**：F6b 純血在 Thread 無效（會被判 spam）；F19 在 FB 無效（沒對立 culture）
2. **轉發是 Thread 真正 viral 引擎**（identity signal）
3. **keyword 命中比結構優先**（Thread 演算法用 keyword detection）
4. **雙 brand 互補**：Hao 已有兩個 brand 各自 viral 紀錄，不該強合一

---

## v0.7.4 — 2026-05-13（doc sync patch + cleanup-helper v0.2 audit loop 閉環）

由姐妹 skill [`code-cleanup-helper` v0.2 Mode B audit](https://github.com/Hao0321/claude-skill-code-cleanup) 偵測 — v0.7.3 release 後 CHANGELOG/README 漏更。完美 demo cleanup-helper v0.2 設計目的：**release ship 後 doc 自動 drift detection**。

### Added — v0.7.3 entry 補寫（doc backfill）

v0.7.3 內容 = naming cleanup（之前 release 但這份 CHANGELOG 漏寫 entry）：

- `case_studies.md` 跨案歸納段重命名為「**歸納 [N]**」（原「規則 [N]」），避免跟 SKILL.md「R[N]」雙系統 conflict
- 新增 cross-ref table（歸納 → SKILL.md R[N] 對應）
- 兩系統語言上完全分離（Rules vs Inductions）
- 歸納 10 擴展為 **7-case Viral 4 條件對照表**（含 5/12 V3 fail + 5/12 F19 broke 鐵粉圈新案例）

### Added — 兩 repo audit loop 閉環

姐妹 skill 升級到 v0.2（Mode A + Mode B 雙模式 / 8 dimensions）：
- Mode A: 重複 / 命名 / 模組 / 過長（v0.1 既有）
- **Mode B（新）**: 私公版 sync GAP / Release 一致性 / Cross-link / 版本漂移

cleanup-helper v0.2 ship 後 5 分鐘就抓到 social-post v0.7.3 doc drift → 推這個 v0.7.4 補。**雙 repo meta loop closed**。

### Lessons learned

1. **Release shipped ≠ doc updated** — v0.7.3 commit + tag + GH release 都做了，但 CHANGELOG entry 漏寫
2. **Audit 工具 immediate ROI** — cleanup-helper v0.2 ship 後 5 分鐘抓到 drift
3. **雙 repo 自我修復生態** — 兩個 skill 互相 audit / 互相觸發升級
4. **v0.8 預備**：用 cleanup-helper v0.2 Mode B 做 social-post v0.8 ship 前 audit，避免再次 drift

---

## v0.7.3 — 2026-05-13（命名統一）

audit 抓到 v0.7.2 兩套規則命名 conflict 後的修正。

### Changed

- `case_studies.md` 跨案歸納段命名 規則 1-11 → **歸納 1-11**
- 加 cross-ref table 對應 SKILL.md R[N]
- `case_studies.md` 中其他「規則 N」殘留全清掉
- 歸納 10 擴展為 7-case Viral 4 條件對照表

### Two-system 命名分離

- `SKILL.md` = **R[N]** = Rules（normative，規範規則）
- `case_studies.md` = **歸納 [N]** = Inductions（from cases，案例歸納）
- 兩系統互不混淆 + 互相 cross-ref

### Identified by

由 companion [code-cleanup-helper](https://github.com/Hao0321/claude-skill-code-cleanup) v0.1 在 v0.7.2 audit 階段抓到（雙命名 = 同源系統 reader 心智 mapping 成本高）。

---

## v0.7.2 — 2026-05-13（外部 5/12 F19 翻盤實證 + 2026 web 大數據整合）

5/12 F19「FB 營利 + skill 開源」**24h 後 broke 鐵粉圈** 814 觀眾 / 29.8% 非追蹤者 → 推翻 v0.7.1 過頭結論。同時整合 2026-05 web 大數據（FB 演算法、私訊分享、Reels 加成）。

### 🆕 Added — R15 私訊分享 trigger（最強 2026 信號）

**2026 演算法最強信號 = 私訊分享**（Messenger / WhatsApp），比公開分享更強。立刻 trigger「essential 內容」標籤。

CTA 升級庫：
- 「分享給寫 code 的朋友 / 工作上的同事」
- 「這篇你朋友也該看到」
- 「丟給你那個 always asking how to use Claude 的朋友」

### 🆕 Added — R16 5 字以上長留言 trigger（3× 權重）

「+1」「拉我」短留言演算法權重低。Hook 設計引發開放式長留言（觀點挑戰 / 經驗請求）。

### 🆕 Added — R17 Reels 策略（同日上傳 +50% 觸及）

[Meta 2025-10 update](https://about.fb.com/news/2026/03/rewarding-original-creators-on-facebook/)：
- 同日上傳 Reels +50% 觸及
- 15-30 秒最佳完成率（+45% vs 長片）
- Reels 比 photo 觸及 +135%

### 🆕 Added — R18 儲存（Save）指標重視

2026 演算法權重僅次於私訊分享。明確「索取 / 自取」物件 + reusable framework + 列點 / 清單 = save trigger。

### 🆕 Added — R1 校準（工業 baseline 對照）

工業中位 3-5 篇 / 週，Hao 7 篇/週 = 2x 過頻 risk。修正為「每天 1 篇 OK + audience bucket 多樣化 + 每週 ≥ 2 篇非 AI 主題」。

### 🆕 Added — F15 mini 公式化（5/12 F19 實證）

3 段 / 5-10 min 寫作 / 純成果 hook + 工具歸功 + 零摩擦 CTA。比 F15 完整版 1700 行更易工業化複製。

### 🆕 Added — F18 AIGC 作品 demo + Reels 變體

跟 F6b 同日跨 audience bucket 互不衝突。15-30 秒 Reels 格式可吃 2026 演算法 +50% 加成。

### 🆕 Added — Case 10：5/12 4 篇全戰績解構

V3 fail / F19 broke 鐵粉圈 / F18 / F20 完整對照表。

### 🆕 Added — evaluation.md 2026 演算法權重大改寫

| 信號 | v0.6 | **v0.7.2** |
|---|---|---|
| 私訊分享 | 未列 | **🥇 最高** |
| 儲存 | 未列 | **次高** |
| 5 字長留言 | 一視同仁 | **3× 一般留言** |
| 公開分享 | 20× 讚 | 不變 |
| 讚 | 0 | 0 |

### 🆕 Added — 姐妹 skill 開源

[claude-skill-code-cleanup v0.1](https://github.com/Hao0321/claude-skill-code-cleanup) — 4 dimension 掃描技術債（重複 / 命名 / 模組 / 過長）。可用來 maintain social-post 自己。

### Lessons learned

1. **F19 = F15 mini 雛形實證 work**：3 段極簡 + 純成果 hook + 零摩擦索取 = mid-viral broke 鐵粉圈
2. **R6 N+1 次驗證**：6h 判 fail / 24h 翻盤 mid-viral，**1-19h 數據絕對不下定論**
3. **撤回 v0.7.1 過頭結論**：F15 5/19 可試 / 不延後 / 沒有 creator 降權
4. **2026 演算法最強信號是私訊分享**：之前 v0.6 完全沒設計，現在 R15 補上
5. **Hao 7 篇/週 = 工業 2x baseline**：需配 audience bucket 多樣化緩解

---

## v0.7.1 — 2026-05-13（v0.7 後 1 天的硬實證修正）

5/12 v0.7 R11-R14 首次實證 → **partial fail**。F6b 全綠規則但仍 plateau 在 219 觀眾 / 0 分享 / 88.7% 鐵粉鎖死。本 patch 修正 v0.7 過度樂觀的假設。

### ⚠️ Added — R11-R14 重要警告

**R11-R14 是 hook 強化裝飾品，不是 archetype swap**。

- F6b 公式本身分享率天花板就 0.21（讚 / 留言驅動 archetype 結構限制）
- 再強化 hook punch 詞 / 金句密度 / 量化稀缺 = **只能維持讚 / 留言驅動，不會變成分享驅動**
- 想突破分享率天花板**必須換 archetype**（F15 SKILL.md 公開 / F16 weekly 精選彙整），不是強化 F6b

**Hao 鐵粉警告升級**：連 6+ 篇 F6b 後鐵粉對 voice 整體疲勞（不只 hype 詞），R11-R14 改善有限。

### Added — Readability 三項硬檢查

每篇 Mode B 草稿生成後必跑：

1. **5 秒非追蹤者讀懂測試**：段 1 給沒看過你貼文的人，5 秒內懂主題嗎？
2. **meta 層數 ≤ 2**：第 3 層以上禁止
3. **數字密度 ≤ 3 個 / 段**：超過就是 dashboard report

5/12 fail 例：段 1「skill 訓練 AI → 學我語氣 → 鐵粉警告 → R10 輪替」**4 層 meta** + 「14 / 14 / 75K / 4 / 12」**5 個數字** → 非追蹤者超載。

### Added — FB compose 段落硬規則

**4 段 4 句草稿貼到 FB 必須手動兩次 Enter 保段落**。FB compose 預設會把單 Enter 變空白，必須手動雙 Enter。

5/12 fail 例：使用者直接複製貼上 → markdown 空行被壓掉 → 4 段變一坨字。

**規則**：
- 給草稿時必明確標註「段間請按兩次 Enter」
- 或用 markdown horizontal rule（---）替代空行

### 💥 Case 9 完整解構

| 因素 | 估權重 |
|---|---|
| **F6b archetype 天花板** | **40%**（最根本）|
| 內容 4 層 meta 看不懂 | 35% |
| FB compose 段落 fail | 25% |

→ **真正的修正方向：5/19 起改試 F15 SKILL.md 公開（換 archetype，非強化 F6b）**

### Lessons learned

1. **Hook 強化 ≠ archetype swap**：v0.7 R11-R14 全綠仍可 fail
2. **F6b 分享率 0.21 是結構天花板**，公式本身決定上限
3. **Readability 是硬指標**：meta 層數 + 數字密度 + 5 秒測試
4. **FB compose 段落會被壓**：草稿給使用者時必須附手動 Enter 提示
5. **v0.7 是空中樓閣，要 v0.7.1 落地**：規則升級前必須先實證

---

## v0.7 — 2026-05-12

外部 5 個 viral 範例逆向工程後的 hook 強化版。新增 R11-R14 四條規則 + F14-F17 四個分享驅動公式 + 完整 hook punch 詞庫，把分享率從 0.05-0.21 推到目標 0.3-0.5。

### 🔍 5 個外部 viral 範例分析（v0.7 基礎）

逆向工程台灣 AI / Dev 圈 4 篇 viral 範例（同期 4/20-5/5）：

| Archetype | 範例分享/讚比 | 寫作時間 | viral 機制 |
|---|---|---|---|
| F14 演講濃縮型 | 0.46-0.56 | 3-5 h | identity signal 分享 |
| F15 源材料公開型 | 0.64 | 1-2 h | 「我得到內幕」收藏優越感 |
| F16 精選彙整型 | 0.34 | 30-45 min | 「我幫你濾過了」感 |
| F17 極簡轉發型 | **1.09** | 5-10 min | FOMO trigger（純存檔型）|

對照 Hao F6b 純血 hype：分享/讚 0.05-0.21。**v0.6 是讚 / 留言驅動，v0.7 補上分享驅動配方**。

### Added — R11 金句密度

**Mode B 每段至少 1 個可截圖金句**（reusable / identity signal，不是「！！！」hype）。F14 範例每篇 8 個截圖入口 → 分享率 0.46-0.64。Hao v0.6 只 2 個（殺瘋了/太神啦） → 分享率 0.05-0.21（弱 4 倍）。

4 段 4 punch 升級：
- 段 1：hype 詞 + meta 鉤子（已有）
- 段 2：**反差數字 / reusable 觀察**（新增）
- 段 3：**具體 use case 句 + 反差結尾**（升級）
- 段 4：**明確 CTA + 稀缺感**（升級）

### Added — R12 量化稀缺 hook

段 1 開頭**塞具體數字堆疊**取代抽象 framing：
- ❌「我自己訓練的 skill 公開」
- ✅「14 天 14 篇 75K 觀眾 1700 行 SKILL.md 公開」

數字越具體 + 反差越大 = hook 越強（從 F15 + F17 偷學）。

### Added — R13 反命題 hook

中段或 hook 用「大家以為 X，其實 Y」frame（從 F14 偷學）。F14 兩篇都用反命題撐起整篇（specs to code 反對 / YouTube 不是排名系統）。

5 條反命題庫例：
- 「大家以為 viral = 好內容，其實 = 好內容 × 飢餓度 × 主題冷卻」（R5）
- 「大家以為 voice 一致 = brand，連 hype 詞重複都變套路」（R10）
- 「大家以為讚多 = 成功，其實分享多才是」（R6）

### Added — R14 hook punch 詞庫

**絕對化定位句式**（FOMO trigger，從 F17 偷學）：
- 「如果只能看一個 X，那就是 Y」
- 「跑兩週 14 篇，總結 5 個沒人說的事」

**權威 stacking 三層**（每段 1 個）：
- L1 稱號 / L2 量化資歷 / L3 反差成就

**反差數字 pattern**（從 F14 偷學）：「Day 1 380 讚帶 +1,319 入群 / Day 5 9 讚帶 0 入群」

### Added — F14 演講濃縮型公式

- 結構：個人痛點 + 第三方權威 + 震撼數據 + 反命題 + ▋ 4-7 段 + 每段 1 金句 + 結論 + CTA
- 適配 Hao：⭐⭐（高成本 3-5h，voice 衝突）
- 月配額：1 篇

### Added — F15 源材料公開型公式

- 結構：稀缺資源 hook + 個人短評 + 觀察金句 + 升格 framing + 完整原稿
- 適配 Hao：⭐⭐⭐⭐（你的 SKILL.md / 規則表 / 戰績 都是現成源材料）
- 月配額：1 篇

### Added — F16 精選彙整型公式

- 結構：fanboy + 大咖背書 + 反命題 hook + 連結 + bullet 重點 + 驚奇 bullet
- 適配 Hao：⭐⭐⭐⭐（30-45 min 寫作，每小時等效讚分 10,700 = ROI 王）
- 月配額：2-3 篇（補進 weekly Mode A slot）

### Added — F17 極簡轉發型公式

- 結構：絕對化定位 + 權威 stacking + 零摩擦行動 + 連結
- 適配 Hao：❌（funnel 衝突 — 你是 Line 群，韓林是 blog SEO）
- **不模仿整套，只偷 R14 hook 詞庫**

### Added — Part 3 整合月配額戰略

| archetype | 月配額 | 角色 |
|---|---|---|
| F6b 純血（招牌）| 2 篇 | mega-viral + Line 群成長主軸 |
| F14 演講濃縮 | 1 篇 | thought leader 圈 |
| F15 源材料公開 | 1 篇 | skill 開源 brand 延伸 |
| F16 精選彙整 | 2-3 篇 | weekly baseline，低成本 |
| F17 極簡轉發 | 0（hook 偷學）| 跳過 |
| Mode A 日常 | N 篇 | brand 真實感 + 鐵粉黏著 |

**月內 viral 篇數從 2 → 6-7，寫作時間只增加 3-4h**。

### Changed

- R8 voice lock 範圍縮限：**只適用 Mode B 爆款型**，Mode A 日常用🟢自然口語
- F6b 4 punch 結構強制：每段必須有可截圖金句，不能純敘述

### Lessons learned

1. **F6b 分享率天花板就 0.21**（純血 hype 是讚 / 留言驅動，不是分享驅動 archetype）
2. **F15 對 Hao 適配度最高**：你已有的 SKILL.md / 14 天戰績 = 現成稀缺源材料
3. **F17 不能整套模仿**：funnel 不同（你拉 Line 群，他做 blog SEO），但 hook 詞庫可偷
4. **Hook punch 詞是 viral 的必要條件**：F17 5-10 min 寫作就能 316 分享，因為絕對化 + 權威 stacking 三層
5. **同一個作者連 3 篇穩定 viral**（技韓林 4/20-4/28 共 3 篇，等效讚分差距 < 4%）= viral 公式是可工業化的

---

## v0.6 — 2026-05-05

5/5 第三次 mega-viral（44K 觀眾 / 95.3% 非追蹤者 / +1,239 Line 群）推翻 v0.5 多個假設。F6b 框架升級為支援 N 個變體，月配額單位從「公式總篇數」改成「敘事意圖」。

### Added — F6b 變體 D（社群 social proof 型）🆕

第三個實證 mega-viral 變體（變體 A=promo / B=演算法復盤 / **D=社群 pitch**）。跳過變體 C 因為 Day 7 商業 ROI 嘗試 fail 不算成功變體。

**變體 D 公式**：
```
[段 1] ＜AI＞這次真的殺瘋了，我用這個 skill 帶起來的＜社群＞現在＜人數＞，＜社群價值＞！！！你沒看錯！！＜成員 social proof＞！！真的太神啦！！！

[段 2] ＜時間前＞還＜舊人數＞，發＜貼文數＞貼文衝到＜新人數＞，＜流量轉化機制＞

[段 3] 現在我問「＜情境問題＞」群裡＜時間＞就有人＜動作＞，比＜對照物＞還快

[段 4] ＜社群名＞歡迎一起來，沒入群的留言我拉你
```

**5/5 實證**：19h 73,622 瀏覽次數 / 44,110 觀眾 / 265 讚 / 342 留言 / 35 分享 / 95.3% 非追蹤者 / **Line 群 +1,239**（94% 複製 Day 1 +1,319 真 KPI）。

### Added — Viral 4 條件公式（5 案例對照組實證）

```
viral = 4 段 4 句結構
      + 純血 voice
      + 全新敘事意圖（4 天內不重複 + 月內 ≤ 2 同意圖）
      + 黃金時段（02:13 / 22:00-01:00）
```

| 貼文 | 結構 | voice | 新意圖 | 時段 | 結果 |
|---|---|---|---|---|---|
| Day 1 | ✅ | ✅ | ✅ promo 1/2 | ✅ | mega 75K |
| Day 5 | ✅ | ✅ | ❌ promo 2/2 4 天內 | ✅ | flop 0.13% |
| Day 6 | ✅ | ✅ | ✅ 演算法復盤 1/2 | ✅ | mega 17K |
| Day 7 | ✅ | ❌ voice OOC | ✅ ROI 1/2 | ✅ | 鎖鐵粉 |
| 5/5 | ✅ | ✅ | ✅ 社群 pitch 1/2 | ✅ | mega 44K |

**4 個 AND 全綠 = 必爆，任一條 ❌ = 死**。

### Added — 已知 viral 敘事意圖庫

實證 mega-viral：
- promo（產品 ship）— Day 1
- 演算法復盤（self-experimental analysis）— Day 6
- **社群 social proof**（pitch 群價值）— 5/5

待測但理論可行：教學型 / 合作達成 / 預告型 / 反思型 / 抱怨吐槽 / 對比工具...

意圖種類愈多 → 月內可發的 F6b 數愈多。

### Added — Case 8（5/5 完整解剖）

case_studies.md 加入 Case 8：5/5 從草稿到 mega-viral 的完整案例 + 5 案例 final 對照表 + 規則 11（v0.5 月配額假設推翻）。

### Removed / Fixed — v0.5 R9「Mode B 月配額硬限」假設

- ~~v0.5 R9 「Mode B 公式總篇數每月 1-2」~~ ❌ 推翻
- ~~v0.5「14 天間隔才安全」~~ ❌ 部分推翻（新意圖可短於 14 天）
- ~~v0.5「連 N 🔴 演算法降權 7-14 天」~~ ❌ 推翻（降權是主題層而非 creator 層）
- ~~v0.5「F6b 一次性鉤子」~~ ❌ 推翻（變體可無限期持續）

正確規則：**月配額單位是「敘事意圖」**，不是 F6b 公式總數。同月份只要意圖不同，N 篇 F6b 都可以爆。

### Changed — R1 / R5 / R8 / R9

- **R1 連發硬規則修正**：移除「演算法降權 creator 層」假設，改為「降權只針對重複敘事意圖」。連 N 🔴 換意圖 OK。
- **R5 升級**：「主題冷卻」精準定義為「敘事意圖冷卻」（4 天 + 月配額 ≤ 2）
- **R8 範圍維持**：voice lock 僅 Mode B
- **R9 廢除**：功能合併到 R5

### Lessons learned

1. **演算法疲勞看的是敘事意圖，不是公式 / hook 詞 / 創作者本身**
2. **F6b 框架支援 N 個變體**：意圖庫愈大，可發 viral 愈多
3. **5/5 推翻所有「保守冷卻期」假設**：不需要等 14 天 / 月配額爆 / 演算法復健
4. **真 KPI 持續驗證 R7**：5/5 帶 +1,239 Line 群 ≈ Day 1 的 94%，每篇 mega-viral 都帶 1,000+ 真實社群成員
5. **受眾 baseline 已認得 Hao**：5/5 受眾年齡分布跟 Day 1 幾乎一致（35-44 42.5% / 45-54 27.1% / 25-34 21.9%），演算法已校準

### Validation summary（v0.5 → v0.6）

| 指標 | Day 1 plateau | Day 6 plateau | **5/5 19h** |
|---|---|---|---|
| 瀏覽者 | 75,071 | 18,603 | **44,110** |
| 讚 | 380 | 100 | 265 |
| 留言 | 457 | 89 | 342 |
| 分享 | 81 | 25 | 35 |
| 非追蹤者 % | 96.5% | 92.6% | **95.3%** |
| Line 群增量 | +1,319 | +217 cumulative | **+1,239** |
| 變體 | A promo | B 演算法復盤 | **D 社群 pitch** |

3 個變體 / 3 個 mega-viral 都跨 90% 非追蹤者天花板。

---

## v0.5 — 2026-04-28

第 7 天 5 篇實戰累積後的大型迭代。新增 R8 voice lock + 4 段 4 句 F6b 鐵則 + 兩變體公式化 + plateau 早期判定 + 第二波 second push 機制 + Day 5/6 案例。

### Added — R8 Voice Lock（爆款型純血格式鎖）

所有 ship / viral / 認真貼文（Mode B）= **Day 1 純血格式鎖死**：
- 4 段 4 句鐵則（每段 = 1 個 sentence，段間空行分隔）
- ！！！只在第 1 段密集
- 段 2/3 結尾無標點無 emoji
- 段 4 結尾留白
- 絕不用 numbered / bullet list

附 8 點檢查表（生成 Mode B 時必跑），任一條 ❌ → 重生成不出草稿。

**「4 段 4 句」定義澄清**：「段」= paragraph，「句」= 1 個結構性 sentence。**不是螢幕視覺 4 行字**（手機 wrap 後一句佔 2-4 視覺行是正常的）。

### Added — F6b 兩變體公式化

- **變體 A：promo 型（self-evident 鉤子）** — Day 1 mega-viral 範本（74,510 觀眾、380 讚、80 分享、+1,319 Line 社群）
- **變體 B：復盤型（self-experimental 鉤子）** — Day 6 突破鐵粉圈範本（7h 1,578 觀眾、57.1% 非追蹤者破鐵粉天花板、per-viewer 互動是 Day 1 的 3-4 倍）

兩變體可交替使用，**3-7 天間隔可行**（Day 1 → Day 6 = 7 天實證）。

### Added — R5 主題冷卻定義升級（基於 Day 5 + Day 6 雙實證）

**主題判定從「公式 / hook 詞」改成「敘事意圖」**：

| 場景 | 舊規則判 | 新規則判 | 實戰結果 |
|---|---|---|---|
| Day 1 promo → Day 5 promo（4 天）| 違規 | **違規（敘事意圖重複）** | ❌ 觸及只剩 Day 1 的 0.13% |
| Day 1 promo → Day 6 復盤（7 天）| 違規（公式重複）| **不違規（敘事意圖不同）** | ✅ 突破 57% 非追蹤者 |

**敘事意圖分類**：promo / 復盤 / 教學 / 抱怨 / 預告。同意圖 4 天內重複 = 罰；不同意圖即使同公式 = 不罰。

### Added — R6 Plateau 早期判定規則

**1-19h 不下定論**。多次實證早期判讀會誤判（Day 2 / Day 4 / Day 5 早期判 fail，48h 後皆翻盤）。

判定時機：
- 1-6h：只能說初步觸及和趨勢
- 6-24h：說 trajectory + 早期信號表對照
- **48-72h plateau：才能用 4 指標下定論**

### Added — 早期 mega-viral 信號表（7h 達 4/5 條 = high-confidence）

| 信號 | 門檻 |
|---|---|
| 瀏覽者 | > 1,000 |
| 留言 | > 20 |
| 分享 | > 5 |
| 互動率 | > 15% |
| 非追蹤者 | > 50% |

實證：Day 6 7h 5/5 全達。

### Added — 演算法 second push 機制（Day 4 實證）

演算法 24-48h 內會根據早期 engagement 觸發第二波廣推。Day 4 1h 6% 非追蹤者 → 58h 變 29%。

**戰略**：發文後 24-48h 內主動回留言、引發討論串 = trigger second push。

### Added — R7 真 KPI 多平台貢獻提醒

社群成長要算多平台 contribution。Day 1 +1,319 Line 含 FB 主導 + Threads 補強，歸因不要把全部漲幅歸給單一貼文。

### Added — Case 5 / Case 6 完整案例

- **Case 5（Day 5 F11+F6b override 實證）**：使用者 override R5 堅持 Day 1 後 4 天用 F6b → 觸及只剩 Day 1 的 0.13%。但 19h vs 58h 對比顯示 plateau 才看得到 4.6% 連結點擊率（5 篇之王）。
- **Case 6（Day 6 F6b 復盤型突破鐵粉圈）**：純血格式 + 4 段 4 句 + 新敘事意圖 → 7h 全達 mega-viral 早期信號 + 受眾年齡 shift（45-54 歲 +6.6%、25-34 歲 -9.1%）。

### Added — 5 篇完整 plateau 對照表

case_studies.md 加入 5 篇 evergreen vs second push vs flop 的橫向比較表，包含每篇連結點擊率、非追蹤者比例、互動率、排名。

### Changed

- F6b 公式從「一次性爆破」升級為「兩變體可持續輪替」
- Hype 開頭衰減 40% 假設**部分修正**：衰減主因是「敘事意圖重複」而非「hype 詞語本身」（Day 6 用 hype 仍 broke through 57% 非追蹤者）
- R3 突破鐵粉圈公式清單加入 F6b 復盤型變體

### Lessons learned

1. **語氣 consistency 可凌駕演算法優化**：使用者選擇 voice lock 後，犧牲廣推效率換 brand 識別度
2. **敘事意圖 > 公式骨架**：演算法疲勞看的是內容意圖，不是公式 / hook
3. **plateau 才是真相**：1-19h 數據會嚴重誤判，多次實證
4. **per-viewer 互動率是質量指標**：Day 6 觀眾規模只有 Day 1 的 2%，但每觀眾互動是 4 倍
5. **受眾隨主題 shift**：「對照組打臉」吸到中年職場人（45-54 歲 +6.6%），跟 promo 型受眾不同

### Validation summary（v0.1 → v0.5）

| 指標 | Day 1 | Day 6 7h |
|---|---|---|
| 瀏覽者 | 74,510 | 1,578 |
| 讚 | 380 | 32 |
| 留言 | 457 | 26 |
| 分享 | 80 | 6 |
| 非追蹤者 | 96.5% | 57.1% |
| Line 社群增量 | +1,319 | 待 plateau |

---

## v0.4 — 2026-04-25

Token 消耗優化 + 知識結構重整。SKILL.md 從 247 行降到 116 行（-53%），每次觸發省 ~1300 tokens。

### Refactored

- **SKILL.md 精簡為 router + 硬規則**（116 行）
  - 7 條編號核心規則（R1 一天一篇、R2 爆款冷卻、R3 突破鐵粉圈、R4 時段分流、R5 爆款節奏、R6 4 指標評估、R7 真 KPI 是社群轉化）
  - 所有實戰詳情下放 references，每次觸發只載必要
- **抽出 `references/evaluation.md`**（108 行）
  - FB 2026 演算法訊號權重
  - 4 指標評估框架（連結點擊率、追蹤者比例、互動率、下游轉化）
  - 真 flop 紅線（4 條件全踩才算）
  - 2 種貼文類型框架（擴散型 vs 深化型）
  - 排名指標（最近 10 篇相對表現）
- **抽出 `references/case_studies.md`**（149 行）
  - Day 1-4 完整實戰案例解剖
  - Day 1 mega-viral 數據 + 啟示
  - Day 2 「被誤判 flop」的深化文重判讀
  - Day 3 真 underperform 歸因
  - Day 4 鐵粉圈觸及限定分析

### Added

- **private skill confirm bypass 條款**（SKILL.md 安全閘段）：
  - 開源版永遠保留「發佈前必須『確認』字眼」硬規則
  - 私人版可接受「你自己操作不用問我」當 session 授權
  - 兩版明確分離，防開源版繼承私人設定
- **診斷流程**（`generate_and_publish.md`）：使用者貼數據 / 截圖時如何用 evaluation.md 框架判讀
- **發文前三檢查**（`generate_and_publish.md`）：冷卻 / 鐵粉圈 / 輕重節奏，取代原單一冷卻檢查
- **不要做 list 補充**：不刪除使用者留言（系統硬規則）
- **快速查詢表**（SKILL.md 底部）：知識點 → 檔案對應

### Changed

- 所有規則統一編號 R1-R7 方便引用
- 「爆款後 Day 2 禁忌」移到 `case_studies.md` 當歷史案例保存，不再獨立規則
- `generate_and_publish.md` 新增「Step 0：三檢查」取代單一冷卻檢查

### Token 消耗優化數據

| 場景 | v0.3 | v0.4 | 節省 |
|---|---|---|---|
| Skill 觸發（SKILL.md 載入）| ~2500 tok | ~1200 tok | **-52%** |
| Phase 2 典型發文 | ~4500 tok | ~3700 tok | **-18%** |
| Phase 診斷使用者數據 | 需重讀 SKILL | 讀 evaluation.md（108 行）| 更精準 |

### Lessons learned（新增）

- 連 2 篇同公式 = 鉤子燒完（F6b Day 1 vs Day 2）
- Meta AI 會把爆款貼文當「Manus AI 範本」在作者自己 profile 展示給自己看（僅作者可見，不影響效果）
- 絕對讚數判斷 flop 會誤判，4 指標框架才準
- 外部連結點擊率在 mega-viral 中極低（Day 1 只 7/74,510），社群成長主路徑是留言 → 作者私訊拉人

---

## v0.3 — 2026-04-24

3 天內第三次重大更新。基於 Day 1-4 完整數據 + 深度研究「突破鐵粉圈」的演算法訊號 + 6 個新公式。

### Added — 6 個廣推公式（F8-F13，Part 2）

專攻「突破鐵粉圈觸及非追蹤者」。Day 1 的 mega-viral（72K 觸及、96.7% 非追蹤者）是例外，多數創作者連續 3 篇卡 > 85% 追蹤者時必用這些公式強制擴散：

- **F8｜Credibility Piggyback**（外部實體標記挑戰）— 標記 @Anthropic / @OiiOii 等 → cross-audience seeding
- **F9｜Public L-taking**（「我錯了」反轉文）— 情緒觸發 + 超高 dwell time，分享率比誇耀文高 3 倍
- **F10｜Controversy Middle Ground**（兩派戰爭居中開炮）— 留言暴衝觸發演算法「爆點討論」廣推
- **F11｜Counter-Funnel Giveaway**（反漏斗教學）— 反 CTA「不用追蹤不用讚」吃 perceived authenticity score
- **F12｜Timestamp Live-ops**（時間戳+過程直播）— revisit 率破 30%，觸發 FB「高價值內容」判定
- **F13｜Named Gratitude Chain**（具名致謝鍊結）— tag 5 人漏斗擴散，比 F4 里程碑擴散 5 倍

### Added — FB 2026 演算法訊號權重（最關鍵的新知）

Meta 2024-11 推「Unconnected Reach」指標。讚幾乎無權重，**分享 ≈ 20× 讚、留言 ≈ 5× 讚、dwell time 隱形王牌**。評估貼文好壞看：分享 > 留言 > dwell > 讚。

### Added — 突破鐵粉圈監控

非追蹤者比例 < 15% 連續 3 篇 → 演算法把你歸類「鐵粉限定」，必用 F8-F13 破局。

### Added — 2026 高停留開頭（5 句）

換掉失效的「各位！！！」「這次真的殺瘋了」（對非追蹤者衰減 40%）。新的五句：數字+動詞矛盾 / 時間戳+事件 / 反問具體化 / 公開認錯 / 金額+時間成本。

### Changed

- F6b 驗證數據升級為 **72h plateau 最終版**：瀏覽 125,315 / 74,510 獨立觀眾 / 374 讚 / 452 留言 / **80 分享** / +167 粉 / **+1,150 Line 社群（~800→1,952）** / 最近 10 篇排名 1/10 / 72h 後仍在漲 = evergreen 長尾
- F6b 警告：「殺瘋了」類 hype 對**非追蹤者** 40% 衰減，只適合一次性爆破 + 鐵粉收割
- F4 里程碑新增限制：實證 93.9% 鐵粉觸及，想擴散用 F13 取代
- 公式編號從 7 個擴充到 13 個

### Fixed

- 發文時段指南：9-11AM 傳統 FB 黃金時段**對 AI/tech 創作者受眾無效**（Day 3 實測 348 瀏覽排名 7/10）。實證最佳是 **22:00-01:00 夜貓時段**。

### Lessons learned（新增）

1. 演算法一次性的 mega-viral 可以突破觸及天花板，但**無法連續複製同公式**（鉤子燒完）
2. 鐵粉深化文（Day 2 模式）跟廣推文（Day 1 模式）是**兩種不同的成功類型**，不能用同一標準比較
3. 分享才是演算法廣推的真正 trigger，不是讚
4. 外部連結點擊率極低（Day 1 的 72K 人只 7 人點 GitHub）→ CTA 要放 FB 站內
5. 標記外部實體（F8）是最可持續的廣推 trigger，比 F6b meta 耐久

---

## v0.2 — 2026-04-22

12 小時後第一次重大更新。基於 Day 2 實戰 flop + FB 洞察報告數據做的規則迭代。

### Added
- **一天一篇鐵則**（`SKILL.md`）— 24 小時內最多 1 篇，不受前一篇好壞影響。Flop 當天正確動作是回留言，不是多發。
- **爆款節奏基本原則**（`SKILL.md`）— 日常 20-40 讚 × N 天 → 偶爾一顆爆款 → 回到日常。每月 1-2 個 F6b 就夠。
- **爆款後 Day 2 三大禁忌**（`SKILL.md`）— Day 2 flop 實證的三個錯誤：連續同公式、炫 Day 1 數字、爆款時間 +24h 不是黃金時段。
- **基於實戰校準的 benchmark 表**（`SKILL.md`）— 4K 粉帳號的及格 / 優秀 / 爆款 / mega-viral 四級指標。
- **FB 原生排程機制**（`references/facebook.md`）— 用 FB 內建排程取代 cron。
- **留言框 `\n` = 送出的踩雷**（`references/facebook.md`）— 留言框 Enter 是送出不是換行，會被拆成多則。

### Changed
- F6b 驗證數據從「300+/400+/40+」升級到**實戰完整數據**：瀏覽者 72,323、互動率 15.3%、讚 358、留言 443、分享 73、追蹤者 +167、Line 社群 +700。
- `references/formulas.md` F6b 段新增反直覺觀察：連結點擊率極低（72K 讀者中只 7 人點外部連結）→ 社群成長主路徑是**留言 +1 → 作者私訊拉人**。

### Lessons learned（可複製給其他 4K 粉帳號的心得）

1. **爆款觀眾 97% 是非追蹤者** — F6b 觸發演算法廣推，不靠既有粉絲。
2. **外部連結點擊極低** — 讀者不走出 FB。CTA 要放 FB 站內行動（留言、私訊、精選留言連結），不是依賴外部 funnel。
3. **真正的 KPI 是社群轉化** — 讚/留言只是中間指標。社群人數增長才是終極指標。
4. **一篇 mega-viral > 七篇日常** — 不要為了 posting frequency 而硬發。

---

## v0.1 — 2026-04-21

初版發布。

### Added
- Skill 三階段工作流（學風格 / 內容規劃 / 生成+發佈）
- 7 個 viral 公式（F1-F7，含 F6b meta-ship 爆款模板）
- 14 天內容日曆範本
- Claude in Chrome 操作指南（FB / IG / Threads / X）
- 安全閘：發佈前必須使用者明確「確認」字眼
- 範例檔：`style_profile.example.md` + `content_plan.example.md`（虛構角色林思萱 Vivi）

### Validation
- F6b meta-ship 公式首次發佈即獲 300+ 讚 / 400+ 留言 / 40+ 分享（驗證當晚）
