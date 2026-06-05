"""Per-run ops + ledger primitives.

Every ingest/value/eval run in this OS produces a typed ``RunManifest``
that lands under ``ops/runs/YYYY/MM/DD/<kind>-<sha>.json``. The
manifest is content-hashed from its inputs + outputs so the same run
on the same fixtures reproduces the same path — which makes the ledger
both a directory of runs and a deduplicator.

The pattern mirrors what the rest of the AthenaTheOwl portfolio does
under different names (Run records in procurement-lab, event ledger
in ai-field-brief, packets in trace-to-eval-harness). Adopting the
same shape early keeps retrofit cost zero when the harness lands.
"""

from sports_os.ops.run_manifest import (
    RunKind,
    RunManifest,
    canonical_id,
    read_manifest,
    write_manifest,
)

__all__ = [
    "RunKind",
    "RunManifest",
    "canonical_id",
    "read_manifest",
    "write_manifest",
]
