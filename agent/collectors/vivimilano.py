import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.vivimilano.corriere.it/musica/concerti/"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36"}


def collect_vivimilano(date_from, date_to):
    events = []
    for page in range(1, 4):
        url = BASE_URL if page == 1 else f"{BASE_URL}?page={page}"
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            resp.raise_for_status()
        except Exception as e:
            print(f"[ViviMilano] Errore pagina {page}: {e}")
            break
        soup = BeautifulSoup(resp.text, "lxml")
        items = (soup.select(".article-list article") or
                 soup.select(".event-item") or
                 soup.select("article"))
        if not items:
            break
        for item in items:
            ev = _parse_item(item)
            if ev:
                events.append(ev)
    print(f"[ViviMilano] Trovati {len(events)} eventi")
    return events


def _parse_item(item):
    try:
        title_el = item.select_one("h2, h3, .title, .event-title")
        if not title_el:
            return None
        title = title_el.get_text(strip=True)
        date_el = item.select_one(".date, time, .event-date")
        dt_str = date_el.get_text(strip=True) if date_el else None
        venue_el = item.select_one(".venue, .location")
        venue = venue_el.get_text(strip=True) if venue_el else ""
        link_el = item.select_one("a[href]")
        link = link_el["href"] if link_el else ""
        if link and link.startswith("/"):
            link = "https://www.vivimilano.corriere.it" + link
        desc_el = item.select_one(".summary, .description, p")
        desc = desc_el.get_text(strip=True) if desc_el else ""
        return {
            "event_name": title, "artist": "",
            "venue_name": venue, "address": "Milano",
            "start_datetime": dt_str, "source_url": link, "description": desc,
        }
    except Exception:
        return None
