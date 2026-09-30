#!/usr/bin/env python3
"""
apple_fetch.py — shared, rate-limited Apple App Store data client for many parallel agents.

Only official public endpoints:
  * iTunes Search API  (https://itunes.apple.com/search, /lookup)
  * App Store search hints (autocomplete) (https://search.itunes.apple.com/.../hints)

Safe for 20+ agents at once: one global rate limit shared across processes through a lock
file (default 18 calls/min in total), plus an on-disk cache so repeated questions are free.

Commands (compact JSON on stdout, meant to be read by an agent):
  search <term> [--country us] [--n 10]   top apps for a phrase: title, url, ratings, age
  hints  <term> [--country us]            Apple autocomplete suggestions (demand signal)
  check  <term> [--country us]            search + hints + blue-ocean summary in one call pair
  avail  <app_id> [--countries us,gb,de,fr,jp,br,cz]   in which storefronts an app exists

Env: APPLE_CACHE_DIR (default ./.apple_cache next to this file), APPLE_CALLS_PER_MIN (18).
"""
import argparse
import fcntl
import hashlib
import json
import os
import plistlib
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.environ.get("APPLE_CACHE_DIR", os.path.join(HERE, ".apple_cache"))
PER_MIN = float(os.environ.get("APPLE_CALLS_PER_MIN", "18"))
UA = "Mozilla/5.0 (research; official iTunes Search API; cached; rate-limited)"
# App Store storefront ids for the hints endpoint (X-Apple-Store-Front header).
STOREFRONT = {"us": "143441", "gb": "143444", "de": "143443", "fr": "143442", "jp": "143462",
              "br": "143503", "cz": "143489", "es": "143454", "it": "143450", "ca": "143455",
              "au": "143460", "mx": "143468", "pl": "143478", "nl": "143452", "in": "143467"}


def _throttle():
    """Global cross-process rate limit: serialize calls through a lock file holding the last call time."""
    os.makedirs(CACHE, exist_ok=True)
    lock_path = os.path.join(CACHE, ".ratelimit")
    gap = 60.0 / PER_MIN
    with open(lock_path, "a+") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        f.seek(0)
        try:
            last = float(f.read().strip() or 0)
        except ValueError:
            last = 0.0
        wait = last + gap - time.time()
        if wait > 0:
            time.sleep(wait)
        f.seek(0)
        f.truncate()
        f.write(str(time.time()))
        f.flush()
        fcntl.flock(f, fcntl.LOCK_UN)


def _get(url, headers=None, kind="x", key=None, ttl_days=7):
    key = key or url
    h = hashlib.sha1(key.encode()).hexdigest()[:20]
    path = os.path.join(CACHE, kind, h + ".bin")
    if os.path.exists(path) and time.time() - os.path.getmtime(path) < ttl_days * 86400:
        return open(path, "rb").read()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    last_err = None
    for attempt in range(4):
        _throttle()
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, **(headers or {})})
            with urllib.request.urlopen(req, timeout=30) as r:
                body = r.read()
            with open(path, "wb") as f:
                f.write(body)
            return body
        except Exception as e:  # noqa: BLE001
            last_err = e
            time.sleep(10 * (2 ** attempt))  # 403/429 from Apple = slow down hard
    raise RuntimeError(f"Apple request failed after retries: {last_err}")


def _days(s):
    try:
        return (datetime.now(timezone.utc) - datetime.fromisoformat(s.replace("Z", "+00:00"))).days
    except Exception:  # noqa: BLE001
        return None


def _tokens(s):
    return [t for t in re.findall(r"[a-z0-9]+", s.lower()) if t]


def title_match(term, title):
    tt = set(_tokens(title))
    return all(t in tt or t.rstrip("s") in tt or (t + "s") in tt for t in _tokens(term))


def search(term, country="us", n=10):
    q = urllib.parse.urlencode({"term": term, "country": country, "media": "software",
                                "entity": "software", "limit": 25})
    raw = json.loads(_get(f"https://itunes.apple.com/search?{q}", kind="search"))
    apps = []
    for i, r in enumerate(raw.get("results", [])[:n], 1):
        apps.append({
            "rank": i, "id": r.get("trackId"), "name": r.get("trackName", ""),
            "url": (r.get("trackViewUrl") or "").split("?")[0],
            "ratings": r.get("userRatingCount", 0), "stars": round(r.get("averageUserRating", 0) or 0, 2),
            "price": r.get("price", 0), "genre": r.get("primaryGenreName", ""),
            "seller": r.get("sellerName", ""), "released": (r.get("releaseDate") or "")[:10],
            "days_since_update": _days(r.get("currentVersionReleaseDate", "")),
            "langs": len(r.get("languageCodesISO2A") or []),
            "title_match": title_match(term, r.get("trackName", "")),
        })
    return {"term": term, "country": country, "result_count": raw.get("resultCount", 0), "top": apps}


def hints(term, country="us"):
    sf = STOREFRONT.get(country, "143441")
    q = urllib.parse.urlencode({"clientApplication": "Software", "term": term})
    body = _get(f"https://search.itunes.apple.com/WebObjects/MZSearchHints.woa/wa/hints?{q}",
                headers={"X-Apple-Store-Front": f"{sf}-1,29"}, kind="hints", key=f"{term}|{country}")
    out = []
    try:
        pl = plistlib.loads(body)
        for d in pl.get("hints", []):
            out.append({"term": d.get("term", ""), "priority": d.get("priority")})
    except Exception:  # noqa: BLE001 — fall back to scraping <string> terms from the XML
        for t in re.findall(r"<key>term</key>\s*<string>([^<]+)</string>", body.decode("utf-8", "ignore")):
            out.append({"term": t, "priority": None})
    norm = " ".join(_tokens(term))
    exact = next((h for h in out if " ".join(_tokens(h["term"])) == norm), None)
    return {"term": term, "country": country, "suggestions": out[:10],
            "exact_suggested": exact is not None, "exact_priority": exact["priority"] if exact else None}


def check(term, country="us"):
    s = search(term, country, 10)
    h = hints(term, country)
    top = s["top"]
    sat = sum(1 for a in top if a["title_match"])
    top3 = max([a["ratings"] for a in top[:3]] or [0])
    strong_matching = [a for a in top if a["title_match"] and a["ratings"] >= 5000]
    stale = [a for a in top[:5] if (a["days_since_update"] or 0) > 540]
    if sat <= 2 and top3 < 2000:
        verdict = "OPEN"
    elif sat >= 6 and len(strong_matching) >= 2:
        verdict = "SATURATED"
    elif len(strong_matching) >= 3 or top3 >= 100000:
        verdict = "HARD"
    else:
        verdict = "CONTESTABLE"
    return {
        "term": term, "country": country, "result_count": s["result_count"],
        "title_saturation": sat, "top3_max_ratings": top3,
        "strong_title_matches": len(strong_matching), "stale_in_top5": len(stale),
        "hint_found": h["exact_suggested"], "hint_priority": h["exact_priority"],
        "related_hints": [x["term"] for x in h["suggestions"][:6]],
        "verdict": verdict,
        "top": [{k: a[k] for k in ("rank", "name", "url", "ratings", "stars", "price", "days_since_update", "title_match", "langs")} for a in top[:6]],
    }


def avail(app_id, countries):
    out = {}
    for c in countries:
        q = urllib.parse.urlencode({"id": app_id, "country": c, "entity": "software"})
        raw = json.loads(_get(f"https://itunes.apple.com/lookup?{q}", kind="lookup"))
        r = (raw.get("results") or [None])[0]
        out[c] = None if not r else {"ratings": r.get("userRatingCount", 0), "langs": r.get("languageCodesISO2A", [])}
    return {"app_id": app_id, "available": {c: v is not None for c, v in out.items()}, "detail": out}


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    for name in ("search", "hints", "check"):
        s = sub.add_parser(name)
        s.add_argument("term")
        s.add_argument("--country", default="us")
        if name == "search":
            s.add_argument("--n", type=int, default=10)
    a_ = sub.add_parser("avail")
    a_.add_argument("app_id")
    a_.add_argument("--countries", default="us,gb,de,fr,jp,br,cz")
    a = p.parse_args()
    if a.cmd == "search":
        res = search(a.term, a.country, a.n)
    elif a.cmd == "hints":
        res = hints(a.term, a.country)
    elif a.cmd == "check":
        res = check(a.term, a.country)
    else:
        res = avail(a.app_id, [c.strip() for c in a.countries.split(",") if c.strip()])
    print(json.dumps(res, ensure_ascii=False, separators=(",", ":")))


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(2)
