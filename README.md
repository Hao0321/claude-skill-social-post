# social-post

> 一個 [Claude Code](https://claude.com/claude-code) skill，讓 AI 學會你的 Facebook 講話風格、幫你規劃內容、自動發到 FB / IG / Threads / X。

**原作者**：**駱君昊 (Hao)** · MetaFantasy Co-Founder / 3D Artist / VFX Artist / AIGC 數位創作者

🔗 [Facebook 個人頁](https://www.facebook.com/lo.jain.hao) · [Claude Code 台灣交流討論區 (Line 社群)](https://line.me/ti/g2/DPTQR_XE6IYP8c5lBxsbRwsvEUsxI-70p1jWoA) · [GitHub](https://github.com/Hao0321)

**👉 覺得有用請按 ⭐ Star，加入社群討論更多 AI 應用**

---

## 這個 skill 的起源

2026-04-21 凌晨，我跟 Claude 一起做這個 skill — 學我自己的 FB 語氣、排 14 天內容日曆、然後自動發文。

做完當下我發了第一篇，貼文鉤子是「**這篇 po 文就是這個 skill 自己發的**」。

結果 24 小時內：
- **300+ 讚 / 400+ 留言 / 40+ 分享**（約 4,000 粉絲帳號）
- **+60 追蹤者**
- 留言/讚比超過 1.0 — 因為 CTA「留言我拉你入群」觸發大量入群需求
- Claude Code 台灣社群人數一口氣大爆長

這個 repo 就是把那晚做出來的 skill 開源，給想用同樣方法經營自己社群的人。

---

## 它在幹嘛（給一般人看的版本）

1. **學你語氣** — Claude 打開你的 FB 個人頁，讀你最近 20 篇貼文，萃取你的用字習慣、常用 emoji、「爽啦」「草」這種口語。寫成一個 `style_profile.md`。
2. **排內容日曆** — 依你的目標（擴大社群 / 轉換付費 / 建立品牌）和頻率，用 7 個**小帳號驗證過的 viral 公式**排 14 天每日內容。
3. **每天生成 + 自動發** — 你說「今天發一篇」→ Claude 讀日曆 → 問你題材 → 依你的語氣生草稿 → 你確認 → Chrome 自動發到 FB/IG/Threads/X。
4. **追蹤戰績 + 自動優化** — 每 2 小時查貼文流量，寫進戰績表。每兩週 review，表現好的公式加頻、差的換題材。

## 為什麼 7 個公式對一般人有效

市面上教發文的內容大多是抄名人（100 萬粉）或是付費廣告，一般小帳號抄了沒效。

這 7 個公式是**專門從 < 5K 粉的小創作者驗證資料**歸納出來，包括：

| # | 公式 | 最吃的平台 | 例 |
|---|---|---|---|
| F1 | Day-N 開發日誌 | Threads | 「Day 6 做 XXX，今天卡在⋯⋯明天⋯⋯」連載式累積追蹤 |
| F2 | 截圖先丟再講 | FB / Threads | 演算法看 dwell time，截圖 = 免費 dwell |
| F3 | 實測翻車版 | FB 長文 | 「我用 X 跑 N 天，三件沒人說的事」save 率高 |
| F4 | 社群里程碑 + 投票 | FB | 慶祝+選擇題，留言權重 > 讚 |
| F5 | 工具對打 | X thread | 「A vs B 跑同一任務，結論：⋯⋯」非追蹤者會搜到 |
| F6a | 推廣 + 邀請碼 | FB / IG | 邀請碼製造互惠感 |
| **F6b** | **meta-ship（ship 自己做的東西）** | **FB / IG** | **本 skill 起源的驗證爆款模板** |
| F7 | POV 吐槽 | Threads | 短文 + 回覆率 > 5% 最大推送 |

詳見 [`social-post/references/formulas.md`](social-post/references/formulas.md)。

---

## 5 分鐘 Quickstart

### 需求

- [Claude Code](https://claude.com/claude-code)（macOS / Windows / Linux）
- [Claude in Chrome MCP](https://docs.claude.com/en/docs/claude-code/mcp) 已安裝
- Chrome 已登入你要發文的社群
- FB 個人頁**至少 20 篇公開貼文**（學風格的樣本量）

### 裝

```bash
# 1. clone
git clone https://github.com/Hao0321/claude-skill-social-post.git

# 2. 把 social-post 資料夾複製到你的 skill 路徑
# macOS / Linux:
cp -r claude-skill-social-post/social-post ~/.claude/skills/social-post
# Windows (PowerShell):
Copy-Item -Path "claude-skill-social-post\social-post" -Destination "$env:USERPROFILE\.claude\skills\social-post" -Recurse

# 3. 把 example 檔改名（之後 Claude 會覆寫成你自己的版本）
cd ~/.claude/skills/social-post
mv style_profile.example.md style_profile.md
mv content_plan.example.md content_plan.md
```

### 用

啟動 Claude Code，說：
```
幫我學 FB 風格
```
→ Claude 會問你 FB 網址 → 打開 Chrome 爬 20 篇 → 寫出你的語氣 profile。

```
幫我排社群內容日曆
```
→ 問目標 + 頻率 → 寫 14 天日曆到 `content_plan.md`。

```
今天發一篇
```
→ Claude 讀今天的公式 → 問題材 → 生草稿 → 你回「確認」→ 自動發四平台。

詳細 step-by-step：[`docs/setup.md`](docs/setup.md)

---

## FAQ

**Q: 我不會寫 code，用得起來嗎？**
A: 會安裝 Claude Code 就好。skill 裝一次、用中文跟它對話、都是中文指令。唯一的技術要求是裝 Chrome MCP 那個 MCP server。

**Q: 會不會被 FB 當機器人封鎖？**
A: 不會直接。skill 只是幫你填表單 + 按發佈，速率跟你自己手動一樣。**但**：
- 不要連發很多篇（skill 本身有爆款 24h 冷卻規則）
- 不要一次留言幾百則相同內容（FB 會判 spam）
- skill 發文前一定會要你確認，你看到不對可以喊停

**Q: 跟 Meta 官方 API 比有什麼差？**
A: 官方 API 要申請開發者帳號、審核、token 管理，大多數一般人做不到。這個 skill 用 Chrome MCP 操作瀏覽器，**你登入的帳號能做什麼、skill 就能做什麼**，不需要任何授權申請。

**Q: 爆款公式真的能複製嗎？**
A: F6b 是我本人驗證過的（就是產出這個 repo 那篇貼文）。其他 6 個是歸納自小創作者 retros，不是 100% 保證爆，但至少比抄名人套路的機率高很多。你實際用了戰績會累積在 `content_plan.md`，兩週後讓 skill 幫你 review。

**Q: 我可以改 / 商用嗎？**
A: MIT License，隨便改隨便用隨便商用。只需要保留 LICENSE 檔（標明我是原作者）。

**Q: 有 bug / 踩到新雷 / 想加公式怎麼辦？**
A: 歡迎 issue / PR。特別是 FB DOM 改版、新平台、新公式變體這類。PR 回來我會合併，貢獻者會出現在 GitHub commit 紀錄。

---

## 限制（要知道）

- **FB DOM 常變**，skill 有 fallback 但不是萬無一失
- **IG 要圖**，純文字貼文會自動改 Threads
- **Threads 桌面版沒有帳號切換**，多帳號只能從手機切
- **FB 留言框 Enter = 送出**（skill 會壓成單行避免被拆）
- **公開貼文不可逆**：發佈前 skill 硬規則要你回「確認」，沒有確認字眼不會發
- **需要你自己的 FB 夠多公開貼文**，太少學不出穩定風格

---

## 授權

[MIT License](LICENSE) — 隨便改、隨便用、商用也行。保留 LICENSE 檔即可。

---

## 致謝

這個 skill 是 **駱君昊 (Hao)** 跟 Claude 在一個晚上對話出來的。

F6b 公式（meta-ship 變體）是 co-build 過程意外驗證的——「這篇 po 就是 skill 自己發的」這句懸念創造了 300+ 讚 / 400+ 留言的爆款。

如果你用這個 skill 做出什麼有趣的東西，歡迎 tag 我的 FB：[@lo.jain.hao](https://www.facebook.com/lo.jain.hao)

想聊 AI 應用、skill 開發、社群經營，加 [Claude Code 台灣交流討論區](https://line.me/ti/g2/DPTQR_XE6IYP8c5lBxsbRwsvEUsxI-70p1jWoA) 🚀

---

**⭐ Star this repo if it helped you. 覺得有用請按星，讓更多人看到。**
