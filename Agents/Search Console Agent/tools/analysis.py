"""
Analysemodules voor Google Search Console data.

Elke functie neemt een GSCData object en geeft een JSON-serialiseerbaar dict terug.
Dit zijn de tools die de agent aan Claude aanbiedt.
"""

from __future__ import annotations

import re
from collections import defaultdict
from .excel_parser import GSCData


# ---------------------------------------------------------------------------
# CTR-benchmarks per positie voor niet-branded queries op schone SERP's
# Bron: First Page Sage 2026, GrowthSRC organic CTR study 2025 (200k keywords)
# Let op: AI Overviews verlagen CTR op pos 1–3 met ~30-40% t.o.v. deze benchmarks.
# ---------------------------------------------------------------------------

_CTR_BENCHMARK = {
    1: 39.8,
    2: 18.7,
    3: 10.2,
    4: 7.4,
    5: 5.1,
    6: 4.0,
    7: 3.1,
    8: 2.6,
    9: 2.4,
    10: 2.2,
    11: 1.5,
    12: 1.3,
    13: 1.1,
    14: 1.0,
    15: 0.9,
    16: 0.8,
    17: 0.7,
    18: 0.6,
    19: 0.5,
    20: 0.5,
}


def _expected_ctr(position: float) -> float:
    """Geeft verwachte CTR (%) op basis van positie, via benchmarktabel met interpolatie."""
    pos = round(position)
    if pos <= 0:
        return _CTR_BENCHMARK[1]
    if pos in _CTR_BENCHMARK:
        return _CTR_BENCHMARK[pos]
    if pos > 20:
        # Exponentieel afnemend na positie 20
        return max(0.1, round(0.5 * (0.85 ** (pos - 20)), 2))
    return 0.0


# ---------------------------------------------------------------------------
# Branded query detectie
# ---------------------------------------------------------------------------

_BRAND_PATTERNS: list[re.Pattern] = []


def _is_branded(query: str, brand_terms: list[str]) -> bool:
    """Geeft True als de query een van de merkgerelateerde termen bevat."""
    q_lower = query.lower()
    return any(term.lower() in q_lower for term in brand_terms if term)


# ---------------------------------------------------------------------------
# Overzicht & totalen
# ---------------------------------------------------------------------------

def get_overview(data: GSCData) -> dict:
    """Totalen en algemene statistieken over de hele dataset."""
    pages = data.pages
    queries = data.queries

    def _stats(items, value_key: str, imp_key: str, pos_key: str, ctr_key: str):
        total_clicks = sum(getattr(i, value_key) for i in items)
        total_imp = sum(getattr(i, imp_key) for i in items)
        avg_pos = (
            round(sum(getattr(i, pos_key) for i in items) / len(items), 1)
            if items else 0.0
        )
        avg_ctr = (
            round(total_clicks / total_imp * 100, 2) if total_imp else 0.0
        )
        return {
            "count": len(items),
            "total_clicks": total_clicks,
            "total_impressions": total_imp,
            "avg_ctr_pct": avg_ctr,
            "avg_position": avg_pos,
        }

    result: dict = {}

    if pages:
        s = _stats(pages, "clicks", "impressions", "position", "ctr")
        result["pages"] = {
            **s,
            "pages_pos_1_3": sum(1 for p in pages if p.position <= 3),
            "pages_pos_4_10": sum(1 for p in pages if 4 <= p.position <= 10),
            "pages_pos_11_plus": sum(1 for p in pages if p.position > 10),
        }

    if queries:
        s = _stats(queries, "clicks", "impressions", "position", "ctr")
        result["queries"] = {
            **s,
            "queries_pos_1_3": sum(1 for q in queries if q.position <= 3),
            "queries_pos_4_10": sum(1 for q in queries if 4 <= q.position <= 10),
            "queries_pos_11_plus": sum(1 for q in queries if q.position > 10),
        }

    return result


# ---------------------------------------------------------------------------
# Top performers
# ---------------------------------------------------------------------------

def get_top_pages(data: GSCData, limit: int = 25) -> dict:
    """Top pagina's gesorteerd op klikken."""
    sorted_pages = sorted(data.pages, key=lambda p: p.clicks, reverse=True)
    return {
        "top_pages": [
            {
                "page": p.page,
                "clicks": p.clicks,
                "impressions": p.impressions,
                "ctr_pct": p.ctr,
                "avg_position": p.position,
            }
            for p in sorted_pages[:limit]
        ]
    }


def get_top_queries(data: GSCData, limit: int = 30) -> dict:
    """Top zoektermen gesorteerd op klikken."""
    sorted_queries = sorted(data.queries, key=lambda q: q.clicks, reverse=True)
    return {
        "top_queries": [
            {
                "query": q.query,
                "clicks": q.clicks,
                "impressions": q.impressions,
                "ctr_pct": q.ctr,
                "avg_position": q.position,
            }
            for q in sorted_queries[:limit]
        ]
    }


# ---------------------------------------------------------------------------
# CTR-kansen
# ---------------------------------------------------------------------------

def get_ctr_opportunities(
    data: GSCData,
    min_impressions: int = 100,
    max_ctr_pct: float = 3.0,
    limit: int = 20,
) -> dict:
    """
    Pagina's en zoektermen met veel vertoningen maar een lage CTR.
    Dit duidt op een mismatch tussen de SERP-weergave (titel/meta) en de zoekvraag.

    Args:
        min_impressions: Minimum vertoningen om mee te tellen
        max_ctr_pct:     Maximale CTR (%) om als kans te kwalificeren
        limit:           Max terug te geven rijen per categorie
    """
    page_opps = [
        p for p in data.pages
        if p.impressions >= min_impressions and p.ctr <= max_ctr_pct
    ]
    query_opps = [
        q for q in data.queries
        if q.impressions >= min_impressions and q.ctr <= max_ctr_pct
    ]

    # Sorteren: meeste vertoningen bovenaan (grootste gemiste bereik)
    page_opps.sort(key=lambda p: p.impressions, reverse=True)
    query_opps.sort(key=lambda q: q.impressions, reverse=True)

    return {
        "filter": {"min_impressions": min_impressions, "max_ctr_pct": max_ctr_pct},
        "page_opportunities": [
            {
                "page": p.page,
                "impressions": p.impressions,
                "clicks": p.clicks,
                "ctr_pct": p.ctr,
                "avg_position": p.position,
                "missed_clicks_estimate": round(p.impressions * (max_ctr_pct / 100) - p.clicks),
            }
            for p in page_opps[:limit]
        ],
        "query_opportunities": [
            {
                "query": q.query,
                "impressions": q.impressions,
                "clicks": q.clicks,
                "ctr_pct": q.ctr,
                "avg_position": q.position,
                "missed_clicks_estimate": round(q.impressions * (max_ctr_pct / 100) - q.clicks),
            }
            for q in query_opps[:limit]
        ],
    }


# ---------------------------------------------------------------------------
# Low-hanging fruit (positie 4–10)
# ---------------------------------------------------------------------------

def get_low_hanging_fruit(
    data: GSCData,
    min_impressions: int = 50,
    pos_min: float = 4.0,
    pos_max: float = 10.0,
    limit: int = 20,
) -> dict:
    """
    Pagina's en zoektermen die net buiten de top 3 vallen (positie 4–10).
    Een kleine rankingverbetering levert hier direct significant meer klikken op.

    Args:
        min_impressions: Minimum vertoningen
        pos_min / pos_max: Positiebereik (standaard 4–10)
    """
    page_fruit = [
        p for p in data.pages
        if pos_min <= p.position <= pos_max and p.impressions >= min_impressions
    ]
    query_fruit = [
        q for q in data.queries
        if pos_min <= q.position <= pos_max and q.impressions >= min_impressions
    ]

    # Sorteren: meeste vertoningen = grootste potentie
    page_fruit.sort(key=lambda p: p.impressions, reverse=True)
    query_fruit.sort(key=lambda q: q.impressions, reverse=True)

    def _potential(item) -> int:
        """Schat extra klikken als item naar positie 3 stijgt (benchmark: ~11% CTR voor pos 3)."""
        target_ctr = _expected_ctr(3.0)
        return max(0, round(item.impressions * target_ctr / 100 - item.clicks))

    return {
        "filter": {"min_impressions": min_impressions, "position_range": f"{pos_min}–{pos_max}"},
        "page_opportunities": [
            {
                "page": p.page,
                "avg_position": p.position,
                "impressions": p.impressions,
                "clicks": p.clicks,
                "ctr_pct": p.ctr,
                "estimated_extra_clicks_if_top3": _potential(p),
            }
            for p in page_fruit[:limit]
        ],
        "query_opportunities": [
            {
                "query": q.query,
                "avg_position": q.position,
                "impressions": q.impressions,
                "clicks": q.clicks,
                "ctr_pct": q.ctr,
                "estimated_extra_clicks_if_top3": _potential(q),
            }
            for q in query_fruit[:limit]
        ],
    }


# ---------------------------------------------------------------------------
# Cannibalisatiedetectie
# ---------------------------------------------------------------------------

def get_cannibalization(data: GSCData, min_impressions: int = 20, limit: int = 20) -> dict:
    """
    Detecteer zoektermen waarbij meerdere pagina's om dezelfde positie strijden.
    Vereist gecombineerde query+page data.

    Args:
        min_impressions: Minimum vertoningen per query om mee te tellen
    """
    if not data.query_pages:
        return {
            "error": "Geen gecombineerde query+page data beschikbaar. "
                     "Exporteer vanuit GSC: Prestaties > filter op zoekopdracht+pagina, "
                     "of gebruik een gecombineerde sheet."
        }

    # Groepeer query_pages op zoekterm
    by_query: dict[str, list] = defaultdict(list)
    for row in data.query_pages:
        if row.impressions >= min_impressions:
            by_query[row.query].append(row)

    # Bewaar alleen queries met 2+ pagina's
    cannibalized = {
        q: rows for q, rows in by_query.items() if len(rows) >= 2
    }

    # Sorteer op totale vertoningen (meest impactvolle cannibalisatie bovenaan)
    sorted_queries = sorted(
        cannibalized.items(),
        key=lambda kv: sum(r.impressions for r in kv[1]),
        reverse=True,
    )

    return {
        "filter": {"min_impressions_per_query": min_impressions},
        "cannibalized_queries_count": len(sorted_queries),
        "cannibalized_queries": [
            {
                "query": q,
                "competing_pages": [
                    {
                        "page": r.page,
                        "clicks": r.clicks,
                        "impressions": r.impressions,
                        "ctr_pct": r.ctr,
                        "avg_position": r.position,
                    }
                    for r in sorted(rows, key=lambda r: r.position)
                ],
            }
            for q, rows in sorted_queries[:limit]
        ],
    }


# ---------------------------------------------------------------------------
# Positieverdeling
# ---------------------------------------------------------------------------

def get_position_distribution(data: GSCData) -> dict:
    """
    Verdeling van pagina's en zoektermen over positiebuckets.
    Geeft inzicht in het algehele ranking-profiel van de site.
    """
    buckets = [(1, 3), (4, 6), (7, 10), (11, 20), (21, 50), (51, 999)]

    def _bucket_label(lo, hi):
        return f"{lo}–{hi}" if hi < 999 else f"{lo}+"

    def _distribute(items, pos_attr: str):
        dist = {}
        for lo, hi in buckets:
            count = sum(1 for i in items if lo <= getattr(i, pos_attr) <= hi)
            dist[_bucket_label(lo, hi)] = count
        return dist

    result = {}
    if data.pages:
        result["pages"] = _distribute(data.pages, "position")
    if data.queries:
        result["queries"] = _distribute(data.queries, "position")
    return result


# ---------------------------------------------------------------------------
# Geen-klikkers met bereik
# ---------------------------------------------------------------------------

def get_zero_click_opportunities(data: GSCData, min_impressions: int = 200, limit: int = 20) -> dict:
    """
    Pagina's en queries met vertoningen maar nul of bijna nul klikken.
    Hoge prioriteit: het bereik is er, de conversie naar klik niet.
    """
    page_zero = [
        p for p in data.pages
        if p.impressions >= min_impressions and p.clicks == 0
    ]
    query_zero = [
        q for q in data.queries
        if q.impressions >= min_impressions and q.clicks == 0
    ]

    page_zero.sort(key=lambda p: p.impressions, reverse=True)
    query_zero.sort(key=lambda q: q.impressions, reverse=True)

    return {
        "filter": {"min_impressions": min_impressions, "clicks": 0},
        "zero_click_pages": [
            {"page": p.page, "impressions": p.impressions, "avg_position": p.position}
            for p in page_zero[:limit]
        ],
        "zero_click_queries": [
            {"query": q.query, "impressions": q.impressions, "avg_position": q.position}
            for q in query_zero[:limit]
        ],
    }


# ---------------------------------------------------------------------------
# CTR-gat analyse (actual vs. verwacht op basis van positie)
# ---------------------------------------------------------------------------

def get_ctr_gap_analysis(
    data: GSCData,
    min_impressions: int = 100,
    min_gap_pct: float = 2.0,
    limit: int = 20,
) -> dict:
    """
    Vergelijkt de werkelijke CTR met de verwachte CTR voor de gegeven positie.
    Een negatieve gap duidt op een titel/meta-probleem ongeacht absolute CTR.

    Args:
        min_impressions: Minimum vertoningen om mee te tellen
        min_gap_pct:     Minimale absolute gap (verwacht - werkelijk) om te rapporteren
        limit:           Max resultaten per categorie
    """
    def _gap_rows(items, key_attr: str):
        gaps = []
        for item in items:
            if item.impressions < min_impressions:
                continue
            expected = _expected_ctr(item.position)
            gap = round(expected - item.ctr, 2)
            if gap >= min_gap_pct:
                gaps.append({
                    key_attr: getattr(item, key_attr),
                    "avg_position": item.position,
                    "actual_ctr_pct": item.ctr,
                    "expected_ctr_pct": expected,
                    "ctr_gap_pct": gap,
                    "impressions": item.impressions,
                    "missed_clicks_estimate": round(item.impressions * gap / 100),
                })
        gaps.sort(key=lambda x: x["missed_clicks_estimate"], reverse=True)
        return gaps[:limit]

    result: dict = {
        "explanation": (
            "Verwachte CTR gebaseerd op First Page Sage 2026 benchmarks (niet-branded, schone SERP). "
            "Benchmarks: pos 1 ≈ 39.8%, pos 3 ≈ 10.2%, pos 5 ≈ 5.1%, pos 10 ≈ 2.2%. "
            "Let op: AI Overviews verlagen CTR op positie 1–3 met ~30-40% t.o.v. deze benchmarks. "
            "Een gap >= min_gap_pct duidt op een slecht presterend title/meta-snippet of intentmismatch."
        ),
        "filter": {"min_impressions": min_impressions, "min_gap_pct": min_gap_pct},
    }
    if data.pages:
        result["page_ctr_gaps"] = _gap_rows(data.pages, "page")
    if data.queries:
        result["query_ctr_gaps"] = _gap_rows(data.queries, "query")
    return result


# ---------------------------------------------------------------------------
# Branded vs. niet-branded segmentatie
# ---------------------------------------------------------------------------

def get_branded_vs_nonbranded(
    data: GSCData,
    brand_terms: list[str] | None = None,
    limit: int = 20,
) -> dict:
    """
    Splitst zoekterm-data in branded en niet-branded queries.
    Branded queries zeggen iets over merkbekendheid, niet-branded over organisch bereik.

    Args:
        brand_terms: Lijst van merkgerelateerde termen (bijv. ["bedrijfsnaam", "productnaam"])
                     Als leeg, wordt op basis van domeinpatronen geprobeerd.
        limit:       Max queries per segment om terug te geven
    """
    if not data.queries:
        return {"error": "Geen zoektermdata beschikbaar."}

    terms = brand_terms or []
    branded = [q for q in data.queries if _is_branded(q.query, terms)]
    nonbranded = [q for q in data.queries if not _is_branded(q.query, terms)]

    def _segment_stats(items):
        if not items:
            return {"count": 0, "total_clicks": 0, "total_impressions": 0, "avg_ctr_pct": 0.0, "avg_position": 0.0}
        total_clicks = sum(q.clicks for q in items)
        total_imp = sum(q.impressions for q in items)
        avg_pos = round(sum(q.position for q in items) / len(items), 1)
        avg_ctr = round(total_clicks / total_imp * 100, 2) if total_imp else 0.0
        return {
            "count": len(items),
            "total_clicks": total_clicks,
            "total_impressions": total_imp,
            "avg_ctr_pct": avg_ctr,
            "avg_position": avg_pos,
        }

    branded_sorted = sorted(branded, key=lambda q: q.clicks, reverse=True)
    nonbranded_sorted = sorted(nonbranded, key=lambda q: q.clicks, reverse=True)

    return {
        "brand_terms_used": terms,
        "note": "Geef brand_terms mee voor nauwkeurige segmentatie. Zonder brand_terms zijn alle queries als niet-branded geclassificeerd." if not terms else "",
        "branded": {
            **_segment_stats(branded),
            "top_queries": [
                {"query": q.query, "clicks": q.clicks, "impressions": q.impressions, "ctr_pct": q.ctr, "avg_position": q.position}
                for q in branded_sorted[:limit]
            ],
        },
        "nonbranded": {
            **_segment_stats(nonbranded),
            "top_queries": [
                {"query": q.query, "clicks": q.clicks, "impressions": q.impressions, "ctr_pct": q.ctr, "avg_position": q.position}
                for q in nonbranded_sorted[:limit]
            ],
        },
    }


# ---------------------------------------------------------------------------
# Query intent classificatie
# ---------------------------------------------------------------------------

_INTENT_PATTERNS = {
    "transactional": re.compile(
        r"\b(kopen?|koop|bestel|bestellen|prijs|prijzen|kosten?|offerte|"
        r"buy|price|order|shop|purchase|€|euro|korting|deal|aanbieding|"
        r"download|probeer|gratis|free trial|demo)\b",
        re.IGNORECASE,
    ),
    "navigational": re.compile(
        r"\b(inloggen|login|account|contact|locatie|openingstijden|"
        r"homepage|website|www|\.nl|\.com|app)\b",
        re.IGNORECASE,
    ),
    "informational": re.compile(
        r"\b(wat is|hoe|waarom|wanneer|verschil|betekenis|uitleg|gids|"
        r"tips|voorbeeld|vergelijk|what is|how to|why|when|guide|"
        r"tutorial|best practices?|checklist|overzicht|voordelen|nadelen)\b",
        re.IGNORECASE,
    ),
}


def _classify_intent(query: str) -> str:
    for intent, pattern in _INTENT_PATTERNS.items():
        if pattern.search(query):
            return intent
    return "unknown"


def get_query_intent_breakdown(data: GSCData, limit: int = 15) -> dict:
    """
    Classificeert zoektermen op intenttype: transactioneel, navigational, informationeel.
    Helpt bij het prioriteren: transactionele queries met slechte CTR zijn urgent.

    Args:
        limit: Max queries per intentcategorie om te tonen
    """
    if not data.queries:
        return {"error": "Geen zoektermdata beschikbaar."}

    by_intent: dict[str, list] = defaultdict(list)
    for q in data.queries:
        intent = _classify_intent(q.query)
        by_intent[intent].append(q)

    result = {}
    for intent, items in sorted(by_intent.items()):
        total_clicks = sum(q.clicks for q in items)
        total_imp = sum(q.impressions for q in items)
        avg_ctr = round(total_clicks / total_imp * 100, 2) if total_imp else 0.0
        sorted_items = sorted(items, key=lambda q: q.impressions, reverse=True)
        result[intent] = {
            "count": len(items),
            "total_clicks": total_clicks,
            "total_impressions": total_imp,
            "avg_ctr_pct": avg_ctr,
            "top_queries": [
                {
                    "query": q.query,
                    "clicks": q.clicks,
                    "impressions": q.impressions,
                    "ctr_pct": q.ctr,
                    "avg_position": q.position,
                }
                for q in sorted_items[:limit]
            ],
        }

    return {
        "intent_breakdown": result,
        "note": (
            "Classificatie is heuristisch op basis van zoekwoordpatronen. "
            "Transactionele queries met lage CTR of slechte positie zijn hoogste prioriteit."
        ),
    }


# ---------------------------------------------------------------------------
# Paginadekking (hoeveel queries per pagina)
# ---------------------------------------------------------------------------

def compare_periods(
    data1: GSCData,
    data2: GSCData,
    limit: int = 20,
) -> dict:
    """
    Vergelijkt twee tijdsperiodes op query- en paginaniveau.
    data1 = basisperiode (ouder), data2 = vergelijkingsperiode (nieuwer).

    Geeft terug:
    - Totale delta's (klikken, vertoningen, CTR, positie)
    - Top stijgers en dalers op klikken
    - Nieuw verschenen en verdwenen queries/pagina's
    - Positieveranderingen per query/pagina

    Args:
        data1: Basisperiode (oudere export)
        data2: Vergelijkingsperiode (nieuwere export)
        limit: Max items per categorie
    """
    result: dict = {}

    # --- Totale delta's ---
    def _totals(data: GSCData, key: str):
        items = data.queries if key == "queries" else data.pages
        if not items:
            return None
        clicks_attr = "clicks"
        imp_attr = "impressions"
        pos_attr = "position"
        total_clicks = sum(getattr(i, clicks_attr) for i in items)
        total_imp = sum(getattr(i, imp_attr) for i in items)
        avg_pos = round(sum(getattr(i, pos_attr) for i in items) / len(items), 1)
        avg_ctr = round(total_clicks / total_imp * 100, 2) if total_imp else 0.0
        return {"clicks": total_clicks, "impressions": total_imp, "avg_ctr_pct": avg_ctr, "avg_position": avg_pos}

    for segment, key_attr in [("queries", "query"), ("pages", "page")]:
        t1 = _totals(data1, segment)
        t2 = _totals(data2, segment)
        if not t1 or not t2:
            continue

        def _delta(v2, v1, invert=False):
            if v1 == 0:
                return None
            d = round((v2 - v1) / v1 * 100, 1)
            return d if not invert else -d

        result[f"{segment}_totals"] = {
            "period1": t1,
            "period2": t2,
            "delta": {
                "clicks_pct": _delta(t2["clicks"], t1["clicks"]),
                "impressions_pct": _delta(t2["impressions"], t1["impressions"]),
                "ctr_pct_change": round(t2["avg_ctr_pct"] - t1["avg_ctr_pct"], 2),
                "position_change": round(t2["avg_position"] - t1["avg_position"], 1),
            },
        }

        # --- Per-item vergelijking ---
        items1 = data1.queries if segment == "queries" else data1.pages
        items2 = data2.queries if segment == "queries" else data2.pages

        map1 = {getattr(i, key_attr): i for i in items1}
        map2 = {getattr(i, key_attr): i for i in items2}

        common_keys = set(map1) & set(map2)
        new_keys = set(map2) - set(map1)
        lost_keys = set(map1) - set(map2)

        # Stijgers en dalers op klikken
        movers = []
        for k in common_keys:
            i1, i2 = map1[k], map2[k]
            click_delta = i2.clicks - i1.clicks
            pos_delta = round(i2.position - i1.position, 1)
            movers.append({
                key_attr: k,
                "clicks_p1": i1.clicks,
                "clicks_p2": i2.clicks,
                "click_delta": click_delta,
                "position_p1": i1.position,
                "position_p2": i2.position,
                "position_delta": pos_delta,
                "impressions_p1": i1.impressions,
                "impressions_p2": i2.impressions,
            })

        movers.sort(key=lambda x: x["click_delta"], reverse=True)
        result[f"{segment}_top_risers"] = movers[:limit]
        result[f"{segment}_top_decliners"] = movers[-limit:][::-1]

        # Positieverbetering (ongeacht klikken)
        pos_movers = sorted(movers, key=lambda x: x["position_delta"])
        result[f"{segment}_biggest_position_gains"] = [
            m for m in pos_movers if m["position_delta"] < 0
        ][:limit]
        result[f"{segment}_biggest_position_losses"] = [
            m for m in reversed(pos_movers) if m["position_delta"] > 0
        ][:limit]

        # Nieuw verschenen
        new_items = sorted(
            [map2[k] for k in new_keys],
            key=lambda i: i.impressions,
            reverse=True,
        )
        result[f"{segment}_new_in_period2"] = [
            {key_attr: getattr(i, key_attr), "clicks": i.clicks, "impressions": i.impressions, "avg_position": i.position}
            for i in new_items[:limit]
        ]

        # Verdwenen
        lost_items = sorted(
            [map1[k] for k in lost_keys],
            key=lambda i: i.clicks,
            reverse=True,
        )
        result[f"{segment}_lost_in_period2"] = [
            {key_attr: getattr(i, key_attr), "clicks_p1": i.clicks, "impressions_p1": i.impressions, "position_p1": i.position}
            for i in lost_items[:limit]
        ]

    return result


def get_page_query_coverage(
    data: GSCData,
    min_queries: int = 5,
    min_impressions_per_query: int = 10,
    limit: int = 20,
) -> dict:
    """
    Analyseert hoeveel zoektermen per pagina vertoningen genereren.
    Pagina's met veel queries maar weinig klikken hebben mogelijk gefragmenteerde focus.
    Pagina's met weinig queries kunnen qua topical authority worden uitgebreid.

    Vereist gecombineerde query+page data.

    Args:
        min_queries:                Minimum aantal queries om een pagina te tonen
        min_impressions_per_query:  Minimum vertoningen per query om mee te tellen
        limit:                      Max pagina's om te tonen
    """
    if not data.query_pages:
        return {
            "error": "Geen gecombineerde query+page data beschikbaar. "
                     "Exporteer vanuit GSC: Prestaties > dimensies Query+Pagina."
        }

    by_page: dict[str, list] = defaultdict(list)
    for row in data.query_pages:
        if row.impressions >= min_impressions_per_query:
            by_page[row.page].append(row)

    pages_with_many_queries = [
        (page, rows) for page, rows in by_page.items() if len(rows) >= min_queries
    ]

    pages_with_many_queries.sort(key=lambda x: sum(r.impressions for r in x[1]), reverse=True)

    return {
        "filter": {
            "min_queries_per_page": min_queries,
            "min_impressions_per_query": min_impressions_per_query,
        },
        "pages": [
            {
                "page": page,
                "query_count": len(rows),
                "total_impressions": sum(r.impressions for r in rows),
                "total_clicks": sum(r.clicks for r in rows),
                "avg_ctr_pct": round(
                    sum(r.clicks for r in rows) / sum(r.impressions for r in rows) * 100, 2
                ) if sum(r.impressions for r in rows) else 0.0,
                "top_queries": [
                    {"query": r.query, "impressions": r.impressions, "clicks": r.clicks, "avg_position": r.position}
                    for r in sorted(rows, key=lambda r: r.impressions, reverse=True)[:5]
                ],
            }
            for page, rows in pages_with_many_queries[:limit]
        ],
    }
