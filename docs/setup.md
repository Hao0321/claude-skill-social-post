# Setup

## 1. 安裝 skill

Clone repo，將 `social-post/` 複製到其中一個位置：

- Codex：`~/.codex/skills/social-post/`
- Claude Code：`~/.claude/skills/social-post/`

Windows PowerShell（Codex）：

```powershell
git clone https://github.com/Hao0321/claude-skill-social-post.git
New-Item -ItemType Directory -Force "$env:USERPROFILE\.codex\skills" | Out-Null
Copy-Item -Recurse ".\claude-skill-social-post\social-post" "$env:USERPROFILE\.codex\skills\social-post"
```

## 2. 建立私人工作檔

在安裝後的 `social-post/` 目錄執行：

```powershell
Copy-Item style_profile.example.md style_profile.md
Copy-Item content_plan.example.md content_plan.md
```

這兩個檔案與日後建立的 `data/` 都不應提交到公開 fork。

## 3. 初始化語氣與內容計畫

依序告訴 agent：

```text
幫我學 FB 風格
幫我排 14 天社群內容
```

如果要從已登入的社群頁面讀貼文或實際發布，環境還需要可控制瀏覽器的工具。規劃、撰稿與數據分析不需要瀏覽器。

## 4. 發布安全閘

告訴 agent「今天發一篇」後，它會先產出各平台草稿。送出前應該：

1. 顯示完整正文。
2. 核對平台與目前登入帳號。
3. 取得當前對話中的明確確認。

未確認就不發布，也不代為登入、切換隱私或刪除貼文。

## 5. 記錄成效

先複製 example bundle 並換成自己的數據：

```powershell
Copy-Item references/outcome-bundle.example.json my-outcome.json
python scripts/log_outcome.py my-outcome.json
```

第一個指令只 dry-run。確認內容後才寫入：

```powershell
python scripts/log_outcome.py my-outcome.json --write
python scripts/social_data.py validate
```

同一貼文日後追加快照時，bundle 可以省略 `post`，只保留新的 `snapshot`；舊快照不會被覆蓋。

## 6. 比較系列與規則

```powershell
python scripts/social_data.py summary --series your-series-id
python scripts/build_rule_registry.py --write
python scripts/self_test.py
```

只比較 maturity 接近的快照。若故事、首幀、文案與發布時間一起改變，必須列為 confound，不能稱為乾淨 A/B。

## Troubleshooting

- `invalid published_at`：時間需使用 ISO 8601 並包含 offset，例如 `2026-08-11T19:49:00+08:00`。
- `unknown post_id`：首次寫入需要 `post`＋`snapshot`；追加快照才可省略 `post`。
- 發到錯帳號風險：發布前截圖或讀取 compose 畫面，讓使用者確認帳號。
- 平台 UI 改版：只更新對應的 `references/facebook.md`、`instagram.md`、`threads.md` 或 `x.md`。
