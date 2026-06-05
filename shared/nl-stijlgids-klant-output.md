# Nederlandse stijlgids voor klant-output

Concrete anti-AI-tells-regels voor klant-output van het Marketing OS.
Doel: documenten voelen alsof een strategisch teamlid van Search Signals ze geschreven heeft, niet alsof een LLM ze gegenereerd heeft.

Niet: abstract tone-of-voice — dat staat in `docs/bureau/dna.md` (direct, scherp, geen #bullshitbingo).
Wel: patronen-te-vermijden + alternatieve formuleringen.

**Geldt voor:** alle klant-output-secties van strategie-sub-agents en is leidraad voor de redacteur.
**Interne secties** (Dunford-onderbouwing, sanity-flags, verificatie-lijst, log-secties) mogen pragmatischer — daar gelden deze regels minder strikt.

---

## Regel 1 — Em-dash (—) sparen

Em-dashes met spaties (—) zijn de duidelijkste AI-tell in Nederlandse tekst. Native NL gebruikt komma, dubbele punt, punt of haakjes.

**Wel toegestaan:**
- Em-dash na een titel of label, gevolgd door uitleg: `**Naam** — functie` of `Persona A — uitleg`. Dit is een Nederlandse opsomming-conventie.
- Em-dash in een bullet-item dat een label + uitleg toont.

**Niet toegestaan:**
- Em-dash midden in lopende zinnen als parenthetisch: ~~"Sigma — een accountantskantoor — werkt al sinds 1998"~~
- Dubbele em-dash voor onderbreking binnen één zin.

| Zo niet | Zo wel |
|---|---|
| Sigma — een accountantskantoor — werkt al sinds 1998. | Sigma, een accountantskantoor, werkt al sinds 1998. of: Sigma (een accountantskantoor) werkt al sinds 1998. |
| Onze klanten weten wat ze willen — geen leverancier, wel een partner. | Onze klanten weten wat ze willen: geen leverancier, wel een partner. |
| Bas pakt het op — Anouk levert input — Mark zorgt voor planning. | Bas pakt het op. Anouk levert input. Mark zorgt voor planning. |

---

## Regel 2 — "Niet X — wel Y" parallelisme spaarzaam

Het patroon `Niet [iets] — wel [iets anders]` of `Geen [X], maar [Y]` is bruikbaar maar wordt door LLM's overgebruikt als ritmisch refrein. Max één keer per document of klant-paragraaf.

| Zo niet | Zo wel |
|---|---|
| Wij zijn geen leverancier, maar een partner. Geen pitch-show, maar een gesprek. Geen wisselende juniors, maar een vast aanspreekpunt. | Wij zien onszelf als partner, niet als leverancier. Geen pitch-show: een open gesprek werkt beter. Klanten praten altijd met dezelfde senior. |

Het probleem zit in de stapeling. Eén keer mag, drie keer is een refrein dat onnatuurlijk leest.

---

## Regel 3 — Geen TL;DR in klant-output

`## TL;DR` is interne werkstructuur. In een klant-deliverable past het niet — het signaleert "dit is door een agent gestructureerd".

**Wel in:** interne brein-bestanden, agent-output naar `_inbox/`, redacteur-logs.
**Niet in:** waardepropositie-slide, persona-slide, ICP-slide, audit-rapport voor klant.

Als samenvatting nodig is in klant-output: zet die als eerste paragraaf in lopende tekst, zonder kop.

---

## Regel 4 — Geen "Concreet:" / "Belangrijk:" / "Let op:" als signaalwoorden

Deze openingswoorden voelen behulpzaam maar dragen een LLM-stempel. Lopende tekst hoort zonder labels te functioneren — als de zin belangrijk is, blijkt dat uit de inhoud.

| Zo niet | Zo wel |
|---|---|
| Belangrijk: wij werken nooit met externe investeerders. | Wij werken nooit met externe investeerders. |
| Concreet: vanaf maand één bouwen we de finance-stack mee. | Vanaf maand één bouwen we de finance-stack mee. |

**Uitzondering:** in zakelijke instructie-secties (workshop-instructies, klant-handelingen) zijn `Let op:`-signalen wél functioneel.

---

## Regel 5 — Geforceerde drie-puntje-opsommingen vermijden

LLM's zetten standaard drie items achter elkaar — vaak omdat dat ritmisch lijkt. Varieer: twee mag, vier mag, soms één goed gekozen voorbeeld is sterker.

**Zo niet:**
- "Wij doen WBSO, ESOP en international tax."
- "Klanten zoeken duidelijkheid, snelheid en zekerheid."

**Zo wel:**
- "Wij doen WBSO en international tax — vrijwel overal in NL moet één van die twee uitbesteed worden, bij ons niet."
- "Klanten zoeken duidelijkheid. Snelheid komt op de tweede plaats; zekerheid spreekt vanzelf."

---

## Regel 6 — Geen vetgedrukte tussenkoppen in lopend verhaal

Hinge-stijl is lopende tekst. Vetgedrukte tussenkoppen breken de leesflow en signaleren AI-structurering.

**Wel toegestaan:**
- Markdown-koppen (`##`, `###`) als sectie-scheiding tussen onderdelen.
- Vetgedrukte labels in tabellen of bullets (`**Label:** uitleg`).

**Niet toegestaan:**
- Vetgedrukte zin midden in een paragraaf om het "belangrijke punt" te markeren.

---

## Regel 7 — Varieer zinslengte

LLM-tekst valt vaak in twee modi: alles middellange zinnen, of staccato-korte zinnen als ritme. Beide voelen onnatuurlijk.

**Zo niet:**
Sigma werkt voor tech-scale-ups. Wij kennen het bedrijfsmodel. Onboarding kost twee weken. Geen wisselende juniors. Vaste partner. Duidelijke afspraken.

**Zo wel:**
Sigma werkt voor tech-scale-ups. We kennen het bedrijfsmodel doordat we al 8 jaar in deze niche werken, en onze onboarding kost daarom maximaal twee weken — geen wisselende juniors, geen "uitleg over MRR", geen kennismaking met drie verschillende contactpersonen.

---

## Regel 8 — Versterkers spaarzaam

*Echt, eigenlijk, juist, daadwerkelijk, precies, nu juist* — LLM's strooien hiermee als ze de zin krachtig willen maken. Een sterke zin heeft geen versterker nodig.

| Zo niet | Zo wel |
|---|---|
| Wij weten écht wat MRR betekent. | Wij weten wat MRR betekent. |
| Onze aanpak is juist anders. | Onze aanpak is anders. |

Versterker mag soms voor klant-stem-quotes of waar het natuurlijk valt — niet als ritmische krukken.

---

## Regel 9 — Slot-zinnen niet als quote-bommen

Elke alinea afsluiten met een korte, krachtige zin (alsof het een quote is) wordt door LLM's overgebruikt. Soms past het, vaak forceert het.

**Zo niet:**
... en zo bouwen we mee aan de groei. Dat is wat Sigma is.

**Zo wel:**
... en zo bouwen we mee aan de groei.

Als de boodschap sterk is, hoeft de slot-zin geen "punchline" te zijn.

---

## Regel 10 — Geen "wij geloven dat..." als refrein

Eén keer kan, herhaling wordt hol.

**Zo niet:**
Wij geloven dat klanten een partner verdienen. Wij geloven dat scale-ups eigen finance-DNA hebben. Wij geloven dat onboarding kort moet zijn.

**Zo wel:**
Klanten verdienen een partner, geen leverancier. Scale-ups hebben hun eigen finance-DNA. Onboarding hoort kort te zijn — twee weken, niet twee maanden.

---

## Discipline voor de redacteur

Conform `.claude/agents/redacteur.md` drielagen-model:

**Laag 1 (auto-fix):**
- Em-dashes in lopende tekst → komma/punt/haakje afhankelijk van context.
- Verwijdering van `Concreet:` / `Belangrijk:` / `Let op:` openingswoorden in lopende klant-output.
- Verwijdering van TL;DR-koppen in klant-output-secties.

**Laag 2 (voorstel):**
- Parallelisme-overdaad, geforceerde drie-puntje-opsommingen, staccato-zinsritme, vetgedrukte tussenkoppen, versterkers, quote-bom-slot-zinnen, "wij geloven dat"-refreinen.

**Laag 3 (flag):**
- Inhoudelijke twijfels, bron-citatie-discipline.

---

## Discipline voor strategie-sub-agents

Alle sub-agents die klant-output produceren (strateeg-icp, strateeg-persona, strateeg-propositie, latere ingrediënten) hebben deze stijlgids als verplichte context.

**Klant-secties** (propositie-paragraaf, persona-tekst, ICP-omschrijving): regels 1-10 toepassen.

**Interne secties** (Dunford-onderbouwing, sanity-flags, verificatie-lijst): regels 1, 4 en 6 toepassen, rest mag pragmatischer.
