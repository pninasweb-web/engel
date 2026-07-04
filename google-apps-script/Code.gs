/**
 * מקבל את המכרזים מהמערכת ומצייר אותם יפה בגיליון, מסודרים לפי חודשים.
 * להדביק ב: הגיליון → Extensions → Apps Script → להחליף את כל התוכן בזה.
 * הסיסמה כבר מוטמעת — אין צורך לשנות כלום, רק להדביק ולפרוס (Deploy).
 *
 * עמודת "נוצר קשר?" היא תיבת סימון — הסימונים נשמרים בין עדכונים (לפי המכרז).
 */
const SECRET = 'engel-bee6778b46e5';

const GREEN = '#2E8B57', GOLD = '#C9971C';
const HEADERS = ['נוצר קשר?', 'מכרז', 'סוג המכרז', 'מיקום', 'שטח (מ״ר)',
                 'תאריך פרסום', 'מועד אחרון להגשה', 'מפרסם', 'פרטי קשר', 'קישור'];
const WIDTHS = [95, 300, 110, 110, 90, 105, 120, 150, 220, 90];

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
  const NC = HEADERS.length;

  // 1) שמירת מצב הסימון הקיים ("נוצר קשר?") לפי קישור המכרז
  const prev = {};
  const lr = sh.getLastRow(), lc = sh.getLastColumn();
  if (lr >= 1 && lc >= 2) {
    const vals = sh.getRange(1, 1, lr, lc).getValues();
    const forms = sh.getRange(1, 1, lr, lc).getFormulas();
    for (let i = 0; i < vals.length; i++) {
      const m = String(forms[i][1] || '').match(/HYPERLINK\("([^"]+)"/);
      if (m) prev[m[1]] = (vals[i][0] === true);
    }
  }

  // 2) ניקוי מלא (כולל תיבות סימון) והגדרת RTL ורוחב עמודות
  sh.clearContents();
  sh.clearFormats();
  sh.getRange(1, 1, sh.getMaxRows(), sh.getMaxColumns()).clearDataValidations();
  sh.setRightToLeft(true);
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
        .setHorizontalAlignment('center').setWrap(true);
      r++;
    }

    sh.getRange(r, 1, 1, NC).setValues([[
      '', row.title, row.ttype, row.location, row.area,
      row.open_date, row.close_date, row.publisher, row.contact, ''
    ]]).setVerticalAlignment('top').setWrap(true);

    // תיבת סימון "נוצר קשר?" + שחזור מצב קודם
    const box = sh.getRange(r, 1);
    box.insertCheckboxes();
    box.setHorizontalAlignment('center');
    if (row.url && prev[row.url]) box.setValue(true);

    // קישורים לחיצים
    if (row.url) {
      const title = String(row.title).replace(/"/g, '""');
      sh.getRange(r, 2).setFormula('=HYPERLINK("' + row.url + '","' + title + '")')
        .setFontColor('#1155CC');
      sh.getRange(r, NC).setFormula('=HYPERLINK("' + row.url + '","פתיחה ↗")')
        .setFontColor('#1155CC');
    }
    if (row.close_date) {
      sh.getRange(r, 7).setFontColor('#B23B2E').setFontWeight('bold');
    }
    r++;
  });
}
