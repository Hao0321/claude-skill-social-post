import { api, copyText, download } from "./api.js";
import { el, field, panel, button, notice } from "./ui.js";

export function editor({ format, platform, title, draft, run, toast, onSaved }) {
  const node = panel("文案編輯", "PRIVATE DRAFT");
  const body = field("貼文正文", "draft", { rows: 10,
    placeholder: "把 AI 完成的文案貼進來，或直接從這裡開始寫。", value: draft?.text || "" });
  body.input.classList.add("editor-area");
  const counters = el("div", "metrics-row");
  const cells = {};
  for (const [id, label] of [["characters_including_spaces", "字元含空白"],
    ["paragraph_count", "段落"], ["explicit_line_breaks", "明示換行"], ["punctuation", "標點"]]) {
    const cell = el("div", "text-metric");
    const value = el("strong", "", "—");
    cell.append(value, el("span", "", label));
    counters.append(cell);
    cells[id] = value;
  }
  const message = el("p", "editor-caption", "格式檢查採用既有分析器；不預測流量，也不會修改你的原文。");
  const row = el("div", "button-row");
  let saveId = null;
  let pendingSignature = null;
  const signatureFor = () => JSON.stringify([title() || "未命名草稿", body.input.value, platform(), format()]);
  let savedSignature = draft ? signatureFor() : null;
  const save = button("保存私人草稿", () => run(save, async () => {
    if (!body.input.value.trim()) throw new Error("請先填入貼文正文。");
    const draftTitle = title() || "未命名草稿";
    const signature = signatureFor();
    if (signature !== pendingSignature) {
      saveId = crypto.randomUUID();
      pendingSignature = signature; // Retrying an uncertain save reuses the same id.
    }
    const result = await api("/api/drafts/save", {
      id: saveId, title: draftTitle, text: body.input.value, platform: platform(), format: format(),
    });
    savedSignature = signature;
    saveId = result.id;
    toast("草稿已保存到本機。未發布到任何平台。");
    await onSaved();
  }), "primary");
  const copy = button("複製文案", () => run(copy, async () => {
    await copyText(body.input.value);
    toast("已複製文案。");
  }));
  const exportButton = button("下載文字", () => download(body.input.value, "social-post-draft.txt"));
  row.append(save, copy, exportButton);
  const previewToggle = button("查看黑底白字版型", () => {
    preview.hidden = !preview.hidden;
    previewToggle.setAttribute("aria-expanded", String(!preview.hidden));
    renderPreview();
  }, "small");
  previewToggle.setAttribute("aria-expanded", "false");
  const preview = el("div", "stack-gap");
  preview.hidden = true;
  preview.id = "black-card-preview";
  previewToggle.setAttribute("aria-controls", preview.id);
  const card = el("div", "black-preview");
  preview.append(el("span", "preview-label", "LAYOUT STUDY / NOT A FACEBOOK RENDER"), card,
    el("p", "editor-caption", "這是本機版型試讀。平台自動換行與背景可用性須發布前另行核對；長文不保證適合背景短卡。"));
  function renderPreview() { card.textContent = body.input.value || "一張卡，只說一個主張。"; }
  let debounce;
  let revision = 0;
  async function updateAnalysis() {
    const current = ++revision;
    try {
      const result = await api("/api/analyze", { text: body.input.value });
      if (current !== revision) return;
      for (const [key, value] of Object.entries(cells)) {
        value.textContent = String(key === "punctuation" ? result.punctuation.total : result.counts[key]);
      }
      const hasEmoji = /\p{Extended_Pictographic}/u.test(body.input.value);
      message.textContent = hasEmoji
        ? "原文含表情符號。此工作台預設任務要求不新增表情符號；保存會保留你輸入的原文。"
        : "格式檢查採用既有分析器；不預測流量，也不會修改你的原文。";
    } catch (error) {
      if (current === revision) message.textContent = error.message;
    }
  }
  body.input.addEventListener("input", () => {
    revision += 1;
    clearTimeout(debounce);
    debounce = setTimeout(updateAnalysis, 250);
    renderPreview();
  });
  node.append(body.wrapper, counters, message, row, el("div", "stack-gap"), previewToggle, preview);
  if (draft) node.append(notice("已開啟保存版本", "修改後保存會建立新的私人版本，不覆蓋原草稿。"));
  updateAnalysis();
  return { node, input: body.input,
    isDirty: () => savedSignature === null ? Boolean(body.input.value.trim()) : signatureFor() !== savedSignature };
}
