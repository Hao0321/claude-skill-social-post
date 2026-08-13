# Threads 發文

> last_verified: 2026-08-13
> verification_scope: Meta 官方基本格式；桌面 UI selector 是本機操作性觀察，實際操作前重驗。
> official_source: https://about.fb.com/news/2023/07/introducing-threads-new-app-text-sharing/

## 參數

- 一般貼文 500 字元，可含連結、圖片與影片；超過就切串。
- 純文字可發；登入與帳號關係依當前產品狀態，不在文案層假設。
- Topic tag、編輯、排程與多帳號 UI 可能變；有關鍵需求時先查當前官方說明／畫面。
- 排版無 Markdown。Hao 的短文優先一段、短句、單一立場或觀察。

## 文案路由

- 日常用 F7／Mode A；立場文才考慮 F19。只讀對應 formula，不把 FB 四段式直接搬過來。
- 第一句必須獨立成立；串文在句子邊界切，每則都要讓讀者知道上一則在講什麼。
- 不把「keyword、轉發、對立」寫成保證流量的公式。私人實證與規則強度從 structured experiments／R19 讀。
- 使用者若要一稿同步，就維持 canonical copy；只有超過 Threads 格式才做機械切串，不另改論點。

## YouTube 導流

- 正文優先維持原生可讀；若使用者選擇不在正文放外部連結，YT URL 可放單一作者回覆。
- 是否導流、何時補 link 與下游成效要建立 experiment；不沿用舊比例或權重預測。
- 歸因看 YouTube Studio 的外部來源；結果寫回 social-post snapshot／experiment。

## UI 流程

1. 開啟 `https://www.threads.com/`，先確認登入與當前帳號；遇 `/login` 停下讓使用者手動登入。
2. 找 New thread／建立按鈕，開 compose。
3. 輸入第一則；需要串文才按 add to thread 並逐則輸入。
4. 發布前再次核對帳號、全文、媒體與可見範圍。
5. 按 Post，等待畫面出現新貼文後才判定成功。

## 安全與 fallback

- 長串先在對話完整預覽；UI 中途失敗可能整串遺失。
- 找不到 compose／帳號切換／發布鈕時先讀當前互動畫面，不用舊 selector 盲點。
- 不自動輸入密碼、不大量回覆、不因登入另一個 Instagram 就假設 Threads 帳號正確。
- 取連結時從個人頁最新貼文取得 `/@.../post/...` permalink，拿不到就回報已發布但連結待生成。
