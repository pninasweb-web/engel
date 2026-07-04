# -*- coding: utf-8 -*-
"""
גרידת מינהל הרכש הממשלתי (mr.gov.il) — מקור מרוכז לרמ"י, משרד החקלאות ועוד.
דף החיפוש מוגש כ-HTML מהשרת. תחביר Hybris: q=<טקסט>:<מיון>:<פאסט>:<ערך>.
משתמשים ב-archive:false כדי לקבל מכרזים פעילים בלבד.
"""
import re
from urllib.parse import quote, urljoin
from bs4 import BeautifulSoup

from fetch import get_html
from tender import Tender
from config import MR_GOV_BASE, MR_GOV_SEARCH_TERMS

# כמה עמודי תוצאות לקרוא לכל מונח חיפוש (20 תוצאות בעמוד)
PAGES_PER_TERM = 2


def _search_page(term, page):
    q = quote(f"{term}:relevance:archive:false")
    url = f"{MR_GOV_BASE}/ilgstorefront/he/search/?q={q}&page={page}"
    return get_html(url)


def _parse_results(html):
    """מחזיר רשימת Tender מדף תוצאות (בלי מיקום — נחלץ בהמשך מדף הפרט)."""
    soup = BeautifulSoup(html, "html.parser")
    out = []

    for head in soup.select("h2.search-results-content-head"):
        link = head.find_parent("a")
        if not link:
            continue
        title = head.get_text(strip=True)
        href = link.get("href", "")
        url = urljoin(MR_GOV_BASE, href)
        pub_id = href.rstrip("/").split("/")[-1]

        # המפרסם וסוג הפרסום נמצאים בכרטיס העוטף
        card = link.find_parent(class_=re.compile("details-main-wrapper")) or link.parent
        card_text = card.get_text(" ", strip=True) if card else ""

        publisher = ""
        m = re.search(r"שם המפרסם:\s*([^\|]+?)(?:\s*מס|\s*\||$)", card_text)
        if m:
            publisher = m.group(1).strip()

        ttype = ""
        sub = card.select_one(".search-result-sub-head, .search-results-sub-head") if card else None
        if sub:
            ttype = sub.get_text(strip=True)

        out.append(Tender(
            uid=f"mr:{pub_id}",
            source="רמ״י / מינהל הרכש",
            title=title,
            url=url,
            publisher=publisher,
            ttype=ttype,
        ))
    return out


def search_candidates():
    """
    מריץ את כל מונחי החיפוש ומחזיר dict של uid -> Tender (ללא כפילויות).
    עדיין בלי סינון גאוגרפי — זה קורה אחרי חילוץ המיקום מדף הפרט.
    """
    found = {}
    for term in MR_GOV_SEARCH_TERMS:
        n = 0
        for page in range(PAGES_PER_TERM):
            html = _search_page(term, page)
            if not html:
                break
            rows = _parse_results(html)
            if not rows:
                break
            for t in rows:
                found.setdefault(t.uid, t)
            n += len(rows)
        print(f'  mr.gov.il "{term}": {n} תוצאות')
    return found


def enrich_location(tender):
    """קורא את דף הפרט ומחלץ יישוב + טקסט רלוונטי לסינון גאוגרפי."""
    html = get_html(tender.url)
    if not html:
        return
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text)

    # שם היישוב מופיע כ"בישוב: X" ונעצר לפני "תקנת/פטור/גוש/מס׳"
    m = re.search(r"בישוב:\s*([^\d,|]{2,40}?)\s*(?:תקנ|פטור|גוש|הענק|מס['׳]|$)", text)
    if m:
        tender.location = m.group(1).strip()

    # חלון טקסט סביב פרטי הנכס — לתצוגה בלבד, לא לסינון האזור
    idx = text.find("בישוב")
    if idx < 0:
        idx = text.find("גוש")
    tender.extra_text = text[max(0, idx - 60):idx + 200] if idx >= 0 else ""
