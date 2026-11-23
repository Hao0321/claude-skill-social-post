# P2 Draft and publish

## Draft context（先少後多）

1. 讀 `voice_quick.md` 與 `current_brief.md`。
2. 必須先跑 `python -B scripts/social_data.py comparables --platform <platform> --content-type <content_type> --surface <surface> --limit 2 --format json`，並在選 hook、版型、長度、關鍵字、語氣、標點與 CTA 時實際使用它帶出的原文與 feature fields。預設只取 2 篇，避免把整庫塞進 context；若結果為空，明示沒有同 cohort 樣本，不臆造成功規則。
   - 平台、content type、surface 三個 filter 必須都有值；否則 `outcome_comparison_allowed:false`，不可用成效做選擇。
   - 回傳順序只代表最近發布，`performance_ranked:false`；不把第一篇叫冠軍，也不推導通用爆款分數。
3. comparables 的日期、星期、精確分鐘只供提出待驗證候選，不得當生成分數、因果權重或固定黃金時段；同分鐘有高低反例時更不得以時間排名文案。
4. 從 `data/rule_registry.json` 找任務相關規則，只開必要的 `rules/RNN.md`。
5. 從 formula index 找一個目標公式，只開該 formula 檔；不要讀完整公式庫。
6. X 草稿另讀 `x.md` 的演算法邊界與 Social Post 使用方式；草稿階段不讀平台 UI 流程。只有使用者確認要實際發布後，才核對目標平台的 UI 與限制。
7. 只有重新學 voice／深度仿寫時才讀完整 `style_profile.md` 或使用者明確指定的 voice Skill。

## ChatGPT Chat／缺本機資料時

- ChatGPT Chat 可用 Skill 時仍走 P2，但先辨認實際可讀到的是私人安裝版，還是只有 GitHub 公開範本。公開 `voice_quick.md` 的待填欄位不是使用者語氣；不得聲稱「已照你的格式」或以通用 Mode C 定義代替真實樣本。
- 若沒有 shell，不能假裝執行 `social_data.py comparables`。改讀當前可存取的私人 quick card、對應 `style_profile.md` 段落及使用者提供的原文／截圖；以同平台、同 surface、同意圖的樣本作質性對照，明示未做成效排序。若連私人樣本都不可讀，先索取一篇原文或請使用者在 ChatGPT 明確選取可用的私人 Skill／專案來源；最多交付標成「未校準」的初稿，不把它當可直接發佈的作者個人版。
- 有 shell 但 exact cohort 回傳 0 篇，也不能跨用其他 surface 的長度或時間做硬規則。可借相近樣本的語氣與節奏，成效與字數只列待測假設。
- 同一篇修改時，保留使用者已刪掉的句號、emoji、Markdown 強調等限制，不在後續版本加回。這些是該篇的明示修訂，除非使用者要求，不能擴成所有貼文的永久禁令。

## 發文前三檢查

- 用最後有效回填紀錄判斷最近三篇陌生分發與題材／意圖冷卻；同篇多次回填可看數量差額，不以截圖時刻推算成熟度；不要從 `content_plan.md` 讀舊績效。
- 確認草稿決策來自同平台／同 content type／同 surface 的 comparables；跨 cohort 只能列差異，不可排成勝負榜。
- 題材、素材、平台與「一稿同步」若已由使用者說明，直接採用，不重問。
- 個人帳號／頻道的內容禁區只讀 `current_brief.md`；通用平台文件不可硬編使用者的私人政策。
- 只有使用者要求實際操作發布才啟用瀏覽器；寫草稿不需要。

## 產稿

1. 先決定這篇唯一主目標：陌生觸及、討論、追更、star、私訊或社群轉化。
2. 選一個 content archetype、一個 hook、一個 CTA；不要把多個公式疊成 dashboard。
3. 使用者明示同步時，只產一份 canonical copy。YouTube 標題可取第一句或另給一行必填標題，但正文不維護第二套。
4. Mode C 先判斷是數據／製程復盤、觀點文，還是連載 caption；「長文」不是越長越好。沿用與該 surface 相符的實際樣本節奏，刪掉重複推論、科普式解說與為了湊互動硬加的問題。沒有同 cohort 樣本時先給精簡可讀稿，不把另一種 surface 的字數或時間硬套到目標平台。
5. 生成後做 quick QA：
   - 首段 5 秒內讀得懂，沒有多層 meta。
   - 數字都有來源；不把推論寫成事實。
   - 語氣像 `voice_quick.md`，沒有顧問腔／AI 總結腔。
   - 只有一個 CTA；沒有不必要 hashtag、emoji 或外部連結。
   - 實際數一次字數、段落、換行、標點、emoji、Markdown 符號；和所選樣本或使用者明示格式逐項對照。若 FB 正文要求純文字，不在 copy 內插入 `**粗體**`、標題或分析註解。
   - Reels／Shorts caption 不假裝能補救片內留存。
6. 任一項失敗就先重寫，再交付；不要讓使用者替系統做第一輪刪減。

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
