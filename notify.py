# -*- coding: utf-8 -*-
"""בניית מייל HTML בעברית (RTL) ושליחתו דרך Gmail SMTP."""
import os
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr

# שמות תצוגה לקבוצות
GROUP_TITLES = {
    "wheat":   "🌾 חיטה / גד״ש",
    "grazing": "🐄 מרעה בקר",
    "general": "🌱 חקלאי — כללי",
}
GROUP_ORDER = ["wheat", "grazing", "general"]


def _expand(bucket):
    """'both' מופיע גם בחיטה וגם במרעה."""
    return ["wheat", "grazing"] if bucket == "both" else [bucket]


def _row_html(t):
    parts = [f'<a href="{t.url}" style="font-weight:bold;color:#1a5d1a;text-decoration:none;">{t.title}</a>']
    meta = [f"מקור: {t.source}"]
    if t.publisher:
        meta.append(f"מפרסם: {t.publisher}")
    if t.ttype:
        meta.append(f"סוג: {t.ttype}")
    if t.location:
        meta.append(f"יישוב: {t.location}")
    if t.close_date:
        meta.append(f"סגירה: {t.close_date}")
    parts.append(
        '<div style="font-size:13px;color:#555;margin-top:2px;">'
        + " · ".join(meta) + "</div>"
    )
    return (
        '<li style="margin:0 0 14px 0;padding:10px 12px;background:#f7faf7;'
        'border-right:3px solid #2e8b2e;border-radius:4px;list-style:none;">'
        + "".join(parts) + "</li>"
    )


def build_html(tenders):
    """מקבל רשימת Tender (עם bucket) ומחזיר HTML מקובץ לפי קבוצה."""
    groups = {g: [] for g in GROUP_ORDER}
    for t in tenders:
        for g in _expand(t.bucket):
            groups[g].append(t)

    sections = []
    for g in GROUP_ORDER:
        items = groups[g]
        if not items:
            continue
        rows = "".join(_row_html(t) for t in items)
        sections.append(
            f'<h2 style="font-size:18px;color:#2e8b2e;margin:22px 0 10px;">'
            f'{GROUP_TITLES[g]} <span style="color:#999;font-weight:normal;">'
            f'({len(items)})</span></h2>'
            f'<ul style="margin:0;padding:0;">{rows}</ul>'
        )

    body = "".join(sections)
    return f"""<div dir="rtl" style="font-family:Arial,Helvetica,sans-serif;max-width:640px;margin:0 auto;color:#222;">
  <h1 style="font-size:20px;border-bottom:2px solid #2e8b2e;padding-bottom:8px;">
    מכרזים חקלאיים חדשים — אזור עמק יזרעאל
  </h1>
  <p style="color:#666;font-size:14px;">נמצאו {len(tenders)} מכרזים חדשים רלוונטיים.</p>
  {body}
  <p style="color:#aaa;font-size:12px;margin-top:28px;border-top:1px solid #eee;padding-top:10px;">
    התראה אוטומטית · המקורות: מועצות אזוריות עמק יזרעאל/גלבוע/מגידו + מינהל הרכש הממשלתי (רמ״י ומשרד החקלאות).
  </p>
</div>"""


def send(tenders):
    """שולח את המייל. פרטי ההתחברות מגיעים ממשתני סביבה / GitHub Secrets."""
    user = os.environ["SMTP_USER"]           # כתובת ה-Gmail השולחת
    password = os.environ["SMTP_APP_PASSWORD"]  # App Password של Gmail
    to_addr = os.environ.get("MAIL_TO", user)

    html = build_html(tenders)
    msg = MIMEText(html, "html", "utf-8")
    msg["Subject"] = Header(f"🌾 {len(tenders)} מכרזים חקלאיים חדשים באזור", "utf-8")
    msg["From"] = formataddr((str(Header("מכרזים חקלאיים", "utf-8")), user))
    msg["To"] = to_addr

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(user, password)
        server.sendmail(user, [a.strip() for a in to_addr.split(",")], msg.as_string())
    print(f"  ✉  נשלח מייל ל-{to_addr}")
