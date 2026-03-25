import json
import time
import requests

PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"
BATCH_SIZE = 10

SYSTEM_PROMPT = """Sei un esperto di musica. Ti vengono dati titoli e descrizioni di eventi musicali live.
Per ciascun evento restituisci una lista di tag di genere musicale.
Regole:
- Massimo 5 tag per evento, in minuscolo
- Usa italiano o inglese (es: rock, jazz, blues, funk, soul, hip-hop, reggae, ska, punk,
  indie, pop, folk, country, metal, alternative, r&b, gospel, world music, latin,
  bossa nova, afrobeat, elettronica, ambient, post-rock, progressive, experimental)
- Se non hai info sufficienti usa ["live music"]
- NON usare mai: classica, lirica, opera, dj set, dj
Rispondi SOLO con un JSON array di array (uno per evento, stesso ordine).
Esempio per 2 eventi: [["rock","alternative"],["jazz","blues"]]"""


def classify_genres(events, api_key):
    for i in range(0, len(events), BATCH_SIZE):
        batch = events[i:i + BATCH_SIZE]
        _classify_batch(batch, api_key)
        if i + BATCH_SIZE < len(events):
            time.sleep(1)
    return events


def _classify_batch(batch, api_key):
    lines = []
    for idx, ev in enumerate(batch):
        text = f"{idx+1}. {ev['event_name']}"
        if ev.get("artist") and ev["artist"] != ev["event_name"]:
            text += f" | Artista: {ev['artist']}"
        if ev.get("description"):
            text += f" | {ev['description'][:200]}"
        lines.append(text)

    payload = {
        "model": "sonar",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": "\n".join(lines)},
        ],
        "temperature": 0.1,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    try:
        resp = requests.post(PERPLEXITY_API_URL, json=payload, headers=headers, timeout=30)
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"].strip()
        start = content.find("[")
        end = content.rfind("]") + 1
        tags_list = json.loads(content[start:end])
        for idx, ev in enumerate(batch):
            if idx < len(tags_list) and isinstance(tags_list[idx], list):
                ev["genre_tags"] = [str(t).lower().strip() for t in tags_list[idx] if t]
            else:
                ev["genre_tags"] = ["live music"]
    except Exception as e:
        print(f"[Classifier] Errore batch: {e}")
        for ev in batch:
            ev["genre_tags"] = ["live music"]
