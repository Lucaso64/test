import re
from datetime import datetime, date
import pytz
from dateutil import parser as dtparser
from bs4 import BeautifulSoup

MILAN_TZ = pytz.timezone("Europe/Rome")


def _strip_html(text):
    """Rimuove tag HTML e normalizza spazi bianchi."""
    if not text:
        return ""
    try:
        cleaned = BeautifulSoup(text, "lxml").get_text(separator=" ")
    except Exception:
        cleaned = re.sub(r"<[^>]+>", " ", text)
    # Rimuove escape sequences tipo \n, \t
    cleaned = re.sub(r"\\[ntr]", " ", cleaned)
    # Collassa spazi multipli
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def normalize_events(raw_events):
    normalized = []
    now = datetime.now(MILAN_TZ)

    for ev in raw_events:
        try:
            # Pulizia descrizione da HTML
            raw_desc = (ev.get("description") or "").strip()
            clean_desc = _strip_html(raw_desc)

            norm = {
                "artist":         (ev.get("artist") or "").strip() or (ev.get("event_name") or "").strip(),
                "event_name":     (ev.get("event_name") or "").strip(),
                "venue_name":     (ev.get("venue_name") or "").strip(),
                "address":        (ev.get("address") or "").strip(),
                "start_datetime": _parse_dt(ev.get("start_datetime"), now),
                "source_url":     (ev.get("source_url") or "").strip(),
                "description":    clean_desc,
                "genre_tags":     [],
            }

            # Scarta se manca nome o data
            if not norm["event_name"] or not norm["start_datetime"]:
                continue

            # Scarta eventi nel passato (data < oggi)
            try:
                ev_date = datetime.fromisoformat(norm["start_datetime"]).date()
                if ev_date < now.date():
                    continue
            except Exception:
                pass

            normalized.append(norm)
        except Exception as e:
            print(f"[Normalizer] Skipped: {e}")
    return normalized


def _parse_dt(val, now=None):
    """Restituisce ISO8601 string con timezone Milano, oppure None.
    Corregge date senza anno assumendo l'anno corrente (o prossimo se nel passato).
    """
    if not val:
        return None
    if isinstance(val, datetime):
        if val.tzinfo is None:
            val = MILAN_TZ.localize(val)
        return val.isoformat()
    if isinstance(val, str):
        # Pulisce tag HTML anche dalla stringa data
        val = _strip_html(val)
        if not val:
            return None
        try:
            dt = dtparser.parse(val, dayfirst=True)
            if dt.tzinfo is None:
                dt = MILAN_TZ.localize(dt)

            # Se la data parsata e' nel passato remoto (piu' di 60 giorni fa)
            # probabilmente il parser ha usato l'anno sbagliato: correggi con anno corrente o +1
            if now:
                now_naive = now.replace(tzinfo=None)
                dt_naive = dt.replace(tzinfo=None)
                days_diff = (now_naive - dt_naive).days
                if days_diff > 60:
                    # Prova con anno corrente
                    dt_fixed = dt.replace(year=now.year)
                    if dt_fixed.replace(tzinfo=None) < now_naive:
                        # Se ancora nel passato, prova anno prossimo
                        dt_fixed = dt.replace(year=now.year + 1)
                    dt = dt_fixed
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
