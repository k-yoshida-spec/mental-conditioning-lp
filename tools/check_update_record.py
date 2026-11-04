"""PR の承認記録チェック（GitHub Actions で実行）。
サイトの中身（content/ src/ assets/）を変える PR には、承認済みの更新リスト docs/updates/YYYYMMDD-*.md が必要。
  python3 tools/check_update_record.py <比較元 ref（例 origin/main）>
"""
import re, sys, subprocess, pathlib
base = sys.argv[1] if len(sys.argv) > 1 else 'origin/main'
files = subprocess.run(['git', 'diff', '--name-only', f'{base}...HEAD'], capture_output=True, text=True, check=True).stdout.split()
site = [f for f in files if f.startswith(('content/', 'src/', 'assets/'))]
if not site: print('サイトの中身の変更なし：更新リスト不要'); sys.exit(0)
if subprocess.run(['git', 'cat-file', '-e', f'{base}:site.json'], capture_output=True).returncode != 0:
    print('初期構築（比較元に site.json が無い）：更新リスト不要'); sys.exit(0)
recs = [f for f in files if re.match(r'docs/updates/\d{8}-.+\.md$', f) and pathlib.Path(f).exists()]
if not recs:
    print('NG：サイトの中身を変えていますが、更新リスト（docs/updates/YYYYMMDD-*.md）がありません。'); sys.exit(1)
ng = []
for f in recs:
    t = pathlib.Path(f).read_text(encoding='utf-8')
    if not re.search(r'^- 更新リスト承認者：[ \t]*\S+', t, re.M): ng.append(f'{f}：承認者が空欄')
    if not re.search(r'^- 更新リスト承認日：[ \t]*\d{4}-\d{2}-\d{2}', t, re.M): ng.append(f'{f}：承認日が空欄')
    if not re.search(r'^\|\s*1\s*\|', t, re.M): ng.append(f'{f}：更新リストの表（No.1〜）がない')
if ng: print('NG：\n' + '\n'.join(ng)); sys.exit(1)
print('OK：承認済みの更新リスト ' + ', '.join(recs))
