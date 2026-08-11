# social-post skill

一個可安裝到 Codex 或 Claude Code 的社群內容 skill：學習你的語氣、規劃內容、撰寫平台化貼文、經確認後發布，並把 Reels／貼文洞察變成可驗證的結構化學習資料。

目前版本：**v2.0.0**。

## v2.0.0 新增什麼

- P3 Log Outcome：每次洞察截圖保存成時間快照，不覆蓋舊數字。
- P4 Optimize Patterns：跨貼文、跨集比較，明示變因、confound 與證據狀態。
- `posts.jsonl`、`insight_snapshots.jsonl`、`experiments.jsonl` 三層資料模型。
- 可重複執行的 validate、series summary、dry-run／atomic write 與 rule registry scripts。
- 公開版不附作者的語氣檔、內容日曆、原始成效資料或私人草稿。

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

`style_profile.md`、`content_plan.md` 與日後產生的 `data/` 都是你的本機資料，不要提交到公開 fork。

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
