from datetime import date
from jinja2 import Template

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Musica Live - Provincia di Milano</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: 'Segoe UI', sans-serif; background: #0f0f0f; color: #f0f0f0; }
  header { background: #1a1a2e; padding: 2rem; text-align: center; border-bottom: 2px solid #e94560; }
  header h1 { font-size: 2rem; color: #e94560; }
  header p { color: #aaa; margin-top: 0.5rem; }
  .controls { padding: 1rem 2rem; background: #16213e; display: flex; gap: 1rem; flex-wrap: wrap; align-items: center; }
  .controls input, .controls select { padding: 0.5rem 1rem; border-radius: 6px; border: 1px solid #333; background: #0f3460; color: #fff; font-size: 0.9rem; }
  .controls input { flex: 1; min-width: 200px; }
  .stats { padding: 0.5rem 2rem; background: #0a0a1a; color: #888; font-size: 0.85rem; }
  .events-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap: 1.2rem; padding: 1.5rem 2rem; }
  .card { background: #1a1a2e; border-radius: 10px; padding: 1.2rem; border-left: 4px solid #e94560; transition: transform 0.2s; }
  .card:hover { transform: translateY(-3px); }
  .card-date { font-size: 0.8rem; color: #e94560; font-weight: bold; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 0.4rem; }
  .card-title { font-size: 1.1rem; font-weight: bold; color: #fff; margin-bottom: 0.3rem; }
  .card-artist { font-size: 0.9rem; color: #ccc; margin-bottom: 0.5rem; }
  .card-venue { font-size: 0.85rem; color: #aaa; margin-bottom: 0.3rem; }
  .card-address { font-size: 0.8rem; color: #888; margin-bottom: 0.7rem; }
  .tags { display: flex; flex-wrap: wrap; gap: 0.4rem; margin-bottom: 0.7rem; }
  .tag { background: #0f3460; color: #53d8fb; padding: 0.2rem 0.6rem; border-radius: 20px; font-size: 0.75rem; }
  .card-link { display: inline-block; padding: 0.3rem 0.8rem; background: #e94560; color: #fff; border-radius: 5px; text-decoration: none; font-size: 0.8rem; }
  .card-link:hover { background: #c73652; }
  .hidden { display: none; }
  footer { text-align: center; padding: 1.5rem; color: #555; font-size: 0.8rem; border-top: 1px solid #222; margin-top: 2rem; }
</style>
</head>
<body>
<header>
  <h1>Musica Live - Provincia di Milano</h1>
  <p>{{ date_from }} &mdash; {{ date_to }} &nbsp;&bull;&nbsp; {{ total }} eventi trovati</p>
</header>
<div class="controls">
  <input type="text" id="search" placeholder="Cerca artista, locale, genere..." oninput="filterEvents()">
  <select id="genre-filter" onchange="filterEvents()">
    <option value="">Tutti i generi</option>
    {% for g in genres %}<option value="{{ g }}">{{ g }}</option>{% endfor %}
  </select>
</div>
<div class="stats" id="stats">Mostrando {{ total }} eventi</div>
<div class="events-grid" id="grid">
{% for ev in events %}
  <div class="card" data-search="{{ (ev.event_name ~ ' ' ~ ev.artist ~ ' ' ~ ev.venue_name ~ ' ' ~ (ev.genre_tags | join(' '))).lower() }}" data-genres="{{ ev.genre_tags | join(',') }}">
    <div class="card-date">{{ ev.start_datetime[:10] if ev.start_datetime else 'Data n.d.' }}{% if ev.start_datetime and ev.start_datetime|length > 10 %} &bull; ore {{ ev.start_datetime[11:16] }}{% endif %}</div>
    <div class="card-title">{{ ev.event_name }}</div>
    {% if ev.artist and ev.artist != ev.event_name %}<div class="card-artist">{{ ev.artist }}</div>{% endif %}
    <div class="card-venue">{{ ev.venue_name }}</div>
    <div class="card-address">{{ ev.address }}</div>
    <div class="tags">{% for tag in ev.genre_tags %}<span class="tag">{{ tag }}</span>{% endfor %}</div>
    {% if ev.source_url %}<a class="card-link" href="{{ ev.source_url }}" target="_blank">Dettagli</a>{% endif %}
  </div>
{% else %}
  <p style="color:#888;grid-column:1/-1;text-align:center;padding:3rem">Nessun evento trovato.</p>
{% endfor %}
</div>
<footer>Aggiornato il {{ generated_at }} &bull; Dati da Eventbrite, ViviMilano, Zero Milano e siti dei locali</footer>
<script>
function filterEvents() {
  const q = document.getElementById('search').value.toLowerCase();
  const g = document.getElementById('genre-filter').value.toLowerCase();
  const cards = document.querySelectorAll('.card');
  let visible = 0;
  cards.forEach(c => {
    const matchQ = !q || c.dataset.search.includes(q);
    const matchG = !g || c.dataset.genres.toLowerCase().includes(g);
    if (matchQ && matchG) { c.classList.remove('hidden'); visible++; }
    else { c.classList.add('hidden'); }
  });
  document.getElementById('stats').textContent = 'Mostrando ' + visible + ' eventi';
}
</script>
</body>
</html>
"""


def generate_html(events, output_path, date_from, date_to):
    from datetime import datetime
    import pytz
    milan_tz = pytz.timezone("Europe/Rome")
    now_str = datetime.now(milan_tz).strftime("%d/%m/%Y %H:%M")

    # Raccogli tutti i generi unici
    all_genres = sorted({tag for ev in events for tag in ev.get("genre_tags", [])})

    tmpl = Template(HTML_TEMPLATE)
    html = tmpl.render(
        events=events,
        genres=all_genres,
        total=len(events),
        date_from=date_from.strftime("%d/%m/%Y"),
        date_to=date_to.strftime("%d/%m/%Y"),
        generated_at=now_str,
    )
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[HTML] Scritti {len(events)} eventi in {output_path}")
