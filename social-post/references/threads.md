# Threads 發文

## 參數

- 字數：500 字（超過切成串）
- Hashtag：僅支援**一個**主 topic tag，`#xxx` 純文字不變連結
- **純文字 OK**，無需圖
- 連結：自動變可點並抓預覽
- 排版：換行、emoji，**無 markdown**
- 綁定：需先登入 IG

## 生成調性

- 口語、短句、能梗就梗，像「群組聊天的音量」
- 比 FB 鬆、比 X 有呼吸感
- > 500 字就切串：第一則放鉤子+主觀點，後續補細節，**在句子邊界切**

## UI 流程

1. `navigate` → `https://www.threads.com/`，等 2 秒
2. **先檢查是否被導向 `/login`**（2026-04 實證：即使 IG 別處登過，Threads 仍可能要求重登）。URL 或 title 含 `login` → 停手告知使用者手動登入，**不要自動輸入密碼**（系統硬規則）
3. 登入狀態 OK 後，`find` "compose box 有什麼新鮮事" 或 "New thread button" 或 "建立" → `left_click`
4. Modal 開後 `find` "thread compose textarea" → `left_click` 焦點 → `type` 內容
5. 分串：打完第一則 → `find` "add to thread button or plus icon" → `left_click` → type 下一則；重複
6. `find` "發佈 Post button in compose dialog" → `left_click` → `wait 3`

## 取連結

```javascript
(() => {
  const a = document.querySelector('a[href*="/@"][href*="/post/"]');
  return a ? a.href : null;
})()
```
先 `navigate` 到 `threads.com/@<使用者帳號>`。

## Fallback

- 找不到 compose 按鈕：試 `computer` action=`key`, text=`"n"`（焦點在頁面非輸入框才有效）
- type 無效：`javascript_tool` 操作 contenteditable
- 發完沒動：等 5 秒，仍無就 screenshot 問使用者

## 重要：串是一次 commit

**長串中途失敗，整串遺失，沒有草稿**。打長串前先在 chat 把每則給使用者 **逐則預覽確認**，再開始操作 UI。

## 速率

- 兩篇間 `wait 10` 秒以上

## Thread 演算法核心差異（vs FB，v0.8 升級）

### 與 FB 演算法 3 大差異

| 維度 | FB 2026 | **Thread 2026** |
|---|---|---|
| 最強信號 | 私訊分享（Messenger）| **轉發（repost）** = identity signal |
| 觸發機制 | dwell time + 互動 + 私訊 | **keyword detection + 立場分布** |
| 內容偏好 | 長文 + 多媒體 + meta hook | **短文 + 對立立場 + 純文字** |
| viral 主路徑 | 鐵粉 → 跨粉絲圈 | **keyword match → 同 ideology 圈廣推** |

### ⚠️ 跨平台公式禁用清單（v0.8.2，2026-05-16 F4 in Thread 反面實證）

**Thread 只能用 F19 / F7 原生公式**。其他公式直接搬 = die。

| 公式 | 設計平台 | Thread 適配 | 為什麼 |
|---|---|---|---|
| F1 Day-N 日誌 | Threads | ✅ 原生 | 連載式 |
| F4 社群里程碑 | FB | ❌ | **無對立 = 無轉發**（2026-05-16 實證：3786 里程碑 8K 觸及 / 轉發 2）|
| F6b 純血 hype | FB | ❌ | ！！！太多 + 4 段太長 |
| F14 演講濃縮 | FB | ❌ | 長文格式不符 |
| F15 mini | FB | ❌ | 3 段格式不符 |
| F16 精選彙整 | FB | ❌ | bullet list 不符 |
| F18 AIGC Reels | FB+IG | ⚠️ | Reels 可，純圖不行 |
| **F19 立場宣言** | **Thread** | ✅ | **核心 Thread 公式** |
| F7 POV 吐槽 | Threads | ✅ | 短梗 + 高互動 |

→ Thread 只玩兩個公式：**F19 立場宣言**（大砲，月 2-4 篇）+ **F7 POV 吐槽**（日常，週 2-3 篇）。

### ⚠️ Thread 排版鐵則（v0.8.1 從 3 篇真實爆款反向工程）

**核心差異：Thread 不分段**，連續逗號流。

| 維度 | FB F6b | **Thread F19** |
|---|---|---|
| 段落數 | 4 段 | **1 段** |
| 空行 | 段間必空行 | **無空行不換行** |
| sentence 分隔 | 段落分 | **逗號 + 「！」** |
| ！級別 | ！！！3 個 | **！1-2 個** |
| 字數 | 200-400 | **60-150** |

**v0.8 第一版誤把 F19 寫成 3 段 = FB 思維帶過來**。v0.8.1 修正：F19 是 1 段不換行的連續逗號流。

### Thread 高 viral keyword 池（2025-2026 實證）

熱門對立 keyword 配對（觸發演算法主動推）：
- 「免費」vs「付費」/「割韭菜」
- 「賺錢」vs「興趣」/「沒差」
- 「公開分享」vs「藏私」
- 「真的」vs「假的」/「TM」
- 「幹翻」/「幹掉」（攻擊性動詞）
- 「韭菜」/「黑粉」/「炒作」

**Hook 必含 ≥ 2 個熱門 keyword + 1 個對立 framing**。

### 實證：hao0321_studio Thread 400 → 10K 粉一週爆款專案（2025-07-08~13）

3 篇都用同公式（F19 Threads 立場宣言型）：

| 日期 | 瀏覽 | 讚 | 留言 | 轉發 | 分享 | 公式核心 |
|---|---|---|---|---|---|---|
| 25/7/8 | **26 萬** | 2,741 | 314 | **76** | 316 | 「我不靠 AI 課程賺錢...來幹掉所有付費課程」|
| 25/7/9 | 6.9 萬 | 916 | 90 | 10 | 34 | 「我的 AI 教學都是免費的，但我不會教你怎麼賺錢...」|
| 25/7/13 | 12.7 萬 | 1,194 | 90 | **12** | 45 | 「最近黑粉都安靜了很多，我做免費 AI 教學就 TM 做真的！」|

**3 篇共通**：
- **敵人 / 英雄敘事**（韭菜販 / 黑粉 vs 我）
- **TM 級用詞 + 攻擊性動詞**（幹翻 / 幹掉）
- **純粹動機 framing**（興趣 / 沒差 / 不為錢）
- **無 CTA 無連結**（純表態）
- **3-5 句完事**（< 200 字）

**戰績**：帳號 400 粉 **→ 一週內破 1 萬**（+9,600 / 7 天 = 1,371 粉 / 天）。

詳見 `formulas.md` F19 公式 + `case_studies.md` Case 11。

## 多帳號踩雷（2026-04 實證）

- **Threads 桌面版沒有帳號切換功能**（只有手機 app 有）。使用者有多個 Threads 帳號時：
  - 若其中一個帳號是「從 FB 自動同步」的（FB 發了會自動鏡像到 Threads），**skill 只發 FB 即可，Threads 會自動跟上**
  - 若需要從不同 Threads 帳號發，**停下告知使用者必須在手機或用 IG 切換後再回頭**，不要嘗試在桌面版切帳號
- 發文前先截圖 compose modal 確認當前帳號名稱，避免誤發
