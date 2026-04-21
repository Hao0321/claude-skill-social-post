# 完整 Setup 指南

從零到每天自動發文的完整步驟。

---

## 0. 前置需求

- [x] 已安裝 [Claude Code](https://claude.com/claude-code)（macOS / Windows / Linux 都行）
- [x] 已安裝 Claude in Chrome MCP（[官方說明](https://docs.claude.com/en/docs/claude-code/mcp)）
- [x] Chrome 瀏覽器已登入你要發文的**所有**社群平台
- [x] 你的 FB 個人頁有**至少 20 篇公開貼文**（否則學不出穩定風格）

## 1. 安裝 skill

```bash
git clone https://github.com/Hao0321/claude-skill-social-post.git ~/tmp-social-post

# macOS / Linux
mkdir -p ~/.claude/skills
cp -r ~/tmp-social-post/social-post ~/.claude/skills/social-post

# Windows（PowerShell）
New-Item -Path "$env:USERPROFILE\.claude\skills" -ItemType Directory -Force
Copy-Item -Path "$env:USERPROFILE\tmp-social-post\social-post" -Destination "$env:USERPROFILE\.claude\skills\social-post" -Recurse
```

把 example 檔改名（改名不改內容，之後 Claude 會覆寫）：

```bash
cd ~/.claude/skills/social-post
mv style_profile.example.md style_profile.md
mv content_plan.example.md content_plan.md
```

## 2. 第一次跟 Claude 對話

啟動 Claude Code（`claude` 指令），在專案目錄內跟它說：

```
幫我學 FB 風格
```

Claude 會：
1. 確認 Chrome MCP 可用
2. 問你 FB 個人頁網址（例 `facebook.com/yourname`）
3. 打開 Chrome → 捲動載入 ~20 篇貼文
4. 分析語氣 → 寫進 `style_profile.md`
5. 給你 3 條重點請你驗收

預期時間：5-10 分鐘。

### 踩雷防護

- **Chrome 要是登出狀態** → skill 會停下請你手動登入，不會自動輸入密碼
- **FB DOM 改版** → skill 有 fallback 用 `get_page_text` 切，通常還能跑
- **貼文太少（< 20）** → 用現有的分析，風格 profile 會稍弱但可用

## 3. 排 14 天內容日曆

```
幫我排社群內容日曆
```

Claude 會問：
- 主目標是什麼？（社群成長 / 商業轉換 / KOL 品牌 / 混搭）
- 每週發幾次？

然後寫入 `content_plan.md`。

### 建議

- **剛開始就每週 3-5 篇**，先別每天逼自己
- **三個目標都選**就選「混搭」，Claude 會依優先序排
- **第一輪日曆把它當草稿**，戰績跑出來再 review 調整

## 4. 每日發文

```
今天發一篇
```

Claude 會：
1. 讀 `content_plan.md` 看今天的公式與平台
2. 問你題材（若沒有，依公式提示丟靈感給你）
3. 生成各平台草稿（不是一稿多投）
4. **完整貼出草稿請你確認**
5. 你回「確認」後 → Chrome 自動發佈
6. 回報「✓ 已發到 FB，連結：...」
7. 更新 `content_plan.md` 戰績表

### ⚠️ 硬規則：沒「確認」不發

這是 skill 內建的安全閘。即使你之前說「完全自動」、即使你用 `--dangerously-skip-permissions` 啟動 Claude Code，**每次發佈前 skill 都會要你在對話裡打「確認」兩字**。公開貼文不可逆，這層不能省。

## 5. 回報戰績

發完過幾小時或隔天，跟 Claude 說：
```
剛剛那篇現在 X 讚 / Y 留言 / Z 分享
```

Claude 會把數字追加到 `content_plan.md` 戰績表。

## 6. （選配）自動追蹤流量

用 `mcp__scheduled-tasks` MCP 建排程任務。

### 建立追蹤任務

跟 Claude 說：
```
建立一個每 2 小時的任務，檢查我最新貼文的讚/留言/分享/粉絲，
記進 content_plan.md 戰績備註欄，
顯著變化時通知我
```

Claude 會用 `mcp__scheduled-tasks__create_scheduled_task` 建 cron 任務。

### 預先授權避免權限彈窗

背景 cron 任務會在新 session 跑，會觸發權限彈窗。**提前把必要權限寫進 `.claude/settings.local.json`**：

```json
{
  "permissions": {
    "allow": [
      "mcp__Claude_in_Chrome__tabs_context_mcp",
      "mcp__Claude_in_Chrome__navigate",
      "mcp__Claude_in_Chrome__computer",
      "mcp__Claude_in_Chrome__javascript_tool",
      "mcp__Claude_in_Chrome__get_page_text",
      "mcp__Claude_in_Chrome__find",
      "mcp__scheduled-tasks__list_scheduled_tasks",
      "mcp__scheduled-tasks__update_scheduled_task",
      "Read(<your-skill-path>/**)",
      "Edit(<your-skill-path>/**)",
      "Write(<your-skill-path>/**)",
      "Bash(date *)"
    ]
  }
}
```

## 7. 每 2 週 review

跟 Claude 說：
```
review 一下
```

Claude 會：
1. 讀戰績表
2. 找高表現/低表現的公式
3. 提出下一輪日曆調整建議
4. 把新日曆寫回 `content_plan.md`，舊的搬到「歷史日曆」段

---

## 疑難排解

### Chrome MCP 失效
- 確認 `claude mcp list` 裡有 `Claude_in_Chrome` server
- 重啟 Claude Code

### FB DOM 變了，skill 抓不到貼文
- 用 `get_page_text` fallback 通常還能跑
- 提 issue 或 PR 更新 `references/facebook.md` 的選擇器

### 留言被拆成多則
- FB 留言框 Enter = 送出（不是換行），skill 已處理為單行
- 若你手動改 skill 的留言格式，**不要留 `\n`**

### 要切 Threads 帳號
- Threads 桌面版**沒有帳號切換**
- 要從不同 Threads 帳號發，必須從手機 app 或重登 IG

### 發到錯帳號
- skill 發文前會截圖 compose modal 給你看當前帳號
- 沒截圖到或看不清楚時直接停手問使用者 — 這是安全閘

### 爆款後演算法推下一篇
- skill 有「爆款後 24h 冷卻規則」自動觸發勸退
- 你堅持要發的話 skill 會強制用輕量公式（F2/Mode A），不開新大主題

---

## 下一步

- 用 2 週後跑第一次 review，看哪些公式對你最有效
- 新發現的踩雷 / 公式變體 / 平台細節，更新到對應 `references/*.md` 並 PR 回 repo

---

## 遇到問題 / 想分享結果？

- **GitHub Issues**：[github.com/Hao0321/claude-skill-social-post/issues](https://github.com/Hao0321/claude-skill-social-post/issues)
- **加入 Claude Code 台灣交流討論區（Line 社群）**：[line.me/ti/g2/DPTQR_XE6IYP8c5lBxsbRwsvEUsxI-70p1jWoA](https://line.me/ti/g2/DPTQR_XE6IYP8c5lBxsbRwsvEUsxI-70p1jWoA)
- **作者 FB**：[駱君昊 Hao · facebook.com/lo.jain.hao](https://www.facebook.com/lo.jain.hao)

如果這個 skill 幫到你，回 FB 貼文 tag 一下原作者是最大的鼓勵 🙏
