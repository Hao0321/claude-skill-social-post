# 共創 Social Post

Social Post 開放所有人提交貢獻，Hao 保留唯一的最高管理權與最終採納權。你可以先試用、回報、提出設計，再從一個小改動開始；透過 fork → PR 參與，不需要 collaborator 邀請。

專案方向與權限見 [GOVERNANCE.md](GOVERNANCE.md)，優先任務見 [ROADMAP.md](ROADMAP.md)。

## 選一個你擅長的模組

| 方向 | 入口 | 合適的貢獻 |
|---|---|---|
| 介面與導覽 | [工作台](social-post/references/workbench.md)、social-post/workbench/、workbench_test.py | P／A-B-C／F 的區分、無表情符號設計、可存取性、私人草稿與匯入流程 |
| 文案、語氣與版型 | [撰稿流程](social-post/references/generate_and_publish.md)、[公開語氣卡](social-post/voice_quick.md) | Mode A／B／C、長度、換行、標點、黑底白字、未校準提示 |
| 成效與學習 | [資料工具](social-post/scripts/social_data.py)、[成效流程](social-post/references/outcome-workflow.md) | 日期／星期／分鐘、snapshot、maturity、完整欄位、可重現分析 |
| 平台與演算法 | [FB](social-post/references/facebook.md)、[IG](social-post/references/instagram.md)、[Threads](social-post/references/threads.md)、[X](social-post/references/x.md)、[YouTube](social-post/references/youtube.md) | 官方來源、查證日期、平台適配與有界假設 |
| 留言與瀏覽器 | [留言流程](social-post/references/comment-operations.md)、[adapter](social-post/references/chrome-comment-adapter.md) | reader、離線 fixture、父留言識別、異常對帳 |
| ChatGPT Chat | [Chat Skill](chatgpt-socialpost/SKILL.md) | 聊天端格式遵循、範本、聲線校準與能力說明 |
| 測試與上手 | [離線測試](social-post/scripts/self_test.py)、本指南 | 跨環境驗證、匿名重現、文件與安裝體驗 |

這些是現有責任邊界，不需要先大搬檔案。成效事實由 JSONL store 管理；adapter 接平台，ledger 管核准與送出狀態，避免各模組重複維護相同規則。

## 從提案到合併

1. 小修可直接開 PR；改架構、資料契約或 live 行為，先用 Issue 描述使用情境與驗收方式。
2. Fork 或建立自己的工作分支。每份 PR 聚焦一個可驗證的改善。
3. 用 fictional 資料重現，保存改前／改後輸出；測試能接受正確情境，也能拒絕原本的錯誤情境。
4. 跑適用驗證，填 PR 範本，說明哪些結果未測。AI 協助生成的內容也由提交者核對。
5. 回應審查，維護者核准後合併。合併到 main 是候選更新；正式 tag／Release 另由 Hao 驗收。

## 本機開發

需要 Python 3.10+ 與 Node.js 22；CI 測 Python 3.10、3.13。從 repo 根目錄執行：

~~~bash
git clone https://github.com/Hao0321/claude-skill-social-post.git
cd claude-skill-social-post
git switch -c feat/your-improvement
python tools/check_public_contribution.py
python -m unittest discover -s tools -p "test_*.py"
python social-post/scripts/social_data.py validate
python social-post/scripts/social_data.py coverage
python social-post/scripts/self_test.py
python social-post/scripts/workbench_test.py
node social-post/scripts/workbench_architecture_test.mjs
~~~

self_test.py 包含既有資料、同步隱私、留言契約及 JavaScript 回歸測試。測試只用本機匿名 fixture，不操作社群帳號。公開版沒有私人 canonical capability ledger，因此部分私人校準明示為不適用，公開 projection 的驗證不等於 live 驗收。

工作台額外測試使用隔離的 fictional 資料。真實瀏覽器導覽可用 workbench_browser_test.mjs 指定 Python、已安裝 Playwright 與私有輸出目錄；不要把 renderer 截圖、任務下載或 receipts 提交至公開 repo。介面不得以假 AI 結果或本機測試宣稱已接通生成／社群送出。

文件修正先檢查連結與語義，CI 仍跑公開檢查。改資料／文案分析補相應重現案例；改留言 adapter 保留既有 guard、來源綁定與不明結果停損。不要為了測試變綠而放寬核准、去重、capability 或隱私規則。

## 可公開的資料

公開內容限通用程式、契約、官方來源、可授權的通用知識及明示為 fictional 的範例。

- 個人 style_profile.md、content_plan.md、drafts/、.rd/、原始洞察圖與真實 JSONL 留在本機。
- voice_quick.md、current_brief.md 是公開範本；自己的設定放安裝副本，不覆蓋公開範本。
- PR、Issue、Discussion、CI log、影片或附件都不能放帳號登入資訊、真實作者／留言、私人貼文、個人路徑與憑證。
- 統計數字與文字可能識別原作者；只移除姓名不等於已匿名。重現預設重建 fictional 資料。
- 隱私檢查會拒絕私有路徑、JSONL、原始媒體、二進位附件及常見憑證模式。它不會辨識所有私人資訊，審查仍須核對文字。

不要提交真實資料來證明工具有用。要分享真實學習成果，先抽象成通用假設，以可重播的 fictional fixture 驗證；流量效果另記未測或經授權的研究，不從單一案例宣稱因果。

## 評估改善

一份有用的證據包含：

- 同一輸入、環境與量尺下的改前／改後行為；
- 具體改善，例如保留原文標點、正確區分發文與截圖時間，或拒絕錯誤父留言；
- 成本與限制，例如新增依賴、額外 context、未驗證平台或相容性；
- 對應正／負情境與來源授權。

Cleanup 與 R&D 是維護者的進階審計工具：Cleanup 提供唯讀量測，R&D 決定採納與發布。貢獻者不需要安裝 Hao 的私人 Skill 才能提交 PR；repo 內的公開測試就是基本入口。

## 授權與溝通

提交內容須由你擁有或有權以本專案的 [MIT License](LICENSE) 貢獻。第三方程式、素材與知識保留來源及所需授權；不提交來源不明內容。

討論聚焦可重現的行為與設計，尊重不同程度的貢獻者。發現隱私或憑證洩漏時，先私下通知 Hao 或使用 repository 提供的私密安全回報入口，公開區只描述問題類型。
