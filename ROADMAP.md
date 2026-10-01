# 共創路線圖

這是提案與分工入口，不是已完成能力清單。執行狀態以 Issue／PR、測試與 [公開 capability projection](social-post/comment-capabilities.json) 為準。

## 第一輪：容易切入、能驗證的改善

| 任務 | 建議夥伴 | 驗收方式 |
|---|---|---|
| ChatGPT Chat 格式一致性 | 文案／prompt | fictional 樣本測 Mode C、指定長度、換行、標點；區分安裝與實際套用 |
| 黑底白字與短文範本 | 創作者／設計 | 保存觀測行數、對齊、標點與長度；以同版型例子評估，避免宣稱單一版型保證流量 |
| 發文時間與資料精度 | Python／資料 | 正確記日期、星期、HH:mm、timezone；拒絕把手機截圖時間當發布時間 |
| 更清楚的首次安裝體驗 | 文件／QA | 全新 clone 可跑公開測試；私人範本與 Chat／Codex 能力界線清楚 |
| 平台 reference 查證 | 研究／內容策略 | 官方一手來源、查證日期、適用平台及未證實假設完整 |

## 第二輪：模組強化

| 任務 | 驗收方式 |
|---|---|
| 成效 schema、comparables 與新 analytics | 不遺漏新欄位；null、rounded、maturity、platform scope 可重播 |
| 學習品質評估 | 改前／改後用相同輸入；沒有私人聲線時如實標記未校準 |
| 平台 reader 與 UI 改版相容性 | 離線負控制拒絕錯誤父層、延遲載入、截斷、帳號與 URL 漂移 |
| 例外／重啟後對帳 | 未知結果停止；保留原 attempt；不能因重啟重送 |
| 效率與依賴 | 同任務比較延遲、context 與維護成本，量測不足不寫成已改善 |

## 後續候選

完整 FB／IG／Threads live 掃描、批次回覆與跨環境 parity 須分平台驗收。公開協作先做 synthetic fixture；需要真實帳號的驗證由帳號所有者另行授權，證據留在私人側，公開只投影可公開的結果。

X 開源演算法可以提供版本化參考與假設，不把預測權重直接套成 FB／IG 的流量公式。跨平台策略須用各自資料驗證。

## 邀請夥伴

可先私下分享這段，再附 repo 連結；這份範本不代表已發送邀請：

> 我想把 Social Post 開放共創，邀請我認可的夥伴一起強化。
> 工具會持續開源，從文案格式、成效學習、平台適配到留言操作，都有可以一起研究的方向。
> 先選一個你擅長的小任務，做出能驗證的改善，我們再一起審查和迭代。
> 你的私人資料與個人風格留在本機。想加入，給我 GitHub 帳號和你想參與的方向。

正式任務用 [Issue 範本](https://github.com/Hao0321/claude-skill-social-post/issues/new/choose) 建立，設計討論放 [Discussions](https://github.com/Hao0321/claude-skill-social-post/discussions)；採納流程見 [CONTRIBUTING.md](CONTRIBUTING.md)。
