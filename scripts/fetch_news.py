#!/usr/bin/env python3
"""Fetch RSS feeds, keep Somalia-related items only, write news.json.
Uses only the Python standard library (no installs needed)."""
import html, json, re, sys, urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from pathlib import Path

# ======================= CONFIG =======================
FEEDS = [
    # trusted=True -> feed is already Somalia-only, skip keyword filter
    {"name": "Google News (عربي)",    "trusted": False,
     "url": "https://news.google.com/rss/search?q=%D8%A7%D9%84%D8%B5%D9%88%D9%85%D8%A7%D9%84&hl=ar&gl=SA&ceid=SA:ar"},
    {"name": "Google News (English)", "trusted": False,
     "url": "https://news.google.com/rss/search?q=Somalia&hl=en&gl=US&ceid=US:en"},
    {"name": "BBC Somali",            "trusted": True,
     "url": "https://feeds.bbci.co.uk/somali/rss.xml"},
    # {"name": "My feed", "trusted": False, "url": "https://example.com/rss.xml"},
]

KEYWORDS = [
    "الصومال", "الصومالي", "الصومالية", "مقديشو", "مقديشيو", "بونتلاند", "أرض الصومال",
    "صوماليلاند", "جوبالاند", "كيسمايو", "بيدوا", "بلدوين", "حركة الشباب",
    "somalia", "somali", "mogadishu", "puntland", "somaliland", "jubaland", "kismayo",
    "baidoa", "al-shabaab", "al shabaab",
    "soomaali", "muqdisho", "xamar", "hargeysa", "garowe",
]
EXCLUDE = []          # words that remove an article even if it matches

MAX_ITEMS = 30
MAX_AGE_DAYS = 7      # 0 = no limit
SUMMARY_LEN = 300
OUT = Path(__file__).resolve().parent.parent / "news.json"
# ======================================================

def local(tag): return tag.rsplit("}", 1)[-1]
def kids(el, name): return [c for c in el if local(c.tag) == name]

def text_of(el, *names):
    for n in names:
        for c in kids(el, n):
            if c.text and c.text.strip():
                return c.text.strip()
    return ""

def clean(t):
    t = re.sub(r"<[^>]+>", " ", t or "")
    return re.sub(r"\s+", " ", html.unescape(t)).strip()

def get_link(el):
    for c in kids(el, "link"):
        if c.get("href"): return c.get("href")
        if c.text and c.text.strip(): return c.text.strip()
    return ""

def get_image(el, raw):
    for c in el.iter():
        n = local(c.tag)
        url = c.get("url")
        if not url: continue
        typ = (c.get("type") or "") + (c.get("medium") or "")
        if n == "thumbnail": return url
        if n in ("content", "enclosure") and (not typ or "image" in typ): return url
    m = re.search(r'<img[^>]+src=["\']([^"\']+)', raw or "", re.I)
    return m.group(1) if m else ""

def parse_date(s):
    if not s: return None
    try:
        d = parsedate_to_datetime(s)
    except Exception:
        try: d = datetime.fromisoformat(s.replace("Z", "+00:00"))
        except Exception: return None
    if d.tzinfo is None: d = d.replace(tzinfo=timezone.utc)
    return d.astimezone(timezone.utc)

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; AMBNewsBot/1.0)"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()

def parse_feed(data, feed):
    root = ET.fromstring(data)
    out = []
    for it in (e for e in root.iter() if local(e.tag) in ("item", "entry")):
        raw = text_of(it, "description", "summary", "content", "encoded")
        title = clean(text_of(it, "title"))
        source = clean(text_of(it, "source")) or feed["name"]
        if source and title.endswith(" - " + source):
            title = title[: -len(source) - 3].strip()
        d = parse_date(text_of(it, "pubDate", "published", "updated", "date"))
        out.append({
            "title": title,
            "link": get_link(it),
            "summary": clean(raw)[:SUMMARY_LEN],
            "date": d,
            "source": source,
            "image": get_image(it, raw),
            "trusted": feed["trusted"],
        })
    return out

def is_somalia(it):
    hay = (it["title"] + " " + it["summary"]).lower()
    if any(k.lower() in hay for k in EXCLUDE): return False
    return it["trusted"] or any(k.lower() in hay for k in KEYWORDS)

def main():
    items = []
    for f in FEEDS:
        try:
            got = parse_feed(fetch(f["url"]), f)
            print(f"OK   {f['name']}: {len(got)} items")
            items += got
        except Exception as e:
            print(f"FAIL {f['name']}: {e}", file=sys.stderr)

    cutoff = datetime.now(timezone.utc) - timedelta(days=MAX_AGE_DAYS) if MAX_AGE_DAYS else None
    seen, kept = set(), []
    epoch = datetime.fromtimestamp(0, timezone.utc)
    for it in sorted(items, key=lambda i: i["date"] or epoch, reverse=True):
        if not it["title"] or not it["link"].startswith("http"): continue
        if not is_somalia(it): continue
        if cutoff and it["date"] and it["date"] < cutoff: continue
        key = re.sub(r"\W+", "", it["title"].lower())[:60]
        if key in seen: continue
        seen.add(key)
        kept.append(it)
        if len(kept) >= MAX_ITEMS: break

    if not kept and OUT.exists():
        print("No Somalia items found - keeping the existing news.json")
        return

    payload = {
        "updated": datetime.now(timezone.utc).isoformat(),
        "count": len(kept),
        "items": [{
            "title": i["title"], "link": i["link"], "summary": i["summary"],
            "date": i["date"].isoformat() if i["date"] else "",
            "source": i["source"], "image": i["image"],
        } for i in kept],
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(kept)} items to {OUT.name}")

if __name__ == "__main__":
    main()
