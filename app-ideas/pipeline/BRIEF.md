# BRIEF — Blue-ocean app idea research (one App Store category per agent)

## Client
Lapnito — a small Czech indie studio that ships many small iOS apps (Flutter/Swift),
grows almost exclusively through App Store ASO (no ad budget, no marketing team),
and wants **no backend servers** (nothing to host, nothing to pay monthly).

## Your job
Produce **exactly 30 app ideas** for your assigned App Store category. Each idea must be:

1. **A niche of an existing, proven-profitable app market** ("parent market"). We do NOT
   attack the head term (e.g. "sleep tracker"); we find a sub-niche the big players
   ignore (an audience, profession, hobby, condition, job-to-be-done, locale or modality)
   where a brand-new app can rank top-3 through ASO alone and dominate.
2. **Offline / serverless**: runs on-device. Allowed: bundled static data, on-device ML
   (Core ML, Vision, Speech, Apple Foundation Models), HealthKit, sensors, camera, iCloud/CloudKit
   sync (Apple-hosted, not ours), StoreKit. "partial" = needs a free public API at runtime
   (penalized). Anything needing our own server, user accounts, moderation, or licensed live
   data → reject.
3. **Revenue ≥ 10 000 CZK net per month in ideal conditions** (≈ 435 USD net ≈ 510 USD gross
   before Apple's 15 % small-business commission; 1 USD ≈ 23 CZK). Show the funnel math:
   downloads/month from niche keywords × conversion × price → net CZK. Be realistic about
   the "ideal" — a niche keyword cluster rarely brings more than 1–5k downloads/month.
4. **Bonus — "US gap"**: a model proven in the US App Store (English-only / US-centric apps)
   that is not localized or not available worldwide → we launch it localized in 50 languages.
   Flag with `us_gap: true` and explain. Also consider the reverse (a model big in DE/JP/BR
   but absent in US). Aim for at least 5 US-gap ideas per category where it makes sense.

## Data source (IMPORTANT)
**Primary: real Apple data via `apple_fetch.py`** (in the work dir). It is shared by ~20
agents through one global rate limit (≈ 18 calls/min in total) and a disk cache, so each
call may wait; that is expected. Budget ≈ 90 Apple calls per category — `check` costs 2.
- `python3 <workdir>/apple_fetch.py check "<keyword>"` → title saturation (0–10 of the top 10
  apps with the phrase in the title), rating strength of the top apps, stale apps, whether
  Apple's own autocomplete suggests the phrase (`hint_found` = real people type it), related
  suggestions, a verdict OPEN / CONTESTABLE / HARD / SATURATED, and the top apps with their
  real App Store URLs. This is the blue-ocean test. Use it on every kept keyword.
- `python3 <workdir>/apple_fetch.py hints "<prefix>"` → what Apple autocompletes (cheap demand probe, 1 call)
- `python3 <workdir>/apple_fetch.py avail <app_id> --countries us,gb,de,fr,jp,br,cz` → US-gap test:
  is the US app missing from other storefronts, or English-only (`langs`)?
**Secondary: WebSearch** — only for parent-market revenue proof or forum demand (≤ 8 searches
per agent; the session-wide cap is small and shared). Never use WebSearch to find App Store links.
If `_partial/<category_slug>_evidence.txt` exists, read it first: an earlier run already checked
some niches and saved real URLs there.

A keyword with `hint_found: false` AND `result_count` < 5 has no proven demand — don't build on it.
A keyword with verdict SATURATED or HARD is not blue ocean — use it only as a parent-market proof.

## Method
1. Brainstorm **45+ candidates** first (write them down for yourself). Start from the
   category's top-grossing parent markets, then split by audience / profession / hobby /
   condition / job-to-be-done / modality / locale. Prefer ideas where the "keyword" is a
   natural phrase a person types (1–3 words, no brand names).
2. Check candidates with `apple_fetch.py check`. For each kept idea record per keyword:
   `saturation` = the `title_saturation` value (0–10), and the strongest niche competitor
   (name + ratings count + how stale), and in `note` the Apple facts (hint yes/no, verdict).
3. Keep the **30 best**: real demand evidence + sparse/weak niche competition +
   monetizable + offline-feasible. Drop: saturated (≥ 6 dedicated title-matching strong
   apps), zero evidence of demand, server-dependent, legally risky.
4. Diversity: at most 3 ideas sharing one parent market; no near-duplicates; avoid ideas
   that are just a reskin of each other (Apple Guideline 4.3 spam risk applies to our
   whole portfolio).

## Hard rules for links
- Every competitor URL must be **copied verbatim from `apple_fetch.py` output** (the `url`
  field) or from an evidence file (`https://apps.apple.com/<cc>/app/<slug>/id<digits>`).
  Never construct, guess or "fix" an ID. If you have no real URL for an idea, it lacks
  evidence — replace the idea.
- 1–4 competitors per idea: the parent-market leader (role `parent`), niche competitors
  (role `niche`), US-only analogue (role `us-only`).

## Devil's advocate (required, be brutal)
For every idea give **≥ 3 specific reasons it could fail** — not generic "there is
competition". Think: Apple ships it as a built-in feature (Sherlock), niche too small,
users won't pay, seasonality, Guideline 4.3 (template/spam), 1.4.1 medical claims,
5.1.1 health data, 2.3.7 keyword stuffing, trademarks/licensed content, data that needs
constant updates, offline infeasibility, retention, a big player adds it in a week,
language/cultural fit abroad. Then `killer_risk` (the single most likely cause of failure)
and `mitigation`.

## Scores (integers 1–10, honest — use the full range)
Your 30 ideas' scores should average around 6, not 8. Inflation makes the ranking useless.
- `demand` — evidence of real search demand + paying users (niche or parent)
- `blue_ocean` — weakness/sparseness of competition on the niche keywords (10 = nobody targets it)
- `monetization` — willingness to pay, price points, subscription fit
- `build_ease` — 1 developer, 10 = 1 week MVP, 5 ≈ 6 weeks, 1 = months
- `offline_fit` — 10 = fully offline by nature
- `safety` — inverse of devil's-advocate risk (10 = very low risk)

## Output
Write the JSON file at the path given in your task. Text fields in **Czech** (natural,
persuasive, but honest — you are *selling* the idea to the founder, then attacking it).
App names, keywords and competitor names in English.

```json
{
  "category": "Health & Fitness",
  "category_slug": "health-fitness",
  "search_notes": "cs — any issues with searching, caveats",
  "ideas": [
    {
      "id": "health-fitness-01",
      "name": "Working app name (EN)",
      "tagline": "cs, one line that sells it",
      "pitch": "cs, 3–5 sentences: who, what pain, why now, why we win this niche",
      "niche": "cs, the ignored niche and WHY incumbents ignore it",
      "parent_market": "cs, proven profitable parent market + leaders",
      "target_user": "cs",
      "features": ["cs", "3–6 items, MVP scope"],
      "offline": "full | mostly | partial",
      "offline_note": "cs, what runs on-device; any optional network",
      "monetization": "cs, model + concrete price points in USD and CZK",
      "revenue_math": "cs, funnel to ≥ 10 000 CZK net/month in ideal conditions",
      "revenue_czk_ideal": 15000,
      "keywords": [
        {"kw": "english niche keyword", "saturation": 2, "competitor": "strongest niche app seen", "note": "cs evidence"}
      ],
      "demand_evidence": "cs, concrete evidence you actually found",
      "competitors": [
        {"name": "App Name", "url": "https://apps.apple.com/us/app/...id123", "role": "parent | niche | us-only", "note": "cs"}
      ],
      "us_gap": false,
      "us_gap_note": "cs or empty",
      "devils_advocate": ["cs specific reason 1", "cs reason 2", "cs reason 3"],
      "killer_risk": "cs",
      "mitigation": "cs",
      "build_weeks": 3,
      "scores": {"demand": 6, "blue_ocean": 7, "monetization": 6, "build_ease": 7, "offline_fit": 9, "safety": 6}
    }
  ]
}
```
`keywords`: 3–6 per idea. Ids: `<category_slug>-01` … `-30`, ordered by your own
preliminary ranking (best first).

## Finish
Validate: `python3 <workdir>/validate.py <your json path>` — fix every ERROR and re-run
until it prints `OK`. Warnings about score inflation must be addressed, not ignored.
Your final message: ≤ 6 lines — idea count, your top 3 (name + one-line why), and any
search problems. Do not paste the JSON into the final message.
