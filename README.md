# social-post skill

一個可安裝到 Codex 或 Claude Code 的社群內容 skill：學習你的語氣、規劃內容、撰寫平台化貼文、經確認後發布，並把 Reels／貼文洞察變成可驗證的結構化學習資料。

目前版本：**v2.1.1**。

## v2.1.1 新增什麼

- 新增 `account_snapshots.jsonl`，帳號 7／30／90 天總覽不再偽裝成單篇貼文數據。
- `log_outcome.py` 支援獨立 account snapshot，並納入 revision hash、lock、atomic commit 與 rollback。
- Validator 檢查平台、時間窗、ID、時間與非負指標；self-test 覆蓋公開空資料與帳號快照寫入。
- 私人 account snapshots 與原始洞察仍由 public export allowlist 排除。

## v2.1.0 重點

- 預設生成路徑改成 quick cards，只讀必要語氣、當前 brief 與一個公式；歷史案例不再灌進每次 context。
- Outcome store 加上跨平台 schema 驗證、原子多檔 transaction、lock 與 optimistic revision，避免並發更新靜默蓋掉資料。
- 實驗採 append-only revision，規則狀態改由明確 metadata 管理，並要求 experiment ↔ rule 雙向 backlink。
- Rules／formulas／cases 拆成單檔索引；mutable 成效只進 JSONL，Markdown 不再複製「最新數字」。
- 新增設定式 public export allowlist、架構 layers 與 required dependency gates。
- 平台 reference 加入查核日期與範圍，區分平台硬規格、內部策略與未驗證演算法假設。

舊版累積的公式、平台規則與公開案例仍保留在 [`social-post/references`](social-post/references)。

## 安裝

```bash
git clone https://github.com/Hao0321/claude-skill-social-post.git
```

Codex：

```powershell
New-Item -ItemType Directory -Force "$env:USERPROFILE\.codex\skills" | Out-Null
Copy-Item -Recurse ".\claude-skill-social-post\social-post" "$env:USERPROFILE\.codex\skills\social-post"
```

Claude Code：把上面的 `.codex\skills` 改成 `.claude\skills`。

macOS／Linux 可把 `social-post/` 複製到 `~/.codex/skills/social-post/` 或 `~/.claude/skills/social-post/`。

接著建立本機檔案：

```powershell
Copy-Item style_profile.example.md style_profile.md
Copy-Item content_plan.example.md content_plan.md
```

接著把 `voice_quick.md` 與 `current_brief.md` 的 placeholder 換成自己的語氣與平台方向。`style_profile.md`、`content_plan.md`、個人化 quick cards 與日後產生的 outcome data 都是你的本機資料，不要提交回公開 fork。

## 五個 Mode

| Mode | 用途 | 例句 |
|---|---|---|
| P0 Plan | 排內容與實驗 |「幫我排 14 天內容」|
| P1 Learn Voice | 學使用者語氣 |「學我的 FB 風格」|
| P2 Draft／Publish | 分平台撰稿與發布 |「今天發一篇」|
| P3 Log Outcome | 保存洞察快照 |「把這批 Reels 數據訓練進去」|
| P4 Optimize Patterns | 跨篇比較與規則升降級 |「比較這三集，找出掉量原因」|

發布是唯一需要瀏覽器登入狀態的 Mode，而且送出前必須取得當前對話的明確確認。分析資料、寫草稿和產出策略都不需要瀏覽器。

## Outcome 快速開始

先用無私人資料的 example 做 dry-run：

```powershell
cd social-post
$env:PYTHONUTF8='1'
python scripts/log_outcome.py references/outcome-bundle.example.json
python scripts/self_test.py
```

正式寫入時才加 `--write`。工具會建立 `data/`，並以 transaction 方式驗證後再更新檔案。

```powershell
python scripts/log_outcome.py your-bundle.json --write
python scripts/social_data.py validate
python scripts/social_data.py summary --series your-series-id
python scripts/build_rule_registry.py --write
```

Schema、因果邊界與追加快照方式見 [`outcome-workflow.md`](social-post/references/outcome-workflow.md)。完整安裝說明見 [`docs/setup.md`](docs/setup.md)。

## 隱私邊界

公開 repo 只放通用引擎、example 與既有公開案例。不要提交：

- `style_profile.md`
- `content_plan.md`
- `drafts/`
- `data/`
- 任何未取得同意的洞察截圖或 caption archive

## 驗證

```powershell
python social-post/scripts/self_test.py
python social-post/scripts/social_data.py validate
```

## License

[MIT](LICENSE)。作者：駱君昊（Hao）。
