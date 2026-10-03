// Reuse the calibrated lexer; explicit UI ownership and required edges.
import assert from "node:assert/strict";
import { readFileSync, readdirSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { join, dirname, posix } from "node:path";
import { parseStaticModuleSpecifiers, sha256 } from "./comment_js_architecture_core.mjs";

const names = ["api.js", "ui.js", "editor.js", "governance.js", "app.js"];
const allowed = {
  "api.js": [], "ui.js": [], "editor.js": ["api.js", "ui.js"],
  "governance.js": ["api.js", "ui.js"],
  "app.js": ["api.js", "ui.js", "editor.js", "governance.js"],
};

export function evaluate(modules) {
  const errors = [];
  const edges = [];
  if (Object.keys(modules).sort().join("|") !== [...names].sort().join("|")) errors.push("module_set");
  for (const [name, source] of Object.entries(modules)) {
    for (const row of parseStaticModuleSpecifiers(source)) {
      if (row.kind !== "static" || !row.specifier?.startsWith("./")) {
        errors.push("external_or_dynamic_loader");
        continue;
      }
      const target = posix.normalize(row.specifier);
      if (!Object.hasOwn(modules, target)) errors.push("missing_target");
      if (!(allowed[name] || []).includes(target)) errors.push("layer");
      edges.push([name, target]);
    }
  }
  for (const [source, targets] of Object.entries(allowed)) {
    for (const target of targets) {
      if (!edges.some(edge => edge[0] === source && edge[1] === target)) errors.push("required_edge");
    }
  }
  function visit(node, chain) {
    if (chain.includes(node)) { errors.push("cycle"); return; }
    for (const [, target] of edges.filter(edge => edge[0] === node)) visit(target, [...chain, node]);
  }
  for (const name of names) visit(name, []);
  return { errors: [...new Set(errors)].sort(), edges };
}

const root = join(dirname(fileURLToPath(import.meta.url)), "..", "workbench");
const modules = Object.fromEntries(names.map(name => [name, readFileSync(join(root, name), "utf8")]));
const inventory = readdirSync(root).filter(name => name.endsWith(".js")).sort();
assert.deepEqual(inventory, [...names].sort());
const real = evaluate(modules);
assert.deepEqual(real.errors, []);
const controls = [
  [{ ...modules, "rogue.js": "" }, "module_set"],
  [Object.fromEntries(Object.entries(modules).filter(([name]) => name !== "api.js")), "module_set"],
  [{ ...modules, "app.js": "" }, "required_edge"],
  [{ ...modules, "app.js": "import './missing.js';" + modules["app.js"] }, "missing_target"],
  [{ ...modules, "api.js": "import './app.js';" + modules["api.js"] }, "cycle"],
  [{ ...modules, "ui.js": "import './editor.js';" + modules["ui.js"] }, "layer"],
  [{ ...modules, "app.js": "import 'https://invalid.example/remote.js';" + modules["app.js"] }, "external_or_dynamic_loader"],
  [{ ...modules, "app.js": "import('./api.js');" + modules["app.js"] }, "external_or_dynamic_loader"],
];
for (const [mutant, expected] of controls) assert.ok(evaluate(mutant).errors.includes(expected), expected);
for (const [name, source] of Object.entries(modules)) {
  assert.ok(!/\p{Extended_Pictographic}/u.test(source), "emoji in UI source: " + name);
  assert.ok(!/\b(?:innerHTML|outerHTML|eval|localStorage|sessionStorage)\b\s*[=(.]/u.test(source),
    "unreviewed HTML/script/credential storage surface: " + name);
}
console.log(JSON.stringify({
  status: "PASS", scope: "workbench_static_ui_graph", module_count: names.length,
  edges: real.edges, negative_controls: controls.length,
  source_sha256: Object.fromEntries(names.map(name => [name, sha256(modules[name])])),
}));
console.log("WORKBENCH_ARCHITECTURE_PASS");
