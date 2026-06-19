# Beslissingslog — Search Signals Agent Repository

---

## 2026-06-19 — Google Ads Analyst: HTML-generatie naar Claude verplaatst

**Probleem:**
De agent had een gebroken dataflow. `agent/__init__.py` bevatte tegenstrijdige output-instructies:
één sectie instrueerde Claude om JSON terug te geven (`sections`-lijst), een andere sectie
instrueerde Claude om HTML te genereren. De code volgde de JSON-instructie: `run_analysis()`
parsete het antwoord met `json.loads()` en gaf `(sections, tool_results)` terug.
`tools/html_renderer.py` bouwde de HTML vervolgens via een vaste Python-template.
De HTML-instructies in de prompt waren dode code. Bovendien verwees de prompt naar
`RAPPORT_OUTPUT_PROMPT.md` — een bestand dat niet bestond.

**Beslissing:**
Claude wordt de baas over de HTML-output. De analyse-engine (`analysis.py`, alle tools)
blijft ongewijzigd — alle cijfers blijven uit de tool-resultaten komen. Wat verandert:

1. **`RAPPORT_OUTPUT_PROMPT.md` aangemaakt** in `google_ads_analyst/` — de enige bron van
   waarheid voor visuele opmaak: CSS (samengevoegd uit html_renderer.py en de systeemprompt),
   HTML-skelet, componentstijlen (badges, alerts, tabellen, bullets, Chart.js setup),
   gegevenspopulatieregels en sectie-overzicht.

2. **`agent/__init__.py` aangepast:**
   - `RAPPORT_OUTPUT_PROMPT.md` wordt op moduleniveau ingeladen via `pathlib` en toegevoegd
     aan de systeemprompt.
   - JSON-outputformaat en dubbele HTML-instructies verwijderd uit de systeemprompt.
   - `run_analysis()` geeft nu `str` (HTML) terug in plaats van `tuple[list[dict], dict[str, str]]`.
   - Eindantwoord: tekst-blokken samenvoegen, code fences strippen, HTML-string teruggeven.
   - `tool_results_store` verwijderd (was alleen nodig voor html_renderer).

3. **`__main__.py` aangepast:**
   - Import van `render_html` verwijderd.
   - `html = run_analysis(...)` direct gebruikt; geen tussenliggende renderer meer.

4. **`tools/html_renderer.py` verwijderd** — CSS en structuur zijn overgedragen naar
   `RAPPORT_OUTPUT_PROMPT.md`.

5. **`AGENT.md` bijgewerkt:** bestandsstructuur, rapportstructuur en dataflow beschrijven
   de nieuwe situatie.

**Afweging:**
Door Claude de HTML te laten genereren, verdwijnt de rigide sectie-volgorde van de Python-renderer
en kan Claude secties weglaten of toevoegen op basis van de daadwerkelijk beschikbare data.
De keerzijde is dat de visuele output minder deterministisch is. Dit is bewust geaccepteerd:
de vaste CSS in `RAPPORT_OUTPUT_PROMPT.md` borgt de look-and-feel, terwijl Claude kan variëren
in welke secties het meeste inzicht bieden voor de specifieke dataset.
