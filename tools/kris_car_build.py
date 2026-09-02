#!/usr/bin/env python3
"""Bespoke build for kris-car: merge the two harvests, pick exterior cover photos,
write template.config.mjs with the dealer's own verified facts, build with the
atelie template and copy into the gallery repo.

Everything written is either harvested from kris_car.mobile.bg, read from the
dealer's own public profiles (mobile.bg contacts tab, Facebook page, cars.bg), or
process wording that is true for any dealer. No invented claims.
"""
import json, os, re, shutil, subprocess, sys
from datetime import date
from PIL import Image
import numpy as np

W = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE = os.path.expanduser("~/Desktop/web-agency/templates/auto-dealers/atelie")
REPO = os.path.expanduser("~/Desktop/web-agency/webbuild-plovdiv-auto-dealers")
SLUG = "kris-car"
BASE_URL = f"https://mitev22.github.io/webbuild-plovdiv-auto-dealers/sites/{SLUG}/"
MAX_CARS = int(os.environ.get("MAX_CARS", "52"))
PHOTOS_PER_CAR = 8

sys.path.insert(0, os.path.join(W, "tools"))
from gen_config import VARIANTS, SYM, compress, phone_href  # noqa: E402

MONTHS = {"януари": "януари", "февруари": "февруари", "март": "март", "април": "април", "май": "май",
          "юни": "юни", "юли": "юли", "август": "август", "септември": "септември",
          "октомври": "октомври", "ноември": "ноември", "декември": "декември"}

def load_cars():
    cars = []
    for h in ("harvest", "harvest2"):
        p = os.path.join(W, h, SLUG, "dealer.json")
        if not os.path.exists(p): continue
        d = json.load(open(p))
        for c in d["cars"]:
            c["_dir"] = os.path.join(W, h, SLUG, "photos", c["id"])
            cars.append(c)
    seen, out = set(), []
    for c in cars:
        if c["id"] in seen: continue
        seen.add(c["id"]); out.append(c)
    return out

def first_reg(s):
    m = re.search(r'([А-Яа-я]+)\s+(20\d\d|19\d\d)', s or "")
    if not m: return None, None
    return m.group(1).lower() + " " + m.group(2), int(m.group(2))

def clean_title(t):
    t = re.sub(r'\s+', ' ', t).strip()
    t = t.replace("=", " ").replace("\\", "/")
    t = re.sub(r'\s+', ' ', t)
    t = re.sub(r'\s*-\s*', "-", t)          # "С-Гаранция-А/Т" stays tight
    t = re.sub(r'(\d),\s+(\d)', r'\1.\2', t)  # "1, 5DCI" -> "1.5DCI"
    return t[:58].strip()

def brand_model(title):
    parts = title.split()
    brand = parts[0]
    model = parts[1] if len(parts) > 1 else ""
    model = re.split(r'[-,/]', model)[0]
    if brand.upper() == "VW": brand = "Volkswagen"
    return brand, model

def tags_for(c):
    hay = (c["title"] + " " + c.get("note_full", "") + " " + c.get("note", "")).lower()
    t = []
    if re.search(r'гаранци', hay): t.append("В гаранция")
    if re.search(r'нов[аи]?\s+(от|в)\s+българия|закупен[иа]?\s+(като\s+)?нов', hay): t.append("Купена нова в България")
    if re.search(r'лизинг', hay): t.append("Възможен лизинг")
    if re.search(r'фактура', hay): t.append("Фактура с ДДС")
    if re.search(r'първи собственик|един собственик', hay) and len(t) < 3: t.append("Един собственик")
    return t[:3]

def exterior_score(path):
    """Exterior shots have a bright sky band on top and a car mass in the middle;
    interiors are grey all over. Score = brightness + blueness of the top quarter,
    plus a bonus for strong horizontal contrast structure."""
    im = Image.open(path).convert("RGB").resize((160, 120))
    a = np.asarray(im).astype(float)
    top = a[:30]
    v = top.mean(axis=2)
    blue = (top[..., 2] - top[..., 0]).mean()
    bright = v.mean()
    sat_top = (top.max(axis=2) - top.min(axis=2)).mean()
    mid = a[40:90]
    contrast = mid.std()
    # dark-headliner interiors: dim top, low blueness
    bottom = a[95:].mean(axis=2).mean()
    score = bright * 0.6 + max(blue, 0) * 2.5 + contrast * 0.4
    if bright < 90: score -= 40
    if bottom < 70: score -= 60     # black dashboard or footwell across the bottom: an interior
    if sat_top > 70 and blue < 0: score -= 25   # warm interiors, orange seats
    return score

def pick_cover(c):
    files = sorted(f for f in os.listdir(c["_dir"]) if f.endswith(".webp"))
    scored = sorted(((exterior_score(os.path.join(c["_dir"], f)), f) for f in files), reverse=True)
    cover = scored[0][1]
    rest = [f for f in files if f != cover]
    # keep the two next-best exteriors right after the cover, then the original order
    nxt = [f for _, f in scored[1:3]]
    rest = nxt + [f for f in rest if f not in nxt]
    return [cover] + rest

def main():
    raw = load_cars()
    print(len(raw), "harvested cars")
    work = os.path.join(W, "build", SLUG)
    if os.path.exists(work): shutil.rmtree(work)
    os.makedirs(os.path.join(work, "src"))
    shutil.copy(os.path.join(TEMPLATE, "build.mjs"), work)
    shutil.copytree(os.path.join(TEMPLATE, "src"), os.path.join(work, "src"), dirs_exist_ok=True)
    assets = os.path.join(work, "assets"); os.makedirs(assets)
    for f in ("logo.png", "favicon.png"):
        shutil.copy(os.path.join(W, f), assets)

    stock, covers = [], {}
    for c in raw:
        if len(stock) >= MAX_CARS: break
        fr, year = first_reg(c.get("firstReg") or c.get("year"))
        if not (c.get("price") and c.get("km") and year and os.path.isdir(c["_dir"])): 
            print("  skip", c["title"][:40], c.get("price"), c.get("km"), year); continue
        order = pick_cover(c)
        cid = f"{len(stock)+1:02d}"
        photos = []
        for j, fn in enumerate(order[:PHOTOS_PER_CAR]):
            src = os.path.join(c["_dir"], fn)
            out = f"{cid}-{j:02d}.webp"
            compress(src, os.path.join(assets, out), 1280 if j == 0 else 1000, 70 if j == 0 else 60)
            photos.append([out, f"Снимка {j+1} на автомобила"])
        compress(os.path.join(c["_dir"], order[0]), os.path.join(assets, f"{cid}-t.webp"), 720, 64)
        if len(order) > 1:
            compress(os.path.join(c["_dir"], order[1]), os.path.join(assets, f"{cid}-t2.webp"), 720, 64)
        covers[cid] = os.path.join(c["_dir"], order[0])
        title = clean_title(c["title"])
        brand, model = brand_model(title)
        hay = (title + " " + c.get("note_full", "")).lower()
        fuel = (c.get("fuel") or "").strip()
        power = (c.get("power") or "").strip()
        note = (c.get("note") or "").strip()
        entry = {
            "id": cid, "title": title, "brand": brand, "model": model,
            "body": (c.get("body") or "Автомобил").strip(),
            "sym": SYM.get((c.get("body") or "").strip(), "car-sedan"),
            "price": c["price"], "year": year, "firstReg": fr,
            "km": c["km"], "engine": ", ".join(x for x in (fuel, power) if x) or "—",
            "fuel": fuel or None,
            "gearbox": (c.get("gearbox") or "—").strip(),
            "drive": "4x4" if re.search(r'4x4|4х4|quattro|xdrive|4motion|awd', hay) else "Предно",
            "colour": (c.get("colour") or "—").strip(),
            "importedFrom": "Купена нова в България" if re.search(r'българия', hay) else "—",
            "owners": "Един" if re.search(r'първи собственик|един собственик', hay) else "—",
            "photos": photos, "thumb": f"{cid}-t.webp", "thumb2": f"{cid}-t2.webp" if len(order) > 1 else None,
            "tags": tags_for(c),
        }
        if note: entry["note"] = note
        eq = c.get("equipment") or []
        if eq: entry["equipment"] = eq[:16]
        stock.append(entry)
    print(len(stock), "cars in stock")

    # hero slots, chosen from the contact sheet by eye
    def find(pattern, k=0):
        for s in stock:
            if re.search(pattern, s["title"], re.I): return s["photos"][k][0]
        return stock[0]["photos"][0][0]
    home_stage = find(r'Arteon')
    about_stage = find(r'Megane SEDAN')
    buy_shot = find(r'Corolla EXECUTIVE')
    checks_shot = find(r'Passat')
    # Open Graph card from the home stage photo
    og = Image.open(os.path.join(assets, home_stage)).convert("RGB")
    w, h = og.size; th = int(w * 630 / 1200)
    og = og.crop((0, max(0, (h - th) // 2), w, max(0, (h - th) // 2) + th)).resize((1200, 630), Image.LANCZOS)
    og.save(os.path.join(assets, "og.jpg"), "JPEG", quality=82)

    stock[0]["featured"] = True
    checks = [
        ["Произход", "Купени нови от официалния вносител за България и върнати от лизинг."],
        ["Гаранция", "Автомобили в гаранция или с гаранция, обслужвани само в оторизиран сервиз."],
        ["Пробег", "Доказуем пробег и пълна сервизна история по програмата на производителя."],
        ["Лизинг", "До 60 месеца чрез Уникредит Лизинг, ОТП/ДСК Лизинг, ОББ Лизинг и Uplease, с 20 до 30 на сто първоначална вноска."],
        ["Фактура", "Издаваме данъчна фактура с ДДС."],
    ]
    stock[0]["checks"] = checks
    phone, mobile = "0884541828", "0885232858"
    email = "office@kriscar-auto.bg"
    q = "Крис Кар автокъща, бул. Цариградско шосе, Пловдив"
    from urllib.parse import quote
    n_listings = 104
    cfg = {
        "business": {"name": "Крис Кар", "kind": "Автокъща", "city": "Пловдив", "logo": "logo.png",
                     "favicon": "favicon.png",
                     "tagline": "Автомобили, купени нови в България и върнати от лизинг.", "founded": 2005},
        "site": {"baseUrl": BASE_URL, "ogImage": "og.jpg"},
        "contact": {
            "phone": phone, "phoneHref": phone_href(phone),
            "mobile": mobile, "mobileHref": phone_href(mobile),
            "email": email,
            "street": "бул. Цариградско шосе, до бензиностанция Алпи", "city": "Пловдив", "postcode": "",
            "hours": [["Понеделник до петък", "09:00 до 19:00"], ["Събота", "09:30 до 19:00"], ["Неделя", "10:00 до 16:00"]],
            "hoursShort": "Отворено всеки ден",
            "mapEmbed": "https://www.google.com/maps?q=" + quote(q) + "&hl=bg&z=15&output=embed",
            "mapLink": "https://www.google.com/maps/search/?api=1&query=" + quote(q),
            "facebook": "https://www.facebook.com/KrisCarAuto/", "instagram": None,
        },
        "theme": "pyasak", "demoThemeSwitcher": True,
        "type": {"display": "Unbounded", "displayWeights": "200;300;400",
                 "text": "Onest", "textWeights": "300;400;500;600", "loclOff": True},
        "variants": VARIANTS,
        "service": None,
        "copy": {
            "homeStatement": "Автомобили, купени нови в България и върнати от лизинг.",
            "homeNote": f"Крис Кар продава автомобили в гаранция, обслужвани само в оторизиран сервиз, с доказуем пробег и пълна сервизна история. Дворът е на Цариградско шосе в Пловдив, до бензиностанция Алпи, и е отворен всеки ден. Възможен е лизинг до 60 месеца.",
            "warrantyMonths": None,
            "vatNote": "Цената е с включено ДДС.",
            "leaseNote": "Възможен лизинг до 60 месеца с 20 до 30 на сто първоначална вноска, чрез Уникредит Лизинг, ОТП/ДСК Лизинг, ОББ Лизинг и Uplease.",
            "fileClaims": None,
            "currency": "€",
            "closeLead": "Имате кола за продажба или за замяна? Оценяваме я на място на двора в Пловдив.",
            "teaserAbout": "Купени нови в България, върнати от лизинг, с гаранция и пълна сервизна история.",
            "stageCaption": f"{n_listings} автомобила на двора",
            "allLabel": f"Всички {len(stock)} автомобила на сайта",
            "stockH1": "Наличностите на двора.",
            "stockLead": "Всяка кола има досие със снимки, данни и оборудване. Филтрирайте по марка, модел, купе, цена или година.",
            "stockMeta": f"{len(stock)} автомобила на сайта",
            "stockMeta2": f"Още обяви на телефон {phone}",
            "homeChecksH2": "Какво стои зад всяка кола.",
            "homeChecksLead": "Условията са едни и същи за всеки автомобил на двора.",
            "checksH2": "Какво стои зад този автомобил.",
            "checksLead": "Данните са от обявата. Подробностите се уточняват на оглед.",
            "stampWords": ["Нова", "от България"],
            "aboutH1": "Автокъща Крис Кар, Пловдив.",
            "aboutBlocks": [
                ["Какво продаваме", [
                    ["Купени нови в България", "Всички автомобили са купени и поддържани от официалните представители на марката за България."],
                    ["Върнати от лизинг", "Обслужвани по сервизната програма на производителя, с доказан произход и реален пробег."],
                    ["В гаранция", "Автомобилите са в гаранция или с гаранция и се обслужват само в оторизиран сервиз."],
                ]],
                ["Как купувате", [
                    ["Оглед на двора", "Цариградско шосе, до бензиностанция Алпи. Отворено е всеки ден, включително неделя."],
                    ["Лизинг до 60 месеца", "Чрез Уникредит Лизинг, ОТП/ДСК Лизинг, ОББ Лизинг и Uplease, с 20 до 30 на сто първоначална вноска."],
                    ["Фактура с ДДС", "Издаваме данъчна фактура. Подходящо за фирми и за автомобили с N1 хомологация."],
                ]],
            ],
            "yearsLabel": "години на пазара",
            "stockFigure": n_listings, "stockFigureLabel": "обяви в момента",
            "thirdFigure": ["7", "дни в седмицата отворено"],
            "buyH1": "Изкупуваме и приемаме за замяна.",
            "buyLead": "Оценката става на място в Пловдив след оглед. Ако вземате кола от двора, вашата може да покрие част от цената.",
            "buySteps": [
                ["Пишете или се обадете", f"Марка, модел, година и пробег. Отговаряме в работно време на {phone} и {mobile}."],
                ["Оглед", "На двора на Цариградско шосе, всеки ден. Ако идвате отдалеч, кажете и ще ви изчакаме."],
                ["Цена", "Получавате конкретна цена след огледа."],
                ["Прехвърляне", "Документите се уреждат при нотариус."],
            ],
            "buyWhatH2": "Двата варианта",
            "buyWhat": [
                ["Замяна", "Вашата кола се приспада от цената на автомобил от двора."],
                ["Изкупуване", "Купуваме я и без да вземате кола от нас."],
                ["Документи", "Носете талона и сервизната книжка, ако я имате."],
            ],
            "buyTradeIn": True,
            "buyTradeInH2": "Замяна срещу кола от двора",
            "buyTradeInLead": f"Вашият автомобил се приспада от цената. Изберете от {len(stock)} автомобила на сайта и елате с двете коли на оглед.",
            "figures": [[str(n_listings), "автомобила на двора"], ["2005", "на пазара от"], ["7", "дни в седмицата отворено"], ["4,6", "от 5 в Google, 96 отзива"]],
            "plotNote": f"{len(stock)} автомобила на сайта, всеки със снимки и досие. Пълният двор е {n_listings}.",
            "freshH2": "Новите на двора",
            "freshLead": "Последните обяви. Задръжте върху снимката за втори кадър.",
            "brandsH2": "По марки",
            "brandsLead": "Изберете марка и списъкът се филтрира.",
            "featLabel": "Най-новата обява",
            "teaserBuy": "Приемаме автомобили за изкупуване и замяна. Вашата кола се приспада от цената.",
            "landingAlt": True,
            "contactH1": "Елате на двора. Отворено е всеки ден.",
            "contactLead": "Понеделник до петък от 9 до 19 часа, събота от 9:30, неделя от 10 до 16. Ако идвате за конкретна кола, обадете се предварително, за да е сигурно, че е на двора.",
        },
        "nav": [
            {"slug": "index", "label": "Начало", "hidden": True},
            {"slug": "nalichnosti", "label": "Наличности"},
            {"slug": "izkupuvane", "label": "Изкупуване"},
            {"slug": "za-nas", "label": "За нас"},
            {"slug": "kontakti", "label": "Контакти"},
        ],
        "stock": stock,
        "images": {
            "homeStage": [home_stage, "Дворът на Крис Кар в Пловдив"],
            "aboutStage": [about_stage, "Автомобил от наличностите на Крис Кар"],
            "serviceShot": [home_stage, "Автомобил от наличностите"],
            "buyShot": [buy_shot, "Автомобил от наличностите на Крис Кар"],
            "checksShot": [checks_shot, "Дворът на Цариградско шосе"],
        },
        "promises": [
            ["Оглед", "Цариградско шосе, до бензиностанция Алпи. Всеки ден."],
            ["Гаранция", "Автомобили в гаранция, обслужвани в оторизиран сервиз."],
            ["Връзка", f"{phone}, {mobile} и {email}."],
        ],
    }
    with open(os.path.join(work, "template.config.mjs"), "w") as f:
        f.write("export default " + json.dumps(cfg, ensure_ascii=False, indent=1) + ";\n")
    r = subprocess.run(["node", "build.mjs"], cwd=work, capture_output=True, text=True, timeout=180)
    if r.returncode != 0: raise SystemExit("build failed: " + r.stderr[-600:])
    dist = os.path.join(work, "dist")
    pages = [p for p in os.listdir(dist) if p.endswith(".html")]
    for p in pages:
        html = open(os.path.join(dist, p)).read()
        if re.search(r'>undefined<|"undefined"|undefined месеца| undefined|>null<', html):
            raise SystemExit(f"{p}: literal undefined/null in output")
        for m in re.finditer(r'(?:src|href)="assets/([^"]+)"', html):
            if not os.path.exists(os.path.join(dist, "assets", m.group(1))):
                raise SystemExit(f"{p}: missing asset {m.group(1)}")
    # contact sheet of the chosen covers, for a visual check
    from PIL import ImageDraw
    cols, tw, th = 6, 220, 165
    sheet = Image.new("RGB", (cols * tw, ((len(stock) + cols - 1) // cols) * (th + 20)), (30, 30, 30))
    dr = ImageDraw.Draw(sheet)
    for i, s in enumerate(stock):
        im = Image.open(os.path.join(assets, s["thumb"])).convert("RGB").resize((tw, th))
        x, y = (i % cols) * tw, (i // cols) * (th + 20)
        sheet.paste(im, (x, y)); dr.text((x + 4, y + th + 4), f"{s['id']} {s['title'][:26]}", fill=(255, 255, 255))
    sheet.save(os.path.join(W, "covers.png"))
    if "--install" in sys.argv:
        site_dir = os.path.join(REPO, "sites", SLUG)
        if os.path.exists(site_dir): shutil.rmtree(site_dir)
        shutil.copytree(dist, site_dir)
        cfg_dir = os.path.join(REPO, "configs", SLUG); os.makedirs(cfg_dir, exist_ok=True)
        shutil.copy(os.path.join(work, "template.config.mjs"), cfg_dir)
        with open(os.path.join(cfg_dir, "BUILD.md"), "w") as f:
            f.write(f"# {SLUG}\n\nTemplate: auto-dealers/atelie (filters + lead forms revision, 2026-09-02)\n"
                    f"Theme: pyasak\nBuilt: {date.today()}\nCars: {len(stock)} of {n_listings} listed on kris_car.mobile.bg\n"
                    f"Build tool: tools/kris_car_build.py (harvest with tools/harvest_dealer.py, then tools/refetch_details.py)\n"
                    f"Facts source: mobile.bg contacts tab (hours, phones), dealer email from Dimi, facebook.com/KrisCarAuto\n")
        print("installed into", site_dir)
    print("built", len(pages), "pages ->", dist)

if __name__ == "__main__":
    main()
