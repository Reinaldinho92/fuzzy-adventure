"""
Combined Agent (GSC + GA4) — CLI entry point.

Gebruik:
    python -m combined_agent --gsc gsc_export.xlsx --ga4 ga4_export.xlsx
    python -m combined_agent --gsc gsc.xlsx --ga4 ga4.xlsx --focus "waarom converteert organisch verkeer slecht?"

Exportinstructies GSC:
    1. Open Google Search Console > Prestaties
    2. Stel de gewenste datumperiode in
    3. Klik op 'Exporteren' > 'Excel (.xlsx)'

Exportinstructies GA4:
    1. Ga naar Google Analytics > Rapporten
    2. Open rapporten voor pagina's, kanalen, landingspagina's en/of apparaten
    3. Exporteer als Google Spreadsheet of CSV (.xlsx of .csv)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    from rich.console import Console
    from rich.markdown import Markdown
    _HAS_RICH = True
except ImportError:
    _HAS_RICH = False

from .config import Config
from search_console_agent.tools.excel_parser import parse_files as gsc_parse_files, validate as gsc_validate
from ga4_agent.tools.excel_parser import parse_files as ga4_parse_files, validate as ga4_validate
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


def _print_markdown(text: str) -> None:
    if _HAS_RICH:
        Console().print(Markdown(text))
    else:
        print(text)


def _validate_paths(file_list: list[str]) -> list[Path]:
    result = []
    for f in file_list:
        p = Path(f)
        if not p.exists():
            _print(f"[red]Bestand niet gevonden: {p}[/red]")
            sys.exit(1)
        if p.suffix.lower() not in (".xlsx", ".xls", ".csv"):
            _print(f"[red]Niet-ondersteund bestandstype: {p.suffix}. Gebruik .xlsx of .csv[/red]")
            sys.exit(1)
        result.append(p)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="combined_agent",
        description="Analyseer Google Search Console én GA4 exportdata gecombineerd met AI.",
    )
    parser.add_argument(
        "--gsc",
        nargs="+",
        metavar="BESTAND",
        required=True,
        help="Een of meerdere GSC exportbestanden (.xlsx of .csv)",
    )
    parser.add_argument(
        "--ga4",
        nargs="+",
        metavar="BESTAND",
        required=True,
        help="Een of meerdere GA4 exportbestanden (.xlsx of .csv)",
    )
    parser.add_argument(
        "--focus",
        "-f",
        metavar="VRAAG",
        default=None,
        help='Optionele specifieke vraag (bijv. "waarom converteert organisch verkeer slecht?")',
    )
    args = parser.parse_args()

    missing = Config.validate()
    if missing:
        _print(f"[red]Fout: stel de volgende omgevingsvariabelen in: {', '.join(missing)}[/red]")
        _print("Maak een .env bestand aan op basis van .env.example")
        sys.exit(1)

    gsc_paths = _validate_paths(args.gsc)
    ga4_paths = _validate_paths(args.ga4)

    gsc_names = ", ".join(p.name for p in gsc_paths)
    ga4_names = ", ".join(p.name for p in ga4_paths)
    _print(f"\n[bold cyan]Combined Agent[/bold cyan] — GSC: {gsc_names}  |  GA4: {ga4_names}\n")

    _print("Bestanden inlezen...", "dim")
    try:
        gsc_data = gsc_parse_files(gsc_paths)
    except Exception as exc:
        _print(f"[red]Fout bij het inlezen van GSC-bestanden: {exc}[/red]")
        sys.exit(1)

    try:
        ga4_data = ga4_parse_files(ga4_paths)
    except Exception as exc:
        _print(f"[red]Fout bij het inlezen van GA4-bestanden: {exc}[/red]")
        sys.exit(1)

    for w in gsc_validate(gsc_data):
        _print(f"[yellow]GSC waarschuwing: {w}[/yellow]")
    for w in ga4_validate(ga4_data):
        _print(f"[yellow]GA4 waarschuwing: {w}[/yellow]")

    _print(
        f"GSC geladen: [bold]{len(gsc_data.queries)}[/bold] zoektermen, "
        f"[bold]{len(gsc_data.pages)}[/bold] pagina's, "
        f"[bold]{len(gsc_data.query_pages)}[/bold] gecombineerde rijen"
    )
    _print(
        f"GA4 geladen: [bold]{len(ga4_data.pages)}[/bold] pagina's, "
        f"[bold]{len(ga4_data.channels)}[/bold] kanalen, "
        f"[bold]{len(ga4_data.landing_pages)}[/bold] landingspagina's"
    )
    _print("")

    if not gsc_data.queries and not gsc_data.pages:
        _print("[red]Geen bruikbare GSC-data gevonden. Controleer de kolomnamen in het bestand.[/red]")
        sys.exit(1)

    if not ga4_data.pages and not ga4_data.channels:
        _print("[red]Geen bruikbare GA4-data gevonden. Controleer de kolomnamen in het bestand.[/red]")
        sys.exit(1)

    _print("Analyse uitvoeren...\n", "dim")
    try:
        report = run_analysis(gsc_data, ga4_data, focus=args.focus)
    except Exception as exc:
        _print(f"[red]Fout tijdens analyse: {exc}[/red]")
        sys.exit(1)

    _print_markdown(report)


if __name__ == "__main__":
    main()
