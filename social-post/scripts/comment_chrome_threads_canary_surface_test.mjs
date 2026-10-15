/** Anonymous Threads preparation fixtures; no browser, network or submission. */
import assert from "node:assert/strict";
import {
  readThreadsZeroTerminal, readThreadsSelectedDialog as reexportedSelectedDialog,
  inspectThreadsCanarySurface, prepareThreadsCanaryReply, revalidateThreadsSelection, inspectThreadsCanaryResult,
} from "./comment_chrome_threads_canary_surface.mjs";
import { readThreadsSelectedDialog } from "./comment_chrome_threads_modal_reader.mjs";
import { getCommentCuaBrowser, installCommentCuaRuntime } from "./comment_cua_runtime.mjs";

import { expected, calls, el, postRow, zeroFixture, modalFixture, evaluate, localJson, action, Locator, sourceFixture, resultFixture } from "./comment_chrome_threads_dom_fixtures_test.mjs";
import { runPureReaderCases } from "./comment_chrome_threads_canary_reader_cases_test.mjs";

assert.equal(reexportedSelectedDialog, readThreadsSelectedDialog, "production surface preserves the independently importable pure callback");

function assertIncompleteCandidate(result) {
  assert.equal(result.complete, false);
  assert.equal(result.exhaustiveThread, result.zeroThreadTerminalCandidate);
  assert.equal(result.absence_proven, false);
  assert.equal(Object.hasOwn(result, "verifiedNewReply"), false);
  assert.equal(Object.hasOwn(result, "replyPermalink"), false);
}

async function testSourceOwnedPreparationCandidates() {
  const readOnly = sourceFixture();
  const first = await inspectThreadsCanarySurface(readOnly.tab, action);
  const second = await inspectThreadsCanarySurface(readOnly.tab, action);
  assertIncompleteCandidate(first); assertIncompleteCandidate(second);
  assert.equal(first.zeroThreadTerminalCandidate, false);
  assert.equal(second.zeroThreadTerminalCandidate, true);
  assert.equal(readOnly.clicks, 0);
  assert.equal(second.replyExhaustionCandidate.kind, "threads_explicit_zero");
  assert.equal(second.replyExhaustionCandidate.observed_count, 0);
  const fixture = sourceFixture();
  assert.equal(fixture.tab.playwright.fill, undefined);
  assert.equal(fixture.tab.dom_cua, undefined);
  const selected = await prepareThreadsCanaryReply(fixture.tab, action);
  assertIncompleteCandidate(selected);
  assert.equal(selected.selectedParentCandidate, true);
  assert.equal(selected.selection.candidate_only, true);
  assert.equal(selected.selection.trigger_binding.comment_permalink, expected.commentUrl);
  assert.equal(Object.hasOwn(selected.selection, "composer_node_id"), false);
  assert.equal(selected.composerEmpty, true);
  assert.equal(fixture.clicks, 1);
  assert.ok(fixture.callbacks.includes("readThreadsNativeColumn") && fixture.callbacks.includes("readThreadsSelectedDialog"),
    "wrapper executes the real source reader and modal callbacks, never canned valid evidence");
  assert.ok(fixture.waits.includes(10000));
  await assert.rejects(prepareThreadsCanaryReply(fixture.tab, action), /already attempted|invalidated|changed/u);
  assert.equal(fixture.clicks, 1);
}

async function testSourceOwnedPreparationRejections() {
  const preexisting = sourceFixture({ preexistingDialog: true });
  await assert.rejects(prepareThreadsCanaryReply(preexisting.tab, action), /pre-existing.*no source selection/u);
  assert.equal(preexisting.clicks, 0);
  const drift = sourceFixture({ onEvaluate: (name, fixture) => {
    if (name === "readThreadsNativeColumn") fixture.url = "https://www.threads.com/@another.reader/post/OtherComment";
  } });
  await assert.rejects(prepareThreadsCanaryReply(drift.tab, action), /URL changed/u);
  assert.equal(drift.clicks, 0);
  const ambiguous = sourceFixture({ ambiguousClick: true });
  await assert.rejects(prepareThreadsCanaryReply(ambiguous.tab, action), /ambiguous anonymous/u);
  await assert.rejects(prepareThreadsCanaryReply(ambiguous.tab, action), /changed|invalidated|already attempted/u);
  assert.equal(ambiguous.clicks, 1);
  const wrongDialog = sourceFixture();
  wrongDialog.modal.content.replaceChildren("Another comment's body");
  await assert.rejects(prepareThreadsCanaryReply(wrongDialog.tab, action), /selected dialog differs/u);
  assert.equal(wrongDialog.clicks, 1);
  const draft = sourceFixture();
  draft.modal.textbox.append("Existing unapproved text");
  await assert.rejects(prepareThreadsCanaryReply(draft.tab, action), /composer differs|composer is not empty/u);
  assert.equal(draft.clicks, 1);
  const changedAction = sourceFixture();
  await inspectThreadsCanarySurface(changedAction.tab, action);
  await assert.rejects(prepareThreadsCanaryReply(changedAction.tab, { ...action, action_id: "another-action" }), /UI binding.*changed/u);
  assert.equal(changedAction.clicks, 0);
  const changedDuringTerminal = sourceFixture({ onEvaluate: (name, fixture) => {
    if (name === "readThreadsZeroTerminal") fixture.zero.focus.content.replaceChildren("Edited native body");
  } });
  await assert.rejects(prepareThreadsCanaryReply(changedDuringTerminal.tab, action), /changed during zero-thread/u);
  assert.equal(changedDuringTerminal.clicks, 0);
  const disabled = sourceFixture();
  disabled.zero.focus.reply.attrs.disabled = "true";
  await assert.rejects(prepareThreadsCanaryReply(disabled.tab, action), /trigger is not enabled/u);
  assert.equal(disabled.clicks, 0);
}

async function testFinalBoundSurfaceDriftRejections() {
  for (const [name, change, message] of [
    ["URL drift", (f) => { f.url = "https://www.threads.com/@another.reader/post/OtherComment"; }, /target URL changed/u],
    ["account drift", (f) => { f.account.attrs.href = "/@another.owner"; }, /active account changed/u],
    ["native whole-body drift", (f) => f.zero.focus.content.replaceChildren("Edited native body"), /exact native parent|native target changed/u],
    ["selected modal body drift", (f) => f.modal.content.replaceChildren("Edited modal body"), /selected dialog.*changed/u],
  ]) {
    const fixture = sourceFixture();
    const prepared = await prepareThreadsCanaryReply(fixture.tab, action);
    assert.equal(prepared.selectedParentCandidate, true);
    const before = { submitLookups: fixture.submitLookups };
    let changed = false;
    fixture.afterSubmitLookup = (f) => {
      assert.equal(changed, false, `${name}: one final lookup boundary, not a repeated retry`);
      changed = true;
      change(f);
    };
    // Inspect directly: a later prepare() stabilization pass must not hide a
    // missing final read in the single inspection returned to the caller.
    await assert.rejects(inspectThreadsCanarySurface(fixture.tab, action), message, name);
    assert.equal(changed, true, `${name}: regression reached the post-bind lookup boundary`);
    assert.equal(fixture.submitLookups, before.submitLookups + 1);
    assert.equal(fixture.clicks, 1, `${name}: drift never reopens or submits the dialog`);
  }
}

async function testPositiveChildReadback() {
  const fixture = resultFixture();
  const confirmed = await inspectThreadsCanaryResult(fixture.tab, action);
  assert.equal(confirmed.verifiedNewReply, true);
  assert.equal(confirmed.replyPermalink, fixture.childUrl);
  assert.equal(confirmed.observedUrl, expected.commentUrl);
  assert.equal(confirmed.absence_verified, false);
  assert.equal(confirmed.complete, false);
  assert.deepEqual(fixture.navigations, [fixture.childUrl, expected.commentUrl]);
  assert.equal(fixture.clicks, 0);

  const delayed = resultFixture({ delayedRegion: true });
  const delayedResult = await inspectThreadsCanaryResult(delayed.tab, action);
  assert.equal(delayedResult.verifiedNewReply, true);
  assert.equal(delayedResult.replyPermalink, delayed.childUrl);
  assert.deepEqual(delayed.regionReadiness, [delayed.childUrl, expected.commentUrl],
    "both child navigation and parent restoration await delayed visible regions before uniqueness checks");
  assert.equal(delayed.clicks, 0);
  const delayedWrongParent = resultFixture({ delayedRegion: true });
  delayedWrongParent.childOriginal.anchor.attrs.href = "/@other.reader/post/WrongParent";
  await assert.rejects(inspectThreadsCanaryResult(delayedWrongParent.tab, action), /native parent context/u,
    "waiting for region visibility never relaxes the immediate-parent check");
  assert.equal(delayedWrongParent.url, expected.commentUrl);
  assert.equal(delayedWrongParent.clicks, 0);

  for (const [name, change, error] of [
    ["wrong immediate parent", (f) => { f.childOriginal.anchor.attrs.href = "/@other.reader/post/WrongParent"; }, /native parent context/u],
    ["wrong original ancestor", (f) => { f.childRoot.anchor.attrs.href = "/@example.owner/post/WrongRoot"; }, /native parent context/u],
    ["reversed context rows", (f) => f.childContext.replaceChildren(f.childParentRow, f.childRootRow), /native parent context/u],
    ["missing original row", (f) => f.childContext.replaceChildren(f.childParentRow), /native parent context/u],
    ["extra context row", (f) => f.childContext.append(el("div")), /native parent context/u],
    ["hidden original row", (f) => { f.childRootRow.attrs.hidden = "true"; }, /native parent context/u],
    ["hidden immediate parent time", (f) => { f.childOriginal.time.attrs.hidden = "true"; }, /native parent context/u],
    ["nested parent decoy", (f) => f.childParentRow.replaceChildren(el("div", {}, [f.childOriginal.owner])), /native parent context/u],
    ["nested extra owner", (f) => f.childOriginal.owner.append(el("div", { "data-pressable-container": "true" })), /native parent context/u],
    ["extra native time", (f) => f.childOriginal.header.append(el("time", {}, ["2m"])), /native parent context/u],
    ["wrong child author", (f) => { f.childFocus.profile.attrs.href = "/@another.owner"; }, /native parent context/u],
    ["wrong whole reply body", (f) => f.childFocus.content.replaceChildren("Unapproved reply text"), /approved text and immediate parent/u],
    ["child URL drift", (f) => { f.onEvaluate = (callback, state) => {
      if (state.scene === "child" && callback === "readThreadsNativeColumn") state.url = "https://www.threads.com/@another.owner/post/WrongURL";
    }; }, /URL changed/u],
  ]) {
    const changed = resultFixture();
    change(changed);
    await assert.rejects(inspectThreadsCanaryResult(changed.tab, action), error, name);
    assert.equal(changed.url, expected.commentUrl, `${name}: restore original parent after unknown result`);
    assert.equal(changed.clicks, 0, `${name}: result inspection never submits`);
  }

  const zero = sourceFixture();
  await assert.rejects(inspectThreadsCanaryResult(zero.tab, action), /no verified parent with a positive native reply count/u);
  assert.equal(zero.clicks, 0);
  const absent = resultFixture();
  absent.zero.tailPagelet.replaceChildren();
  await assert.rejects(inspectThreadsCanaryResult(absent.tab, action), /no unique own child candidate/u);
  assert.deepEqual(absent.navigations, [], "no candidate does not navigate or imply absence");

  const finalDrift = resultFixture();
  finalDrift.onEvaluate = (callback, state) => {
    if (callback === "discoverThreadsOwnChildLinks" && ++state.discoveryReads === 2) {
      state.url = "https://www.threads.com/@another.owner/post/WrongURL";
    }
  };
  await assert.rejects(inspectThreadsCanaryResult(finalDrift.tab, action), /URL changed|context changed/u,
    "URL drift during the final candidate read must not return success");
}

async function testCuaChildUsesNewOwnedTabWithoutParentNavigation() {
  let active;
  let sequence = 0;
  const browserId = "anonymous-cua-browser";
  const cua = {
    async getState() {
      active.stateReads += 1;
      return { browsers: [{ id: browserId, family: "chrome", type: "extension",
        metadata: { extensionInstanceId: active.extension ?? "anonymous-cua-extension" },
        tabs: [
          { id: active.parent.tab.id, url: active.parent.url },
          { id: `existing-child-${sequence}`, url: active.parent.childUrl },
          ...(active.child && !active.child.closed ? [{ id: active.child.tab.id, url: active.child.url }] : []),
        ],
      }] };
    },
    async getTab(id, options) {
      active.gets.push(id);
      assert.equal(options.browser, browserId);
      assert.equal(id, active.parent.tab.id, "result inspection cannot borrow an already listed child");
      return active.parent.tab;
    },
    async createBrowserTab(browser, url, options) {
      active.creates.push(url);
      assert.equal(browser, "chrome");
      assert.equal(url, active.parent.childUrl, "only the exact own-child link discovered in native DOM may be opened");
      assert.equal(options.sessionName, "💬 Social Post");
      if (active.creationError) throw active.creationError;
      const parent = active.parent;
      const child = { ...parent, url, scene: "child", document: parent.childDocument,
        waits: [], callbacks: [], closed: false, closes: 0,
        onEvaluate: (name, state) => active.onChildEvaluate?.(name, state) };
      child.tab = { id: `created-child-${sequence}`, url: async () => child.url,
        playwright: new Locator(child, [child.document]),
        goto: async () => { active.forbidden.push("child goto"); throw new Error("CUA result never navigates child"); },
        close: async () => { child.closes += 1; child.closed = true; },
      };
      active.child = child;
      return child.tab;
    },
  };
  function nextCase() {
    sequence += 1;
    const parent = resultFixture();
    parent.tab.id = `cua-parent-${sequence}`;
    const test = { parent, child: null, gets: [], creates: [], stateReads: 0, forbidden: [] };
    parent.tab.goto = async () => { test.forbidden.push("parent goto"); throw new Error("CUA result must preserve parent navigation"); };
    parent.tab.close = async () => { test.forbidden.push("parent close"); throw new Error("CUA result cannot close parent"); };
    active = test;
    return test;
  }
  async function inspect(test) {
    active = test;
    const parent = await getCommentCuaBrowser().tabs.get(test.parent.tab.id);
    return inspectThreadsCanaryResult(parent, action);
  }
  function assertReadOnlyLifecycle(test, created = true) {
    assert.deepEqual(test.forbidden, []);
    assert.deepEqual(test.gets, [test.parent.tab.id], "no get/reclaim on an existing child tab");
    assert.equal(test.creates.length, created ? 1 : 0, "no creation or navigation retries");
    assert.equal(test.parent.clicks, 0);
    assert.deepEqual(test.parent.navigations, []);
    if (test.child) {
      assert.equal(test.child.closes, 1, "close only the one owned child tab, including on failed proof");
      assert.equal(test.child.clicks, 0);
    }
  }
  const positive = nextCase();
  await installCommentCuaRuntime(cua, { browserId });
  const observed = await inspect(positive);
  assert.equal(observed.verifiedNewReply, true);
  assert.equal(observed.replyPermalink, positive.parent.childUrl);
  assert.equal(observed.observedUrl, expected.commentUrl);
  assert.equal(observed.complete, false);
  assert.equal(observed.absence_verified, false);
  assert.ok(positive.stateReads >= 12, "fresh browser ownership surrounds both original-parent and child inspections");
  assert.equal(positive.child.callbacks.filter((name) => name === "readThreadsNativeColumn").length, 2);
  assert.equal(positive.parent.callbacks.filter((name) => name === "readThreadsNativeColumn").length, 3,
    "the unchanged original parent is read initially and twice after the child proof");
  assertReadOnlyLifecycle(positive);

  for (const [name, mutate, error] of [
    ["wrong immediate parent", (t) => { t.parent.childOriginal.anchor.attrs.href = "/@other.reader/post/WrongParent"; }, /native parent context/u],
    ["wrong original ancestor", (t) => { t.parent.childRoot.anchor.attrs.href = "/@example.owner/post/WrongRoot"; }, /native parent context/u],
    ["reversed ancestors", (t) => t.parent.childContext.replaceChildren(t.parent.childParentRow, t.parent.childRootRow), /native parent context/u],
    ["wrong own author", (t) => { t.parent.childFocus.profile.attrs.href = "/@another.owner"; }, /native parent context/u],
    ["wrong full body", (t) => t.parent.childFocus.content.replaceChildren("Not the approved reply"), /approved text and immediate parent/u],
    ["child URL drift", (t) => { t.onChildEvaluate = (name, state) => {
      if (name === "readThreadsNativeColumn") state.url = "https://www.threads.com/@another.owner/post/WrongURL";
    }; }, /URL changed/u],
    ["child ID drift", (t) => { t.onChildEvaluate = (name, state) => {
      if (name === "readThreadsNativeColumn") state.tab.id = `changed-child-${sequence}`;
    }; }, /tab|identity/u],
    ["child retained handle drift", (t) => { t.onChildEvaluate = (name, state) => {
      if (name === "readThreadsNativeColumn") state.tab.url = async () => state.url;
    }; }, /retained CUA Tab handle changed/u],
    ["browser extension drift", (t) => { t.onChildEvaluate = (name) => {
      if (name === "readThreadsNativeColumn") t.extension = "changed-extension";
    }; }, /extensionInstanceId changed/u],
    ["parent URL drift while child inspected", (t) => { t.onChildEvaluate = (name) => {
      if (name === "readThreadsNativeColumn") t.parent.url = "https://www.threads.com/@another.owner/post/WrongURL";
    }; }, /URL differs|URL changed/u],
    ["final parent body drift", (t) => { t.parent.onEvaluate = (name, state) => {
      if (name === "discoverThreadsOwnChildLinks" && ++state.discoveryReads === 2) state.zero.focus.content.replaceChildren("Changed parent body");
    }; }, /verified parent/u],
    ["final parent URL drift", (t) => { t.parent.onEvaluate = (name, state) => {
      if (name === "discoverThreadsOwnChildLinks" && ++state.discoveryReads === 2) state.url = "https://www.threads.com/@another.owner/post/WrongURL";
    }; }, /URL changed/u],
  ]) {
    const test = nextCase(); mutate(test);
    await assert.rejects(inspect(test), error, name);
    assertReadOnlyLifecycle(test);
  }
  const missing = nextCase();
  missing.parent.zero.tailPagelet.replaceChildren();
  await assert.rejects(inspect(missing), /no unique own child candidate/u);
  assertReadOnlyLifecycle(missing, false);

  const creationFailed = nextCase();
  creationFailed.creationError = new Error("documented CUA creation failed");
  await assert.rejects(inspect(creationFailed), (error) => error === creationFailed.creationError);
  assertReadOnlyLifecycle(creationFailed);
  assert.equal(creationFailed.child, null, "creation failure cannot fall back to navigating the parent");
}

runPureReaderCases();
await testSourceOwnedPreparationCandidates();
await testSourceOwnedPreparationRejections();
await testFinalBoundSurfaceDriftRejections();
await testPositiveChildReadback();
await testCuaChildUsesNewOwnedTabWithoutParentNavigation();
const revalidation = sourceFixture();
const prepared = await prepareThreadsCanaryReply(revalidation.tab, action);
revalidation.modal.textbox.append(action.reply_text);
const ready = await revalidateThreadsSelection(revalidation.tab, action);
assert.equal(ready.selection_digest, prepared.selection_digest);
assert.equal(ready.composerText, action.reply_text);
revalidation.modal.textbox.attrs.hidden = "true";
await assert.rejects(revalidateThreadsSelection(revalidation.tab, action), /selected dialog differs/u);
assert.equal(revalidation.clicks, 1);
assert.ok(calls.zero >= 45 && calls.modal >= 50, "real callback execution covers anonymous positive and negative DOM shapes");
assert.equal(calls.clicks, 0);
assert.equal(calls.fills, 0);
console.log("PASS Threads source-selected empty preparation and native DOM readers (anonymous; no browser submission)");
