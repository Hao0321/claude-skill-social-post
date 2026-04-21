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

## 多帳號踩雷（2026-04 實證）

- **Threads 桌面版沒有帳號切換功能**（只有手機 app 有）。使用者有多個 Threads 帳號時：
  - 若其中一個帳號是「從 FB 自動同步」的（FB 發了會自動鏡像到 Threads），**skill 只發 FB 即可，Threads 會自動跟上**
  - 若需要從不同 Threads 帳號發，**停下告知使用者必須在手機或用 IG 切換後再回頭**，不要嘗試在桌面版切帳號
- 發文前先截圖 compose modal 確認當前帳號名稱，避免誤發
