# Service architecture proposal

Status: design only. No paid API, billing or automatic AI bridge is deployed.

## Shared core, different execution hosts

Keep one versioned Social Post rule/router core. A local Codex/Claude workbench
and a future hosted service consume that core rather than maintain divergent
writing rules. A Skill instructs an agent; it is not itself a running model.
Hosted generation requires a separately configured model executor.

Preserve the three axes: workflow P0–P5, format A/B/C, formula F.
Every generation job binds the chosen core revision, user-approved voice
revision, platform, selected formula and available evidence. Re-check final
format, facts and user constraints before returning a draft.

## Possible paid API boundary

Start with asynchronous draft generation and revision, not cloud control of
customers' social accounts. A proposed POST /v1/draft-jobs accepts a topic,
authorized style profile, platform, format and formula; GET /v1/draft-jobs/{id}
returns the tenant-owned status, copy and checks. These are proposed endpoints,
not the current local /api/task route.

Charging for hosting, model execution, team workflows and support can coexist
with the repository's MIT source distribution. Do not promise exclusive
ownership of open-source code, unlimited generation or free provider usage.
Choose pricing only after measuring cost per successful job, revision rate
and support demand. Generated quality and traffic are not guaranteed.

Before public deployment, require tenant authentication, authorization on
every object, isolated storage and voice profiles, per-tenant quotas, cost
ceilings, cancellation, idempotent requests, usage metering, billing
reconciliation and audit logs. Redact secrets; define retention, deletion and
export. Do not reuse the local loopback cookie as a customer API credential.

## Publication and comment execution

A Social Post API is a service API owned by this product, not the Meta API.
That distinction does not remove platform rules or account risk.

If customers later request browser-only posting/replies, use a separately
authorized local worker in each customer's own signed-in browser environment.
The hosted draft service never inherits the maintainer's session or accepts
exported browser Cookies. Do not build a shared cloud browser with everyone's
accounts.

The worker checks supported host/runtime, exact account and post/comment
scope, fresh approval and final text digest before external mutations.
Use the existing durable once-only action/permit and reconciliation contracts.
For publication, require a corresponding posting-specific verification
contract; do not treat comment-canary evidence as a posting receipt.
Unknown results stop, and restrictions/checkpoints require user resolution.
No repeated sending, permission bypass or “never banned” promises.

## Acceptance before integrated AI UI

A future bridge must prove: a real selected host/model receives the bound
task; the actual result returns to the correct workspace/job; interrupted
and duplicated jobs do not cause duplicate billing or sending; and a
draft-only request never becomes publication authority. A mock result,
clipboard button or successful local browser test is not this evidence.

Maintain source-version rollback and independent provider/platform adapters.
A platform UI change updates its adapter and evidence, not the shared
authorization rules. Preserve owner review and public contribution governance.
