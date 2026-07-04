# -*- coding: utf-8 -*-
"""בניית מייל HTML מעוצב (RTL) ושליחתו דרך Gmail SMTP."""
import os
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr

# לכל קבוצה: אמוji, שם, צבע הדגשה, גוון רקע
GROUP_TITLES = {
    "wheat":   ("🌾", "חיטה / גד״ש", "#c9971c", "#fff8e6"),
    "grazing": ("🐄", "מרעה בקר",    "#2e8b57", "#eaf6ef"),
    "general": ("🌱", "חקלאי — כללי", "#5b8a3a", "#eef4e8"),
}
GROUP_ORDER = ["wheat", "grazing", "general"]


def _expand(bucket):
    return ["wheat", "grazing"] if bucket == "both" else [bucket]


def _detail_row(icon, label, value):
    if not value:
        return ""
    return (
        f'<tr>'
        f'<td style="padding:3px 0;color:#8a8a8a;font-size:13px;white-space:nowrap;'
        f'vertical-align:top;width:96px;">{icon} {label}</td>'
        f'<td style="padding:3px 0;color:#2b2b2b;font-size:13px;">{value}</td>'
        f'</tr>'
    )


def _contact_html(t):
    bits = []
    if t.contact_name:
        bits.append(t.contact_name)
    if t.contact_phone:
        bits.append(f'<a href="tel:{t.contact_phone}" style="color:#2e8b57;text-decoration:none;">☎ {t.contact_phone}</a>')
    if t.contact_email:
        bits.append(f'<a href="mailto:{t.contact_email}" style="color:#2e8b57;text-decoration:none;">✉ {t.contact_email}</a>')
    return " · ".join(bits)


def _card_html(t, accent):
    badge = (
        f'<span style="background:#eee;color:#555;font-size:11px;padding:2px 8px;'
        f'border-radius:10px;white-space:nowrap;">{t.ttype}</span>' if t.ttype else ""
    )
    rows = "".join([
        _detail_row("📍", "מיקום", t.location),
        _detail_row("📐", "שטח", f"{t.area} מ״ר" if t.area else ""),
        _detail_row("🧭", "גוש/חלקה", t.parcel),
        _detail_row("📅", "פורסם", t.open_date),
        _detail_row("⏰", "מועד אחרון", t.close_date),
        _detail_row("🏷️", "מס׳ מכרז", t.number),
        _detail_row("🏛️", "מפרסם", t.publisher),
        _detail_row("📋", "תנאים", t.terms),
        _detail_row("👤", "יצירת קשר", _contact_html(t)),
    ])
    return f"""
    <div style="background:#ffffff;border:1px solid #ececec;border-right:4px solid {accent};
                border-radius:10px;padding:16px 18px;margin:0 0 14px;">
      <table style="width:100%;border-collapse:collapse;"><tr>
        <td style="vertical-align:top;">
          <a href="{t.url}" style="font-size:16px;font-weight:700;color:#1c1c1c;
             text-decoration:none;line-height:1.35;">{t.title}</a>
        </td>
        <td style="vertical-align:top;text-align:left;white-space:nowrap;padding-right:8px;">{badge}</td>
      </tr></table>
      <table style="border-collapse:collapse;margin-top:10px;width:100%;">{rows}</table>
      <a href="{t.url}" style="display:inline-block;margin-top:12px;background:{accent};
         color:#fff;font-size:13px;font-weight:600;text-decoration:none;
         padding:8px 16px;border-radius:6px;">לפרטים המלאים ←</a>
    </div>"""


def build_html(tenders):
    groups = {g: [] for g in GROUP_ORDER}
    for t in tenders:
        for g in _expand(t.bucket):
            groups[g].append(t)

    sections = []
    for g in GROUP_ORDER:
        items = groups[g]
        if not items:
            continue
        emoji, name, accent, tint = GROUP_TITLES[g]
        cards = "".join(_card_html(t, accent) for t in items)
        sections.append(f"""
        <div style="margin:26px 0 6px;">
          <span style="background:{tint};color:{accent};font-size:16px;font-weight:700;
                       padding:7px 16px;border-radius:20px;">
            {emoji} {name} ({len(items)})
          </span>
        </div>
        {cards}""")

    today = datetime.now().strftime("%d/%m/%Y")
    return f"""<div dir="rtl" style="background:#f4f6f4;padding:22px 0;margin:0;
         font-family:'Segoe UI',Arial,Helvetica,sans-serif;">
  <div style="max-width:640px;margin:0 auto;">

    <div style="background:linear-gradient(135deg,#2e8b57,#3aa06a);background-color:#2e8b57;
                border-radius:12px;padding:22px 24px;color:#fff;">
      <div style="font-size:22px;font-weight:800;">🌾 מכרזים חקלאיים חדשים</div>
      <div style="font-size:14px;opacity:.92;margin-top:4px;">
        משק אנג׳ל · אזור עמק יזרעאל · {today}
      </div>
      <div style="font-size:13px;opacity:.85;margin-top:8px;">
        נמצאו {len(tenders)} מכרזים חדשים ורלוונטיים.
      </div>
    </div>

    {''.join(sections)}

    <div style="color:#9aa39a;font-size:12px;margin-top:24px;padding:14px 6px;
                border-top:1px solid #e2e6e2;line-height:1.6;">
      התראה אוטומטית יומית · מקורות: מועצות אזוריות עמק יזרעאל / גלבוע / מגידו +
      מינהל הרכש הממשלתי (רמ״י, משרד החקלאות, רשות הטבע והגנים).<br>
      הנתונים מחולצים אוטומטית — יש לוודא פרטים סופיים בקישור למכרז המקורי.
    </div>

  </div>
</div>"""


def send(tenders):
    user = os.environ["SMTP_USER"]
    password = os.environ["SMTP_APP_PASSWORD"]
    to_addr = os.environ.get("MAIL_TO", user)

    html = build_html(tenders)
    msg = MIMEText(html, "html", "utf-8")
    msg["Subject"] = Header(f"🌾 {len(tenders)} מכרזים חקלאיים חדשים באזור עמק יזרעאל", "utf-8")
    msg["From"] = formataddr((str(Header("מכרזים · משק אנג׳ל", "utf-8")), user))
    msg["To"] = to_addr

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(user, password)
        server.sendmail(user, [a.strip() for a in to_addr.split(",")], msg.as_string())
    print(f"  ✉  נשלח מייל ל-{to_addr}")
