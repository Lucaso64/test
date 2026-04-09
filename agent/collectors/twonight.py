import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin


BASE_URL = "https://2night.it"
SOURCE_URL = "https://2night.it/milano/eventi.html"


def collect():
    response = requests.get(
        SOURCE_URL,
        timeout=20,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; MilanoEventsBot/1.0)"
        },
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    results = []
    seen = set()

    for item in soup.select("h3 a[href]"):
        href = (item.get("href") or "").strip()
        title = " ".join(item.get_text(" ", strip=True).split())

        if not href or not title:
            continue

        full_url = urljoin(BASE_URL, href)

        if full_url in seen:
            continue

        seen.add(full_url)

        results.append(
            {
                "source": "2night",
                "city": "Milano",
                "title": title,
                "url": full_url,
            }
        )

    return results
