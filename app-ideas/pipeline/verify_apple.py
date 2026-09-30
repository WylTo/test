#!/usr/bin/env python3
"""
verify_apple.py — add real Apple numbers to every idea's keywords, then re-run build.py.

For each keyword of the top-N ideas (by current score) it calls apple_fetch.check():
iTunes Search API (result count, title saturation, rating strength of the top apps)
+ App Store autocomplete (does Apple suggest the phrase = real people type it).
Writes apple_data.json next to this script; build.py folds it into the ranking.

Usage (needs network access to itunes.apple.com and search.itunes.apple.com):
  python3 verify_apple.py --top 200            # ~45 min at 18 calls/min, resumable (cached)
  python3 verify_apple.py --top 0              # every idea (several hours)
  python3 build.py
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import apple_fetch  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ideas", default=os.path.join(HERE, "..", "data", "ideas.json"))
    ap.add_argument("--top", type=int, default=200, help="0 = all ideas")
    ap.add_argument("--kw-per-idea", type=int, default=3)
    ap.add_argument("--country", default="us")
    ap.add_argument("--out", default=os.path.join(HERE, "apple_data.json"))
    a = ap.parse_args()

    data = json.load(open(a.ideas, encoding="utf-8"))
    ideas = sorted(data["ideas"], key=lambda x: x.get("rank", 9999))
    if a.top:
        ideas = ideas[:a.top]
    kws = []
    for x in ideas:
        for k in x["keywords"][:a.kw_per_idea]:
            kw = k["kw"].strip().lower()
            if kw not in kws:
                kws.append(kw)

    out = {"country": a.country, "keywords": {}}
    if os.path.exists(a.out):
        out = json.load(open(a.out, encoding="utf-8"))
    todo = [k for k in kws if k not in out["keywords"]]
    print(f"{len(kws)} keywords, {len(todo)} still to fetch (~{len(todo) * 2 / apple_fetch.PER_MIN:.0f} min)", file=sys.stderr)
    for i, kw in enumerate(todo, 1):
        try:
            res = apple_fetch.check(kw, a.country)
        except Exception as e:  # noqa: BLE001
            print(f"[{i}/{len(todo)}] {kw}: ERROR {e}", file=sys.stderr)
            continue
        res["keyword"] = kw
        out["keywords"][kw] = res
        print(f"[{i}/{len(todo)}] {kw}: {res['verdict']} sat={res['title_saturation']} top3={res['top3_max_ratings']} hint={res['hint_found']}", file=sys.stderr)
        if i % 10 == 0:
            json.dump(out, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump(out, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"wrote {a.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
