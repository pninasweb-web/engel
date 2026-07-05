/**
 * מצייר את המכרזים בגיליון, מסודרים לפי חודשים. פונט קבוע: Rubik.
 * עמודות: מס׳ סידורי | פרטי המכרז | קישור | ✅ נוצר קשר? | ✅ נשלח?
 * הסימונים נשמרים בין עדכונים (לפי המכרז).
 * להדביק ב: הגיליון → Extensions → Apps Script → להחליף הכל → לשמור → לפרוס מחדש.
 */
const SECRET = 'engel-bee6778b46e5';
const GREEN = '#2E8B57', GOLD = '#C9971C', FONT = 'Rubik';
const HEADERS = ['מס׳','מכרז','סוג המכרז','מיקום','שטח (מ״ר)','תאריך פרסום',
                 'מועד אחרון להגשה','מפרסם','פרטי קשר','קישור','נוצר קשר?','נשלח?'];
const WIDTHS = [45,300,110,100,85,100,115,140,200,80,90,80];

function doPost(e) {
  try {
    const b = JSON.parse(e.postData.contents);
    if (b.token !== SECRET) return ContentService.createTextOutput('unauthorized');
    render(b.rows || []);
    return ContentService.createTextOutput('ok');
  } catch (err) { return ContentService.createTextOutput('error: ' + err); }
}

function render(rows) {
  const sh = SpreadsheetApp.getActiveSpreadsheet().getSheets()[0];
  const NC = HEADERS.length;
  const prev = {};
  const lr = sh.getLastRow(), lc = sh.getLastColumn();
  if (lr >= 1 && lc >= 2) {
    const vals = sh.getRange(1,1,lr,lc).getValues();
    const forms = sh.getRange(1,1,lr,lc).getFormulas();
    for (let i=0;i<vals.length;i++){
      const m = String(forms[i][1]||'').match(/HYPERLINK\("([^"]+)"/);
      if (m) prev[m[1]] = {contact: vals[i][10]===true, sent: vals[i][11]===true};
    }
  }
  sh.clearContents(); sh.clearFormats();
  sh.getRange(1,1,sh.getMaxRows(),sh.getMaxColumns()).clearDataValidations();
  sh.setRightToLeft(true);
  WIDTHS.forEach(function(w,i){ sh.setColumnWidth(i+1,w); });
  sh.getRange(1,1,1,NC).merge().setValue('🌾  מכרזים חקלאיים · אנגל · אזור עמק יזרעאל')
    .setBackground(GREEN).setFontColor('#fff').setFontWeight('bold').setFontSize(14).setHorizontalAlignment('right');
  sh.setRowHeight(1,30);
  if (!rows.length){
    sh.getRange(3,1).setValue('אין מכרזים עדיין — הגיליון יתעדכן אוטומטית.');
    sh.getRange(1,1,sh.getLastRow(),NC).setFontFamily(FONT); return;
  }
  let r=3, lastMonth=null, n=0;
  rows.forEach(function(row){
    if (row.month!==lastMonth){
      lastMonth=row.month;
      sh.getRange(r,1,1,NC).merge().setValue('📅  '+row.month)
        .setBackground(GOLD).setFontColor('#fff').setFontWeight('bold').setHorizontalAlignment('right'); r++;
      sh.getRange(r,1,1,NC).setValues([HEADERS])
        .setBackground(GREEN).setFontColor('#fff').setFontWeight('bold').setHorizontalAlignment('center').setWrap(true); r++;
    }
    n++;
    sh.getRange(r,1,1,NC).setValues([[n,row.title,row.ttype,row.location,row.area,row.open_date,(row.close_date||'לא צוין'),row.publisher,row.contact,'','','']])
      .setVerticalAlignment('top').setWrap(true);
    sh.getRange(r,1).setHorizontalAlignment('center');
    const c=sh.getRange(r,11); c.insertCheckboxes(); c.setHorizontalAlignment('center');
    const s=sh.getRange(r,12); s.insertCheckboxes(); s.setHorizontalAlignment('center');
    if (row.url){
      const title=String(row.title).replace(/"/g,'""');
      sh.getRange(r,2).setFormula('=HYPERLINK("'+row.url+'","'+title+'")').setFontColor('#1155CC');
      sh.getRange(r,10).setFormula('=HYPERLINK("'+row.url+'","פתיחה ↗")').setFontColor('#1155CC');
      if (prev[row.url]){ if(prev[row.url].contact) c.setValue(true); if(prev[row.url].sent) s.setValue(true); }
    }
    if (row.close_date) sh.getRange(r,7).setFontColor('#B23B2E').setFontWeight('bold');
    else sh.getRange(r,7).setFontColor('#999999');
    r++;
  });
  sh.getRange(1,1,sh.getLastRow(),NC).setFontFamily(FONT);
}
