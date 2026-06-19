# RAPPORT_OUTPUT_PROMPT.md — HTML-bouwhandleiding Google Ads Analyst

Dit bestand is de enige bron van waarheid voor de visuele opmaak van het Google Ads rapport.
De CSS, het HTML-skelet en alle componentstijlen hier zijn **vast** — ze zorgen voor een
consistente, professionele look-and-feel in elk rapport. Claude bepaalt welke secties worden
opgenomen en in welke volgorde, maar past de stijlen nooit aan.

**Absolute regel:** alle getallen in het rapport komen uitsluitend uit de tool-resultaten.
Nooit zelf berekenen, schatten of plaatshoudertekst invullen.

---

## Vaste HTML-basisstructuur

Elk rapport begint met precies deze structuur:

```html
<!DOCTYPE html>
<html lang="nl">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Google Ads Rapport — [Klantnaam] — [Periode]</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.js"></script>
  <style>
    /* [Volledige CSS — zie sectie "Vaste CSS" hieronder] */
  </style>
</head>
<body>
<header>
  <h1>Google Ads Rapport — [Klantnaam]</h1>
  <div class="meta">Gegenereerd op [datum] &nbsp;·&nbsp; Bronbestanden: [bestandsnamen]</div>
</header>
<nav>
  <a href="#samenvatting">Samenvatting</a>
  <!-- Meer nav-links per aanwezige sectie -->
</nav>
<div class="stat-cards">
  <!-- KPI-scorekaarten -->
</div>
<main>
  <!-- Secties -->
</main>
<script>
  /* [Chart.js setup + grafiekcode — zie sectie "Chart.js configuratie" hieronder] */
</script>
</body>
</html>
```

---

## Vaste CSS

Kopieer deze CSS volledig in het `<style>`-blok. Pas de waarden niet aan.

```css
/* --- CSS-variabelen en dark mode --- */
:root {
  --bg: #FFFFFF;
  --bg-secondary: #F7F6F2;
  --text: #1A1915;
  --text-secondary: #5F5E5A;
  --border: #E8E6DF;
  --accent: #1A56DB;
  --green-bg:  #EAF3DE; --green-text:  #3B6D11;
  --red-bg:    #FCEBEB; --red-text:    #A32D2D;
  --amber-bg:  #FAEEDA; --amber-text:  #854F0B;
  --blue-bg:   #E6F1FB; --blue-text:   #185FA5;
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #1A1915;
    --bg-secondary: #242320;
    --text: #F0EFE9;
    --text-secondary: #9C9A94;
    --border: #333128;
    --accent: #4D80E4;
  }
}

/* --- Reset --- */
* { box-sizing: border-box; margin: 0; padding: 0; }

/* --- Body --- */
body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  background: var(--bg-secondary);
  color: var(--text);
  line-height: 1.6;
}

/* --- Header --- */
header {
  background: var(--accent);
  color: #fff;
  padding: 24px 40px;
}
header h1   { font-size: 1.8rem; font-weight: 700; }
header .meta { font-size: 0.85rem; opacity: 0.85; margin-top: 4px; }

/* --- Navigatie --- */
nav {
  background: var(--bg);
  border-bottom: 1px solid var(--border);
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
  color: var(--text-secondary);
  text-decoration: none;
  font-size: 0.875rem;
  font-weight: 500;
  border-bottom: 3px solid transparent;
  white-space: nowrap;
}
nav a:hover { color: var(--accent); border-bottom-color: var(--accent); }

/* --- KPI-scorekaarten --- */
.stat-cards {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  padding: 24px 40px;
  background: var(--bg);
  border-bottom: 1px solid var(--border);
}
.stat-card {
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 16px 24px;
  min-width: 140px;
}
.stat-label { font-size: 0.75rem; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.05em; }
.stat-value { font-size: 1.5rem; font-weight: 700; color: var(--accent); margin-top: 4px; }
.stat-card .delta-pos { color: var(--green-text); font-size: 0.8rem; margin-top: 2px; }
.stat-card .delta-neg { color: var(--red-text);   font-size: 0.8rem; margin-top: 2px; }
.stat-card .delta-neu { color: var(--text-secondary); font-size: 0.8rem; margin-top: 2px; }

/* --- Hoofdinhoud --- */
main { padding: 0 40px 40px; }
section {
  background: var(--bg);
  border-radius: 12px;
  border: 1px solid var(--border);
  padding: 28px;
  margin-top: 24px;
}
section h2 {
  font-size: 1.2rem;
  font-weight: 700;
  color: var(--text);
  margin-bottom: 20px;
  padding-bottom: 12px;
  border-bottom: 2px solid var(--accent);
}

/* --- Tabellen --- */
.tbl, table { width: 100%; border-collapse: collapse; font-size: 0.875rem; }
.tbl th, thead th {
  background: var(--bg-secondary);
  padding: 10px 12px;
  text-align: left;
  font-weight: 600;
  font-size: 0.8rem;
  color: var(--text-secondary);
  border-bottom: 2px solid var(--border);
}
.tbl td, tbody td {
  padding: 10px 12px;
  border-bottom: 1px solid var(--border);
  vertical-align: middle;
}
.tbl tr:last-child td, tbody tr:last-child td { border-bottom: none; }
.tbl tr:hover td, tbody tr:hover td { background: var(--bg-secondary); }
.table-wrap { overflow-x: auto; margin: 20px 0; }

/* Kleurcodering CPA-cellen */
.cpa-good { background: var(--green-bg); color: var(--green-text); }
.cpa-bad  { background: var(--red-bg);   color: var(--red-text); }

/* QS-kleuren */
.qs-low  { background: var(--red-bg);   color: var(--red-text);   font-weight: 600; padding: 2px 6px; border-radius: 3px; }
.qs-mid  { background: var(--amber-bg); color: var(--amber-text); font-weight: 600; padding: 2px 6px; border-radius: 3px; }
.qs-high { background: var(--green-bg); color: var(--green-text); font-weight: 600; padding: 2px 6px; border-radius: 3px; }

/* IS-kleuren */
.is-low  { color: var(--red-text);   font-weight: 600; }
.is-mid  { color: var(--amber-text); font-weight: 600; }
.is-high { color: var(--green-text); font-weight: 600; }

/* Periodecomparatie pijlen */
.delta-up   { color: var(--green-text); font-weight: 600; }
.delta-down { color: var(--red-text);   font-weight: 600; }

/* --- Bullets/aanbevelingen --- */
.bullets, ul.bullets {
  list-style: none;
  margin-top: 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.bullets li {
  padding: 10px 14px 10px 40px;
  background: var(--bg-secondary);
  border-left: 3px solid var(--accent);
  border-radius: 0 6px 6px 0;
  font-size: 0.875rem;
  position: relative;
}
.bullets li::before {
  content: "→";
  position: absolute;
  left: 14px;
  color: var(--accent);
  font-weight: 700;
}

/* Uitlegbullets (max. 5, direct na aanbeveling) */
ul.uitleg-bullets {
  list-style: disc;
  margin: 6px 0 0 20px;
  font-size: 0.82rem;
  color: var(--text-secondary);
  display: flex;
  flex-direction: column;
  gap: 3px;
}

/* --- Badges --- */
.badge { display: inline-block; font-size: 11px; padding: 2px 8px; border-radius: 4px; font-weight: 500; }
.badge-red   { background: var(--red-bg);       color: var(--red-text); }
.badge-green { background: var(--green-bg);      color: var(--green-text); }
.badge-amber { background: var(--amber-bg);      color: var(--amber-text); }
.badge-blue  { background: var(--blue-bg);       color: var(--blue-text); }
.badge-gray  { background: var(--bg-secondary);  color: var(--text-secondary); }

/* --- Alert-blokken --- */
.alert {
  border-left: 3px solid;
  padding: .75rem 1rem;
  border-radius: 0 6px 6px 0;
  font-size: 13px;
  margin-bottom: .75rem;
}
.alert-red   { border-color: #E24B4A; background: var(--red-bg);   color: var(--red-text); }
.alert-amber { border-color: #EF9F27; background: var(--amber-bg); color: var(--amber-text); }
.alert-green { border-color: #639922; background: var(--green-bg); color: var(--green-text); }
.alert strong { display: block; margin-bottom: 2px; }

/* --- Grafiek-containers --- */
.chart-wrap { position: relative; height: 300px; margin: 20px 0; }
.chart-caption { font-size: 0.8rem; color: var(--text-secondary); margin-top: 8px; }

/* --- Responsief --- */
@media (max-width: 768px) {
  header, .stat-cards, main { padding-left: 16px; padding-right: 16px; }
  nav { padding: 0 16px; }
  .stat-cards { gap: 10px; }
  .stat-card { min-width: 110px; padding: 12px 16px; }
}
```

---

## Chart.js configuratie

Voeg dit script **als eerste** toe in het `<script>`-blok, vóór alle grafiekcode:

```javascript
const isDark    = window.matchMedia('(prefers-color-scheme: dark)').matches;
const gridColor = isDark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.06)';
const textColor = isDark ? '#9C9A94' : '#5F5E5A';

Chart.defaults.font.family = "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif";
Chart.defaults.font.size   = 12;
Chart.defaults.color       = textColor;
```

Grafiek-container template (verplicht voor elke grafiek):

```html
<div class="chart-wrap">
  <canvas id="chart-[uniek-id]" aria-label="[beschrijving van de grafiek]" role="img"></canvas>
</div>
<p class="chart-caption">[Korte toelichting — verplicht tekstalternatief voor screenreaders]</p>
```

Gebruik **altijd** `aria-label` op `<canvas>` én een `<p class="chart-caption">` eronder.

---

## Gegevenspopulatie

**Absolute regel: alle getallen komen uit de tool-resultaten. Nooit eigen berekeningen of schattingen.**

Afgeleide metrics zijn toegestaan als de gronddata aanwezig is in de tool-output:
- CPA = kosten ÷ conversies
- CVR = conversies ÷ klikken × 100
- ROAS = conversiewaarde ÷ kosten (alleen als `conv_value > 0`)
- Delta % = (periode2 − periode1) ÷ periode1 × 100 (alleen bij compare_periods)

**Nederlandse getalnotatie (verplicht in elke waarde):**
- Punt als duizendtalscheider, komma als decimaalscheider → `€1.234,56`
- Percentages: één decimaal → `3,2%`
- Geen Engelse notatie (`12,345` of `€1,234.56` is fout)

---

## Vereiste en optionele secties

### Altijd aanwezig (4 verplichte secties)

| Sectie-id | Koptekst | Inhoud |
|-----------|----------|--------|
| `samenvatting` | Samenvatting | KPI-scorekaarten + 3–5 meest opvallende bevindingen |
| `impactacties` | Impactacties voor de specialist | Concrete acties met verwacht effect in € of conversies |
| `klant_update` | Update voor de klant | Positieve formulering, geen jargon, gefocust op voortgang |
| `monitoring` | Punten om in de gaten te houden | Signalen, trends, risico's voor de volgende maand |

### Optioneel (toon alleen als data beschikbaar)

| Sectie-id | Koptekst | Wanneer |
|-----------|----------|---------|
| `campagnes` | Campagneprestaties | Altijd als campagnedata aanwezig |
| `zoekwoorden` | Zoekwoorden | Als zoekwoorddata aanwezig |
| `verspild_budget` | Verspild budget | Als get_wasted_spend resultaten zijn |
| `kansen` | Kansen | Als get_search_term_opportunities resultaten zijn |
| `kwaliteitsscore` | Kwaliteitsscore | Als QS-data aanwezig |
| `vertoningsaandeel` | Vertoningsaandeel | Als IS-data aanwezig |
| `periodecomparatie` | Periodecomparatie | Alleen als twee periodes zijn aangeleverd |

---

## Naamgeving outputbestand

```
rapport_[klantnaam-lowercase-geen-spaties]_[periode-compact].html

Voorbeelden:
  rapport_veriflow_feb-apr2025.html
  rapport_acmecorp_q1-2025.html
  rapport_klantx_jan2025.html
```

Klantnaam haal je uit de data (campagnenamen, bestandsnaam of --focus argument).
Als de naam niet bepaalbaar is, gebruik dan "klant".
