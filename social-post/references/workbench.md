# Local Content Workbench

Read this when the user asks to open the Social Post UI or understand its modes.
The source checkout provides a local workbench, not a hosted AI service.

## Launch

From the installed Social Post directory:

    python -B scripts/workbench.py

Default address: http://127.0.0.1:8766. Python 3.10+ is required; the runtime uses
only the standard library. No npm install, AI key, Meta API, browser profile or
Cookie export is needed.

Use the host's process/terminal tool to keep the process running. In Codex,
open its printed URL in a browser panel with the available open-in-Codex tool.
In Claude Code, show the URL and use its available browser-opening mechanism
only when the user requested opening the interface. Do not promise a browser
tool that the host does not provide. Stop the owned process with Ctrl+C.

If the port is occupied, inspect its owner before reuse; never terminate an
unrelated process. Use --port 0 to obtain a new loopback port instead.
The service binds only to 127.0.0.1. It is not a phone/5G remote portal.
An explicit --root changes the private workspace; do not point it at another
person's profile or a shared/public folder.

## Three independent choices

- P0–P5: plan, learn voice, draft, record outcomes, compare, manage comments.
- A/B/C: writing format, subordinate to the user's real voice and samples.
- F: one installed creation formula. The selector reads headings, not the
  entire library; “由 Skill 依題材選擇” leaves the choice to the host agent.

F IDs refer to existing formula files, not new workflow hotkeys. Public
installations show only their generic installed formulas. Private formula
contents and learned examples must not enter the public export.

## Current drafting journey

1. Choose P2, platform, A/B/C and optionally F. Enter a short topic and any
   necessary real facts. A one-line topic must not be expanded into invented
   numbers, results or promises.
2. Build and copy the task. Codex invokes $social-post; Claude Code invokes
   /social-post. ChatGPT requires an actually available Skill/context;
   a local installation is not automatically available in cloud chat.
3. The host agent reads the selected reference, private voice card, brief and
   exact-cohort evidence, then writes and checks the complete copy.
4. Paste the copy into the workbench; check counts, paragraphs, punctuation
   and the labelled local black-card study. Save/copy/download the draft.
   Unsaved body changes prompt before route changes or unloading.

The interface does not automatically send a prompt to, or receive a result
from, an existing Codex/Claude session. Do not relabel its task preview as
generated copy. Saving is local and does not publish.

## Outcomes and external actions

P3 validates an outcome bundle without writing. A separate confirmation
consumes a ten-minute preview and appends through the canonical locked writer;
stale, invalid, expired or replayed commits are rejected. The bundled sample
is explicitly fictional. Importing data is not automatically voice training.

P4 retrieves recent exact-cohort cases, not a performance ranking. Unknown
publication minutes remain unknown; screenshot clock time is not post time.

P5 prepares a comment-drafting task. It does not scan or send from the UI.
Existing publication and Chrome comment workflows remain separate and obey
their current session authority, account/scope checks and capability gates.
Adding a UI does not unlock default-off live actuation or prove cross-platform
automation. Read comment-operations.md before any real comment operation.

## Planned service, not a deployed API

For a possible paid service design, read [service-architecture.md](service-architecture.md).
This checkout has no multi-tenant authentication, billing, public API gateway,
AI provider execution, scheduled publishing or tenant browser workers.
Never expose this local server with a public tunnel as a commercial API.

## Verification

    python -B scripts/workbench_test.py
    node scripts/workbench_architecture_test.mjs

Actual renderer journeys additionally use the optional developer-only
workbench_browser_test.mjs with explicit Python and installed Playwright
paths. They use an isolated fictional workspace, not a user's browser.
