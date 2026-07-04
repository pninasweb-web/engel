# -*- coding: utf-8 -*-
"""
שליחת המכרזים לגיליון Google Sheets חי (בדרייב של המשתמשת).
העדכון נעשה דרך Web App של Google Apps Script — ה-Action שולח JSON,
והסקריפט בצד גוגל מצייר את הגיליון יפה, מסודר לפי חודשים.

משתני סביבה (GitHub Secrets):
  SHEETS_WEBHOOK_URL  — כתובת ה-Web App
  SHEETS_TOKEN        — סיסמת אימות פשוטה (זהה לזו שבסקריפט)
כשלא מוגדרים — הפונקציה פשוט לא עושה כלום (למשל בהרצה מקומית).
"""
import os
import json
import urllib.request

from spreadsheet import _month_key, HEB_MONTHS, _contact


def _month_label(key):
    year, month = key
    return f"{HEB_MONTHS[month]} {year}" if month else "ללא תאריך"


def _payload_rows(tenders):
    """ממיין לפי חודש (מהחדש לישן) ומכין שורות עם תווית חודש לכל אחת."""
    ordered = sorted(
        tenders,
        key=lambda t: (_month_key(t), t.open_date or ""),
        reverse=True,
    )
    rows = []
    for t in ordered:
        rows.append({
            "month": _month_label(_month_key(t)),
            "title": t.title,
            "ttype": t.ttype,
            "location": t.location,
            "area": t.area,
            "open_date": t.open_date,
            "close_date": t.close_date,
            "publisher": t.publisher,
            "contact": _contact(t),
            "url": t.url,
        })
    return rows


def push(tenders):
    url = os.environ.get("SHEETS_WEBHOOK_URL")
    if not url:
        return
    payload = {
        "token": os.environ.get("SHEETS_TOKEN", ""),
        "rows": _payload_rows(tenders),
    }
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url, data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            print(f"  📗 גיליון Google עודכן ({len(payload['rows'])} שורות, {resp.status})")
    except Exception as exc:  # noqa: BLE001
        print(f"  ! עדכון הגיליון נכשל: {exc}")
