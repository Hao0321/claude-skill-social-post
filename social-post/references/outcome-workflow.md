# Outcome learning workflow

## 目錄

- 資料來源層級
- Log Outcome
- Review pending evidence
- Post analysis contract
- Optimize Patterns
- Schema 原則
- 因果與證據邊界
- 指令

## 資料來源層級

1. `data/posts.jsonl`：貼文本體、發布條件、caption variant。
2. `data/insight_snapshots.jsonl`：同一貼文可有多個時間快照，永遠保留 `captured_at` 與 maturity。
3. `data/account_snapshots.jsonl`：帳號 7／30／90 天滾動總覽；不綁任何單篇貼文。
4. `data/experiments.jsonl`：跨貼文假設、變因、confound、證據狀態與下一輪測試。
5. `data/corrections.jsonl`：既有 event 的事實修正；append-only，原始列不覆寫。
6. `data/rule_registry.json`：由 `references/rules/RNN.md` 生成的導航，不是規則正文。
7. `references/case_studies.md`：舊案例索引；個別全文在 `references/cases/`，只作歷史證據。

不得再把新數據只寫進 prose。結構化資料是成效事實的 canonical source；Markdown 只留解讀與人類可讀摘要。

任何其他 Skill 收到 FB／IG／YouTube／Threads／X 的流量、演算法、留存、受眾或轉化證據時，都要路由到本資料層。專門 Skill 可保留診斷方法，但不得另存一套會漂移的 outcome memory。跨平台同內容要共用永久 `post_id`，平台各自建 snapshot；只有 Meta 合併卡片時只記 reference，不虛構缺少的平台完整洞察。

X 快照只記平台實際提供的 impressions／views、互動類別、點擊、停留、追蹤與下游轉化；缺少的欄位維持 `null`。公開 For You 原始碼的權重對應的是個別讀者的預測，不得套到貼文總互動數生成「演算法分數」。若以公開機制提出實驗假設，在 experiment 記來源 commit、可觀測指標、maturity 與 confound；規則是否成立仍由私有實測決定，見 `x.md`。

## Log Outcome

1. 確認貼文 identity、平台、發布時間與時區。
2. 每組截圖視為一個 snapshot，不覆蓋前一次。記錄截圖時間；不知道就標 `captured_at_confidence: low`，不要猜成最終值。
   帳號期間總覽使用 `account_snapshot_id`、`platform`、`window_days` 與 `captured_at`；不要建立假的 `post_id`。
   只有發布確認、但尚無任何成效值的事件保留 `measurement_status:awaiting_data` 並設 `aggregation_eligible:false`；不得讓 null／placeholder snapshot 進 latest outcome 或 pattern aggregation。
3. IG／FB 合併面板保留 total，也記可取得的平台拆分。未拆出的 follower／follow 指標加 scope note。
4. UI 顯示率保留在 `rates_reported`；手算 derived metric 不覆蓋 UI 值。
5. Retention 圖沒有精確座標時只寫 curve note，不偽造百分比。
6. 平台縮寫值、`<0.1%`、圖上目測值分別以 `metric_qualifiers` 標成 `rounded`、`upper_bound`、`visual_estimate`；未標者才視為 exact。`metrics` 內的值用直接欄位名；位於 benchmark、audience 或其他巢狀物件的值用相對於 snapshot 根節點的 dotted path。
7. 發現發布時間、片長或舊快照精度錯誤時，bundle 追加 `correction`；不得直接重寫既有 JSONL event。Correction 不可改任何 identity field。
8. 先 dry-run bundle，再以 `--write` 寫入；最後跑 validate。

## Review pending evidence

同批補件或整合最近幾天資料時，先跑唯讀盤點：

```powershell
python -B scripts/review_outcome_intakes.py --since 2025-02-01 --format json
```

`--since` 是本機收件事件的日期（含當日；若有全文補件，採最近補件日期），不是發文或截圖日期。沒有本機 intake 檔時回傳空清單，不建立檔案。報告只供本機看缺件，不是正式成效矩陣或公開輸出。

- `data/outcome_intakes.jsonl` 可保存作者的 `owner_post_outcome_intake`（`post_candidate`、`snapshot_observation`）及 `owner_account_outcome_intake`（`account_snapshot_candidate`）。每筆有唯一 `intake_id`、`recorded_at`、`owner_scope: own`、`platform`。保留原始證據，不用收件時間代替觀測時間。
- `author_full_caption_confirmation` 以 `parent_intake_id`、`snapshot_source_intake_id`、`post_id`、`snapshot_id` 綁定原筆，提供完整分析的 `post_candidate`；全文須與原截斷開頭一致。補件不另計樣本；同篇多組真正不同快照也不多算貼文。舊紀錄留作歷史。
- Facebook 等單平台原值、未明示平台的總覽、另一平台參考，以及帳號期間總覽分開。缺值不補 0，縮寫不補精度，不把一般點擊算成外連點擊。
- 缺截圖時間就留在待補件，不猜測、不計入正式比較。補齊後，用原身分與來源建立正式 bundle，走原生 dry-run → 明確寫入 → validate／coverage。盤點只用精確 ID 確認是否已登錄，不驗證流量歸因或執行升級。

## Post analysis contract

每篇 learned post 都必須明示以下狀態，不能只靠 caption 是否非空來判斷可否學習：

- `analysis_status` 只用 `pending／complete／excluded_placeholder`。
- `analysis_version` 記錄產生目前特徵的分析器版本；未分析的新 post 使用 `pending`。
- `analysis_eligible` 只有完成且證據足夠的真實 caption 才能是 `true`。
- `caption_sha256` 綁定 UTF-8 caption 原文；caption 改動後舊分析必須失效並重新產生。
- `published_at_confidence`、`caption_confidence` 與 `analysis_evidence` 明示時間、文案和分析的證據邊界。

`analysis_status:complete` 必須保留可重算與可比較的完整特徵：

1. `format_features`：surface、caption layout、字數、去空白字數、內容字數、空格、段落、明示換行、分隔塊、逗號／頓號／句號／問號／驚嘆號、引號／書名號、連結、hashtag、emoji 與明示 CTA 數。Facebook 黑底白字另記背景、字色、字重、置中與實際觀測行數；Reel／Short／短劇另記 `vertical_9_16`，不得以 caption 換行冒充 UI 自動換行。
2. `wording_features`：opening、hook、mechanism、differentiator、proof style、keywords、named entities、numbers observed、numeric language、voice、punctuation style 與 CTA。未知值用 `null`／空清單，不用推測補齊；可由完整 caption 確認「確實沒有」時，另用 `proof_present:false`、`cta_type:none`、`explicit_cta:0` 等欄位區分「已知不存在」與「尚未取得」。
3. `publication_context`：由 `published_at` 與 timezone 重算並驗證 `local_date`、`weekday_zh_tw`、`local_time`（`HH:mm`）與 daypart；不得依截圖手機狀態列時間猜發布分鐘。
4. 同稿跨平台若有逐平台證據，另存 `platform_publications`：每個平台自己的 `published_at`、IANA timezone、`sync_mode`、caption SHA-256 與 media SHA-256。沒有逐平台收據或媒體 digest 時不要填假值，保留共同發布時間與信心即可。
5. 穩定的文案與包裝特徵屬 post，不藏在某一平台的 insight snapshot；snapshot 只保存該次觀測的成效與平台脈絡。

caption 被截斷、只看見片名／集數代稱、或仍等待完整資料時：

- 用 `excluded_placeholder` 或 `pending`，並強制 `analysis_eligible:false`。
- placeholder 可保存實際可見字串及 exclusion reason，但不得把未知的 hook、版型、關鍵字、語氣或 CTA 當成已觀測事實。
- pending／placeholder 不進 voice、keyword、timing 或 pattern aggregation；補到原始證據後再以 append-only correction 升級。

## Optimize Patterns

分析前先用 feature matrix 連結 post 特徵與同平台、同 maturity 的 latest eligible snapshot；series summary 只作 KPI 總覽。先排除 `pending`、`excluded_placeholder`、`analysis_eligible:false`、caption hash 不符、analysis version 無效、`awaiting_data` 或 `aggregation_eligible:false`。比較順序：

Matrix 的 outcome 不只驗證固定 KPI。每個適用但未被固定 schema 命名的平台子樹（例如 YouTube 搜尋詞、48 小時來源、外部來源、推薦內容、營利與內容包裝）都必須原值進入 `extended_analytics`，並由 `coverage` 逐子樹 exact-compare。少一棵、值漂移或憑空多一棵都不能宣稱完整；私人 evidence 路徑與 digest 則只留在 canonical ledger，不進生成 context。

1. 平台 scope、觀測時間與 maturity 是否相近、是否 plateau；不同 maturity 不直接排終局勝負。
2. Watch quality：平均觀看占片長、略過率、首段／片尾曲線。
3. Distribution：Reels＋探索、個人檔案、非粉絲。
4. Conversion：follow／play、follow／reach、profile／reach。
5. Content 與 packaging：cold open、standalone premise、字幕／語言、caption 長度、段落／分隔、標點、關鍵字、語氣、CTA、黑底白字或影片版型、首幀與時段。

兩集同時改了故事、首幀與 caption，不得稱為 A/B。先列共變量與 confound，再說哪個解釋目前最有力。

## Schema 原則

- ID 永久不改：`post_id`、`snapshot_id`、`experiment_id`。
- 時間使用 ISO 8601＋offset，例如 `2026-08-11T14:56:00+08:00`。
- Learned post 必須有可驗證的 `analysis_status／analysis_version／analysis_eligible／caption_sha256`；只有 `complete＋true` 才可進 pattern learning。
- 日期、星期與 `HH:mm` 是由發布 timestamp 衍生的可驗證欄位；衍生值不一致就 fail，不同欄位不得各自成為漂移的 source of truth。
- 百分比一律存 0–100，不存 0–1。
- Missing value 用 `null`，不填 0。
- Measurement qualifier 只用 `exact／rounded／lower_bound／upper_bound／visual_estimate／not_reported`；巢狀 measurement 以 dotted path 指向實際存在的值，validator 會拒絕失效路徑。
- Evidence status 只用 `hypothesis／emerging／validated／deprecated`。
- 同系列多集不等於獨立樣本；在 `independent_samples` 明示。

## 因果與證據邊界

- Caption 可是分類／搜尋／轉化訊號，但不能替代影片留存。
- 早期 snapshot 只能報趨勢，不做終局勝負。
- 發布日期、星期與分鐘只能先列為候選變因，不能由單篇或同系列共變資料直接推成因果；同一精確分鐘若同時出現高低差異很大的結果，就不是已驗證的爆款時段。
- `n=3` 同系列可降低單點偶然，不能直接升成跨題材定律。
- 規則升級需符合 `references/rules.md` 索引頂部的證據強度公約，正文寫回對應 `references/rules/RNN.md`。
- 平台規格與演算法會變；若結論依賴當前官方規則，先查權威來源並記 last verified。

## 指令

```powershell
$env:PYTHONUTF8='1'
python scripts/social_data.py validate
python scripts/social_data.py summary --series <series-id>
python scripts/social_data.py matrix --series <series-id> --platform <platform> --maturity <maturity>
python scripts/social_data.py matrix --series <series-id> --captured-before <ISO-8601-with-offset>
python scripts/log_outcome.py outcome-bundle.json
python scripts/log_outcome.py outcome-bundle.json --write
python scripts/build_rule_registry.py --write
python scripts/split_rule_archive.py --refresh-manifest
```
