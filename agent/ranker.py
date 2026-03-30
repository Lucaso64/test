import json
import time
import requests

PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"

# Prompt per scoring: valuta ogni evento su tre dimensioni
SYSTEM_PROMPT_SCORE = """Sei un critico musicale esperto di jazz, blues e funk.
Ti vengono forniti eventi musicali live nella provincia di Milano.
Per ciascun evento assegna un punteggio da 1 a 10 basandoti su:
- Notorieta' e rilevanza artistica dell'artista/band (1-4 punti)
- Qualita' e interesse musicale dell'evento (1-3 punti)
- Rarita' e unicita' dell'evento (1-3 punti)

Rispondi SOLO con un JSON array di oggetti, uno per evento, nello stesso ordine in cui li ricevi.
Ogni oggetto deve avere:
- "score": numero intero da 1 a 10
- "description": stringa di massimo 60 parole in italiano che descrive perche' l'evento e' interessante,
  menzionando lo stile musicale, l'artista e cosa rende speciale la serata.

Esempio risposta per 2 eventi:
[
  {"score": 8, "description": "Serata jazz di alto livello con il quartetto di Marco Bianchi..."},
  {"score": 6, "description": "Blues elettrico dalla scena chicagoana con influenze soul..."}
]"""


def rank_events(events, api_key, top_n=20):
    """
    Valuta tutti gli eventi con Perplexity e restituisce i top_n per score.
    Aggiunge 'score' e 'description' a ogni evento.
    """
    # Processa in batch da 15 per non superare il context window
    BATCH_SIZE = 15
    for i in range(0, len(events), BATCH_SIZE):
        batch = events[i:i + BATCH_SIZE]
        _score_batch(batch, api_key)
        if i + BATCH_SIZE < len(events):
            time.sleep(1.5)

    # Ordina per score decrescente e prendi i top_n
    scored = [ev for ev in events if ev.get("score", 0) > 0]
    scored.sort(key=lambda e: e.get("score", 0), reverse=True)
    return scored[:top_n]


def _score_batch(batch, api_key):
    lines = []
    for idx, ev in enumerate(batch):
        text = f"{idx+1}. Evento: {ev['event_name']}"
        if ev.get("artist") and ev["artist"] != ev["event_name"]:
            text += f" | Artista: {ev['artist']}"
        text += f" | Locale: {ev['venue_name']}"
        if ev.get("start_datetime"):
            text += f" | Data: {ev['start_datetime'][:10]}"
        if ev.get("genre_tags"):
            text += f" | Generi: {', '.join(ev['genre_tags'])}"
        if ev.get("description"):
            text += f" | Info: {ev['description'][:300]}"
        lines.append(text)

    payload = {
        "model": "sonar",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT_SCORE},
            {"role": "user", "content": "\n".join(lines)},
        ],
        "temperature": 0.2,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        resp = requests.post(PERPLEXITY_API_URL, json=payload, headers=headers, timeout=45)
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"].strip()

        # Estrai JSON robusto
        start = content.find("[")
        end = content.rfind("]") + 1
        if start == -1 or end == 0:
            raise ValueError("Nessun JSON array trovato nella risposta")
        results = json.loads(content[start:end])

        for idx, ev in enumerate(batch):
            if idx < len(results) and isinstance(results[idx], dict):
                ev["score"] = int(results[idx].get("score", 5))
                ev["description"] = str(results[idx].get("description", "")).strip()
            else:
                ev["score"] = 5
                ev["description"] = ""

    except Exception as e:
        print(f"[Ranker] Errore batch scoring: {e}")
        for ev in batch:
            ev["score"] = 5
            ev["description"] = ""
