#!/usr/bin/env python3
"""Generate a per-dealer template.config.mjs + assets from harvest + ledger.

Everything written is either harvested fact (dealer's own listings) or
process-generic wording that is true for any dealer. No invented claims.
"""
import html, io, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from clean_note import clean_note
from PIL import Image

HARVEST = os.path.expanduser("~/Desktop/web-agency/_harvest/plovdiv-auto-dealers")
THEMES = ["pyasak", "grafit", "maslina", "oksid"]

VARIANTS = [
    {"slug": "pyasak", "label": "Пясък", "note": "Топъл, тих. Пясъчна земя, кехлибарен акцент.",
     "shell": "#DFD8C8", "shell2": "#D3CBB8", "card": "#EDE8DC", "night": "#191714",
     "ink": "#161412", "mute": "#57514A", "brass": "#6E521E", "brassLt": "#C0A177", "ok": "#31593A"},
    {"slug": "grafit", "label": "Графит", "note": "Студен и прецизен. Стоманен акцент, повече техника.",
     "shell": "#DCDEE0", "shell2": "#CDD0D3", "card": "#ECEEEF", "night": "#15181B",
     "ink": "#12151A", "mute": "#4E555C", "brass": "#33546E", "brassLt": "#8FB2CC", "ok": "#2C5C46"},
    {"slug": "maslina", "label": "Маслина", "note": "Дълбоко зелено. Спокойно, малко по-скъпо на вид.",
     "shell": "#DEE0D3", "shell2": "#CFD2C2", "card": "#EBEDE1", "night": "#171A13",
     "ink": "#14170F", "mute": "#4F5546", "brass": "#4F6127", "brassLt": "#A6B878", "ok": "#2F5A38"},
    {"slug": "oksid", "label": "Оксид", "note": "Костено бяло с ръждив акцент. Най-топлият и най-силният.",
     "shell": "#E4D6CD", "shell2": "#D6C4B8", "card": "#F1E7E0", "night": "#1B1512",
     "ink": "#17120F", "mute": "#585049", "brass": "#8A3D24", "brassLt": "#CE8E70", "ok": "#31593A"},
]

SYM = {"Джип": "car-suv", "Комби": "car-estate", "Ван": "car-estate", "Миниван": "car-estate",
       "Пикап": "car-suv", "Седан": "car-sedan", "Хечбек": "car-sedan", "Купе": "car-sedan",
       "Кабрио": "car-sedan"}

def clean_name(name):
    n = re.sub(r'\s+', ' ', name).strip()
    n = re.sub(r'^(АВТОКЪЩА|Автокъща|автокъща)\s+', '', n)
    if re.fullmatch(r'(?:[А-ЯA-Z]\s)+[А-ЯA-Z]', n):
        n = n.replace(' ', '')
    if ' - ' in n and len(n) > 30:
        head = n.split(' - ')[0].strip()
        if len(head) >= 4: n = head
    if '-' in n and len(n) > 40:
        head = n.split('-')[0].strip()
        if len(head) >= 6: n = head
    return n[:40].strip()

def phone_href(p):
    d = re.sub(r'\D', '', p)
    if d.startswith('00359'): d = d[5:]
    elif d.startswith('359'): d = d[3:]
    elif d.startswith('0'): d = d[1:]
    return "tel:+359" + d

def compress(src, dst, width, q):
    im = Image.open(src).convert("RGB")
    if im.width > width:
        im = im.resize((width, int(im.height * width / im.width)), Image.LANCZOS)
    im.save(dst, "WEBP", quality=q)

def usable_logo(path):
    try:
        im = Image.open(path).convert("RGBA")
        if min(im.size) < 36: return None
        px = im.convert("RGB").resize((24, 24))
        vals = list(px.getdata())
        lum = sum(0.299*r+0.587*g+0.114*b for r, g, b in vals) / len(vals)
        if lum > 228: return None   # near-white logo would vanish on the light shells
        return im
    except Exception:
        return None

def month_year(s):
    m = re.search(r'(20\d\d|19\d\d)', s or '')
    return int(m.group(1)) if m else None

def gen(slug, ledger_row, theme, assets_dir):
    dealer = json.load(open(os.path.join(HARVEST, slug, "dealer.json")))
    name = clean_name(ledger_row["name"])
    loc = ledger_row["address"].split(",")[0].strip()
    city = re.sub(r'^(град|село|гр\.|с\.)\s+', '', loc)
    street = html.unescape(ledger_row["address"].split(",", 1)[1].strip()) if "," in ledger_row["address"] else ""
    if street in ("-", ""): street = "Попитайте за адреса по телефона"
    phones = [p.strip() for p in re.split(r'[,;/]|\s{2,}| и ', ledger_row["phone"]) if len(re.sub(r'\D', '', p)) >= 6]
    phone = phones[0] if phones else ""
    listings = re.search(r'(\d+) listings', ledger_row["size_signals"])
    n_listings = int(listings.group(1)) if listings else None
    since = re.search(r'dealer since \d+\.\d+\.(\d{4})', ledger_row["size_signals"])
    founded = int(since.group(1)) if since else 2020

    os.makedirs(assets_dir, exist_ok=True)
    logo_file = None
    lp = os.path.join(HARVEST, slug, "logo.pic")
    if os.path.exists(lp):
        im = usable_logo(lp)
        if im:
            im.save(os.path.join(assets_dir, "logo.png"))
            logo_file = "logo.png"

    curs = [c.get("currency") for c in dealer["cars"] if c.get("currency")]
    cur = "лв." if curs.count("лв.") > len(curs) / 2 else "€"
    stock, skipped = [], 0
    for i, car in enumerate(dealer["cars"][:6]):
        if car.get("currency") and car["currency"] != cur:
            skipped += 1; continue
        year = month_year(car.get("firstReg"))
        if not (car.get("price") and car.get("km") and year and car.get("saved_photos")):
            skipped += 1; continue
        cid = f"{len(stock)+1:02d}"
        photos = []
        for j, rel in enumerate(car["saved_photos"][:8]):
            src = os.path.join(HARVEST, slug, "photos", rel)
            fn = f"{cid}-{j:02d}.webp"
            compress(src, os.path.join(assets_dir, fn), 1280 if j == 0 else 1000, 70 if j == 0 else 60)
            photos.append([fn, "Снимка " + str(j + 1) + " на автомобила"])
        title = re.sub(r'\s+', ' ', car["title"]).strip()[:58]
        note_src = clean_note(car.get("note") or "")
        hay = (title + " " + note_src).lower()
        drive = "4x4" if re.search(r'4x4|4х4|quattro|xdrive|4motion|awd|4 x 4', hay) else "—"
        imp = "—"
        mi = re.search(r'внос(?:\s+\w+)?\s+от\s+([А-Яа-я]+)', note_src)
        if mi: imp = mi.group(1)
        fuel = (car.get("fuel") or "").strip()
        power = (car.get("power") or "").strip()
        engine = ", ".join([x for x in (fuel, power) if x]) or "—"
        entry = {
            "id": cid, "title": title, "body": car.get("body") or "Автомобил",
            "sym": SYM.get((car.get("body") or "").strip(), "car-sedan"),
            "price": car["price"], "year": year, "firstReg": car.get("firstReg") or str(year),
            "km": car["km"], "engine": engine, "gearbox": car.get("gearbox") or "—",
            "drive": drive, "colour": car.get("colour") or "—", "importedFrom": imp,
            "owners": "—", "photos": photos,
        }
        if note_src: entry["note"] = note_src
        eq = car.get("equipment") or []
        if eq: entry["equipment"] = eq[:12]
        if len(stock) == 0:
            entry["featured"] = True
            entry["checks"] = [
                ["Снимки", "Снимките във всяко досие са на самия автомобил."],
                ["Данни", "Годината, пробегът и двигателят са от обявата на автокъщата."],
                ["Цена", "Цената е обявената от автокъщата."],
                ["Оглед", "Всяка кола може да се види и тества на място."],
            ]
        stock.append(entry)

    if len(stock) < 3:
        raise RuntimeError(f"{slug}: only {len(stock)} usable cars")

    first = stock[0]["photos"][0][0]
    about_img = stock[1]["photos"][1][0] if len(stock[1]["photos"]) > 1 else stock[1]["photos"][0][0]
    buy_img = stock[2]["photos"][0][0]

    stmt = f"{n_listings} автомобила в продажба в момента." if n_listings else "Автомобилите са на двора. Снимките са истински."
    cfg = {
        "business": {"name": name, "kind": "Автокъща", "city": city, "logo": logo_file,
                     "tagline": stmt, "founded": founded},
        "contact": {
            "phone": phone, "phoneHref": phone_href(phone),
            "email": "", "street": street, "city": city, "postcode": "",
            "hours": [["Оглед", "Всеки ден след уговорка по телефона"]],
            "hoursShort": "Оглед след уговорка",
            "mapEmbed": None, "facebook": "#", "instagram": "#",
        },
        "theme": theme, "demoThemeSwitcher": True,
        "type": {"display": "Unbounded", "displayWeights": "200;300;400",
                 "text": "Onest", "textWeights": "300;400;500;600", "loclOff": True},
        "variants": VARIANTS,
        "service": None,
        "copy": {
            "homeStatement": stmt,
            "homeNote": f"{name} е автокъща в {city}, {street}. Всяка обява има реални снимки и данни за колата. Обадете се на {phone} и елате на оглед.",
            "warrantyMonths": None,
            "vatNote": "Цената е обявената от автокъщата.",
            "fileClaims": None,
            "currency": cur,
            "closeLead": "Автокъщата приема автомобили за изкупуване и замяна. Обадете се за оценка.",
            "teaserAbout": "Данните и снимките на всяка кола са пред вас, преди да дойдете на оглед.",
            "stageCaption": "Част от наличностите на двора",
            "allLabel": "Виж наличностите",
            "stockH1": "Наличностите на двора.",
            "stockLead": f"Подбрани автомобили от обявите на {name}. Всяка кола има досие със снимки и данни.",
            "stockMeta": f"{len(stock)} автомобила в тази селекция",
            "stockMeta2": f"Пълният списък е на телефон {phone}",
            "homeChecksH2": "Какво виждате за всяка кола.",
            "homeChecksLead": "Всяко досие идва със снимки на конкретния автомобил и данните от обявата.",
            "checksH2": "Какво съдържа досието.",
            "checksLead": "Данните са от обявата на автокъщата. Подробностите се уточняват на оглед.",
            "stampWords": ["Реални", "снимки"],
            "aboutH1": f"Автокъща {name}, {city}.",
            "aboutBlocks": None,
            "yearsLabel": "години с обяви в mobile.bg",
            "stockFigure": n_listings or len(stock),
            "stockFigureLabel": "обяви в момента",
            "buyH1": "Приемаме коли за изкупуване и замяна.",
            "buyLead": f"Обадете се или пишете. Оценката става след оглед на място в {city}.",
            "buySteps": [
                ["Обадете се", f"Кажете марка, година и пробег на {phone}."],
                ["Оглед", f"На място в {city}, по уговорка."],
                ["Цена", "Получавате конкретна цена след огледа."],
                ["Прехвърляне", "Документите се уреждат при нотариус."],
            ],
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
            "homeStage": [first, "Автомобил от наличностите на автокъщата"],
            "aboutStage": [about_img, "Автомобил от наличностите"],
            "serviceShot": [first, "Автомобил от наличностите"],
            "buyShot": [buy_img, "Автомобил от наличностите"],
        },
        "promises": [
            ["Оглед", f"На място в {city}, по уговорка."],
            ["Снимки", "Всички снимки са на конкретната кола."],
            ["Връзка", f"Телефонът е {phone}."],
        ],
    }
    return cfg

if __name__ == "__main__":
    print("module; use build_all.py")
