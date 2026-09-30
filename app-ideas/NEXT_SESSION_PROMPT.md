Pokračuj v průzkumu ve složce `app-ideas/` na této větvi. Přečti si `app-ideas/README.md`.

1. Nejdřív ověř přístup k Apple: `python3 app-ideas/pipeline/apple_fetch.py check "snore tracker"`.
   Pokud to selže, zastav se a řekni mi, co blokuje.
2. Pracovní složka je `app-ideas/pipeline/` (BRIEF.md, REVIEW_BRIEF.md, validátory, apple_fetch.py,
   evidence v `_partial/`). Pro každou z 27 kategorií App Store spusť jednoho výzkumného agenta
   podle `BRIEF.md`, nejvýš 20 najednou. Výstupy patří do `pipeline/ideas/<slug>.json`.
   Seznam kategorií a slugů je v `pipeline/build.py` (CATS).
3. Jakmile kategorie projde validátorem, spusť na ni oponenta podle `REVIEW_BRIEF.md`
   (výstup `pipeline/review/<slug>.json`).
4. Nakonec `python3 app-ideas/pipeline/build.py`, zkontroluj `app-ideas/index.html`,
   commitni, pushni a publikuj stránku jako artifact (`app-ideas/artifact.html`).

Cíl, pravidla a formát jsou stejné jako v původním zadání: 30 nápadů na kategorii, offline bez
serverů, nika v trhu, který už vydělává, blue-ocean klíčová slova ověřená přes Apple, odkazy
na konkurenci, cíl aspoň 10 000 Kč měsíčně, US gap nápady, ďáblův advokát a pořadí od nejlepšího.
Na tento úkol můžeš použít kredity.
