"""
Google Search Console Analyse Agent.
Claude analyseert GSC-exportdata via tool use en levert een strategisch rapport.
"""

from __future__ import annotations

import json
import anthropic

from ..config import Config
from ..tools.excel_parser import GSCData
from ..tools.analysis import (
    get_overview,
    get_top_pages,
    get_top_queries,
    get_ctr_opportunities,
    get_ctr_gap_analysis,
    get_low_hanging_fruit,
    get_cannibalization,
    get_position_distribution,
    get_zero_click_opportunities,
    get_branded_vs_nonbranded,
    get_query_intent_breakdown,
    get_page_query_coverage,
    compare_periods,
)


_SYSTEM_PROMPT = """Je bent een Google Search Console analist van Search Signals, een B2B digitaal \
marketingbureau. Je helpt klanten hun organische zoekprestaties begrijpen en verbeteren.

Search Signals werkt als strategische partner — eerlijk, direct, resultaatgericht. Geen bullshit: \
als iets niet werkt, zeg je dat. Aanbevelingen zijn concreet en prioriteren op impact.

## Beschikbare analysetools

**Basis:**
- get_overview — totale statistieken (altijd als eerste aanroepen)
- get_top_pages — best presterende pagina's op klikken
- get_top_queries — best presterende zoektermen op klikken
- get_position_distribution — verdeling over positiebuckets

**Periodeanalyse:**
- compare_periods — vergelijkt twee tijdsperiodes: totale delta's, stijgers/dalers, nieuwe en \
verdwenen queries/pagina's, positieveranderingen. Alleen beschikbaar als twee periodes zijn aangeleverd.

**CTR-analyse:**
- get_ctr_gap_analysis — vergelijkt werkelijke CTR met verwachte CTR per positie (op basis van \
industriebenchmarks: pos 1 ≈ 28.5%, pos 3 ≈ 11%, pos 10 ≈ 2.5%). Dit is nauwkeuriger dan een \
vaste drempel.
- get_ctr_opportunities — pagina's/queries met hoge vertoningen en lage absolute CTR

**Kansanalyse:**
- get_low_hanging_fruit — positie 4–10 met significant bereik; potentie berekend op basis van \
benchmarkCTR voor positie 3 (≈11%)
- get_zero_click_opportunities — bereik zonder klikken (featured snippets, slechte snippets)

**Segmentatie & structuur:**
- get_branded_vs_nonbranded — split branded vs. niet-branded queries (geef brand_terms mee)
- get_query_intent_breakdown — classificeert queries als transactioneel/navigational/informationeel
- get_cannibalization — zoektermen waarop meerdere pagina's concurreren
- get_page_query_coverage — pagina's met veel queries (topical authority of gefragmenteerde focus)

## Analytisch kader

**CTR-beoordeling (2026 benchmarks, niet-branded, schone SERP):**
- Positie 1 ≈ 39.8% | Positie 3 ≈ 10.2% | Positie 5 ≈ 5.1% | Positie 10 ≈ 2.2%
- AI Overviews verlagen CTR op positie 1–3 met ~30–40%. Een CTR van 3% op positie 1 kan dus \
normaal zijn als Google een AIO toont.
- Signaal voor zero-click/AIO-probleem: sterke positie (1–3) met CTR < 2%.
- Gebruik get_ctr_gap_analysis als primaire CTR-diagnosetool.

**Prioritering via ICE-score:**
- Impact = impressies × CTR-gap (gemiste klikken)
- Confidence: hoog voor title/meta-herschrijf (bewezen effectief), laag voor nieuwe content
- Effort: title-aanpassing = laag, full content rebuild = hoog
- Volgorde: title/meta-optimalisaties eerst (snel, hoge confidence), daarna content-verbeteringen

**Intentmatch:** Transactionele queries met slechte positie of CTR zijn urgenter dan \
informatieve queries — ze staan dichter bij een conversie.

**Cannibalisatie:** Hoge ernst als: positieverschil < 3 EN impressieratio (zwakkere/sterkere pagina) \
> 0.5. Oplossing in volgorde van voorkeur: 301-redirect naar sterkste URL, differentieer de \
inhoud, voeg canonical tag toe.

**Branded vs. niet-branded:** Gebruik niet-branded klikgroei (kwartaal-op-kwartaal) als \
primaire SEO KPI. Branded groei is een merk-KPI, geen SEO-indicator.

**Content decay:** Beide impressies én klikken dalen stapsgewijs (niet plotseling) = klassiek \
decay-patroon. CTR daalt maar impressies stabiel = SERP-feature heeft klikken overgenomen.

**Periodecomparatie:** Als twee periodes beschikbaar zijn, roep dan altijd eerst compare_periods \
aan. Interpreteer delta's als volgt:
- Klikken -20%+ met stabiele impressies → CTR-probleem (snippet gewijzigd of concurrentie)
- Klikken én impressies beide -20%+ → rankingverlies of seizoenseffect
- Positie verbeterd maar minder klikken → SERP-feature (AIO/snippet) absorbeert klikken
- Nieuwe queries in periode 2 → kansen om op voort te bouwen
- Verdwenen queries → content decay of deïndexering onderzoeken

## Structuur van het rapport

### 1. Samenvatting
Totale prestaties (klikken, vertoningen, gemiddelde positie, CTR) en de 2–3 meest opvallende \
bevindingen. Vergelijk branded vs. niet-branded aandeel als die data beschikbaar is.

### 2. Sterktes
Wat werkt goed? Welke pagina's of zoektermen presteren sterk ten opzichte van de benchmarks?

### 3. Prioriteit 1 — Directe kansen (hoge impact, lage inspanning)
Concrete actiepunten. Geef per aanbeveling:
- Wat: welke pagina of zoekterm
- Actie: wat moet er precies veranderen (bijv. "herschrijf title tag van X naar Y")
- Verwacht effect: schatting van extra klikken op basis van CTR-benchmarks

### 4. Prioriteit 2 — Structurele verbeteringen (hogere inspanning, grotere impact)
Aanbevelingen die meer werk kosten maar strategisch belangrijk zijn (bijv. content \
samenvoegen bij cannibalisatie, nieuwe pagina's aanmaken voor ontbrekende intenties).

### 5. Prioriteit 3 — Aandachtspunten
Waarschuwingssignalen, zero-click queries, of structurele problemen die monitored moeten worden.

Schrijf in het Nederlands. Wees direct en concreet. Vermijd jargon zonder uitleg. \
Geef altijd schattingen van de impact in concrete aantallen (extra klikken per maand)."""


_TOOLS = [
    {
        "name": "get_overview",
        "description": (
            "Geeft een overzicht van de totale GSC-prestaties: totaal klikken, vertoningen, "
            "gemiddelde CTR en positie, plus verdeling van pagina's en queries over positiebuckets. "
            "Altijd als eerste aanroepen voor contextueel begrip."
        ),
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_top_pages",
        "description": "Top pagina's gesorteerd op klikken. Geeft URL, klikken, vertoningen, CTR en positie.",
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Aantal pagina's om terug te geven (standaard 25, max 50)",
                }
            },
            "required": [],
        },
    },
    {
        "name": "get_top_queries",
        "description": "Top zoektermen gesorteerd op klikken. Geeft query, klikken, vertoningen, CTR en positie.",
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Aantal zoektermen om terug te geven (standaard 30, max 100)",
                }
            },
            "required": [],
        },
    },
    {
        "name": "get_ctr_opportunities",
        "description": (
            "Pagina's en zoektermen met veel vertoningen maar een lage CTR. "
            "Dit zijn kansen om titels en meta descriptions te verbeteren."
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
                    "description": "Maximum CTR % om als kans te kwalificeren (standaard 3.0)",
                },
                "limit": {"type": "integer", "description": "Max resultaten per categorie (standaard 20)"},
            },
            "required": [],
        },
    },
    {
        "name": "get_low_hanging_fruit",
        "description": (
            "Pagina's en zoektermen op positie 4–10 met significante vertoningen. "
            "Een kleine rankingverbetering levert direct veel extra klikken op."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "min_impressions": {
                    "type": "integer",
                    "description": "Minimum vertoningen (standaard 50)",
                },
                "pos_min": {"type": "number", "description": "Ondergrens positie (standaard 4.0)"},
                "pos_max": {"type": "number", "description": "Bovengrens positie (standaard 10.0)"},
                "limit": {"type": "integer", "description": "Max resultaten (standaard 20)"},
            },
            "required": [],
        },
    },
    {
        "name": "get_cannibalization",
        "description": (
            "Detecteert zoektermen waarbij meerdere pagina's concurreren (keyword cannibalisatie). "
            "Vereist gecombineerde query+page data in het Excel-bestand."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "min_impressions": {
                    "type": "integer",
                    "description": "Minimum vertoningen per query (standaard 20)",
                },
                "limit": {"type": "integer", "description": "Max te rapporteren queries (standaard 20)"},
            },
            "required": [],
        },
    },
    {
        "name": "get_position_distribution",
        "description": (
            "Verdeling van pagina's en zoektermen over positiebuckets (1–3, 4–6, 7–10, 11–20, 21–50, 51+). "
            "Geeft inzicht in het algehele rankingprofiel."
        ),
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_zero_click_opportunities",
        "description": (
            "Pagina's en zoektermen met veel vertoningen maar nul klikken. "
            "Hoogste prioriteit: het bereik is er, maar het levert niets op."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "min_impressions": {
                    "type": "integer",
                    "description": "Minimum vertoningen (standaard 200)",
                },
                "limit": {"type": "integer", "description": "Max resultaten (standaard 20)"},
            },
            "required": [],
        },
    },
    {
        "name": "get_ctr_gap_analysis",
        "description": (
            "Vergelijkt de werkelijke CTR met de verwachte CTR op basis van industriebenchmarks per positie "
            "(pos 1 ≈ 28.5%, pos 3 ≈ 11%, pos 10 ≈ 2.5%). "
            "Nauwkeuriger dan een vaste CTR-drempel: een CTR van 5% is slecht voor positie 1 maar goed voor positie 10. "
            "Gebruik dit als primaire tool voor title/meta-optimalisatiekansen."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "min_impressions": {
                    "type": "integer",
                    "description": "Minimum vertoningen om mee te tellen (standaard 100)",
                },
                "min_gap_pct": {
                    "type": "number",
                    "description": "Minimale CTR-gap (verwacht - werkelijk) in procentpunten (standaard 2.0)",
                },
                "limit": {"type": "integer", "description": "Max resultaten per categorie (standaard 20)"},
            },
            "required": [],
        },
    },
    {
        "name": "get_branded_vs_nonbranded",
        "description": (
            "Splitst zoekterm-data in branded en niet-branded queries. "
            "Branded queries reflecteren merkbekendheid, niet-branded queries organisch bereik. "
            "Geef brand_terms mee voor nauwkeurige segmentatie."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "brand_terms": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Merkgerelateerde zoektermen (bijv. ['bedrijfsnaam', 'productnaam', 'domeinnaam']). Probeer dit af te leiden uit de top queries.",
                },
                "limit": {"type": "integer", "description": "Max queries per segment (standaard 20)"},
            },
            "required": [],
        },
    },
    {
        "name": "get_query_intent_breakdown",
        "description": (
            "Classificeert zoektermen op intenttype: transactioneel (kopen/bestellen), "
            "navigational (merk/inloggen), of informationeel (hoe/wat/waarom). "
            "Helpt bij het prioriteren: transactionele queries met slechte CTR zijn het meest urgent."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "Max queries per intentcategorie (standaard 15)"},
            },
            "required": [],
        },
    },
    {
        "name": "get_page_query_coverage",
        "description": (
            "Analyseert hoeveel zoektermen per pagina vertoningen genereren. "
            "Pagina's met veel queries maar weinig klikken per query hebben mogelijk gefragmenteerde focus. "
            "Pagina's met weinig queries kunnen worden uitgebreid voor meer topical authority. "
            "Vereist gecombineerde query+page data."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "min_queries": {
                    "type": "integer",
                    "description": "Minimum aantal queries per pagina om te tonen (standaard 5)",
                },
                "min_impressions_per_query": {
                    "type": "integer",
                    "description": "Minimum vertoningen per query om mee te tellen (standaard 10)",
                },
                "limit": {"type": "integer", "description": "Max pagina's (standaard 20)"},
            },
            "required": [],
        },
    },
    {
        "name": "compare_periods",
        "description": (
            "Vergelijkt twee tijdsperiodes op query- en paginaniveau. "
            "Geeft: totale delta's (klikken, vertoningen, CTR, positie), top stijgers en dalers, "
            "positieveranderingen, nieuw verschenen en verdwenen queries/pagina's. "
            "Alleen beschikbaar als twee periodes zijn aangeleverd — controleer data_context eerst."
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


def _dispatch(tool_name: str, tool_input: dict, data: GSCData, data2: GSCData | None = None) -> str:
    """Voer de juiste analysefunctie uit en geef JSON terug."""
    fn_map = {
        "get_overview": lambda: get_overview(data),
        "get_top_pages": lambda: get_top_pages(data, limit=int(tool_input.get("limit", 25))),
        "get_top_queries": lambda: get_top_queries(data, limit=int(tool_input.get("limit", 30))),
        "get_ctr_opportunities": lambda: get_ctr_opportunities(
            data,
            min_impressions=int(tool_input.get("min_impressions", 100)),
            max_ctr_pct=float(tool_input.get("max_ctr_pct", 3.0)),
            limit=int(tool_input.get("limit", 20)),
        ),
        "get_low_hanging_fruit": lambda: get_low_hanging_fruit(
            data,
            min_impressions=int(tool_input.get("min_impressions", 50)),
            pos_min=float(tool_input.get("pos_min", 4.0)),
            pos_max=float(tool_input.get("pos_max", 10.0)),
            limit=int(tool_input.get("limit", 20)),
        ),
        "get_cannibalization": lambda: get_cannibalization(
            data,
            min_impressions=int(tool_input.get("min_impressions", 20)),
            limit=int(tool_input.get("limit", 20)),
        ),
        "get_position_distribution": lambda: get_position_distribution(data),
        "get_zero_click_opportunities": lambda: get_zero_click_opportunities(
            data,
            min_impressions=int(tool_input.get("min_impressions", 200)),
            limit=int(tool_input.get("limit", 20)),
        ),
        "get_ctr_gap_analysis": lambda: get_ctr_gap_analysis(
            data,
            min_impressions=int(tool_input.get("min_impressions", 100)),
            min_gap_pct=float(tool_input.get("min_gap_pct", 2.0)),
            limit=int(tool_input.get("limit", 20)),
        ),
        "get_branded_vs_nonbranded": lambda: get_branded_vs_nonbranded(
            data,
            brand_terms=tool_input.get("brand_terms") or [],
            limit=int(tool_input.get("limit", 20)),
        ),
        "get_query_intent_breakdown": lambda: get_query_intent_breakdown(
            data,
            limit=int(tool_input.get("limit", 15)),
        ),
        "get_page_query_coverage": lambda: get_page_query_coverage(
            data,
            min_queries=int(tool_input.get("min_queries", 5)),
            min_impressions_per_query=int(tool_input.get("min_impressions_per_query", 10)),
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


def run_analysis(data: GSCData, focus: str | None = None, data2: GSCData | None = None) -> str:
    """
    Voer een volledige GSC-analyse uit op de opgegeven data.

    Args:
        data:   Geparsede GSC data — basisperiode (of enige periode)
        focus:  Optionele focusvraag of aandachtspunt van de gebruiker
        data2:  Optionele tweede periode voor vergelijkingsanalyse

    Returns:
        Strategisch GSC-rapport als opgemaakte Markdown-tekst.
    """
    client = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)

    def _summary(d: GSCData, label: str) -> str:
        return (
            f"{label}:\n"
            f"  - Zoektermen: {len(d.queries)} rijen\n"
            f"  - Pagina's: {len(d.pages)} rijen\n"
            f"  - Gecombineerde query+page: {len(d.query_pages)} rijen\n"
            f"  - Bronbestanden: {', '.join(d.source_files)}\n"
        )

    data_context = _summary(data, "Periode 1 (basis)")
    if data2 is not None:
        data_context += "\n" + _summary(data2, "Periode 2 (vergelijking)")
        data_context += "\nVergelijkingsanalyse beschikbaar via de tool compare_periods."

    user_msg = "Analyseer de GSC-data en maak een strategisch rapport.\n\n" + data_context
    if focus:
        user_msg += f"\nSpecifieke focus van de klant: {focus}"

    if not data.queries and not data.pages:
        return "Fout: geen bruikbare GSC-data gevonden. Controleer het Excel-bestand."

    messages: list[dict] = [{"role": "user", "content": user_msg}]

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
                    return block.text
            return "(geen rapport ontvangen)"

        if response.stop_reason != "tool_use":
            break

        messages.append({"role": "assistant", "content": response.content})

        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                result = _dispatch(block.name, block.input, data, data2)
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    }
                )

        if tool_results:
            messages.append({"role": "user", "content": tool_results})

    return "Analyse kon niet worden voltooid."
