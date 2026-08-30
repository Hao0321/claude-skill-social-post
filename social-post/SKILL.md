---
name: social-post
description: 學習使用者的 Facebook／Instagram／YouTube／Threads／X 語氣與受眾，規劃、撰寫、確認後發佈內容；以已登入 Chrome 受控掃描、草擬及回覆 FB／IG／Threads 留言；並作為流量、留存與轉化的結構化帳本。使用者說「發文」「用我的口氣」「回覆留言」「自動回留言」「掃留言」「查流量」「演算法」「把數據訓練進去」「比較貼文」「優化 pattern」時使用。
---

# Social Post

把內容生成、實際發布與成效學習分開。依意圖只讀必要資料，不把整個案例庫一次塞進 context。

## Session 啟動

P2 預設讀 `voice_quick.md`；只有 P1 重新學語氣、使用者明確要求深度仿寫，或 quick card 無法裁決時，才完整讀 `style_profile.md` 或使用者明確指定的 voice Skill。安全與使用者明示 > voice quick／明確指定的 voice Skill > 公式。

## 路由

| 觸發 | Mode | 必讀 |
|---|---|---|
| 重新規劃、排內容 | P0 Plan | `references/phase0_plan.md`＋`current_brief.md`＋`scripts/social_data.py comparables` compact context＋目標 formula；Hermes Agent 的結構化 X 研究另讀 `references/hermes-tweet.md` |
| 重新學語氣 | P1 Learn Voice | `references/learn_style.md`＋`style_profile.md` |
| 寫一篇、PO、發文 | P2 Draft／Publish | `references/generate_and_publish.md`＋`voice_quick.md`＋`current_brief.md`＋`scripts/social_data.py comparables` compact context＋單一 formula；確認後才讀平台 ref；Hermes Agent 的 X route 另讀 `references/hermes-tweet.md` |
| 把數據訓練進來、記錄成效 | P3 Log Outcome | `references/outcome-workflow.md`＋`data/*.jsonl` |
| 比較貼文／集數、找 pattern | P4 Optimize Patterns | `references/outcome-workflow.md`＋`references/evaluation.md`＋相關 rules |
| 掃描、草擬、回覆 FB／IG／Threads 留言 | P5 Comment Ops | `references/comment-operations.md`＋實際操作時的 `references/chrome-comment-adapter.md`＋`scripts/comment_chrome_actuator.mjs`＋`references/comment-policy.json`＋目標平台 ref＋`voice_quick.md` |
| 查歷史 Case | Legacy Case | `references/case_studies.md` 索引，再讀單一 `references/cases/case-NN.md` |

路由前用一句話告知正在做哪個 Mode。單純診斷不需要 Chrome。

## Source of truth

| 資料 | Canonical source |
|---|---|
| 貼文／caption／發布條件 | `data/posts.jsonl` |
| 洞察快照 | `data/insight_snapshots.jsonl` |
| 帳號期間總覽 | `data/account_snapshots.jsonl` |
| 跨篇假設與 confound | `data/experiments.jsonl` |
| 事實修正事件 | `data/corrections.jsonl`；原始 event 不覆寫 |
| 規則正文 | `references/rules/RNN.md`；`references/rules.md` 是索引 |
| 規則生命週期／實驗 backlink | `references/rules/metadata.json` |
| 規則機器索引 | `data/rule_registry.json`（生成檔） |
| 舊案例全文 | `references/cases/` |
| Chrome 可見留言 observation | `data/comment_events.jsonl`；私人 append-only ledger |
| Chrome 掃描目標／期限 | `data/browser_scan_requests.jsonl`；私人 append-only ledger，先建立再掃描 |
| 回覆草稿／permit／送出／對帳 | `data/reply_events.jsonl`；私人 append-only ledger |
| 留言自動化政策 | `references/comment-policy.json` |
| 產品能力完成度／外部 canary | 私版 `.rd/capability-ledger.json` 是唯一 canonical ledger；`comment-capabilities.json` 只是 hash-bound 生成式公開投影，fixture 與 live 分開 |

新成效不得只寫進 Markdown。先寫 JSONL，再視需要更新人類摘要。

## 流量與演算法單一歸檔中樞

- 不論素材由 `video-autopilot`、YouTube 專門 Skill、Meta 面板或其他流程產生，所有發布後的流量、推薦來源、搜尋、留存、互動、受眾、追蹤／訂閱與轉化證據，都必須寫回本 Skill 的 `data/*.jsonl`。
- 專門 Skill 可以做平台診斷或產生剪輯／包裝建議；但觀測事實、跨平台比較、實驗證據與規則升降級，以本 Skill 為 canonical source，禁止另建互相漂移的成效記憶。
- 同一內容的 FB／IG／YouTube 指標各自建立有平台 scope 的 snapshot；Meta 合併卡片只能作 cross-platform reference，沒有完整平台洞察時不得冒充該平台 snapshot。
- 演算法時效性知識仍可放目標平台 reference；私人實測是否成立，只能依本 Skill 的同 maturity、多樣本資料升級。

## P3 Log Outcome

1. 每組洞察圖建立新 snapshot；不覆蓋舊數字。既有 event 的發布時間、片長或精度要修正時，追加 correction event，不直接改舊列。
   帳號 7／30／90 天總覽寫 `account_snapshots.jsonl`，不得綁到單篇貼文。
2. 每篇新 post 先建立 `analysis_status`、`analysis_version`、`analysis_eligible` 與精確 caption 的 `caption_sha256`；尚未完成語義分析時只能是 `pending`＋`analysis_eligible:false`，不得先進 pattern learning。
3. `complete` post 必須保存完整文案／版型／長度、換行與段落、標點、關鍵字、named entities、數字語言、opening、hook、mechanism、differentiator、proof、語氣、CTA，以及由 `published_at`＋timezone 驗證出的日期、星期、`HH:mm` 與 daypart。黑底白字另存背景、字色、字重、對齊與觀測行數；影片另存直式版型，不從縮圖猜未見內容。
4. caption 截斷、僅有代稱、placeholder 或尚待補證據時標成 `excluded_placeholder` 或 `pending`，一律 `analysis_eligible:false`；缺值用 `null`／空清單與低 confidence 明示，不補寫不存在的 hook、關鍵字、語氣或 CTA。
5. 記 published_at、captured_at、hours_since_publish 與 maturity。IG／FB total 與可取得的拆分同時保存；missing 用 `null`。
6. UI rate 與 derived rate 分開；留存曲線目測只寫 note。縮寫、上限或目測數字用 `metric_qualifiers` 標成 `rounded／upper_bound／visual_estimate`，不得冒充 exact。`metrics` 內的值直接用欄位名；其他巢狀值使用 dotted path（例如 `benchmarks_reported.views_more_than_usual_approx`）。
7. 先 dry-run `scripts/log_outcome.py`，明確寫入時才加 `--write`；寫完執行 `scripts/social_data.py validate`，caption hash、deterministic counts、日期／星期／分鐘或 analysis eligibility 任一不一致都不得通過。

## P4 Optimize Patterns

先跑 feature matrix；series summary 只作 KPI 總覽。Matrix 只納入 `analysis_status:complete`、`analysis_eligible:true`、caption hash 與 analysis version 均有效的 post，並在選 latest 前排除 `awaiting_data`／`aggregation_eligible:false`，再以相同平台 scope 與 maturity 比較。每列必須同時帶出文案長度、段落／分隔、完整 Unicode 標點 profile、關鍵字、語氣、CTA、黑底白字／影片版型、日期、星期、分鐘與成效；可用 `--captured-before` 重建當時可見的歷史比較，避免後來快照污染判斷。

跨平台同步內容若有可驗證的各平台收據，使用 `platform_publications` 分別記錄平台發布時間、IANA timezone、sync mode、caption digest 與 media digest；只有共同時間、沒有逐平台憑證時保留單一 `published_at` 並明示信心，不虛構每個平台的分鐘。不同 UI 表面出現 104.2／104.3 或 211／215 這類差異時，保留全部 `surface_observations`、表面與證據，canonical 值只作查詢基準，不覆蓋原始差異。

故事、首幀、集數、caption、CTA、版型或時段同時改變時，列為 confound，不稱乾淨 A/B。發布時間只可作候選變因：同一精確分鐘若同時出現高低差異很大的結果，不得把該分鐘寫成爆款原因或固定黃金時段；必須由相近題材、包裝、平台與 maturity 的獨立樣本另行驗證。

證據狀態只用：`hypothesis → emerging → validated → deprecated`。同一系列三集是 n=3 posts，但不是三個獨立樣本。實驗可用同一 `experiment_id` 追加 revision；不可覆寫歷史。候選規則必須同時在 experiment `rule_ids` 與 rule metadata `experiment_ids` 建 backlink。

## 實際發佈與留言安全閘

只有 P2 的瀏覽器發布與 P5 的實際掃描／回覆需要 `chrome:control-chrome` 與已登入狀態。P2 的 Hermes Tweet 選配 X route 使用其獨立 toolset，不需要 Chrome。草稿、規劃、分析、資料回填與 P5 ledger 操作也不需要 Chrome。

- 發佈前必須在當前對話取得明確「確認」。
- 使用者若在當前 session 明示「你自己操作不用問」，私人版可免逐次確認；不跨 session。
- 上一條不適用於 Hermes Tweet 的 `tweet_action`。每次都要確認完整 endpoint、payload、帳號、side effects 與 reason。
- 不幫登入、不改帳號／隱私、不刪文、不自動按讚／follow／大量留言。
- P5 掃描前先以當前 session 建立有期限的 browser scan request，Chrome receipt 只能回綁既定帳號／貼文 scope，完成掃描即追加可區分零留言的 completion event。production scan 模組不含 fixture factory，只接受 source-controlled、trusted-host-resolved、版本化、deep-frozen 且 process-branded 的 FB／IG／Threads plan；目前 live adapter 全部 unavailable。完整展開必須由 versioned exhaustion contract 證明 cursor traversal、monotonic discovered count、explicit terminal 與 terminal coverage；兩次空 viewport read、raw selector、fake tab、caller resolver 或 `threadExpansionComplete` 宣告都無效。P5 預設 `batch_confirm`；`bounded_auto` 只在當前 session 明示平台、帳號、貼文與本輪範圍後，以有期限、指定 scope、有限次數的 ledger grant 啟用。每則回覆都要一次性 permit；重算 reply hash，綁定 action／fresh locator／正確父留言與零 exact-own baseline；reply thread 在碰 trigger、消耗 durable claim、finish 與 recovery reinspection 前都要另以 version 1 exhaustion 證明 target-scoped cursor／count／traversal／terminal stable coverage，`0` reply 或 `0` expander 不構成 absence。later page／lazy expander、無 terminal、virtualization 或 same-fingerprint replacement 一律零 submit click、claim 前發現則零 claim，recovery 不得推導 not-sent。之後才可經 durable atomic claim、process-wide 單次送出及完整畫面驗證。finish／reconcile 另須由 shell:false branded bridge 持有 versioned 一次性 capability；ledger 只存 nonce hash、scope binding 與 receipt digest。裸 `WRITE_OK`、raw／fixture receipt、偽 nonce、重播 capability、未全展開或不可檢查的回覆串一律拒絕；分批執行不得重置 grant 上限。
- 正式版 `comment-policy.json` 的 `live_browser_actuation_enabled` 預設為 `false`：仍可建立 scan request、執行 dry-run／草稿與產生 action，但 `browser-scan --write`、`browser-begin --write`、`browser-finish --write`、`browser-reconcile --write` 在受控 Browser fixture 與登入 canary 完成前一律拒絕。使用者核准回覆不會繞過這個維護者 kill switch。
- 送出結果不明時標記 `needs_reconcile` 並停止整批；未重新讀取畫面前不得重送。零 API Chrome 模式不宣稱 24/7 背景監聽。
- `send_started`／`needs_reconcile` 後若 Node／Chrome 重啟或 receipt capability 過期，只能由 fused actuator 以 fresh session 進入 reconcile recovery；bearer 留在私有 Node 閉包，保留原 attempt、不得重發 submit claim、不得退回 `approved`。
- P5 不處理私訊、媒體／GIF 回覆或全帳號歷史爬取；大量 keyword 索取改用單一公開作者留言提供自助入口。
- 預設跨平台重新包裝；但使用者明示「同步發布／一稿多發」時，正文共用一份，只有平台必填欄位沿用正文內容（例如 YouTube 標題取第一句），不再額外維護多套文案。
- FB／Threads 正文不放外部連結；依 R25 使用留言或平台允許的位置。
- 沒有 IG 圖／影片就停，讓使用者選擇提供素材、跳過 IG 或改 Threads。

## 平台規則

平台規格會變。Hashtag、字數、發佈 UI、演算法等時效規則只在目標平台 reference 維護，標示 last verified；跨 skill 衝突時先查權威來源，不同時保留兩個硬數字。

## 維護

- 每次 outcome 更新後跑 data validate、rule registry build、cleanup drift audit。
- 每次 outcome／analysis 更新後另跑 `python scripts/social_data.py coverage`；只有 `coverage_complete=true`，且每個適用的平台 outcome 子樹都通過獨立 exact-compare 維度，才可宣稱每篇 eligible post 的文案、長度、版型、關鍵字、語氣、完整標點、日期／星期／分鐘與全部 outcomes 已進入可供 P0／P2 使用的矩陣。固定欄位以外的新平台 analytics 自動進 `extended_analytics`，不可因 schema 尚未命名而遺漏。
- 修改任一 `rules/RNN.md` 後跑 `split_rule_archive.py --refresh-manifest`，再 build rule registry。
- `case_studies.md` 只保留索引；新增 Case 寫獨立檔或直接以 structured outcome 取代。
- 公開 export 使用 allowlist：只公開通用引擎、匿名範例與去快照操作卡；不得公開完整 `style_profile.md`、`content_plan.md`、`drafts/`、任何 outcome／correction JSONL、私人 rules／formulas／cases 或 `.rd/`。同步工具必須先跑 privacy preflight，BLOCK 時不得寫入鏡像。
- 維護公開版時，先同步、再驗證公開鏡像；只有當輪使用者明確授權 release 時，才交由 R&D external-change gate 推送。不得把一次授權永久化。
- 能力狀態只改 `.rd/capability-ledger.json`，再用 `python scripts/comment_capability_gate.py --write-projection` 重建公開留言投影；gate 必須拒絕漏項、額外 obligation、狀態漂移、來源 hash 漂移與手改 projection。
- 私公版路徑只從 `audit.config.json` 讀；未設定就回報 NOT_CHECKED，不猜 sibling repo。
- 修改 Chrome comment JavaScript 後，必須先跑 `node scripts/comment_js_architecture_gate.mjs --self-test`，再以 `--output .rd/receipts/js-architecture-gate.json` 保存 actual closed-graph receipt；最後跑 `comment_self_test.py`。此產品原生 gate 只補 JS graph 證據，不得把 Cleanup 的跨語言 `NOT_CHECKED` 改寫成 provider PASS。

```powershell
$env:PYTHONUTF8='1'
python scripts/social_data.py validate
python scripts/social_data.py coverage
python scripts/social_data.py summary --series <series-id>
python scripts/social_data.py matrix --series <series-id> --platform <platform> --maturity <maturity>
python scripts/build_rule_registry.py --write
python scripts/comment_assistant.py validate
node scripts/comment_js_architecture_gate.mjs --self-test
node scripts/comment_js_architecture_gate.mjs --output .rd/receipts/js-architecture-gate.json
python scripts/comment_self_test.py
python ../code-cleanup-helper/scripts/audit.py . --mode all
```
