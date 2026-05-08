# Search Signals — Agent Repository

> Interne AI-agents die de werkzaamheden van Search Signals ondersteunen.
> Lees voor de volledige context en werkafspraken altijd eerst `CLAUDE.md`.

---

## Agents

| Agent                  | Map                              | Status  |
|------------------------|----------------------------------|---------|
| Orchestrator           | `/agents/orchestrator/`          | gepland |
| Google Ads Copywriter  | `/agents/google-ads-copywriter/` | gepland |
| SEO Copywriter         | `/agents/seo-copywriter/`        | gepland |
| SEO Analyst            | `/agents/seo-analyst/`           | gepland |
| Google Ads Analyst     | `/agents/google-ads-analyst/`    | gepland |
| Asana Planner          | `/agents/asana-planner/`         | gepland |
| Data Analyst           | `/agents/data-analyst/`          | gepland |
| Rapportage Creator     | `/agents/rapportage-creator/`    | gepland |

---

## Structuur

```
/agents/        → één submap per agent, elk met een AGENT.md
/shared/        → gedeelde protocollen, tools en templates
/docs/          → beslissingslog en changelog
CLAUDE.md       → projectdocumentatie en werkafspraken voor Claude Code
```

---

## Nieuwe agent toevoegen

1. Maak een submap aan in `/agents/`
2. Kopieer de `AGENT.md` template uit `/shared/templates/`
3. Vul de template in en voeg de agent toe aan de tabel hierboven
4. Zie `CLAUDE.md` voor verdere werkafspraken

---

Search Signals © 2025 — intern gebruik
