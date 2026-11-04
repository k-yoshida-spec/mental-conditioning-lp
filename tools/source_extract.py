"""更新資料（PP・Word・Excel・PDF・テキスト）から文章を取り出し、差分用の JSON にする。
  python3 tools/source_extract.py <資料> [出力.json]
出力: {"file", "kind", "units":[{"no","title","texts":[…],"notes":[…]}]}
  単位: PP＝スライド / Word＝見出しで区切った節 / Excel＝シート / PDF＝ページ / テキスト＝見出し(#)で区切った節
"""
import json, sys, pathlib

def unit(no, title, texts, notes=None):
    return {'no': no, 'title': title, 'texts': texts, 'notes': notes or []}

def pptx(path):
    from pptx import Presentation
    from pptx.util import Emu
    def st(sh):
        out = []
        if sh.shape_type == 6 and hasattr(sh, 'shapes'):
            for s in sh.shapes: out += st(s)
        if getattr(sh, 'has_table', False) and sh.has_table:
            for row in sh.table.rows:
                cells = [c.text.strip().replace('\n', ' ') for c in row.cells]
                if any(cells): out.append(' | '.join(cells))
        if getattr(sh, 'has_text_frame', False) and sh.has_text_frame:
            for p in sh.text_frame.paragraphs:
                t = p.text.replace('\v', ' ').strip()
                if t: out.append(t)
        return out
    us = []
    for i, s in enumerate(Presentation(path).slides, 1):
        texts = []
        for sh in sorted(s.shapes, key=lambda x: ((x.top or Emu(0)), (x.left or Emu(0)))): texts += st(sh)
        notes = [l.strip() for l in s.notes_slide.notes_text_frame.text.splitlines() if l.strip()] if s.has_notes_slide else []
        us.append(unit(i, texts[0] if texts else '', texts, notes))
    return us

def sections(lines, is_head):
    us, cur = [], None
    for l in lines:
        if is_head(l) or cur is None:
            cur = unit(len(us) + 1, l, []); us.append(cur)
        cur['texts'].append(l)
    return us

def docx(path):
    import docx as D
    d = D.Document(path); lines, heads = [], set()
    body = d.element.body
    for el in body.iterchildren():
        tag = el.tag.split('}')[-1]
        if tag == 'p':
            p = D.text.paragraph.Paragraph(el, d)
            t = p.text.strip()
            if t:
                lines.append(t)
                if (p.style is not None and p.style.name.lower().startswith(('heading', '見出し', 'title'))): heads.add(len(lines) - 1)
        elif tag == 'tbl':
            for row in D.table.Table(el, d).rows:
                cells = [c.text.strip().replace('\n', ' ') for c in row.cells]
                if any(cells): lines.append(' | '.join(cells))
    idx = iter(range(len(lines)))
    return sections(lines, lambda l, _i=idx: next(_i) in heads)

def xlsx(path):
    import openpyxl
    wb = openpyxl.load_workbook(path, data_only=True); us = []
    for ws in wb.worksheets:
        rows = []
        for r in ws.iter_rows(values_only=True):
            cells = ['' if v is None else str(v).strip() for v in r]
            while cells and not cells[-1]: cells.pop()
            if any(cells): rows.append(' | '.join(cells))
        us.append(unit(len(us) + 1, ws.title, rows))
    return us

def pdf(path):
    import pdfplumber
    us = []
    with pdfplumber.open(path) as d:
        for i, pg in enumerate(d.pages, 1):
            lines = [l.strip() for l in (pg.extract_text() or '').splitlines() if l.strip()]
            us.append(unit(i, lines[0] if lines else '', lines))
    return us

def text(path):
    lines = [l.rstrip() for l in pathlib.Path(path).read_text(encoding='utf-8').splitlines() if l.strip()]
    return sections(lines, lambda l: l.lstrip().startswith('#'))

KINDS = {'.pptx': pptx, '.docx': docx, '.xlsx': xlsx, '.pdf': pdf, '.txt': text, '.md': text}

def extract(path):
    ext = pathlib.Path(path).suffix.lower()
    if ext not in KINDS: sys.exit(f'未対応の形式です: {ext}（対応: {", ".join(KINDS)}）。画像やGoogle形式は Claude が直接読んで更新リストを作ります。')
    return {'file': pathlib.Path(path).name, 'kind': ext[1:], 'units': KINDS[ext](path)}

if __name__ == '__main__':
    d = extract(sys.argv[1]); s = json.dumps(d, ensure_ascii=False, indent=1)
    if len(sys.argv) > 2:
        pathlib.Path(sys.argv[2]).write_text(s + '\n', encoding='utf-8')
        print(f"{d['kind']}：{len(d['units'])}単位を抽出 → {sys.argv[2]}")
    else: print(s)
