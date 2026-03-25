import requests
import json
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36"}

VENUES = [
    {"name": "Biko Club", "url": "https://www.biko.eu/", "address": "Via Ettore Ponti 40, Milano"},
    {"name": "Blue Note Milano", "url": "https://www.bluenotemilano.com/", "address": "Via Pietro Borsieri 37, Milano"},
    {"name": "Circolo Magnolia", "url": "https://www.circolomagnolia.it/", "address": "Via Circonvallazione Idroscalo, Segrate"},
    {"name": "Santeria Toscana 31", "url": "https://www.santeria.it/", "address": "Via Toscana 31, Milano"},
    {"name": "Spirit de Milan", "url": "https://www.spiritdemilan.it/", "address": "Via Bovisasca 59, Milano"},
    {"name": "Legend Club", "url": "https://www.legendclub.it/", "address": "Via Canova 41, Milano"},
    {"name": "Arci Bellezza", "url": "https://www.arcibellezza.it/", "address": "Via Giovanni Bellezza 16, Milano"},
    {"name": "Mare Culturale Urbano", "url": "https://www.maremilano.org/", "address": "Via Gabrio Casati 2, Milano"},
    {"name": "Nidaba Theatre", "url": "https://www.nidabatheatre.com/", "address": "Via Casoretto 5, Milano"},
    {"name": "Germi", "url": "https://www.germimilano.it/", "address": "Via Giulio e Corrado Venini 39, Milano"},
    {"name": "Barrios Live", "url": "https://www.barrios.it/", "address": "Viale Monte Nero 29, Milano"},
    {"name": "Tunnel Club", "url": "https://www.tunnelmilano.it/", "address": "Via Sammartini 30, Milano"},
    {"name": "Arci Ohibo", "url": "https://www.ohibo.it/", "address": "Viale Aretusa 23, Milano"},
    {"name": "Init Club", "url": "https://www.initclubmilano.it/", "address": "Via Gian Carlo Castelbarco 12, Milano"},
    {"name": "Serraglio", "url": "https://serraglio.it/", "address": "Corso Buenos Aires 16, Milano"},
    {"name": "Rock n Roll Club", "url": "https://rocknrollmilano.com/", "address": "Via Chiusi 14, Milano"},
]


def collect_venues(date_from, date_to):
    all_events = []
    for venue in VENUES:
        try:
            events = _scrape_venue(venue)
            all_events.extend(events)
            print(f"[Venues] {venue['name']}: {len(events)} eventi")
        except Exception as e:
            print(f"[Venues] Errore su {venue['name']}: {e}")
    return all_events


def _scrape_venue(venue):
    events = []
    resp = requests.get(venue["url"], headers=HEADERS, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "lxml")
    prog_link = None
    for a in soup.find_all("a", href=True):
        text = a.get_text(strip=True).lower()
        href = a["href"].lower()
        if any(kw in text or kw in href for kw in ["event", "programm", "concert", "agenda", "calendario", "spettacol"]):
            prog_link = a["href"]
            break
    if prog_link:
        if prog_link.startswith("/"):
            prog_link = venue["url"].rstrip("/") + prog_link
        if not prog_link.startswith("http"):
            prog_link = venue["url"] + prog_link
        try:
            resp2 = requests.get(prog_link, headers=HEADERS, timeout=15)
            resp2.raise_for_status()
            soup = BeautifulSoup(resp2.text, "lxml")
        except Exception:
            pass
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string)
            items = data if isinstance(data, list) else [data]
            for item in items:
                if item.get("@type") == "Event":
                    ev = _from_schema(item, venue)
                    if ev:
                        events.append(ev)
        except Exception:
            pass
    if not events:
        items = (soup.select(".event") or soup.select(".evento") or
                 soup.select(".concert") or soup.select("article"))
        for item in items[:20]:
            ev = _parse_generic(item, venue)
            if ev:
                events.append(ev)
    return events


def _from_schema(data, venue):
    try:
        name = data.get("name", "").strip()
        if not name:
            return None
        start = data.get("startDate", "")
        loc = data.get("location", {})
        if isinstance(loc, dict):
            address = loc.get("address", venue["address"])
            if isinstance(address, dict):
                address = address.get("streetAddress", venue["address"])
            vname = loc.get("name", venue["name"])
        else:
            address, vname = venue["address"], venue["name"]
        performer = data.get("performer", {})
        artist = performer.get("name", "") if isinstance(performer, dict) else ""
        return {
            "event_name": name, "artist": artist,
            "venue_name": vname, "address": address,
            "start_datetime": start,
            "source_url": data.get("url", venue["url"]),
            "description": data.get("description", "")[:300],
        }
    except Exception:
        return None


def _parse_generic(item, venue):
    try:
        title_el = item.select_one("h1, h2, h3, h4, .title, .name")
        if not title_el:
            return None
        title = title_el.get_text(strip=True)
        date_el = item.select_one("time, .date, .data, .when")
        dt_str = (date_el.get("datetime") or date_el.get_text(strip=True)) if date_el else None
        link_el = item.select_one("a[href]")
        link = link_el["href"] if link_el else venue["url"]
        if link.startswith("/"):
            link = venue["url"].rstrip("/") + link
        return {
            "event_name": title, "artist": "",
            "venue_name": venue["name"], "address": venue["address"],
            "start_datetime": dt_str, "source_url": link, "description": "",
        }
    except Exception:
        return None
