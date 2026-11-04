"""前回反映した資料（sources/last-<形式>.json）と新しい資料の差分を、単位（スライド・節・シート・ページ）ごとに出す。
  python3 tools/source_diff.py sources/last-pptx.json /tmp/new.json
同じ形式の資料どうしで比べる。前回分が無い形式は「比較なし」と出し、資料全体を今のサイトと突き合わせて更新リストを作る。
"""
import json, sys, difflib, pathlib
if not pathlib.Path(sys.argv[1]).exists():
    print(f'比較なし（{sys.argv[1]} がありません）。資料全体を今のサイトの文章と突き合わせて更新リストを作ってください。'); sys.exit(0)
a = json.load(open(sys.argv[1], encoding='utf-8')); b = json.load(open(sys.argv[2], encoding='utf-8'))
ua = a.get('units') or a.get('slides'); ub = b.get('units') or b.get('slides')
A = {s['no']: s for s in ua}; B = {s['no']: s for s in ub}
out = []
for no in sorted(set(A) | set(B)):
    sa, sb = A.get(no), B.get(no)
    if not sa: out.append(f"### {no}（追加）「{sb['title']}」\n" + '\n'.join('+ ' + t for t in sb['texts'] + sb['notes'])); continue
    if not sb: out.append(f"### {no}（削除）「{sa['title']}」"); continue
    parts = []
    for name, la, lb in (('本文', sa['texts'], sb['texts']), ('ノート', sa['notes'], sb['notes'])):
        d = [l for l in difflib.ndiff(la, lb) if l[:2] in ('- ', '+ ')]
        if d: parts.append(f"**{name}**\n" + '\n'.join(d))
    if parts: out.append(f"### {no}「{sb['title']}」\n" + '\n\n'.join(parts))
print('\n\n'.join(out) if out else '変更なし（前回反映した資料と同じです）')
