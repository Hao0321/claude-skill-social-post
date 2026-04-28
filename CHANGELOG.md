# Changelog

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
