"""
Search Console Agent — CLI entry point.

Gebruik:
    python -m search_console_agent <bestand.xlsx> [bestand2.csv ...]
    python -m search_console_agent queries.csv pages.csv --focus "waarom daalt ons verkeer?"
    python -m search_console_agent jan.xlsx --vergelijk feb.xlsx
    python -m search_console_agent q1_queries.csv q1_pages.csv --vergelijk q2_queries.csv q2_pages.csv

Ondersteunde bestandstypen:
    .xlsx  — Excel met één of meerdere sheets (queries / pages / gecombineerd)
    .csv   — Enkelvoudige GSC CSV-export

GSC-exportinstructies:
    1. Open Google Search Console > Prestaties
    2. Stel de gewenste datumperiode in (bijv. jan–mrt voor kwartaalvergelijking)
    3. Klik op 'Exporteren' rechtsbovenin
    4. Kies 'Excel (.xlsx)' of 'Kommagescheiden waarden (.csv)'
    5. Herhaal stap 2–4 voor de tweede periode en geef dit mee via --vergelijk
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
        prog="search_console_agent",
        description="Analyseer Google Search Console exportdata met AI.",
    )
    parser.add_argument(
        "files",
        nargs="+",
        metavar="BESTAND",
        help="Een of meerdere GSC exportbestanden (.xlsx of .csv)",
    )
    parser.add_argument(
        "--focus",
        "-f",
        metavar="VRAAG",
        default=None,
        help='Optionele specifieke vraag of aandachtspunt (bijv. "waarom daalt ons verkeer?")',
    )
    parser.add_argument(
        "--vergelijk",
        "-v",
        nargs="+",
        metavar="BESTAND",
        default=None,
        help="Een of meerdere GSC-exportbestanden voor de vergelijkingsperiode (bijv. vorige maand)",
    )
    args = parser.parse_args()

    # Valideer API key
    missing = Config.validate()
    if missing:
        _print(f"[red]Fout: stel de volgende omgevingsvariabelen in: {', '.join(missing)}[/red]")
        _print("Maak een .env bestand aan op basis van .env.example")
        sys.exit(1)

    # Valideer bestanden
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

    # Banner
    file_names = ", ".join(p.name for p in paths)
    if paths2:
        file_names += "  →  " + ", ".join(p.name for p in paths2)
    _print(f"\n[bold cyan]Search Console Agent[/bold cyan] — {file_names}\n")

    # Parseer bestanden
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

    # Toon waarschuwingen
    warnings = validate(data)
    for w in warnings:
        _print(f"[yellow]Waarschuwing periode 1: {w}[/yellow]")
    if data2:
        for w in validate(data2):
            _print(f"[yellow]Waarschuwing periode 2: {w}[/yellow]")

    _print(
        f"Geladen periode 1: [bold]{len(data.queries)}[/bold] zoektermen, "
        f"[bold]{len(data.pages)}[/bold] pagina's, "
        f"[bold]{len(data.query_pages)}[/bold] gecombineerde rijen"
    )
    if data2:
        _print(
            f"Geladen periode 2: [bold]{len(data2.queries)}[/bold] zoektermen, "
            f"[bold]{len(data2.pages)}[/bold] pagina's, "
            f"[bold]{len(data2.query_pages)}[/bold] gecombineerde rijen"
        )
    _print("")

    if not data.queries and not data.pages:
        _print("[red]Geen bruikbare data gevonden. Controleer de kolomnamen in het bestand.[/red]")
        _print(
            "Verwachte kolommen: 'Top queries'/'Query'/'Zoekopdracht', "
            "'Top pages'/'Page'/'Pagina', Clicks, Impressions, CTR, Position"
        )
        sys.exit(1)

    # Analyse uitvoeren
    _print("Analyse uitvoeren...\n", "dim")
    try:
        report = run_analysis(data, focus=args.focus, data2=data2)
    except Exception as exc:
        _print(f"[red]Fout tijdens analyse: {exc}[/red]")
        sys.exit(1)

    # Rapport tonen
    _print_markdown(report)


if __name__ == "__main__":
    main()
