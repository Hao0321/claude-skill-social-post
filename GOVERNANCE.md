# 共創治理

Social Post 維持 [MIT 開源](LICENSE)，採用與 Video Autopilot、Editkin 相同的「人人可提交，Hao 採納」方式。Hao 保留唯一最高管理權；任何人可以試用、fork、開 Issue 與 PR。受認可的夥伴可參與開發和審查，邀請不代表授予管理權。

## 角色

| 角色 | 責任 | GitHub 權限 |
|---|---|---|
| 貢獻者 | 提案、回報、提交 PR、提供匿名重現 | 不需要 repository 寫入權限 |
| 受邀夥伴 | 依約定模組開發、回應問題、協助審查 | 預設 fork → PR；持續開發需要 Write 時由 Hao 另行指定 |
| 模組 reviewer | 檢查該方向的行為、證據與回歸 | 提供 review；不取代 Hao 的必要核准 |
| Hao／release owner | 定方向、核准採納、維護權限、驗收正式發布 | repository owner |

所有檔案的唯一必要 code owner 為 @Hao0321，包含 CODEOWNERS 本身。加入夥伴或擔任 reviewer，不會取得管理權、所有權或主分支繞過權限。

本 repo 是個人帳號 repository，collaborator 會取得寫入權限，不能把它說成只可審稿。只想提案／審閱的人可先走 fork／PR；若日後需要 triage、分團隊與更細權限，再評估 GitHub Organization，另行決定移轉。

## 審查與發布

預設流程：提案 → 工作分支／fork → PR → CI → code owner 核准 → 合併 → 候選驗收 → 正式發布。

main 的目標保護：

- 合併前需要一份核准審查，且符合 CODEOWNERS；
- 新 commit 使舊核准失效，未解決的 review conversation 阻擋合併；
- 最後推送者不能核准自己的最新變更；
- 兩個 Python 版本的 Public checks 都通過；
- 不允許 force push 或刪除 main。

GitHub 遠端設定才是實際執行規則；這份文件和 CODEOWNERS 本身不會自動啟用 branch protection。初期 owner 保留 GitHub admin bypass，以便啟動與維護 CI；例外應附可查證的理由，不提供給一般 collaborator。

所有 PR 都須 Hao 的 code owner 核准；模組夥伴作補充 reviewer。即使 reviewer 通過或 CI 全綠，也不自動合併、不自動發布。v* 正式版本標籤的建立、更新、刪除限定 Hao0321 繞過者。

個人 repository 的 Write 協作者可以管理 Releases。main 與 tag 保護不能完全禁止他們改 Release 說明或資產；若要維持所有發布操作只由 Hao 控制，使用 fork／PR 模式即可，不授予 Write。未來增加 Write、admin 或移轉所有權均須由 Hao 明確決定。

main 可持續接收通過審查的候選改善。tag／Release 需要另驗能力與交付狀態；離線 fixture 綠燈不代表 Meta live 回覆、完整掃描或私人資料同步已完成。

## 採納與分歧

改動以使用者利益、可重現證據、維護成本、隱私與既有契約判斷。若兩種方案都有價值，先用同一任務做小型比較；無法裁決時由 Hao 定案並在 Issue／PR 留下理由。

模組 owner 接受任務不等於可以變更別人的資料來源。私人成效與個人聲線不放公開 repo，也不因 collaborator 身分自動取得存取。

## 加入與退出

任何人直接 fork 並提交一份小 PR，依實際貢獻認識彼此。Hao 可邀請認可的夥伴參與特定方向，先確認 GitHub 帳號與第一個小任務；只有需要 repo 內工作分支、且 Hao 明確指定 Write 時才發送 collaborator 邀請。

退出時取消後續權限與 reviewer 指派，已合併貢獻仍依 MIT 保留版本歷史與署名。

GitHub 權限說明：[個人 repository 協作權限](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/repository-access-and-collaboration/permission-levels-for-a-personal-account-repository)、[Code owners](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners)、[Branch protection](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)。
