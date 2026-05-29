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

### 1. Samenvatting
Totale prestaties (klikken, vertoningen, kosten, conversies, CPA, ROAS als beschikbaar) \
en de 2–3 meest opvallende bevindingen.

### 2. Sterktes
Welke campagnes, advertentiegroepen of zoekwoorden presteren uitzonderlijk goed? \
Wat zijn de drivers van succes?

### 3. Prioriteit 1 — Directe kansen (hoge impact, lage inspanning)
Concrete actiepunten. Geef per aanbeveling:
- Wat: welk zoekwoord, advertentiegroep of campagne
- Actie: wat moet er precies veranderen
- Verwacht effect: geschatte besparing of extra conversies

### 4. Prioriteit 2 — Structurele verbeteringen (hogere inspanning, grotere impact)
Aanbevelingen die meer werk kosten maar strategisch belangrijk zijn \
(bijv. campagnestructuur herindelen, kwaliteitsscore-traject, nieuwe zoekwoordgroepen).

### 5. Prioriteit 3 — Aandachtspunten
Waarschuwingssignalen, budgetlimieten, kwaliteitsscores in vrije val, of \
trends die gemonitord moeten worden.

Schrijf in het Nederlands. Wees direct en concreet. Vermijd jargon zonder uitleg. \
Geef altijd schattingen van de impact in concrete aantallen (euro's bespaard, extra conversies)."""


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


def run_analysis(data: AdsData, focus: str | None = None, data2: AdsData | None = None) -> str:
    """
    Voer een volledige Google Ads analyse uit op de opgegeven data.

    Args:
        data:   Geparsede Google Ads data — basisperiode (of enige periode)
        focus:  Optionele focusvraag of aandachtspunt van de gebruiker
        data2:  Optionele tweede periode voor vergelijkingsanalyse

    Returns:
        Strategisch Google Ads rapport als opgemaakte Markdown-tekst.
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
        return "Fout: geen bruikbare Google Ads data gevonden. Controleer het Excel-bestand."

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
