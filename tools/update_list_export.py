"""更新リスト（docs/updates/*.md）を、クライアント送付用の Word と Excel にする。
  python3 tools/update_list_export.py docs/updates/20261102-xxx.md [--to 送付用]
出力: <to>/<md名>.docx（印刷・署名用） と <to>/<md名>.xlsx（項目ごとに回答を書き込める）
承認欄が空なら空欄のまま（クライアントが記入）、記入済みならその内容を載せる。
"""
import re, sys, pathlib, argparse, datetime
from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ROW_HEIGHT_RULE
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, Mm, RGBColor
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.worksheet.datavalidation import DataValidation

FONT = 'Yu Gothic'
from kitcfg import CFG
COMPANY = CFG.get('company', '合同会社K&Aプロジェクト')

def parse(md):
    t = md.read_text(encoding='utf-8').splitlines()
    d = {'title': '', 'meta': [], 'rows': [], 'questions': [], 'approval': {}}
    sec = None
    for l in t:
        if l.startswith('# '): d['title'] = l[2:].strip(); continue
        if l.startswith('## '): sec = l[3:].strip(); continue
        if sec is None and l.startswith('- ') and not l[2:].startswith(INTERNAL): d['meta'].append(l[2:].strip())
        elif sec == '更新リスト' and l.startswith('|') and not re.match(r'^\|\s*(No|-)', l):
            c = [x.strip() for x in l.strip().strip('|').split('|')]
            if c and c[0]: d['rows'].append(c + [''] * (6 - len(c)))
        elif sec == '確認したいこと' and l.startswith('- '): d['questions'].append(l[2:].strip())
        elif sec == '承認' and l.startswith('- '):
            k, _, v = l[2:].partition('：'); d['approval'][k.strip()] = v.strip()
    return d

INTERNAL = ('比較の基準',)  # 社内向けの行は送付用に載せない
HEAD = ['No', 'ページ・場所', '変更前', '変更後', '根拠（資料のどこ）', '判断']

def word(d, out):
    doc = Document()
    st = doc.styles['Normal']; st.font.name = FONT; st.font.size = Pt(10.5)
    st.element.get_or_add_rPr().get_or_add_rFonts().set(qn('w:eastAsia'), FONT)
    s = doc.sections[0]
    s.orientation = WD_ORIENT.LANDSCAPE; s.page_width, s.page_height = Mm(297), Mm(210)
    for m in ('left_margin', 'right_margin'): setattr(s, m, Mm(18))
    s.top_margin = s.bottom_margin = Mm(15)
    def para(text, size=10.5, bold=False, color=None, space=4):
        p = doc.add_paragraph(); r = p.add_run(text); r.font.size = Pt(size); r.bold = bold
        r._element.get_or_add_rPr().get_or_add_rFonts().set(qn('w:eastAsia'), FONT)
        if color: r.font.color.rgb = RGBColor.from_string(color)
        p.paragraph_format.space_after = Pt(space); return p
    def shade(cell, hexcolor):
        tcPr = cell._element.get_or_add_tcPr(); sh = OxmlElement('w:shd')
        sh.set(qn('w:val'), 'clear'); sh.set(qn('w:color'), 'auto'); sh.set(qn('w:fill'), hexcolor); tcPr.append(sh)
    def table(rows, widths, head=True, min_h=None):
        tb = doc.add_table(rows=len(rows), cols=len(widths)); tb.style = 'Table Grid'; tb.alignment = WD_TABLE_ALIGNMENT.CENTER
        tb.autofit = False
        lay = OxmlElement('w:tblLayout'); lay.set(qn('w:type'), 'fixed'); tb._tbl.tblPr.append(lay)
        for j, w in enumerate(widths): tb.columns[j].width = Mm(w)
        for g, w in zip(tb._tbl.tblGrid.findall(qn('w:gridCol')), widths): g.set(qn('w:w'), str(int(w * 56.7)))
        for i, row in enumerate(rows):
            if min_h and i > 0:
                tb.rows[i].height = Mm(min_h); tb.rows[i].height_rule = WD_ROW_HEIGHT_RULE.AT_LEAST
            for j, v in enumerate(row):
                c = tb.cell(i, j); c.width = Mm(widths[j]); c.text = ''
                r = c.paragraphs[0].add_run(v); r.font.size = Pt(9.5); r._element.get_or_add_rPr().get_or_add_rFonts().set(qn('w:eastAsia'), FONT)
                if head and i == 0: r.bold = True; shade(c, 'E2F3E9')
        return tb
    para('ホームページ更新リスト（ご確認・ご承認のお願い）', 16, True, '1F5A3E', 2)
    para(d['title'].replace('更新リスト：', ''), 11, False, '4F5E56', 8)
    para(f'作成：{COMPANY}　　作成日：{datetime.date.today():%Y年%m月%d日}', 9.5, False, '4F5E56', 6)
    for m in d['meta']: para('・' + m, 9.5, space=1)
    para('', space=2)
    para('更新リスト', 12, True, '23774F')
    wh = HEAD[:4] + ['修正依頼（ご記入欄）'] + HEAD[4:]
    table([wh] + [r[:4] + [''] + r[4:6] for r in d['rows']], [10, 44, 44, 44, 58, 36, 18], min_h=16)
    para('', space=2)
    para('確認したいこと', 12, True, '23774F')
    for q in d['questions'] or ['なし']: para('・' + q, space=2)
    para('', space=2)
    para('ご承認', 12, True, '23774F')
    a = d['approval']
    table([['承認日', a.get('更新リスト承認日', '') or '　　　　年　　月　　日'],
           ['承認者（ご署名）', a.get('更新リスト承認者', '')],
           ['承認の内容', a.get('承認の内容', '') or '□ 全件承認　　□ 修正依頼あり（表の「修正依頼」欄にご記入ください）'],
           ['その他のご意見', '']], [50, 200], head=False)
    para('ご承認後、承認された項目のみを反映し、最終確認ののち公開いたします。', 9, False, '4F5E56', 0)
    doc.save(out)

def excel(d, out):
    wb = Workbook(); ws = wb.active; ws.title = '更新リスト'
    f = lambda **k: Font(name=FONT, **k)
    thin = Side(style='thin', color='B9C9BF'); box = Border(left=thin, right=thin, top=thin, bottom=thin)
    wrap = Alignment(wrap_text=True, vertical='top')
    ws['A1'] = 'ホームページ更新リスト（ご確認・ご承認のお願い）'; ws['A1'].font = f(size=14, bold=True, color='1F5A3E')
    ws['A2'] = d['title'].replace('更新リスト：', ''); ws['A2'].font = f(size=11, color='4F5E56')
    ws['A3'] = f'作成：{COMPANY}　作成日：{datetime.date.today():%Y-%m-%d}'; ws['A3'].font = f(size=10, color='4F5E56')
    r = 4
    for m in d['meta']: ws.cell(r, 1, '・' + m).font = f(size=10); r += 1
    ws.cell(r + 1, 1, '黄色の列にご記入ください。直してほしい点は「修正依頼」に、各項目の可否は「ご回答」（承認／除外／修正）から選んでください。').font = f(size=10, bold=True, color='9A5B00')
    r += 3
    head = HEAD[:4] + ['修正依頼（ご記入欄）'] + HEAD[4:] + ['ご回答']
    INPUT = (5, 8)  # 記入欄の列
    for j, h in enumerate(head, 1):
        c = ws.cell(r, j, h); c.font = f(bold=True); c.border = box; c.alignment = Alignment(horizontal='center', vertical='center')
        c.fill = PatternFill('solid', fgColor='FFF4CC' if j in INPUT else 'E2F3E9')
    dv = DataValidation(type='list', formula1='"承認,除外,修正"', allow_blank=True); ws.add_data_validation(dv)
    first = r + 1
    for row in d['rows']:
        r += 1
        for j, v in enumerate(row[:4] + [''] + row[4:6] + [''], 1):
            c = ws.cell(r, j, int(v) if j == 1 and v.isdigit() else v); c.font = f(size=10); c.border = box
            c.alignment = Alignment(horizontal='center', vertical='top') if j in (1, 7, 8) else wrap
            if j in INPUT: c.fill = PatternFill('solid', fgColor='FFFBEA')
        dv.add(ws.cell(r, 8)); ws.row_dimensions[r].height = 48
    last = r
    r += 2; ws.cell(r, 1, '確認したいこと').font = f(size=11, bold=True, color='23774F')
    for q in d['questions'] or ['なし']: r += 1; ws.cell(r, 1, '・' + q).font = f(size=10)
    r += 2; ws.cell(r, 1, 'ご承認').font = f(size=11, bold=True, color='23774F')
    a = d['approval']
    for k, v in [('承認日', a.get('更新リスト承認日', '')), ('承認者', a.get('更新リスト承認者', '')),
                 ('承認の内容', a.get('承認の内容', '')),
                 ('回答の集計', f'=COUNTIF(H{first}:H{last},"承認")&"件承認／"&COUNTIF(H{first}:H{last},"除外")&"件除外／"&COUNTIF(H{first}:H{last},"修正")&"件修正（全"&COUNTA(A{first}:A{last})&"件）"')]:
        r += 1
        ws.cell(r, 2, k).font = f(size=10, bold=True); ws.cell(r, 2).border = box
        ws.merge_cells(start_row=r, start_column=3, end_row=r, end_column=5)
        c = ws.cell(r, 3, v); c.font = f(size=10); c.border = box
        if k != '回答の集計' and not v: c.fill = PatternFill('solid', fgColor='FFFBEA')
    for col, w in zip('ABCDEFGH', [6, 28, 30, 30, 34, 24, 10, 12]): ws.column_dimensions[col].width = w
    ws.freeze_panes = ws.cell(first, 1)
    ws.page_setup.orientation = 'landscape'; ws.page_setup.fitToWidth = 1; ws.page_setup.fitToHeight = 0
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    wb.save(out)

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('md'); ap.add_argument('--to', default='送付用'); A = ap.parse_args()
    md = pathlib.Path(A.md); d = parse(md)
    if not d['rows']: sys.exit('更新リストの表が空です')
    to = pathlib.Path(A.to); to.mkdir(parents=True, exist_ok=True)
    word(d, to / (md.stem + '.docx')); excel(d, to / (md.stem + '.xlsx'))
    print(f'{len(d["rows"])}件 → {to / (md.stem + ".docx")} / {to / (md.stem + ".xlsx")}')
