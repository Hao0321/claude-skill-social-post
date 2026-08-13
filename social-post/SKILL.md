---
name: social-post
description: 學習使用者的 Facebook／Instagram／YouTube／Threads／X 語氣與受眾，規劃內容、撰寫平台化貼文、經確認後發佈；並作為所有流量、演算法、留存與轉化學習的唯一結構化帳本，做跨平台／跨篇／跨集比較、實驗設計及規則升降級。使用者說「發文」「幫我寫」「用我的口氣」「排貼文」「查流量」「演算法」「分析 Reels／Shorts」「把數據訓練進去」「記錄成效」「比較這幾篇」「優化 pattern」「review」時使用。
---

# Social Post

把內容生成、實際發布與成效學習分開。依意圖只讀必要資料，不把整個案例庫一次塞進 context。

## Session 啟動

P2 預設讀 `voice_quick.md`；只有 P1 重新學語氣、使用者明確要求深度仿寫，或 quick card 無法裁決時，才完整讀 `style_profile.md`／`hao-voice`。安全與使用者明示 > voice quick／明確載入的 hao-voice > 公式。

## 路由

| 觸發 | Mode | 必讀 |
|---|---|---|
| 重新規劃、排內容 | P0 Plan | `references/phase0_plan.md`＋`current_brief.md`＋目標 formula |
| 重新學語氣 | P1 Learn Voice | `references/learn_style.md`＋`style_profile.md` |
| 寫一篇、PO、發文 | P2 Draft／Publish | `references/generate_and_publish.md`＋`voice_quick.md`＋`current_brief.md`＋單一 formula；確認後才讀平台 ref |
| 把數據訓練進來、記錄成效 | P3 Log Outcome | `references/outcome-workflow.md`＋`data/*.jsonl` |
| 比較貼文／集數、找 pattern | P4 Optimize Patterns | `references/outcome-workflow.md`＋`references/evaluation.md`＋相關 rules |
| 查歷史 Case | Legacy Case | `references/case_studies.md` 索引，再讀單一 `references/cases/case-NN.md` |

路由前用一句話告知正在做哪個 Mode。單純診斷不需要 Chrome。

## Source of truth

| 資料 | Canonical source |
|---|---|
| 貼文／caption／發布條件 | `data/posts.jsonl` |
| 洞察快照 | `data/insight_snapshots.jsonl` |
| 帳號期間總覽 | `data/account_snapshots.jsonl` |
| 跨篇假設與 confound | `data/experiments.jsonl` |
| 規則正文 | `references/rules/RNN.md`；`references/rules.md` 是索引 |
| 規則生命週期／實驗 backlink | `references/rules/metadata.json` |
| 規則機器索引 | `data/rule_registry.json`（生成檔） |
| 舊案例全文 | `references/cases/` |

新成效不得只寫進 Markdown。先寫 JSONL，再視需要更新人類摘要。

## 流量與演算法單一歸檔中樞

- 不論素材由 `video-autopilot`、YouTube 專門 Skill、Meta 面板或其他流程產生，所有發布後的流量、推薦來源、搜尋、留存、互動、受眾、追蹤／訂閱與轉化證據，都必須寫回本 Skill 的 `data/*.jsonl`。
- 專門 Skill 可以做平台診斷或產生剪輯／包裝建議；但觀測事實、跨平台比較、實驗證據與規則升降級，以本 Skill 為 canonical source，禁止另建互相漂移的成效記憶。
- 同一內容的 FB／IG／YouTube 指標各自建立有平台 scope 的 snapshot；Meta 合併卡片只能作 cross-platform reference，沒有完整平台洞察時不得冒充該平台 snapshot。
- 演算法時效性知識仍可放目標平台 reference；私人實測是否成立，只能依本 Skill 的同 maturity、多樣本資料升級。

## P3 Log Outcome

1. 每組洞察圖建立新 snapshot；不覆蓋舊數字。
   帳號 7／30／90 天總覽寫 `account_snapshots.jsonl`，不得綁到單篇貼文。
2. 記 published_at、captured_at、hours_since_publish 與 maturity。
3. IG／FB total 與可取得的拆分同時保存；missing 用 `null`。
4. UI rate 與 derived rate 分開；留存曲線目測只寫 note。
5. 先 dry-run `scripts/log_outcome.py`，明確寫入時才加 `--write`。
6. 寫完執行 `scripts/social_data.py validate`。

## P4 Optimize Patterns

先跑 series summary，再比較相近 maturity。依序看 watch quality、distribution、conversion、content、packaging。故事、首幀、集數與 caption 同時改變時，列為 confound，不稱乾淨 A/B。

證據狀態只用：`hypothesis → emerging → validated → deprecated`。同一系列三集是 n=3 posts，但不是三個獨立樣本。實驗可用同一 `experiment_id` 追加 revision；不可覆寫歷史。候選規則必須同時在 experiment `rule_ids` 與 rule metadata `experiment_ids` 建 backlink。

## 實際發佈安全閘

只有 P2 的實際發布需要 `chrome:control-chrome` 與已登入狀態；草稿、規劃、分析、資料回填不需要。

- 發佈前必須在當前對話取得明確「確認」。
- 使用者若在當前 session 明示「你自己操作不用問」，私人版可免逐次確認；不跨 session。
- 不幫登入、不改帳號／隱私、不刪文、不自動按讚／follow／大量留言。
- 預設跨平台重新包裝；但使用者明示「同步發布／一稿多發」時，正文共用一份，只有平台必填欄位沿用正文內容（例如 YouTube 標題取第一句），不再額外維護多套文案。
- FB／Threads 正文不放外部連結；依 R25 使用留言或平台允許的位置。
- 沒有 IG 圖／影片就停，讓使用者選擇提供素材、跳過 IG 或改 Threads。

## 平台規則

平台規格會變。Hashtag、字數、發佈 UI、演算法等時效規則只在目標平台 reference 維護，標示 last verified；跨 skill 衝突時先查權威來源，不同時保留兩個硬數字。

## 維護

- 每次 outcome 更新後跑 data validate、rule registry build、cleanup drift audit。
- 修改任一 `rules/RNN.md` 後跑 `split_rule_archive.py --refresh-manifest`，再 build rule registry。
- `case_studies.md` 只保留索引；新增 Case 寫獨立檔或直接以 structured outcome 取代。
- 公開 export 使用 allowlist：`voice_quick.md`／`current_brief.md` 已是去快照的操作卡，可公開；不得公開完整 `style_profile.md`、`content_plan.md`、`drafts/`、outcome JSONL、`references/cases/`、`.rd/`。
- 私公版路徑只從 `audit.config.json` 讀；未設定就回報 NOT_CHECKED，不猜 sibling repo。

```powershell
$env:PYTHONUTF8='1'
python scripts/social_data.py validate
python scripts/social_data.py summary --series reborn-married-driver
python scripts/build_rule_registry.py --write
python ../code-cleanup-helper/scripts/audit.py . --mode all
```
