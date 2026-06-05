"""
GA4 Agent — CLI entry point.

Gebruik:
    python -m ga4_agent rapport.xlsx
    python -m ga4_agent paginas.xlsx kanalen.csv --focus "waarom daalt ons verkeer?"
    python -m ga4_agent data.xlsx --focus "hoe presteren onze landingspagina's?"

Exportinstructies GA4:
    1. Ga naar Google Analytics > Rapporten
    2. Open het gewenste rapport (bijv. Betrokkenheid > Pagina's en schermen)
    3. Klik rechtsboven op het download-icoon > Download als Google Spreadsheet of CSV
    4. Exporteer eventueel aparte rapporten voor kanalen (Acquisitie > Overzicht) en
       apparaten (Technologie > Overzicht)
    5. Geef alle bestanden mee aan de agent — die detecteert automatisch welke data erin zit

Ondersteunde bestandstypen:
    .xlsx  — Excel met één of meerdere sheets (auto-detect per sheet)
    .csv   — Enkelvoudige GA4 CSV-export
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
from .tools.excel_parser import parse_files, validate
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


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="ga4_agent",
        description="Analyseer Google Analytics 4 exportdata met AI.",
    )
    parser.add_argument(
        "files",
        nargs="+",
        metavar="BESTAND",
        help="Een of meerdere GA4 exportbestanden (.xlsx of .csv)",
    )
    parser.add_argument(
        "--focus",
        "-f",
        metavar="VRAAG",
        default=None,
        help='Optionele specifieke vraag (bijv. "waarom daalt ons verkeer?")',
    )
    args = parser.parse_args()

    # Valideer API key
    missing = Config.validate()
    if missing:
        _print(f"[red]Fout: stel de volgende omgevingsvariabelen in: {', '.join(missing)}[/red]")
        _print("Maak een .env bestand aan op basis van .env.example")
        sys.exit(1)

    # Valideer bestanden
    paths = []
    for f in args.files:
        p = Path(f)
        if not p.exists():
            _print(f"[red]Bestand niet gevonden: {p}[/red]")
            sys.exit(1)
        if p.suffix.lower() not in (".xlsx", ".xls", ".csv"):
            _print(f"[red]Niet-ondersteund bestandstype: {p.suffix}. Gebruik .csv of .xlsx[/red]")
            sys.exit(1)
        paths.append(p)

    file_names = ", ".join(p.name for p in paths)
    _print(f"\n[bold cyan]GA4 Agent[/bold cyan] — {file_names}\n")

    # Parseer bestanden
    _print("Bestanden inlezen...", "dim")
    try:
        data = parse_files(paths)
    except Exception as exc:
        _print(f"[red]Fout bij het inlezen van de bestanden: {exc}[/red]")
        sys.exit(1)

    # Toon waarschuwingen
    for w in validate(data):
        _print(f"[yellow]Waarschuwing: {w}[/yellow]")

    _print(
        f"Geladen: [bold]{len(data.pages)}[/bold] pagina's, "
        f"[bold]{len(data.channels)}[/bold] kanalen, "
        f"[bold]{len(data.landing_pages)}[/bold] landingspagina's, "
        f"[bold]{len(data.devices)}[/bold] apparaten"
    )
    _print("")

    if not data.pages and not data.channels:
        _print("[red]Geen bruikbare data gevonden. Controleer de kolomnamen in het bestand.[/red]")
        _print(
            "Verwachte kolommen (pagina's): 'Page path', 'Sessions', 'Bounce rate', 'Conversions'\n"
            "Verwachte kolommen (kanalen): 'Session default channel group', 'Sessions', 'Conversions'"
        )
        sys.exit(1)

    # Analyse uitvoeren
    _print("Analyse uitvoeren...\n", "dim")
    try:
        report = run_analysis(data, focus=args.focus)
    except Exception as exc:
        _print(f"[red]Fout tijdens analyse: {exc}[/red]")
        sys.exit(1)

    _print_markdown(report)


if __name__ == "__main__":
    main()
