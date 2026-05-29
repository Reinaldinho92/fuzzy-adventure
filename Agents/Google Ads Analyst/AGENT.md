# Google Ads Analyst Agent

## Rol
Analyseert Google Ads campagneprestaties op basis van Excel/CSV-exports en levert een
strategisch rapport met concrete optimalisatieaanbevelingen. Richt zich op het vinden van
verspild budget, kansen voor opschaling en structurele verbeterpunten.

## Status
Operationeel — versie 1.0

## Gebruik

```bash
cd "Agents/Google Ads Analyst/google_ads_analyst"

# Installeer dependencies
pip install -r requirements.txt

# Kopieer en vul .env in
cp .env.example .env
# Vul ANTHROPIC_API_KEY in

# Enkele periode
python -m google_ads_analyst campagnes.xlsx

# Meerdere bestanden tegelijk (campagnes + zoekwoorden + zoektermen)
python -m google_ads_analyst campagnes.csv zoekwoorden.csv zoektermen.csv

# Met een specifieke focusvraag
python -m google_ads_analyst data.xlsx --focus "waarom stijgt onze CPA de laatste weken?"

# Twee periodes vergelijken
python -m google_ads_analyst jan.xlsx --vergelijk feb.xlsx

# Kwartaalvergelijking met meerdere bestanden per periode
python -m google_ads_analyst q1_campagnes.csv q1_zoekwoorden.csv --vergelijk q2_campagnes.csv q2_zoekwoorden.csv
```

## Exportinstructies Google Ads

De agent ondersteunt vier rapportniveaus. Exporteer ze apart of combineer in één Excel met meerdere sheets.

### 1. Campagneniveau
1. Google Ads > Campagnes
2. Kolommen: Campagne, Klikken, Vertoningen, CTR, Gem. CPC, Kosten, Conversies, Conversieratio, Kosten/conversie, Dagelijks budget
3. Exporteer als Excel of CSV

### 2. Advertentiegroepniveau
1. Google Ads > Advertentiegroepen
2. Kolommen: Campagne, Advertentiegroep, Klikken, Vertoningen, CTR, Gem. CPC, Kosten, Conversies, Conversieratio, Kosten/conversie
3. Exporteer als Excel of CSV

### 3. Zoekwoordniveau
1. Google Ads > Zoekwoorden
2. Kolommen: Campagne, Advertentiegroep, Zoekwoord, Zoektype, Klikken, Vertoningen, CTR, Gem. CPC, Kosten, Conversies, Conversieratio, Kosten/conversie, **Kwaliteitsscore**
3. Exporteer als Excel of CSV

### 4. Zoektermniveau (aanbevolen voor volledige analyse)
1. Google Ads > Zoekwoorden > Zoektermen
2. Kolommen: Zoekterm, Zoekwoord, Campagne, Advertentiegroep, Zoektype, Klikken, Vertoningen, CTR, Gem. CPC, Kosten, Conversies, Conversieratio, Kosten/conversie
3. Exporteer als Excel of CSV

> **Tip:** Exporteer alle vier niveaus en geef ze mee aan de agent voor de meest complete analyse.

## Analysetools

| Tool | Beschrijving |
|------|-------------|
| `get_overview` | Totale prestaties: kosten, klikken, conversies, CPA, CTR |
| `get_top_campaigns` | Best/slechtst presterende campagnes |
| `get_top_ad_groups` | Best/slechtst presterende advertentiegroepen |
| `get_top_keywords` | Best/slechtst presterende zoekwoorden |
| `get_top_search_terms` | Meest gebruikte zoektermen (uit zoekterm-rapport) |
| `get_wasted_spend` | Hoge kosten, nul conversies — direct besparingspotentieel |
| `get_quality_score_analysis` | Lage kwaliteitsscores per zoekwoord |
| `get_ctr_analysis` | Lage CTR per campagne/advertentiegroep/zoekwoord |
| `get_conversion_analysis` | Conversieratio-analyse, best/slechtst converterend |
| `get_search_term_opportunities` | Zoektermen die als exact zoekwoord toegevoegd kunnen worden |
| `get_negative_keyword_candidates` | Zoektermen die uitsluitingszoekwoorden moeten worden |
| `get_budget_analysis` | Budgetgelimiteerde en onderbenutte campagnes |
| `compare_periods` | Vergelijking twee periodes: delta's in kosten, conversies, CPA |

## Rapportstructuur

Het rapport is ingedeeld in vijf secties:
1. **Samenvatting** — totale KPI's en 2–3 meest opvallende bevindingen
2. **Sterktes** — wat werkt goed en waarom
3. **Prioriteit 1** — directe kansen (hoge impact, lage inspanning)
4. **Prioriteit 2** — structurele verbeteringen (hogere inspanning, grotere impact)
5. **Prioriteit 3** — aandachtspunten en waarschuwingssignalen

## Bestandsstructuur

```
google_ads_analyst/
├── __main__.py          → CLI entry point
├── __init__.py
├── config.py            → API-sleutel en modelconfiguratie
├── requirements.txt
├── .env.example
├── agent/
│   └── __init__.py      → Agent-logica, system prompt, tool-definities
└── tools/
    ├── __init__.py
    ├── excel_parser.py  → Parser voor Google Ads exports (xlsx/csv)
    └── analysis.py      → Analysemodules (tools die de agent aanroept)
```
