from datetime import datetime
import pytz
from dateutil import parser as dtparser

MILAN_TZ = pytz.timezone("Europe/Rome")


def normalize_events(raw_events):
    normalized = []
    for ev in raw_events:
        try:
            norm = {
                "artist":        (ev.get("artist") or "").strip() or (ev.get("event_name") or "").strip(),
                "event_name":    (ev.get("event_name") or "").strip(),
                "venue_name":    (ev.get("venue_name") or "").strip(),
                "address":       (ev.get("address") or "").strip(),
                "start_datetime": _parse_dt(ev.get("start_datetime")),
                "source_url":    (ev.get("source_url") or "").strip(),
                "description":   (ev.get("description") or "").strip(),
                "genre_tags":    [],
            }
            if not norm["event_name"] or not norm["start_datetime"]:
                continue
            normalized.append(norm)
        except Exception as e:
            print(f"[Normalizer] Skipped: {e}")
    return normalized


def _parse_dt(val):
    if not val:
        return None
    if isinstance(val, datetime):
        if val.tzinfo is None:
            val = MILAN_TZ.localize(val)
        return val.isoformat()
    if isinstance(val, str):
        try:
            dt = dtparser.parse(val, dayfirst=True)
            if dt.tzinfo is None:
                dt = MILAN_TZ.localize(dt)
            return dt.isoformat()
        except Exception:
            return None
    return None


def deduplicate(events):
    seen = set()
    unique = []
    for ev in events:
        key = (
            ev["event_name"].lower().strip()[:60],
            ev["venue_name"].lower().strip()[:40],
            (ev["start_datetime"] or "")[:10],
        )
        if key not in seen:
            seen.add(key)
            unique.append(ev)
    return unique
