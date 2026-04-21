# Instagram 發文

## 參數

- 字數：2,200 字上限，**前 125 字後被折疊**，重點前置
- Hashtag：5-15 個甜蜜點（上限 30，太多像 spam）
- **必須有圖/影片**，純文字發不了
- 連結：內文不可點（只有 bio 可點），導流用 link-in-bio 或 Threads
- 排版：換行、emoji，**無 markdown**；中文空行常被吃

## 生成調性

- 前 125 字當鉤子
- hashtag 放文末空行隔開
- 比 FB 更視覺化、更短

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
