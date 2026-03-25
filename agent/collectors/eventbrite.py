import requests
from bs4 import BeautifulSoup
from datetime import date

BASE_URL = "https://www.eventbrite.it/d/italy--milan/music--concerts/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36"
}


def collect_eventbrite(date_from, date_to):
    events = []
    for page in range(1, 6):
        url = BASE_URL if page == 1 else f"{BASE_URL}?page={page}"
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            resp.raise_for_status()
        except Exception as e:
            print(f"[Eventbrite] Errore pagina {page}: {e}")
            break
        soup = BeautifulSoup(resp.text, "lxml")
        cards = (soup.select("div[data-testid='event-card']") or
                 soup.select("article.eds-event-card") or
                 soup.select(".search-event-card-wrapper"))
        if not cards:
            break
        for card in cards:
            ev = _parse_card(card)
            if ev:
                events.append(ev)
    print(f"[Eventbrite] Trovati {len(events)} eventi")
    return events


def _parse_card(card):
    try:
        title_el = (card.select_one("h2") or
                    card.select_one("[data-testid='event-card-title']") or
                    card.select_one(".eds-event-card__formatted-name"))
        if not title_el:
            return None
        title = title_el.get_text(strip=True)
        date_el = (card.select_one("p[data-testid='event-card-date']") or
                   card.select_one(".eds-event-card__formatted-date") or
                   card.select_one("time"))
        dt_str = date_el.get_text(strip=True) if date_el else None
        loc_el = (card.select_one("p[data-testid='event-card-venue']") or
                  card.select_one(".card-text--truncated__one") or
                  card.select_one(".eds-event-card__formatted-location"))
        location = loc_el.get_text(strip=True) if loc_el else ""
        link_el = card.select_one("a[href]")
        link = link_el["href"] if link_el else ""
        if link and not link.startswith("http"):
            link = "https://www.eventbrite.it" + link
        desc_el = card.select_one(".eds-event-card-content__sub-title")
        desc = desc_el.get_text(strip=True) if desc_el else ""
        venue_name, address = "", "Milano"
        if " - " in location:
            parts = location.split(" - ", 1)
            venue_name, address = parts[0].strip(), parts[1].strip()
        else:
            venue_name = location
        return {
            "event_name": title, "artist": "",
            "venue_name": venue_name, "address": address,
            "start_datetime": dt_str, "source_url": link, "description": desc,
        }
    except Exception:
        return None
