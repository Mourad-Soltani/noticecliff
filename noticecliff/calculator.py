# Signature: Mourad.Soltani
"""Pure date math for contractual notice windows."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, timedelta
from typing import Iterable, List, Optional, Sequence


class NoticeCliffError(ValueError):
    """Invalid notice-window input."""


@dataclass(frozen=True)
class CliffResult:
    renewal_date: str
    notice_days: int
    count_mode: str
    buffer_days: int
    as_of: str
    cancel_by: str
    days_remaining: int
    risk: str
    skipped_dates: List[str]
    signature: str = "Mourad.Soltani"

    def to_dict(self) -> dict:
        return asdict(self)


def _parse_date(value: str, field: str) -> date:
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise NoticeCliffError(f"{field} must be YYYY-MM-DD") from exc


def _is_weekend(day: date) -> bool:
    return day.weekday() >= 5


def _step_back(day: date, steps: int, business: bool, skip: set[date]) -> tuple[date, List[str]]:
    if steps < 0:
        raise NoticeCliffError("notice_days and buffer_days must be >= 0")
    cursor = day
    skipped: List[str] = []
    remaining = steps
    # Guard against pathological skip sets.
    guard = 0
    while remaining > 0:
        guard += 1
        if guard > 3660:
            raise NoticeCliffError("could not walk notice window; skip_dates too dense")
        cursor -= timedelta(days=1)
        if business and (_is_weekend(cursor) or cursor in skip):
            skipped.append(cursor.isoformat())
            continue
        if not business and cursor in skip:
            skipped.append(cursor.isoformat())
            continue
        remaining -= 1
    return cursor, skipped


def risk_band(days_remaining: int) -> str:
    if days_remaining < 0:
        return "missed"
    if days_remaining <= 3:
        return "critical"
    if days_remaining <= 14:
        return "soon"
    return "safe"


def compute_cliff(
    renewal_date: str,
    notice_days: int,
    count_mode: str = "calendar",
    buffer_days: int = 0,
    as_of: Optional[str] = None,
    skip_dates: Optional[Sequence[str]] = None,
) -> CliffResult:
    """Return the last day a notice can still land before renewal.

    The renewal date itself is not a valid notice day. Counting starts on the
    day before renewal. Business mode ignores weekends and any skip_dates.
    buffer_days are extra days pulled forward so a letter can be posted.
    """
    renewal = _parse_date(renewal_date, "renewal_date")
    today = _parse_date(as_of, "as_of") if as_of else date.today()
    mode = (count_mode or "calendar").strip().lower()
    if mode not in {"calendar", "business"}:
        raise NoticeCliffError("count_mode must be calendar or business")
    try:
        notice = int(notice_days)
        buffer = int(buffer_days)
    except (TypeError, ValueError) as exc:
        raise NoticeCliffError("notice_days and buffer_days must be integers") from exc
    if notice > 366 or buffer > 60:
        raise NoticeCliffError("notice_days max 366 and buffer_days max 60")
    skip = set()
    for raw in skip_dates or []:
        skip.add(_parse_date(raw, "skip_dates"))
    start = renewal - timedelta(days=1)
    total_steps = notice + buffer
    # notice_days is the length of the window ending the day before renewal.
    # A 30-day notice means 30 countable days ending on start, so we step
    # notice_days - 1 if notice_days > 0, then apply buffer on top.
    if total_steps == 0:
        cancel_by = start
        skipped: List[str] = []
    else:
        steps = total_steps - 1 if notice > 0 else buffer
        # If notice is 0, buffer still walks back from the day before renewal.
        if notice == 0:
            cancel_by, skipped = _step_back(start + timedelta(days=1), buffer, mode == "business", skip)
        else:
            cancel_by, skipped = _step_back(start + timedelta(days=1), total_steps, mode == "business", skip)
    days_remaining = (cancel_by - today).days
    return CliffResult(
        renewal_date=renewal.isoformat(),
        notice_days=notice,
        count_mode=mode,
        buffer_days=buffer,
        as_of=today.isoformat(),
        cancel_by=cancel_by.isoformat(),
        days_remaining=days_remaining,
        risk=risk_band(days_remaining),
        skipped_dates=skipped,
    )


def summarize(rows: Iterable[CliffResult]) -> dict:
    items = list(rows)
    bands = {"missed": 0, "critical": 0, "soon": 0, "safe": 0}
    for item in items:
        bands[item.risk] = bands.get(item.risk, 0) + 1
    return {"count": len(items), "bands": bands, "signature": "Mourad.Soltani"}
