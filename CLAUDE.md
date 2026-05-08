# Search Signals — Agent Repository

## Over ons

Search Signals is een online marketing bureau dat zich richt op het online transformeren en groeien van B2B bedrijven. Wij werken voor B2B bedrijven in de servicebranch: van accountantskantoren en machineproducenten tot product compliance en informatiebeveiliging.

Ons team bestaat uit 4 personen en werkt primair met:
Asana (projectmanagement), Slack (communicatie), Canva (design),
Claude Code (AI-development) en de Google-suite (Ads, Analytics, Search Console).

---

## Doel van deze repository

Deze repository bevat AI-agents die de werkzaamheden van Search Signals ondersteunen.
Elke agent is ontworpen voor een specifieke rol binnen ons bureau.

Agents worden gecoördineerd door de Orchestrator en communiceren via een Claude Project.

Het systeem is opgezet om eenvoudig uitbreidbaar te zijn:
nieuwe agents kunnen worden toegevoegd door een submap aan te maken in `/agents/`
en een bijbehorend `AGENT.md` te vullen volgens de standaard template.

---

## Repo-structuur

```
/agents/
  orchestrator/         → verbindt en coördineert alle agents
  google-ads-copywriter/
  seo-copywriter/
  seo-analyst/
  google-ads-analyst/
  asana-planner/
  data-analyst/
  rapportage-creator/
/shared/
  protocol.md           → communicatieprotocol tussen agents
  tools.md              → gedeelde tools en API-koppelingen
  templates/            → gedeelde output-templates
/docs/
  beslissingslog.md     → waarom keuzes zijn gemaakt
  changelog.md          → wat er per sessie is gewijzigd
CLAUDE.md               → dit bestand — altijd als eerste lezen
```

---

## Werkafspraken voor Claude Code

- Lees altijd eerst dit bestand én de `AGENT.md` van de betreffende agent voordat je iets doet.
- Werk agent-voor-agent. Pas nooit meerdere agents tegelijk aan.
- Maak geen bestanden aan buiten de aangegeven mapstructuur.
- Vraag om expliciete bevestiging voordat je een bestaande agent of gedeeld bestand wijzigt.
- Documenteer elke significante keuze kort in `/docs/beslissingslog.md`.
- Houd agents modulair: een agent mag geen logica bevatten die thuishoort in een andere agent.

---

## Agent-overzicht

| Agent                  | Rol                                                        | Primaire gebruiker    | Status  |
|------------------------|------------------------------------------------------------|-----------------------|---------|
| Orchestrator           | Coördineert alle agents, bepaalt volgorde en dataflow      | Heel team             | gepland |
| Google Ads Copywriter  | Schrijft advertentieteksten voor Google Ads campagnes      | Ads specialist        | gepland |
| SEO Copywriter         | Schrijft SEO-geoptimaliseerde content voor klanten         | SEO specialist        | gepland |
| SEO Analyst            | Analyseert rankings, zoekwoorden en SEO-prestaties         | SEO specialist        | gepland |
| Google Ads Analyst     | Analyseert campagneprestaties en geeft optimalisatieadvies | Ads specialist        | gepland |
| Asana Planner          | Maakt maandelijkse takenplanning aan in Asana              | Heel team             | gepland |
| Data Analyst           | Verwerkt en interpreteert marketingdata van klanten        | Strateeg / analist    | gepland |
| Rapportage Creator     | Genereert klantrapportages op basis van data en analyses   | Accountmanager / team | gepland |

> Om een nieuwe agent toe te voegen: maak een submap aan in `/agents/`, kopieer de `AGENT.md`
> template uit `/shared/templates/` en vul deze in. Voeg de agent toe aan bovenstaande tabel.

---

## Communicatie tussen agents

Agents communiceren via een Claude Project. De Orchestrator is het centrale punt:
hij ontvangt een opdracht, bepaalt welke agents nodig zijn, geeft ze context mee
en verwerkt hun output tot een samenhangend resultaat.

De details van dit protocol worden uitgewerkt in `/shared/protocol.md` zodra
de eerste agents operationeel zijn.

---

## Status van dit systeem

Dit systeem is in actieve ontwikkeling. Agents worden één voor één uitgewerkt en getest
voordat de volgende wordt aangemaakt. De Orchestrator wordt als laatste volledig ingericht,
nadat alle individuele agents een stabiele skillset hebben.
