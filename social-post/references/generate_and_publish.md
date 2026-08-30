# P2 Draft and publish

## Draft context（先少後多）

1. 讀 `voice_quick.md` 與 `current_brief.md`。
2. 必須先跑 `python -B scripts/social_data.py comparables --platform <platform> --content-type <content_type> --surface <surface> --maturity <maturity> --limit 2 --format json`，並在選 hook、版型、長度、關鍵字、語氣、標點與 CTA 時實際使用它帶出的原文與 feature fields。預設只取 2 篇，避免把整庫塞進 context；若結果為空，明示沒有同 cohort 樣本，不臆造成功規則。
   - 平台、maturity、content type、surface 四個 filter 必須都有值；否則 `outcome_comparison_allowed:false`，不可用成效做選擇。
   - 回傳順序只代表最近發布，`performance_ranked:false`；不把第一篇叫冠軍，也不推導通用爆款分數。
3. comparables 的日期、星期、精確分鐘只供提出待驗證候選，不得當生成分數、因果權重或固定黃金時段；同分鐘有高低反例時更不得以時間排名文案。
4. 從 `data/rule_registry.json` 找任務相關規則，只開必要的 `rules/RNN.md`。
5. 從 formula index 找一個目標公式，只開該 formula 檔；不要讀完整公式庫。
6. 草稿階段不讀平台 UI 流程。只有使用者確認要實際發布後，才讀目標平台 reference。
7. 只有重新學 voice／深度仿寫時才讀完整 `style_profile.md` 或使用者明確指定的 voice Skill。

## 發文前三檢查

- 用 structured latest snapshot 判斷前篇 maturity、是否仍成長、最近三篇陌生分發與題材／意圖冷卻；不要從 `content_plan.md` 讀舊績效。
- 確認草稿決策來自同平台／同 maturity／同 content type／同 surface 的 comparables；跨 cohort 只能列差異，不可排成勝負榜。
- 題材、素材、平台與「一稿同步」若已由使用者說明，直接採用，不重問。
- 個人帳號／頻道的內容禁區只讀 `current_brief.md`；通用平台文件不可硬編使用者的私人政策。
- 只有使用者要求實際操作發布才啟用瀏覽器；寫草稿不需要。

## 產稿

1. 先決定這篇唯一主目標：陌生觸及、討論、追更、star、私訊或社群轉化。
2. 選一個 content archetype、一個 hook、一個 CTA；不要把多個公式疊成 dashboard。
3. 使用者明示同步時，只產一份 canonical copy。YouTube 標題可取第一句或另給一行必填標題，但正文不維護第二套。
4. 生成後做 quick QA：
   - 首段 5 秒內讀得懂，沒有多層 meta。
   - 數字都有來源；不把推論寫成事實。
   - 語氣像 `voice_quick.md`，沒有顧問腔／AI 總結腔。
   - 只有一個 CTA；沒有不必要 hashtag、emoji 或外部連結。
   - Reels／Shorts caption 不假裝能補救片內留存。
5. 任一項失敗就先重寫，再交付。

## 確認與發布

1. 把最終 copy 與平台清單完整顯示給使用者。
2. 讀本次目標平台 reference 與 `last_verified`。UI／限制若可能已變，先查官方來源。
3. 取得當前對話的明確確認；若使用者本 session 已授權免逐次確認，依 SKILL.md 執行。
4. X 若在 Hermes Agent 使用結構化 route，另讀 `hermes-tweet.md`。先用 `tweet_explore` 找 catalog route，再顯示完整 endpoint、payload、帳號、side effects 與 reason。每次 `tweet_action` 都要重新確認，不沿用 session 的瀏覽器免問授權。
5. 依序發布；每個平台回報結果與連結。任何平台失敗就停，說明已完成與卡住項目。

## 發布後

- 發布事實用 outcome bundle 寫 `posts.jsonl`；還沒有洞察時可建立 awaiting snapshot，missing 用 `null`。
- X 走 Hermes Tweet 時，把工具實際回傳的 URL 或 post ID 與 route 寫進同一筆 outcome。不從 request 推測成功，也不另建檔案。
- 不更新 `content_plan.md` 的績效 row。新數據只進 structured ledgers。
- 使用者回傳洞察時切 P3；跨篇比較切 P4。

## 沒題材

若使用者真的沒有題材，才依 current brief 提 3 個互斥選項：日常觀察、可展示成果、數據復盤。寧可跳過，不為日曆湊文。
