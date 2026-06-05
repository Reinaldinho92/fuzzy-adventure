"""
Google Analytics 4 — Data API client.
Authenticatie via service account JSON.
"""

from __future__ import annotations

from dataclasses import dataclass

from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    DateRange,
    Dimension,
    Metric,
    OrderBy,
    RunReportRequest,
)
from google.oauth2 import service_account


_SCOPES = ["https://www.googleapis.com/auth/analytics.readonly"]


@dataclass
class GA4PageData:
    path: str
    title: str
    sessions: int
    pageviews: int
    bounce_rate: float
    avg_engagement_seconds: float
    conversions: int


def _make_client(service_account_path: str) -> BetaAnalyticsDataClient:
    creds = service_account.Credentials.from_service_account_file(
        service_account_path, scopes=_SCOPES
    )
    return BetaAnalyticsDataClient(credentials=creds)


def _normalise_property_id(property_id: str) -> str:
    if not property_id.startswith("properties/"):
        return f"properties/{property_id}"
    return property_id


def get_page_performance(
    property_id: str,
    service_account_path: str,
    days: int = 90,
    limit: int = 500,
) -> list[GA4PageData]:
    """
    Paginaprestaties gesorteerd op sessies (hoog → laag).

    Args:
        property_id:           GA4 property ID (met of zonder 'properties/')
        service_account_path:  Pad naar service account JSON
        days:                  Analyseperiode in dagen
        limit:                 Max aantal rijen

    Returns:
        Lijst van GA4PageData per pagina
    """
    client = _make_client(service_account_path)
    request = RunReportRequest(
        property=_normalise_property_id(property_id),
        date_ranges=[DateRange(start_date=f"{days}daysAgo", end_date="today")],
        dimensions=[
            Dimension(name="pagePath"),
            Dimension(name="pageTitle"),
        ],
        metrics=[
            Metric(name="sessions"),
            Metric(name="screenPageViews"),
            Metric(name="bounceRate"),
            Metric(name="averageSessionDuration"),
            Metric(name="conversions"),
        ],
        order_bys=[
            OrderBy(metric=OrderBy.MetricOrderBy(metric_name="sessions"), desc=True)
        ],
        limit=limit,
    )

    response = client.run_report(request)
    pages = []
    for row in response.rows:
        dv = row.dimension_values
        mv = row.metric_values
        pages.append(GA4PageData(
            path=dv[0].value,
            title=dv[1].value,
            sessions=int(mv[0].value or 0),
            pageviews=int(mv[1].value or 0),
            bounce_rate=round(float(mv[2].value or 0) * 100, 1),
            avg_engagement_seconds=round(float(mv[3].value or 0), 1),
            conversions=int(float(mv[4].value or 0)),
        ))
    return pages


def get_traffic_overview(
    property_id: str,
    service_account_path: str,
    days: int = 90,
) -> dict:
    """
    Traffic per kanaal (Organic, Direct, Referral, Paid, Social, Email, etc.)

    Returns:
        Dict met 'channels' lijst, 'period_days' en samengevoegde totalen
    """
    client = _make_client(service_account_path)
    request = RunReportRequest(
        property=_normalise_property_id(property_id),
        date_ranges=[DateRange(start_date=f"{days}daysAgo", end_date="today")],
        dimensions=[Dimension(name="sessionDefaultChannelGroup")],
        metrics=[
            Metric(name="sessions"),
            Metric(name="totalUsers"),
            Metric(name="screenPageViews"),
            Metric(name="bounceRate"),
            Metric(name="averageSessionDuration"),
            Metric(name="conversions"),
        ],
        order_bys=[
            OrderBy(metric=OrderBy.MetricOrderBy(metric_name="sessions"), desc=True)
        ],
    )

    response = client.run_report(request)
    channels = []
    total_sessions = 0
    total_users = 0
    total_conversions = 0

    for row in response.rows:
        s = int(row.metric_values[0].value or 0)
        u = int(row.metric_values[1].value or 0)
        c = int(float(row.metric_values[5].value or 0))
        total_sessions += s
        total_users += u
        total_conversions += c
        channels.append({
            "channel": row.dimension_values[0].value,
            "sessions": s,
            "users": u,
            "pageviews": int(row.metric_values[2].value or 0),
            "bounce_rate": round(float(row.metric_values[3].value or 0) * 100, 1),
            "avg_session_duration_s": round(float(row.metric_values[4].value or 0), 1),
            "conversions": c,
        })

    return {
        "period_days": days,
        "total_sessions": total_sessions,
        "total_users": total_users,
        "total_conversions": total_conversions,
        "channels": channels,
    }


def get_landing_page_performance(
    property_id: str,
    service_account_path: str,
    days: int = 90,
    limit: int = 100,
) -> list[dict]:
    """
    Prestaties per landingspagina (eerste pagina van de sessie).

    Returns:
        Lijst van dicts met path, sessions, bounce_rate, conversions
    """
    client = _make_client(service_account_path)
    request = RunReportRequest(
        property=_normalise_property_id(property_id),
        date_ranges=[DateRange(start_date=f"{days}daysAgo", end_date="today")],
        dimensions=[Dimension(name="landingPage")],
        metrics=[
            Metric(name="sessions"),
            Metric(name="bounceRate"),
            Metric(name="averageSessionDuration"),
            Metric(name="conversions"),
            Metric(name="totalUsers"),
        ],
        order_bys=[
            OrderBy(metric=OrderBy.MetricOrderBy(metric_name="sessions"), desc=True)
        ],
        limit=limit,
    )

    response = client.run_report(request)
    result = []
    for row in response.rows:
        result.append({
            "path": row.dimension_values[0].value,
            "sessions": int(row.metric_values[0].value or 0),
            "bounce_rate": round(float(row.metric_values[1].value or 0) * 100, 1),
            "avg_session_duration_s": round(float(row.metric_values[2].value or 0), 1),
            "conversions": int(float(row.metric_values[3].value or 0)),
            "users": int(row.metric_values[4].value or 0),
        })
    return result


def get_device_breakdown(
    property_id: str,
    service_account_path: str,
    days: int = 90,
) -> list[dict]:
    """
    Traffic en conversies uitgesplitst naar apparaattype (desktop / mobile / tablet).
    """
    client = _make_client(service_account_path)
    request = RunReportRequest(
        property=_normalise_property_id(property_id),
        date_ranges=[DateRange(start_date=f"{days}daysAgo", end_date="today")],
        dimensions=[Dimension(name="deviceCategory")],
        metrics=[
            Metric(name="sessions"),
            Metric(name="totalUsers"),
            Metric(name="bounceRate"),
            Metric(name="conversions"),
        ],
        order_bys=[
            OrderBy(metric=OrderBy.MetricOrderBy(metric_name="sessions"), desc=True)
        ],
    )

    response = client.run_report(request)
    result = []
    for row in response.rows:
        result.append({
            "device": row.dimension_values[0].value,
            "sessions": int(row.metric_values[0].value or 0),
            "users": int(row.metric_values[1].value or 0),
            "bounce_rate": round(float(row.metric_values[2].value or 0) * 100, 1),
            "conversions": int(float(row.metric_values[3].value or 0)),
        })
    return result
