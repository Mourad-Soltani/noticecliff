# Signature: Mourad.Soltani
"""Command line entry for NoticeCliff."""

from __future__ import annotations

import argparse
import json
import sys

from noticecliff.calculator import NoticeCliffError, compute_cliff


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="noticecliff", description="Last safe cancel date before auto-renewal")
    parser.add_argument("--renewal", required=True, help="Renewal date YYYY-MM-DD")
    parser.add_argument("--notice-days", type=int, required=True)
    parser.add_argument("--count-mode", default="calendar", choices=["calendar", "business"])
    parser.add_argument("--buffer-days", type=int, default=0)
    parser.add_argument("--as-of", default=None)
    parser.add_argument("--skip-date", action="append", default=[])
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = compute_cliff(
            renewal_date=args.renewal,
            notice_days=args.notice_days,
            count_mode=args.count_mode,
            buffer_days=args.buffer_days,
            as_of=args.as_of,
            skip_dates=args.skip_date,
        )
    except NoticeCliffError as exc:
        print(json.dumps({"error": str(exc), "signature": "Mourad.Soltani"}))
        return 2
    print(json.dumps(result.to_dict(), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
