# Spec 0003 — Design

## Why a manifest

Three reasons:

1. **Replay.** A future replay-strict harness needs to know what
   produced this output. The manifest carries inputs, code_sha, and
   fixture_sha256 — enough to ask "given these refs, would the same
   run produce the same output?"

2. **Dedup.** A weekly cron that re-ingests the same matches should
   not produce a new file every Monday. Content-hashed ids make the
   ledger self-deduplicating.

3. **Portfolio parity.** procurement-lab has Run records; ai-field-brief
   has event ledger; trace-to-eval has packets. sports-os adopts the
   same shape early so the eventual cross-repo harness can read this
   repo's runs without a custom adapter.

## Why date buckets

`ops/runs/YYYY/MM/DD/` is the same layout `ops/event-log/` uses in
ai-field-brief and `ops/run-records/` uses in procurement-lab. Three
benefits:

- pruning is `rm -rf` on a year/month directory
- a single day's runs fit on one screen during incident review
- `git diff` between two days has a deterministic narrow scope

## Why explicit `run_date`

The other ledger repos all read `datetime.utcnow()` implicitly inside
`write_*` functions. That broke replay determinism more than once during
the W22 chaos suite. sports-os refuses to do that — every call site
either passes `run_date="2026-06-05"` directly or injects `today=`. The
test suite proves both paths work.

## What's deferred

- automated STATUS.md rendering (R-OPS-005 is manual for v0)
- a query API beyond `list_manifests` (good enough until the ledger has
  > 100 entries)
- a CLI subcommand `sports-os runs list` (lands when the next
  spec ships)
