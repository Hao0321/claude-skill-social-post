# social-post skill

一個可安裝到 Codex 或 Claude Code 的社群內容 Skill；另提供精簡的 ChatGPT Chat 版。可學習本機聲線、規劃內容、撰寫平台化貼文、經確認後發布，以已登入 Chrome 受控管理 FB／IG／Threads 留言，並把跨平台洞察保存成可驗證的結構化資料。

## 一起共創 Social Post

所有人都能用 Issue 提案、透過 fork → Pull Request 提交改善；Hao 保留唯一的最高管理權、合併審查與正式發布權。認可的夥伴可參與模組開發和審查，專案維持 MIT 開源。

先看 [共創指南](CONTRIBUTING.md)、[治理與協作權限](GOVERNANCE.md) 和 [共創路線圖](ROADMAP.md)。每份 PR 說明要改善的使用情境、改前／改後證據及限制，再經測試與維護者審查合併。私人語氣、真實貼文、帳號成效與留言留在各自本機；公開測試使用 fictional 資料。

討論想法可到 [Discussions](https://github.com/Hao0321/claude-skill-social-post/discussions)，可重現問題與正式提案使用 [Issues](https://github.com/Hao0321/claude-skill-social-post/issues/new/choose)。

目前穩定標籤：**v2.5.0**；`main` 已同步 **Unreleased candidate**。

Unreleased candidate 有封閉 JavaScript 模組清單、固定 browser-runtime revision／雜湊、架構自校準與單次送出／異常恢復的回歸測試。另已完成一次 IG 真實單次送出、原生子回覆查證與唯讀 recovery 對帳，以及一次 Chrome 斷線後的來源連線恢復與原目標讀取；這些證據不代表三平台 live Meta 回覆已解鎖。

> `main` 已分開讀取與送出開關：FB／IG／Threads 指定原生留言的 target-only 回填各有實證；整篇掃描未開放，`live_browser_actuation_enabled` 仍預設為 `false`。真實送出／結果回讀未完成三平台 canary，不能宣稱全面自動回覆已完成。

本候選版仍未完成三平台真實自動回覆驗收。過長契約與平台程式已按責任拆分，完整測試通過；但離線測試不能代替 FB／Threads 的登入操作、完整回覆串與父層驗證。穩定標籤仍為 v2.5.0，沒有新建正式 Release 或升級 production capability。

Cleanup 保留固定的程式長度警告與未測項，不以調高門檻消除問題。跨語言圖與私版 `no-origin` 更新來源仍未由 Cleanup 驗證；另有產品原生 JavaScript 架構圖，但不能把不同量尺或未測項當成同一份通過證明。

## Unreleased on main

- 工作台更新至 0.2.0：五平台 × 圖文／影片共十個學習分區；同平台仍按 content type、surface 與 maturity 選取可比較案例，不用其他分區的贏家補空缺。外部案例與自己的成效分開保存。
- 新增私人寫作契約：凍結已安裝的聲線、F 寫法與規則來源，寫稿綁定指定 F／格式與正式版本。F 變體分開選擇，過期版本、來源漂移及結構違規會被拒絕；結構檢查不能代替 AI 的語義與事實審查。
- 新資料只成為觀測或候選修改。正式更新採「完整前後文與證據 → 作者審核指定版本 → 另行啟用」，僅影響核准的平台／媒體分區；原始來源和前版保留。介面新增「資料分區與審核」及編輯器的 F 契約核對。
- 新流程通過 18 項原生治理測試與 28 項隔離 Chromium 介面檢查；介面測試使用 fictional 資料，並非 Meta 實帳號發布或回覆驗收。

- 共用掃描、送出、領域驗證與各平台 DOM reader 已模組化；所有新增執行依賴仍納入來源雜湊與精確公開清單。模組與依賴數由當次架構測試產生，不用舊報告冒充本版證據。
- 新增來源持有的 Chrome 明確斷線恢復：只在 cached browser 的精確斷線錯誤後重選一次，同一來源與 Chrome family，不清除防重送紀錄。空分頁、一般逾時、頁面失效及權限拒絕不觸發重連；已完成一次真實恢復後的指定留言讀取，不保證所有斷線原因均已排除。
- 指定留言的唯讀 intake 優先使用唯一 exact-URL 分頁，重新核對 handle／URL 並保留既有分頁；沒有相符分頁才建立暫時分頁，多個相符則停止。送出與對帳流程不因此變更。
- Threads 圖示式回覆按鈕新增獨立 semantic-SVG node binder，保留原有 IG／generic 文字識別；隱藏文字、額外圖示、標籤不一致或節點漂移一律拒絕。此 helper 本身不點擊、不填字、不授權送出。
- 將文件唯讀核對與 runtime 權限狀態分離，將 DOM-CUA 節點識別與送出規則分離；原介面、防重送狀態與來源雜湊保護保留。
- 新增 FB 原生留言完整本文 reader，涵蓋 IMG.alt／BR、作者歧義、在線狀態連結、父子網址與驗證途中換頁的負向測試。修正後已完成一則真實 exact-tab 重用、來源雙讀與私人帳本回填；不代表整篇或回覆串完整，未送出 FB 留言。
- Threads 原生 reader 以明確的 root／focus pagelet context、原生時間連結、完整本文與帳號雙讀核對指定留言；一則真實 target-only 回填已完成。拒絕錯誤父層、截斷、載入中及 URL／帳號漂移；「尚無回覆」只記為候選訊號，不當作完整空串或送出授權。
- 新增 `observeTargetComment`：只回填一則指定原生留言，保留完整作者／本文與來源憑證，不冒充整篇掃描完成。
- 新增獨立的單則 IG `executeCanaryReply` 候選入口：只能使用已核准 action、最長 300 秒且限一次的來源綁定 lease；正式送出開關維持關閉，不因 canary 自動升級三平台能力。
- 一次真實 IG 執行已驗證「單次送出 → 即時回讀不足而停止 → 新 session 唯讀 recovery → 原帳本確認 sent」，沒有重送；真實本文、帳號與回覆連結只保留在私人帳本。
- 修正原生 textarea 以目前 `value` 綁定節點，並在刻意選擇父留言後綁定選中的編輯器；填字與後續 claim 前的穩定節點檢查仍嚴格保留。
- IG 原生回覆保留平台自動產生的 `@mention`，先確認完整回覆串與零自己回覆；以實際頁面連續核對處理巢狀展開與延後載入，不假造瀏覽器未提供的 document epoch。未知結果停止並進入唯讀對帳。
- 新增 default-only `executeApprovedReply` 候選入口與 read-only recovery，拒絕 caller tab／action／selector／callback；原核准文字、帳號、貼文、留言及原 attempt 都必須一致。
- 更新 Codex Chrome runtime 固定版本至 `26.825.51511`，保留 bytes／SHA-256 驗證。
- Threads 已驗證一則原生父層 context 與 target-only 回填；完整回覆串、選定編輯器、送出與新子回覆查證仍未驗收。FB 已辨識既有自己回覆，但完整展開與編輯器選定父層尚未驗證。IG 原生留言頁已核對帳號、完整本文、父子留言、正數回覆展開及原生 mention 編輯器；真實送出仍限獨立 canary，不代表泛用路徑已開放。
- 修正 Facebook story query 身分保留與完整度判定；支援 Instagram 同一 shortcode 的 `p/reel/reels/tv` 網址及 `/p/S/c/P` 留言，拒絕跨貼文、重複或矛盾識別欄位。IG 內顯示的 Facebook 留言數不得混入 IG 掃描。
- 公開版本只含通用程式與匿名測試。真實留言、草稿、帳號洞察、原文、照片與私人憑證不在發布範圍內。

- 結構化分析不只保存成效數字，也保存原文 SHA、確定性長度、版型／黑底白字屬性、關鍵字、實體、數字語言、voice、CTA、完整 Unicode 標點，以及日期、星期、`HH:mm` 與 daypart。
- 新增 `coverage` gate，逐篇證明完整原文、長度、版型、關鍵字、語氣、標點、發文時間與 outcome 確實進入 feature matrix；每個適用的平台 analytics 子樹另有 exact-compare 維度，未被固定 schema 命名的新欄位也會進 `extended_analytics`，低信心 placeholder 不會混入規律。
- P0 規劃與 P2 撰稿必須先讀 canonical comparables／context；只有同平台、同 maturity、同 content type 與同 surface 才能比較 outcome。
- 發文分鐘只作候選變因，`causal_claim_allowed:false`；不會因兩篇同時發文就把流量差歸因於時間。
- FB／IG／Threads localhost Browser E2E 已通過：每平台各掃描兩則、只接受一次送出、正確 parent 與 exact reply 均可驗證。證據仍是 `localhost_test_only_candidate`、`in_memory_test_only`，promotion 與 live actuation 都保持 false。
- 修正 contenteditable readback、跨 realm submit schema、導頁後平台／帳號／貼文 readiness gate，以及每次 attempt 明示 `test_only`。
- 唯一核准的 browser-client lazy import 現在會在載入前驗證固定 revision、bytes 與 SHA-256，並寫入 architecture receipt；缺檔、重複 import、eager import 或任一欄漂移都 fail closed。

## v2.5.0

- 新增模組化 live-DOM actuator contract：薄 facade 分離 scan、send 與本機 durable claim bridge，掃描、preflight、單次送出、送後驗證與重新對帳都有可執行負向測試。
- 核准文字會重算 SHA-256，action、fresh locator plan、強留言 anchor、同一父層 reply controls 與零 exact-own baseline 全部綁入 preparation；可變 locator `expected` 不能覆蓋核准證據。
- 不再接受裸字串 `WRITE_OK`。`browser-begin` 必須先原子寫入 append-only ledger，才輸出逐欄綁定的 `SUBMIT_CLAIM`；process-wide reservation 與 durable ledger 共同阻擋併發、actor 重建及跨程序重播。
- 送後只有完整展開、所有 reply item 可檢查、正確父層從 0 變成恰好 1 份 own-account exact reply，而且總回覆數至少為送出前基線＋1 才能成功；回覆總數倒退、pre-existing、hidden、malformed 或 duplicate evidence 都 fail closed。
- fixture receipt 明示 `test_only:true`，Python live ledger 直接拒絕；URL 也拒絕 credentials、非預設 port、不同 host／path／query。
- `browser-scan` 現在持久化 completion event，可區分「request 還沒執行」與「已完整掃描但零留言」。
- 任一同 session／同平台／帳號／貼文的回覆進入 `needs_reconcile`，後續 action 與 preflight 都會被 circuit breaker 阻擋，直到完成對帳。
- FB／IG／Threads fixture 改為真實互動頁面：驗證 exact own reply、正確 parent、一次 accepted submit、composer 清空與 submit disabled。
- 新增 closed-world capability ledger，明確分開 contract 綠燈、真瀏覽器 fixture 與 live Meta canary；缺 Browser backend 或登入授權時不冒充完成。

## v2.4.0

- P5 從操作手冊升級成可執行的 Chrome action／receipt bridge：`browser-scan-request → browser-scan → browser-action → browser-begin → browser-finish → browser-reconcile`。
- 掃描 scope 會先寫入有 session 與期限的 append-only request；Chrome 不能從目前頁面自行決定帳號或貼文，每則 comment anchor 也必須綁定核准貼文。
- 每次送出會綁定 action、一次性 permit、session、平台／帳號／貼文／留言、本文 fingerprint 與最終 reply hash。
- 送出前驗證貼文 URL、空白 composer、填入後 exact text 與 60 秒 freshness；送出後只有六項畫面證據全成立才記為 `sent_verified`。
- 任何 timeout、導頁、矛盾狀態或不明結果一律 `needs_reconcile`，不自動重點；重新檢視仍不確定就保持 `NO_CHANGE`。
- 正式 ledger 會拒絕可繞過 bridge 的 raw begin／finish／reconcile；三平台匿名 fixture 與負向測試可安全開源。

## 安裝

```bash
git clone https://github.com/Hao0321/claude-skill-social-post.git
```

Codex（Windows PowerShell）：

```powershell
New-Item -ItemType Directory -Force "$env:USERPROFILE\.codex\skills" | Out-Null
Copy-Item -Recurse ".\claude-skill-social-post\social-post" "$env:USERPROFILE\.codex\skills\social-post"
```

Claude Code：把目的地改成 `.claude\skills\social-post`。macOS／Linux 可複製到 `~/.codex/skills/social-post/` 或 `~/.claude/skills/social-post/`。

ChatGPT Chat：可在「技能 → 建立 → 透過編輯器建立」使用 [`chatgpt-socialpost/SKILL.md`](chatgpt-socialpost/SKILL.md) 的公開規則，並在個人化設定保留自己的私人語氣簡卡。這個精簡版不包含本機分析腳本、Chrome 留言操作或任何作者的私人樣本；只安裝公開規則，不代表已完成個人聲線校準。不要把私人貼文、帳號數據或憑證提交到本 repo。

首次使用先建立只存在本機的個人檔：

```powershell
cd social-post
Copy-Item style_profile.example.md style_profile.md
Copy-Item content_plan.example.md content_plan.md
```

再把 `voice_quick.md` 與 `current_brief.md` 的 placeholder 換成自己的方向。

完成自己的聲線、規則與已安裝 F 寫法設定後，明確建立本機初始契約；這不是從公開範本學會任何作者的個人語氣：

```powershell
python -B scripts/social_governance.py bootstrap --write
python -B scripts/social_governance.py status
python -B scripts/social_governance.py channels
```

只有首次設定使用 `bootstrap`。之後新增爆款案例不直接改原檔，改走候選、作者審核、另行啟用；遇到來源漂移不可用重新初始化掩蓋。契約、學習紀錄、候選與審核事件都只存本機 `data/`，不要提交至公開 repo。完整流程見 [寫作契約與分區學習](social-post/references/writing-governance.md)。

## 六個 Mode

| Mode | 用途 |
|---|---|
| P0 Plan | 規劃內容與實驗 |
| P1 Learn Voice | 從已授權樣本學本機聲線 |
| P2 Draft／Publish | 撰稿；當輪確認後才發布 |
| P3 Log Outcome | 保存貼文、快照、帳號總覽與 corrections |
| P4 Optimize Patterns | 對齊 maturity 後做跨篇／跨平台比較 |
| P5 Comment Ops | 以 Chrome 受控掃描、草擬與核准；live 回覆需另經 canary 解鎖 |

## 本機工作台 0.2.0

新增黑／暖白／鈷藍的 editorial 介面，沒有表情符號、遠端字型或額外 npm 執行依賴。六個流程各有用途、輸入與產出導覽；P2 可另外選 A／B／C 寫法及本機已安裝的 F 公式。這是 main 上的 source candidate，不是新 stable Release。

從 repo 根目錄啟動：

~~~bash
python -B social-post/scripts/workbench.py
~~~

開啟 http://127.0.0.1:8766，或在 Codex／Claude Code 呼叫 Social Post 並說「開啟工作台」。需要 Python 3.10+；只監聽本機，不提供手機遠端入口。

目前撰稿流程是「選平台／圖文或影片／寫法／公式 → 填題材 → 建立並複製任務 → Codex／Claude Code 讀取正式契約並依 Skill 寫完整 → 貼回核對、編輯、保存」。介面尚未自動呼叫 AI 或接收 AI 結果；不要把任務預覽誤認為生成文案。草稿可保存、重開、複製、下載；黑底白字預覽明示不是 Facebook 的實際排版。

P3 支援先驗證再明確追加 outcome JSON，保留原始歷史並拒絕過期、重播與資料版本衝突；P4 讀取最近 exact-cohort 案例，不假造資料或預測流量。P5 只建立回覆草擬任務；UI 不會自動發布或送留言，也不改既有 production 開關。

詳見 [工作台導覽](social-post/references/workbench.md)。[收費服務架構](social-post/references/service-architecture.md) 是設計提案，沒有部署商業 API、計費或多租戶服務；不要把本機服務直接暴露到公開網路。

## Comment Ops 快速開始

P5 不串 Meta API，也不匯出 Chrome Cookie 或 session。預設是 `batch_confirm`，不提供 24/7 背景監聽或無邊界全自動模式。`main` 的受控掃描與送出採獨立政策；核准回覆不會繞過 default-off 送出開關。實際 Chrome 操作需要 `chrome:control-chrome`、使用者既有登入狀態與來源綁定 adapter。已驗證的單則 IG canary 不代表其他留言、平台或批次路徑已驗證。

Codex 與 Claude Code 都能使用 P0–P4、P5 的離線草稿／政策／ledger／測試功能。現有 existing-session Chrome runtime 則固定依賴 Codex bundled Chrome revision；Claude Code 或獨立公開 clone 找不到精確 runtime 時會 fail closed，不會改走未審核的瀏覽器路徑，也不代表 Claude 安裝已具備 live Meta 控制能力。

```powershell
$env:PYTHONUTF8='1'
python scripts/comment_assistant.py validate
python scripts/comment_assistant.py queue --format json
python scripts/comment_self_test.py
python scripts/comment_capability_gate.py
node scripts/comment_chrome_actuator_test.mjs
node scripts/comment_chrome_claim_bridge_test.mjs
node scripts/comment_chrome_claim_integration_test.mjs
node scripts/comment_js_architecture_gate.mjs --self-test
```

實際流程與停損條件見 [`comment-operations.md`](social-post/references/comment-operations.md)，JSON bridge contract 見 [`chrome-comment-adapter.md`](social-post/references/chrome-comment-adapter.md)。定位依當下可見 DOM／accessibility state 建立，不使用一組長期寫死的 Meta selector。所有 ledger command 預設 dry-run，明確加上 `--write` 才會寫入本機。

## Outcome 快速開始

```powershell
$env:PYTHONUTF8='1'
python scripts/log_outcome.py references/outcome-bundle.example.json
python scripts/self_test.py
python scripts/social_data.py validate
python scripts/social_data.py coverage
python scripts/social_data.py summary --series fictional-workbench-example
```

正式寫入時才加 `--write`。修正既有 event 可參考 [`correction-bundle.example.json`](social-post/references/correction-bundle.example.json)。

## 隱私邊界

公開 repo 只收 schema、工具、匿名規則與明示為 fictional 的例子。不要提交：

- `style_profile.md`、`content_plan.md`、`drafts/`；
- `data/*.jsonl` 的真實 outcome／correction；
- `comment_events.jsonl`、`reply_events.jsonl`、`browser_scan_requests.jsonl` 的真實留言、作者、貼文、回覆與掃描目標；
- 原始洞察截圖、caption archive、帳號名稱、個人路徑；
- 私人 JSONL 貼文／成效／correction／帳號資料與 `.rd` receipts／canonical ledger；
- Cookie、session、access token、瀏覽器 profile、登入資料；
- 從私人數據升級出的規則、公式或案例。

## 驗證

```powershell
python social-post/scripts/self_test.py
python social-post/scripts/social_data.py validate
python social-post/scripts/social_data.py coverage
python social-post/scripts/comment_assistant.py validate
python social-post/scripts/comment_capability_gate.py
node social-post/scripts/comment_chrome_actuator_test.mjs
node social-post/scripts/comment_chrome_claim_bridge_test.mjs
node social-post/scripts/comment_chrome_claim_integration_test.mjs
node social-post/scripts/comment_js_architecture_gate.mjs --self-test
```

## License

[MIT](LICENSE)。Copyright holder：Hao0321 contributors。
