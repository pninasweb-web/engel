# -*- coding: utf-8 -*-
"""גרידת מכרזים מדפי /bids/ של המועצות האזוריות.

לפלטפורמה שתי תבניות HTML:
  A) הגלבוע:      <a class="link-bid" href="./bids/?id=NN">כותרת</a>
  B) עמק יזרעאל/מגידו: <a class="bid-toggle" href="#bidNN">כותרת</a>
הפרסר תומך בשתיהן. תאריכים נלקחים מתאי השורה (dd/mm/yyyy).
"""
import re
from urllib.parse import urljoin
from bs4 import BeautifulSoup

from fetch import get_html
from tender import Tender

_DATE_RE = re.compile(r"\d{2}/\d{2}/\d{4}")


def _dates_from_row(cells):
    """מחזיר (open_date, close_date) מתוך תאי השורה."""
    dates = [c for c in cells if _DATE_RE.fullmatch(c.strip())]
    if len(dates) >= 2:
        return dates[0], dates[-1]
    if len(dates) == 1:
        return "", dates[0]
    return "", ""


def scrape(council):
    html = get_html(council["url"])
    if not html:
        return []

    soup = BeautifulSoup(html, "html.parser")
    tenders = {}

    for link in soup.select("a.link-bid, a.bid-toggle"):
        title = link.get_text(strip=True)
        if not title:
            continue
        href = link.get("href", "")
        m = re.search(r"(\d+)", href)
        bid_id = m.group(1) if m else title
        uid = f"council:{council['name']}:{bid_id}"
        if uid in tenders:
            continue

        row = link.find_parent("tr")
        cells = [td.get_text(" ", strip=True) for td in row.find_all("td")] if row else []
        open_date, close_date = _dates_from_row(cells)
        # תא סוג = תא קצר שאינו הכותרת ואינו תאריך (למשל "פומבי")
        ttype = ""
        for c in cells:
            if c and c != title and not _DATE_RE.search(c) and len(c) <= 20:
                ttype = c
                break

        t = Tender(
            uid=uid,
            source=council["name"],
            title=title,
            url=urljoin(council["url"], href),
            publisher=council["name"],
            ttype=ttype,
            open_date=open_date,
            close_date=close_date,
        )

        # תבנית B (עמק יזרעאל/מגידו): הפרטים בפאנל פנימי באותו עמוד — חינם
        if href.startswith("#"):
            _fill_from_panel(t, soup, href.lstrip("#"))

        tenders[uid] = t

    return list(tenders.values())


_EMAIL_RE = re.compile(r"[\w.\-]+@[\w.\-]+\.\w{2,}")
_PHONE_RE = re.compile(r"0\d[-\s]?\d{6,7}")


def _fill_from_panel(tender, soup, panel_id):
    """מחלץ תיאור/מספר/יצירת קשר מהפאנל הפנימי (תבנית עמק יזרעאל)."""
    panel = soup.find(id=panel_id)
    if not panel:
        return
    text = re.sub(r"\s+", " ", panel.get_text(" ", strip=True))
    tender.number = _grab(r"מספר מכרז:?\s*([\w/]+)", text)
    tender.terms = _grab(r"תאור המכרז:?\s*(.{5,180}?)(?:תאריך|מועד|לצפייה|$)", text) \
        or _grab(r"תאור המשרה:?\s*(.{5,180}?)(?:תאריך|מועד|$)", text)
    tender.contact_email = _grab_re(_EMAIL_RE, text)
    tender.contact_phone = _grab_re(_PHONE_RE, text)


def enrich_match(tender):
    """השלמת פרטים למכרז תואם מתבנית A (הגלבוע) — עמוד ?id= נפרד."""
    if "?id=" not in tender.url:
        return
    html = get_html(tender.url)
    if not html:
        return
    panel = BeautifulSoup(html, "html.parser").select_one(
        ".bid-content, .content-bid, main, article") or BeautifulSoup(html, "html.parser")
    text = re.sub(r"\s+", " ", panel.get_text(" ", strip=True))
    if not tender.contact_email:
        tender.contact_email = _grab_re(_EMAIL_RE, text)
    if not tender.contact_phone:
        tender.contact_phone = _grab_re(_PHONE_RE, text)


def _grab(pattern, text):
    m = re.search(pattern, text)
    return m.group(1).strip() if m else ""


def _grab_re(rx, text):
    m = rx.search(text)
    return m.group(0).strip() if m else ""


def scrape_all(councils):
    out = []
    for c in councils:
        rows = scrape(c)
        print(f"  {c['name']}: {len(rows)} מכרזים")
        out.extend(rows)
    return out
