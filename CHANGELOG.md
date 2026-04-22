# Changelog

## v0.2 — 2026-04-22

12 小時後第一次重大更新。基於 Day 2 實戰 flop + FB 洞察報告數據做的規則迭代。

### Added
- **一天一篇鐵則**（`SKILL.md`）— 24 小時內最多 1 篇，不受前一篇好壞影響。Flop 當天正確動作是回留言，不是多發。
- **爆款節奏基本原則**（`SKILL.md`）— 日常 20-40 讚 × N 天 → 偶爾一顆爆款 → 回到日常。每月 1-2 個 F6b 就夠。
- **爆款後 Day 2 三大禁忌**（`SKILL.md`）— Day 2 flop 實證的三個錯誤：連續同公式、炫 Day 1 數字、爆款時間 +24h 不是黃金時段。
- **基於實戰校準的 benchmark 表**（`SKILL.md`）— 4K 粉帳號的及格 / 優秀 / 爆款 / mega-viral 四級指標。
- **FB 原生排程機制**（`references/facebook.md`）— 用 FB 內建排程取代 cron。
- **留言框 `\n` = 送出的踩雷**（`references/facebook.md`）— 留言框 Enter 是送出不是換行，會被拆成多則。

### Changed
- F6b 驗證數據從「300+/400+/40+」升級到**實戰完整數據**：瀏覽者 72,323、互動率 15.3%、讚 358、留言 443、分享 73、追蹤者 +167、Line 社群 +700。
- `references/formulas.md` F6b 段新增反直覺觀察：連結點擊率極低（72K 讀者中只 7 人點外部連結）→ 社群成長主路徑是**留言 +1 → 作者私訊拉人**。

### Lessons learned（可複製給其他 4K 粉帳號的心得）

1. **爆款觀眾 97% 是非追蹤者** — F6b 觸發演算法廣推，不靠既有粉絲。
2. **外部連結點擊極低** — 讀者不走出 FB。CTA 要放 FB 站內行動（留言、私訊、精選留言連結），不是依賴外部 funnel。
3. **真正的 KPI 是社群轉化** — 讚/留言只是中間指標。社群人數增長才是終極指標。
4. **一篇 mega-viral > 七篇日常** — 不要為了 posting frequency 而硬發。

---

## v0.1 — 2026-04-21

初版發布。

### Added
- Skill 三階段工作流（學風格 / 內容規劃 / 生成+發佈）
- 7 個 viral 公式（F1-F7，含 F6b meta-ship 爆款模板）
- 14 天內容日曆範本
- Claude in Chrome 操作指南（FB / IG / Threads / X）
- 安全閘：發佈前必須使用者明確「確認」字眼
- 範例檔：`style_profile.example.md` + `content_plan.example.md`（虛構角色林思萱 Vivi）

### Validation
- F6b meta-ship 公式首次發佈即獲 300+ 讚 / 400+ 留言 / 40+ 分享（驗證當晚）
