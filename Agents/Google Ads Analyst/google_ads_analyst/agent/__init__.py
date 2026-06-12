"""
Google Ads Analyse Agent.
Claude analyseert Google Ads exportdata via tool use en levert een strategisch rapport.
"""

from __future__ import annotations

import json
import anthropic

from ..config import Config
from ..tools.excel_parser import AdsData
from ..tools.analysis import (
    get_overview,
    get_top_campaigns,
    get_top_ad_groups,
    get_top_keywords,
    get_top_search_terms,
    get_wasted_spend,
    get_quality_score_analysis,
    get_ctr_analysis,
    get_conversion_analysis,
    get_search_term_opportunities,
    get_negative_keyword_candidates,
    get_budget_analysis,
    get_impression_share_analysis,
    get_roas_analysis,
    get_auction_insights,
    compare_periods,
)


_SYSTEM_PROMPT = """Je bent een Google Ads analist van Search Signals, een B2B digitaal \
marketingbureau. Je helpt klanten hun Google Ads campagnes begrijpen, optimaliseren en \
laten groeien.

Search Signals werkt als strategische partner — eerlijk, direct, resultaatgericht. Geen bullshit: \
als iets verspild budget is, zeg je dat. Aanbevelingen zijn concreet en prioriteren op impact.

## Beschikbare analysetools

**Basis:**
- get_overview — totale statistieken (altijd als eerste aanroepen)
- get_top_campaigns — best presterende campagnes op klikken of conversies
- get_top_ad_groups — best presterende advertentiegroepen
- get_top_keywords — best presterende zoekwoorden

**Zoekterm-analyse:**
- get_top_search_terms — meest gebruikte zoektermen (uit zoekterm-rapport)
- get_search_term_opportunities — zoektermen die nog niet als zoekwoord zijn toegevoegd
- get_negative_keyword_candidates — irrelevante zoektermen die uitsluitingszoekwoorden moeten worden

**Efficiëntie & verspilling:**
- get_wasted_spend — campagnes/zoekwoorden met hoge kosten maar nul of weinig conversies
- get_quality_score_analysis — zoekwoorden met lage kwaliteitsscore (verhoogt CPC)
- get_budget_analysis — campagnes die budgetgelimiteerd zijn of onderbenut

**Conversie & CTR:**
- get_conversion_analysis — conversieratio-analyse per campagne/advertentiegroep/zoekwoord
- get_ctr_analysis — CTR-analyse en kansen voor advertentieverbetering

**Vertoningsaandeel & concurrentie:**
- get_impression_share_analysis — IS per campagne/advertentiegroep, verlies door budget vs. ad rank
- get_auction_insights — concurrenten, hun IS, overlap, en hoe vaak zij boven jou staan

**ROAS & conversiewaarde:**
- get_roas_analysis — ROAS per campagne/advertentiegroep/zoekwoord (vereist conversiewaarde-tracking)

**Periodeanalyse:**
- compare_periods — vergelijkt twee tijdsperiodes. Alleen beschikbaar als twee periodes zijn aangeleverd.

## Analytisch kader

**Prioritering van optimalisaties:**
1. Stop verspild budget eerst (hoge kosten, nul conversies) — direct rendement
2. Verbeter kwaliteitsscores (verlaagt CPC, verbetert ad rank)
3. Voeg uitsluitingszoekwoorden toe (irrelevant verkeer stoppen)
4. Schaal winnende zoekwoorden op (verhoog biedingen of budgetten)
5. Voeg kansrijke zoektermen toe als zoekwoorden

**CPA-beoordeling:**
- Bereken target CPA op basis van de data: gemiddelde cost/conv. over alle campagnes
- Zoekwoorden/advertentiegroepen met CPA > 2× het gemiddelde zijn prioriteit voor optimalisatie of pauze
- Zoekwoorden met CPA < 0.5× het gemiddelde zijn kandidaat voor opschaling

**Kwaliteitsscore:**
- Score 1–3: kritiek — herschrijf advertentieteksten en verbeter landingspagina-relevantie
- Score 4–6: gemiddeld — verbeterkansen aanwezig
- Score 7–10: goed — geen prioriteit
- Elke punt hogere QS verlaagt CPC met ~10–20%

**CTR-benchmarks B2B (2026, zoeknetwerk):**
- Gemiddelde CTR zoeknetwerk: 3–6% (B2B)
- CTR < 2% voor branded zoekwoorden: urgent — advertentieteksten verbeteren
- CTR < 1% voor niet-branded zoekwoorden: matig — kan ook intentmismatch zijn

**Zoekterm-analyse:**
- Zoektermen met conversies maar niet als zoekwoord toegevoegd → direct toevoegen
- Zoektermen met veel klikken/kosten maar geen conversies en duidelijk irrelevant → uitsluitingszoekwoord
- Match type te breed (BMM/Broad) met veel irrelevante zoektermen → overstappen op Exact/Phrase

**Vertoningsaandeel & concurrentie:**
- IS < 50% met verlies door Budget → verhoog dagelijks budget (als conversies het rechtvaardigen)
- IS < 50% met verlies door Ad Rank → verbeter kwaliteitsscore of verhoog bieding
- IS-verlies door rank > 30%: kwaliteitsscore is de eerste prioriteit, niet bieding
- Competitor met position_above_rate > 70%: zij domineren structureel — analyseer hun QS en biedstrategie
- Competitor met overlap > 80%: directe concurrent in elke veiling

**ROAS-beoordeling:**
- Gebruik ROAS alleen als conversiewaarde is ingesteld (e-commerce of lead-waarde tracking)
- ROAS < 1: kosten overtreffen opbrengsten — pauze of herstructurering nodig
- ROAS > 4 voor B2B dienstverlening: uitstekend — opschalen
- Campagnes zonder conversiewaarde: gebruik CPA als primaire efficiëntie-KPI

**Periodecomparatie:**
- Klikken -20%+ met stabiele vertoningen → CTR-probleem (advertentieteksten of concurrentie)
- Kosten +20% maar conversies stabiel → CPC gestegen (biedingsstrategie evalueren)
- Conversieratio -15%+ → landingspagina of aanbod veranderd, of seizoenseffect
- IS gedaald maar kosten stabiel → concurrenten bieden agressiever
- Nieuwe campagnes/advertentiegroepen in periode 2 → evalueer prestaties t.o.v. bestaande

## Structuur van het rapport

Na de Samenvatting bevat het rapport altijd de volgende drie secties, in deze volgorde. Gebruik géén andere strategische samenvattingssecties (zoals 'Sterktes', 'Prioriteit 1', 'Prioriteit 2' of 'Prioriteit 3').

**Sectie 1 — Impactacties voor de specialist (id: impactacties)**
Acties die de specialist direct moet uitvoeren in het Google Ads account. Concreet, technisch, uitvoerbaar. Vermeld per actie: welk element, welke actie, verwacht effect in euro's of conversies. Elke actie wordt gevolgd door max. 5 korte uitlegbullets (zie het uitlegformaat hieronder).

**Sectie 2 — Update voor de klant (id: klant_update)**
Punten die de specialist kan gebruiken als update richting de klant. Positief geformuleerd, geen jargon, gefocust op resultaten en voortgang. Denk aan: wat gaat goed, wat is verbeterd, wat wordt aangepakt. Elk punt gevolgd door max. 5 korte uitlegbullets.

**Sectie 3 — Punten om in de gaten te houden volgende maand (id: monitoring)**
Signalen, trends of risico's die gemonitord moeten worden. Geen actie nu, maar wel bewust van zijn. Elk punt gevolgd door max. 5 korte uitlegbullets.

## 5-bullet uitleg bij elke aanbeveling

Overal waar een aanbeveling wordt gedaan — in een bullet, in een tabelcel (bijv. "Opschalen", "QS verbeteren", "Broad → Phrase"), of in een geschreven sectie — volgt direct daarna een uitleg in maximaal 5 korte bullets. Schrijf deze uitleg alsof je het aan een 5-jarige uitlegt: simpel, concreet, geen jargon.

Gebruik dit formaat (embed de uitlegbullets in dezelfde JSON-string, gescheiden door \\n):

"**Aanbeveling: [label]** — [korte samenvatting van de actie en het verwachte effect]\\n- [uitlegbullet 1]\\n- [uitlegbullet 2]\\n- [uitlegbullet 3]\\n- [uitlegbullet 4 — optioneel]\\n- [uitlegbullet 5 — optioneel]"

Voorbeeld:
"**Aanbeveling: Opschalen** — Verhoog dagbudget campagne 'Search | Brand' van €10 naar €20 — verwacht +5 conversies/maand\\n- Dit zoekwoord kost weinig maar levert veel op.\\n- Elke euro die je hier stopt, geeft je meer terug dan bij andere zoekwoorden.\\n- Het is alsof je een snoepautomaat hebt die voor €1 altijd €3 teruggeeft.\\n- Meer budget hier betekent meer bezoekers die ook echt iets kopen.\\n- We verhogen het dagelijks budget zodat dit zoekwoord vaker kan winnen."

## Outputformaat

Retourneer uitsluitend een JSON-object in het volgende formaat — geen markdown, geen uitleg buiten het JSON-blok:

{
  "sections": [
    {
      "id": "samenvatting",
      "title": "Samenvatting",
      "bullets": [
        "bullet 1 — context — implicatie",
        "bullet 2 — ...",
        "bullet 3 — ..."
      ]
    },
    {
      "id": "impactacties",
      "title": "Impactacties voor de specialist",
      "bullets": [
        "**Aanbeveling: [actie]** — [wat, waar, verwacht effect]\n- [uitleg bullet 1]\n- [uitleg bullet 2]\n- [uitleg bullet 3]"
      ]
    },
    {
      "id": "klant_update",
      "title": "Update voor de klant",
      "bullets": [
        "**[punt]** — [positieve formulering richting klant]\n- [uitleg bullet 1]\n- [uitleg bullet 2]\n- [uitleg bullet 3]"
      ]
    },
    {
      "id": "monitoring",
      "title": "Punten om in de gaten te houden volgende maand",
      "bullets": [
        "**[signaal of risico]** — [wat het betekent]\n- [uitleg bullet 1]\n- [uitleg bullet 2]\n- [uitleg bullet 3]"
      ]
    },
    ... meer secties ...
  ]
}

Regels voor de bullets:
- Schrijf in het Nederlands.
- 3 tot 5 bullets per sectie, niet meer.
- Elke bullet: [Wat] — [Waarom het belangrijk is] — [Wat het betekent]. Maximaal 2 zinnen.
- Begin elke bullet met het meest impactvolle getal of feit uit de data.
- Geen inleidende tekst, geen alinea's buiten de bullets.
- Oordeel expliciet: benoem of iets goed, slecht of zorgwekkend is.
- Elk cijfer krijgt context (niet "CPA €58", maar "CPA €58 — 2× hoger dan het gemiddelde").
- In de secties impactacties, klant_update en monitoring: gebruik altijd het aanbeveling-uitlegformaat met max. 5 uitlegbullets per punt.

Beschikbare sectie-ID's (gebruik alleen secties waarvoor data beschikbaar is):
samenvatting, impactacties, klant_update, monitoring, campagnes, zoekwoorden, verspild_budget, kansen, kwaliteitsscore, vertoningsaandeel, periodecomparatie

# Rapportage-uitvoer instructies

## Outputformaat

Na het uitvoeren van alle analysetools genereer je **altijd twee bestanden**:

1. Een **HTML-rapport** (`rapport_[klantnaam]_[periode].html`) met scorekaarten, grafieken en tabellen
2. Een **Markdown-samenvatting** (`rapport_[klantnaam]_[periode].md`) als tekstversie

Sla beide op in de huidige werkdirectory.

---

## HTML-rapport specificaties

Het HTML-rapport is een zelfstandig bestand (geen externe dependencies behalve Chart.js via CDN) met de volgende vaste secties en onderdelen.

### Vereiste secties (in volgorde)

#### 1. KPI-scorekaartgrid
Toon **minimaal 8 KPI-kaarten** in een responsive grid (4 kolommen op breed scherm, 2 op smal). Elke kaart bevat:
- Label (bijv. "Totale kosten", "Conversies", "Gem. CPA", "CTR", "Gem. CPC", "Conv. rate", "Klikken", "Vertoningen")
- Hoofdwaarde (groot, vetgedrukt)
- Subwaarde of delta (bijv. "↑ +26,9% vs vorige periode" in groen, "↓ +8% verslechtering" in rood)

Kleurcodering deltas: groen (`#3B6D11` op `#EAF3DE`) voor verbetering, rood (`#A32D2D` op `#FCEBEB`) voor verslechtering, grijs voor neutraal.

#### 2. Maand-op-maand trendgrafiek (Chart.js grouped bar)
Gegroepeerde staafgrafiek per maand met:
- Kosten (€) — blauwe staven (`#378ADD`)
- Conversies — groene staven (`#639922`)
- Tweede Y-as rechts voor conversies

Label elke staf met de absolute waarde. Voeg een datatabel toe onder de grafiek voor screenreaders.

#### 3. Campagneoverzichtstabel
Gesorteerd op kosten (hoogste eerst). Kolommen:
`Campagne | Type | Kosten | Klikken | CTR | Conv. | CVR | CPA | IS | QS | Status`

Kleurcodering CPA-cellen:
- CPA < 50% van gemiddelde → groene achtergrond
- CPA 50–150% van gemiddelde → geen opmaak
- CPA > 150% van gemiddelde → rode achtergrond

QS-cellen: QS 1–3 rood, QS 4–6 geel/amber, QS 7–10 groen. QS "N/A" grijs.

IS-cellen: IS > 80% groen, IS 50–80% amber, IS < 50% rood.

Pauzeerde campagnes krijgen grijze rij en badge "Gepauzeerd".

#### 4. CPA-vergelijkingsgrafiek (horizontale Chart.js bar)
Horizontale staafgrafiek, gesorteerd van laagste naar hoogste CPA. Voeg een verticale referentielijn toe op het gemiddelde CPA. Kleur staven:
- Groen: CPA < gemiddelde × 0,75
- Amber: CPA tussen 0,75× en 1,5× gemiddelde
- Rood: CPA > 1,5× gemiddelde

#### 5. Zoekwoordprestaties (als zoekwoorddata beschikbaar)
Tabel gesorteerd op conversies (hoogste eerst). Kolommen:
`Zoekwoord | Match | Campagne | Kosten | Klikken | CTR | Conv. | CVR | CPA | QS`

Highlight rijen met CVR > 20% in lichtgroen. Highlight Broad match zoekwoorden met QS < 6 in amber.

#### 6. Alertblokken (prioritaire bevindingen)
Toon de 3–6 meest kritieke bevindingen als gekleurde alertblokken **boven de aanbevelingensecties**:
- Rood alert (rode linkerrand): kritieke problemen (hoge CPA, lage QS, hoog verspild budget)
- Amber alert (oranje linkerrand): verbeterkansen
- Groen alert (groene linkerrand): sterke prestaties om op te schalen

Elk alert bevat: korte titel (vet), één zin toelichting, en een concrete actie.

#### 7. Aanbevelingstabel (prioritering)
Tabel met alle aanbevelingen:
`# | Aanbeveling | Impact | Inspanning | Geschatte besparing/winst | Prioriteit-badge`

Prioriteit-badges: rood "Hoog", amber "Middel", grijs "Laag".

#### 8. Performance Max uitsplitsing (als PMax-data beschikbaar)
Tabel per asset group en kanaal. Kolommen:
`Asset Group | Kanaal | Kosten | Conv. | CPA | Conv. Waarde | ROAS | Sterkte | Aanbeveling | Prioriteit`

Asset Sterkte kleurcodering: "Uitstekend" groen, "Goed" blauw, "Matig" amber, "Slecht" rood.

#### 9. Periodecomparatie (als twee periodes zijn aangeleverd)
Tabel met delta's per campagne: kosten Δ, klikken Δ, conversies Δ, CPA-verandering. Pijlen (↑↓) met kleur voor richting.

---

## Technische HTML-vereisten

```html
<!-- Vaste structuur -->
<!DOCTYPE html>
<html lang="nl">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Google Ads Rapport — [Klantnaam] — [Periode]</title>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.js"></script>
  <style>
    /* Gebruik CSS-variabelen voor kleuren zodat dark mode werkt */
    :root {
      --bg: #FFFFFF;
      --bg-secondary: #F7F6F2;
      --text: #1A1915;
      --text-secondary: #5F5E5A;
      --border: #E8E6DF;
      --green-bg: #EAF3DE; --green-text: #3B6D11;
      --red-bg: #FCEBEB;   --red-text: #A32D2D;
      --amber-bg: #FAEEDA; --amber-text: #854F0B;
      --blue-bg: #E6F1FB;  --blue-text: #185FA5;
    }
    @media (prefers-color-scheme: dark) {
      :root {
        --bg: #1A1915; --bg-secondary: #242320;
        --text: #F0EFE9; --text-secondary: #9C9A94;
        --border: #333128;
      }
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
           background: var(--bg); color: var(--text); padding: 2rem; }
    .container { max-width: 900px; margin: 0 auto; }
  </style>
</head>
```

**Chart.js configuratie (dark mode aware):**
```javascript
const isDark = matchMedia('(prefers-color-scheme: dark)').matches;
const gridColor = isDark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.06)';
const textColor = isDark ? '#9C9A94' : '#5F5E5A';

// Gebruik altijd deze defaults
Chart.defaults.font.family = "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif";
Chart.defaults.font.size = 12;
Chart.defaults.color = textColor;
```

**Tabelstijlen:**
```css
.tbl { width: 100%; border-collapse: collapse; font-size: 13px; }
.tbl th { text-align: left; padding: 7px 10px; font-weight: 500; font-size: 12px;
          color: var(--text-secondary); border-bottom: 1px solid var(--border); }
.tbl td { padding: 7px 10px; border-bottom: 1px solid var(--border); }
.tbl tr:last-child td { border-bottom: none; }
.tbl tr:hover td { background: var(--bg-secondary); }
```

**Badge-stijlen:**
```css
.badge { display: inline-block; font-size: 11px; padding: 2px 8px;
         border-radius: 4px; font-weight: 500; }
.badge-red    { background: var(--red-bg);   color: var(--red-text); }
.badge-green  { background: var(--green-bg); color: var(--green-text); }
.badge-amber  { background: var(--amber-bg); color: var(--amber-text); }
.badge-blue   { background: var(--blue-bg);  color: var(--blue-text); }
.badge-gray   { background: var(--bg-secondary); color: var(--text-secondary); }
```

**Alert-stijlen:**
```css
.alert { border-left: 3px solid; padding: .75rem 1rem;
         border-radius: 0 6px 6px 0; font-size: 13px; margin-bottom: .75rem; }
.alert-red   { border-color: #E24B4A; background: var(--red-bg);   color: var(--red-text); }
.alert-amber { border-color: #EF9F27; background: var(--amber-bg); color: var(--amber-text); }
.alert-green { border-color: #639922; background: var(--green-bg); color: var(--green-text); }
```

---

## Gegevenspopulatie

Alle cijfers in het HTML-rapport worden **direct vanuit de tool-resultaten** ingevuld — geen placeholders, geen voorbeelddata. Bereken ontbrekende metrics als volgt:
- CPA = kosten / conversies (als cost_per_conv ontbreekt)
- CVR = conversies / klikken × 100
- ROAS = conversiewaarde / kosten (alleen als conv_value > 0)
- Delta % = (periode2 − periode1) / periode1 × 100

Formatteer getallen in Nederlandse notatie: punt als duizendtalscheider, komma als decimaalscheider (€1.234,56). Percentages met één decimaal (3,2%).

---

## Voorbeeld tool-aanroepvolgorde voor volledig rapport

Roep altijd de tools in deze volgorde aan voordat je het HTML-rapport genereert:

```
1. get_overview            → KPI-scorekaarten + samenvatting
2. get_top_campaigns       → campagnetabel + CPA-grafiek
3. get_wasted_spend        → rode alertblokken
4. get_top_keywords        → zoekwoordtabel
5. get_quality_score_analysis → QS-highlights in tabellen
6. get_budget_analysis     → IS/budget-badges
7. get_conversion_analysis → CVR-highlights
8. get_impression_share_analysis → IS-kolom campagnetabel
9. get_top_search_terms    (als beschikbaar)
10. get_search_term_opportunities  (als beschikbaar)
11. get_negative_keyword_candidates (als beschikbaar)
12. get_roas_analysis      (als conv_value beschikbaar)
13. get_auction_insights   (als beschikbaar)
14. compare_periods        (als twee periodes beschikbaar)
```

Pas daarna genereer je eerst het HTML-bestand en dan het Markdown-bestand.

---

## Naamgeving outputbestanden

```
rapport_[klantnaam-lowercase-geen-spaties]_[periode-compact].html
rapport_[klantnaam-lowercase-geen-spaties]_[periode-compact].md

Voorbeelden:
  rapport_veriflow_feb-apr2025.html
  rapport_acmecorp_q1-2025.html
  rapport_klantx_jan2025.html
```

Klantnaam haal je uit de data (campagnenamen, bestandsnaam of --focus argument). Als de naam niet bepaalbaar is, gebruik dan "klant".

# Visuele rapportage — creatieve richtlijn

## Vrijheid binnen kaders

Het bestand `RAPPORT_OUTPUT_PROMPT.md` is **inspiratie, geen sjabloon**. Je hoeft de exacte
indeling, volgorde of grafiektypen niet te kopiëren. Wat je wél altijd doet:

- Het rapport bevat **scorekaarten** voor de belangrijkste KPI's
- Het rapport bevat **minimaal twee grafieken** (bijv. trend, vergelijking, verdeling)
- Het rapport bevat **tabellen** voor campagne-, zoekwoord- of zoektermdata
- Alle visuele elementen worden gevuld met de **werkelijke data** uit de analysetools

## Wat je mag aanpassen

- Grafiektype: wissel staafgrafiek in voor lijndiagram, scatter, donut of radar als dat
  de data beter weergeeft
- Volgorde van secties: zet de meest opvallende bevinding bovenaan als dat meer impact heeft
- Aantal KPI-kaarten: toon meer of minder afhankelijk van welke metrics relevant zijn
- Kleurgebruik: pas aan zolang groen/rood consequent "goed/slecht" aanduidt
- Extra secties: voeg een sectie toe die specifiek inspeelt op de focusvraag of de data
  die het meest opvalt in deze specifieke analyse

## Wat niet verandert

- Het rapport is één zelfstandig `.html` bestand met Chart.js via CDN
- Dark mode werkt via CSS-variabelen
- Alle getallen zijn in Nederlandse notatie (punt als duizendtalsscheider, komma als decimaal)
- Elke grafiek heeft een tekstalternatief (aria-label of bijschrift) voor toegankelijkheid"""


_TOOLS = [
    {
        "name": "get_overview",
        "description": (
            "Geeft een overzicht van de totale Google Ads prestaties: klikken, vertoningen, kosten, "
            "conversies, gemiddelde CPC, CTR, conversieratio en CPA. "
            "Altijd als eerste aanroepen voor contextueel begrip."
        ),
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_top_campaigns",
        "description": "Top campagnes gesorteerd op kosten of conversies. Geeft klikken, vertoningen, kosten, conversies, CPA en CTR.",
        "input_schema": {
            "type": "object",
            "properties": {
                "sort_by": {
                    "type": "string",
                    "description": "Sorteercriterium: 'cost' (standaard), 'conversions', 'clicks', of 'ctr'",
                },
                "limit": {"type": "integer", "description": "Aantal campagnes (standaard 20)"},
            },
            "required": [],
        },
    },
    {
        "name": "get_top_ad_groups",
        "description": "Top advertentiegroepen gesorteerd op kosten of conversies.",
        "input_schema": {
            "type": "object",
            "properties": {
                "sort_by": {
                    "type": "string",
                    "description": "Sorteercriterium: 'cost' (standaard), 'conversions', 'clicks'",
                },
                "limit": {"type": "integer", "description": "Aantal advertentiegroepen (standaard 25)"},
            },
            "required": [],
        },
    },
    {
        "name": "get_top_keywords",
        "description": "Top zoekwoorden gesorteerd op conversies of kosten. Inclusief kwaliteitsscore indien beschikbaar.",
        "input_schema": {
            "type": "object",
            "properties": {
                "sort_by": {
                    "type": "string",
                    "description": "Sorteercriterium: 'conversions' (standaard), 'cost', 'clicks', 'ctr'",
                },
                "limit": {"type": "integer", "description": "Aantal zoekwoorden (standaard 30)"},
            },
            "required": [],
        },
    },
    {
        "name": "get_top_search_terms",
        "description": (
            "Top zoektermen uit het zoekterm-rapport. Laat zien welke echte zoekopdrachten "
            "je advertenties triggeren. Essentieel voor het vinden van uitsluitingszoekwoorden "
            "en nieuwe zoekwoordkansen."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "sort_by": {
                    "type": "string",
                    "description": "Sorteercriterium: 'cost' (standaard), 'conversions', 'clicks'",
                },
                "limit": {"type": "integer", "description": "Aantal zoektermen (standaard 50)"},
            },
            "required": [],
        },
    },
    {
        "name": "get_wasted_spend",
        "description": (
            "Zoekwoorden, advertentiegroepen en campagnes met significant budget maar "
            "nul of zeer weinig conversies. Dit is het meest directe besparingspotentieel."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "min_cost": {
                    "type": "number",
                    "description": "Minimum kosten (€) om mee te tellen (standaard 50)",
                },
                "max_conversions": {
                    "type": "number",
                    "description": "Maximum conversies om als verspilling te kwalificeren (standaard 0)",
                },
                "limit": {"type": "integer", "description": "Max resultaten per niveau (standaard 20)"},
            },
            "required": [],
        },
    },
    {
        "name": "get_quality_score_analysis",
        "description": (
            "Analyseert kwaliteitsscores van zoekwoorden. Lage QS verhoogt CPC en verlaagt Ad Rank. "
            "Geeft verdeling over QS-buckets en kritieke zoekwoorden (QS 1–3)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "max_qs": {
                    "type": "integer",
                    "description": "Maximale kwaliteitsscore om te rapporteren (standaard 6)",
                },
                "min_impressions": {
                    "type": "integer",
                    "description": "Minimum vertoningen om mee te tellen (standaard 10)",
                },
                "limit": {"type": "integer", "description": "Max zoekwoorden (standaard 30)"},
            },
            "required": [],
        },
    },
    {
        "name": "get_ctr_analysis",
        "description": (
            "CTR-analyse per campagne, advertentiegroep en zoekwoord. "
            "Lage CTR duidt op slechte advertentierelevantie of verkeerde zoekwoordmatch."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "min_impressions": {
                    "type": "integer",
                    "description": "Minimum vertoningen om mee te tellen (standaard 100)",
                },
                "max_ctr_pct": {
                    "type": "number",
                    "description": "Maximale CTR (%) om als kans te kwalificeren (standaard 2.0)",
                },
                "limit": {"type": "integer", "description": "Max resultaten per niveau (standaard 20)"},
            },
            "required": [],
        },
    },
    {
        "name": "get_conversion_analysis",
        "description": (
            "Conversieratio-analyse per campagne, advertentiegroep en zoekwoord. "
            "Identificeert best en slechtst converterende elementen en berekent CPA."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "min_clicks": {
                    "type": "integer",
                    "description": "Minimum klikken om statistische betrouwbaarheid te garanderen (standaard 20)",
                },
                "limit": {"type": "integer", "description": "Max resultaten per niveau (standaard 20)"},
            },
            "required": [],
        },
    },
    {
        "name": "get_search_term_opportunities",
        "description": (
            "Zoektermen met conversies of hoge CTR die nog niet als exact zoekwoord zijn toegevoegd. "
            "Dit zijn directe kansen om meer controle te krijgen over winnende zoekopdrachten."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "min_clicks": {
                    "type": "integer",
                    "description": "Minimum klikken voor een zoekterm om als kans te kwalificeren (standaard 5)",
                },
                "limit": {"type": "integer", "description": "Max zoektermen (standaard 25)"},
            },
            "required": [],
        },
    },
    {
        "name": "get_negative_keyword_candidates",
        "description": (
            "Zoektermen met veel kosten of klikken maar nul conversies die duidelijk irrelevant zijn. "
            "Dit zijn kandidaten voor uitsluitingszoekwoorden."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "min_cost": {
                    "type": "number",
                    "description": "Minimum kosten (€) per zoekterm (standaard 10)",
                },
                "limit": {"type": "integer", "description": "Max zoektermen (standaard 30)"},
            },
            "required": [],
        },
    },
    {
        "name": "get_budget_analysis",
        "description": (
            "Analyseert budgetuitputting per campagne. Identificeert campagnes die "
            "budgetgelimiteerd zijn (gemiste kansen) en campagnes die sterk onderbenut zijn."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "Max campagnes (standaard 20)"},
            },
            "required": [],
        },
    },
    {
        "name": "get_impression_share_analysis",
        "description": (
            "Analyseert vertoningsaandeel (IS) per campagne en advertentiegroep. "
            "Geeft hoeveel IS verloren gaat door budgetlimiet versus lage ad rank. "
            "Essentieel voor het prioriteren van budgetverhogingen vs. kwaliteitsscoreverbeteringen."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "Max campagnes/advertentiegroepen (standaard 20)"},
            },
            "required": [],
        },
    },
    {
        "name": "get_roas_analysis",
        "description": (
            "ROAS (Return on Ad Spend) analyse per campagne, advertentiegroep en zoekwoord. "
            "Vereist dat conversiewaarde is ingesteld. "
            "Identificeert best en slechtst renderende elementen op basis van omzetrendement."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "Max elementen per categorie (standaard 20)"},
            },
            "required": [],
        },
    },
    {
        "name": "get_auction_insights",
        "description": (
            "Veilinginzichten: concurrenten en hun vertoningsaandeel, overlappingspercentage, "
            "hoe vaak zij boven jou staan, en hoe vaak jij boven hen staat. "
            "Helpt bij het identificeren van de sterkste concurrenten en prioriteren van biedingen."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "Max concurrenten (standaard 20)"},
            },
            "required": [],
        },
    },
    {
        "name": "compare_periods",
        "description": (
            "Vergelijkt twee tijdsperiodes op campagne-, advertentiegroep- en zoekwoordniveau. "
            "Geeft: totale delta's (kosten, klikken, conversies, CPA), stijgers en dalers, "
            "nieuw verschenen en verdwenen elementen. "
            "Alleen beschikbaar als twee periodes zijn aangeleverd."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Max items per categorie (standaard 20)",
                },
            },
            "required": [],
        },
    },
]


def _dispatch(tool_name: str, tool_input: dict, data: AdsData, data2: AdsData | None = None) -> str:
    """Voer de juiste analysefunctie uit en geef JSON terug."""
    fn_map = {
        "get_overview": lambda: get_overview(data),
        "get_top_campaigns": lambda: get_top_campaigns(
            data,
            sort_by=tool_input.get("sort_by", "cost"),
            limit=int(tool_input.get("limit", 20)),
        ),
        "get_top_ad_groups": lambda: get_top_ad_groups(
            data,
            sort_by=tool_input.get("sort_by", "cost"),
            limit=int(tool_input.get("limit", 25)),
        ),
        "get_top_keywords": lambda: get_top_keywords(
            data,
            sort_by=tool_input.get("sort_by", "conversions"),
            limit=int(tool_input.get("limit", 30)),
        ),
        "get_top_search_terms": lambda: get_top_search_terms(
            data,
            sort_by=tool_input.get("sort_by", "cost"),
            limit=int(tool_input.get("limit", 50)),
        ),
        "get_wasted_spend": lambda: get_wasted_spend(
            data,
            min_cost=float(tool_input.get("min_cost", 50)),
            max_conversions=float(tool_input.get("max_conversions", 0)),
            limit=int(tool_input.get("limit", 20)),
        ),
        "get_quality_score_analysis": lambda: get_quality_score_analysis(
            data,
            max_qs=int(tool_input.get("max_qs", 6)),
            min_impressions=int(tool_input.get("min_impressions", 10)),
            limit=int(tool_input.get("limit", 30)),
        ),
        "get_ctr_analysis": lambda: get_ctr_analysis(
            data,
            min_impressions=int(tool_input.get("min_impressions", 100)),
            max_ctr_pct=float(tool_input.get("max_ctr_pct", 2.0)),
            limit=int(tool_input.get("limit", 20)),
        ),
        "get_conversion_analysis": lambda: get_conversion_analysis(
            data,
            min_clicks=int(tool_input.get("min_clicks", 20)),
            limit=int(tool_input.get("limit", 20)),
        ),
        "get_search_term_opportunities": lambda: get_search_term_opportunities(
            data,
            min_clicks=int(tool_input.get("min_clicks", 5)),
            limit=int(tool_input.get("limit", 25)),
        ),
        "get_negative_keyword_candidates": lambda: get_negative_keyword_candidates(
            data,
            min_cost=float(tool_input.get("min_cost", 10)),
            limit=int(tool_input.get("limit", 30)),
        ),
        "get_budget_analysis": lambda: get_budget_analysis(
            data,
            limit=int(tool_input.get("limit", 20)),
        ),
        "get_impression_share_analysis": lambda: get_impression_share_analysis(
            data,
            limit=int(tool_input.get("limit", 20)),
        ),
        "get_roas_analysis": lambda: get_roas_analysis(
            data,
            limit=int(tool_input.get("limit", 20)),
        ),
        "get_auction_insights": lambda: get_auction_insights(
            data,
            limit=int(tool_input.get("limit", 20)),
        ),
        "compare_periods": lambda: (
            compare_periods(data, data2, limit=int(tool_input.get("limit", 20)))
            if data2 is not None
            else {"error": "Geen tweede periode beschikbaar. Gebruik --vergelijk <bestanden> om twee periodes te vergelijken."}
        ),
    }
    fn = fn_map.get(tool_name)
    if fn is None:
        return json.dumps({"error": f"Onbekende tool: {tool_name}"})
    return json.dumps(fn(), ensure_ascii=False, indent=2)


def run_analysis(
    data: AdsData, focus: str | None = None, data2: AdsData | None = None
) -> tuple[list[dict], dict[str, str]]:
    """
    Voer een volledige Google Ads analyse uit op de opgegeven data.

    Args:
        data:   Geparsede Google Ads data — basisperiode (of enige periode)
        focus:  Optionele focusvraag of aandachtspunt van de gebruiker
        data2:  Optionele tweede periode voor vergelijkingsanalyse

    Returns:
        Tuple van (sections, tool_results_store):
        - sections: list van sectie-dicts met 'id', 'title', 'bullets'
        - tool_results_store: dict van toolnaam -> ruwe JSON-string
    """
    client = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)

    def _summary(d: AdsData, label: str) -> str:
        return (
            f"{label}:\n"
            f"  - Campagnes: {len(d.campaigns)} rijen\n"
            f"  - Advertentiegroepen: {len(d.ad_groups)} rijen\n"
            f"  - Zoekwoorden: {len(d.keywords)} rijen\n"
            f"  - Zoektermen: {len(d.search_terms)} rijen\n"
            f"  - Veilinginzichten: {len(d.auction_insights)} concurrenten\n"
            f"  - Bronbestanden: {', '.join(d.source_files)}\n"
        )

    data_context = _summary(data, "Periode 1 (basis)")
    if data2 is not None:
        data_context += "\n" + _summary(data2, "Periode 2 (vergelijking)")
        data_context += "\nVergelijkingsanalyse beschikbaar via de tool compare_periods."

    user_msg = "Analyseer de Google Ads data en maak een strategisch rapport.\n\n" + data_context
    if focus:
        user_msg += f"\nSpecifieke focus van de klant: {focus}"

    if not data.campaigns and not data.keywords:
        return [], {}

    messages: list[dict] = [{"role": "user", "content": user_msg}]
    tool_results_store: dict[str, str] = {}

    while True:
        response = client.messages.create(
            model=Config.CLAUDE_MODEL,
            max_tokens=8096,
            system=[
                {
                    "type": "text",
                    "text": _SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            tools=_TOOLS,
            messages=messages,
        )

        if response.stop_reason == "end_turn":
            for block in response.content:
                if block.type == "text":
                    raw = block.text.strip()
                    # Strip markdown code fences if present
                    if raw.startswith("```"):
                        lines = raw.splitlines()
                        # remove first and last fence lines
                        raw = "\n".join(
                            line for line in lines
                            if not line.strip().startswith("```")
                        ).strip()
                    try:
                        parsed = json.loads(raw)
                        sections = parsed.get("sections", [])
                    except Exception:
                        sections = []
                    return sections, tool_results_store
            return [], tool_results_store

        if response.stop_reason != "tool_use":
            break

        messages.append({"role": "assistant", "content": response.content})

        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                result = _dispatch(block.name, block.input, data, data2)
                tool_results_store[block.name] = result
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    }
                )

        if tool_results:
            messages.append({"role": "user", "content": tool_results})

    return [], tool_results_store
