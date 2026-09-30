#!/usr/bin/env python3
"""Merge ideas/*.json + review/*.json (+ optional apple_data.json), score, rank, and render HTML.

Usage: python3 build.py [--work DIR] [--out-dir DIR]
Writes:
  <out-dir>/index.html          full standalone document (open locally)
  <out-dir>/artifact.html       same page without the <html>/<head>/<body> skeleton (for publishing)
  <out-dir>/data/ideas.json     merged + scored dataset
"""
import argparse
import glob
import html
import json
import os
from datetime import date

CATS = [
    ("health-fitness", "Zdraví a fitness"), ("productivity", "Produktivita"),
    ("utilities", "Utility"), ("education", "Vzdělávání"), ("finance", "Finance"),
    ("lifestyle", "Životní styl"), ("photo-video", "Foto a video"), ("music", "Hudba"),
    ("travel", "Cestování"), ("business", "Byznys"), ("games", "Hry"),
    ("food-drink", "Jídlo a pití"), ("medical", "Zdravotnictví"), ("reference", "Příručky"),
    ("entertainment", "Zábava"), ("sports", "Sport"), ("graphics-design", "Grafika a design"),
    ("kids", "Děti"), ("navigation", "Navigace"), ("books", "Knihy"),
    ("developer-tools", "Vývojářské nástroje"), ("weather", "Počasí"),
    ("shopping", "Nakupování"), ("social-networking", "Sociální sítě"), ("news", "Zprávy"),
    ("magazines-newspapers", "Časopisy a noviny"), ("stickers", "Samolepky"),
]
CAT_CS = dict(CATS)
W = {"demand": 0.22, "blue_ocean": 0.26, "monetization": 0.18,
     "build_ease": 0.12, "offline_fit": 0.07, "safety": 0.15}
# Same app idea proposed in several categories: build it once. Best-scored copy stays primary.
DUPES = [
    ["graphics-design-02", "photo-video-02"], ["business-02", "graphics-design-10"],
    ["business-29", "graphics-design-27"], ["lifestyle-04", "entertainment-01"],
    ["games-02", "entertainment-04"], ["kids-01", "education-02"],
    ["business-01", "finance-10"], ["business-10", "finance-09"],
    ["sports-02", "navigation-01"], ["health-fitness-03", "travel-03"],
    ["education-26", "kids-14"], ["entertainment-02", "social-networking-03"],
    ["shopping-19", "social-networking-02"], ["navigation-11", "utilities-04", "weather-04"],
    ["navigation-06", "weather-10"], ["productivity-02", "utilities-05"],
]
VERDICT_ADJ = {"GO": 3.0, "MAYBE": 0.0, "KILL": -15.0, None: -4.0}


def apple_adjust(kw_data):
    """Small, transparent nudge from Apple data when available (see Metodika)."""
    if not kw_data:
        return 0.0, None
    adj = 0.0
    hinted = [k for k in kw_data if k.get("hint_found")]
    strong = [k for k in kw_data if (k.get("top3_max_ratings") or 0) >= 20000 and (k.get("title_saturation") or 0) >= 5]
    open_ = [k for k in kw_data if (k.get("title_saturation") or 0) <= 2 and (k.get("top3_max_ratings") or 0) < 2000]
    if hinted:
        adj += 3.0
    else:
        adj -= 3.0
    adj -= 2.0 * len(strong)
    adj += 1.0 * min(2, len(open_))
    return max(-8.0, min(6.0, adj)), {"hinted": len(hinted), "strong": len(strong), "open": len(open_)}


def main():
    ap = argparse.ArgumentParser()
    here = os.path.dirname(os.path.abspath(__file__))
    ap.add_argument("--work", default=here)
    ap.add_argument("--out-dir", default=os.path.normpath(os.path.join(here, "..")))
    a = ap.parse_args()

    apple = {}
    apple_path = os.path.join(a.work, "apple_data.json")
    if os.path.exists(apple_path):
        apple = json.load(open(apple_path, encoding="utf-8")).get("keywords", {})

    ideas, cat_meta = [], {}
    for slug, cs in CATS:
        p = os.path.join(a.work, "ideas", f"{slug}.json")
        if not os.path.exists(p):
            continue
        d = json.load(open(p, encoding="utf-8"))
        rp = os.path.join(a.work, "review", f"{slug}.json")
        rev = json.load(open(rp, encoding="utf-8")) if os.path.exists(rp) else {}
        rmap = {r["id"]: r for r in rev.get("reviews", [])}
        cat_meta[slug] = {"slug": slug, "name_cs": cs, "name_en": d.get("category", slug),
                          "search_notes": d.get("search_notes", ""),
                          "review_summary": rev.get("summary", ""), "reviewed": bool(rmap)}
        for i, idea in enumerate(d["ideas"], 1):
            r = rmap.get(idea["id"])
            sc = (r or {}).get("scores") or idea["scores"]
            base = 10.0 * sum(W[k] * sc[k] for k in W)
            verdict = r["verdict"] if r else None
            kwd = [apple[k["kw"].lower()] for k in idea["keywords"] if k["kw"].lower() in apple]
            aadj, ainfo = apple_adjust(kwd)
            if r and r.get("web_checked"):
                idea = dict(idea, evidence="web")
            ev_adj = 0.0 if idea.get("evidence") == "web" else -3.0
            score = round(max(0.0, min(100.0, base + VERDICT_ADJ[verdict] + aadj + ev_adj)), 1)
            idea = dict(idea)
            idea.update({
                "category_slug": slug, "category_cs": cs, "author_rank": i,
                "review": r, "verdict": verdict, "final_scores": sc,
                "score_base": round(base, 1), "score": score,
                "revenue_czk_realistic": (r or {}).get("revenue_czk_realistic"),
                "apple": kwd, "apple_info": ainfo,
            })
            ideas.append(idea)

    byid = {x["id"]: x for x in ideas}
    for grp in DUPES:
        members = [byid[i] for i in grp if i in byid]
        if len(members) < 2:
            continue
        members.sort(key=lambda x: -x["score"])
        prim = members[0]
        for m in members[1:]:
            m["dup_of"] = {"id": prim["id"], "name": prim["name"], "category_cs": prim["category_cs"]}
            m["score"] = round(max(0.0, m["score"] - 8.0), 1)
        prim["dup_also"] = [{"id": m["id"], "name": m["name"], "category_cs": m["category_cs"]} for m in members[1:]]

    vorder = {"GO": 0, "MAYBE": 1, None: 2, "KILL": 3}
    ideas.sort(key=lambda x: (-x["score"], vorder[x["verdict"]], -(x["revenue_czk_realistic"] or 0)))
    for n, x in enumerate(ideas, 1):
        x["rank"] = n
    per_cat = {}
    for x in ideas:
        per_cat.setdefault(x["category_slug"], []).append(x)
    for slug, lst in per_cat.items():
        for n, x in enumerate(lst, 1):
            x["cat_rank"] = n
        m = cat_meta[slug]
        m["count"] = len(lst)
        m["go"] = sum(1 for x in lst if x["verdict"] == "GO")
        m["maybe"] = sum(1 for x in lst if x["verdict"] == "MAYBE")
        m["kill"] = sum(1 for x in lst if x["verdict"] == "KILL")
        m["avg"] = round(sum(x["score"] for x in lst) / len(lst), 1)
        m["top"] = lst[0]["name"]
        m["top_id"] = lst[0]["id"]
        m["top_score"] = lst[0]["score"]

    stats = {
        "ideas": len(ideas), "categories": len(per_cat),
        "go": sum(1 for x in ideas if x["verdict"] == "GO"),
        "maybe": sum(1 for x in ideas if x["verdict"] == "MAYBE"),
        "kill": sum(1 for x in ideas if x["verdict"] == "KILL"),
        "unreviewed": sum(1 for x in ideas if x["verdict"] is None),
        "us_gap": sum(1 for x in ideas if x.get("us_gap")),
        "web": sum(1 for x in ideas if x.get("evidence") == "web"),
        "competitor_links": sum(len(x["competitors"]) + len((x["review"] or {}).get("missed_competitors", [])) for x in ideas),
        "apple_verified": bool(apple),
        "generated": date.today().isoformat(),
    }
    cats_out = [cat_meta[s] for s, _ in CATS if s in cat_meta]
    payload = {"stats": stats, "categories": cats_out, "weights": W, "ideas": ideas}

    os.makedirs(os.path.join(a.out_dir, "data"), exist_ok=True)
    with open(os.path.join(a.out_dir, "data", "ideas.json"), "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)

    tpl = open(os.path.join(a.work, "template.html"), encoding="utf-8").read()
    blob = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    page = tpl.replace("/*__DATA__*/null", blob)
    with open(os.path.join(a.out_dir, "artifact.html"), "w", encoding="utf-8") as f:
        f.write(page)
    head_end = page.index("</style>") + len("</style>")
    full = ("<!doctype html>\n<html lang=\"cs\">\n<head>\n<meta charset=\"utf-8\">\n"
            "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1, viewport-fit=cover\">\n"
            + page[:head_end] + "\n</head>\n<body>\n" + page[head_end:] + "\n</body>\n</html>\n")
    with open(os.path.join(a.out_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(full)
    print(json.dumps(stats, ensure_ascii=False))
    print(f"size: {len(page)/1024/1024:.2f} MB")


if __name__ == "__main__":
    main()
