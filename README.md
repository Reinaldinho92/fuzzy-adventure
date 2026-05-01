# 🤖 Search Signals — AI Agents

> Interne AI-agents voor Search Signals, gebouwd op de Anthropic Claude API.  
> Elke agent is zelfstandig inzetbaar en ontworpen voor een specifieke marketingtaak.  
> Een centrale orchestrator coördineert de samenwerking tussen agents.

---

## 📁 Repository structuur

```
search-signals-agents/
│
├── README.md                    # Dit bestand
├── .env.example                 # Voorbeeld omgevingsvariabelen (API keys etc.)
├── requirements.txt             # Python-dependencies (of package.json voor Node)
│
├── core/                        # Gedeelde bouwstenen voor alle agents
│   ├── claude_client.py         # Wrapper rondom de Anthropic API
│   ├── base_agent.py            # Abstract basisklasse voor alle agents
│   └── utils.py                 # Gedeelde hulpfuncties
│
├── orchestrator/                # Manager die agents aanstuurt en koppelt
│   ├── README.md                # Hoe de orchestrator werkt
│   ├── orchestrator.py          # Hoofd-orchestratorlogica
│   └── workflows/               # Voorgedefinieerde multi-agent workflows
│       └── ...
│
├── agents/
│   │
│   ├── google_ads_copywriter/   # Agent: Google Ads Copywriter
│   │   ├── README.md            # Beschrijving, gebruik & voorbeelden
│   │   ├── agent.py             # Agent-implementatie
│   │   ├── prompts.py           # System prompts & instructies
│   │   ├── config.yaml          # Instellingen (taal, tone-of-voice, limieten)
│   │   └── examples/            # Voorbeeldinput/output
│   │       ├── input_example.json
│   │       └── output_example.json
│   │
│   └── _template/               # Startpunt voor nieuwe agents
│       ├── README.md
│       ├── agent.py
│       ├── prompts.py
│       └── config.yaml
│
└── docs/                        # Aanvullende documentatie
    ├── agent-design-guide.md    # Richtlijnen voor het bouwen van nieuwe agents
    └── orchestrator-design.md   # Architectuuroverzicht van de orchestrator
```

---

## 🚀 Agents overzicht

| Agent | Map | Status | Omschrijving |
|---|---|---|---|
| Google Ads Copywriter | `agents/google_ads_copywriter/` | ✅ Actief | Schrijft RSA-advertenties, headlines & descriptions op basis van briefing |
| Orchestrator | `orchestrator/` | 🔜 In ontwikkeling | Coördineert samenwerking tussen agents |

> **Nieuwe agent toevoegen?** Kopieer de `agents/_template/` map en volg de instructies in `docs/agent-design-guide.md`.

---

## ⚙️ Installatie

```bash
# 1. Kloon de repository
git clone https://github.com/search-signals/agents.git
cd agents

# 2. Maak een virtual environment aan (Python)
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 3. Installeer dependencies
pip install -r requirements.txt

# 4. Stel je omgevingsvariabelen in
cp .env.example .env
# Vul je ANTHROPIC_API_KEY in .env in
```

---

## 🔑 Omgevingsvariabelen

Maak een `.env` bestand op basis van `.env.example`:

```env
ANTHROPIC_API_KEY=sk-ant-...
DEFAULT_MODEL=claude-sonnet-4-20250514
```

> ⚠️ Voeg `.env` nooit toe aan versiebeheer. Het staat standaard in `.gitignore`.

---

## 🧠 Architectuur

Elke agent in deze repository:

- Is **zelfstandig inzetbaar** — je kunt een agent aanroepen zonder de rest van het systeem
- Heeft een **eigen system prompt** in `prompts.py`, afgestemd op de specifieke taak
- Heeft een **configuratiebestand** (`config.yaml`) voor taal, tone-of-voice en andere parameters
- Erft van `core/base_agent.py` voor consistentie in logging, foutafhandeling en API-gebruik
- Communiceert via de **Anthropic Claude API** (`claude-sonnet-4-20250514`)

De **orchestrator** (in ontwikkeling) werkt als een manager-agent die:
- Bepaalt welke agents worden ingezet voor een gegeven taak
- Input doorstuurt naar de juiste agents en output samenvoegt
- Multi-step workflows uitvoert waarbij agents van elkaars output gebruikmaken

```
Gebruiker / Systeem
       │
       ▼
  Orchestrator
  ┌────┴────┐
  ▼         ▼
Agent A   Agent B   ...
```

---

## 📋 Bijdragen

1. Maak een nieuwe branch aan: `git checkout -b feature/naam-van-agent`
2. Kopieer `agents/_template/` naar `agents/jouw_agent_naam/`
3. Implementeer de agent en vul de README in
4. Maak een pull request aan met een korte beschrijving

---

## 📄 Licentie

Intern gebruik — Search Signals © 2025. Niet bedoeld voor externe distributie.
