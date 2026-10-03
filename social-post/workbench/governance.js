import { api } from "./api.js";
import { el, button, panel, notice, field, heading } from "./ui.js";

export async function governancePage({ run, toast, overview }) {
  const page = el("div");
  page.append(heading("資料分區與規則審核", "AUTHOR CONTROL", "觀測不等於規則。你決定何時改變寫法。"));
  const data = await api("/api/governance");
  const locked = data.contract.status === "locked";
  page.append(notice(locked ? "正式作者契約已鎖定" : "尚未建立作者契約",
    locked ? "Revision " + data.contract.revision + "。新數據不會自動改寫；原始 F 與規則完整保留。" :
      "先提供真實私人聲線與公式，再由主機明確建立基準。公開範本不是你的作者資料。"));
  const channels = panel("平台 × 媒體資料分區", "ISOLATED LEARNING");
  const grid = el("div", "mode-grid");
  for (const row of overview.learning_channels.channels) {
    const card = el("article", "comparison-card");
    card.append(el("h3", "", row.platform + " / " + (row.media_family === "video" ? "影片" : "圖文")),
      el("p", "", row.post_count + " 篇自己的貼文 / " + row.snapshot_rows + " 份可用觀測"));
    const detail = el("details");
    detail.append(el("summary", "", "版型與觀測階段"), el("pre", "", JSON.stringify(row.cohorts, null, 2)));
    card.append(detail); grid.append(card);
  }
  channels.append(grid, notice("第三方參考獨立保存", data.external_references.length +
    " 份外部觀測，不計入自己的貼文、追蹤成長或平台勝率。合併面板與媒體未確認資料不進跨區排名。"));
  const proposals = panel("候選更新", "REVIEW BEFORE ACTIVATE");
  proposals.append(notice("先分析，再由你審核與啟用",
    "候選必須指向既有規則，帶同平台／媒體證據與完整前後文。批准不等於啟用；每次操作都綁定精確版本。AI 不得代替你自行按批准。"));
  if (!data.proposals.length) proposals.append(el("p", "", "目前沒有待審候選。既有規則未變更。"));
  for (const event of data.proposals) {
    const row = event.proposal;
    const card = el("article", "comparison-card");
    card.append(el("h3", "", row.title), el("p", "", row.scope.platform + " / " + row.scope.media_family + " / " + event.state),
      el("p", "", row.reason));
    const diff = el("details");
    diff.append(el("summary", "", "核對完整前後文、證據與版本"),
      el("pre", "", JSON.stringify({ target: row.target, before: row.base_text, after: row.replacement_text,
        evidence: row.evidence, claim: row.evidence_claim, base: row.base_revision, digest: event.proposal_digest }, null, 2)));
    card.append(diff);
    if (event.state !== "activated") {
      const notes = field("審核理由", "review_notes", { rows: 3, hint: "請實際閱讀原規則、修改與證據；不是自動語義驗證。" });
      card.append(notes.wrapper);
      const actions = el("div", "button-row");
      for (const [decision, label] of [["approve", "批准此版本"], ["reject", "拒絕此版本"]]) {
        const control = button(label, () => run(control, async () => {
          if (!notes.input.value.trim()) throw new Error("請填寫實際審核理由。");
          if (!window.confirm(label + "「" + row.title + "」？\n" + event.proposal_digest + "\n批准後仍須另行啟用。")) return;
          await api("/api/governance/review", { proposal_id: row.proposal_id, proposal_digest: event.proposal_digest,
            decision, notes: notes.input.value });
          toast("審核已保存；尚未改變正式寫法。"); location.reload();
        }));
        actions.append(control);
      }
      if (event.state === "approve") {
        const control = button("啟用已批准更新", () => run(control, async () => {
          if (!window.confirm("啟用此版本？只影響 " + row.scope.platform + " / " + row.scope.media_family +
            "。\n" + event.proposal_digest + "\n舊版本將保留。")) return;
          await api("/api/governance/activate", { proposal_id: row.proposal_id, proposal_digest: event.proposal_digest });
          toast("已啟用。原始來源與前一契約保留。"); location.reload();
        }), "primary");
        actions.append(control);
      }
      card.append(actions);
    }
    proposals.append(card);
  }
  page.append(channels, el("div", "stack-gap"), proposals);
  return page;
}
