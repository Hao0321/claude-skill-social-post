---
name: social-post
description: 學習使用者的 Facebook／Instagram／Threads／X 語氣與受眾，規劃內容、撰寫平台化貼文、經確認後發佈，並把貼文與 Reels 洞察以時間快照寫入結構化資料，做跨貼文／跨集比較、caption 與留存歸因、實驗設計及規則升降級。使用者說「發文」「幫我寫」「用我的口氣」「排貼文」「查流量」「分析 Reels」「把數據訓練進去」「記錄成效」「比較這幾篇」「優化 pattern」「review」時使用。
---

# Social Post

把內容生成、實際發布與成效學習分開。依任務只讀必要資料，不把整個案例庫一次塞進 context。

## 路由

| 觸發 | Mode | 必讀 |
|---|---|---|
| 重新規劃、排內容日曆 | P0 Plan | `references/phase0_plan.md`、`content_plan.md`、目標 formulas |
| 重新學語氣 | P1 Learn Voice | `references/learn_style.md`、`style_profile.md` |
| 寫一篇、PO、發文 | P2 Draft／Publish | `references/generate_and_publish.md`、style／plan、目標平台 ref |
| 把數據訓練進來、記錄成效 | P3 Log Outcome | `references/outcome-workflow.md`、`data/*.jsonl` |
| 比較貼文／集數、找 pattern | P4 Optimize Patterns | outcome workflow、`references/evaluation.md`、相關 rules |
| 查歷史 Case | Legacy Case | `references/case_studies.md` 的相關段落 |

開始前用一句話告知正在使用哪個 Mode。單純規劃、撰稿、診斷與資料回填不需要瀏覽器。

## 使用者資料

- `style_profile.md` 與 `content_plan.md` 由 example 檔建立，屬本機資料，不應提交到公開 fork。
- `data/` 由 outcome scripts 首次寫入時建立，預設不附任何作者資料。
- 使用者若另有 voice skill，可把它當上游參考；安全與本次明示要求優先。

## Outcome source of truth

| 資料 | Canonical source |
|---|---|
| 貼文、caption、發布條件 | `data/posts.jsonl` |
| 洞察時間快照 | `data/insight_snapshots.jsonl` |
| 跨篇假設與 confound | `data/experiments.jsonl` |
| 規則機器索引 | `data/rule_registry.json`（生成檔） |
| 規則正文 | `references/rules.md`；fork 也可拆成 `references/rules/RNN.md` |
| 歷史案例 | `references/case_studies.md` |

新成效不得只寫進 Markdown。先寫 JSONL，再視需要更新人類摘要。

## P3 Log Outcome

1. 確認貼文 identity、平台、發布時間、時區與截圖時間。
2. 每組洞察圖建立新 snapshot；不覆蓋舊數字。
3. IG／FB total 與可取得的拆分同時保存；missing 用 `null`，不可補成 0。
4. UI rate 與 derived rate 分開；留存曲線目測只寫 note。
5. 新貼文 bundle 含 `post`＋`snapshot`；既有貼文追加快照時可只傳 `snapshot`。
6. 先 dry-run，明確寫入時才加 `--write`；寫完執行 validate。

## P4 Optimize Patterns

先產出 series summary，再比較相近 maturity。依序看 watch quality、distribution、conversion、content、packaging。故事、首幀、集數與 caption 同時改變時，列為 confound，不稱乾淨 A/B。

證據狀態只用 `hypothesis → emerging → validated → deprecated`。同一系列三集是 n=3 posts，但不是三個獨立樣本。

## 實際發布安全閘

只有 P2 的實際發布需要瀏覽器控制與已登入狀態。

- 發布前必須在當前對話取得明確確認，並再次核對平台、帳號與正文。
- 不代為登入、不改帳號或隱私、不刪文、不自動按讚／follow／大量留言。
- 跨平台不是原文複製；依目標平台重新包裝。
- 沒有 IG 圖片或影片就停，讓使用者提供素材、跳過 IG 或改 Threads。

## 平台規則

平台規格會變。Hashtag、字數、發布 UI、演算法等時效規則只在目標平台 reference 維護並標示 last verified；若結論依賴當前平台規則，先查官方來源。

## 指令

```powershell
$env:PYTHONUTF8='1'
python scripts/social_data.py validate
python scripts/social_data.py summary --series your-series-id
python scripts/log_outcome.py references/outcome-bundle.example.json
python scripts/log_outcome.py references/outcome-bundle.example.json --write
python scripts/build_rule_registry.py --write
python scripts/self_test.py
```
