# OFFLINE RUN — overrides for BRIEF.md (read BRIEF.md first, then this)

No live data is available in this run: Apple domains are blocked and the WebSearch budget is
exhausted. **Do not call WebSearch, WebFetch, curl or apple_fetch.py.** Everything else in
BRIEF.md applies (30 ideas, niche of a proven market, offline/serverless, ≥ 10 000 CZK ideal,
US-gap ideas, devil's advocate, honest scores, Czech text, JSON schema, validator).

## Your data
1. `_partial/<category_slug>_evidence.txt` (if it exists) — real findings from ~15 web searches
   done earlier for your category: which niches are CROWDED (don't propose those as blue ocean)
   and which are OPEN, with real App Store URLs. Build on it: the OPEN niches and draft
   rankings there should form the core of your 30. Other categories' evidence files may also
   hold useful URLs (e.g. business ↔ productivity, reference ↔ education); you may use them.
2. Your own knowledge of the App Store market (as of 2025–26) for the rest.

## Links (hard rule — the validator enforces it)
- A competitor `url` may ONLY be an App Store URL copied verbatim from a `_partial/*.txt` file.
  The validator rejects any app ID not present there. Never write an ID from memory.
- For competitors you know but have no evidence URL for, set `"url": ""` — the page will
  generate an App Store search link from the name automatically.
- Aim: every idea whose niche appears in the evidence file should carry ≥ 1 evidence URL.

## Honesty fields (add to every idea)
- `"evidence": "web"` if the niche's saturation/competitors come from the evidence file,
  `"evidence": "knowledge"` if it is your own market knowledge only.
- For `"knowledge"` ideas, keyword `saturation` is your estimate; say so in the keyword `note`
  ("odhad"). Score `blue_ocean` no higher than 7 for knowledge-only ideas.
- `demand_evidence` must state honestly what is verified and what is assumed.

Validate with `python3 validate.py ideas/<slug>.json` (run it from the pipeline dir) until OK.
Final message ≤ 4 lines.
