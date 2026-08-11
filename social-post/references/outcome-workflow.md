# Outcome learning workflow

## 資料來源層級

1. `data/posts.jsonl`：貼文本體、發布條件、caption variant。
2. `data/insight_snapshots.jsonl`：同一貼文可有多個時間快照，永遠保留 `captured_at` 與 maturity。
3. `data/experiments.jsonl`：跨貼文假設、變因、confound、證據狀態與下一輪測試。
4. `data/rule_registry.json`：由 rules 生成的導航，不是規則正文。
5. `references/case_studies.md`：舊案例，只作歷史證據。

不得把新數據只寫進 prose。結構化資料是成效事實的 canonical source；Markdown 只留解讀與人類摘要。

## Log Outcome

1. 確認貼文 identity、平台、發布時間與時區。
2. 每組截圖視為一個 snapshot，不覆蓋前一次。記錄截圖時間；不知道就標 `captured_at_confidence: low`。
3. IG／FB 合併面板保留 total，也記可取得的平台拆分。未拆出的指標加 scope note。
4. UI 顯示率保留在 `rates_reported`；手算 derived metric 不覆蓋 UI 值。
5. Retention 圖沒有精確座標時只寫 curve note，不偽造百分比。
6. 新貼文 bundle 含 `post`＋`snapshot`；追加快照時可只含 `snapshot`。
7. 先 dry-run，再以 `--write` 寫入；工具會先在暫存資料中驗證，通過後才一次替換資料檔。

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
- `series_id`、`episode_number`、`duration_seconds` 是選填；一般圖文貼文不必偽裝成系列影片。
- 百分比一律存 0–100，不存 0–1。
- Missing value 用 `null`，不填 0。
- Platform breakdown 可以是 partial；只有涵蓋貼文全部平台時才強制加總等於 total。
- maturity 使用 `early`、`early_not_plateau`、`developing`、`near_48h_not_final`、`mature` 或 `plateau`。
- Evidence status 只用 `hypothesis`、`emerging`、`validated`、`deprecated`。
- 同系列多集不等於獨立樣本；在 `independent_samples` 明示。

## 因果與證據邊界

- Caption 可是分類、搜尋與轉化訊號，但不能替代影片留存。
- 早期 snapshot 只能報趨勢，不做終局勝負。
- `n=3` 同系列可降低單點偶然，不能直接升成跨題材定律。
- 規則升級需符合 `references/rules.md` 的證據強度公約。
- 平台規格與演算法會變；若結論依賴當前規則，先查官方來源並記 last verified。

## 指令

```powershell
$env:PYTHONUTF8='1'
python scripts/social_data.py validate
python scripts/social_data.py summary --series your-series-id
python scripts/log_outcome.py references/outcome-bundle.example.json
python scripts/log_outcome.py references/outcome-bundle.example.json --write
python scripts/build_rule_registry.py --write
```
