import os
import sys
from datetime import datetime, timedelta
import pytz

sys.path.insert(0, os.path.dirname(__file__))

from collectors.eventbrite import collect_eventbrite
from collectors.vivimilano import collect_vivimilano
from collectors.zero_milano import collect_zero_milano
from collectors.venues import collect_venues
from normalizer import normalize_events, deduplicate
from classifier import classify_genres
from html_generator import generate_html

MILAN_TZ = pytz.timezone("Europe/Rome")
NOW = datetime.now(MILAN_TZ)
DATE_FROM = NOW.date()
DATE_TO = (NOW + timedelta(days=30)).date()

PERPLEXITY_API_KEY = os.environ.get("PERPLEXITY_API_KEY", "")

EXCLUDED_GENRES = {"classica", "lirica", "opera", "dj set", "electronic dj", "djset", "dj"}

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "..", "output", "agenda.html")


def main():
    print(f"[Agent] Raccolta eventi dal {DATE_FROM} al {DATE_TO}")
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    raw_events = []

    print("[Collector] Eventbrite...")
    raw_events += collect_eventbrite(DATE_FROM, DATE_TO)

    print("[Collector] ViviMilano...")
    raw_events += collect_vivimilano(DATE_FROM, DATE_TO)

    print("[Collector] Zero Milano...")
    raw_events += collect_zero_milano(DATE_FROM, DATE_TO)

    print("[Collector] Locali singoli...")
    raw_events += collect_venues(DATE_FROM, DATE_TO)

    print(f"[Collector] Totale grezzo: {len(raw_events)} eventi")

    events = normalize_events(raw_events)
    events = deduplicate(events)
    print(f"[Normalizer] Dopo deduplicazione: {len(events)} eventi")

    if PERPLEXITY_API_KEY:
        print("[Classifier] Classificazione generi con Perplexity API...")
        events = classify_genres(events, PERPLEXITY_API_KEY)
    else:
        print("[Classifier] Nessuna API key trovata, generi non classificati")
        for ev in events:
            ev["genre_tags"] = ["live music"]

    filtered = []
    for ev in events:
        tags_lower = {t.lower() for t in ev.get("genre_tags", [])}
        if tags_lower & EXCLUDED_GENRES:
            continue
        filtered.append(ev)
    print(f"[Filter] Dopo filtro generi: {len(filtered)} eventi")

    filtered.sort(key=lambda e: e.get("start_datetime") or "")

    print("[HTML] Generazione agenda.html...")
    generate_html(filtered, OUTPUT_PATH, DATE_FROM, DATE_TO)
    print(f"[Done] Agenda salvata in: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
