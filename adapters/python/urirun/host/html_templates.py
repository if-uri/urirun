from __future__ import annotations

import html as _html
from pathlib import Path as _Path

_HERE = _Path(__file__).parent


def docs_nodes_html(profiles: list) -> str:
    rows = []
    for profile in profiles:
        rows.append(
            "<tr>"
            f"<td id=\"{_html.escape(profile['id'])}\"><strong>{_html.escape(profile['label'])}</strong>"
            f"<br><code>{_html.escape(profile['id'])}</code></td>"
            f"<td>{_html.escape(profile['description'])}</td>"
            f"<td><code>{_html.escape(profile['transport'])}</code></td>"
            f"<td><code>{_html.escape(profile['runtime'])}</code></td>"
            f"<td>{_html.escape(', '.join(profile.get('routesHint') or []))}</td>"
            "</tr>"
        )
    return """<!doctype html>
<html lang="pl">
<head>
  <meta charset="utf-8">
  <title>urirun node types</title>
  <style>
    body { font: 15px/1.45 system-ui, sans-serif; margin: 32px; max-width: 1180px; color: #e5e7eb; background: #0f172a; }
    a { color: #67e8f9; } code { color: #bae6fd; }
    table { border-collapse: collapse; width: 100%; margin-top: 18px; }
    th, td { border: 1px solid #334155; padding: 10px; vertical-align: top; }
    th { text-align: left; background: #111827; }
    .subtle { color: #94a3b8; }
  </style>
</head>
<body>
  <h1>Typy node w urirun</h1>
  <p class="subtle">To jest backendowe źródło prawdy używane przez dashboard, discovery i URI object registry.</p>
  <table>
    <thead><tr><th>Typ</th><th>Kiedy używać</th><th>Transport</th><th>Runtime</th><th>Typowe URI</th></tr></thead>
    <tbody>""" + "\n".join(rows) + """</tbody>
  </table>
  <h2>Zasada wyboru komponentu</h2>
  <p>Jeśli komponent żyje jako proces i ma port/status, zrób z niego <strong>service</strong>.
  Jeśli dostarcza ograniczoną zdolność URI, zrób <strong>connector</strong>.
  Jeśli jest żywym widokiem, zrób <strong>widget</strong>.
  Jeśli jest skończonym plikiem lub raportem, zrób <strong>artifact</strong>.</p>
  <p><a href="/">Powrót do dashboardu</a></p>
</body>
</html>"""


INDEX_HTML = (_HERE / "dashboard.html").read_text(encoding="utf-8")

NODE_TYPES_DOC_HTML = (_HERE / "node-types.html").read_text(encoding="utf-8")

SCANNER_HTML = (_HERE / "scanner.html").read_text(encoding="utf-8")
