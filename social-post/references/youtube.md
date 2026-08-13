# Social → YouTube bridge

> last_verified: 2026-08-13  
> verification_scope: Hao 的內容／風險政策與跨平台資料路由；YouTube UI／政策數字不在本檔維護。  
> canonical_outcomes: `data/*.jsonl`

## Hao 的發布邊界

- 純 AI 短劇不發 YouTube。這是 Hao 根據頻道曾被拔除營利、申訴後恢復的帳號實務決策，不用一般平台建議覆寫。
- YouTube 保留給本人教學、製程、評論，以及戰鬥陀螺等非 AI 實拍 Shorts。
- 若題材或 AI 使用程度不明，不自動把它歸類為可上 YouTube；先看使用者當輪定義。

## 跨平台導流

- Social 正文先對當地平台成立，不把整篇寫成「去別站看」。
- 使用者鎖定正文不放連結時，URL 只放單一作者留言、IG bio 或限時動態 link sticker。
- 使用者要求一稿同步 IG／FB／YT Shorts 時，正文維持一份；YouTube 必填標題可從第一句抽取。
- 不大量貼重複 link、不 DM 洗連結、不用推測的演算法權重保證導流。

## 分工

| 問題 | Canonical owner |
|---|---|
| 影片題材、title／thumbnail、留存診斷 | `yt-algorithm-mastery`／影片專門 skill |
| Social copy、CTA、跨平台發布 | `social-post` P2 |
| 發布後觀看、來源、留存、訂閱與轉化 | `social-post` structured ledgers |
| 跨篇假設與下一輪測試 | `data/experiments.jsonl` |

## 量測

1. 同一內容跨平台共用 `post_id`，各平台建立自己的 snapshot。
2. YouTube 的觀看、engaged views、停留觀看、流量來源、訂閱與 retention 不互相代換；沒有就存 `null`。
3. Social 導流效果用可辨識的外部來源與相近 maturity 比較；同時改 title、影片、發布時間與 social copy 時要列 confound。
4. 最新數字只跑 summary，不抄回本檔或 `content_plan.md`。

## 發布前檢查

- 這支內容符合 Hao 的 YouTube 邊界。
- 素材與版權可發布；不是把純 AI 短劇偷換成「Shorts」就繞過政策。
- canonical copy、YT 標題與唯一 CTA 已確認。
- 發布後已準備 post identity；洞察尚未生成就建 awaiting snapshot，不填假 0。
