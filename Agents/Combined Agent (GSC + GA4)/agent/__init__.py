"""
Combined Agent — Google Search Console + GA4.
Claude analyseert GSC- én GA4-exportdata in één run en legt kruisverbanden.
"""

from __future__ import annotations

import json
import anthropic

from ..config import Config
from search_console_agent.tools.excel_parser import GSCData
from search_console_agent.tools.analysis import (
    get_overview as gsc_get_overview,
    get_top_pages as gsc_get_top_pages,
    get_top_queries as gsc_get_top_queries,
    get_ctr_opportunities as gsc_get_ctr_opportunities,
    get_ctr_gap_analysis as gsc_get_ctr_gap_analysis,
    get_low_hanging_fruit as gsc_get_low_hanging_fruit,
    get_cannibalization as gsc_get_cannibalization,
    get_position_distribution as gsc_get_position_distribution,
    get_zero_click_opportunities as gsc_get_zero_click_opportunities,
    get_branded_vs_nonbranded as gsc_get_branded_vs_nonbranded,
    get_query_intent_breakdown as gsc_get_query_intent_breakdown,
    get_page_query_coverage as gsc_get_page_query_coverage,
)
from ga4_agent.tools.excel_parser import GA4Data
from ga4_agent.tools.analysis import (
    get_overview as ga4_get_overview,
    get_channel_breakdown,
    get_top_pages as ga4_get_top_pages,
    get_low_engagement_pages,
    get_high_bounce_pages,
    get_conversion_analysis,
    get_landing_page_analysis,
    get_device_breakdown,
    get_organic_performance,
)


_SYSTEM_PROMPT = """Je bent een digitale marketing analist van Search Signals, een B2B digitaal \
marketingbureau. Je hebt toegang tot zowel Google Search Console (GSC) als Google Analytics 4 (GA4) \
data van dezelfde website.

Search Signals werkt als strategische partner — eerlijk, direct, resultaatgericht. Geen bullshit: \
als iets niet werkt, zeg je dat. Aanbevelingen zijn concreet en prioriteren op impact.

## Werkwijze

1. Roep eerst `gsc_get_overview` en `ga4_get_overview` aan om de totale context te begrijpen.
2. Gebruik daarna gerichte tools om specifieke vragen te beantwoorden.
3. Leg actief kruisverbanden tussen GSC en GA4 — dat is de meerwaarde van deze gecombineerde analyse.

## Beschikbare GSC-tools (prefix: gsc_)

- gsc_get_overview — totale GSC-statistieken (klikken, vertoningen, CTR, positie)
- gsc_get_top_pages — best presterende pagina's op klikken
- gsc_get_top_queries — best presterende zoektermen op klikken
- gsc_get_position_distribution — verdeling over positiebuckets
- gsc_get_ctr_gap_analysis — CTR-gap per pagina/query t.o.v. benchmarks
- gsc_get_ctr_opportunities — hoge vertoningen, lage CTR
- gsc_get_low_hanging_fruit — positie 4–10 met significant bereik
- gsc_get_zero_click_opportunities — bereik zonder klikken
- gsc_get_branded_vs_nonbranded — branded vs. niet-branded split
- gsc_get_query_intent_breakdown — intentclassificatie van zoektermen
- gsc_get_cannibalization — keyword cannibalisatie detectie
- gsc_get_page_query_coverage — topical authority per pagina

## Beschikbare GA4-tools (prefix: ga4_)

- ga4_get_overview — totale GA4-statistieken (sessies, gebruikers, bounce, conversies)
- ga4_get_channel_breakdown — prestaties per kanaal
- ga4_get_top_pages — meest bezochte pagina's
- ga4_get_low_engagement_pages — pagina's met lage gemiddelde engagementtijd
- ga4_get_high_bounce_pages — pagina's met hoge bounce rate
- ga4_get_conversion_analysis — conversiepagina's + zero-conversion pagina's
- ga4_get_landing_page_analysis — prestaties van landingspagina's
- ga4_get_device_breakdown — sessies per apparaattype
- ga4_get_organic_performance — organisch kanaal geïsoleerd

## Kruisverbanden om te leggen

**Bereik vs. gedrag:**
- GSC hoge vertoningen/klikken + GA4 hoge bounce → traffic komt aan maar content overtuigt niet
- GSC goede positie + GA4 lage engagementtijd → intentmismatch: zoekterm matcht niet met pagina-inhoud

**Conversie-lek:**
- GSC hoge klikken op pagina + GA4 nul conversies → funnel breekt na landing
- GSC lage CTR + GA4 hoge conversie op die pagina → prioriteer title/meta-optimalisatie voor extra volume

**Kanaalefficiëntie:**
- GA4 organisch kanaal isoleren en vergelijken met GSC-totalen → check consistentie
- GSC branded queries hoog + GA4 direct verkeer hoog → sterke merkbekendheid, maar organisch bereik smal

**Content kwaliteit:**
- GSC positie 1–3 + GA4 lage betrokkenheid → featured snippet trekt verkeer aan maar content voldoet niet
- GSC zero-click + GA4 geen traffic op die URL → volledige SERP-absorptie, overweeg andere aanpak

## CTR-benchmarks (2026, niet-branded, schone SERP)

Positie 1 ≈ 39.8% | Positie 3 ≈ 10.2% | Positie 5 ≈ 5.1% | Positie 10 ≈ 2.2%
AI Overviews verlagen CTR op positie 1–3 met ~30–40%.

## Structuur van het rapport

### 1. Executive Summary
Totale prestaties GSC én GA4 in 3–5 bullets. De 2–3 meest urgente bevindingen uit de kruisanalyse.

### 2. Organisch kanaal: van zoekterm tot conversie
Hoe loopt het pad van zoekopdracht (GSC) → landing (GA4) → conversie (GA4)?
Waar breekt de funnel?

### 3. Content-performance: kansen en lekken
Per belangrijke pagina: GSC-bereik vs. GA4-gedrag. Waar is de kwaliteit sterk, waar lekt waarde?

### 4. Prioriteit 1 — Directe kansen (hoge impact, lage inspanning)
Concrete actiepunten met verwacht effect in aantallen (extra klikken, lagere bounce, extra conversies).

### 5. Prioriteit 2 — Structurele verbeteringen
Aanbevelingen met grotere impact maar meer werk (content rebuild, funnel-optimalisatie, cannibalisatie).

### 6. Aandachtspunten & monitoring
Waarschuwingssignalen die bewaking nodig hebben maar nog geen directe actie vereisen.

Schrijf in het Nederlands. Wees direct en concreet. Vermijd jargon zonder uitleg. \
Geef altijd schattingen van de impact in concrete aantallen."""


_TOOLS = [
    # --- GSC tools ---
    {
        "name": "gsc_get_overview",
        "description": (
            "Totale GSC-prestaties: klikken, vertoningen, gemiddelde CTR en positie. "
            "Altijd als eerste aanroepen samen met ga4_get_overview."
        ),
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "gsc_get_top_pages",
        "description": "Top pagina's gesorteerd op klikken (GSC). Geeft URL, klikken, vertoningen, CTR en positie.",
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "Aantal pagina's (standaard 25, max 50)"},
            },
            "required": [],
        },
    },
    {
        "name": "gsc_get_top_queries",
        "description": "Top zoektermen gesorteerd op klikken (GSC). Geeft query, klikken, vertoningen, CTR en positie.",
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "Aantal zoektermen (standaard 30, max 100)"},
            },
            "required": [],
        },
    },
    {
        "name": "gsc_get_ctr_gap_analysis",
        "description": (
            "Vergelijkt werkelijke CTR met verwachte CTR per positie (benchmarks). "
            "Gebruik als primaire tool voor title/meta-optimalisatiekansen."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "min_impressions": {"type": "integer", "description": "Minimum vertoningen (standaard 100)"},
                "min_gap_pct": {"type": "number", "description": "Minimale CTR-gap in procentpunten (standaard 2.0)"},
                "limit": {"type": "integer", "description": "Max resultaten per categorie (standaard 20)"},
            },
            "required": [],
        },
    },
    {
        "name": "gsc_get_ctr_opportunities",
        "description": "Pagina's en zoektermen met veel vertoningen maar lage CTR (GSC).",
        "input_schema": {
            "type": "object",
            "properties": {
                "min_impressions": {"type": "integer", "description": "Minimum vertoningen (standaard 100)"},
                "max_ctr_pct": {"type": "number", "description": "Maximum CTR % (standaard 3.0)"},
                "limit": {"type": "integer", "description": "Max resultaten per categorie (standaard 20)"},
            },
            "required": [],
        },
    },
    {
        "name": "gsc_get_low_hanging_fruit",
        "description": "Pagina's en zoektermen op positie 4–10 met significante vertoningen (GSC).",
        "input_schema": {
            "type": "object",
            "properties": {
                "min_impressions": {"type": "integer", "description": "Minimum vertoningen (standaard 50)"},
                "pos_min": {"type": "number", "description": "Ondergrens positie (standaard 4.0)"},
                "pos_max": {"type": "number", "description": "Bovengrens positie (standaard 10.0)"},
                "limit": {"type": "integer", "description": "Max resultaten (standaard 20)"},
            },
            "required": [],
        },
    },
    {
        "name": "gsc_get_zero_click_opportunities",
        "description": "Pagina's en zoektermen met veel vertoningen maar nul klikken (GSC).",
        "input_schema": {
            "type": "object",
            "properties": {
                "min_impressions": {"type": "integer", "description": "Minimum vertoningen (standaard 200)"},
                "limit": {"type": "integer", "description": "Max resultaten (standaard 20)"},
            },
            "required": [],
        },
    },
    {
        "name": "gsc_get_position_distribution",
        "description": "Verdeling van pagina's en zoektermen over positiebuckets (GSC).",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "gsc_get_branded_vs_nonbranded",
        "description": "Splitst zoektermen in branded en niet-branded (GSC).",
        "input_schema": {
            "type": "object",
            "properties": {
                "brand_terms": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Merkgerelateerde zoektermen. Probeer af te leiden uit de top queries.",
                },
                "limit": {"type": "integer", "description": "Max queries per segment (standaard 20)"},
            },
            "required": [],
        },
    },
    {
        "name": "gsc_get_query_intent_breakdown",
        "description": "Classificeert zoektermen als transactioneel, navigational of informationeel (GSC).",
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "Max queries per intentcategorie (standaard 15)"},
            },
            "required": [],
        },
    },
    {
        "name": "gsc_get_cannibalization",
        "description": "Detecteert zoektermen waarbij meerdere pagina's concurreren (GSC).",
        "input_schema": {
            "type": "object",
            "properties": {
                "min_impressions": {"type": "integer", "description": "Minimum vertoningen per query (standaard 20)"},
                "limit": {"type": "integer", "description": "Max te rapporteren queries (standaard 20)"},
            },
            "required": [],
        },
    },
    {
        "name": "gsc_get_page_query_coverage",
        "description": "Analyseert hoeveel zoektermen per pagina vertoningen genereren (GSC).",
        "input_schema": {
            "type": "object",
            "properties": {
                "min_queries": {"type": "integer", "description": "Minimum queries per pagina (standaard 5)"},
                "min_impressions_per_query": {"type": "integer", "description": "Minimum vertoningen per query (standaard 10)"},
                "limit": {"type": "integer", "description": "Max pagina's (standaard 20)"},
            },
            "required": [],
        },
    },
    # --- GA4 tools ---
    {
        "name": "ga4_get_overview",
        "description": (
            "Totale GA4-statistieken: sessies, gebruikers, bounce rate, conversies, engagementtijd. "
            "Altijd als eerste aanroepen samen met gsc_get_overview."
        ),
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "ga4_get_channel_breakdown",
        "description": "Prestaties per kanaal (organisch, betaald, direct, social, e-mail etc.) uit GA4.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "ga4_get_top_pages",
        "description": "Meest bezochte pagina's op sessies/gebruikers uit GA4.",
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "Aantal pagina's (standaard 25)"},
            },
            "required": [],
        },
    },
    {
        "name": "ga4_get_low_engagement_pages",
        "description": "Pagina's met voldoende traffic maar lage gemiddelde engagementtijd (GA4).",
        "input_schema": {
            "type": "object",
            "properties": {
                "min_sessions": {"type": "integer", "description": "Minimum sessies (standaard 50)"},
                "max_engagement_seconds": {"type": "number", "description": "Maximum engagementtijd in seconden (standaard 30)"},
                "limit": {"type": "integer", "description": "Max resultaten (standaard 20)"},
            },
            "required": [],
        },
    },
    {
        "name": "ga4_get_high_bounce_pages",
        "description": "Pagina's met hoge bounce rate (standaard >70%) en voldoende traffic (GA4).",
        "input_schema": {
            "type": "object",
            "properties": {
                "min_sessions": {"type": "integer", "description": "Minimum sessies (standaard 50)"},
                "bounce_threshold": {"type": "number", "description": "Minimale bounce rate % (standaard 70.0)"},
                "limit": {"type": "integer", "description": "Max resultaten (standaard 20)"},
            },
            "required": [],
        },
    },
    {
        "name": "ga4_get_conversion_analysis",
        "description": "Conversiepagina's én pagina's met traffic maar nul conversies (GA4).",
        "input_schema": {
            "type": "object",
            "properties": {
                "min_sessions": {"type": "integer", "description": "Minimum sessies voor zero-conversion pagina's (standaard 20)"},
                "limit": {"type": "integer", "description": "Max resultaten per categorie (standaard 20)"},
            },
            "required": [],
        },
    },
    {
        "name": "ga4_get_landing_page_analysis",
        "description": "Prestaties van landingspagina's (eerste pagina van de sessie) uit GA4.",
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "Aantal landingspagina's (standaard 25)"},
            },
            "required": [],
        },
    },
    {
        "name": "ga4_get_device_breakdown",
        "description": "Sessies, bounce rate en conversies per apparaattype (GA4).",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "ga4_get_organic_performance",
        "description": "Geïsoleerde prestaties van het organische zoekkanaal (GA4). Vergelijk met GSC-totalen.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
]


def _dispatch_gsc(tool_name: str, tool_input: dict, gsc_data: GSCData) -> str:
    fn_map = {
        "gsc_get_overview": lambda: gsc_get_overview(gsc_data),
        "gsc_get_top_pages": lambda: gsc_get_top_pages(gsc_data, limit=int(tool_input.get("limit", 25))),
        "gsc_get_top_queries": lambda: gsc_get_top_queries(gsc_data, limit=int(tool_input.get("limit", 30))),
        "gsc_get_ctr_opportunities": lambda: gsc_get_ctr_opportunities(
            gsc_data,
            min_impressions=int(tool_input.get("min_impressions", 100)),
            max_ctr_pct=float(tool_input.get("max_ctr_pct", 3.0)),
            limit=int(tool_input.get("limit", 20)),
        ),
        "gsc_get_ctr_gap_analysis": lambda: gsc_get_ctr_gap_analysis(
            gsc_data,
            min_impressions=int(tool_input.get("min_impressions", 100)),
            min_gap_pct=float(tool_input.get("min_gap_pct", 2.0)),
            limit=int(tool_input.get("limit", 20)),
        ),
        "gsc_get_low_hanging_fruit": lambda: gsc_get_low_hanging_fruit(
            gsc_data,
            min_impressions=int(tool_input.get("min_impressions", 50)),
            pos_min=float(tool_input.get("pos_min", 4.0)),
            pos_max=float(tool_input.get("pos_max", 10.0)),
            limit=int(tool_input.get("limit", 20)),
        ),
        "gsc_get_cannibalization": lambda: gsc_get_cannibalization(
            gsc_data,
            min_impressions=int(tool_input.get("min_impressions", 20)),
            limit=int(tool_input.get("limit", 20)),
        ),
        "gsc_get_position_distribution": lambda: gsc_get_position_distribution(gsc_data),
        "gsc_get_zero_click_opportunities": lambda: gsc_get_zero_click_opportunities(
            gsc_data,
            min_impressions=int(tool_input.get("min_impressions", 200)),
            limit=int(tool_input.get("limit", 20)),
        ),
        "gsc_get_branded_vs_nonbranded": lambda: gsc_get_branded_vs_nonbranded(
            gsc_data,
            brand_terms=tool_input.get("brand_terms") or [],
            limit=int(tool_input.get("limit", 20)),
        ),
        "gsc_get_query_intent_breakdown": lambda: gsc_get_query_intent_breakdown(
            gsc_data,
            limit=int(tool_input.get("limit", 15)),
        ),
        "gsc_get_page_query_coverage": lambda: gsc_get_page_query_coverage(
            gsc_data,
            min_queries=int(tool_input.get("min_queries", 5)),
            min_impressions_per_query=int(tool_input.get("min_impressions_per_query", 10)),
            limit=int(tool_input.get("limit", 20)),
        ),
    }
    fn = fn_map.get(tool_name)
    if fn is None:
        return json.dumps({"error": f"Onbekende GSC-tool: {tool_name}"})
    return json.dumps(fn(), ensure_ascii=False, indent=2)


def _dispatch_ga4(tool_name: str, tool_input: dict, ga4_data: GA4Data) -> str:
    fn_map = {
        "ga4_get_overview": lambda: ga4_get_overview(ga4_data),
        "ga4_get_channel_breakdown": lambda: get_channel_breakdown(ga4_data),
        "ga4_get_top_pages": lambda: ga4_get_top_pages(ga4_data, limit=int(tool_input.get("limit", 25))),
        "ga4_get_low_engagement_pages": lambda: get_low_engagement_pages(
            ga4_data,
            min_sessions=int(tool_input.get("min_sessions", 50)),
            max_engagement_seconds=float(tool_input.get("max_engagement_seconds", 30.0)),
            limit=int(tool_input.get("limit", 20)),
        ),
        "ga4_get_high_bounce_pages": lambda: get_high_bounce_pages(
            ga4_data,
            min_sessions=int(tool_input.get("min_sessions", 50)),
            bounce_threshold=float(tool_input.get("bounce_threshold", 70.0)),
            limit=int(tool_input.get("limit", 20)),
        ),
        "ga4_get_conversion_analysis": lambda: get_conversion_analysis(
            ga4_data,
            min_sessions=int(tool_input.get("min_sessions", 20)),
            limit=int(tool_input.get("limit", 20)),
        ),
        "ga4_get_landing_page_analysis": lambda: get_landing_page_analysis(
            ga4_data, limit=int(tool_input.get("limit", 25))
        ),
        "ga4_get_device_breakdown": lambda: get_device_breakdown(ga4_data),
        "ga4_get_organic_performance": lambda: get_organic_performance(ga4_data),
    }
    fn = fn_map.get(tool_name)
    if fn is None:
        return json.dumps({"error": f"Onbekende GA4-tool: {tool_name}"})
    return json.dumps(fn(), ensure_ascii=False, indent=2)


def _dispatch(tool_name: str, tool_input: dict, gsc_data: GSCData, ga4_data: GA4Data) -> str:
    if tool_name.startswith("gsc_"):
        return _dispatch_gsc(tool_name, tool_input, gsc_data)
    if tool_name.startswith("ga4_"):
        return _dispatch_ga4(tool_name, tool_input, ga4_data)
    return json.dumps({"error": f"Onbekende tool: {tool_name}"})


def run_analysis(gsc_data: GSCData, ga4_data: GA4Data, focus: str | None = None) -> str:
    """
    Voer een gecombineerde GSC + GA4 analyse uit.

    Args:
        gsc_data: Geparsede GSC-data
        ga4_data: Geparsede GA4-data
        focus:    Optionele specifieke vraag of aandachtspunt

    Returns:
        Strategisch gecombineerd rapport als Markdown-tekst.
    """
    client = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)

    context = (
        "Beschikbare data:\n\n"
        "GSC (Google Search Console):\n"
        f"  - Zoektermen: {len(gsc_data.queries)} rijen\n"
        f"  - Pagina's: {len(gsc_data.pages)} rijen\n"
        f"  - Gecombineerde query+page: {len(gsc_data.query_pages)} rijen\n"
        f"  - Bronbestanden: {', '.join(gsc_data.source_files)}\n\n"
        "GA4 (Google Analytics 4):\n"
        f"  - Pagina's: {len(ga4_data.pages)} rijen\n"
        f"  - Kanalen: {len(ga4_data.channels)} rijen\n"
        f"  - Landingspagina's: {len(ga4_data.landing_pages)} rijen\n"
        f"  - Apparaten: {len(ga4_data.devices)} rijen\n"
        f"  - Bronbestanden: {', '.join(ga4_data.source_files)}\n"
    )

    user_msg = (
        "Analyseer de gecombineerde GSC- en GA4-data en maak een strategisch rapport. "
        "Leg actief kruisverbanden tussen beide databronnen.\n\n"
        + context
    )
    if focus:
        user_msg += f"\nSpecifieke focus van de klant: {focus}"

    if not gsc_data.queries and not gsc_data.pages:
        return "Fout: geen bruikbare GSC-data gevonden. Controleer het GSC-bestand."
    if not ga4_data.pages and not ga4_data.channels:
        return "Fout: geen bruikbare GA4-data gevonden. Controleer het GA4-bestand."

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
                result = _dispatch(block.name, block.input, gsc_data, ga4_data)
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
