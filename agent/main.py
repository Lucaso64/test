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
from ranker import rank_events
from html_generator import generate_html

MILAN_TZ = pytz.timezone("Europe/Rome")
NOW = datetime.now(MILAN_TZ)
DATE_FROM = NOW.date()
DATE_TO = (NOW + timedelta(days=30)).date()

PERPLEXITY_API_KEY = os.environ.get("PERPLEXITY_API_KEY", "")

# Generi target: jazz, blues, funk e sottogeneri
TARGET_GENRES = {
    "jazz", "blues", "funk", "soul", "r&b", "gospel",
    "bebop", "swing", "bossa nova", "latin jazz", "acid jazz",
    "smooth jazz", "free jazz", "jazz fusion", "fusion",
    "rhythm and blues", "neo soul", "nu-jazz", "nu jazz",
    "electric blues", "delta blues", "chicago blues",
    "boogie", "groove",
}

TOP_N = 20  # eventi da selezionare

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
        print("[Classifier] Nessuna API key, generi non classificati")
        for ev in events:
            ev["genre_tags"] = ["live music"]

    # Filtra: tieni solo eventi con almeno un genere target
    jazz_events = []
    for ev in events:
        tags = {t.lower() for t in ev.get("genre_tags", [])}
        if tags & TARGET_GENRES:
            jazz_events.append(ev)
    print(f"[Filter] Eventi jazz/blues/funk: {len(jazz_events)}")

    if not jazz_events:
        print("[Warning] Nessun evento trovato nei generi target. Uso tutti gli eventi.")
        jazz_events = events

    # Ranking con Perplexity: seleziona top 20
    if PERPLEXITY_API_KEY and jazz_events:
        print(f"[Ranker] Scoring e selezione top {TOP_N}...")
        top_events = rank_events(jazz_events, PERPLEXITY_API_KEY, top_n=TOP_N)
    else:
        top_events = sorted(jazz_events, key=lambda e: e.get("start_datetime") or "")[:TOP_N]

    print(f"[Ranker] Top {len(top_events)} eventi selezionati")

    # Ordina per data
    top_events.sort(key=lambda e: e.get("start_datetime") or "")

    print("[HTML] Generazione agenda.html...")
    generate_html(top_events, OUTPUT_PATH, DATE_FROM, DATE_TO, top_n=TOP_N)
    print(f"[Done] Agenda salvata in: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
