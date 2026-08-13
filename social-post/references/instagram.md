# Instagram 發文

> last_verified: 2026-08-13
> verification_scope: 官方 carousel／hashtag 基本能力；caption 折疊與桌面 UI 是操作性觀察，發布前以當前畫面為準。
> official_sources: https://www.facebook.com/help/269314186824048/ ; https://www.facebook.com/help/351460621611097/

## 參數

- 字數：沿用 2,200 字操作 guard；折疊位置會依介面變動，重點一律前置
- Hashtag：內部策略用 **2-5 個高度相關標籤**；官方目前允許 caption／留言放 hashtag，硬上限與產品行為仍可能調整
- **必須有圖/影片**，純文字發不了
- 連結：內文不可點（只有 bio 可點），導流用 link-in-bio 或 Threads
- 排版：換行、emoji，**無 markdown**；中文空行常被吃

## IG → YouTube 導流（cross-ref）

IG 導 YT 三條路（IG 是導流平台優先序 **#2**，次於 Threads）：
1. **link-in-bio** 放當期 YT 影片
2. **限動 link sticker**
3. caption 導去 **Threads**，再走 Threads→YT（主力）

⚠️ IG 內文連結不可點，**別在 caption 塞裸 URL**。完整協定見 [`youtube.md`](youtube.md)。

## 生成調性

- 前 125 字當鉤子
- hashtag 放文末空行隔開
- 比 FB 更視覺化、更短

## Hao AI 短劇 Reel 路由

- 私人實測只從 `data/*.jsonl` 與 `scripts/social_data.py summary --series <series>` 讀；本檔不保存快照數字。
- 同系列不同集、不同 maturity、不同首幀與 caption 不是乾淨 A/B。先列 confound，再看 R43 的 standalone premise 假設。
- Caption 可提供題材詞與單一 CTA，但全球陌生分發仍優先看影片留存、略過與推薦來源。
- 純 AI 短劇只發布 IG＋FB，不發 YouTube；實拍 Shorts 不受此限制。
- 介面若出現廣告受眾字樣，在是否 boost 確認前，不把人口輪廓宣稱為純自然 TAM。

## 沒圖就停

使用者沒圖時告知選項：(A) 給我圖 (B) 跳過 IG (C) 改 Threads。**不要自己決定。**

## UI 流程

1. `navigate` → `https://www.instagram.com/`，等 2 秒
2. `find` "Create new post button in left sidebar" → `left_click`（若出子選單選「貼文」，不是 Story/Reels/Live）
3. 告知使用者「請把圖拖進剛開的視窗或用『從電腦選擇』，傳完回我『圖已上傳』」，**不要自動化檔案對話框**
4. `find` "Next button" → `left_click`（跳過裁切）
5. 再一次 `find` "Next button" → `left_click`（跳過濾鏡）
6. `find` "caption textarea" → `left_click` 焦點 → `type` 內容（含 hashtag）
7. `find` "Share button" → `left_click` → `wait 5`
8. 等 dialog 關回到 feed

## 取連結

```javascript
(() => {
  const a = document.querySelector('a[href*="/p/"]');
  return a ? a.href : null;
})()
```
先 `navigate` 到 `instagram.com/<使用者帳號>/`，再跑上面 JS 取最新一篇。

## Fallback

- 找不到 Create 按鈕：可能帳號被限、或藏進 `...` 選單。screenshot 問使用者
- Next 灰色：圖還沒傳好 / 格式不支援（HEIC 有時 fail），請換格式
- Share 後卡住：等 10 秒，仍無動靜停手告知

## 速率

- 發完一篇至少 `wait 30` 秒再發下一篇
- 不自動 like/follow/留言
- 只支援 feed 貼文；Reels/Story 告知使用者自己發
