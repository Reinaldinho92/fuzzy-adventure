"""
Analysemodules voor Google Ads data.

Elke functie neemt een AdsData object en geeft een JSON-serialiseerbaar dict terug.
Dit zijn de tools die de agent aan Claude aanbiedt.
"""

from __future__ import annotations

from collections import defaultdict
from .excel_parser import AdsData, CampaignRow, AdGroupRow, KeywordRow, SearchTermRow


# ---------------------------------------------------------------------------
# Overzicht & totalen
# ---------------------------------------------------------------------------

def get_overview(data: AdsData) -> dict:
    """Totalen en algemene statistieken over de hele dataset."""

    def _totals(items, label: str) -> dict | None:
        if not items:
            return None
        total_clicks = sum(i.clicks for i in items)
        total_imp = sum(i.impressions for i in items)
        total_cost = round(sum(i.cost for i in items), 2)
        total_conv = round(sum(i.conversions for i in items), 2)
        avg_ctr = round(total_clicks / total_imp * 100, 2) if total_imp else 0.0
        avg_cpc = round(total_cost / total_clicks, 2) if total_clicks else 0.0
        conv_rate = round(total_conv / total_clicks * 100, 2) if total_clicks else 0.0
        cpa = round(total_cost / total_conv, 2) if total_conv else 0.0
        return {
            "label": label,
            "count": len(items),
            "total_clicks": total_clicks,
            "total_impressions": total_imp,
            "total_cost_eur": total_cost,
            "total_conversions": total_conv,
            "avg_ctr_pct": avg_ctr,
            "avg_cpc_eur": avg_cpc,
            "conv_rate_pct": conv_rate,
            "cpa_eur": cpa,
        }

    result: dict = {}
    for items, label, key in [
        (data.campaigns, "Campagnes", "campaigns"),
        (data.ad_groups, "Advertentiegroepen", "ad_groups"),
        (data.keywords, "Zoekwoorden", "keywords"),
        (data.search_terms, "Zoektermen", "search_terms"),
    ]:
        t = _totals(items, label)
        if t:
            result[key] = t

    # Gebruik campagnedata als primaire bron voor totalen, anders zoekwoorden
    primary = result.get("campaigns") or result.get("keywords")
    if primary:
        result["summary"] = {
            "total_cost_eur": primary["total_cost_eur"],
            "total_clicks": primary["total_clicks"],
            "total_conversions": primary["total_conversions"],
            "cpa_eur": primary["cpa_eur"],
            "avg_ctr_pct": primary["avg_ctr_pct"],
            "avg_cpc_eur": primary["avg_cpc_eur"],
            "conv_rate_pct": primary["conv_rate_pct"],
        }

    return result


# ---------------------------------------------------------------------------
# Top performers
# ---------------------------------------------------------------------------

def _sort_key(item, sort_by: str):
    mapping = {
        "cost": item.cost,
        "conversions": item.conversions,
        "clicks": item.clicks,
        "ctr": item.ctr,
    }
    return mapping.get(sort_by, item.cost)


def get_top_campaigns(data: AdsData, sort_by: str = "cost", limit: int = 20) -> dict:
    sorted_items = sorted(data.campaigns, key=lambda i: _sort_key(i, sort_by), reverse=True)
    return {
        "sort_by": sort_by,
        "campaigns": [
            {
                "campaign": c.campaign,
                "clicks": c.clicks,
                "impressions": c.impressions,
                "ctr_pct": c.ctr,
                "avg_cpc_eur": round(c.avg_cpc, 2),
                "cost_eur": round(c.cost, 2),
                "conversions": c.conversions,
                "conv_rate_pct": c.conv_rate,
                "cpa_eur": round(c.cost_per_conv, 2),
            }
            for c in sorted_items[:limit]
        ],
    }


def get_top_ad_groups(data: AdsData, sort_by: str = "cost", limit: int = 25) -> dict:
    sorted_items = sorted(data.ad_groups, key=lambda i: _sort_key(i, sort_by), reverse=True)
    return {
        "sort_by": sort_by,
        "ad_groups": [
            {
                "campaign": a.campaign,
                "ad_group": a.ad_group,
                "clicks": a.clicks,
                "impressions": a.impressions,
                "ctr_pct": a.ctr,
                "avg_cpc_eur": round(a.avg_cpc, 2),
                "cost_eur": round(a.cost, 2),
                "conversions": a.conversions,
                "conv_rate_pct": a.conv_rate,
                "cpa_eur": round(a.cost_per_conv, 2),
            }
            for a in sorted_items[:limit]
        ],
    }


def get_top_keywords(data: AdsData, sort_by: str = "conversions", limit: int = 30) -> dict:
    sorted_items = sorted(data.keywords, key=lambda i: _sort_key(i, sort_by), reverse=True)
    return {
        "sort_by": sort_by,
        "keywords": [
            {
                "keyword": k.keyword,
                "match_type": k.match_type,
                "campaign": k.campaign,
                "ad_group": k.ad_group,
                "clicks": k.clicks,
                "impressions": k.impressions,
                "ctr_pct": k.ctr,
                "avg_cpc_eur": round(k.avg_cpc, 2),
                "cost_eur": round(k.cost, 2),
                "conversions": k.conversions,
                "conv_rate_pct": k.conv_rate,
                "cpa_eur": round(k.cost_per_conv, 2),
                "quality_score": k.quality_score if k.quality_score else "n.v.t.",
            }
            for k in sorted_items[:limit]
        ],
    }


def get_top_search_terms(data: AdsData, sort_by: str = "cost", limit: int = 50) -> dict:
    if not data.search_terms:
        return {"error": "Geen zoektermdata beschikbaar. Exporteer het zoekterm-rapport vanuit Google Ads."}
    sorted_items = sorted(data.search_terms, key=lambda i: _sort_key(i, sort_by), reverse=True)
    return {
        "sort_by": sort_by,
        "search_terms": [
            {
                "search_term": s.search_term,
                "matched_keyword": s.keyword,
                "match_type": s.match_type,
                "campaign": s.campaign,
                "ad_group": s.ad_group,
                "clicks": s.clicks,
                "impressions": s.impressions,
                "ctr_pct": s.ctr,
                "avg_cpc_eur": round(s.avg_cpc, 2),
                "cost_eur": round(s.cost, 2),
                "conversions": s.conversions,
                "conv_rate_pct": s.conv_rate,
                "cpa_eur": round(s.cost_per_conv, 2),
            }
            for s in sorted_items[:limit]
        ],
    }


# ---------------------------------------------------------------------------
# Verspild budget
# ---------------------------------------------------------------------------

def get_wasted_spend(
    data: AdsData,
    min_cost: float = 50.0,
    max_conversions: float = 0.0,
    limit: int = 20,
) -> dict:
    """
    Identificeert elementen met significant budget maar (bijna) geen conversies.
    Dit is het meest directe besparingspotentieel.
    """
    def _filter(items, name_attr: str):
        wasted = [
            i for i in items
            if i.cost >= min_cost and i.conversions <= max_conversions
        ]
        wasted.sort(key=lambda i: i.cost, reverse=True)
        return [
            {
                name_attr: getattr(i, name_attr),
                "cost_eur": round(i.cost, 2),
                "clicks": i.clicks,
                "conversions": i.conversions,
                "ctr_pct": i.ctr,
            }
            for i in wasted[:limit]
        ]

    result = {
        "filter": {"min_cost_eur": min_cost, "max_conversions": max_conversions},
    }

    campaign_wasted = _filter(data.campaigns, "campaign")
    ag_wasted = _filter(data.ad_groups, "ad_group")
    kw_wasted = _filter(data.keywords, "keyword")

    if campaign_wasted:
        result["wasted_campaigns"] = campaign_wasted
        result["wasted_campaigns_total_eur"] = round(sum(i["cost_eur"] for i in campaign_wasted), 2)
    if ag_wasted:
        result["wasted_ad_groups"] = ag_wasted
        result["wasted_ad_groups_total_eur"] = round(sum(i["cost_eur"] for i in ag_wasted), 2)
    if kw_wasted:
        result["wasted_keywords"] = kw_wasted
        result["wasted_keywords_total_eur"] = round(sum(i["cost_eur"] for i in kw_wasted), 2)

    if not campaign_wasted and not ag_wasted and not kw_wasted:
        result["message"] = f"Geen elementen gevonden met kosten ≥ €{min_cost} en ≤ {max_conversions} conversies."

    return result


# ---------------------------------------------------------------------------
# Kwaliteitsscore-analyse
# ---------------------------------------------------------------------------

def get_quality_score_analysis(
    data: AdsData,
    max_qs: int = 6,
    min_impressions: int = 10,
    limit: int = 30,
) -> dict:
    """
    Analyseert kwaliteitsscores van zoekwoorden.
    Lage QS verhoogt CPC en verlaagt ad rank.
    """
    keywords_with_qs = [k for k in data.keywords if k.quality_score > 0]

    if not keywords_with_qs:
        return {"error": "Geen kwaliteitsscores beschikbaar. Voeg de kolom 'Kwaliteitsscore' toe aan je zoekwoordexport."}

    # Verdeling over buckets
    distribution = {"1-3 (kritiek)": 0, "4-6 (gemiddeld)": 0, "7-10 (goed)": 0}
    for k in keywords_with_qs:
        if k.quality_score <= 3:
            distribution["1-3 (kritiek)"] += 1
        elif k.quality_score <= 6:
            distribution["4-6 (gemiddeld)"] += 1
        else:
            distribution["7-10 (goed)"] += 1

    low_qs = [
        k for k in keywords_with_qs
        if k.quality_score <= max_qs and k.impressions >= min_impressions
    ]
    low_qs.sort(key=lambda k: (k.quality_score, -k.cost))

    avg_qs = round(sum(k.quality_score for k in keywords_with_qs) / len(keywords_with_qs), 1)

    return {
        "filter": {"max_qs": max_qs, "min_impressions": min_impressions},
        "total_keywords_with_qs": len(keywords_with_qs),
        "avg_quality_score": avg_qs,
        "distribution": distribution,
        "low_quality_score_keywords": [
            {
                "keyword": k.keyword,
                "match_type": k.match_type,
                "campaign": k.campaign,
                "ad_group": k.ad_group,
                "quality_score": k.quality_score,
                "impressions": k.impressions,
                "clicks": k.clicks,
                "cost_eur": round(k.cost, 2),
                "avg_cpc_eur": round(k.avg_cpc, 2),
            }
            for k in low_qs[:limit]
        ],
    }


# ---------------------------------------------------------------------------
# CTR-analyse
# ---------------------------------------------------------------------------

def get_ctr_analysis(
    data: AdsData,
    min_impressions: int = 100,
    max_ctr_pct: float = 2.0,
    limit: int = 20,
) -> dict:
    """
    CTR-analyse: elementen met veel vertoningen maar lage CTR.
    Lage CTR duidt op slechte advertentierelevantie of verkeerde match type.
    """
    def _low_ctr(items, name_attr: str):
        filtered = [
            i for i in items
            if i.impressions >= min_impressions and i.ctr <= max_ctr_pct
        ]
        filtered.sort(key=lambda i: i.impressions, reverse=True)
        return [
            {
                name_attr: getattr(i, name_attr),
                "impressions": i.impressions,
                "clicks": i.clicks,
                "ctr_pct": i.ctr,
                "cost_eur": round(i.cost, 2),
            }
            for i in filtered[:limit]
        ]

    result = {"filter": {"min_impressions": min_impressions, "max_ctr_pct": max_ctr_pct}}

    campaign_low = _low_ctr(data.campaigns, "campaign")
    ag_low = _low_ctr(data.ad_groups, "ad_group")
    kw_low = _low_ctr(data.keywords, "keyword")

    if campaign_low:
        result["low_ctr_campaigns"] = campaign_low
    if ag_low:
        result["low_ctr_ad_groups"] = ag_low
    if kw_low:
        result["low_ctr_keywords"] = kw_low

    return result


# ---------------------------------------------------------------------------
# Conversie-analyse
# ---------------------------------------------------------------------------

def get_conversion_analysis(
    data: AdsData,
    min_clicks: int = 20,
    limit: int = 20,
) -> dict:
    """
    Conversieratio-analyse per niveau.
    Identificeert best en slechtst converterende elementen.
    """
    def _conv_stats(items, name_attr: str):
        filtered = [i for i in items if i.clicks >= min_clicks]
        if not filtered:
            return None

        avg_conv_rate = (
            sum(i.conv_rate for i in filtered) / len(filtered)
            if filtered else 0.0
        )

        # Berekende gemiddelde CPA
        total_cost = sum(i.cost for i in filtered)
        total_conv = sum(i.conversions for i in filtered)
        avg_cpa = round(total_cost / total_conv, 2) if total_conv else 0.0

        # Sorteren op conv_rate (best converterend)
        best = sorted(filtered, key=lambda i: i.conv_rate, reverse=True)
        worst = sorted(
            [i for i in filtered if i.conversions == 0 or i.conv_rate < avg_conv_rate / 2],
            key=lambda i: i.cost,
            reverse=True,
        )

        def _row(i):
            return {
                name_attr: getattr(i, name_attr),
                "clicks": i.clicks,
                "conversions": i.conversions,
                "conv_rate_pct": i.conv_rate,
                "cost_eur": round(i.cost, 2),
                "cpa_eur": round(i.cost_per_conv, 2),
            }

        return {
            "avg_conv_rate_pct": round(avg_conv_rate, 2),
            "avg_cpa_eur": avg_cpa,
            "best_converting": [_row(i) for i in best[:limit]],
            "worst_converting_or_zero": [_row(i) for i in worst[:limit]],
        }

    result = {"filter": {"min_clicks": min_clicks}}

    for items, key, attr in [
        (data.campaigns, "campaigns", "campaign"),
        (data.ad_groups, "ad_groups", "ad_group"),
        (data.keywords, "keywords", "keyword"),
    ]:
        stats = _conv_stats(items, attr)
        if stats:
            result[key] = stats

    return result


# ---------------------------------------------------------------------------
# Zoekterm-kansen
# ---------------------------------------------------------------------------

def get_search_term_opportunities(
    data: AdsData,
    min_clicks: int = 5,
    limit: int = 25,
) -> dict:
    """
    Zoektermen met goede prestaties (conversies of hoge CTR) die nog niet als
    exact zoekwoord zijn toegevoegd. Direct toevoegen geeft meer controle en
    kan CPC verlagen.
    """
    if not data.search_terms:
        return {"error": "Geen zoektermdata beschikbaar."}

    # Bestaande exacte zoekwoorden als referentie
    exact_keywords = {
        k.keyword.lower().strip("[]")
        for k in data.keywords
        if k.match_type.lower() in ("exact", "exacte overeenkomst", "[exact]")
    }

    opportunities = []
    for s in data.search_terms:
        if s.clicks < min_clicks:
            continue
        term_clean = s.search_term.lower().strip()
        if term_clean not in exact_keywords:
            opportunities.append(s)

    # Sorteer: zoektermen met conversies eerst, dan op klikken
    opportunities.sort(key=lambda s: (s.conversions, s.clicks), reverse=True)

    return {
        "filter": {"min_clicks": min_clicks},
        "note": (
            "Dit zijn zoektermen die je advertenties triggeren maar nog niet als exact zoekwoord zijn toegevoegd. "
            "Zoektermen met conversies zijn directe prioriteit."
        ),
        "opportunities": [
            {
                "search_term": s.search_term,
                "matched_keyword": s.keyword,
                "campaign": s.campaign,
                "ad_group": s.ad_group,
                "clicks": s.clicks,
                "conversions": s.conversions,
                "conv_rate_pct": s.conv_rate,
                "cost_eur": round(s.cost, 2),
                "cpa_eur": round(s.cost_per_conv, 2) if s.conversions else None,
                "recommendation": "Toevoegen als exact zoekwoord" if s.conversions > 0 else "Overwegen als exact zoekwoord",
            }
            for s in opportunities[:limit]
        ],
    }


# ---------------------------------------------------------------------------
# Uitsluitingszoekwoord-kandidaten
# ---------------------------------------------------------------------------

def get_negative_keyword_candidates(
    data: AdsData,
    min_cost: float = 10.0,
    limit: int = 30,
) -> dict:
    """
    Zoektermen met significant budget maar nul conversies.
    Dit zijn kandidaten voor uitsluitingszoekwoorden.
    """
    if not data.search_terms:
        return {"error": "Geen zoektermdata beschikbaar."}

    candidates = [
        s for s in data.search_terms
        if s.cost >= min_cost and s.conversions == 0
    ]
    candidates.sort(key=lambda s: s.cost, reverse=True)

    total_wasted = round(sum(s.cost for s in candidates), 2)

    return {
        "filter": {"min_cost_eur": min_cost, "conversions": 0},
        "total_wasted_on_candidates_eur": total_wasted,
        "candidate_count": len(candidates),
        "note": (
            "Controleer handmatig of deze zoektermen irrelevant zijn voordat je ze uitsluit. "
            "Sommige kunnen relevant zijn maar nog te weinig data hebben."
        ),
        "negative_keyword_candidates": [
            {
                "search_term": s.search_term,
                "matched_keyword": s.keyword,
                "campaign": s.campaign,
                "ad_group": s.ad_group,
                "clicks": s.clicks,
                "cost_eur": round(s.cost, 2),
                "impressions": s.impressions,
                "ctr_pct": s.ctr,
            }
            for s in candidates[:limit]
        ],
    }


# ---------------------------------------------------------------------------
# Budget-analyse
# ---------------------------------------------------------------------------

def get_budget_analysis(data: AdsData, limit: int = 20) -> dict:
    """
    Analyseert budgetuitputting per campagne.
    Vereist dat budget-kolom aanwezig is in de export.
    """
    campaigns_with_budget = [c for c in data.campaigns if c.budget > 0]

    if not campaigns_with_budget:
        return {
            "note": "Geen budgetdata beschikbaar. Voeg de kolom 'Dagelijks budget' toe aan je campagne-export.",
            "total_campaigns": len(data.campaigns),
        }

    result = []
    for c in campaigns_with_budget:
        utilization = round(c.cost / c.budget * 100, 1) if c.budget else 0.0
        result.append({
            "campaign": c.campaign,
            "daily_budget_eur": round(c.budget, 2),
            "cost_eur": round(c.cost, 2),
            "budget_utilization_pct": utilization,
            "status": (
                "Budget gelimiteerd (>95%)" if utilization > 95
                else "Onderbenut (<50%)" if utilization < 50
                else "Normaal"
            ),
            "conversions": c.conversions,
            "cpa_eur": round(c.cost_per_conv, 2),
        })

    result.sort(key=lambda x: x["budget_utilization_pct"], reverse=True)

    budget_limited = [r for r in result if r["budget_utilization_pct"] > 95]
    underutilized = [r for r in result if r["budget_utilization_pct"] < 50]

    return {
        "all_campaigns": result[:limit],
        "budget_limited_campaigns": budget_limited,
        "underutilized_campaigns": underutilized,
        "note": (
            "Budgetgelimiteerde campagnes met conversies missen omzet — overweeg budgetverhoging. "
            "Sterk onderbenutte campagnes zonder conversies zijn kandidaat voor pauze."
        ),
    }


# ---------------------------------------------------------------------------
# Periodeanalyse
# ---------------------------------------------------------------------------

def compare_periods(data1: AdsData, data2: AdsData, limit: int = 20) -> dict:
    """
    Vergelijkt twee tijdsperiodes op campagne-, advertentiegroep- en zoekwoordniveau.
    data1 = basisperiode (ouder), data2 = vergelijkingsperiode (nieuwer).
    """
    result: dict = {}

    def _totals(items):
        if not items:
            return None
        total_cost = sum(i.cost for i in items)
        total_clicks = sum(i.clicks for i in items)
        total_conv = sum(i.conversions for i in items)
        avg_ctr = round(total_clicks / sum(i.impressions for i in items) * 100, 2) if sum(i.impressions for i in items) else 0.0
        avg_cpa = round(total_cost / total_conv, 2) if total_conv else 0.0
        avg_cpc = round(total_cost / total_clicks, 2) if total_clicks else 0.0
        return {
            "clicks": total_clicks,
            "cost_eur": round(total_cost, 2),
            "conversions": round(total_conv, 2),
            "avg_ctr_pct": avg_ctr,
            "cpa_eur": avg_cpa,
            "avg_cpc_eur": avg_cpc,
        }

    def _delta(v2, v1):
        if v1 == 0:
            return None
        return round((v2 - v1) / v1 * 100, 1)

    for segment, key_attr, items1, items2 in [
        ("campaigns", "campaign", data1.campaigns, data2.campaigns),
        ("ad_groups", "ad_group", data1.ad_groups, data2.ad_groups),
        ("keywords", "keyword", data1.keywords, data2.keywords),
    ]:
        t1 = _totals(items1)
        t2 = _totals(items2)
        if not t1 or not t2:
            continue

        result[f"{segment}_totals"] = {
            "period1": t1,
            "period2": t2,
            "delta": {
                "clicks_pct": _delta(t2["clicks"], t1["clicks"]),
                "cost_pct": _delta(t2["cost_eur"], t1["cost_eur"]),
                "conversions_pct": _delta(t2["conversions"], t1["conversions"]),
                "cpa_change_eur": round(t2["cpa_eur"] - t1["cpa_eur"], 2),
                "cpc_change_eur": round(t2["avg_cpc_eur"] - t1["avg_cpc_eur"], 2),
                "ctr_change_pct": round(t2["avg_ctr_pct"] - t1["avg_ctr_pct"], 2),
            },
        }

        map1 = {getattr(i, key_attr): i for i in items1}
        map2 = {getattr(i, key_attr): i for i in items2}
        common = set(map1) & set(map2)
        new_keys = set(map2) - set(map1)
        lost_keys = set(map1) - set(map2)

        movers = []
        for k in common:
            i1, i2 = map1[k], map2[k]
            movers.append({
                key_attr: k,
                "cost_p1": round(i1.cost, 2),
                "cost_p2": round(i2.cost, 2),
                "cost_delta_eur": round(i2.cost - i1.cost, 2),
                "conv_p1": i1.conversions,
                "conv_p2": i2.conversions,
                "conv_delta": round(i2.conversions - i1.conversions, 2),
                "cpa_p1": round(i1.cost_per_conv, 2),
                "cpa_p2": round(i2.cost_per_conv, 2),
            })

        movers.sort(key=lambda x: x["conv_delta"], reverse=True)
        result[f"{segment}_top_risers"] = movers[:limit]
        result[f"{segment}_top_decliners"] = movers[-limit:][::-1]

        new_items = sorted([map2[k] for k in new_keys], key=lambda i: i.cost, reverse=True)
        result[f"{segment}_new_in_period2"] = [
            {key_attr: getattr(i, key_attr), "cost_eur": round(i.cost, 2), "conversions": i.conversions}
            for i in new_items[:limit]
        ]

        lost_items = sorted([map1[k] for k in lost_keys], key=lambda i: i.cost, reverse=True)
        result[f"{segment}_lost_in_period2"] = [
            {key_attr: getattr(i, key_attr), "cost_p1_eur": round(i.cost, 2), "conversions_p1": i.conversions}
            for i in lost_items[:limit]
        ]

    return result
