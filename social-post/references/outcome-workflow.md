# Outcome learning workflow

## 目錄

- 時間政策與資料來源
- Log Outcome
- 補件與部分內容分析
- Post analysis contract
- 比較與同篇後續數據
- 指令

## 時間政策與資料來源

P0–P4永久採publication-only-v1；機器唯一來源為 `scripts/social_outcome_time_policy.py`。分析時間只用發布日期、星期、時區與分鐘。所有新舊文案的截圖／手機時鐘均不索取、不猜測，不影響入庫、分析資格、排序、篩選、比較或寫作特徵。舊captured_at、hours_since_publish、maturity等欄位只留原始歷史存檔；讀取時忽略、新寫入時移除。此作者明示政策優先於舊案例／規則／凍結來源中的相反要求，不更動voice與F段落結構。P5的安全期限與freshness另有用途，不受影響。

成效仍寫回data/posts.jsonl、insight_snapshots.jsonl、account_snapshots.jsonl、experiments.jsonl、corrections.jsonl；原始event不覆寫。規則導航為生成的rule_registry.json，舊全文在references/cases/。同內容各平台各建observation；Meta不明平台總覽與另一平台局部卡只是reference，不能相減補出平台完整成績。帳號30天等總覽用獨立account ID與window_days，不綁單篇。

## Log Outcome

1. 核對永久post ID、平台、內容／版型、發布時間與時區。手機狀態列、附件建立／上傳時間不是發布證據；發布未知保留intake，不猜分鐘。
2. 每次回填用不同snapshot ID追加，所有舊筆保留。同一篇今天、隔天各給一次數字，依提供順序記第1、2筆；最後有效回填供目前查詢，不要求截圖幾點。
3. 作者明示「發文當天／隔天」可放observation_label；這不是自動驗證的精確24小時。不由輸入順序、收件或發布時間捏造實際觀測間隔與每小時速度。
4. 真正沒有成效值才設measurement_status:awaiting_data及aggregation_eligible:false，不能遮蔽先前有效數據。缺截圖時間永遠不是排除理由；缺完整原文是另一件事。
5. UI rate與derived分開；縮寫／上限／目測以metric_qualifiers標exact、rounded、lower_bound、upper_bound、visual_estimate、not_reported，巢狀值用dotted path。來源、受眾、留存及平台明示窗口照原值保存；首頁不是非追蹤，一般點擊不是外連，分享不全是私訊。缺值用null，不補0。
6. 事實／發布時間／精度修正用correction，不改identity。先log_outcome.py dry-run，再明確--write，最後validate／coverage；舊截圖欄位即使格式錯誤也忽略，不修補或索取它們。

## 補件與部分內容分析

review_outcome_intakes.py唯讀盤點，--since只查收件事件日期，不是學習變數。支援owner_post_outcome_intake、owner_post_outcome_intake_pending_publication_time與owner_account_outcome_intake。無本機資料回空清單，不建假樣本。

全文／發布補件分別為author_full_caption_confirmation、author_publication_time_confirmation，以parent intake、snapshot source、post、snapshot ID精確回綁，不多算樣本。發布補件不能改文案／已知時間／snapshot；近似分鐘保留precision。缺截圖時間不再列missing。原生numeric metrics、未知值名單、完整platform_analytics及Meta／IG reference分開；不可丟掉replies、reposts、quotes、profile_views或未來子樹。

--include-analysis才明確讀取data/learning_events.jsonl中的intake_content_analysis，不當成已啟用F。註記精確欄位：analysis_id、source_intake_id、post_id、snapshot_id、platform、media_family、caption_sha256、content_scope、recorded_at、phrases、evidence、structure、hypotheses、confounds、next_test、candidates。

- content_scope為complete_caption或visible_first_post；後者不猜續文、CTA、emoji碼或完整字數。所有計數明示只綁已知原文／prefix。
- phrase有text、role、interpretation、basis。Role為topic/use_case/brand/cost_benefit/rights_claim/launch_hook/proof/differentiator/cta/audience/boundary/time_claim；caption_exact要逐字存在caption，visible_transcription只能引用原筆保存的visible_following_phrases。解讀不是量測因果。
- evidence為非空{path,sha256}，只能引用這筆intake／合法補件的data/evidence來源，bytes漂移即拒絕。四個解讀／測試清單不可空；candidate有candidate_id/statement/exclusions/next_test，保持hypothesis，不自動啟用規則。
- --analysis-input乾跑，--write-analysis才在既有writer lock下追加。同ID完全重播去重，同ID變更拒絕。可選supersedes_analysis_id建立新解讀revision，父筆必須存在、仍有效且同post／snapshot／平台scope；原始event不刪除，不允許跨scope或重複分岔。預設只回放有效revision。
- 分析status與完整度仍依實際文案：缺續文能分析已知片段，但不能假裝取得完整原稿。截圖時間不再影響任何資格。

## Post analysis contract

每篇保留analysis_status、analysis_version、analysis_eligible、caption_sha256、信心及analysis_evidence。完整且可學原文為complete＋true；pending／excluded_placeholder保留已知文字但不冒充全文。完整特徵包含：

- format_features：字數、空白、段落／換行／分隔、完整Unicode標點、emoji、連結、hashtag、surface和版型；黑底白字另記顏色／字重／對齊／行數，影片另記真實比例。
- wording_features：opening、hook、mechanism、differentiator、proof、keywords、實體名、數字語言、voice與CTA。區分「確實沒有」和未知，不把功能主張當已驗證成果。
- publication_context：由published_at與timezone驗證日期、星期、HH:mm及daypart。只有逐平台收據齊全才填platform_publications與各自digest，不補假分鐘。

## 比較與同篇後續數據

Matrix依平台、media family、content type與surface分區，不再有maturity／截圖時鐘條件。先排除缺全文／hash無效的整篇分析，以及真正awaiting／明示不eligible的outcome，再按提供順序取同post／平台最後有效紀錄。舊值完整保留，history --post <id>回傳序列、作者給的階段標籤和同平台數量差額；不自動換算每小時速度。

P0／P2預設取2篇compact comparables，按發布時間選最近案例而非成效排名。沒有同平台／內容類型／版型不回退混池。每列保留原文、長度、版型、完整標點、詞句、語氣、CTA、發布日期／星期／分鐘與全部適用analytics；未被固定schema命名的子樹進extended_analytics，由coverage逐子樹exact compare，私人來源路徑不進生成context。

題材、首圖、文案、CTA或時段同時變更就列confound，不稱乾淨A/B。發布時間是分析條件，不保證同分鐘複製同級流量。重複snapshot不是新獨立post，單篇／同系列不證明關鍵字因果。hypothesis→emerging→validated→deprecated及作者精確diff審核維持；截圖時間不構成任何規則升級門檻。

## 指令

```powershell
python -B scripts/review_outcome_intakes.py --include-analysis --format json
python -B scripts/social_data.py validate
python -B scripts/social_data.py coverage
python -B scripts/social_data.py matrix --platform <platform>
python -B scripts/social_data.py comparables --platform <platform> --content-type <type> --surface <surface> --limit 2
python -B scripts/social_data.py history --post <permanent-post-id> --platform <platform>
python -B scripts/log_outcome.py outcome-bundle.json
python -B scripts/log_outcome.py outcome-bundle.json --write
```
