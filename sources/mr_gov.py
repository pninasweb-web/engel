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
PAGES_PER_TERM = 3


def _search_page(term, page):
    # מיון לפי תאריך עדכון (החדשים ביותר קודם) — כדי לתפוס מכרזים טריים
    # ולא הודעות ישנות מלפני שנים.
    q = quote(f"{term}:updateDate:archive:false")
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
        title = re.sub(r"\s+", " ", head.get_text(strip=True))
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


def _grab(pattern, text, group=1):
    m = re.search(pattern, text)
    return m.group(group).strip() if m else ""


def enrich_details(tender):
    """קורא את דף הפרט ומחלץ את כל הנתונים המפורטים למייל."""
    html = get_html(tender.url)
    if not html:
        return
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"&nbsp;?", " ", text)
    text = re.sub(r"\s+", " ", text)

    # יישוב — נעצר לפני "תקנת/פטור/גוש/מס׳"
    tender.location = _grab(
        r"בישוב:\s*([^\d,|]{2,40}?)\s*(?:תקנ|פטור|גוש|הענק|מס['׳]|$)", text)

    # תאריכים
    tender.open_date = _grab(r"תאריך פרסום:\s*(\d{2}/\d{2}/\d{4})", text)
    deadline = _grab(r"מועד אחרון להגשה:\s*([^|]{0,60}?)\s*(?:איש קשר|פרטי|תקנ|$)", text)
    # מציגים מועד אחרון רק אם הוא מכיל תאריך אמיתי (לא "השגות")
    tender.close_date = deadline if re.search(r"\d{2}/\d{2}/\d{4}", deadline) else ""

    # מהות ההתקשרות = התנאים/התיאור (מנקים מספרי רישום ארוכים שמלכלכים)
    terms = _grab(r"מהות ההתקשרות:\s*([^,]{3,80})", text)
    terms = re.sub(r"\s*\d{6,}\s*", " ", terms).strip()
    tender.terms = terms

    # שטח וגוש/חלקה
    tender.area = _grab(r"שטח עיסקה:\s*([\d,]+)", text)
    tender.parcel = _grab(r"בגוש חלקה ושיטת רישום\s*([^|]{3,60}?)(?:בישוב|במגרש|תכנית|$)", text)

    # יצירת קשר — מבודדים את בלוק "איש קשר" כדי לא לתפוס מספרי תכנית/גוש רועשים
    block = _grab(r"(איש קשר:.{0,160}?)(?:מהות ההתקשרות|שטח עיסקה|$)", text) or text
    tender.contact_name = _grab(r"איש קשר:\s*([^\d]{2,40}?)\s*(?:דוא|טלפון|מייל|$)", block)
    tender.contact_email = _grab(r"([\w.\-]+@[\w.\-]+\.\w{2,})", block)
    # טלפון: מסומן במפורש, או מספר טלפון תקין בתוך בלוק אנשי הקשר בלבד
    tender.contact_phone = (_grab(r"טלפון:?\s*(0\d[-\s]?\d{6,7})", block)
                            or _grab(r"\b(0\d{1,2}-?\d{7})\b", block))
