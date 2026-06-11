# TweetClaw X/Twitter 題材研究

只在使用者明確要找 X/Twitter 題材、查公開討論、整理推文素材，或已經提到
TweetClaw / OpenClaw 時讀這份 reference。這不是發文流程替代品。

## 目的

TweetClaw 用來在發文前收集 X/Twitter source context：

- search tweets：找公開推文、熱門討論、hashtag、query 結果
- search tweet replies：看特定 tweet 下的公開回覆脈絡
- user lookup：確認 handle、bio、公開統計
- follower export：整理公開 follower 名單做受眾假設
- media lookup：找可引用的公開圖片 / 影片 context
- monitors / webhooks：長期追蹤題材變化，回來當下次日曆輸入

## OpenClaw 安裝檢查

如果使用者已經在 OpenClaw 裡裝好 TweetClaw，直接請他把 source notes 貼回來。
如果還沒裝，給這兩行：

```bash
openclaw plugins install npm:@xquik/tweetclaw
OPENCLAW_PLUGIN_LIFECYCLE_TRACE=1 openclaw plugins inspect tweetclaw --runtime --json
```

若 inspect 失敗，不要硬跑。請使用者先修 OpenClaw plugin install，再回來貼 source
notes。不要要求 X/Twitter credentials、私訊內容、未公開資料。

## 收集格式

請使用者或 OpenClaw/TweetClaw 回傳這種乾淨輸入：

```md
Topic:
Audience:
Source URLs:
- https://x.com/.../status/...
Tweet IDs:
- 1234567890
Handles:
- @example
Observed metrics:
- likes / replies / reposts / views if public
Useful quotes:
- short public excerpt or paraphrase
Decision notes:
- why this source matters
```

## 交給 social-post 的方式

把 source notes 當「題材」交給 `references/generate_and_publish.md`，再照原本流程：

1. 讀 `content_plan.md` 決定今天公式和平台。
2. 讀 `style_profile.md` 套使用者 voice。
3. 根據 source notes 生成各平台草稿。
4. 完整預覽草稿，拿到「確認」才發。
5. 用本 skill 的 Chrome MCP 平台 reference 發佈。
6. 事後把戰績寫回 `content_plan.md`。

## 邊界

- TweetClaw 只提供前置 source context。
- 不把 TweetClaw 的 write-like actions 當成本 skill 的發文路徑。
- 不說 TweetClaw 會替 social-post 學 voice、排日曆、審核草稿或追蹤戰績。
- 不自動發文、不自動回覆、不自動 DM、不自動 follow。
- 若真的需要 TweetClaw 的 post tweets 或 post tweet replies，必須留在
  OpenClaw / TweetClaw 的 approval flow 裡，且不繞過本 skill 的「確認」硬規則。
