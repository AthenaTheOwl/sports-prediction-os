# Spec 0003 — Ops ledger

## R-OPS-001 — typed RunManifest record
Each ingest/value/eval run produces a Pydantic `RunManifest` with
`id` (content hash), `kind` (ingest|value|eval), `inputs`, `outputs`,
`code_sha`, `fixture_sha256`, `run_date`. Source at
[src/sports_os/ops/run_manifest.py](../../src/sports_os/ops/run_manifest.py).

## R-OPS-002 — content-hashed id
`canonical_id(kind, inputs, outputs, code_sha, fixture_sha256)` produces
a 16-char sha256 prefix. Same content = same id, regardless of input/output
list order. Different content = different id.

## R-OPS-003 — date-bucketed ledger layout
Every manifest lands at `ops/runs/YYYY/MM/DD/<kind>-<id>.json`. The path
is derived from `manifest.run_date`, never from the system clock at
write time (sports-os does not consult `Date.now()` implicitly — a
fixed date must be passed via `run_date=` or `today=`).

## R-OPS-004 — append-only, deduplicated by content
The ledger is append-only by convention. Two writes with identical
content + date land at the same path (idempotent overwrite); two writes
with different content land at different paths.

## R-OPS-005 — STATUS.md is the human-facing summary
`ops/STATUS.md` is the operator-facing single source of truth for "what
state is this repo in." Updated when a new run lands or a spec
graduates. Manually maintained for v0; auto-rendered from the ledger in
a follow-up spec.
