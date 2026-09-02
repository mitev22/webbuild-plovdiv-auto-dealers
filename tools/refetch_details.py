#!/usr/bin/env python3
"""Re-fetch each listing page and merge the richer fields (price, km, firstReg,
equipment, note, colour, body) into a dealer.json written by harvest_dealer.py.
Photos are not touched. Usage: refetch_details.py <dealer.json>"""
import json, re, ssl, sys, time, urllib.request
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36",
      "Referer": "https://www.mobile.bg/"}
ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
def get(url):
    for t in range(3):
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30, context=ctx).read().decode("windows-1251", errors="replace")
        except Exception:
            if t == 2: raise
            time.sleep(1.5)
FIELD_MAP = {"Дата на производство": "firstReg", "Пробег [км]": "km_raw", "Двигател": "fuel",
             "Скоростна кутия": "gearbox", "Мощност": "power", "Евростандарт": "euro",
             "Категория": "body", "Цвят": "colour"}
EXTRA_SECTIONS = ["Комфорт", "Безопасност", "Интериор", "Друго"]
def parse(html):
    car = {}
    flat = re.sub(r'<[^>]+>', ' ', html)
    pm = re.search(r'([\d][\d\s]{1,11})\s*(лв\.|EUR|€)', flat)
    if pm:
        car["price"] = int(re.sub(r'\s', '', pm.group(1))); car["currency"] = "лв." if "лв" in pm.group(2) else "€"
    text = re.sub(r'<[^>]+>', '\n', html)
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    for bg, key in FIELD_MAP.items():
        try: car[key] = lines[lines.index(bg) + 1]
        except (ValueError, IndexError): pass
    if "km_raw" in car:
        m = re.search(r'([\d\s]+)', car["km_raw"])
        if m: car["km"] = int(re.sub(r'\s', '', m.group(1)))
    eq, seen = [], set()
    for sec in EXTRA_SECTIONS:
        try: i = lines.index(sec)
        except ValueError: continue
        for l in lines[i + 1:i + 40]:
            if l in EXTRA_SECTIONS or len(l) > 60 or l in seen: break
            if re.match(r'^[А-Яа-яA-Za-z0-9]', l) and not l.startswith('Виж'):
                eq.append(l); seen.add(l)
    car["equipment"] = eq[:24]
    di = next((j for j, l in enumerate(lines) if 'Допълнителна информация' in l), None)
    if di is not None:
        desc = re.sub(r'\s+', ' ', ' '.join(lines[di + 1:di + 8])).strip()
        car["note_full"] = desc[:1200]
        if len(desc) > 260:
            cut = desc[:260].rsplit('.', 1)
            desc = (cut[0] + '.') if len(cut) > 1 and len(cut[0]) > 60 else desc[:260]
        car["note"] = desc
    return car
if __name__ == "__main__":
    p = sys.argv[1]; d = json.load(open(p))
    for i, c in enumerate(d["cars"]):
        try:
            c.update(parse(get(c["url"])))
            print(f"[{i+1}/{len(d['cars'])}] {c['title'][:40]:40s} {c.get('price')} {c.get('km')} {len(c.get('equipment',[]))}eq", flush=True)
        except Exception as e:
            print("FAIL", c["url"], e, flush=True)
        time.sleep(0.5)
    json.dump(d, open(p, "w"), ensure_ascii=False, indent=1)
    print("DONE")
