# Writing governance and isolated learning

## 目錄 / Navigation

- [Independent learning channels](#independent-learning-channels)
- [Frozen originals and effective versions](#frozen-originals-and-effective-versions)
- [Mandatory drafting gate, every selected F](#mandatory-drafting-gate-every-selected-f)
- [Candidate → owner review → explicit activation](#candidate--owner-review--explicit-activation)
- [UI and external authority](#ui-and-external-authority)

Read before P0–P4. This contract takes precedence over legacy instructions to
edit an author voice, formula or rule immediately after seeing a new example.
It does not supersede safety, verified platform restrictions or the user's
explicit per-draft instructions. A per-draft exception is not a permanent update.

## Independent learning channels

Five platforms × `text_image` / `video`, then content type, surface and maturity.
Text, black-background cards, photos and carousels remain separate surfaces;
Reels, Shorts and long video also remain separate. Broad media labels alone
do not make samples comparable. No empty-cohort fallback to a pooled winner.

Own facts stay in the original outcome ledgers. Platform-combined observations
are reference-only, not an individual platform result. Unknown or conflicting
media stays quarantined. Snapshot clocks, rounded counts, missing denominators,
audience populations and capture maturity retain their existing qualifiers.

External examples live in `data/learning_events.jsonl`, kind `external_reference`.
They need no invented own post ID or publication minute. Multiple platforms or
observations of one content ID are not independent content samples. Preserve
caption, visual layout, wording, punctuation, source provenance, unknown fields
and observation times. Never use an external voice to replace the author's voice.
Legacy external experiment events remain historical provenance and planned-test
context after migration; the external-reference ledger owns current observations.

## Frozen originals and effective versions

The owner's explicit initial setup captures real voice, all installed F sources,
rule bodies and private writing policy into immutable, digest-addressed versions.
`data/author_contract.json` selects one version under `data/author_contracts/`.
Original sources are never overwritten or silently recaptured. Unexpected source
drift blocks generation until investigated. Public placeholders cannot be locked
as a learned author. No contract/voice/data is exported with the generic engine.

    python -B scripts/social_governance.py bootstrap --write
    python -B scripts/social_governance.py status
    python -B scripts/social_governance.py channels

Do not run bootstrap to hide an existing mismatch. Preserve the baseline receipt.

## Mandatory drafting gate, every selected F

1. Select the platform, media family, A/B/C writing format and one actual F.
   F6a and F6b are different variants; ambiguous F06 is rejected after locking.
   Do not apply F6b's promotional voice to Mode C or overlay all formulas at once.
2. Verify the active revision; read the FULL effective selected F and voice from
   `context`, not only its heading. Approved scoped overrides take priority over
   the unchanged historical source. Related rules must also use effective
   overrides when present. If the host cannot read this context, say unconfigured;
   do not pretend a cloud chat loaded private local files.

       python -B scripts/social_governance.py context --platform facebook --media-family text_image --format B --formula F06b

3. Read exact-cohort own evidence. Do not invent achievements, statistics, proof,
   dialogue or optimal posting minutes from a one-line brief. Legacy algorithm
   multipliers, cadence and guaranteed-viral claims are hypotheses, not frozen
   platform facts. Locking preserves writing requirements, not their causal proof.
4. Draft to the selected F's ordered intent, section functions, hook, CTA and
   punctuation requirements. Preserve the existing A/B/C rules, real source
   exceptions and exact per-draft instructions. No emoji or decorative Markdown.
   F6b's four paragraphs, blank lines, no links/lists, first-paragraph-only
   exclamations and bare later endings have deterministic rejection checks.
5. Run `check-draft` with the same revision, actual F, format, platform and media.
   A stale revision or structural failure must be fixed before final delivery.

       python -B scripts/social_governance.py check-draft --input draft.txt --revision REVISION --platform facebook --media-family text_image --format B --formula F06b

6. The host MUST additionally review the entire effective formula: ordered
   section purposes, topic fit, author's voice, each factual claim's source,
   single CTA and user exceptions. Correct text when any check fails. Preserve a
   private QA note bound to draft SHA, contract revision and formula SHA when
   producing a saved delivery. Hashes and paragraph counts cannot prove semantic
   imitation. `structural_pass` is never advertised as `delivery_ready` or proof
   that every F requirement is machine-verified. Scratch saves remain allowed.

## Candidate → owner review → explicit activation

New cases and P1/P4 analysis are evidence, not approval. Propose complete
replacement text for a frozen source, an exact platform/media scope, recorded
same-scope evidence IDs, a reason and a title. The proposal captures its base
revision, original text, source hash and proposal digest. Single external viral
examples remain candidates, never independently validated author rules.

    python -B scripts/social_governance.py propose --input proposal.json --write

Show the owner full before/after, evidence limitations, scope and exact digest.
Only their explicit approval of this displayed change permits a review event.
The assistant MUST NOT manufacture consent, use `--owner-confirmed` on a general
"improve the Skill" request, or click its own approval buttons. The local UI
relies on its authenticated same-origin owner session; it is not identity signing
or cryptographic proof that a human rather than an agent clicked.

    python -B scripts/social_governance.py review --proposal ID --digest DIGEST --decision approve --notes "actual review reason" --owner-confirmed --write
    python -B scripts/social_governance.py activate --proposal ID --digest DIGEST --owner-confirmed --write

Approval alone changes no effective text. Activation is a separate deliberate
step, scoped ONLY to the chosen platform/media; original source bytes and parent
versions stay intact. Edited, stale, rejected, unapproved or replayed proposals
are blocked. Any concurrent activation requires rebasing and fresh review.
To revert, propose the preserved original/prior text for the same scope and
review/activate it normally; never delete evidence or bypass approval by replacing
the pointer. Back up the whole private data directory, not just its active pointer.

## UI and external authority

"資料分區與審核" shows ten channels, the lock revision and full candidate diffs.
"核對正式 F 契約" in the editor checks the actual selected F and draft, not its
preview. Saving/copying scratch text is not approval to publish or a QA receipt.
No new AI execution, public API, scheduling or Chrome comment capability is
implied. Existing publishing and comment gates remain unchanged and default-off.
