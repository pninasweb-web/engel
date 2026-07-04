/**
 * מקבל את המכרזים מהמערכת ומצייר אותם יפה בגיליון, מסודרים לפי חודשים.
 * להדביק ב: הגיליון → Extensions → Apps Script → להחליף את כל התוכן בזה.
 *
 * חשוב: שנה את SECRET לערך משלך, ושים בדיוק את אותו ערך ב-GitHub
 * כ-Secret בשם SHEETS_TOKEN.
 */
const SECRET = 'CHANGE_ME_TOKEN';   // ← שנה לערך סודי משלך

const GREEN = '#2E8B57', GOLD = '#C9971C';
const HEADERS = ['מכרז', 'סוג המכרז', 'מיקום', 'שטח (מ״ר)', 'תאריך פרסום',
                 'מועד אחרון להגשה', 'מפרסם', 'פרטי קשר', 'קישור'];
const WIDTHS = [320, 110, 110, 90, 105, 120, 150, 220, 90];

function doPost(e) {
  try {
    const body = JSON.parse(e.postData.contents);
    if (body.token !== SECRET) {
      return ContentService.createTextOutput('unauthorized');
    }
    render(body.rows || []);
    return ContentService.createTextOutput('ok');
  } catch (err) {
    return ContentService.createTextOutput('error: ' + err);
  }
}

function render(rows) {
  const sh = SpreadsheetApp.getActiveSpreadsheet().getSheets()[0];
  sh.clear();
  sh.setRightToLeft(true);
  const NC = HEADERS.length;
  WIDTHS.forEach(function (w, i) { sh.setColumnWidth(i + 1, w); });

  // כותרת עליונה
  sh.getRange(1, 1, 1, NC).merge()
    .setValue('🌾  מכרזים חקלאיים · אנגל · אזור עמק יזרעאל')
    .setBackground(GREEN).setFontColor('#ffffff').setFontWeight('bold')
    .setFontSize(14).setHorizontalAlignment('right');
  sh.setRowHeight(1, 30);

  if (!rows.length) {
    sh.getRange(3, 1).setValue('אין מכרזים עדיין — הגיליון יתעדכן אוטומטית.');
    return;
  }

  let r = 3, lastMonth = null;
  rows.forEach(function (row) {
    if (row.month !== lastMonth) {
      lastMonth = row.month;
      sh.getRange(r, 1, 1, NC).merge()
        .setValue('📅  ' + row.month)
        .setBackground(GOLD).setFontColor('#ffffff').setFontWeight('bold')
        .setHorizontalAlignment('right');
      r++;
      sh.getRange(r, 1, 1, NC).setValues([HEADERS])
        .setBackground(GREEN).setFontColor('#ffffff').setFontWeight('bold')
        .setHorizontalAlignment('center');
      r++;
    }
    sh.getRange(r, 1, 1, NC).setValues([[
      row.title, row.ttype, row.location, row.area, row.open_date,
      row.close_date, row.publisher, row.contact, ''
    ]]).setVerticalAlignment('top').setWrap(true);

    if (row.url) {
      const title = String(row.title).replace(/"/g, '""');
      sh.getRange(r, 1).setFormula('=HYPERLINK("' + row.url + '","' + title + '")')
        .setFontColor('#1155CC');
      sh.getRange(r, NC).setFormula('=HYPERLINK("' + row.url + '","פתיחה ↗")')
        .setFontColor('#1155CC');
    }
    if (row.close_date) {
      sh.getRange(r, 6).setFontColor('#B23B2E').setFontWeight('bold');
    }
    r++;
  });
}
