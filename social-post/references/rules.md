# 核心規則庫（R1-R43 索引）

本檔保留證據公約與導航；完整定義、實證與操作細節在 `rules/RNN.md`。P2 發文或診斷時只讀相關規則檔。

---

## 📐 證據強度公約（升級門檻，不佔 R 編號）

全 repo 通用的升級標準。任何規則、公式、案例結論要標成 proven，都要過這一關。

| 標記 | 門檻 | 寫法限制 |
|---|---|---|
| **proven** | **n ≥ 2 個彼此獨立、confound 可分離**的案例 | 可寫成鐵則、可加粗 |
| 🧪 **emerging** | n = 1，或 n ≥ 2 但 confound 糾纏無法分離 | **不准寫成鐵則、不准加粗**，要標出未分離的變數 |
| housekeeping | 純一致性修正（數字對齊、錯字、交叉引用） | 不涉及強度宣稱 |

**獨立的定義**：不同帳號、不同題材、不同話題波、不同時段 —— 共用其中任何一項就要說明，共用多項就不算獨立。

**兩條鐵律**：
1. **沒有出處的數字一律刪**，不要因為「看起來合理」就留著。內插出來的數字（在兩個已知點之間補中間值）**不算實證**。
2. **沒有新增也是合格的結論。** 審計的價值在於找出該刪的，不是產出更多規則。

---

## R1-R43 navigation

每條永久規則已拆成獨立檔案。只讀任務相關的 R，避免一次載入整本規則庫。

| R | 標題 | 狀態 | 檔案 |
|---:|---|---|---|
| R1 | 一天一篇 + 強制輕重交替（v0.7.2 細化） | active | [R1](rules/R01.md) |
| R2 | 爆款後 24h 冷卻 | active | [R2](rules/R02.md) |
| R3 | 突破鐵粉圈（連 3 篇 < 15% 非追蹤者） | active | [R3](rules/R03.md) |
| R4 | 時段按受眾分流 | active | [R4](rules/R04.md) |
| R5 | 敘事意圖冷卻（核心規則，5 案例升級） | active | [R5](rules/R05.md) |
| R6 | 評估看 4 指標 + 必須 48-72h plateau 才判定 | active | [R6](rules/R06.md) |
| R7 | 真 KPI 是社群轉化，不是讚 | active | [R7](rules/R07.md) |
| R8 | Voice Lock — 僅 Mode B 爆款型用 Day 1 純血格式 | active | [R8](rules/R08.md) |
| R9 | ~~Mode B 月配額硬限~~ → 廢除（併入 R5） | deprecated | [R9](rules/R09.md) |
| R10 | Hype 詞輪替 | active | [R10](rules/R10.md) |
| R11 | 金句密度（從 F14 偷學） | active | [R11](rules/R11.md) |
| R12 | 量化稀缺 hook | active | [R12](rules/R12.md) |
| R13 | 反命題 hook | active | [R13](rules/R13.md) |
| R14 | Hook punch 詞庫 | active | [R14](rules/R14.md) |
| R15 | 私訊分享 trigger（2026 最強信號） | active | [R15](rules/R15.md) |
| R16 | 5 字以上長留言 trigger（3× 權重） | active | [R16](rules/R16.md) |
| R17 | Reels 策略（2026 +50% 同日加成） | active | [R17](rules/R17.md) |
| R18 | 儲存（Save）指標重視 | active | [R18](rules/R18.md) |
| R19 | Threads 轉發權重 + Keyword 機制 | active | [R19](rules/R19.md) |
| R20 | 漸進改進原則（F4 → F19 5 階段，v0.8.3） | active | [R20](rules/R20.md) |
| R21 | ~~公式跨年衰退 -80%~~ → 撤回（v0.8.5） | deprecated | [R21](rules/R21.md) |
| R22 | ~~keyword 過 peak~~ → 部分撤回 | deprecated | [R22](rules/R22.md) |
| R23 | per-view 追蹤轉化率（保留，新評估指標） | active | [R23](rules/R23.md) |
| R24 | 純血公式可連發，但主題須各換（v0.8.5 → 🧪 2026-07 大幅降級） | emerging | [R24](rules/R24.md) |
| R25 | 🚨 FB / Threads 貼文絕不附外部連結（硬規則） | active | [R25](rules/R25.md) |
| R26 | ── 分隔符鐵則（Mode C 長文） | active | [R26](rules/R26.md) |
| R27 | 個人脆弱 confess（Mode C 廣 identity） | active | [R27](rules/R27.md) |
| R28 | 行業反主流 framing（Mode C 最強） | active | [R28](rules/R28.md) |
| R29 | Mode C 同日連發策略 | active | [R29](rules/R29.md) |
| R30 | FB 社團 cross-post 策略（v0.9.1，5/22 + 5/29 實證） | active | [R30](rules/R30.md) |
| R31 | Brand 邊界澄清時機（v0.9.2，5/27 F24 實證） | active | [R31](rules/R31.md) |
| R32 | 集體 framing trigger（v0.9.3，5/26-5/29 三實證） | active | [R32](rules/R32.md) |
| R33 | FB 週任務情報 = 演算法獎勵訊號（🧪 候選，6/1 實證） | emerging | [R33](rules/R33.md) |
| R34 | 真實 voice — 反 AI 腔（🚨 硬規則，6/1 使用者鎖定，永久不可覆寫） | active | [R34](rules/R34.md) |
| R35 | 關鍵詞留言索取 CTA = broke 鐵粉圈引擎（🏆 6/7 實證，最強 CTA） | active | [R35](rules/R35.md) |
| R36 | demo > claim 鐵律（broke 鐵粉圈最強單一槓桿，🏆 4 案例同變數實證，跨 FB/Thread） | active | [R36](rules/R36.md) |
| R37 | value-prop-lead 開場 —「它幫你做什麼」碾壓 meta 故事 / 好奇 hook（🏆 6/25 實證，史上最高儲存） | active | [R37](rules/R37.md) |
| R38 | 第三方具體戰績 social proof 🧪 emerging（n=1，且與 R36 共用 Case 33-A 對照組） —「別人用我的東西做出的誇張成績」> 自誇（🏆 6/26 實證） | emerging | [R38](rules/R38.md) |
| R39 | 分享（Share）= 跨粉絲圈最強引擎（20x 讚 / FB 2026 Unconnected Reach 核心 / 內容強時走分享路徑） | active | [R39](rules/R39.md) |
| R40 | Dwell time（停留秒數）= 第三廣推信號 / 隱形王牌（提取自 formulas.md 訊號表） | active | [R40](rules/R40.md) |
| R41 | superlative hook 🧪 emerging（n=1，confound 未分離） —「最大 / 第一 / 史上最 / 破紀錄」= milestone / 成果 broke 放大器（6/14 實證） | emerging | [R41](rules/R41.md) |
| R42 | archetype 飽和天花板 —「強化 hook ≠ 換 archetype」（5/12 V3 fail 實證） | emerging | [R42](rules/R42.md) |
| R43 | 連載短劇每集必須能被陌生觀眾單獨看懂 | emerging | [R43](rules/R43.md) |
