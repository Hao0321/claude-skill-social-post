# Outcome learning workflow

## 目錄

- 資料來源層級
- Log Outcome
- Optimize Patterns
- Schema 原則
- 因果與證據邊界
- 指令

## 資料來源層級

1. `data/posts.jsonl`：貼文本體、發布條件、caption variant。
2. `data/insight_snapshots.jsonl`：同一貼文可有多個時間快照，永遠保留 `captured_at` 與 maturity。
3. `data/experiments.jsonl`：跨貼文假設、變因、confound、證據狀態與下一輪測試。
4. `data/rule_registry.json`：由 `references/rules/RNN.md` 生成的導航，不是規則正文。
5. `references/case_studies.md`：舊案例索引；個別全文在 `references/cases/`，只作歷史證據。

不得再把新數據只寫進 prose。結構化資料是成效事實的 canonical source；Markdown 只留解讀與人類可讀摘要。

任何其他 Skill 收到 FB／IG／YouTube／Threads／X 的流量、演算法、留存、受眾或轉化證據時，都要路由到本資料層。專門 Skill 可保留診斷方法，但不得另存一套會漂移的 outcome memory。跨平台同內容要共用永久 `post_id`，平台各自建 snapshot；只有 Meta 合併卡片時只記 reference，不虛構缺少的平台完整洞察。

## Log Outcome

1. 確認貼文 identity、平台、發布時間與時區。
2. 每組截圖視為一個 snapshot，不覆蓋前一次。記錄截圖時間；不知道就標 `captured_at_confidence: low`，不要猜成最終值。
3. IG／FB 合併面板保留 total，也記可取得的平台拆分。未拆出的 follower／follow 指標加 scope note。
4. UI 顯示率保留在 `rates_reported`；手算 derived metric 不覆蓋 UI 值。
5. Retention 圖沒有精確座標時只寫 curve note，不偽造百分比。
6. 先 dry-run bundle，再以 `--write` 寫入；最後跑 validate。

## Optimize Patterns

分析前先用 latest snapshot 產出 series summary。比較順序：

1. 觀測時間是否相近、是否 plateau。
2. Watch quality：平均觀看占片長、略過率、首段／片尾曲線。
3. Distribution：Reels＋探索、個人檔案、非粉絲。
4. Conversion：follow／play、follow／reach、profile／reach。
5. Content 與 packaging：cold open、standalone premise、字幕／語言、caption、CTA、時段。

兩集同時改了故事、首幀與 caption，不得稱為 A/B。先列共變量與 confound，再說哪個解釋目前最有力。

## Schema 原則

- ID 永久不改：`post_id`、`snapshot_id`、`experiment_id`。
- 時間使用 ISO 8601＋offset，例如 `2026-08-11T14:56:00+08:00`。
- 百分比一律存 0–100，不存 0–1。
- Missing value 用 `null`，不填 0。
- Evidence status 只用 `hypothesis／emerging／validated／deprecated`。
- 同系列多集不等於獨立樣本；在 `independent_samples` 明示。

## 因果與證據邊界

- Caption 可是分類／搜尋／轉化訊號，但不能替代影片留存。
- 早期 snapshot 只能報趨勢，不做終局勝負。
- `n=3` 同系列可降低單點偶然，不能直接升成跨題材定律。
- 規則升級需符合 `references/rules.md` 索引頂部的證據強度公約，正文寫回對應 `references/rules/RNN.md`。
- 平台規格與演算法會變；若結論依賴當前官方規則，先查權威來源並記 last verified。

## 指令

```powershell
$env:PYTHONUTF8='1'
python scripts/social_data.py validate
python scripts/social_data.py summary --series reborn-married-driver
python scripts/log_outcome.py outcome-bundle.json
python scripts/log_outcome.py outcome-bundle.json --write
python scripts/build_rule_registry.py --write
python scripts/split_rule_archive.py --refresh-manifest
```
