# -*- coding: utf-8 -*-
"""בניית מיילים מעוצבים (RTL) ושליחתם דרך Gmail SMTP."""
import os
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.header import Header
from email.utils import formataddr

import config

# צבע הדגשה לכל קבוצה
_ACCENT = {"wheat": "#c9971c", "both": "#c9971c",
           "general": "#5b8a3a", "grazing": "#2e8b57"}
_BUCKET_CHIP = {"wheat": ("🌾", "חיטה/גד״ש", "#fff8e6", "#c9971c"),
                "both": ("🌾", "חיטה/גד״ש", "#fff8e6", "#c9971c"),
                "general": ("🌱", "חקלאי", "#eef4e8", "#5b8a3a"),
                "grazing": ("🐄", "מרעה", "#eaf6ef", "#2e8b57")}


def _accent(bucket):
    return _ACCENT.get(bucket, "#5b8a3a")


def _detail_row(icon, label, value, color="#2b2b2b", bold=False):
    if not value:
        return ""
    weight = "600" if bold else "normal"
    return (
        f'<tr><td style="padding:3px 0;color:#8a8a8a;font-size:13px;white-space:nowrap;'
        f'vertical-align:top;width:120px;">{icon} {label}</td>'
        f'<td style="padding:3px 0;color:{color};font-weight:{weight};font-size:13px;">{value}</td></tr>'
    )


def _contact_html(t):
    bits = []
    if t.contact_name:
        bits.append(t.contact_name)
    if t.contact_phone:
        bits.append(f'<a href="tel:{t.contact_phone}" style="color:#2e8b57;text-decoration:none;">☎ {t.contact_phone}</a>')
    elif t.contact_email or t.contact_name:
        # יש פרטי קשר אך בלי טלפון — מציינים במפורש
        bits.append('<span style="color:#a0a0a0;">☎ לא צוין טלפון</span>')
    if t.contact_email:
        bits.append(f'<a href="mailto:{t.contact_email}" style="color:#2e8b57;text-decoration:none;">✉ {t.contact_email}</a>')
    return " · ".join(bits)


def _chip(bucket):
    emoji, name, bg, fg = _BUCKET_CHIP.get(bucket, ("🌱", "חקלאי", "#eef4e8", "#5b8a3a"))
    return (f'<span style="background:{bg};color:{fg};font-size:11px;font-weight:600;'
            f'padding:2px 9px;border-radius:10px;white-space:nowrap;">{emoji} {name}</span>')


def _card(t):
    accent = _accent(t.bucket)
    badge = (f'<span style="background:#eee;color:#555;font-size:11px;padding:2px 8px;'
             f'border-radius:10px;white-space:nowrap;">{t.ttype}</span>' if t.ttype else "")
    rows = "".join([
        _detail_row("📍", "מיקום", t.location),
        _detail_row("📐", "שטח", f"{t.area} מ״ר" if t.area else ""),
        _detail_row("🧭", "גוש/חלקה", t.parcel),
        _detail_row("📅", "פורסם", t.open_date),
        _detail_row("⏰", "מועד אחרון להגשה", t.close_date, color="#b23b2e", bold=True),
        _detail_row("🏷️", "מס׳ מכרז", t.number),
        _detail_row("🏛️", "מפרסם", t.publisher),
        _detail_row("📋", "תנאים", t.terms),
        _detail_row("👤", "יצירת קשר", _contact_html(t)),
    ])
    return f"""
    <div style="background:#ffffff;border:1px solid #ececec;border-right:4px solid {accent};
                border-radius:10px;padding:16px 18px;margin:0 0 14px;">
      <table style="width:100%;border-collapse:collapse;"><tr>
        <td style="vertical-align:top;">{_chip(t.bucket)}
          <div style="margin-top:6px;"><a href="{t.url}" style="font-size:16px;font-weight:700;
             color:#1c1c1c;text-decoration:none;line-height:1.35;">{t.title}</a></div>
        </td>
        <td style="vertical-align:top;text-align:left;white-space:nowrap;padding-right:8px;">{badge}</td>
      </tr></table>
      <table style="border-collapse:collapse;margin-top:10px;width:100%;">{rows}</table>
      <a href="{t.url}" style="display:inline-block;margin-top:12px;background:{accent};
         color:#fff;font-size:13px;font-weight:600;text-decoration:none;
         padding:8px 16px;border-radius:6px;">לפרטים המלאים ←</a>
    </div>"""


def _section(title, emoji, tenders, accent="#2e8b57"):
    if not tenders:
        return ""
    cards = "".join(_card(t) for t in tenders)
    return f"""
      <div style="margin:28px 0 12px;border-bottom:2px solid {accent};padding-bottom:6px;">
        <span style="font-size:19px;font-weight:800;color:{accent};">{emoji} {title}</span>
        <span style="color:#aaa;font-weight:normal;font-size:15px;">({len(tenders)})</span>
      </div>
      {cards}"""


def _banner(subtitle, count_line):
    today = datetime.now().strftime("%d/%m/%Y")
    return f"""
    <div style="background:linear-gradient(135deg,#2e8b57,#3aa06a);background-color:#2e8b57;
                border-radius:12px;padding:22px 24px;color:#fff;">
      <div style="font-size:22px;font-weight:800;">מכרזים חקלאיים · אנגל</div>
      <div style="font-size:14px;opacity:.92;margin-top:4px;">{subtitle} · {today}</div>
      <div style="font-size:13px;opacity:.85;margin-top:8px;">{count_line}</div>
    </div>"""


_FOOTER = """
    <div style="color:#9aa39a;font-size:12px;margin-top:26px;padding:14px 6px;
                border-top:1px solid #e2e6e2;line-height:1.6;">
      התראה אוטומטית · מקורות: מועצות אזוריות עמק יזרעאל / גלבוע / מגידו +
      מינהל הרכש הממשלתי (רמ״י, משרד החקלאות, רשות הטבע והגנים).<br>
      הנתונים מחולצים אוטומטית — יש לוודא פרטים סופיים בקישור למכרז המקורי.
    </div>"""


def _spreadsheet_block():
    """קישור + הסבר על קובץ האקסל המצטבר (הקובץ עצמו מצורף למייל)."""
    link = ""
    if config.SPREADSHEET_URL:
        link = (f'<a href="{config.SPREADSHEET_URL}" style="display:inline-block;'
                f'background:#1f6b3b;color:#fff;font-size:13px;font-weight:600;'
                f'text-decoration:none;padding:9px 18px;border-radius:6px;margin-top:8px;">'
                f'📊 לצפייה בקובץ כל המכרזים ←</a>')
    return f"""
      <div style="background:#eef4e8;border:1px solid #d8e6cf;border-radius:10px;
                  padding:14px 18px;margin:22px 0 4px;">
        <div style="font-size:14px;font-weight:700;color:#2e6b3b;">📎 קובץ ריכוז כל המכרזים</div>
        <div style="font-size:13px;color:#4a5a48;margin-top:3px;">
          מצורף למייל קובץ אקסל מעוצב עם כל המכרזים, מסודרים לפי חודשים.
        </div>
        {link}
      </div>"""


def _wrap(inner):
    return f"""<div dir="rtl" style="background:#f4f6f4;padding:22px 14px;margin:0;
         font-family:'Segoe UI',Arial,Helvetica,sans-serif;">
  <div style="max-width:600px;margin:0 auto;">{inner}</div></div>"""


def build_daily(new_tenders, week_tenders):
    banner = _banner("מכרזים חקלאיים חדשים",
                     f"{len(new_tenders)} מכרזים חדשים היום · {len(week_tenders)} נוספים רלוונטיים השבוע")
    body = (_section("מכרזים חדשים", "🆕", new_tenders, "#2e8b57")
            + _section("מכרזים רלוונטיים השבוע", "📆", week_tenders, "#5b8a3a"))
    return _wrap(banner + body + _spreadsheet_block() + _FOOTER)


def build_weekly(week_tenders):
    banner = _banner("סיכום שבועי", f"{len(week_tenders)} מכרזים רלוונטיים ב-7 הימים האחרונים")
    body = _section("מכרזים רלוונטיים השבוע", "📆", week_tenders, "#2e8b57")
    return _wrap(banner + body + _spreadsheet_block() + _FOOTER)


# ---------------------------------------------------------------------------
# שליחה
# ---------------------------------------------------------------------------

def _send(subject, html, attach_path=None):
    user = os.environ["SMTP_USER"]
    password = os.environ["SMTP_APP_PASSWORD"]
    to_addr = os.environ.get("MAIL_TO", user)

    msg = MIMEMultipart("mixed")
    msg["Subject"] = Header(subject, "utf-8")
    msg["From"] = formataddr((str(Header("מכרזים חקלאיים · אנגל", "utf-8")), user))
    msg["To"] = to_addr
    msg.attach(MIMEText(html, "html", "utf-8"))

    if attach_path and os.path.exists(attach_path):
        with open(attach_path, "rb") as f:
            part = MIMEApplication(f.read(), _subtype="vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        part.add_header("Content-Disposition", "attachment", filename="מכרזים-אנגל.xlsx")
        msg.attach(part)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(user, password)
        server.sendmail(user, [a.strip() for a in to_addr.split(",")], msg.as_string())
    print(f"  ✉  נשלח מייל ל-{to_addr}")


def send_daily(new_tenders, week_tenders, attach_path="tenders.xlsx"):
    _send(f"{len(new_tenders)} מכרזים חקלאיים חדשים באזור עמק יזרעאל",
          build_daily(new_tenders, week_tenders), attach_path=attach_path)


def send_weekly(week_tenders, attach_path="tenders.xlsx"):
    _send(f"סיכום שבועי · {len(week_tenders)} מכרזים חקלאיים רלוונטיים",
          build_weekly(week_tenders), attach_path=attach_path)
