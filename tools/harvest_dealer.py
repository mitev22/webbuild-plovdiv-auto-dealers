#!/usr/bin/env python3
"""Harvest a dealer's own inventory (data + photos) from their mobile.bg subdomain.

Usage: harvest_dealer.py <host> [--max-cars N] [--out DIR]
Writes: <out>/<slug>/dealer.json + photos/<car-id>/NN.webp
Photos and data are the dealer's own public materials, used to build THEIR demo.
"""
import json, os, re, ssl, sys, time, urllib.request

UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36",
      "Referer": "https://www.mobile.bg/"}
ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE

def get(url, binary=False):
    req = urllib.request.Request(url, headers=UA)
    raw = urllib.request.urlopen(req, timeout=30, context=ctx).read()
    return raw if binary else raw.decode("windows-1251", errors="replace")

FIELD_MAP = {
    "Дата на производство": "year", "Пробег [км]": "mileage", "Двигател": "fuel",
    "Скоростна кутия": "gearbox", "Мощност": "power", "Евростандарт": "euro",
    "Категория": "category", "Цвят": "color", "Купе": "body",
}

def parse_listing(html, url):
    car = {"url": url}
    t = re.search(r'<h1[^>]*>(.*?)</h1>', html, re.S)
    if not t: t = re.search(r'<title>(.*?)(?:\s*-\s*обяви.*?)?</title>', html, re.S)
    car["title"] = re.sub(r'\s*Обява:.*$', '', re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', t.group(1))).strip()) if t else ""
    pm = re.search(r'([\d\s]{2,12})\s*(лв\.|EUR|€)', re.sub(r'<[^>]+>', ' ', html))
    car["price_raw"] = (pm.group(0).strip() if pm else "")
    text = re.sub(r'<[^>]+>', '\n', html)
    for bg, key in FIELD_MAP.items():
        m = re.search(re.escape(bg) + r'\s*\n+\s*([^\n]{1,60})', text)
        if m: car[key] = m.group(1).strip()
    dm = re.search(r'<div[^>]*class="[^"]*description[^"]*"[^>]*>(.*?)</div>', html, re.S | re.I)
    if dm:
        car["description"] = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', dm.group(1))).strip()[:2000]
    photos = []
    for p in re.findall(r'((?://|https://)[a-z0-9.]*focus\.bg/mobile/photosorg/[^"\'\s)]+\.webp)', html):
        if "/big1/" in p:
            photos.append("https:" + p if p.startswith("//") else p)
    car["photos"] = sorted(set(photos))
    return car

def harvest(host, max_cars=8, out_root="."):
    slug = host.split(".")[0].replace("_", "-")
    out = os.path.join(out_root, slug)
    os.makedirs(os.path.join(out, "photos"), exist_ok=True)
    home = get(f"https://{host}")
    dealer = {"host": host, "slug": slug}
    nm = re.search(r'<title>(.*?)(?:\s*-\s*обяви.*?)?</title>', home, re.S)
    dealer["title"] = nm.group(1).strip() if nm else host
    logo = re.search(r'(//cdn\d*\.focus\.bg/mobile/images/houseslogos/[^"\s]+)', home)
    if logo:
        dealer["logo_url"] = "https:" + logo.group(1)
        try:
            with open(os.path.join(out, "logo.pic"), "wb") as f:
                f.write(get(dealer["logo_url"], binary=True))
        except Exception: pass
    ht = re.sub(r'<[^>]+>', '\n', home)
    for label, key in [("Адрес", "address"), ("Телефон", "phone"), ("Работно време", "hours")]:
        m = re.search(re.escape(label) + r'[:\s]*\n*\s*([^\n]{1,120})', ht)
        if m: dealer[key] = m.group(1).strip()
    ads = []
    seen = set()
    skip_hint = int(sys.argv[sys.argv.index("--skip")+1]) if "--skip" in sys.argv else 0
    for page in range(1, 6):
        url = f"https://{host}" + ("" if page == 1 else f"/obiavi/avtomobili-dzhipove/p-{page}")
        try: h = home if page == 1 else get(url)
        except Exception: break
        page_ads = [a for a in re.findall(r'href="(https://[^"]+/obiava-[^"]+)"', h)]
        new = []
        for a in page_ads:
            if a not in seen and a not in new: new.append(a)
        if not new and page > 1: break
        for a in new: seen.add(a)
        ads.extend(new)
        if len(ads) >= (max_cars + skip_hint) * 2: break
        time.sleep(0.4)
    cars = []
    seen_ids = set()
    skip = int(sys.argv[sys.argv.index("--skip")+1]) if "--skip" in sys.argv else 0
    ads = ads[skip:]
    for ad in ads:
        if len(cars) >= max_cars: break
        aid = re.search(r'obiava-(\d+)', ad)
        if not aid or aid.group(1)[:13] in seen_ids: continue
        seen_ids.add(aid.group(1)[:13])
        try:
            car = parse_listing(get(ad), ad)
        except Exception as e:
            print(f"  skip {ad}: {e}"); continue
        cid = re.search(r'obiava-(\d+)', ad).group(1)
        car["id"] = cid
        pdir = os.path.join(out, "photos", cid)
        os.makedirs(pdir, exist_ok=True)
        saved = []
        for i, purl in enumerate(car["photos"][:18]):
            fp = os.path.join(pdir, f"{i:02d}.webp")
            try:
                with open(fp, "wb") as f: f.write(get(purl, binary=True))
                saved.append(os.path.basename(fp))
            except Exception: pass
            time.sleep(0.15)
        car["saved_photos"] = saved
        cars.append(car)
        print(f"  {car['title'][:50]:50s} {len(saved):2d} photos  {car.get('price_raw','')}")
        time.sleep(0.4)
    dealer["cars"] = cars
    with open(os.path.join(out, "dealer.json"), "w") as f:
        json.dump(dealer, f, ensure_ascii=False, indent=1)
    print(f"OK {slug}: {len(cars)} cars -> {out}")
    return dealer

if __name__ == "__main__":
    host = sys.argv[1]
    max_cars = int(sys.argv[sys.argv.index("--max-cars")+1]) if "--max-cars" in sys.argv else 8
    out = sys.argv[sys.argv.index("--out")+1] if "--out" in sys.argv else "."
    harvest(host, max_cars, out)
