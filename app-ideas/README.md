# Atlas niche aplikací: rozpracovaný průzkum

Cíl: 30 nápadů na offline aplikace bez serverů pro každou kategorii App Store (27 kategorií,
asi 810 nápadů). Každý nápad má mířit na opomíjenou niku v trhu, který už prokazatelně
vydělává, mít ověřenou poptávku a slabou konkurenci přes data z Apple („blue ocean“ klíčová
slova), odkazy na konkurenci, výpočet cesty k 10 000 Kč měsíčně, oponenturu ďáblova
advokáta a výsledné pořadí. Výstupem je HTML stránka.

## Stav k 2026-09-30

Průzkum se v první relaci zastavil na dvou limitech cloudového prostředí:

1. **Apple domény jsou blokované síťovou politikou prostředí**: `itunes.apple.com`,
   `search.itunes.apple.com`, `apps.apple.com`, `rss.applemarketingtools.com`,
   `api.appstoreconnect.apple.com`. Bez nich nejde ověřit skutečnou poptávku ani
   konkurenci přímo u Apple.
2. **Webové vyhledávání má limit 200 dotazů na relaci.** Paralelní agenti ho vyčerpali
   během několika minut, dřív než stihli dokončit jedinou kategorii.

Hotové ani ověřené nápady zatím nejsou. Připravená je celá výrobní linka a poznatky
z prvních asi 200 vyhledávání (ve kterých nikách je už přeplněno a kde je volno, se
skutečnými odkazy do App Store).

## Co je ve složce

| Cesta | Co to je |
|---|---|
| `pipeline/BRIEF.md` | Zadání pro výzkumného agenta jedné kategorie (metoda, pravidla, JSON schéma) |
| `pipeline/REVIEW_BRIEF.md` | Zadání pro agenta v roli ďáblova advokáta (verdikty GO / MAYBE / KILL) |
| `pipeline/apple_fetch.py` | Klient Apple dat pro 20 paralelních agentů: iTunes Search API, našeptávač App Store, dostupnost aplikace v zemích. Globální limit dotazů a mezipaměť |
| `pipeline/validate.py`, `validate_review.py` | Kontrola výstupů agentů (30 nápadů, skutečné URL z App Store, skóre bez nafukování) |
| `pipeline/build.py` + `template.html` | Sloučení, skórování, pořadí a vygenerování HTML (`index.html`) |
| `pipeline/verify_apple.py` | Doplnění Apple čísel ke klíčovým slovům hotových nápadů a přepočet pořadí |
| `pipeline/_partial/*_evidence.txt` | Poznatky z první relace pro jednotlivé kategorie |

Offline testy proběhly na umělých datech: validátory, skórování, vykreslení HTML
v Chromiu na šířce počítače i telefonu, ve světlém i tmavém režimu. `apple_fetch.py`
je otestovaný na simulovaných odpovědích. Proti skutečnému Apple API zatím neběžel,
protože byl odsud blokovaný.

## Jak pokračovat

1. V nastavení cloudového prostředí (menu prostředí v záhlaví relace → Edit →
   Network access) povolte domény `itunes.apple.com` a `search.itunes.apple.com`,
   ideálně i `apps.apple.com` a `rss.applemarketingtools.com`. Druhou možností je
   přepnout přístup k síti na plný.
2. Volitelně přidejte do proměnných prostředí `CLAUDE_CODE_MAX_WEB_SEARCHES_PER_SESSION=1500`.
   Výzkum už na webovém vyhledávání nestojí, pomůže jen u důkazů tržeb a poptávky.
3. Spusťte novou relaci na této větvi a vložte zadání z `NEXT_SESSION_PROMPT.md`.

Odhad: Apple povoluje asi 20 dotazů za minutu z jedné IP adresy. 27 kategorií × ~90
dotazů plus oponentura vychází zhruba na 3–4 hodiny běhu na pozadí.
