/** Anonymous DOM and tab doubles shared by pure-reader and runtime tests. */
import assert from "node:assert/strict";
import { runInNewContext } from "node:vm";
import { readThreadsZeroTerminal } from "./comment_chrome_threads_canary_surface.mjs";
import { readThreadsSelectedDialog } from "./comment_chrome_threads_modal_reader.mjs";

const expected = Object.freeze({
  account: "example.owner", author: "example.reader", host: "www.threads.com",
  postId: "Root123", commentId: "Comment456",
  postUrl: "https://www.threads.com/@example.owner/post/Root123",
  commentUrl: "https://www.threads.com/@example.reader/post/Comment456",
  postPath: "/@example.owner/post/Root123", targetPath: "/@example.reader/post/Comment456",
  selector: ":scope > div:nth-of-type(1) > div:nth-of-type(2) > div:nth-of-type(1)",
  body: "Useful complete update", displayedAt: "1m", targetDatetime: "2026-08-31T00:00:00.000Z",
});
const calls = { zero: 0, modal: 0, clicks: 0, fills: 0 };

function matches(node, selector) {
  return selector.split(",").some((part) => {
    let simple = part.trim();
    const exclusions = [...simple.matchAll(/:not\(([^()]+)\)/gu)].map((match) => match[1]);
    simple = simple.replace(/:not\([^()]+\)/gu, "");
    if (exclusions.some((excluded) => matches(node, excluded))) return false;
    const tag = simple.match(/^[A-Za-z][A-Za-z0-9-]*/u)?.[0];
    if (tag && node.tagName !== tag.toUpperCase()) return false;
    const nth = simple.match(/:nth-of-type\((\d+)\)/u)?.[1];
    if (nth && node.parentElement?.children.filter((child) => child.tagName === node.tagName).indexOf(node) + 1 !== Number(nth)) return false;
    for (const match of simple.matchAll(/\[([^\]=\s*^$]+)(?:([*^$]?=)"([^"]*)")?\]/gu)) {
      const value = node.getAttribute(match[1]);
      if (value === null) return false;
      if (match[2] === "=" && value !== match[3]) return false;
      if (match[2] === "*=" && !value.includes(match[3])) return false;
      if (match[2] === "^=" && !value.startsWith(match[3])) return false;
      if (match[2] === "$=" && !value.endsWith(match[3])) return false;
    }
    return true;
  });
}

class Node {
  constructor(tag, attrs = {}, children = []) {
    this.nodeType = 1;
    this.tagName = tag.toUpperCase();
    this.attrs = attrs;
    this.childNodes = [];
    this.parentElement = null;
    for (const child of children) this.append(child);
  }
  append(child) {
    const node = typeof child === "string" ? { nodeType: 3, nodeValue: child } : child;
    node.parentElement = this;
    this.childNodes.push(node);
    return node;
  }
  replaceChildren(...children) {
    for (const child of this.childNodes) child.parentElement = null;
    this.childNodes = [];
    for (const child of children) this.append(child);
  }
  get children() { return this.childNodes.filter((child) => child.nodeType === 1); }
  get parentNode() { return this.parentElement; }
  get firstElementChild() { return this.children[0] ?? null; }
  get lastElementChild() { return this.children.at(-1) ?? null; }
  get nextElementSibling() {
    const siblings = this.parentElement?.children ?? [];
    return siblings[siblings.indexOf(this) + 1] ?? null;
  }
  getAttribute(name) { return this.attrs[name] ?? null; }
  hasAttribute(name) { return Object.hasOwn(this.attrs, name); }
  get innerText() {
    if (!this.getClientRects().length) return "";
    return this.childNodes.map((child) => child.nodeType === 3 ? child.nodeValue : child.innerText).join("");
  }
  get textContent() { return this.childNodes.map((child) => child.nodeType === 3 ? child.nodeValue : child.textContent).join(""); }
  getClientRects() {
    if (this.tagName === "TITLE") return [];
    for (let node = this; node; node = node.parentElement) if (node.attrs.hidden === "true") return [];
    return [{}];
  }
  contains(node) {
    for (let current = node; current; current = current.parentElement) if (current === this) return true;
    return false;
  }
  closest(selector) {
    for (let node = this; node; node = node.parentElement) if (matches(node, selector)) return node;
    return null;
  }
  querySelectorAll(selector) {
    if (selector.startsWith(":scope > ")) {
      return selector.slice(9).split(" > ").reduce((nodes, part) => nodes.flatMap((node) => node.children.filter((child) => matches(child, part))), [this]);
    }
    return this.children.flatMap((child) => [
      ...(matches(child, selector) ? [child] : []), ...child.querySelectorAll(selector),
    ]);
  }
  querySelector(selector) { return this.querySelectorAll(selector)[0] ?? null; }
  click() { calls.clicks += 1; throw new Error("pure candidate callbacks cannot click"); }
  fill() { calls.fills += 1; throw new Error("pure candidate callbacks cannot fill"); }
}
const el = (tag, attrs = {}, children = []) => new Node(tag, attrs, children);

function postRow({ path = expected.targetPath, author = expected.author, body = expected.body, zero = true } = {}) {
  const profile = el("a", { role: "link", href: `/@${author}` }, [author]);
  const time = el("time", { datetime: expected.targetDatetime }, [expected.displayedAt]);
  const anchor = el("a", { role: "link", href: path }, [time]);
  const header = el("div", {}, [profile, anchor]);
  const content = el("div", { dir: "auto" }, [body]);
  const replyIcon = el("svg", { role: "img", "aria-label": "回覆" }, [el("title", {}, ["回覆"]), el("path")]);
  const reply = el("div", { role: "button" }, [el("span", {}, [replyIcon]), el("span")]);
  const controls = el("div", {}, [reply]);
  const bodyControls = el("div", {}, [content, controls]);
  const marker = el("div", {}, zero ? ["尚無回覆"] : []);
  const ownComposer = el("div", {}, [
    el("a", { role: "link", href: `/@${expected.account}` }, [expected.account]),
    el("div", { role: "textbox", contenteditable: "true", "aria-placeholder": `回覆${expected.author}……` }),
  ]);
  const shell = el("div", {}, [el("div", {}, [el("img", { alt: `${author}的大頭貼照` })]), header, bodyControls, marker, ownComposer]);
  const owner = el("div", { "data-pressable-container": "true" }, [shell]);
  return { owner, shell, header, profile, time, anchor, content, controls, bodyControls, marker, ownComposer, reply };
}

function zeroFixture() {
  const original = postRow({ path: expected.postPath, author: expected.account, body: "Root post", zero: false });
  const focus = postRow();
  const originalPagelet = el("div", { "data-pagelet": "threads_post_page_0" }, [original.owner]);
  const focusPagelet = el("div", { "data-pagelet": "threads_post_page_1" }, [focus.owner]);
  const tailPagelet = el("div", { "data-pagelet": "threads_post_page_{n}" });
  const emptyTail = el("div");
  const context = el("div", {}, [originalPagelet, focusPagelet, tailPagelet, emptyTail]);
  const root = el("div", { role: "region", "aria-label": "直欄內文" }, [context]);
  return { root, context, originalPagelet, focusPagelet, tailPagelet, emptyTail, original, focus };
}

function modalFixture() {
  const heading = el("h2", {}, ["回覆"]);
  const avatarImage = el("img", { alt: `${expected.author}的大頭貼照` });
  const avatarLink = el("a", { href: `/@${expected.author}` }, [avatarImage]);
  const avatar = el("div", {}, [avatarLink]);
  const profile = el("a", { href: `/@${expected.author}` }, [expected.author]);
  const time = el("time", { datetime: expected.targetDatetime }, [expected.displayedAt]);
  const header = el("div", {}, [profile, time]);
  const connector = el("div");
  const context = el("div", {}, [`正在回覆@${expected.account}`]);
  const content = el("div", { dir: "auto" }, [expected.body]);
  const bodyShell = el("div", {}, [context, content]);
  const bodyBranch = el("div", {}, [bodyShell]);
  const card = el("div", {}, [avatar, header, connector, bodyBranch]);
  const ownAvatar = el("img", { alt: `${expected.account}的大頭貼照` });
  const ownLabel = el("span", {}, [expected.account]);
  const textbox = el("div", { role: "textbox", contenteditable: "true", "data-lexical-editor": "true",
    "aria-placeholder": `回覆 ${expected.author}……` });
  const composer = el("div", {}, [ownAvatar, ownLabel, textbox]);
  const addThreadAvatar = el("img", { alt: `${expected.account}的大頭貼照` });
  const addThreadBranch = el("div", {}, [addThreadAvatar]);
  const submit = el("button", {}, ["發佈"]);
  const root = el("div", { role: "dialog", "aria-modal": "true" }, [heading, card, composer, addThreadBranch, submit]);
  return { root, heading, card, avatar, avatarLink, avatarImage, profile, time, header, connector, context,
    content, bodyShell, bodyBranch, ownAvatar, ownLabel, textbox, composer, addThreadAvatar, addThreadBranch, submit };
}

function evaluate(callback, fixture, input = expected) {
  if (callback === readThreadsZeroTerminal) calls.zero += 1;
  if (callback === readThreadsSelectedDialog) calls.modal += 1;
  return runInNewContext(`(${callback.toString()})(root, expected)`, { root: fixture.root, expected: input, URL });
}
const localJson = (value) => JSON.parse(JSON.stringify(value));

const action = Object.freeze({
  action_id: "anonymous-action", intent_id: "anonymous-intent", session_id: "anonymous-session",
  permit_id: "anonymous-permit", comment_fingerprint: "anonymous-fingerprint",
  reply_text: "hello", reply_hash: "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824",
  expected_body: expected.body, author_key: expected.author, post_permalink: expected.postUrl,
  scope: { platform: "threads", account_key: expected.account, post_key: expected.postId, comment_key: expected.commentId },
  comment_anchor: { platform_comment_id: expected.commentId, comment_permalink: expected.commentUrl },
});

class Locator {
  constructor(fixture, nodes) { this.fixture = fixture; this.nodes = nodes; }
  locator(selector) { return new Locator(this.fixture, this.nodes.flatMap((node) => node.querySelectorAll(selector))); }
  filter({ has }) { return new Locator(this.fixture, this.nodes.filter((node) => has.nodes.some((child) => node.contains(child)))); }
  getByRole(role, options = {}) {
    const selector = role === "button" ? 'button,[role="button"]' : `[role="${role}"]`;
    const located = new Locator(this.fixture, this.nodes.flatMap((node) => node.querySelectorAll(selector))
      .filter((node) => !options.name || (node.getAttribute("aria-label") || node.innerText) === options.name));
    if (role === "button" && options.name === "發佈" && this.fixture.dialogOpen) {
      this.fixture.submitLookups += 1;
      this.fixture.afterSubmitLookup?.(this.fixture);
    }
    return located;
  }
  nth(index) { return new Locator(this.fixture, this.nodes.slice(index, index + 1)); }
  async count() { return this.nodes.length; }
  async isVisible() { return this.nodes.length === 1 && this.nodes[0].getClientRects().length > 0; }
  async isEnabled() { return this.nodes.length === 1 && !this.nodes[0].hasAttribute("disabled"); }
  async getAttribute(name) { assert.equal(this.nodes.length, 1); return this.nodes[0].getAttribute(name); }
  async waitFor(options) {
    assert.equal(options.state, "visible");
    assert.ok([10000, 15000].includes(options.timeoutMs));
    this.fixture.waits.push(options.timeoutMs);
    await this.fixture.beforeWait?.(this, options);
    if (!(await this.isVisible())) throw new Error("anonymous native readiness requires exactly one visible node");
  }
  async click() {
    assert.equal(this.nodes.length, 1);
    assert.equal(this.nodes[0], this.fixture.zero.focus.reply, "only the exact native reply opener can be clicked");
    this.fixture.clicks += 1;
    assert.ok(this.fixture.clicks <= 1, "source selection never retries an uncertain click");
    if (this.fixture.ambiguousClick) throw new Error("ambiguous anonymous reply-opening click");
    this.fixture.openDialog();
  }
  async evaluate(callback, input) {
    assert.equal(this.nodes.length, 1, "real callback evaluation requires exactly one native node");
    this.fixture.callbacks.push(callback.name);
    const result = evaluate(callback, { root: this.nodes[0] }, input);
    this.fixture.onEvaluate?.(callback.name, this.fixture);
    return result;
  }
}

function sourceFixture(options = {}) {
  const fixture = { zero: zeroFixture(), modal: modalFixture(), url: expected.commentUrl,
    submitLookups: 0, clicks: 0,
    dialogOpen: false, waits: [], callbacks: [], ...options };
  fixture.zero.original.reply.append("3");
  fixture.account = el("a", { role: "link", href: `/@${expected.account}` }, [el("svg", { "aria-label": "個人檔案" })]);
  const title = el("a", { href: expected.targetPath }, [el("h1", {}, ["Thread"])]);
  fixture.document = el("div", {}, [fixture.account, title, fixture.zero.root]);
  fixture.openDialog = () => { fixture.dialogOpen = true; fixture.document.append(fixture.modal.root); };
  if (fixture.preexistingDialog) fixture.openDialog();
  fixture.tab = { id: "anonymous-canary-tab", url: async () => fixture.url,
    playwright: new Locator(fixture, [fixture.document]) };
  return fixture;
}

function resultFixture({ delayedRegion = false } = {}) {
  const fixture = sourceFixture();
  const childPath = `/@${expected.account}/post/OwnReply789`;
  const childUrl = `https://${expected.host}${childPath}`;
  fixture.zero.focus.reply.append("1");
  fixture.zero.focus.marker.replaceChildren();
  const observedChild = postRow({ path: childPath, author: expected.account, body: action.reply_text });
  fixture.zero.tailPagelet.append(observedChild.owner);
  const parentDocument = fixture.document;
  const childRoot = postRow({ path: expected.postPath, author: expected.account, body: "Root post", zero: false });
  const childOriginal = postRow({ path: expected.targetPath, author: expected.author, body: expected.body, zero: false });
  const childFocus = postRow({ path: childPath, author: expected.account, body: action.reply_text });
  const childRootRow = el("div", {}, [childRoot.owner]);
  const childParentRow = el("div", {}, [childOriginal.owner]);
  const childContext = el("div", { "data-pagelet": "threads_post_page_0" }, [childRootRow, childParentRow]);
  const childRegion = el("div", { role: "region", "aria-label": "直欄內文" }, [el("div", {}, [
    childContext,
    el("div", { "data-pagelet": "threads_post_page_1" }, [childFocus.owner]),
  ])]);
  const childDocument = el("div", {}, [
    el("a", { role: "link", href: `/@${expected.account}` }, [el("svg", { "aria-label": "個人檔案" })]),
    el("a", { href: childPath }, [el("h1", {}, ["Thread"])]), childRegion,
  ]);
  Object.assign(fixture, { childPath, childUrl, childRoot, childOriginal, childFocus, childDocument,
    childRootRow, childParentRow, childContext,
    parentDocument, observedChild, scene: "parent", navigations: [], discoveryReads: 0,
    regionReadiness: [] });
  fixture.beforeWait = async (locator) => {
    const region = fixture.document.querySelector('[role="region"]');
    if (delayedRegion && region?.attrs.hidden === "true" && locator.nodes.includes(region)) {
      await Promise.resolve();
      delete region.attrs.hidden;
      fixture.regionReadiness.push(fixture.url);
    }
  };
  fixture.tab.goto = async (url) => {
    assert.ok([expected.commentUrl, childUrl].includes(url), "navigation uses only the exact observed native child and original parent");
    fixture.navigations.push(url);
    fixture.scene = url === childUrl ? "child" : "parent";
    fixture.url = url;
    fixture.document = fixture.scene === "child" ? childDocument : parentDocument;
    if (delayedRegion) fixture.document.querySelector('[role="region"]').attrs.hidden = "true";
    fixture.tab.playwright = new Locator(fixture, [fixture.document]);
  };
  return fixture;
}


export { expected, calls, el, postRow, zeroFixture, modalFixture, evaluate, localJson, action, Locator, sourceFixture, resultFixture };
