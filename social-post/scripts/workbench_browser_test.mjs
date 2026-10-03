// Optional dev-only actual Chromium journey. No user's Chrome or real social data.
import assert from "node:assert/strict";
import { spawn, spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import { createReadStream, mkdtempSync, mkdirSync, readFileSync, realpathSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve, basename } from "node:path";
import { fileURLToPath } from "node:url";
import { createRequire } from "node:module";

const args = process.argv.slice(2);
const options = {};
for (let index = 0; index < args.length; index += 2) options[args[index]] = args[index + 1];
for (const key of ["--python", "--playwright", "--output"]) assert.ok(options[key], key + " is required");
const require = createRequire(import.meta.url);
const { chromium } = require(resolve(options["--playwright"]));
const skillRoot = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const output = resolve(options["--output"]);
mkdirSync(output, { recursive: true });
const tempBase = realpathSync(tmpdir());
const workspace = mkdtempSync(join(tempBase, "social-workbench-browser-"));
mkdirSync(join(workspace, "references/formulas"), { recursive: true });
writeFileSync(join(workspace, "references/formulas/F01.md"), "# F1 Fictional formula\n\nFictional body.");
writeFileSync(join(workspace, "references/formulas/F06.md"), "# F6 | Mode B\n\n## F6a Invitation\n\n## F6b Own ship\n[Result]\n[Process]\n[Use]\n[One action]\n");
writeFileSync(join(workspace, "voice_quick.md"), "Fictional author used only by this isolated test; plain factual voice.\n");
mkdirSync(join(workspace, "data"));
writeFileSync(join(workspace, "data/writing_policy.json"), JSON.stringify({ schema_version: 1, no_emoji: true,
  plain_text: true, formula_checks: { F06b: { paragraphs: 4, no_links: true, no_lists: true,
    exclamations_first_only: true, bare_endings_after_first: true } } }));
function governance(action, file) {
  const command = ["-B", join(skillRoot, "scripts/social_governance.py"), action, "--root", workspace, "--write"];
  if (file) command.push("--input", file);
  const result = spawnSync(options["--python"], command, { encoding: "utf8", shell: false,
    env: { SystemRoot: process.env.SystemRoot, TEMP: tmpdir(), TMP: tmpdir(), PYTHONUTF8: "1" } });
  assert.equal(result.status, 0, result.stdout + result.stderr);
  return JSON.parse(result.stdout);
}
const baseline = governance("bootstrap");
writeFileSync(join(workspace, "external.json"), JSON.stringify({ reference_id: "fictional-external",
  content_id: "one-fictional-video", platform: "instagram", media_family: "video", caption: "Fictional external caption",
  published_at: null, captured_at: null, metrics: { likes: 100 }, metric_qualifiers: { likes: "exact" },
  evidence: [{ source: "explicitly fictional renderer control" }] }));
governance("record-reference", join(workspace, "external.json"));
writeFileSync(join(workspace, "proposal.json"), JSON.stringify({ title: "Fictional reviewed change",
  target: "references/formulas/F01.md", replacement_text: "# F1 Fictional formula\n\nReviewed fictional body.",
  scope: { platform: "instagram", media_family: "video" }, evidence_ids: ["fictional-external"],
  reason: "Isolated review-flow test, not a real author update." }));
const candidate = governance("propose", join(workspace, "proposal.json"));
const child = spawn(options["--python"], ["-B", join(skillRoot, "scripts", "workbench.py"),
  "--root", workspace, "--port", options["--port"] || "0"], {
  shell: false, stdio: ["ignore", "pipe", "pipe"],
  env: { SystemRoot: process.env.SystemRoot, TEMP: tmpdir(), TMP: tmpdir(), PYTHONUTF8: "1" },
});
let stdout = "", stderr = "", browser;
child.stdout.on("data", data => { stdout = (stdout + data).slice(-8192); });
child.stderr.on("data", data => { stderr = (stderr + data).slice(-8192); });
const checks = [];
const pageErrors = [];
const externalRequests = [];

async function until(predicate, timeout = 10000) {
  const deadline = Date.now() + timeout;
  while (!predicate()) {
    assert.ok(Date.now() < deadline, "readiness timeout");
    await new Promise(done => setTimeout(done, 50));
  }
}
async function hashFile(path) {
  const hash = createHash("sha256");
  for await (const chunk of createReadStream(path)) hash.update(chunk);
  return hash.digest("hex");
}

try {
  await until(() => /http:\/\/127\.0\.0\.1:\d+/.test(stdout) || child.exitCode !== null);
  assert.equal(child.exitCode, null, "server startup: " + stderr);
  const origin = stdout.match(/http:\/\/127\.0\.0\.1:\d+/)[0];
  browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
  const page = await context.newPage();
  page.on("pageerror", error => pageErrors.push(error.message));
  page.on("request", request => { if (!request.url().startsWith(origin + "/")) externalRequests.push(request.url()); });
  await page.goto(origin);
  await page.getByRole("heading", { name: "你想完成哪件事？" }).waitFor();
  for (const [width, height] of [[1440, 1000], [1024, 900], [390, 844]]) {
    await page.setViewportSize({ width, height });
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true, "horizontal overflow");
    assert.equal(await page.locator(".mode-card").count(), 6);
    assert.equal(await page.locator(".format-tile").count(), 3);
    assert.equal(await page.evaluate(() => /\p{Extended_Pictographic}/u.test(document.body.innerText)), false);
    await page.screenshot({ path: join(output, "home-" + width + ".png"), fullPage: true });
    checks.push("responsive_home_" + width);
  }
  await page.setViewportSize({ width: 1440, height: 1000 });
  for (const id of ["P0", "P1", "P2", "P3", "P4", "P5"]) {
    await page.locator('#nav a[href="#' + id + '"]').click();
    await page.waitForFunction(current => document.querySelector(".workflow-head .eyebrow")
      ?.textContent.startsWith(current + " / "), id);
    assert.match(await page.locator(".workflow-head .eyebrow").first().innerText(), new RegExp(id));
    if (["P0", "P1", "P2", "P5"].includes(id)) {
      await page.getByLabel(id === "P1" ? "這批樣本的用途" : "題材或任務主題").fill("Fictional workbench task");
      await page.getByLabel(id === "P1" ? "完整原文與來源" : id === "P5" ? "原留言與脈絡" : "真實事實與補充素材")
        .fill("Complete fictional original material.");
      if (id === "P2") await page.getByLabel("創作公式 F").selectOption("F01");
      const action = { P0: "建立規劃任務", P1: "建立學習任務", P2: "建立撰稿任務", P5: "建立回覆任務" }[id];
      await page.getByRole("button", { name: action, exact: true }).click();
      await page.getByText("任務已建立，尚未執行 AI。下一步：複製到 Codex／Claude Code。", { exact: true }).waitFor();
      assert.match(await page.locator(".task-output").last().innerText(), /使用 \$social-post/);
      if (id === "P2") assert.match(await page.locator(".task-output").last().innerText(), /references\/formulas\/F01\.md/);
      const downloadPromise = page.waitForEvent("download");
      await page.getByRole("button", { name: "下載任務", exact: true }).click();
      const download = await downloadPromise;
      await download.saveAs(join(output, "task-" + id + ".txt"));
      assert.match(readFileSync(join(output, "task-" + id + ".txt"), "utf8"), new RegExp("工作流程：" + id));
    }
    checks.push("mode_" + id);
  }
  await page.locator('#nav a[href="#P2"]').click();
  await page.waitForFunction(() => document.querySelector(".workflow-head .eyebrow")?.textContent.startsWith("P2 / "));
  await page.getByLabel("題材或任務主題").fill("Fictional saved draft");
  await page.getByRole("button", { name: "Mode C 觀點復盤", exact: true }).click();
  const original = "  A fictional draft!\n\nOriginal spacing.\n";
  await page.getByLabel("貼文正文").fill(original);
  await page.getByRole("button", { name: "保存私人草稿", exact: true }).click();
  await page.locator(".draft-item").filter({ hasText: "Fictional saved draft" }).waitFor();
  await page.reload();
  await page.locator(".draft-item").filter({ hasText: "Fictional saved draft" }).click();
  await page.getByLabel("題材或任務主題").waitFor();
  await page.waitForFunction(() => document.querySelector('textarea[name="draft"]')?.value.includes("Original spacing."));
  assert.equal(await page.getByLabel("貼文正文").inputValue(), original);
  assert.equal(await page.getByRole("button", { name: "Mode C 觀點復盤", exact: true }).getAttribute("aria-pressed"), "true");
  await page.getByRole("button", { name: "查看黑底白字版型", exact: true }).click();
  await page.locator(".black-preview").waitFor({ state: "visible" });
  assert.equal(await page.locator(".black-preview").textContent(), original);
  await page.getByLabel("貼文正文").fill(original + "Unsaved change.");
  page.once("dialog", dialog => dialog.dismiss());
  await page.locator('#nav a[href="#P0"]').click();
  await page.waitForFunction(() => location.hash === "#P2");
  assert.equal(await page.getByLabel("貼文正文").inputValue(), original + "Unsaved change.");
  await page.getByLabel("貼文正文").fill(original);
  checks.push("unsaved_navigation_cancel_preserves_original", "formula_handoff_uses_installed_reference");
  await page.screenshot({ path: join(output, "editor-desktop.png"), fullPage: true });
  await page.setViewportSize({ width: 390, height: 844 });
  assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
  await page.screenshot({ path: join(output, "editor-mobile.png"), fullPage: true });
  checks.push("draft_save_reload_reopen_exact_text_and_mode", "black_card_preview", "responsive_editor_390");
  await page.getByLabel("創作公式 F").selectOption("F06b");
  await page.getByRole("button", { name: "Mode B 成果發布", exact: true }).click();
  await page.getByLabel("貼文正文").fill("A result!!\n\nA real process\n\nA use case");
  await page.getByRole("button", { name: "核對正式 F 契約", exact: true }).click();
  await page.getByText("結構檢查未通過：wrong_paragraph_count", { exact: true }).waitFor();
  await page.getByLabel("貼文正文").fill("A result!!\n\nA real process\n\nA use case\n\nOne action");
  await page.getByRole("button", { name: "核對正式 F 契約", exact: true }).click();
  await page.getByText("結構檢查通過；仍需主機閱讀完整 F 正文，審查語義順序、語氣與事實。", { exact: true }).waitFor();
  checks.push("f6_variant_selector", "f6_structural_negative_and_positive", "semantic_review_not_falsely_passed");
  await page.getByLabel("貼文正文").fill(original);
  await page.getByRole("button", { name: "Mode C 觀點復盤", exact: true }).click();
  await page.locator('#nav a[href="#learning"]').click();
  await page.getByRole("heading", { name: "資料分區與規則審核", exact: true }).waitFor();
  assert.equal(await page.locator(".mode-grid .comparison-card").count(), 10);
  await page.screenshot({ path: join(output, "learning-mobile.png"), fullPage: true });
  assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
  assert.equal(JSON.parse(readFileSync(join(workspace, "data/author_contract.json"), "utf8")).revision, baseline.revision);
  await page.getByLabel("審核理由").fill("Reviewed this fictional diff, scope and single-sample limits for the renderer test.");
  page.once("dialog", dialog => dialog.accept());
  await page.getByRole("button", { name: "批准此版本", exact: true }).click();
  await page.getByRole("button", { name: "啟用已批准更新", exact: true }).waitFor();
  assert.equal(JSON.parse(readFileSync(join(workspace, "data/author_contract.json"), "utf8")).revision, baseline.revision);
  page.once("dialog", dialog => dialog.accept());
  await page.getByRole("button", { name: "啟用已批准更新", exact: true }).click();
  await page.getByText("instagram / video / activated", { exact: true }).waitFor();
  const active = JSON.parse(readFileSync(join(workspace, "data/author_contract.json"), "utf8"));
  const version = JSON.parse(readFileSync(join(workspace, "data/author_contracts", active.revision + ".json"), "utf8"));
  assert.notEqual(active.revision, baseline.revision);
  assert.equal(version.parent_revision, baseline.revision);
  assert.equal(version.proposal_digest, candidate.proposal_digest);
  assert.equal(readFileSync(join(workspace, "references/formulas/F01.md"), "utf8"), "# F1 Fictional formula\n\nFictional body.");
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.screenshot({ path: join(output, "learning-desktop.png"), fullPage: true });
  checks.push("ten_media_channels", "responsive_learning_390", "approve_does_not_activate", "explicit_scoped_activation_keeps_original");
  await page.locator('#nav a[href="#P3"]').click();
  await page.waitForFunction(() => document.querySelector(".workflow-head .eyebrow")?.textContent.startsWith("P3 / "));
  await page.getByLabel("Outcome JSON", { exact: true }).fill('{"snapshot":{},"snapshot":{}}');
  await page.getByRole("button", { name: "驗證並預覽", exact: true }).click();
  await page.getByRole("status").filter({ hasText: "資料格式不正確" }).first().waitFor();
  assert.equal(await page.getByRole("button", { name: "確認追加到本機資料庫", exact: true }).isDisabled(), true);
  await page.getByRole("button", { name: "載入虛構示例", exact: true }).click();
  await page.waitForFunction(() => document.querySelector('textarea[name="bundle"]')?.value.includes("fictional-workbench-example"));
  await page.getByRole("button", { name: "驗證並預覽", exact: true }).click();
  const commit = page.getByRole("button", { name: "確認追加到本機資料庫", exact: true });
  await page.waitForFunction(() => [...document.querySelectorAll("button")].some(button =>
    button.textContent === "確認追加到本機資料庫" && !button.disabled));
  assert.equal(parse_json_count(), 0);
  await commit.click();
  await page.getByText("已追加保存。原始歷史保留；未發布到任何社群平台。", { exact: true }).waitFor();
  assert.equal(await commit.isDisabled(), true);
  assert.equal(parse_json_count(), 1);
  checks.push("invalid_import_blocked", "preview_no_write", "explicit_commit_and_replay_control");
  await page.locator('#nav a[href="#P4"]').click();
  await page.waitForFunction(() => document.querySelector(".workflow-head .eyebrow")?.textContent.startsWith("P4 / "));
  await page.getByLabel("內容類型").fill("text");
  await page.getByLabel("版型／發布表面").fill("text_feed");
  await page.getByRole("button", { name: "讀取可比案例", exact: true }).click();
  await page.getByText("找到 0 份可比資料，顯示最近 0 份", { exact: true }).waitFor();
  checks.push("pending_post_excluded_from_comparables");
  const keyboardLink = page.locator('#nav a[href="#P0"]');
  await keyboardLink.focus();
  await keyboardLink.press("Enter");
  await page.waitForFunction(() => document.querySelector(".workflow-head .eyebrow")?.textContent.startsWith("P0 / "));
  checks.push("keyboard_navigation_native_enter");
  assert.deepEqual(pageErrors, []);
  assert.deepEqual(externalRequests, []);
  checks.push("zero_uncaught_browser_errors", "zero_external_requests");
  const sources = ["scripts/workbench.py", "scripts/workbench_service.py", "scripts/workbench_contract.py",
    "scripts/workbench_store.py", "scripts/workbench_formulas.py", "workbench/app.js", "workbench/api.js", "workbench/ui.js",
    "workbench/editor.js", "workbench/governance.js", "workbench/styles.css", "workbench/layout.css", "workbench/index.html",
    "scripts/social_writing_contract.py", "scripts/social_learning.py", "scripts/social_cohorts.py", "scripts/social_governance_store.py",
    "scripts/social_primitives.py", "scripts/social_governance.py", "scripts/workbench_browser_test.mjs"];
  const receipt = {
    schema_version: 1, status: "PASS", evidence_class: "owned_loopback_fictional_browser",
    recorded_at: new Date().toISOString(), checks, viewport_count: 3,
    private_user_data_used: false, external_request_count: 0, browser_error_count: 0,
    source_sha256: Object.fromEntries(await Promise.all(sources.map(async name => [name, await hashFile(join(skillRoot, name))]))),
    runtime: { node_version: process.version, node_sha256: await hashFile(process.execPath),
      python_sha256: await hashFile(options["--python"]),
      chromium_sha256: await hashFile(chromium.executablePath()) },
  };
  writeFileSync(join(output, "browser-receipt.json"), JSON.stringify(receipt, null, 2));
  console.log("WORKBENCH_BROWSER_PASS checks=" + checks.length);
  function parse_json_count() {
    try { return readFileSync(join(workspace, "data/posts.jsonl"), "utf8").trim().split("\n").filter(Boolean).length; }
    catch (error) { if (error.code === "ENOENT") return 0; throw error; }
  }
} finally {
  await browser?.close();
  child.kill();
  await until(() => child.exitCode !== null || child.signalCode !== null, 5000);
  const actual = realpathSync(workspace);
  assert.equal(dirname(actual), tempBase);
  assert.ok(basename(actual).startsWith("social-workbench-browser-"));
  rmSync(actual, { recursive: true, force: true });
}
