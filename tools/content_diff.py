"""サイトの「変更前 → 変更後」一覧（文章データ＋テンプレートの変更行）を Markdown で出す（PR本文・確認用）。
  python3 tools/content_diff.py [比較元 git ref、既定 origin/main]
"""
import json, sys, subprocess, difflib
from kitcfg import ROOT, CFG
ref = sys.argv[1] if len(sys.argv) > 1 else 'origin/main'
cpath = CFG.get('content', 'content/text.json')
show = lambda p: subprocess.run(['git', '-C', str(ROOT), 'show', f'{ref}:{p}'], capture_output=True, check=True).stdout.decode('utf-8')
old = json.loads(show(cpath)); new = json.loads((ROOT / cpath).read_text(encoding='utf-8'))
cut = lambda s, n=140: (s if len(s) <= n else s[:n] + '…').replace('|', '／').replace('\n', ' ')
rows = [(k, old.get(k), new.get(k)) for k in list(new) + [k for k in old if k not in new] if old.get(k) != new.get(k)]
if rows:
    print(f'文章の変更：{len(rows)}か所\n\n| 場所（キー） | 変更前 | 変更後 |\n|---|---|---|')
    for k, o, n in rows: print(f"| `{k}` | {cut(o) if o is not None else '（追加）'} | {cut(n) if n is not None else '（削除）'} |")
else:
    print(f'文章（{cpath}）の変更なし')
ot = show('src/template.html').splitlines(); nt = (ROOT / 'src/template.html').read_text(encoding='utf-8').splitlines()
d = [l for l in difflib.unified_diff(ot, nt, lineterm='', n=0) if l[:1] in '+-' and l[:3] not in ('+++', '---')]
if d:
    print(f'\nテンプレート（金額・リンク・レイアウト等）の変更：{len(d)}行\n\n```diff')
    for l in d[:60]: print(l[:200])
    print('```')
