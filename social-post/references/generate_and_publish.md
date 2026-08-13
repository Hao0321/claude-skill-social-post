# P2 Draft and publish

## Draft context（先少後多）

1. 讀 `voice_quick.md` 與 `current_brief.md`。
2. 從 `data/rule_registry.json` 找任務相關規則，只開必要的 `rules/RNN.md`。
3. 從 formula index 找一個目標公式，只開該 formula 檔；不要讀完整公式庫。
4. 草稿階段不讀平台 UI 流程。只有使用者確認要實際發布後，才讀目標平台 reference。
5. 只有重新學 voice／深度仿寫時才讀完整 `style_profile.md` 或 `hao-voice`。

## 發文前三檢查

- 用 structured latest snapshot 判斷前篇 maturity、是否仍成長、最近三篇陌生分發與題材／意圖冷卻；不要從 `content_plan.md` 讀舊績效。
- 題材、素材、平台與「一稿同步」若已由使用者說明，直接採用，不重問。
- 純 AI 短劇排除 YouTube；實拍 Shorts 可同步 YouTube。
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
2. 取得當前對話的明確確認；若使用者本 session 已授權免逐次確認，依 SKILL.md 執行。
3. 讀本次目標平台 reference 與 `last_verified`。UI／限制若可能已變，先查官方來源。
4. 依序發布；每個平台回報結果與連結。任何平台失敗就停，說明已完成與卡住項目。

## 發布後

- 發布事實用 outcome bundle 寫 `posts.jsonl`；還沒有洞察時可建立 awaiting snapshot，missing 用 `null`。
- 不更新 `content_plan.md` 的績效 row。新數據只進 structured ledgers。
- 使用者回傳洞察時切 P3；跨篇比較切 P4。

## 沒題材

若使用者真的沒有題材，才依 current brief 提 3 個互斥選項：日常觀察、可展示成果、數據復盤。寧可跳過，不為日曆湊文。
