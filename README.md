# 🤖 Search Signals — AI Agents

> Interne AI-agents voor Search Signals, aangestuurd via Claude Projects.  
> GitHub dient als de centrale kennisbasis: alle prompts, instructies en configuraties leven hier.  
> Claude leest deze bestanden als context en voert taken uit via het bijbehorende Project.

---

## 💡 Hoe het werkt

```
GitHub (backbone)                  Claude Project (werkplek)
─────────────────                  ──────────────────────────
prompts.md          ──────────▶    Projectkennis / MCP-sync
config.md           ──────────▶    Projectinstructies
examples/           ──────────▶    Few-shot voorbeelden
                                          │
                                          ▼
                                   Jij geeft input
                                          │
                                          ▼
                                   Claude levert output
```

**GitHub = de hersenen.** Prompts, gedragsregels en voorbeelden staan hier.  
**Claude Project = de werkplek.** Hier geef je input en ontvang je output.  
**Aanpassingen** doe je altijd in GitHub — nooit direct in Claude.

---

## 🔗 GitHub koppelen aan Claude Projects

Je hebt twee opties om GitHub-bestanden beschikbaar te maken in een Claude Project:

### Optie 1 — Handmatig uploaden *(simpelst, nu al mogelijk)*
1. Open het Claude Project van de betreffende agent
2. Upload de relevante bestanden (`prompts.md`, `config.md`, `examples/`) als projectkennis
3. Herhaal dit wanneer bestanden in GitHub worden aangepast

### Optie 2 — GitHub MCP-integratie *(aanbevolen voor structureel gebruik)*
1. Verbind GitHub als MCP-server aan Claude via de integratie-instellingen in Claude.ai
2. Claude leest automatisch de laatste versie van bestanden uit de repository
3. Wijzigingen in GitHub zijn direct beschikbaar in het Project — zonder opnieuw uploaden

> **Aanbeveling:** Start met Optie 1 om snel te testen. Schakel over naar Optie 2 zodra je de agents structureel gaat gebruiken.

---

## 📁 Repository structuur

```
search-signals-agents/
│
├── README.md                          # Dit bestand
│
├── agents/
│   │
│   ├── google_ads_copywriter/         # Agent: Google Ads Copywriter
│   │   ├── README.md                  # Wat deze agent doet & hoe je hem gebruikt
│   │   ├── prompts.md                 # System prompt — plak dit in de projectinstructies
│   │   ├── config.md                  # Tone-of-voice, taal, tekenlimieten, doelgroepen
│   │   └── examples/                  # Few-shot voorbeelden voor betere output
│   │       ├── example_01.md          # Voorbeeld: input briefing → output advertenties
│   │       └── example_02.md
│   │
│   └── _template/                     # Startpunt voor nieuwe agents
│       ├── README.md
│       ├── prompts.md
│       └── config.md
│
└── orchestrator/                      # Manager-agent (in ontwikkeling)
    ├── README.md
    └── prompts.md                     # Instructies voor het aansturen van meerdere agents
```

---

## 🚀 Agents overzicht

| Agent | Map | Status | Omschrijving |
|---|---|---|---|
| Google Ads Copywriter | `agents/google_ads_copywriter/` | ✅ Actief | Schrijft RSA-advertenties op basis van een briefing |
| Orchestrator | `orchestrator/` | 🔜 In ontwikkeling | Coördineert samenwerking tussen agents |

---

## ➕ Nieuwe agent toevoegen

1. Kopieer `agents/_template/` naar `agents/naam_van_agent/`
2. Vul `prompts.md` in met de system prompt voor deze agent
3. Beschrijf tone-of-voice en parameters in `config.md`
4. Voeg voorbeelden toe in de `examples/` map
5. Maak een nieuw Claude Project aan en laad de bestanden in als projectkennis
6. Werk de tabel hierboven bij

---

## 📋 Werkinstructies per agent

Elke agentmap bevat een eigen `README.md` met:
- Wat de agent doet
- Welke input je aanlevert
- Hoe je het Claude Project instelt
- Voorbeelden van gebruik

---

## 📄 Licentie

Intern gebruik — Search Signals © 2025. Niet bedoeld voor externe distributie.
