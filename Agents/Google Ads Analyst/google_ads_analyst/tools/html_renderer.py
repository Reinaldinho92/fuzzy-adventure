"""
HTML-rapport renderer voor Google Ads Analyst.

Genereert een volledig zelfstandig HTML-rapport op basis van:
- AdsData object (campagnes, zoekwoorden, etc.)
- tool_results dict (ruwe JSON strings per toolnaam)
- sections list (bullets van Claude in gestructureerd formaat)
"""

from __future__ import annotations

import json
from datetime import datetime

from .excel_parser import AdsData


# ---------------------------------------------------------------------------
# Hulpfuncties
# ---------------------------------------------------------------------------

def _fmt_eur(value: float) -> str:
    return f"€{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _fmt_pct(value: float) -> str:
    return f"{value:.1f}%"


def _rate_cpa(cpa: float, avg_cpa: float) -> str:
    if avg_cpa <= 0:
        return "🟡"
    if cpa < avg_cpa * 0.8:
        return "🟢"
    if cpa < avg_cpa * 1.5:
        return "🟡"
    return "🔴"


def _rate_ctr(ctr: float) -> str:
    if ctr > 3.0:
        return "🟢"
    if ctr > 1.0:
        return "🟡"
    return "🔴"


def _rate_qs(qs: int) -> str:
    if qs >= 7:
        return "🟢"
    if qs >= 4:
        return "🟡"
    return "🔴"


def _rate_is(is_pct: float) -> str:
    if is_pct >= 70.0:
        return "🟢"
    if is_pct >= 40.0:
        return "🟡"
    return "🔴"


def _safe_json(tool_results: dict, key: str) -> dict | list | None:
    raw = tool_results.get(key)
    if not raw:
        return None
    try:
        return json.loads(raw)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Chart helpers
# ---------------------------------------------------------------------------

def _chart_js(chart_id: str, chart_type: str, labels: list, datasets: list, options_extra: str = "") -> str:
    labels_json = json.dumps(labels, ensure_ascii=False)
    datasets_json = json.dumps(datasets, ensure_ascii=False)
    return f"""
<div style="height:300px;position:relative;">
  <canvas id="{chart_id}"></canvas>
</div>
<script>
(function() {{
  var ctx = document.getElementById('{chart_id}').getContext('2d');
  new Chart(ctx, {{
    type: '{chart_type}',
    data: {{
      labels: {labels_json},
      datasets: {datasets_json}
    }},
    options: {{
      responsive: true,
      maintainAspectRatio: false,
      {options_extra}
    }}
  }});
}})();
</script>
"""


# ---------------------------------------------------------------------------
# Sectie-renderers
# ---------------------------------------------------------------------------

def _render_bullets(bullets: list[str]) -> str:
    if not bullets:
        return ""
    items = "".join(f"<li>{b}</li>" for b in bullets)
    return f'<ul class="bullets">{items}</ul>'


def _render_table(headers: list[str], rows: list[list]) -> str:
    if not rows:
        return ""
    head = "".join(f"<th>{h}</th>" for h in headers)
    body = ""
    for row in rows[:8]:
        cells = "".join(f"<td>{cell}</td>" for cell in row)
        body += f"<tr>{cells}</tr>"
    return f'<div class="table-wrap"><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'


def _section_html(section_id: str, title: str, chart_html: str, table_html: str, bullets: list[str]) -> str:
    bullets_html = _render_bullets(bullets)
    return f"""
<section id="{section_id}">
  <h2>{title}</h2>
  {chart_html}
  {table_html}
  {bullets_html}
</section>
"""


# ---------------------------------------------------------------------------
# Per-sectie bouw-functies
# ---------------------------------------------------------------------------

_CHART_COUNTER = [0]


def _uid(prefix: str) -> str:
    _CHART_COUNTER[0] += 1
    return f"{prefix}_{_CHART_COUNTER[0]}"


def _build_campagnes(data: AdsData, bullets: list[str]) -> str:
    campaigns = sorted(data.campaigns, key=lambda c: c.cost, reverse=True)[:8]
    if not campaigns:
        return ""

    total_conv = sum(c.conversions for c in data.campaigns)
    total_cost = sum(c.cost for c in data.campaigns)
    avg_cpa = total_cost / total_conv if total_conv > 0 else 0

    labels = [c.campaign[:30] for c in campaigns]
    datasets = [
        {"label": "Kosten (€)", "data": [round(c.cost, 2) for c in campaigns],
         "backgroundColor": "rgba(26,86,219,0.7)", "borderColor": "#1A56DB", "borderWidth": 1},
        {"label": "Conversies", "data": [round(c.conversions, 1) for c in campaigns],
         "backgroundColor": "rgba(255,153,0,0.7)", "borderColor": "#FF9900", "borderWidth": 1,
         "yAxisID": "y2"},
    ]
    cid = _uid("camp")
    chart = _chart_js(cid, "bar", labels, datasets,
                      'indexAxis: "y", scales: { y: { ticks: { font: { size: 11 } } }, y2: { position: "right", display: false } }')

    headers = ["Campagne", "Kosten", "Klikken", "Conv.", "CPA", "CTR", "Beoordeling"]
    rows = []
    for c in campaigns:
        cpa = c.cost_per_conv if c.cost_per_conv > 0 else (c.cost / c.conversions if c.conversions > 0 else 0)
        beoordeling = _rate_cpa(cpa, avg_cpa) if c.conversions > 0 else _rate_ctr(c.ctr)
        rows.append([
            c.campaign[:40],
            _fmt_eur(c.cost),
            c.clicks,
            round(c.conversions, 1),
            _fmt_eur(cpa) if cpa > 0 else "—",
            _fmt_pct(c.ctr),
            beoordeling,
        ])

    return _section_html("campagnes", "Campagneprestaties", chart,
                         _render_table(headers, rows), bullets)


def _build_zoekwoorden(data: AdsData, bullets: list[str]) -> str:
    kws = sorted(data.keywords, key=lambda k: k.conversions, reverse=True)[:8]
    if not kws:
        return ""

    total_conv = sum(k.conversions for k in data.keywords)
    total_cost = sum(k.cost for k in data.keywords)
    avg_cpa = total_cost / total_conv if total_conv > 0 else 0

    labels = [k.keyword[:30] for k in kws]
    datasets = [
        {"label": "Conversies", "data": [round(k.conversions, 1) for k in kws],
         "backgroundColor": "rgba(26,86,219,0.7)", "borderColor": "#1A56DB", "borderWidth": 1},
    ]
    cid = _uid("kw")
    chart = _chart_js(cid, "bar", labels, datasets, 'indexAxis: "y"')

    headers = ["Zoekwoord", "Match", "Kosten", "Conv.", "CPA", "QS", "Beoordeling"]
    rows = []
    for k in kws:
        cpa = k.cost_per_conv if k.cost_per_conv > 0 else (k.cost / k.conversions if k.conversions > 0 else 0)
        qs_str = str(k.quality_score) if k.quality_score > 0 else "—"
        beoordeling = _rate_cpa(cpa, avg_cpa) if k.conversions > 0 else _rate_ctr(k.ctr)
        rows.append([
            k.keyword[:40],
            k.match_type,
            _fmt_eur(k.cost),
            round(k.conversions, 1),
            _fmt_eur(cpa) if cpa > 0 else "—",
            qs_str,
            beoordeling,
        ])

    return _section_html("zoekwoorden", "Zoekwoorden", chart,
                         _render_table(headers, rows), bullets)


def _build_verspild_budget(tool_results: dict, bullets: list[str]) -> str:
    raw = _safe_json(tool_results, "get_wasted_spend")
    if not raw:
        return ""

    items = []
    for key in ("keywords", "campaigns", "ad_groups"):
        for item in (raw.get(key) or []):
            name = item.get("keyword") or item.get("campaign") or item.get("ad_group") or "—"
            cost = float(item.get("cost", 0))
            clicks = int(item.get("clicks", 0))
            conv = float(item.get("conversions", 0))
            items.append({"name": name, "cost": cost, "clicks": clicks, "conversions": conv})

    items = sorted(items, key=lambda x: x["cost"], reverse=True)[:8]
    if not items:
        return ""

    labels = [i["name"][:30] for i in items]
    datasets = [
        {"label": "Kosten (€)", "data": [round(i["cost"], 2) for i in items],
         "backgroundColor": "rgba(220,53,69,0.7)", "borderColor": "#DC3545", "borderWidth": 1},
    ]
    cid = _uid("waste")
    chart = _chart_js(cid, "bar", labels, datasets, 'indexAxis: "y"')

    headers = ["Zoekwoord/Campagne", "Kosten", "Klikken", "Conv.", "Beoordeling"]
    rows = [[i["name"][:40], _fmt_eur(i["cost"]), i["clicks"], round(i["conversions"], 1), "🔴"] for i in items]

    return _section_html("verspild_budget", "Verspild budget", chart,
                         _render_table(headers, rows), bullets)


def _build_kansen(tool_results: dict, bullets: list[str]) -> str:
    raw = _safe_json(tool_results, "get_search_term_opportunities")
    if not raw:
        return ""
    items = raw if isinstance(raw, list) else raw.get("opportunities") or raw.get("search_terms") or []
    if not items:
        return ""

    items = items[:8]
    headers = ["Zoekterm", "Klikken", "Conv.", "CTR", "Aanbeveling"]
    rows = []
    for item in items:
        st = item.get("search_term", item.get("keyword", "—"))
        clicks = int(item.get("clicks", 0))
        conv = float(item.get("conversions", 0))
        ctr = float(item.get("ctr", 0))
        rows.append([st[:40], clicks, round(conv, 1), _fmt_pct(ctr), "➕ Toevoegen"])

    return _section_html("kansen", "Kansen", "", _render_table(headers, rows), bullets)


def _build_kwaliteitsscore(tool_results: dict, data: AdsData, bullets: list[str]) -> str:
    kws_with_qs = [k for k in data.keywords if k.quality_score > 0]
    if not kws_with_qs:
        return ""

    buckets = {"1-3": 0, "4-6": 0, "7-10": 0}
    for k in kws_with_qs:
        if k.quality_score <= 3:
            buckets["1-3"] += 1
        elif k.quality_score <= 6:
            buckets["4-6"] += 1
        else:
            buckets["7-10"] += 1

    cid = _uid("qs")
    chart = _chart_js(cid, "bar",
                      list(buckets.keys()),
                      [{"label": "Aantal zoekwoorden",
                        "data": list(buckets.values()),
                        "backgroundColor": ["rgba(220,53,69,0.7)", "rgba(255,193,7,0.7)", "rgba(40,167,69,0.7)"],
                        "borderWidth": 1}],
                      "")

    worst = sorted(kws_with_qs, key=lambda k: k.quality_score)[:8]
    headers = ["Zoekwoord", "QS", "Impressies", "Kosten", "Beoordeling"]
    rows = [[k.keyword[:40], k.quality_score, k.impressions, _fmt_eur(k.cost), _rate_qs(k.quality_score)]
            for k in worst]

    return _section_html("kwaliteitsscore", "Kwaliteitsscore", chart,
                         _render_table(headers, rows), bullets)


def _build_vertoningsaandeel(data: AdsData, bullets: list[str]) -> str:
    camps_with_is = [c for c in data.campaigns if c.impression_share > 0]
    if not camps_with_is:
        return ""

    camps_with_is = sorted(camps_with_is, key=lambda c: c.impression_share)[:8]
    labels = [c.campaign[:30] for c in camps_with_is]
    datasets = [
        {"label": "IS%", "data": [round(c.impression_share, 1) for c in camps_with_is],
         "backgroundColor": "rgba(26,86,219,0.7)"},
        {"label": "Verlies Budget%", "data": [round(c.lost_is_budget, 1) for c in camps_with_is],
         "backgroundColor": "rgba(255,193,7,0.7)"},
        {"label": "Verlies Rank%", "data": [round(c.lost_is_rank, 1) for c in camps_with_is],
         "backgroundColor": "rgba(220,53,69,0.7)"},
    ]
    cid = _uid("is")
    chart = _chart_js(cid, "bar", labels, datasets,
                      'indexAxis: "y", scales: { x: { stacked: true }, y: { stacked: true } }')

    headers = ["Campagne", "IS%", "Verlies Budget%", "Verlies Rank%", "Oorzaak", "Beoordeling"]
    rows = []
    for c in camps_with_is:
        if c.lost_is_budget > c.lost_is_rank:
            oorzaak = "Budget"
        elif c.lost_is_rank > 0:
            oorzaak = "Ad Rank"
        else:
            oorzaak = "—"
        rows.append([
            c.campaign[:35],
            _fmt_pct(c.impression_share),
            _fmt_pct(c.lost_is_budget),
            _fmt_pct(c.lost_is_rank),
            oorzaak,
            _rate_is(c.impression_share),
        ])

    return _section_html("vertoningsaandeel", "Vertoningsaandeel", chart,
                         _render_table(headers, rows), bullets)


def _build_periodecomparatie(tool_results: dict, bullets: list[str]) -> str:
    raw = _safe_json(tool_results, "compare_periods")
    if not raw or "error" in raw:
        return ""

    totals = raw.get("totals") or {}
    p1 = totals.get("period1") or {}
    p2 = totals.get("period2") or {}

    if not p1 and not p2:
        return ""

    labels = ["Kosten (€)", "Klikken", "Conversies"]
    p1_vals = [round(float(p1.get("cost", 0)), 2), int(p1.get("clicks", 0)), round(float(p1.get("conversions", 0)), 1)]
    p2_vals = [round(float(p2.get("cost", 0)), 2), int(p2.get("clicks", 0)), round(float(p2.get("conversions", 0)), 1)]

    datasets = [
        {"label": "Periode 1", "data": p1_vals, "backgroundColor": "rgba(26,86,219,0.7)"},
        {"label": "Periode 2", "data": p2_vals, "backgroundColor": "rgba(255,153,0,0.7)"},
    ]
    cid = _uid("period")
    chart = _chart_js(cid, "bar", labels, datasets, "")

    delta = raw.get("delta") or {}
    headers = ["Metric", "Periode 1", "Periode 2", "Delta"]
    rows = [
        ["Kosten", _fmt_eur(float(p1.get("cost", 0))), _fmt_eur(float(p2.get("cost", 0))),
         _fmt_eur(float(delta.get("cost", 0)))],
        ["Klikken", p1.get("clicks", "—"), p2.get("clicks", "—"), delta.get("clicks", "—")],
        ["Conversies", p1.get("conversions", "—"), p2.get("conversions", "—"), delta.get("conversions", "—")],
        ["CPA", _fmt_eur(float(p1.get("cpa", 0))), _fmt_eur(float(p2.get("cpa", 0))),
         _fmt_eur(float(delta.get("cpa", 0)))],
    ]

    return _section_html("periodecomparatie", "Periodecomparatie", chart,
                         _render_table(headers, rows), bullets)


# ---------------------------------------------------------------------------
# Hoofd-renderer
# ---------------------------------------------------------------------------

def render_html(
    data: AdsData,
    tool_results: dict[str, str],
    sections: list[dict],
    data2: AdsData | None = None,
) -> str:
    """
    Genereer een volledig zelfstandig HTML-rapport.

    Args:
        data:         Primaire AdsData
        tool_results: Dict van toolnaam -> ruwe JSON-string
        sections:     List van sectie-dicts met 'id', 'title', 'bullets'
        data2:        Optionele tweede periode (voor periodecomparatie)

    Returns:
        Volledig HTML-document als string
    """
    _CHART_COUNTER[0] = 0  # reset counter per render

    bullets_by_id: dict[str, list[str]] = {}
    for s in sections:
        bullets_by_id[s.get("id", "")] = s.get("bullets", [])

    # Overzicht statistieken
    total_cost = sum(c.cost for c in data.campaigns)
    total_clicks = sum(c.clicks for c in data.campaigns)
    total_conv = sum(c.conversions for c in data.campaigns)
    avg_cpa = total_cost / total_conv if total_conv > 0 else 0
    avg_ctr_raw = [c.ctr for c in data.campaigns if c.impressions > 0]
    avg_ctr = sum(avg_ctr_raw) / len(avg_ctr_raw) if avg_ctr_raw else 0

    date_str = datetime.now().strftime("%d-%m-%Y")
    source_str = ", ".join(data.source_files)

    # Bouw secties
    section_order = [
        "samenvatting", "campagnes", "zoekwoorden", "verspild_budget",
        "kansen", "kwaliteitsscore", "vertoningsaandeel", "periodecomparatie"
    ]

    built_sections: dict[str, str] = {}

    # Samenvatting — alleen bullets
    samenvatting_bullets = bullets_by_id.get("samenvatting", [])
    if samenvatting_bullets:
        built_sections["samenvatting"] = _section_html(
            "samenvatting", "Samenvatting", "", "", samenvatting_bullets)

    if data.campaigns:
        html = _build_campagnes(data, bullets_by_id.get("campagnes", []))
        if html:
            built_sections["campagnes"] = html

    if data.keywords:
        html = _build_zoekwoorden(data, bullets_by_id.get("zoekwoorden", []))
        if html:
            built_sections["zoekwoorden"] = html

    html = _build_verspild_budget(tool_results, bullets_by_id.get("verspild_budget", []))
    if html:
        built_sections["verspild_budget"] = html

    html = _build_kansen(tool_results, bullets_by_id.get("kansen", []))
    if html:
        built_sections["kansen"] = html

    if data.keywords:
        html = _build_kwaliteitsscore(tool_results, data, bullets_by_id.get("kwaliteitsscore", []))
        if html:
            built_sections["kwaliteitsscore"] = html

    html = _build_vertoningsaandeel(data, bullets_by_id.get("vertoningsaandeel", []))
    if html:
        built_sections["vertoningsaandeel"] = html

    if data2 is not None:
        html = _build_periodecomparatie(tool_results, bullets_by_id.get("periodecomparatie", []))
        if html:
            built_sections["periodecomparatie"] = html

    sections_html = "".join(built_sections.get(sid, "") for sid in section_order)

    # Nav links
    nav_labels = {
        "samenvatting": "Samenvatting", "campagnes": "Campagnes",
        "zoekwoorden": "Zoekwoorden", "verspild_budget": "Verspild budget",
        "kansen": "Kansen", "kwaliteitsscore": "Kwaliteitsscore",
        "vertoningsaandeel": "Vertoningsaandeel", "periodecomparatie": "Periodecomparatie",
    }
    nav_items = "".join(
        f'<a href="#{sid}">{nav_labels[sid]}</a>'
        for sid in section_order if sid in built_sections
    )

    stat_cards = f"""
<div class="stat-cards">
  <div class="stat-card">
    <div class="stat-label">Totale kosten</div>
    <div class="stat-value">{_fmt_eur(total_cost)}</div>
  </div>
  <div class="stat-card">
    <div class="stat-label">Klikken</div>
    <div class="stat-value">{total_clicks:,}</div>
  </div>
  <div class="stat-card">
    <div class="stat-label">Conversies</div>
    <div class="stat-value">{round(total_conv, 1)}</div>
  </div>
  <div class="stat-card">
    <div class="stat-label">Gem. CPA</div>
    <div class="stat-value">{_fmt_eur(avg_cpa)}</div>
  </div>
  <div class="stat-card">
    <div class="stat-label">Gem. CTR</div>
    <div class="stat-value">{_fmt_pct(avg_ctr)}</div>
  </div>
</div>
"""

    css = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: 'Inter', sans-serif;
  background: #F8F9FA;
  color: #1F2937;
  line-height: 1.6;
}
header {
  background: #1A56DB;
  color: white;
  padding: 24px 40px;
}
header h1 { font-size: 1.8rem; font-weight: 700; }
header .meta { font-size: 0.85rem; opacity: 0.85; margin-top: 4px; }
nav {
  background: white;
  border-bottom: 1px solid #E5E7EB;
  padding: 0 40px;
  display: flex;
  gap: 0;
  overflow-x: auto;
  position: sticky;
  top: 0;
  z-index: 100;
}
nav a {
  display: inline-block;
  padding: 12px 16px;
  color: #4B5563;
  text-decoration: none;
  font-size: 0.875rem;
  font-weight: 500;
  border-bottom: 3px solid transparent;
  white-space: nowrap;
}
nav a:hover { color: #1A56DB; border-bottom-color: #1A56DB; }
.stat-cards {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  padding: 24px 40px;
  background: white;
  border-bottom: 1px solid #E5E7EB;
}
.stat-card {
  background: #F8F9FA;
  border: 1px solid #E5E7EB;
  border-radius: 8px;
  padding: 16px 24px;
  min-width: 140px;
}
.stat-label { font-size: 0.75rem; color: #6B7280; text-transform: uppercase; letter-spacing: 0.05em; }
.stat-value { font-size: 1.5rem; font-weight: 700; color: #1A56DB; margin-top: 4px; }
main { padding: 0 40px 40px; }
section {
  background: white;
  border-radius: 12px;
  border: 1px solid #E5E7EB;
  padding: 28px;
  margin-top: 24px;
}
section h2 {
  font-size: 1.2rem;
  font-weight: 700;
  color: #111827;
  margin-bottom: 20px;
  padding-bottom: 12px;
  border-bottom: 2px solid #1A56DB;
}
.table-wrap { overflow-x: auto; margin: 20px 0; }
table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.875rem;
}
thead th {
  background: #F3F4F6;
  padding: 10px 12px;
  text-align: left;
  font-weight: 600;
  font-size: 0.8rem;
  color: #374151;
  border-bottom: 2px solid #E5E7EB;
}
tbody td {
  padding: 10px 12px;
  border-bottom: 1px solid #F3F4F6;
  vertical-align: middle;
}
tbody tr:hover { background: #F9FAFB; }
.bullets {
  list-style: none;
  margin-top: 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.bullets li {
  padding: 10px 14px 10px 40px;
  background: #F8F9FA;
  border-left: 3px solid #1A56DB;
  border-radius: 0 6px 6px 0;
  font-size: 0.875rem;
  position: relative;
}
.bullets li::before {
  content: "→";
  position: absolute;
  left: 14px;
  color: #1A56DB;
  font-weight: 700;
}
@media (max-width: 768px) {
  header, .stat-cards, main { padding-left: 16px; padding-right: 16px; }
  nav { padding: 0 16px; }
  .stat-cards { gap: 10px; }
  .stat-card { min-width: 110px; padding: 12px 16px; }
}
"""

    return f"""<!DOCTYPE html>
<html lang="nl">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Google Ads Analyse — {date_str}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <style>
{css}
  </style>
</head>
<body>
<header>
  <h1>Google Ads Analyse</h1>
  <div class="meta">Gegenereerd op {date_str} &nbsp;·&nbsp; Bronbestanden: {source_str}</div>
</header>
<nav>
  {nav_items}
</nav>
{stat_cards}
<main>
{sections_html}
</main>
</body>
</html>
"""
