"""
Google Ads Analyst Agent — CLI entry point.

Gebruik:
    python -m google_ads_analyst <bestand.xlsx> [bestand2.csv ...]
    python -m google_ads_analyst campagnes.csv zoekwoorden.csv --focus "waarom stijgt onze CPA?"
    python -m google_ads_analyst jan.xlsx --vergelijk feb.xlsx
    python -m google_ads_analyst q1.xlsx q1_zoektermen.csv --vergelijk q2.xlsx q2_zoektermen.csv

Ondersteunde bestandstypen:
    .xlsx  — Excel met één of meerdere sheets (campagnes / advertentiegroepen / zoekwoorden / zoektermen)
    .csv   — Enkelvoudige Google Ads CSV-export

Google Ads exportinstructies:
    1. Open Google Ads > kies het gewenste niveau (Campagnes / Advertentiegroepen / Zoekwoorden / Zoektermen)
    2. Klik op het kolommenpictogram en voeg toe:
       Klikken, Vertoningen, CTR, Gem. CPC, Kosten, Conversies, Conversieratio, Kosten/conversie
       (voeg ook Kwaliteitsscore toe voor het zoekwoordniveau)
    3. Klik op 'Exporteren' (downloadpictogram) > kies Excel (.xlsx) of CSV
    4. Herhaal stap 1–3 voor de vergelijkingsperiode en geef mee via --vergelijk
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

try:
    from rich.console import Console
    _HAS_RICH = True
except ImportError:
    _HAS_RICH = False

from .config import Config
from .tools.excel_parser import parse_files, validate
from .tools.html_renderer import render_html
from .agent import run_analysis


def _print(text: str, style: str = "") -> None:
    if _HAS_RICH:
        console = Console()
        if style:
            console.print(text, style=style)
        else:
            console.print(text)
    else:
        print(text)


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="google_ads_analyst",
        description="Analyseer Google Ads exportdata met AI.",
    )
    parser.add_argument(
        "files",
        nargs="+",
        metavar="BESTAND",
        help="Een of meerdere Google Ads exportbestanden (.xlsx of .csv)",
    )
    parser.add_argument(
        "--focus",
        "-f",
        metavar="VRAAG",
        default=None,
        help='Optionele specifieke vraag of aandachtspunt (bijv. "waarom stijgt onze CPA?")',
    )
    parser.add_argument(
        "--vergelijk",
        "-v",
        nargs="+",
        metavar="BESTAND",
        default=None,
        help="Een of meerdere Google Ads exportbestanden voor de vergelijkingsperiode (bijv. vorige maand)",
    )
    args = parser.parse_args()

    missing = Config.validate()
    if missing:
        _print(f"[red]Fout: stel de volgende omgevingsvariabelen in: {', '.join(missing)}[/red]")
        _print("Maak een .env bestand aan op basis van .env.example")
        sys.exit(1)

    def _validate_paths(file_list):
        result = []
        for f in file_list:
            p = Path(f)
            if not p.exists():
                _print(f"[red]Bestand niet gevonden: {p}[/red]")
                sys.exit(1)
            if p.suffix.lower() not in (".xlsx", ".xls", ".csv"):
                _print(f"[red]Niet-ondersteund bestandstype: {p.suffix}[/red]")
                sys.exit(1)
            result.append(p)
        return result

    paths = _validate_paths(args.files)
    paths2 = _validate_paths(args.vergelijk) if args.vergelijk else []

    file_names = ", ".join(p.name for p in paths)
    if paths2:
        file_names += "  →  " + ", ".join(p.name for p in paths2)
    _print(f"\n[bold cyan]Google Ads Analyst[/bold cyan] — {file_names}\n")

    _print("Bestanden inlezen...", "dim")
    try:
        data = parse_files(paths)
    except Exception as exc:
        _print(f"[red]Fout bij het inlezen van de bestanden: {exc}[/red]")
        sys.exit(1)

    data2 = None
    if paths2:
        try:
            data2 = parse_files(paths2)
        except Exception as exc:
            _print(f"[red]Fout bij het inlezen van de vergelijkingsbestanden: {exc}[/red]")
            sys.exit(1)

    for w in validate(data):
        _print(f"[yellow]Waarschuwing periode 1: {w}[/yellow]")
    if data2:
        for w in validate(data2):
            _print(f"[yellow]Waarschuwing periode 2: {w}[/yellow]")

    _print(
        f"Geladen periode 1: [bold]{len(data.campaigns)}[/bold] campagnes, "
        f"[bold]{len(data.ad_groups)}[/bold] advertentiegroepen, "
        f"[bold]{len(data.keywords)}[/bold] zoekwoorden, "
        f"[bold]{len(data.search_terms)}[/bold] zoektermen"
    )
    if data2:
        _print(
            f"Geladen periode 2: [bold]{len(data2.campaigns)}[/bold] campagnes, "
            f"[bold]{len(data2.ad_groups)}[/bold] advertentiegroepen, "
            f"[bold]{len(data2.keywords)}[/bold] zoekwoorden, "
            f"[bold]{len(data2.search_terms)}[/bold] zoektermen"
        )
    _print("")

    if not data.campaigns and not data.keywords and not data.ad_groups:
        _print("[red]Geen bruikbare data gevonden. Controleer de kolomnamen in het bestand.[/red]")
        _print(
            "Verwachte kolommen: 'Campaign'/'Campagne', 'Ad group'/'Advertentiegroep', "
            "'Keyword'/'Zoekwoord', 'Search term'/'Zoekterm', "
            "Clicks/Klikken, Impressions/Vertoningen, CTR, Cost/Kosten, Conversions/Conversies"
        )
        sys.exit(1)

    _print("Analyse uitvoeren...\n", "dim")
    try:
        sections, tool_results = run_analysis(data, focus=args.focus, data2=data2)
    except Exception as exc:
        _print(f"[red]Fout tijdens analyse: {exc}[/red]")
        sys.exit(1)

    html = render_html(data, tool_results, sections, data2=data2)

    # Sla op als bestand
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"rapport_{timestamp}.html"
    filepath = Path.cwd() / filename
    filepath.write_text(html, encoding="utf-8")
    _print(f"Rapport opgeslagen: {filename}", "dim")

    # Print HTML naar stdout zodat Claude Code het als artifact rendert
    print(html)


if __name__ == "__main__":
    main()
