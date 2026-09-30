#!/usr/bin/env python3
"""Validate an ideas/<slug>.json file against BRIEF.md. Prints OK or ERROR/WARN lines."""
import json
import re
import sys
from statistics import mean

URL_RE = re.compile(r"^https://apps\.apple\.com/[a-z]{2}/app/([^/?#]+/)?id\d{6,12}(\?.*)?$")
SCORE_KEYS = ["demand", "blue_ocean", "monetization", "build_ease", "offline_fit", "safety"]
STR_FIELDS = ["id", "name", "tagline", "pitch", "niche", "parent_market", "target_user",
              "offline_note", "monetization", "revenue_math", "demand_evidence",
              "killer_risk", "mitigation"]


def main(path):
    errors, warns = [], []
    try:
        data = json.load(open(path, encoding="utf-8"))
    except Exception as e:
        print(f"ERROR: cannot parse JSON: {e}")
        return 1
    for k in ["category", "category_slug", "ideas"]:
        if k not in data:
            errors.append(f"top-level missing '{k}'")
    ideas = data.get("ideas", [])
    slug = data.get("category_slug", "")
    if len(ideas) != 30:
        errors.append(f"expected 30 ideas, got {len(ideas)}")
    seen_ids, seen_names, seen_urls = set(), set(), {}
    for i, idea in enumerate(ideas, 1):
        tag = idea.get("id", f"#{i}")
        exp_id = f"{slug}-{i:02d}"
        if idea.get("id") != exp_id:
            errors.append(f"{tag}: id should be '{exp_id}'")
        if tag in seen_ids:
            errors.append(f"{tag}: duplicate id")
        seen_ids.add(tag)
        nm = str(idea.get("name", "")).strip().lower()
        if nm in seen_names:
            errors.append(f"{tag}: duplicate name '{nm}'")
        seen_names.add(nm)
        for f in STR_FIELDS:
            v = idea.get(f)
            if not isinstance(v, str) or not v.strip():
                errors.append(f"{tag}: '{f}' must be a non-empty string")
        if len(str(idea.get("pitch", ""))) < 120:
            warns.append(f"{tag}: pitch is very short — sell it (3–5 sentences)")
        feats = idea.get("features")
        if not isinstance(feats, list) or not (3 <= len(feats) <= 6):
            errors.append(f"{tag}: features must be a list of 3–6 items")
        if idea.get("offline") not in ("full", "mostly", "partial"):
            errors.append(f"{tag}: offline must be full|mostly|partial")
        rev = idea.get("revenue_czk_ideal")
        if not isinstance(rev, int) or rev < 10000:
            errors.append(f"{tag}: revenue_czk_ideal must be an int >= 10000 (got {rev!r})")
        elif rev > 400000:
            warns.append(f"{tag}: revenue_czk_ideal {rev} looks unrealistic for a niche app")
        kws = idea.get("keywords")
        if not isinstance(kws, list) or not (3 <= len(kws) <= 6):
            errors.append(f"{tag}: keywords must be a list of 3–6 objects")
        else:
            for kw in kws:
                if not isinstance(kw, dict) or not str(kw.get("kw", "")).strip():
                    errors.append(f"{tag}: keyword entries need 'kw'")
                    continue
                s = kw.get("saturation")
                if not isinstance(s, int) or not (0 <= s <= 10):
                    errors.append(f"{tag}: keyword '{kw.get('kw')}' saturation must be int 0–10")
                for f in ("competitor", "note"):
                    if not isinstance(kw.get(f), str):
                        errors.append(f"{tag}: keyword '{kw.get('kw')}' needs string '{f}'")
        comps = idea.get("competitors")
        if not isinstance(comps, list) or not (1 <= len(comps) <= 4):
            errors.append(f"{tag}: competitors must be a list of 1–4 objects")
        else:
            for c in comps:
                url = str(c.get("url", ""))
                if not URL_RE.match(url):
                    errors.append(f"{tag}: competitor '{c.get('name')}' has non-App-Store or malformed url '{url}'")
                if c.get("role") not in ("parent", "niche", "us-only"):
                    errors.append(f"{tag}: competitor '{c.get('name')}' role must be parent|niche|us-only")
                if not str(c.get("name", "")).strip():
                    errors.append(f"{tag}: competitor missing name")
                m = re.search(r"id(\d+)", url)
                if m:
                    seen_urls.setdefault(m.group(1), set()).add(str(c.get("name", "")).strip().lower())
        if not isinstance(idea.get("us_gap"), bool):
            errors.append(f"{tag}: us_gap must be true/false")
        elif idea["us_gap"] and not str(idea.get("us_gap_note", "")).strip():
            errors.append(f"{tag}: us_gap true requires us_gap_note")
        da = idea.get("devils_advocate")
        if not isinstance(da, list) or len(da) < 3 or not all(isinstance(x, str) and x.strip() for x in da):
            errors.append(f"{tag}: devils_advocate needs >= 3 non-empty strings")
        bw = idea.get("build_weeks")
        if not isinstance(bw, (int, float)) or not (0.5 <= bw <= 26):
            errors.append(f"{tag}: build_weeks must be a number 0.5–26")
        sc = idea.get("scores", {})
        for k in SCORE_KEYS:
            v = sc.get(k) if isinstance(sc, dict) else None
            if not isinstance(v, int) or not (1 <= v <= 10):
                errors.append(f"{tag}: scores.{k} must be int 1–10")
    for app_id, names in seen_urls.items():
        if len(names) > 1:
            warns.append(f"app id {app_id} is used for different app names {sorted(names)} — a copied URL may be wrong")
    try:
        allsc = [idea["scores"][k] for idea in ideas for k in SCORE_KEYS if k not in ("offline_fit",)]
        avg = mean(allsc)
        if avg > 7.0:
            warns.append(f"score inflation: mean of demand/blue_ocean/monetization/build_ease/safety = {avg:.2f} (> 7.0). Be harsher.")
        for k in SCORE_KEYS:
            vals = [idea["scores"][k] for idea in ideas]
            if max(vals) - min(vals) < 3 and k != "offline_fit":
                warns.append(f"scores.{k} barely varies ({min(vals)}–{max(vals)}); use the full range")
    except Exception:
        pass
    usg = sum(1 for idea in ideas if idea.get("us_gap") is True)
    if usg < 3:
        warns.append(f"only {usg} US-gap ideas — look for more where it makes sense")
    for e in errors:
        print("ERROR:", e)
    for w in warns:
        print("WARN:", w)
    if not errors:
        print(f"OK ({len(ideas)} ideas, {len(warns)} warnings)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
