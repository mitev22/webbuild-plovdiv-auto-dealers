#!/usr/bin/env python3
"""Clean a car description harvested from a mobile.bg listing.

Dealers type their descriptions into mobile.bg by hand, so the raw text carries
emphasis markers (***bold***), underscore rules, decorative bullets, HTML
entities and runs of spaced exclamation marks. mobile.bg also appends its own
footer ("Виж всички обяви в …  Контакти с продавача …") which is not the
dealer's copy at all. None of that belongs on a client's site.

What survives: the dealer's own sentences, their wording and their capitals.
This only removes typography, never claims.
"""
import html
import re

# mobile.bg's own footer, in the forms the harvester produces
TAIL = re.compile(
    r'(?:Виж\s+вс[ия]чки\s+обяви\s+в\b|Контакти\s+с\s+продавача\b|'
    r'Обявата\s+е\s+видяна\b|Добави\s+в\s+бележника\b).*$',
    re.S | re.I)

# ◦ • ▪ ‣ · ● ■ ★ ☆ ✔ ✓ ➤ ➔ » and friends used as bullet furniture
GLYPHS = re.compile(r'[•‣▪▫●■◦★☆'
                    r'✔✓➤➔»«→►▶❖✶]+')
RULE = re.compile(r'[_\-=~\.]{4,}')          # ______ / ------ / ...... rules
SPACED_BANG = re.compile(r'\s*([!?])(?:\s*[!?])+')   # "! ! !" and "! !! !"


def clean_note(text, max_chars=240):
    """Return the dealer's description with the typography junk removed.

    An empty string means nothing worth showing survived, and the caller should
    omit the note rather than render a blank paragraph.
    """
    if not text:
        return ""
    s = str(text)

    # Entities arrive single- or double-encoded depending on the harvest path.
    for _ in range(2):
        if "&" in s:
            s = html.unescape(s)
    s = s.replace("�", " ")             # cp1251 decode failures

    s = TAIL.sub(" ", s)
    # Emphasis runs and rules are block separators in the dealer's own layout,
    # so they become sentence breaks rather than vanishing and running claims together.
    s = re.sub(r'\*{2,}', '. ', s)
    s = s.replace("*", " ")
    s = GLYPHS.sub(". ", s)
    s = RULE.sub(". ", s)
    s = SPACED_BANG.sub(r"\1", s)            # "! ! !" -> "!"
    s = re.sub(r'(\d)\.\s+(\d)', r'\1.\2', s)        # "2. 0" -> "2.0"
    s = re.sub(r'\s+([,.;:!?])', r'\1', s)           # " ," -> ","
    s = re.sub(r'([,.;:!?])(?=[^\s\d])', r'\1 ', s)  # "състояние.Всичко" -> ". В"
    s = re.sub(r'\.\s*(?:\.\s*)+', '. ', s)          # ". . ." -> ". "
    s = re.sub(r'([!?.])\s*\.(?=\s|$)', r'\1', s)   # a bullet's "." landing after "!"
    s = re.sub(r'\.\s*([,;:])', r'\1', s)           # ". ," -> ",""
    s = re.sub(r'\s+', ' ', s).strip()
    s = re.sub(r'^[\s.,;:!?/|-]+', '', s)            # leading punctuation left behind

    if max_chars and len(s) > max_chars:
        cut = s[:max_chars]
        stop = max(cut.rfind('. '), cut.rfind('! '), cut.rfind('? '))
        s = (cut[:stop + 1] if stop > 60 else cut.rsplit(' ', 1)[0]).strip()

    # A fragment with no letters, or a lone cut-off word, is not a description.
    # Kept deliberately low: "Пали и върви." is terse but it is the dealer's own copy.
    if len(re.sub(r'[^\w]', '', s, flags=re.UNICODE)) < 8:
        return ""
    s = re.sub(r'\s+\d{1,3}[.,]?$', '.', s)   # trailing "… 4-MATIC 3." cut mid-figure
    s = re.sub(r'\s+([.!?])$', r'\1', s)
    if not re.search(r'[.!?]$', s):
        s += "."
    return s


TESTS = [
    # maxcar: emphasis markers and underscore rules
    ("***Възможност за лизинг = 6300 евро първоначална вноска*** ______________________ "
     "RANGE ROVER EVOQUE 2. 0 4X4 2020 TOP ______________________ ** *ТОП СЪСТОЯНИЕ*** "
     "***Подарък обслужване***",
     "Възможност за лизинг = 6300 евро първоначална вноска. RANGE ROVER EVOQUE 2.0 4X4 2020 TOP. "
     "ТОП СЪСТОЯНИЕ. Подарък обслужване."),
    # a trailing cut-off figure is dropped, not left dangling
    ("***Възможност за лизинг = 9300 евро първоначална вноска*** ____________ "
     "MERCEDES-BENZ GLE350 D COUPE 4-MATIC 3.",
     "Възможност за лизинг = 9300 евро първоначална вноска. MERCEDES-BENZ GLE350 D COUPE 4-MATIC."),
    # aldicar: double-encoded bullet entities
    ("&#9702; НОВ ВНОС ОТ СЕВЕРНА ИТАЛИЯ ! ! ! &#9702; BlueEFFICIENCY &#9702; 138000km ! ! ! !",
     "НОВ ВНОС ОТ СЕВЕРНА ИТАЛИЯ! BlueEFFICIENCY. 138000km!"),
    ("&amp;#9702; ЗАКУПЕН ОТ ВИТОША АУТО &amp;#9702; ПЪЛНА СЕРВИЗНА ИСТОРИЯ",
     "ЗАКУПЕН ОТ ВИТОША АУТО. ПЪЛНА СЕРВИЗНА ИСТОРИЯ."),
    # success: mobile.bg's own footer must go
    ("Лизинг без доказване на доходи ! ! ! Само срещу лична карта ! ! ! Виж всички обяви в "
     "success.bazar.bg и success.mobile.bg Контакти с продавача Success Automobile",
     "Лизинг без доказване на доходи! Само срещу лична карта!"),
    # marovski: spaced bangs mid-sentence
    ("197000км реален доказуем пробег! ! ! Нов внос Италия! ! Без грам ръждичка! !",
     "197000км реален доказуем пробег! Нов внос Италия! Без грам ръждичка!"),
    # peevauto: broken decode and spaced ellipsis
    ("РЕАЛНА ГОДИНА И КИЛОМЕТРИ! !! Външни забележки. . . . , четири детайла за боя! ! !",
     "РЕАЛНА ГОДИНА И КИЛОМЕТРИ! Външни забележки, четири детайла за боя!"),
    # a clean note is left alone
    ("Автомобилът е закупен от официалното представителство на марката в България, "
     "с доказуем пробег и пълна сервизна история.",
     "Автомобилът е закупен от официалното представителство на марката в България, "
     "с доказуем пробег и пълна сервизна история."),
    # nothing but furniture, or a cut-off fragment -> no note at all
    # short but real dealer copy survives once the footer is stripped
    ("Като Нова! ! ! Виж всички обяви в x.bazar.bg Контакти с продавача Алекс Нет Груп",
     "Като Нова!"),
    ("Пали и върви. Виж всички обяви в terax.mobile.bg Контакти с продавача ТЕРАКС",
     "Пали и върви."),
    ("*** _________________ ***", ""),
    ("Г", ""),
    ("&#9702; &#9702; !!!", ""),
    ("", ""),
    ("Виж всички обяви в x.mobile.bg Контакти с продавача X", ""),
]

if __name__ == "__main__":
    bad = 0
    for src, want in TESTS:
        got = clean_note(src)
        if got != want:
            bad += 1
            print("FAIL\n  in:   %r\n  want: %r\n  got:  %r" % (src[:90], want, got))
    print(("%d/%d passed" % (len(TESTS) - bad, len(TESTS))) if not bad else "%d FAILED" % bad)
    raise SystemExit(1 if bad else 0)
