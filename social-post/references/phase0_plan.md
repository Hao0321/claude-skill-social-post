# P0 Content planning

## 目標

把下一個可執行內容序列寫進 `current_brief.md`。它只存方向、平台政策與下一步，不存績效數字；發布與成效分別進 structured ledgers。

## 流程

1. 從對話判定主目標：陌生觸及、star、客戶私訊、社群轉化、追更或品牌信任。資訊已足夠就直接規劃，不重問。
2. 必須先跑 compact comparables context：`python -B scripts/social_data.py comparables --platform <platform> --content-type <content_type> --surface <surface> --limit 2 --format json`。只用同平台／媒體與版型 cohort；它必須帶出原文、長度／版型、關鍵字、語氣、標點、日期／星期／分鐘與 outcomes，規劃時實際引用這些欄位。若沒有合格樣本，明示「無可比案例」再退回 brief／rules，不補造 pattern。
   - 四個 filter 缺一個時，輸出會標成 `cohort_is_exact:false` 與 `outcome_comparison_allowed:false`，只能拿來找資料，不能比較成效。
   - 選樣固定按發布時間取最近案例，明示 `performance_ranked:false`；它不是「最佳文案榜」，不得把回傳順序解讀成勝負或爆款分數。
3. 跑 latest summary 只查看 KPI 與前篇是否仍成長；題材、archetype、CTA 與格式差異一律從 comparables context 讀，不把不同時間窗硬比。
   X 內容另讀 `x.md` 的 For You 來源與邊界；把 hook、媒體、連結、hashtag 與發布時間當待驗證變因，不依公開權重預估觸及。
4. 選 3–5 個內容 slot。每個 slot 只寫：題材、主目標、平台、archetype、唯一 CTA、要驗證的假設。
5. 同敘事意圖與 archetype 保持間隔；前篇仍在長尾成長時，下一篇換 intent 或延後。
6. 使用者明示同步發布時，slot 只維護一份 canonical copy。
7. 更新 `current_brief.md` 的當前方向。舊 14 天表若需要追溯，留在 `content_plan.md` legacy archive，不再追加績效。

## 輸出

- 先給下一篇的明確建議。
- 再給後續 2–4 個 slot 與各自目的。
- 把要驗證的差異寫成 experiment plan；同時改多個變因時標 confound，不稱 A/B。

## 不做

- 不為湊滿 14 天硬排。
- 不從單篇爆款直接複製成鐵則。
- 不把成效數字抄進 plan／voice／platform prose。
- 不同平台口徑、不同題材不可直接排成勝負榜。
- 發布日期、星期與精確分鐘只作候選變因；comparables 顯示同分鐘高低結果時，不得推薦固定黃金時段或宣稱因果。
