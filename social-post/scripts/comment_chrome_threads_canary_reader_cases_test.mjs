/** Pure serialized callback acceptance; no browser or submission. */
import assert from "node:assert/strict";
import { readThreadsZeroTerminal } from "./comment_chrome_threads_canary_surface.mjs";
import { readThreadsSelectedDialog } from "./comment_chrome_threads_modal_reader.mjs";
import { expected, calls, el, postRow, zeroFixture, modalFixture, evaluate, localJson } from "./comment_chrome_threads_dom_fixtures_test.mjs";

function assertCandidateOnly(result) {
  for (const field of ["complete", "exhaustiveThread", "absence_proven", "selectedParentCandidate", "selection", "verifiedNewReply", "replyPermalink"]) {
    assert.equal(Object.hasOwn(result, field), false, `${field} cannot be granted by a pure DOM callback`);
  }
}

function testObservedZeroTerminal() {
  const fixture = zeroFixture();
  assert.equal(fixture.root.querySelector(expected.selector), fixture.focus.owner, "test selector resolves the actual source owner");
  const observed = evaluate(readThreadsZeroTerminal, fixture);
  assert.ok(observed, "exact observed root/focus/empty-native-tail/empty-DIV shape must parse");
  assert.notEqual(Object.getPrototypeOf(observed), Object.prototype, "the actual callback result stays cross-realm");
  assert.deepEqual(localJson(observed), {
    terminal: true, targetDatetime: expected.targetDatetime, marker: "尚無回覆",
    parentPath: expected.postPath, targetPath: expected.targetPath,
    pageletNames: ["threads_post_page_0", "threads_post_page_1", "threads_post_page_{n}"], unlabelledTailEmpty: true, observedChildCount: 0,
  });
  assertCandidateOnly(observed);
  fixture.focus.ownComposer.querySelector('[role="textbox"]').append(el("br"));
  assert.ok(evaluate(readThreadsZeroTerminal, fixture), "an empty inline lexical line remains empty");
}

function testZeroLayoutAndChildrenRejections() {
  const child = () => postRow({ path: "/@another.reader/post/Child789", author: "another.reader", body: "Existing child", zero: false }).owner;
  for (const [name, change] of [
    ["missing explicit native tail", (f) => f.context.replaceChildren(f.originalPagelet, f.focusPagelet, f.emptyTail)],
    ["missing explicit unlabelled tail", (f) => f.context.replaceChildren(f.originalPagelet, f.focusPagelet, f.tailPagelet)],
    ["unknown pagelet", (f) => { f.tailPagelet.attrs["data-pagelet"] = "threads_unknown_page_7"; }],
    ["numeric substitute for observed literal tail", (f) => { f.tailPagelet.attrs["data-pagelet"] = "threads_post_page_7"; }],
    ["wrong literal native tail", (f) => { f.tailPagelet.attrs["data-pagelet"] = "threads_post_page_{m}"; }],
    ["unbraced native tail", (f) => { f.tailPagelet.attrs["data-pagelet"] = "threads_post_page_n"; }],
    ["duplicate root pagelet", (f) => { f.tailPagelet.attrs["data-pagelet"] = "threads_post_page_0"; }],
    ["duplicate focus pagelet", (f) => { f.tailPagelet.attrs["data-pagelet"] = "threads_post_page_1"; }],
    ["labelled final DIV", (f) => { f.emptyTail.attrs["data-pagelet"] = "threads_post_page_8"; }],
    ["extra nonpagelet context child", (f) => f.context.append(el("div"))],
    ["extra unknown context child", (f) => f.context.append(el("div", { "data-pagelet": "unknown" }))],
    ["context sibling", (f) => f.root.append(el("div"))],
    ["native tail contains text", (f) => f.tailPagelet.append("Unmapped reply")],
    ["unlabelled tail contains text", (f) => f.emptyTail.append("Unmapped reply")],
    ["native tail contains child", (f) => f.tailPagelet.append(child())],
    ["unlabelled tail contains child", (f) => f.emptyTail.append(child())],
    ["inline composer contains child", (f) => f.focus.ownComposer.append(child())],
    ["root pagelet contains child", (f) => f.originalPagelet.append(child())],
    ["empty tail has hidden interactive child", (f) => f.emptyTail.append(el("button", { hidden: "true" }))],
    ["root and focus reversed", (f) => f.context.replaceChildren(f.focusPagelet, f.originalPagelet, f.tailPagelet, f.emptyTail)],
    ["focus nested under different parent", (f) => f.context.replaceChildren(f.originalPagelet, el("div", {}, [f.focusPagelet]), f.tailPagelet, f.emptyTail)],
    ["missing inline editor shell branch", (f) => f.focus.shell.replaceChildren(...f.focus.shell.children.slice(0, 4))],
    ["duplicate inline editor", (f) => f.focus.ownComposer.append(el("div", { role: "textbox", contenteditable: "true", "aria-placeholder": `回覆${expected.author}……` }))],
    ["inline editor already filled", (f) => f.focus.ownComposer.querySelector('[role="textbox"]').append("Existing draft")],
    ["inline editor hidden draft", (f) => f.focus.ownComposer.querySelector('[role="textbox"]').append(el("span", { hidden: "true" }, ["Existing draft"]))],
    ["hidden inline editor", (f) => { f.focus.ownComposer.querySelector('[role="textbox"]').attrs.hidden = "true"; }],
    ["inline editor wrong target", (f) => { f.focus.ownComposer.querySelector('[role="textbox"]').attrs["aria-placeholder"] = "回覆another.reader……"; }],
    ["inline editor not editable", (f) => { f.focus.ownComposer.querySelector('[role="textbox"]').attrs.contenteditable = "false"; }],
  ]) {
    const fixture = zeroFixture(); change(fixture);
    assert.equal(evaluate(readThreadsZeroTerminal, fixture), null, name);
  }
}

function testZeroMarkerPendingAndIdentityRejections() {
  const cases = [
    ["missing target marker", (f) => f.focus.marker.replaceChildren()],
    ["partial marker", (f) => f.focus.marker.replaceChildren("尚無回")],
    ["marker with extra text", (f) => f.focus.marker.append(" except hidden replies")],
    ["hidden marker", (f) => { f.focus.marker.attrs.hidden = "true"; }],
    ["marker has control", (f) => f.focus.marker.append(el("button"))],
    ["duplicate marker", (f) => f.original.marker.append("尚無回覆")],
    ["misplaced marker", (f) => { f.focus.marker.replaceChildren(); f.focus.content.append("尚無回覆"); }],
    ["root busy", (f) => { f.root.attrs["aria-busy"] = "true"; }],
    ["pending status", (f) => f.focus.controls.append(el("div", { role: "status" }))],
    ["pending progress", (f) => f.focus.controls.append(el("div", { role: "progressbar" }))],
    ["busy descendant", (f) => f.focus.controls.append(el("div", { "aria-busy": "true" }))],
    ["wrong root", (f) => { f.original.anchor.attrs.href = "/@example.owner/post/OtherRoot"; }],
    ["wrong target", (f) => { f.focus.anchor.attrs.href = "/@example.reader/post/OtherComment"; }],
    ["native target query", (f) => { f.focus.anchor.attrs.href += "?tracking=1"; }],
    ["foreign target host", (f) => { f.focus.anchor.attrs.href = `https://foreign.example${expected.targetPath}`; }],
    ["hidden target anchor", (f) => { f.focus.anchor.attrs.hidden = "true"; }],
    ["duplicate target time", (f) => f.focus.anchor.append(el("time", { datetime: expected.targetDatetime }, [expected.displayedAt]))],
    ["missing native datetime", (f) => { delete f.focus.time.attrs.datetime; }],
    ["partial native datetime", (f) => { f.focus.time.attrs.datetime = "2026-08-31"; }],
    ["different displayed timestamp", (f) => f.focus.time.replaceChildren("2m")],
  ];
  for (const label of ["載入中", "Loading…", "顯示更多回覆", "查看更多回覆", "載入更多", "更多回覆", "See more replies", "View more replies", "Load more"]) {
    cases.push([`pending/expander ${label}`, (f) => f.focus.controls.append(el("div", { role: "button" }, [label]))]);
  }
  for (const [name, change] of cases) {
    const fixture = zeroFixture(); change(fixture);
    assert.equal(evaluate(readThreadsZeroTerminal, fixture), null, name);
  }
}

function testObservedDialogAndRichBody() {
  const fixture = modalFixture();
  assert.equal(fixture.time.closest("a"), null, "the observed modal TIME has no permalink anchor");
  assert.equal(fixture.card.children[0], fixture.avatar);
  assert.equal(fixture.avatar.tagName, "DIV", "the native avatar branch is a DIV, not the profile link itself");
  assert.equal(fixture.avatar.firstElementChild, fixture.avatarLink);
  assert.equal(fixture.avatarLink.firstElementChild, fixture.avatarImage);
  assert.equal(fixture.root.querySelectorAll(`img[alt="${expected.account}的大頭貼照"]`).length, 2,
    "native own-account avatars occur separately in composer and add-thread branches");
  assert.equal(fixture.composer.contains(fixture.addThreadAvatar), false);
  assert.equal(fixture.time.getAttribute("datetime"), zeroFixture().focus.time.getAttribute("datetime"));
  assert.deepEqual(fixture.bodyBranch.children, [fixture.bodyShell], "the fourth card branch has one native DIV shell");
  assert.equal(fixture.bodyShell.tagName, "DIV");
  assert.deepEqual(fixture.bodyShell.children, [fixture.context, fixture.content]);
  assert.equal(fixture.context.innerText, `正在回覆@${expected.account}`, "observed ancestor context has no inserted space");
  const observed = evaluate(readThreadsSelectedDialog, fixture);
  assert.ok(observed, "observed four-child parent card, nested author avatar and two own-avatar branches must parse");
  assert.notEqual(Object.getPrototypeOf(observed), Object.prototype);
  assert.deepEqual(localJson(observed), {
    author: expected.author, body: expected.body, displayedAt: expected.displayedAt,
    targetDatetime: expected.targetDatetime, ancestorAuthor: expected.account, account: expected.account,
    composerText: "", composerEmpty: true, placeholder: `回覆 ${expected.author}……`, terminal: false,
  });
  assertCandidateOnly(observed);
  const spacedContext = modalFixture();
  spacedContext.context.replaceChildren(` 正在回覆 \n\t@${expected.account} `);
  assert.ok(evaluate(readThreadsSelectedDialog, spacedContext), "normalized whitespace before the exact complete handle is equivalent");
  fixture.textbox.append("Existing unapproved draft");
  const draft = evaluate(readThreadsSelectedDialog, fixture, { ...expected, reply_text: "Caller proposed replacement" });
  assert.equal(draft.composerText, "Existing unapproved draft", "pure observation reports actual text; caller reply cannot replace it");
  assert.equal(draft.composerEmpty, false);
  assertCandidateOnly(draft);
  const rich = modalFixture();
  rich.content.replaceChildren("Cafe\u0301 ", el("img", { alt: "🙂" }), el("br"), el("p", {}, ["第二行"]), el("div", {}, ["Last block"]));
  assert.equal(evaluate(readThreadsSelectedDialog, rich, { ...expected, body: "Café 🙂 第二行 Last block" }).body, "Café 🙂 第二行 Last block");
  rich.textbox.attrs["aria-placeholder"] = `回覆${expected.author}⋯⋯`;
  assert.ok(evaluate(readThreadsSelectedDialog, rich, { ...expected, body: "Café 🙂 第二行 Last block" }), "both supported Chinese ellipsis spellings preserve exact author binding");
  const nestedTime = modalFixture();
  nestedTime.header.replaceChildren(nestedTime.profile);
  nestedTime.header.append(el("div", {}, [el("span", {}, [nestedTime.time])]));
  assert.ok(evaluate(readThreadsSelectedDialog, nestedTime), "native TIME may be nested within the same header without a permalink");
  for (const child of [el("br"), el("img", { alt: "🙂" }), el("span", { hidden: "true" }, ["Hidden draft"])]) {
    const empty = modalFixture(); empty.textbox.append(child);
    assert.equal(evaluate(readThreadsSelectedDialog, empty).composerEmpty, child.tagName === "BR",
      "a blank lexical line is empty; image-only and hidden drafts are not");
  }
}

function testDialogParentAndBodyRejections() {
  for (const [name, change] of [
    ["wrong author avatar href", (f) => { f.avatarLink.attrs.href = "/@another.reader"; }],
    ["wrong author avatar alt", (f) => { f.avatarImage.attrs.alt = "another.reader的大頭貼照"; }],
    ["profile anchor substituted for native avatar DIV", (f) => f.card.replaceChildren(f.avatarLink, f.header, f.connector, f.bodyBranch)],
    ["duplicate nested author profile", (f) => f.avatarLink.append(el("a", { href: `/@${expected.author}` }))],
    ["ambiguous sibling author profile", (f) => f.avatar.append(el("a", { href: "/@another.reader" }))],
    ["duplicate nested author avatar", (f) => f.avatarLink.append(el("div", {}, [el("img", { alt: `${expected.author}的大頭貼照` })]))],
    ["author avatar outside profile anchor", (f) => { f.avatarLink.replaceChildren(); f.avatar.append(f.avatarImage); }],
    ["wrong header author href", (f) => { f.profile.attrs.href = "/@another.reader"; }],
    ["partial author label", (f) => f.profile.replaceChildren("example.read")],
    ["duplicate header profile", (f) => f.header.append(el("a", { href: `/@${expected.author}` }, [expected.author]))],
    ["wrong native datetime", (f) => { f.time.attrs.datetime = "2026-08-31T00:00:01.000Z"; }],
    ["wrong displayed timestamp", (f) => f.time.replaceChildren("2m")],
    ["time inside anchor", (f) => f.header.replaceChildren(f.profile, el("a", { href: expected.targetPath }, [f.time]))],
    ["duplicate time", (f) => f.header.append(el("time", { datetime: expected.targetDatetime }, [expected.displayedAt]))],
    ["hidden time", (f) => { f.time.attrs.hidden = "true"; }],
    ["wrong ancestor", (f) => f.context.replaceChildren("正在回覆 @another.owner")],
    ["ancestor label partial", (f) => f.context.replaceChildren("正在回覆 @example.own")],
    ["ancestor label extra content", (f) => f.context.append(" and another parent")],
    ["ancestor label has extra prefix", (f) => f.context.replaceChildren(`Other text 正在回覆@${expected.account}`)],
    ["ancestor handle contains whitespace", (f) => f.context.replaceChildren("正在回覆@example. owner")],
    ["ancestor context missing at sign", (f) => f.context.replaceChildren(`正在回覆${expected.account}`)],
    ["hidden ancestor suffix", (f) => f.context.append(el("span", { hidden: "true" }, ["Another parent"]))],
    ["aria-hidden ancestor suffix", (f) => f.context.append(el("span", { "aria-hidden": "true" }, ["Another parent"]))],
    ["body is a matching fragment", (f) => f.content.replaceChildren("complete")],
    ["body edited", (f) => f.content.replaceChildren("Useful edited update")],
    ["body has extra text", (f) => f.content.append(" Another sentence")],
    ["body has extra descendant", (f) => f.content.append(el("span", {}, [" Another sentence"]))],
    ["extra body branch", (f) => f.bodyBranch.append(el("div", {}, ["Unobserved body fragment"]))],
    ["extra direct body text", (f) => f.bodyBranch.append("Unobserved body fragment")],
    ["previous direct-two-child body shape", (f) => f.bodyBranch.replaceChildren(f.context, f.content)],
    ["missing body shell", (f) => f.bodyBranch.replaceChildren()],
    ["multiple body shells", (f) => f.bodyBranch.append(el("div"))],
    ["non-DIV body shell", (f) => { f.bodyShell.tagName = "SPAN"; }],
    ["extra wrapping shell", (f) => f.bodyBranch.replaceChildren(el("div", {}, [f.bodyShell]))],
    ["missing shell context", (f) => f.bodyShell.replaceChildren(f.content)],
    ["missing shell body", (f) => f.bodyShell.replaceChildren(f.context)],
    ["extra shell child", (f) => f.bodyShell.append(el("div"))],
    ["extra direct shell text", (f) => f.bodyShell.append("Unobserved body fragment")],
    ["hidden body branch", (f) => { f.bodyBranch.attrs.hidden = "true"; }],
    ["aria-hidden body branch", (f) => { f.bodyBranch.attrs["aria-hidden"] = "true"; }],
    ["hidden body shell", (f) => { f.bodyShell.attrs.hidden = "true"; }],
    ["aria-hidden body shell", (f) => { f.bodyShell.attrs["aria-hidden"] = "true"; }],
    ["hidden ancestor context", (f) => { f.context.attrs.hidden = "true"; }],
    ["aria-hidden ancestor context", (f) => { f.context.attrs["aria-hidden"] = "true"; }],
    ["aria-hidden body node", (f) => { f.content.attrs["aria-hidden"] = "true"; }],
    ["extra direct card text", (f) => f.card.append("Unobserved parent fragment")],
    ["hidden body", (f) => { f.content.attrs.hidden = "true"; }],
    ["hidden body suffix", (f) => f.content.append(el("span", { hidden: "true" }, ["Unobserved suffix"]))],
    ["aria-hidden substantive body", (f) => f.content.replaceChildren(el("span", { "aria-hidden": "true" }, [expected.body]))],
    ["collapsed body", (f) => { f.content.attrs["aria-expanded"] = "false"; }],
    ["collapsed descendant", (f) => f.content.append(el("span", { "aria-expanded": "false" }))],
    ["truncation button", (f) => f.content.append(el("button", {}, ["查看更多"]))],
    ["truncation role button", (f) => f.content.append(el("div", { role: "button" }, ["See more"]))],
    ["connector text", (f) => f.connector.append("Another parent")],
    ["connector interactive node", (f) => f.connector.append(el("div", { role: "button" }))],
    ["extra parent card child", (f) => f.card.append(el("div"))],
    ["duplicate parent card", (f) => f.root.append(modalFixture().card)],
  ]) {
    const fixture = modalFixture(); change(fixture);
    assert.equal(evaluate(readThreadsSelectedDialog, fixture), null, name);
  }
}

function testDialogComposerAndStructureRejections() {
  for (const [name, change] of [
    ["wrong dialog role", (f) => { f.root.attrs.role = "region"; }],
    ["nonmodal dialog", (f) => { f.root.attrs["aria-modal"] = "false"; }],
    ["hidden modal", (f) => { f.root.attrs.hidden = "true"; }],
    ["nested duplicate dialog", (f) => f.root.append(el("div", { role: "dialog" }))],
    ["wrong heading", (f) => f.heading.replaceChildren("New post")],
    ["duplicate heading", (f) => f.root.append(el("h2", {}, ["回覆"]))],
    ["pending status", (f) => f.root.append(el("div", { role: "status" }))],
    ["pending progress", (f) => f.root.append(el("div", { role: "progressbar" }))],
    ["busy descendant", (f) => f.root.append(el("div", { "aria-busy": "true" }))],
    ["busy dialog", (f) => { f.root.attrs["aria-busy"] = "true"; }],
    ["duplicate textbox", (f) => f.composer.append(el("div", { ...f.textbox.attrs }))],
    ["textbox is not a DIV", (f) => { f.textbox.tagName = "TEXTAREA"; }],
    ["noneditable textbox", (f) => { f.textbox.attrs.contenteditable = "false"; }],
    ["nonlexical textbox", (f) => { delete f.textbox.attrs["data-lexical-editor"]; }],
    ["textbox within parent card", (f) => { f.composer.replaceChildren(f.ownAvatar, f.ownLabel); f.connector.append(f.textbox); }],
    ["wrong placeholder author", (f) => { f.textbox.attrs["aria-placeholder"] = "回覆 another.reader……"; }],
    ["partial placeholder author", (f) => { f.textbox.attrs["aria-placeholder"] = "回覆 example.read……"; }],
    ["missing placeholder", (f) => { delete f.textbox.attrs["aria-placeholder"]; }],
    ["partial ellipsis", (f) => { f.textbox.attrs["aria-placeholder"] = `回覆 ${expected.author}…`; }],
    ["composer avatar account mismatch", (f) => { f.ownAvatar.attrs.alt = "another.owner的大頭貼照"; }],
    ["add-thread avatar account mismatch", (f) => { f.addThreadAvatar.attrs.alt = "another.owner的大頭貼照"; }],
    ["malformed third own avatar in composer", (f) => f.composer.append(el("img", { alt: `${expected.account}的大頭貼照` }))],
    ["malformed nested extra own avatar", (f) => f.addThreadBranch.append(el("div", {}, [el("img", { alt: `${expected.account}的大頭貼照` })]))],
    ["missing composer avatar", (f) => f.composer.replaceChildren(f.ownLabel, f.textbox)],
    ["missing add-thread avatar", (f) => f.addThreadBranch.replaceChildren()],
    ["both own avatars in composer branch", (f) => { f.addThreadBranch.replaceChildren(); f.composer.append(f.addThreadAvatar); }],
    ["partial own account text", (f) => f.ownLabel.replaceChildren("example.own")],
    ["own account is only a prefix", (f) => f.ownLabel.replaceChildren("example.owner.other")],
    ["duplicate own account label", (f) => f.composer.append(el("span", {}, [expected.account]))],
    ["wrong own account text", (f) => f.ownLabel.replaceChildren("another.owner")],
    ["foreign own-composer profile", (f) => f.composer.append(el("a", { href: "/@another.owner" }))],
    ["own composer context includes parent card", (f) => { f.root.replaceChildren(f.heading, f.composer, f.submit); f.composer.append(f.card); }],
    ["missing submit", (f) => f.submit.replaceChildren("Other action")],
    ["duplicate submit", (f) => f.root.append(el("button", {}, ["發佈"]))],
    ["submit inside parent card", (f) => { f.root.replaceChildren(f.heading, f.card, f.composer); f.connector.append(f.submit); }],
  ]) {
    const fixture = modalFixture(); change(fixture);
    assert.equal(evaluate(readThreadsSelectedDialog, fixture), null, name);
  }
}


export function runPureReaderCases() {
  testObservedZeroTerminal();
  testZeroLayoutAndChildrenRejections();
  testZeroMarkerPendingAndIdentityRejections();
  testObservedDialogAndRichBody();
  testDialogParentAndBodyRejections();
  testDialogComposerAndStructureRejections();
}
