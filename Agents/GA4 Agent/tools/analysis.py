"""
GA4 analysefuncties die als tools beschikbaar zijn voor de agent.

Alle functies ontvangen een GA4Data object (geparsede Excel-export) en retourneren
een serialiseerbaar dict of lijst, klaar voor JSON-output.
"""

from __future__ import annotations

from .excel_parser import GA4Data, ChannelRow, PageRow


# ---------------------------------------------------------------------------
# Analyse functies
# ---------------------------------------------------------------------------

def get_overview(data: GA4Data) -> dict:
    """Totale KPI's en een samenvatting per kanaal op hoofdlijnen."""
    total_sessions = sum(ch.sessions for ch in data.channels)
    total_users = sum(ch.users for ch in data.channels)
    total_conversions = sum(ch.conversions for ch in data.channels)
    conversion_rate = round(total_conversions / total_sessions * 100, 2) if total_sessions else 0.0

    # Fallback: als kanaaldata ontbreekt, tel op uit pagina's
    if not total_sessions and data.pages:
        total_sessions = sum(p.sessions for p in data.pages)
        total_conversions = sum(p.conversions for p in data.pages)
        conversion_rate = round(total_conversions / total_sessions * 100, 2) if total_sessions else 0.0

    channels_summary = [
        {
            "channel": ch.channel,
            "sessions": ch.sessions,
            "sessions_pct": round(ch.sessions / total_sessions * 100, 1) if total_sessions else 0,
            "conversions": ch.conversions,
            "bounce_rate": ch.bounce_rate,
            "avg_session_duration_s": ch.avg_session_duration_s,
        }
        for ch in sorted(data.channels, key=lambda c: c.sessions, reverse=True)
    ]

    return {
        "total_sessions": total_sessions,
        "total_users": total_users,
        "total_conversions": total_conversions,
        "conversion_rate_pct": conversion_rate,
        "total_pages_with_traffic": len(data.pages),
        "total_landing_pages": len(data.landing_pages),
        "channels_available": len(data.channels),
        "devices_available": len(data.devices),
        "channels_summary": channels_summary,
    }


def get_channel_breakdown(data: GA4Data) -> list[dict]:
    """Gedetailleerd overzicht per kanaal inclusief conversieratio."""
    total_sessions = sum(ch.sessions for ch in data.channels)
    result = []
    for ch in sorted(data.channels, key=lambda c: c.sessions, reverse=True):
        s = ch.sessions
        c = ch.conversions
        result.append({
            "channel": ch.channel,
            "sessions": s,
            "sessions_pct": round(s / total_sessions * 100, 1) if total_sessions else 0,
            "users": ch.users,
            "pageviews": ch.pageviews,
            "bounce_rate": ch.bounce_rate,
            "avg_session_duration_s": ch.avg_session_duration_s,
            "conversions": c,
            "conversion_rate_pct": round(c / s * 100, 2) if s else 0,
        })
    return result


def get_top_pages(data: GA4Data, limit: int = 25) -> list[dict]:
    """Beste pagina's gesorteerd op sessies, met engagement en conversiemetrics."""
    sorted_pages = sorted(data.pages, key=lambda p: p.sessions, reverse=True)
    return [
        {
            "path": p.path,
            "title": p.title,
            "sessions": p.sessions,
            "pageviews": p.pageviews,
            "bounce_rate": p.bounce_rate,
            "avg_engagement_seconds": p.avg_engagement_seconds,
            "conversions": p.conversions,
            "conversion_rate_pct": round(p.conversions / p.sessions * 100, 2) if p.sessions else 0,
        }
        for p in sorted_pages[:limit]
    ]


def get_low_engagement_pages(
    data: GA4Data,
    min_sessions: int = 50,
    max_engagement_seconds: float = 30.0,
    limit: int = 20,
) -> list[dict]:
    """
    Pagina's met voldoende traffic maar een lage gemiddelde engagementtijd.
    Kandidaten voor content- of UX-verbetering.
    """
    candidates = [
        p for p in data.pages
        if p.sessions >= min_sessions and p.avg_engagement_seconds <= max_engagement_seconds
    ]
    candidates.sort(key=lambda p: p.sessions, reverse=True)
    return [
        {
            "path": p.path,
            "title": p.title,
            "sessions": p.sessions,
            "avg_engagement_seconds": p.avg_engagement_seconds,
            "bounce_rate": p.bounce_rate,
            "conversions": p.conversions,
        }
        for p in candidates[:limit]
    ]


def get_high_bounce_pages(
    data: GA4Data,
    min_sessions: int = 50,
    bounce_threshold: float = 70.0,
    limit: int = 20,
) -> list[dict]:
    """
    Pagina's met een hoge bounce rate en voldoende traffic.
    Hoge bounce duidt op een mismatch tussen verwachting en content.
    """
    candidates = [
        p for p in data.pages
        if p.sessions >= min_sessions and p.bounce_rate >= bounce_threshold
    ]
    candidates.sort(key=lambda p: p.bounce_rate, reverse=True)
    return [
        {
            "path": p.path,
            "title": p.title,
            "sessions": p.sessions,
            "bounce_rate": p.bounce_rate,
            "avg_engagement_seconds": p.avg_engagement_seconds,
            "conversions": p.conversions,
        }
        for p in candidates[:limit]
    ]


def get_conversion_analysis(
    data: GA4Data,
    min_sessions: int = 20,
    limit: int = 20,
) -> dict:
    """
    Convertiepagina's én pagina's met traffic maar nul conversies.
    Direct inzicht in waar omzet lekt.
    """
    with_conversions = sorted(
        [p for p in data.pages if p.conversions > 0],
        key=lambda p: p.conversions,
        reverse=True,
    )
    zero_conversion = sorted(
        [p for p in data.pages if p.conversions == 0 and p.sessions >= min_sessions],
        key=lambda p: p.sessions,
        reverse=True,
    )

    def _fmt(p: PageRow) -> dict:
        return {
            "path": p.path,
            "title": p.title,
            "sessions": p.sessions,
            "conversions": p.conversions,
            "conversion_rate_pct": round(p.conversions / p.sessions * 100, 2) if p.sessions else 0,
            "avg_engagement_seconds": p.avg_engagement_seconds,
        }

    return {
        "converting_pages": [_fmt(p) for p in with_conversions[:limit]],
        "zero_conversion_pages": [_fmt(p) for p in zero_conversion[:limit]],
        "total_converting_pages": len(with_conversions),
        "total_zero_conversion_pages": len(zero_conversion),
    }


def get_landing_page_analysis(data: GA4Data, limit: int = 25) -> list[dict]:
    """
    Prestaties van landingspagina's (eerste pagina van de sessie).
    Hoge bounce rate hier duidt op een mismatch met de traffic-bron.
    """
    sorted_lp = sorted(data.landing_pages, key=lambda p: p.sessions, reverse=True)
    result = []
    for p in sorted_lp[:limit]:
        s = p.sessions
        c = p.conversions
        result.append({
            "path": p.path,
            "sessions": s,
            "users": p.users,
            "bounce_rate": p.bounce_rate,
            "avg_session_duration_s": p.avg_session_duration_s,
            "conversions": c,
            "conversion_rate_pct": round(c / s * 100, 2) if s else 0,
        })
    return result


def get_device_breakdown(data: GA4Data) -> list[dict]:
    """
    Sessies, gebruikers en conversies uitgesplitst per apparaat.
    Voor B2B is desktop dominant — afwijkingen kunnen duiden op UX-problemen.
    """
    total_sessions = sum(d.sessions for d in data.devices)
    result = []
    for d in sorted(data.devices, key=lambda x: x.sessions, reverse=True):
        s = d.sessions
        c = d.conversions
        result.append({
            "device": d.device,
            "sessions": s,
            "sessions_pct": round(s / total_sessions * 100, 1) if total_sessions else 0,
            "users": d.users,
            "bounce_rate": d.bounce_rate,
            "conversions": c,
            "conversion_rate_pct": round(c / s * 100, 2) if s else 0,
        })
    return result


def get_organic_performance(data: GA4Data) -> dict:
    """
    Isoleer organisch zoekverkeer (Organic Search kanaal) voor SEO-gerichte analyse.
    """
    organic = next(
        (ch for ch in data.channels if "organic" in ch.channel.lower()),
        None,
    )
    total_sessions = sum(ch.sessions for ch in data.channels)

    if not organic:
        return {"error": "Geen 'Organic Search' kanaal gevonden in de data."}

    s = organic.sessions
    return {
        "channel": organic.channel,
        "sessions": s,
        "sessions_pct_of_total": round(s / total_sessions * 100, 1) if total_sessions else 0,
        "users": organic.users,
        "bounce_rate": organic.bounce_rate,
        "avg_session_duration_s": organic.avg_session_duration_s,
        "conversions": organic.conversions,
        "conversion_rate_pct": round(organic.conversions / s * 100, 2) if s else 0,
    }
