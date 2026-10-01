import { api, copyText, download } from "./api.js";
import { el, button, notice, heading, panel, field, renderNav, home, workflowHead, outputPanel } from "./ui.js";
import { editor } from "./editor.js";

const main = document.querySelector("#main");
let catalog, overview, pendingDraft;
let selectedFormat = "C";
let toastTimer;
let renderVersion = 0;
let activeRoute = "home";
let dirtyGuard = null;

function toast(text) {
  const node = document.querySelector("#toast");
  node.textContent = text;
  node.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { node.hidden = true; }, 6500);
}

async function run(control, action, status) {
  control.disabled = true;
  control.setAttribute("aria-busy", "true");
  if (status) status.textContent = "處理中";
  try { await action(); }
  catch (error) {
    if (status) status.textContent = error.message;
    toast(error.message);
  } finally {
    control.disabled = false;
    control.removeAttribute("aria-busy");
  }
}

function taskBuilder(mode, draft) {
  const node = panel("建立工作任務", "START WITH A CLEAR BRIEF");
  const form = el("form");
  form.addEventListener("submit", event => event.preventDefault());
  const platform = field("目標平台", "platform", { options: catalog.platforms, value: draft?.platform || "facebook" });
  const topic = field(mode.id === "P1" ? "這批樣本的用途" : "題材或任務主題", "topic", {
    placeholder: mode.id === "P2" ? "例如：下一版自動剪輯的開發進度" : "這次想完成什麼？", value: draft?.title || "",
  });
  topic.input.required = true;
  const goal = field("主要目標", "goal", { options: [
    { value: "分享觀察", label: "分享觀察" }, { value: "建立品牌信任", label: "建立品牌信任" },
    { value: "引發討論", label: "引發討論" }, { value: "陌生觸及", label: "陌生觸及" },
    { value: "展示成果", label: "展示成果" }, { value: "後續追更", label: "後續追更" },
  ] });
  const details = field(mode.id === "P1" ? "完整原文與來源" : mode.id === "P5" ? "原留言與脈絡" : "真實事實與補充素材", "details", {
    rows: 6, placeholder: mode.id === "P1" ? "貼上你自己寫的完整原文，註明平台、日期與喜歡的特徵。" :
      mode.id === "P5" ? "貼上完整留言、前後脈絡與希望如何回應。這裡不會直接送出。" :
      "寫下已完成的事情、可驗證數字，以及這篇不想使用的寫法。",
    hint: "不填無法確認的數字。請勿貼上密碼、Cookie 或登入憑證。",
  });
  details.input.required = ["P1", "P5"].includes(mode.id);
  const pair = el("div", "field-pair");
  pair.append(platform.wrapper, goal.wrapper);
  form.append(topic.wrapper, pair);
  if (mode.id === "P2") {
    const picker = el("div", "format-picker");
    const guidance = el("p", "format-guidance");
    const controls = [];
    for (const format of catalog.formats) {
      const control = el("button", "format-choice");
      control.type = "button";
      control.setAttribute("aria-label", "Mode " + format.id + " " + format.name);
      control.append(el("strong", "", format.id), el("span", "", format.name));
      control.addEventListener("click", () => { selectedFormat = format.id; update(); });
      controls.push([control, format]);
      picker.append(control);
    }
    function update() {
      for (const [control, format] of controls) control.setAttribute("aria-pressed", String(format.id === selectedFormat));
      guidance.textContent = catalog.formats.find(format => format.id === selectedFormat).description;
    }
    if (draft) selectedFormat = draft.format;
    update();
    form.append(picker, guidance);
  }
  const formula = field("創作公式 F", "formula", {
    options: [{ value: "", label: "由 Skill 依題材選擇" },
      ...catalog.formulas.map(item => ({ value: item.id, label: item.label }))],
    hint: "F 是內容骨架；A／B／C 是寫法，P0–P5 是工作流程。只列出本機已安裝的公式。",
  });
  if (["P0", "P2"].includes(mode.id)) form.append(formula.wrapper);
  form.append(details.wrapper);
  const url = field("參考網址", "url", { placeholder: "選填；網址只當素材，不會由服務抓取" });
  form.append(url.wrapper);
  node.append(form);
  return { node, form, platform, topic, details, goal, url, formula };
}

function wireTask(mode, builder, output) {
  const status = el("p", "inline-status");
  status.setAttribute("role", "status");
  const create = button(mode.action, () => run(create, async () => {
    if (!builder.form.reportValidity()) return;
    const result = await api("/api/task", {
      mode: mode.id, platform: builder.platform.input.value,
      format: mode.id === "P2" ? selectedFormat : "",
      formula: ["P0", "P2"].includes(mode.id) ? builder.formula.input.value : "",
      topic: builder.topic.input.value, details: builder.details.input.value,
      goal: builder.goal.input.value, url: builder.url.input.value,
    });
    output.output.classList.remove("empty");
    output.output.textContent = result.prompt;
    output.output.tabIndex = 0;
    output.actions?.remove();
    const actions = el("div", "button-row");
    const copy = button("複製任務", () => run(copy, async () => {
      await copyText(result.prompt); toast("已複製。請貼到 Codex／Claude Code 執行；ChatGPT 須有可用 Skill。");
    }), "primary");
    actions.append(copy, button("下載任務", () => download(result.prompt, "social-post-task.txt")));
    output.node.append(actions);
    output.actions = actions;
    status.textContent = "任務已建立，尚未執行 AI。下一步：複製到 Codex／Claude Code。";
  }, status), "primary");
  builder.node.append(create, status);
}

async function draftList(node) {
  const rows = await api("/api/drafts");
  node.replaceChildren();
  if (!rows.length) {
    node.append(notice("還沒有保存草稿", "到「撰寫貼文」編輯正文後，按「保存私人草稿」。不會自動上傳或發布。"));
    return;
  }
  for (const draft of rows) {
    const control = el("button", "draft-item");
    control.type = "button";
    const copy = el("span");
    copy.append(el("strong", "", draft.title), el("small", "", draft.platform + " / MODE " + draft.format + " / " + draft.saved_at));
    control.append(copy, el("span", "", "OPEN"));
    control.addEventListener("click", () => run(control, async () => {
      pendingDraft = await api("/api/drafts/" + draft.id);
      if (location.hash === "#P2") await render();
      else location.hash = "P2";
    }));
    node.append(control);
  }
}

function drafting(mode, draft) {
  const grid = el("div", "workspace-grid");
  const builder = taskBuilder(mode, draft);
  const output = outputPanel();
  wireTask(mode, builder, output);
  const left = el("div", "editor-stack");
  left.append(builder.node, output.node);
  const right = el("div", "editor-stack");
  const drafts = el("div", "draft-list");
  const edit = editor({
    format: () => selectedFormat, platform: () => builder.platform.input.value,
    title: () => builder.topic.input.value, draft, run, toast,
    onSaved: async () => { await draftList(drafts); overview = await api("/api/overview"); },
  });
  dirtyGuard = edit.isDirty;
  const archive = panel("私人草稿", "SAVED LOCALLY");
  archive.append(drafts);
  right.append(edit.node, archive);
  draftList(drafts).catch(error => drafts.append(notice("草稿無法讀取", error.message, true)));
  grid.append(left, right);
  return grid;
}

function handoff(mode) {
  const grid = el("div", "workspace-grid");
  const builder = taskBuilder(mode);
  const output = outputPanel();
  wireTask(mode, builder, output);
  grid.append(builder.node, output.node);
  return grid;
}

function importing() {
  const grid = el("div", "workspace-grid");
  const inputPanel = panel("匯入 outcome bundle", "VALIDATE BEFORE WRITE");
  const fileArea = el("div", "import-file");
  const file = el("input");
  file.type = "file";
  file.accept = ".json,application/json";
  file.setAttribute("aria-label", "選擇 outcome JSON 檔案");
  fileArea.append(file, el("p", "field-hint", "只讀取你選取的 JSON；沒有遠端上傳。上限 100 KB。"));
  const json = field("Outcome JSON", "bundle", { rows: 16, placeholder: "貼上 schema 相符的 outcome bundle，或選取 JSON 檔案。" });
  json.input.classList.add("import-area");
  const resultPanel = panel("驗證與寫入", "EXPLICIT CONFIRMATION");
  const result = el("pre", "task-output", "尚未驗證。預覽不會改動既有資料。");
  const status = el("p", "inline-status");
  status.setAttribute("role", "status");
  let preview = null;
  const commit = button("確認追加到本機資料庫", () => run(commit, async () => {
    const id = preview;
    preview = null;
    const response = await api("/api/outcome/commit", { preview_id: id });
    status.textContent = "已追加保存。原始歷史保留；未發布到任何社群平台。";
    result.textContent = JSON.stringify(response, null, 2);
    overview = await api("/api/overview");
  }, status).finally(() => { commit.disabled = !preview; }), "primary");
  commit.disabled = true;
  const invalidate = () => {
    preview = null; commit.disabled = true;
    status.textContent = ""; result.textContent = "資料已變更，請重新驗證。";
  };
  json.input.addEventListener("input", invalidate);
  file.addEventListener("change", async () => {
    try {
      if (!file.files[0]) return;
      if (file.files[0].size > 100000) throw new Error("檔案超過 100 KB，請分成較小批次。");
      json.input.value = await file.files[0].text(); invalidate();
    } catch (error) { toast(error.message); }
  });
  const validate = button("驗證並預覽", () => run(validate, async () => {
    invalidate();
    const captured = json.input.value;
    const response = await api("/api/outcome/preview", { bundle_json: captured });
    if (captured !== json.input.value) throw new Error("驗證期間資料已變更，請重新驗證。");
    preview = response.preview_id;
    result.textContent = JSON.stringify(response.normalized, null, 2);
    commit.disabled = false;
    status.textContent = "驗證通過，尚未寫入。請核對內容後再確認追加。";
  }, status), "primary");
  const example = button("載入虛構示例", () => run(example, async () => {
    const value = await api("/api/outcome/example");
    json.input.value = JSON.stringify(value, null, 2); invalidate();
    toast("已載入虛構示例；不是你的真實貼文，尚未寫入。");
  }));
  const actions = el("div", "button-row");
  actions.append(validate, example);
  inputPanel.append(fileArea, json.wrapper, actions);
  resultPanel.append(result, commit, status, notice("不是自動學習權重", "匯入會保留原始數據。待分析或缺少原文的資料不會進入可比案例；語氣學習與規律驗證仍依 Skill 執行。"));
  grid.append(inputPanel, resultPanel);
  return grid;
}

function comparing() {
  const grid = el("div", "workspace-grid");
  const controls = panel("設定可比範圍", "EXACT COHORT ONLY");
  const fields = {
    platform: field("平台", "platform", { options: catalog.platforms, value: "facebook" }),
    content_type: field("內容類型", "content_type", { placeholder: "請填資料庫使用的內容類型", value: overview.content_types[0] || "" }),
    surface: field("版型／發布表面", "surface", { placeholder: "請填資料庫使用的 surface", value: overview.surfaces[0] || "" }),
    maturity: field("成效觀測階段", "maturity", { options: catalog.maturities, value: "developing" }),
  };
  for (const [name, value] of Object.entries(fields)) {
    controls.append(value.wrapper);
    value.input.required = true;
    if (["content_type", "surface"].includes(name)) {
      const known = name === "content_type" ? overview.content_types : overview.surfaces;
      if (known.length) {
        const list = el("datalist");
        list.id = "known-" + name;
        known.forEach(text => list.append(el("option", "", text)));
        value.input.setAttribute("list", list.id); controls.append(list);
      }
    }
  }
  const output = panel("最近可比案例", "NOT A PERFORMANCE RANKING");
  const list = el("div", "compare-list");
  list.append(notice("四個條件要對齊", "只比較同平台、內容類型、版型與觀測階段。沒有樣本時會直接顯示，不補造案例。"));
  for (const { input } of Object.values(fields)) input.addEventListener("input", () => {
    list.replaceChildren(notice("比較條件已變更", "請重新讀取，舊結果不代表新的比較範圍。"));
  });
  const load = button("讀取可比案例", () => run(load, async () => {
    const query = Object.fromEntries(Object.entries(fields).map(([key, value]) => [key, value.input.value]));
    if (Object.values(query).some(value => !value.trim())) throw new Error("請完整填入四個比較條件。");
    const response = await api("/api/compare", query);
    if (Object.entries(fields).some(([key, value]) => value.input.value !== query[key])) {
      throw new Error("讀取期間比較條件已變更，請重新讀取。");
    }
    list.replaceChildren(notice("找到 " + response.available_count + " 份可比資料，顯示最近 " + response.returned_count + " 份",
      "按發布時間選取，不按成效排名。發文分鐘只是待驗證變因，不是流量預測或固定黃金時段。"));
    for (const row of response.comparables) {
      const card = el("article", "comparison-card");
      const date = row.publication || {};
      card.append(el("h3", "", row.post_id),
        el("p", "comparison-caption", row.caption || "原文未取得"),
        el("p", "comparison-data", [row.platform, row.maturity, date.published_at || "發布時間未取得"].join(" / ")));
      const detail = el("details");
      detail.append(el("summary", "", "查看完整格式、用詞、標點、日期與成效特徵"),
        el("pre", "", JSON.stringify(row, null, 2)));
      card.append(detail); list.append(card);
    }
  }), "primary");
  controls.append(load, el("div", "stack-gap"), notice("現有資料的命名", "內容類型與 surface 使用原始 ledger 值；輸入框會提示資料庫中已有的選項。"));
  output.append(list);
  grid.append(controls, output);
  return grid;
}

async function render() {
  const request = ++renderVersion;
  const route = location.hash.slice(1) || "home";
  if (dirtyGuard?.() && !window.confirm("正文有未保存的變更。確定離開並放棄這些變更？")) {
    history.replaceState(null, "", "#" + activeRoute);
    pendingDraft = null;
    return;
  }
  dirtyGuard = null;
  activeRoute = route;
  const mode = catalog.modes.find(item => item.id === route);
  renderNav(catalog, mode ? route : route === "drafts" ? "drafts" : "home");
  main.replaceChildren();
  if (route === "drafts") {
    main.append(heading("私人草稿", "YOUR LOCAL ARCHIVE", "保存版本不會自動發布"));
    const list = el("div", "draft-list"); main.append(list);
    await draftList(list);
  } else if (!mode) {
    overview = await api("/api/overview");
    if (request !== renderVersion) return;
    main.append(home(catalog, overview));
  } else {
    main.append(workflowHead(mode));
    if (mode.id === "P5") main.append(notice("此介面不操作 Chrome，也不開啟批次送出",
      "僅建立草擬任務。live 回覆仍受既有帳號、父留言、核准、canary 與能力閘限制；未驗收功能不會因 UI 出現而解鎖。"));
    if (mode.id === "P2") {
      main.append(notice("目前的撰稿交接流程",
        "01 選平台、A／B／C 與 F 公式，填一句題材。02 建立並複製任務。03 在 Codex／Claude Code 依 Skill 完成文案。04 貼回右側編輯、檢查與保存。此版尚未接通按鈕自動呼叫 AI。"));
      main.append(drafting(mode, pendingDraft)); pendingDraft = null;
    } else if (mode.id === "P3") main.append(importing());
    else if (mode.id === "P4") main.append(comparing());
    else main.append(handoff(mode));
  }
  document.title = (mode?.name || (route === "drafts" ? "私人草稿" : "Content Workbench")) + " — Social Post";
}

async function boot() {
  try {
    [catalog, overview] = await Promise.all([api("/api/catalog"), api("/api/overview")]);
    document.querySelector("#version").textContent = "V " + catalog.version;
    await render();
    window.addEventListener("hashchange", () => render().catch(error => {
      main.replaceChildren(notice("此流程目前無法讀取", error.message, true),
        button("重新連線", () => location.reload(), "primary"));
    }));
    window.addEventListener("beforeunload", event => {
      if (!dirtyGuard?.()) return;
      event.preventDefault();
      event.returnValue = "";
    });
  } catch (error) {
    main.replaceChildren(notice("工作台目前無法讀取", error.message, true),
      button("重新連線", () => location.reload(), "primary"));
  }
}

boot();
