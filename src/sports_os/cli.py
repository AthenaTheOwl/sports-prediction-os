"""Top-level CLI for sports-prediction-os.

Subcommands:
  registry             — print the parsed source registry
  ingest               — fetch + cache one provider's data for a (league, season, scope)
  analyze              — run the value layer on a cached match (placeholder in v0)

The CLI is intentionally thin — each subcommand delegates to a single
function in the package so the same primitives drive the Streamlit app.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .registry import load_registry
from .sources.understat import (
    DEFAULT_CACHE as UNDERSTAT_CACHE,
    FetchError,
    fetch_match_shots,
)


def _cmd_registry(args: argparse.Namespace) -> int:
    reg = load_registry(args.registry) if args.registry else load_registry()
    print(json.dumps(reg.model_dump(), indent=2, default=str))
    return 0


def _cmd_ingest(args: argparse.Namespace) -> int:
    if args.provider != "understat":
        print(
            f"provider `{args.provider}` not implemented in v0 — "
            "only `understat` ships in this scaffold.",
            file=sys.stderr,
        )
        return 1
    if not args.match_ids:
        print("--match-id is required at least once for understat ingest in v0.", file=sys.stderr)
        return 2
    cache_dir = args.cache_dir or UNDERSTAT_CACHE
    failures: list[str] = []
    for mid in args.match_ids:
        try:
            shots = fetch_match_shots(
                mid, cache_dir=cache_dir, use_network=not args.offline
            )
        except FetchError as exc:
            failures.append(f"{mid}: {exc}")
            continue
        print(f"match {mid}: {len(shots)} shots")
    if failures:
        for line in failures:
            print(f"failed: {line}", file=sys.stderr)
        return 1
    return 0


def _cmd_analyze(_args: argparse.Namespace) -> int:
    print(
        "analyze: not implemented in v0. "
        "Track lands in spec 0003 once socceraction integration is wired."
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sports-os",
        description="Sports prediction OS — soccer event-data analysis.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    reg = sub.add_parser("registry", help="dump the parsed source registry")
    reg.add_argument(
        "--registry",
        type=Path,
        default=None,
        help="override path to sources.yaml (default: config/sources.yaml)",
    )
    reg.set_defaults(func=_cmd_registry)

    ing = sub.add_parser("ingest", help="fetch + cache provider data")
    ing.add_argument("provider", choices=["understat", "statsbomb-open"])
    ing.add_argument(
        "--match-id",
        dest="match_ids",
        action="append",
        default=[],
        help="match id to fetch (repeatable)",
    )
    ing.add_argument(
        "--offline",
        action="store_true",
        help="read cache only; never touch the network",
    )
    ing.add_argument(
        "--cache-dir",
        type=Path,
        default=None,
        help="override the on-disk cache root",
    )
    ing.set_defaults(func=_cmd_ingest)

    ana = sub.add_parser("analyze", help="run the value layer on a cached match")
    ana.set_defaults(func=_cmd_analyze)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
