// Presentation only. All user material goes through textContent/value, never HTML.
export function el(tag, className = "", text = "") {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text) node.textContent = text;
  return node;
}

export function button(text, handler, variant = "") {
  const node = el("button", "button " + variant, text);
  node.type = "button";
  if (handler) node.addEventListener("click", handler);
  return node;
}

export function notice(title, text, error = false) {
  const node = el("div", "notice" + (error ? " error" : ""));
  node.append(el("strong", "", title), el("p", "", text));
  return node;
}

export function heading(title, eyebrow, note = "") {
  const node = el("div", "section-heading");
  const text = el("div");
  text.append(el("p", "eyebrow", eyebrow), el("h2", "", title));
  node.append(text);
  if (note) node.append(el("p", "", note));
  return node;
}

export function panel(title, caption = "") {
  const node = el("section", "panel");
  const header = el("div", "panel-head");
  header.append(el("h2", "", title), el("span", "mono", caption));
  node.append(header);
  return node;
}

export function field(label, name, { type = "text", placeholder = "", hint = "", options, value = "", rows } = {}) {
  const wrapper = el("label", "field");
  const title = el("span", "field-title", label);
  const input = el(options ? "select" : rows ? "textarea" : "input");
  input.name = name;
  if (options) {
    for (const option of options) {
      const item = el("option", "", typeof option === "string" ? option : option.label);
      item.value = typeof option === "string" ? option : option.value;
      input.append(item);
    }
  } else {
    if (!rows) input.type = type;
    input.placeholder = placeholder;
    if (rows) input.rows = rows;
    input.maxLength = name === "title" ? 160 : 24000;
  }
  input.value = value;
  wrapper.append(title, input);
  if (hint) wrapper.append(el("span", "field-hint", hint));
  return { wrapper, input };
}

export function renderNav(catalog, current) {
  const nav = document.querySelector("#nav");
  nav.replaceChildren();
  const rows = [{ id: "home", index: "00", name: "工作台總覽" }, ...catalog.modes,
    { id: "drafts", index: "07", name: "私人草稿" }, { id: "learning", index: "08", name: "資料分區與審核" }];
  for (const row of rows) {
    const link = el("a", "nav-item");
    link.href = "#" + row.id;
    link.append(el("span", "", row.index), el("span", "", row.name));
    if (row.id === current) link.setAttribute("aria-current", "page");
    nav.append(link);
  }
}

function poster() {
  const node = el("div", "hero-poster");
  node.setAttribute("aria-hidden", "true");
  const top = el("div", "poster-top");
  top.append(el("span", "", "FROM SIGNAL TO STORY"), el("span", "", "EST. 2026"));
  const bottom = el("div", "poster-bottom");
  const words = el("p");
  words.append(el("span", "", "THINK. MAKE."), el("br"), el("span", "", "LEARN. REPEAT."));
  bottom.append(words, el("span", "poster-number", "01—06"));
  node.append(top, el("div", "poster-line"), el("div", "poster-line second"),
    el("div", "poster-ring"), el("div", "poster-band", "OWN YOUR VOICE."),
    el("div", "poster-cut"), bottom);
  return node;
}

export function home(catalog, overview) {
  const page = el("div");
  const hero = el("section", "hero");
  const copy = el("div", "hero-copy");
  const title = el("h1", "hero-title", "SOCIAL");
  title.append(el("span", "blue-text", "POST."));
  const start = el("a", "button primary", "開始撰寫貼文");
  start.href = "#P2";
  copy.append(el("span", "eyebrow", "CONTENT, WITH INTENTION."), title,
    el("h2", "", "讓內容，有自己的聲音。"),
    el("p", "", "從一個想法，到一篇有你風格的貼文。把規劃、創作與成效放在同一個工作台，下一步不再靠猜。"), start);
  hero.append(copy, poster());
  const strip = el("div", "signal-strip");
  const values = [
    ["WORKSPACE", "資料只留本機", overview.voice_available ? "私人聲線檔案已連結" : "尚未建立私人聲線", true],
    ["POST ARCHIVE", String(overview.posts), "已記錄貼文"],
    ["OUTCOME SNAPSHOTS", String(overview.snapshots), "成效快照"],
    ["PRIVATE DRAFTS", String(overview.drafts), "已保存草稿"],
  ];
  for (const [label, value, detail, state] of values) {
    const cell = el("div", "signal-cell" + (state ? " state" : ""));
    cell.append(el("p", "eyebrow", label), el("strong", "", value), el("small", "", detail));
    strip.append(cell);
  }
  const grid = el("div", "mode-grid");
  for (const mode of catalog.modes) {
    const tile = el("button", "mode-card" + (mode.id === "P2" ? " accent" : ""));
    tile.type = "button";
    tile.addEventListener("click", () => { location.hash = mode.id; });
    const top = el("div", "mode-card-top");
    top.append(el("span", "", mode.index + " / " + mode.english), el("span", "", mode.id));
    tile.append(top, el("h3", "", mode.name), el("p", "", mode.summary));
    grid.append(tile);
  }
  const formats = el("section", "formats-section");
  const formatGrid = el("div", "format-grid");
  for (const format of catalog.formats) {
    const tile = el("div", "format-tile");
    const text = el("div");
    text.append(el("h3", "", format.name), el("p", "", format.description));
    tile.append(el("span", "format-letter", format.id), text);
    formatGrid.append(tile);
  }
  formats.append(heading("三種寫法，不是三個流程。", "WRITING FORMATS", "A / B / C 決定寫法，F 決定內容骨架"), formatGrid);
  const boundary = notice("工具執行與 AI 撰稿，分工清楚。",
    "工作台可保存草稿、檢查格式、驗證匯入與讀取案例。AI 任務需貼到 Codex／Claude Code 執行；ChatGPT 另須可用 Skill。此介面不會自動發布或送出留言。");
  boundary.classList.add("home-notice");
  page.append(hero, strip, heading("你想完成哪件事？", "SIX WAYS TO MOVE FORWARD", "不用記模式代號，從目的開始。"), grid, formats, boundary);
  return page;
}

export function workflowHead(mode) {
  const node = el("header", "workflow-head");
  const back = el("a", "breadcrumb", "WORKSPACE / 工作台總覽");
  back.href = "#home";
  const title = el("div", "workflow-title-row");
  const copy = el("div");
  copy.append(el("p", "eyebrow", mode.id + " / " + mode.english),
    el("h1", "", mode.question), el("p", "", mode.summary));
  title.append(copy, el("span", "workflow-number", mode.index));
  const io = el("div", "io-row");
  for (const [name, items] of [["INPUT", mode.inputs], ["OUTPUT", mode.outputs]]) {
    const group = el("div", "io-group");
    const tags = el("div", "io-tags");
    for (const text of items) tags.append(el("span", "io-tag", text));
    group.append(el("span", "eyebrow", name), tags);
    io.append(group);
  }
  node.append(back, title, io);
  return node;
}

export function outputPanel() {
  const node = panel("任務預覽", "AI HANDOFF");
  const output = el("div", "task-output empty");
  output.append(el("span", "empty-mark", "—"),
    el("p", "", "填入題材與必要素材，建立一份清楚的 Social Post 任務。"),
    el("p", "", "建立任務不等於已執行 AI，也不授權外部發布。"));
  node.append(output);
  return { node, output };
}
