#!/usr/bin/env python3
"""Validate review/<slug>.json against the ideas file. Prints OK or ERROR/WARN lines."""
import json
import glob
import os
import re
import sys
from statistics import mean

HERE = os.path.dirname(os.path.abspath(__file__))

URL_RE = re.compile(r"^https://apps\.apple\.com/[a-z]{2}/app/([^/?#]+/)?id\d{6,12}(\?.*)?$")
SCORE_KEYS = ["demand", "blue_ocean", "monetization", "build_ease", "offline_fit", "safety"]


def main(ideas_path, review_path):
    errors, warns = [], []
    ideas = json.load(open(ideas_path, encoding="utf-8"))
    try:
        rev = json.load(open(review_path, encoding="utf-8"))
    except Exception as e:
        print(f"ERROR: cannot parse JSON: {e}")
        return 1
    ids = [i["id"] for i in ideas["ideas"]]
    if rev.get("category_slug") != ideas.get("category_slug"):
        errors.append("category_slug mismatch")
    if not str(rev.get("summary", "")).strip():
        errors.append("summary missing")
    reviews = rev.get("reviews", [])
    got = [r.get("id") for r in reviews]
    missing = [i for i in ids if i not in got]
    extra = [i for i in got if i not in ids]
    dups = {i for i in got if got.count(i) > 1}
    if missing:
        errors.append(f"missing reviews for {missing}")
    if extra:
        errors.append(f"unknown ids {extra}")
    if dups:
        errors.append(f"duplicate reviews {sorted(dups)}")
    verdicts = []
    for r in reviews:
        tag = r.get("id", "?")
        v = r.get("verdict")
        verdicts.append(v)
        if v not in ("GO", "MAYBE", "KILL"):
            errors.append(f"{tag}: verdict must be GO|MAYBE|KILL")
        sc = r.get("scores", {})
        for k in SCORE_KEYS:
            x = sc.get(k) if isinstance(sc, dict) else None
            if not isinstance(x, int) or not (1 <= x <= 10):
                errors.append(f"{tag}: scores.{k} must be int 1–10")
        if not isinstance(r.get("extra_risks"), list):
            errors.append(f"{tag}: extra_risks must be a list")
        mc = r.get("missed_competitors", [])
        if not isinstance(mc, list):
            errors.append(f"{tag}: missed_competitors must be a list")
        else:
            for c in mc:
                if c.get("url") and not URL_RE.match(str(c.get("url", ""))):
                    errors.append(f"{tag}: missed competitor '{c.get('name')}' bad url '{c.get('url')}'")
                m = re.search(r"id(\d+)", str(c.get("url") or ""))
                if m:
                    ev = set()
                    for f in glob.glob(os.path.join(HERE, "_partial", "*.txt")):
                        ev |= set(re.findall(r"\bid(\d{6,12})\b", open(f, encoding="utf-8").read()))
                    if m.group(1) not in ev:
                        errors.append(f"{tag}: missed competitor url id {m.group(1)} not found in _partial/*.txt — save the search result there first or leave url empty")
        rr = r.get("revenue_czk_realistic")
        if not isinstance(rr, int) or rr < 0:
            errors.append(f"{tag}: revenue_czk_realistic must be a non-negative int")
        if not str(r.get("reviewer_note", "")).strip():
            errors.append(f"{tag}: reviewer_note missing")
    n = len(reviews) or 1
    go = verdicts.count("GO") / n
    kill = verdicts.count("KILL") / n
    if go > 0.6:
        warns.append(f"{go:.0%} GO — too lenient? Recheck the weakest GOs.")
    if kill == 0:
        warns.append("no KILL verdicts — are you sure nothing has a fatal flaw?")
    try:
        avg = mean(r["scores"][k] for r in reviews for k in SCORE_KEYS if k != "offline_fit")
        if avg > 6.8:
            warns.append(f"mean adjusted score {avg:.2f} > 6.8 — be harsher")
    except Exception:
        pass
    for e in errors:
        print("ERROR:", e)
    for w in warns:
        print("WARN:", w)
    if not errors:
        print(f"OK ({len(reviews)} reviews: GO {verdicts.count('GO')}, MAYBE {verdicts.count('MAYBE')}, KILL {verdicts.count('KILL')}; {len(warns)} warnings)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
