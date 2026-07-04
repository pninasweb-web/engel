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

        tenders[uid] = Tender(
            uid=uid,
            source=council["name"],
            title=title,
            url=urljoin(council["url"], href),
            ttype=ttype,
            open_date=open_date,
            close_date=close_date,
        )

    return list(tenders.values())


def scrape_all(councils):
    out = []
    for c in councils:
        rows = scrape(c)
        print(f"  {c['name']}: {len(rows)} מכרזים")
        out.extend(rows)
    return out
