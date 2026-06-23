"""Top-level CLI for sports-prediction-os.

Subcommands:
  show                 — print a ranked, readable read of the committed sample match
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

from .analysis import SAMPLE_MATCH, load_report
from .registry import load_registry
from .sources.understat import (
    DEFAULT_CACHE as UNDERSTAT_CACHE,
    FetchError,
    fetch_match_shots,
)


def _cmd_show(_args: argparse.Namespace) -> int:
    """No-arg, offline, read-only read of the committed sample match.

    Prints a ranked shot table (by xG), a per-team summary, and a
    one-line headline finding. Nothing here touches the network.
    """
    from rich.console import Console
    from rich.table import Table

    if not SAMPLE_MATCH.exists():
        print(
            f"no sample match artifact at {SAMPLE_MATCH} — "
            "expected a committed data/sample/*.json file.",
            file=sys.stderr,
        )
        return 1

    report = load_report()
    console = Console()

    console.print(
        f"[bold]{report.scoreline}[/bold]  "
        f"[dim]{report.league} {report.season} - {report.datetime}[/dim]"
    )
    console.print(
        f"[dim]{len(report.shots)} shots - {report.total_xG:.2f} total xG[/dim]\n"
    )

    teams = Table(title="team summary")
    teams.add_column("team")
    teams.add_column("shots", justify="right")
    teams.add_column("xG", justify="right")
    teams.add_column("goals", justify="right")
    teams.add_column("G-xG", justify="right")
    for t in report.teams:
        teams.add_row(
            t.team,
            str(t.shots),
            f"{t.xG:.2f}",
            str(t.goals),
            f"{t.xG_diff:+.2f}",
        )
    console.print(teams)

    shots = Table(title="top shots by xG")
    shots.add_column("#", justify="right")
    shots.add_column("min", justify="right")
    shots.add_column("player")
    shots.add_column("team")
    shots.add_column("xG", justify="right")
    shots.add_column("result")
    for i, s in enumerate(report.top_shots(5), start=1):
        marker = "[green]GOAL[/green]" if s.is_goal else s.result
        shots.add_row(
            str(i), str(s.minute), s.player, s.team, f"{s.xG:.2f}", marker
        )
    console.print(shots)

    console.print(f"\n[bold]finding:[/bold] {report.headline()}")
    return 0


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

    show = sub.add_parser(
        "show",
        help="print a ranked, readable read of the committed sample match",
    )
    show.set_defaults(func=_cmd_show)

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
