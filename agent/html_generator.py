from jinja2 import Template

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Top {{ top_n }} Jazz Blues Funk - Milano</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: 'Segoe UI', sans-serif; background: #0a0a0a; color: #f0f0f0; }
  header { background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); padding: 2.5rem 2rem; text-align: center; border-bottom: 3px solid #f0a500; }
  header h1 { font-size: 2.2rem; color: #f0a500; letter-spacing: 2px; }
  header .subtitle { color: #aaa; margin-top: 0.6rem; font-size: 1rem; }
  header .subtitle span { color: #f0a500; font-weight: bold; }
  .search-bar { padding: 1.2rem 2rem; background: #111; display: flex; gap: 1rem; flex-wrap: wrap; align-items: center; border-bottom: 1px solid #222; }
  .search-bar input { flex: 1; min-width: 220px; padding: 0.6rem 1.2rem; border-radius: 25px; border: 1px solid #333; background: #1a1a2e; color: #fff; font-size: 0.9rem; outline: none; }
  .search-bar input:focus { border-color: #f0a500; }
  .stats { padding: 0.6rem 2rem; background: #0a0a0a; color: #666; font-size: 0.82rem; }
  .events-list { max-width: 900px; margin: 0 auto; padding: 1.5rem 1.5rem; display: flex; flex-direction: column; gap: 1.4rem; }
  .card { background: #111827; border-radius: 12px; padding: 1.5rem; border-left: 5px solid #f0a500; position: relative; transition: transform 0.2s, box-shadow 0.2s; }
  .card:hover { transform: translateX(4px); box-shadow: -4px 0 20px rgba(240,165,0,0.15); }
  .card-rank { position: absolute; top: 1.2rem; right: 1.2rem; background: #f0a500; color: #000; font-weight: bold; font-size: 0.85rem; width: 34px; height: 34px; border-radius: 50%; display: flex; align-items: center; justify-content: center; }
  .card-score-bar { position: absolute; top: 0; left: 0; height: 3px; border-radius: 0 0 0 12px; background: linear-gradient(90deg, #f0a500, #ff6b35); }
  .card-date { font-size: 0.78rem; color: #f0a500; font-weight: bold; text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 0.5rem; }
  .card-title { font-size: 1.25rem; font-weight: bold; color: #fff; margin-bottom: 0.3rem; padding-right: 2.5rem; }
  .card-artist { font-size: 0.95rem; color: #d4a017; margin-bottom: 0.6rem; font-style: italic; }
  .card-description { font-size: 0.9rem; color: #ccc; line-height: 1.6; margin-bottom: 0.9rem; border-left: 2px solid #333; padding-left: 0.8rem; }
  .card-meta { display: flex; flex-wrap: wrap; gap: 1rem; margin-bottom: 0.8rem; font-size: 0.85rem; }
  .card-venue { color: #9ca3af; }
  .card-venue span { color: #e5e7eb; font-weight: 500; }
  .card-address { color: #6b7280; }
  .tags { display: flex; flex-wrap: wrap; gap: 0.4rem; margin-bottom: 0.9rem; }
  .tag { background: #1e3a5f; color: #60a5fa; padding: 0.2rem 0.7rem; border-radius: 20px; font-size: 0.75rem; font-weight: 500; }
  .card-link { display: inline-block; padding: 0.4rem 1rem; background: transparent; color: #f0a500; border: 1px solid #f0a500; border-radius: 6px; text-decoration: none; font-size: 0.82rem; transition: all 0.2s; }
  .card-link:hover { background: #f0a500; color: #000; }
  .hidden { display: none; }
  footer { text-align: center; padding: 2rem; color: #444; font-size: 0.78rem; border-top: 1px solid #1a1a1a; margin-top: 1rem; }
  @media (max-width: 600px) { .events-list { padding: 1rem; } .card { padding: 1.2rem; } }
</style>
</head>
<body>
<header>
  <h1>Top {{ top_n }} Jazz &bull; Blues &bull; Funk</h1>
  <p class="subtitle">Provincia di Milano &nbsp;&bull;&nbsp; <span>{{ date_from }}</span> &mdash; <span>{{ date_to }}</span> &nbsp;&bull;&nbsp; Selezionati da <span>{{ total_found }}</span> eventi</p>
</header>
<div class="search-bar">
  <input type="text" id="search" placeholder="Cerca artista, locale, genere..." oninput="filterEvents()">
</div>
<div class="stats" id="stats">Mostrando {{ events|length }} eventi</div>
<div class="events-list" id="list">
{% for ev in events %}
{% set rank = loop.index %}
  <div class="card" data-search="{{ (ev.event_name ~ ' ' ~ ev.artist ~ ' ' ~ ev.venue_name ~ ' ' ~ (ev.genre_tags|join(' ')) ~ ' ' ~ ev.description).lower() }}">
    <div class="card-score-bar" style="width: {{ (ev.score|default(5)) * 10 }}%"></div>
    <div class="card-rank">#{{ rank }}</div>
    <div class="card-date">
      {{ ev.start_datetime[:10] if ev.start_datetime else 'Data n.d.' }}
      {%- if ev.start_datetime and ev.start_datetime|length > 16 %} &bull; ore {{ ev.start_datetime[11:16] }}{%- endif %}
    </div>
    <div class="card-title">{{ ev.event_name }}</div>
    {% if ev.artist and ev.artist != ev.event_name %}
    <div class="card-artist">{{ ev.artist }}</div>
    {% endif %}
    {% if ev.description %}
    <div class="card-description">{{ ev.description }}</div>
    {% endif %}
    <div class="card-meta">
      <div class="card-venue">Locale: <span>{{ ev.venue_name }}</span></div>
      {% if ev.address %}<div class="card-address">{{ ev.address }}</div>{% endif %}
    </div>
    <div class="tags">{% for tag in ev.genre_tags %}<span class="tag">{{ tag }}</span>{% endfor %}</div>
    {% if ev.source_url %}<a class="card-link" href="{{ ev.source_url }}" target="_blank">Dettagli &rarr;</a>{% endif %}
  </div>
{% else %}
  <p style="color:#666;text-align:center;padding:3rem">Nessun evento trovato.</p>
{% endfor %}
</div>
<footer>Aggiornato il {{ generated_at }} &bull; Fonti: Eventbrite, ViviMilano, Zero Milano, locali diretti &bull; Ranking AI by Perplexity</footer>
<script>
function filterEvents() {
  const q = document.getElementById('search').value.toLowerCase();
  const cards = document.querySelectorAll('.card');
  let visible = 0;
  cards.forEach(c => {
    const match = !q || c.dataset.search.includes(q);
    c.classList.toggle('hidden', !match);
    if (match) visible++;
  });
  document.getElementById('stats').textContent = 'Mostrando ' + visible + ' eventi';
}
</script>
</body>
</html>
"""


def generate_html(events, output_path, date_from, date_to, top_n=20):
    from datetime import datetime
    import pytz
    milan_tz = pytz.timezone("Europe/Rome")
    now_str = datetime.now(milan_tz).strftime("%d/%m/%Y %H:%M")

    tmpl = Template(HTML_TEMPLATE)
    html = tmpl.render(
        events=events,
        top_n=top_n,
        total_found=len(events),
        date_from=date_from.strftime("%d/%m/%Y"),
        date_to=date_to.strftime("%d/%m/%Y"),
        generated_at=now_str,
    )
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[HTML] Scritti {len(events)} eventi top in {output_path}")
