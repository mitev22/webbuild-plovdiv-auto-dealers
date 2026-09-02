#!/usr/bin/env python3
"""Re-fetch a dealer's FULL car descriptions and rewrite their demo in place.

The original batch harvest stored only the first 260 characters of each mobile.bg
description, which cut most dealers off mid-sentence — usually right before the
paragraph that actually sells them ("we import from Central Europe, every car is
checked, we provide the VIN…").

This walks the description block line by line, which `clean_note` cannot do once
the text is joined, so it can drop three things a joined string hides:

  * the extras list ("*Антиблокираща система"), already shown in Оборудване;
  * the dealer's phone line, already in the header, the footer and the call bar;
  * the model headline sandwiched between two rule lines, which merely repeats
    the page's own h1 — and, when a dealer has copy-pasted a listing, contradicts
    it (maxcar's BMW X5 carries a MERCEDES-BENZ GLE350 headline).

Usage:  refetch_full_notes.py <slug> [<slug> ...] [--apply] [--max N]
Without --apply it prints what it would change and touches nothing.
"""
import json
import os
import re
import ssl
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from clean_note import clean_note

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HARVEST = os.path.expanduser("~/Desktop/web-agency/_harvest/plovdiv-auto-dealers")
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/128.0 Safari/537.36",
      "Referer": "https://www.mobile.bg/"}
CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE

STOP = re.compile(r'^(?:\*{0,3}\s*)(?:Екстри|Особености|Допълнително оборудване|'
                  r'Виж\s+вс[ия]чки\s+обяви|Контакти\s+с\s+продавача|Сподели|Принтирай)', re.I)
PHONE = re.compile(r'^\*{0,3}\s*(?:Тел|Телефон|GSM|Моб)\s*[:.]', re.I)
EXTRA = re.compile(r'^\*[^*\s]')            # "*Антиблокираща система"
RULE_LINE = re.compile(r'^[\s_\-=~.*]{4,}$')  # a divider line and nothing else
MAX_NOTE = 520


def get(url, tries=3):
    for t in range(tries):
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers=UA),
                                          timeout=30, context=CTX).read().decode("windows-1251",
                                                                                 errors="replace")
        except Exception:
            if t == tries - 1:
                raise
            time.sleep(1.5)


def description_lines(html_text):
    lines = [l.strip() for l in re.sub(r'<[^>]+>', '\n', html_text).split('\n') if l.strip()]
    i = next((j for j, l in enumerate(lines) if 'Допълнителна информация' in l), None)
    if i is None:
        return []
    out = []
    for l in lines[i + 1:i + 80]:
        if STOP.search(l) or EXTRA.match(l):
            break
        out.append(l)
    return out


def assemble(lines):
    """Drop furniture, then join. Rule lines become sentence breaks in clean_note."""
    keep = []
    for k, l in enumerate(lines):
        if PHONE.match(l):
            continue
        if RULE_LINE.match(l):
            keep.append(".")              # a divider is a sentence break
            continue
        prev_rule = k > 0 and RULE_LINE.match(lines[k - 1])
        next_rule = k + 1 < len(lines) and RULE_LINE.match(lines[k + 1])
        if prev_rule and next_rule:
            continue                      # the repeated model headline
        keep.append(l)
    return " ".join(keep)


def full_note(url):
    return clean_note(assemble(description_lines(get(url))), max_chars=MAX_NOTE)


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def run(slug, apply_it, limit=None):
    dpath = os.path.join(HARVEST, slug, "dealer.json")
    cpath = os.path.join(REPO, "configs", slug, "template.config.mjs")
    if not (os.path.exists(dpath) and os.path.exists(cpath)):
        print(f"  {slug}: no harvest or config, skipped")
        return 0
    dealer = json.load(open(dpath))
    cfg = json.loads(open(cpath).read()[len("export default "):].rstrip().rstrip(";"))
    by_url = {c["url"]: c for c in dealer["cars"]}
    # stock[] follows dealer.json order but gen_config drops cars with no price, no
    # mileage or no year, so position is not a safe key -- a sold listing in the middle
    # shifts everything after it. Pair on the title instead, and refuse anything
    # ambiguous: attaching one car's description to another car's page is far worse
    # than leaving a stale note.
    def key(t):
        # gen_config truncates titles at 58 chars, so compare just inside that. 28 was
        # too short: two Jeep Grand Cherokees differing only after "SUMMIT= " collided.
        return re.sub(r'\s+', ' ', t).strip()[:52].lower()
    buckets = {}
    for car in dealer["cars"]:
        buckets.setdefault(key(car["title"]), []).append(car)
    pairs, used = [], set()
    for entry in cfg["stock"]:
        cands = [c for c in buckets.get(key(entry["title"]), []) if id(c) not in used]
        if len(cands) != 1:
            print(f"  {slug}/{entry['id']}: no unique harvest match, skipped "
                  f"({len(cands)} candidates) -- {entry['title'][:50]}")
            continue
        used.add(id(cands[0]))
        pairs.append((entry, cands[0]))
    changed = 0
    for entry, car in pairs:
        if limit and changed >= limit:
            break
        try:
            new = full_note(car["url"])
        except Exception as e:
            print(f"  {slug}/{entry['id']}: fetch failed: {e}")
            continue
        old = entry.get("note", "")
        if new and new != old:
            changed += 1
            print(f"  {slug}/{entry['id']} {entry['title'][:34]:34s} {len(old):3d} -> {len(new):3d}")
            if apply_it:
                entry["note"] = new
                by_url[car["url"]]["note"] = new
                f = os.path.join(REPO, "sites", slug, f"avtomobil-{entry['id']}.html")
                if os.path.exists(f):
                    h = open(f, encoding="utf8").read()
                    h2 = re.sub(r'<p class="sub">.*?</p>',
                                lambda m: f'<p class="sub">{esc(new)}</p>', h, count=1, flags=re.S)
                    open(f, "w", encoding="utf8").write(h2)
        time.sleep(0.4)
    if apply_it and changed:
        open(cpath, "w", encoding="utf8").write(
            "export default " + json.dumps(cfg, ensure_ascii=False, indent=1) + ";\n")
        json.dump(dealer, open(dpath, "w"), ensure_ascii=False, indent=1)
    return changed


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    apply_it = "--apply" in sys.argv
    total = 0
    for slug in args:
        print(f"== {slug}")
        total += run(slug, apply_it)
    print(f"{total} descriptions {'rewritten' if apply_it else 'would change'}")
