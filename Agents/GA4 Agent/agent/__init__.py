"""
GA4 Analyse Agent — hoofdmodule.
Claude analyseert GA4-data via tool use en levert een strategisch rapport.
"""

from __future__ import annotations

import json
import anthropic

from ..config import Config
from ..tools.excel_parser import GA4Data
from ..tools.analysis import (
    get_overview,
    get_channel_breakdown,
    get_top_pages,
    get_low_engagement_pages,
    get_high_bounce_pages,
    get_conversion_analysis,
    get_landing_page_analysis,
    get_device_breakdown,
    get_organic_performance,
)


_SYSTEM_PROMPT = """Je bent een Google Analytics 4 analist van Search Signals, een B2B digitaal \
marketingbureau. Je helpt klanten hun websitegedrag en conversies begrijpen en verbeteren.

Search Signals werkt als strategische partner — eerlijk, direct, resultaatgericht. Geen bullshit: \
als iets niet werkt, zeg je dat. Aanbevelingen zijn concreet en prioriteren op impact.

## Beschikbare analysetools

- get_overview — totale KPI's en kanaalsplit (altijd als eerste aanroepen)
- get_channel_breakdown — gedetailleerd overzicht per kanaal met conversieratio's
- get_top_pages — beste pagina's op sessies met engagement en conversie
- get_low_engagement_pages — pagina's met veel sessions maar lage engagementtijd
- get_high_bounce_pages — pagina's met hoge bounce rate en voldoende traffic
- get_conversion_analysis — convertiepagina's én zero-conversion pagina's met traffic
- get_landing_page_analysis — landingspaginaprestaties (eerste pagina van de sessie)
- get_device_breakdown — desktop / mobile / tablet split met conversieratio's
- get_organic_performance — geïsoleerde prestaties van het organische zoekkanaal

Roep altijd eerst get_overview aan. Roep daarna de tools aan die relevant zijn op basis \
van wat je ziet. Bel niet meer tools dan nodig — als de overview geen kanaaldata heeft, \
sla get_channel_breakdown dan over.

## Analytisch kader

**Engagementsignalen:**
- Gemiddelde engagementtijd < 30 seconden bij >50 sessies → content sluit niet aan of is te oppervlakkig
- Bounce rate > 70% op een landingspagina → mismatch between belofte (advertentie/snippet) en content
- Bounce rate < 20% → verdacht laag, controleer of GA4 correct is geconfigureerd

**Conversieanalyse:**
- Voor B2B geldt: een conversieratio van 1–3% op diensten-/contactpagina's is realistisch
- Pagina's met >100 sessies en 0 conversies zijn urgente verbeterkandidaten
- Vergelijk conversieratio per kanaal: organisch vs. direct vs. betaald zijn baselines

**Kanaalinterpretatie:**
- Organic Search > 40% van sessies = gezonde organische vindbaarheid
- Direct > 30% zonder duidelijk merk = mogelijk dark social of fout in tracking
- Referral met hoge bounce rate = kwalitatief zwakke bronpagina
- Paid Search zonder conversies = budgetverspilling — directe actie vereist

**Device:**
- B2B publiek: desktop meestal dominant (60–80%). Mobile > 40% is ongebruikelijk
- Mobile-gebruikers met hoge bounce: controleer mobiele UX van landingspagina's

**Prioritering via impact:**
- Hoog: pagina's met veel traffic maar geen conversies → directe omzetderving
- Middel: lage engagementtijd op diensten-/blogpagina's → content- of UX-probleem
- Laag: device- of kanaalmixy optimalisaties zonder directe conversieverliezen

## Structuur van het rapport

### 1. Samenvatting
Totale prestaties (sessies, gebruikers, conversies, conversieratio) en de 2–3 meest opvallende \
bevindingen.

### 2. Sterktes
Wat werkt goed? Welke kanalen, pagina's of patronen presteren boven verwachting?

### 3. Prioriteit 1 — Directe kansen (hoge impact, lage inspanning)
Per aanbeveling:
- Wat: welke pagina of kanaal
- Actie: wat moet er precies veranderen
- Verwacht effect: schatting in concrete aantallen (extra conversies per maand)

### 4. Prioriteit 2 — Structurele verbeteringen
Aanbevelingen die meer werk kosten maar strategisch belangrijk zijn.

### 5. Prioriteit 3 — Aandachtspunten & monitoring
Waarschuwingssignalen of patronen die gemonitord moeten worden.

Schrijf in het Nederlands. Wees direct en concreet. Vermijd jargon zonder uitleg."""


_TOOLS = [
    {
        "name": "get_overview",
        "description": (
            "Totale GA4 KPI's: sessies, gebruikers, conversies, conversieratio en kanaalsamenvatting. "
            "Altijd als eerste aanroepen."
        ),
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_channel_breakdown",
        "description": (
            "Gedetailleerd overzicht per verkeersbron (Organic, Direct, Referral, Paid, Social, Email). "
            "Sessieaandeel, bounce rate, gemiddelde sessieduur en conversieratio per kanaal."
        ),
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_top_pages",
        "description": (
            "Beste pagina's gesorteerd op sessies. Pad, titel, sessies, pageviews, "
            "bounce rate, gemiddelde engagementtijd en conversies."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Aantal pagina's (standaard 25, max 50)",
                }
            },
            "required": [],
        },
    },
    {
        "name": "get_low_engagement_pages",
        "description": (
            "Pagina's met voldoende traffic maar lage gemiddelde engagementtijd. "
            "Kandidaten voor content- of UX-verbetering."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "min_sessions": {"type": "integer", "description": "Minimum sessies (standaard 50)"},
                "max_engagement_seconds": {
                    "type": "number",
                    "description": "Maximum engagementtijd in seconden (standaard 30)",
                },
                "limit": {"type": "integer", "description": "Max resultaten (standaard 20)"},
            },
            "required": [],
        },
    },
    {
        "name": "get_high_bounce_pages",
        "description": (
            "Pagina's met hoge bounce rate (standaard >70%) en voldoende traffic. "
            "Hoge bounce duidt op mismatch tussen verwachting en content."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "min_sessions": {"type": "integer", "description": "Minimum sessies (standaard 50)"},
                "bounce_threshold": {
                    "type": "number",
                    "description": "Minimale bounce rate % (standaard 70.0)",
                },
                "limit": {"type": "integer", "description": "Max resultaten (standaard 20)"},
            },
            "required": [],
        },
    },
    {
        "name": "get_conversion_analysis",
        "description": (
            "Convertiepagina's (gerangschikt op conversies) én pagina's met traffic maar nul conversies. "
            "Direct inzicht in waar omzet lekt."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "min_sessions": {
                    "type": "integer",
                    "description": "Minimum sessies voor zero-conversion pagina's (standaard 20)",
                },
                "limit": {"type": "integer", "description": "Max resultaten per categorie (standaard 20)"},
            },
            "required": [],
        },
    },
    {
        "name": "get_landing_page_analysis",
        "description": (
            "Prestaties van landingspagina's (eerste pagina van de sessie). "
            "Hoge bounce rate hier duidt op mismatch met de traffic-bron."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "Aantal landingspagina's (standaard 25)"},
            },
            "required": [],
        },
    },
    {
        "name": "get_device_breakdown",
        "description": (
            "Sessies, gebruikers, bounce rate en conversies per apparaattype (desktop / mobile / tablet). "
            "Voor B2B is desktop dominant — afwijkingen wijzen op UX-problemen of verkeerde doelgroep."
        ),
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_organic_performance",
        "description": (
            "Geïsoleerde prestaties van het organische zoekkanaal. "
            "Gebruik dit om SEO-bijdrage te beoordelen los van betaald en direct verkeer."
        ),
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
]


def _dispatch(tool_name: str, tool_input: dict, data: GA4Data) -> str:
    fn_map = {
        "get_overview": lambda: get_overview(data),
        "get_channel_breakdown": lambda: get_channel_breakdown(data),
        "get_top_pages": lambda: get_top_pages(data, limit=int(tool_input.get("limit", 25))),
        "get_low_engagement_pages": lambda: get_low_engagement_pages(
            data,
            min_sessions=int(tool_input.get("min_sessions", 50)),
            max_engagement_seconds=float(tool_input.get("max_engagement_seconds", 30.0)),
            limit=int(tool_input.get("limit", 20)),
        ),
        "get_high_bounce_pages": lambda: get_high_bounce_pages(
            data,
            min_sessions=int(tool_input.get("min_sessions", 50)),
            bounce_threshold=float(tool_input.get("bounce_threshold", 70.0)),
            limit=int(tool_input.get("limit", 20)),
        ),
        "get_conversion_analysis": lambda: get_conversion_analysis(
            data,
            min_sessions=int(tool_input.get("min_sessions", 20)),
            limit=int(tool_input.get("limit", 20)),
        ),
        "get_landing_page_analysis": lambda: get_landing_page_analysis(
            data, limit=int(tool_input.get("limit", 25))
        ),
        "get_device_breakdown": lambda: get_device_breakdown(data),
        "get_organic_performance": lambda: get_organic_performance(data),
    }
    fn = fn_map.get(tool_name)
    if fn is None:
        return json.dumps({"error": f"Onbekende tool: {tool_name}"})
    return json.dumps(fn(), ensure_ascii=False, indent=2)


def run_analysis(data: GA4Data, focus: str | None = None) -> str:
    """
    Voer een volledige GA4-analyse uit op de geparsede Excel-data.

    Args:
        data:  Geparsede GA4Data uit Excel-export
        focus: Optionele specifieke vraag of aandachtspunt van de gebruiker

    Returns:
        Strategisch GA4-rapport als opgemaakte Markdown-tekst.
    """
    client = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)

    context = (
        f"Beschikbare data:\n"
        f"  - Pagina's: {len(data.pages)} rijen\n"
        f"  - Kanalen: {len(data.channels)} rijen\n"
        f"  - Landingspagina's: {len(data.landing_pages)} rijen\n"
        f"  - Apparaten: {len(data.devices)} rijen\n"
        f"  - Bronbestanden: {', '.join(data.source_files)}\n"
    )

    user_msg = f"Analyseer de GA4-data en maak een strategisch rapport.\n\n{context}"
    if focus:
        user_msg += f"\nSpecifieke focus van de klant: {focus}"

    if not data.pages and not data.channels:
        return "Fout: geen bruikbare GA4-data gevonden. Controleer het Excel-bestand."

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
                result = _dispatch(block.name, block.input, data)
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
