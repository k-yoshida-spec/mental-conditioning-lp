"""ビルド（サイトキット共通）。設定は site.json。
  python3 tools/build.py [--lang ja] [--base https://<公開先>/]
入力 : src/template.html（レイアウト。文章は ⟦キー⟧、画像は {{記号}}）＋ 文章データ（site.json の content）＋ assets/img
出力 : dist/index.html（単体ページ）／ mode が element なら dist/<tag>.js（Wix などに埋め込むカスタムエレメント）と dist/test-ce.html
"""
import json, re, sys, shutil, argparse, os
from kitcfg import ROOT, CFG, content_path

ap = argparse.ArgumentParser(); ap.add_argument('--lang', default='ja'); ap.add_argument('--base', default=os.environ.get('KA_BASE', CFG.get('production_url', '')))
A = ap.parse_args()
IMG = CFG.get('images', {})
tpl = (ROOT / 'src/template.html').read_text(encoding='utf-8')
cf = content_path(A.lang); text = json.loads(cf.read_text(encoding='utf-8'))
errs = []
def tr(m):
    k = m.group(1)
    if k not in text: errs.append('文章データに無いキー: ' + k); return ''
    if not str(text[k]).strip(): errs.append('空の文章: ' + k)
    return str(text[k])
page = re.sub('⟦([^⟧]+)⟧', tr, tpl)
unused = {k for k in set(text) - set(re.findall('⟦([^⟧]+)⟧', tpl)) if not k.startswith('meta.')}
if unused: print('注意: テンプレートで使われていないキー', sorted(unused)[:20])
left = [x for x in re.findall(r'\{\{([A-Z_0-9]+)\}\}', page) if x not in IMG]
if left: errs.append('未処理の差し込み記号: ' + ', '.join(sorted(set(left))))
missing = [f for f in IMG.values() if not (ROOT / 'assets/img' / f).exists()]
if missing: errs.append('assets/img に無い画像: ' + ', '.join(missing))
if errs: print('\n'.join(errs)); sys.exit(1)

D = ROOT / 'dist'; shutil.rmtree(D, ignore_errors=True); (D / 'img').mkdir(parents=True)
for f in (ROOT / 'assets/img').iterdir():
    if f.is_file(): shutil.copy(f, D / 'img' / f.name)

# 1) 単体ページ
std = page
for k, f in IMG.items(): std = std.replace('{{' + k + '}}', 'img/' + f)
desc = text.get('meta.description', '')
if re.match(r'\s*<!doctype', std, re.I):
    html = std
else:   # 断片のテンプレートは文書の形に包む
    L = std.splitlines(True); si = next((i for i, l in enumerate(L) if l.lstrip().startswith('<style')), 0)
    html = ('<!doctype html>\n<html lang="' + A.lang + '">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width,initial-scale=1">\n'
            + ''.join(L[:si]) + (f'<meta name="description" content="{desc}">\n' if desc else '') + '</head>\n<body>\n' + ''.join(L[si:]) + '\n</body>\n</html>\n')
if CFG.get('hide_selector'):
    html = html.replace('</head>', '<style>' + CFG['hide_selector'] + '{display:none!important}</style>\n</head>', 1)
(D / 'index.html').write_text(html, encoding='utf-8')

# 2) カスタムエレメント
if CFG.get('mode') == 'element':
    tag = CFG['tag']
    styles = re.findall(r'<style[^>]*>(.*?)</style>', page, re.S)
    scripts = re.findall(r'<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>', page, re.S)
    body = re.search(r'<body[^>]*>(.*)</body>', page, re.S)
    markup = body.group(1) if body else page
    markup = re.sub(r'<style[^>]*>.*?</style>|<script[^>]*>.*?</script>|<(title|meta|link)\b[^>]*>(.*?</title>)?', '', markup, flags=re.S)
    css = '\n'.join(styles)
    fonts = re.findall(r'<link[^>]+rel=["\']stylesheet["\'][^>]+href=["\']([^"\']+)', page) + re.findall(r'@import\s+url\(["\']?([^"\')]+)', css)
    css = re.sub(r'@import\s+url\([^)]*\)\s*;?', '', css)
    css = (':host{display:block;width:100%}\n.kroot{display:block}\n' + (CFG['hide_selector'] + '{display:none!important}\n' if CFG.get('hide_selector') else '')
           + re.sub(r'(^|[\s,}])(html|body)(?=[\s.:{,])', r'\1.kroot', css.replace(':root', '.kroot')))
    script = '\n'.join(scripts)
    for k, f in IMG.items():
        markup = markup.replace('{{' + k + '}}', '%%B%%img/' + f)
        css = css.replace('{{' + k + '}}', '%%B%%img/' + f)
        for q in '"\'': script = script.replace(q + '{{' + k + '}}' + q, 'KA_B+"img/' + f + '"')
    for r in CFG.get('ce_replace', []):
        assert script.count(r['find']) == 1, '置き換え対象が見つかりません: ' + r['find'][:60]
        script = script.replace(r['find'], (ROOT / r['file']).read_text(encoding='utf-8'))
    cls = ''.join(w.capitalize() for w in re.split(r'[-_]', tag))
    fill = lambda s: s.replace('{{TAG}}', tag).replace('{{CLASS}}', cls).replace('{{TITLE}}', CFG.get('title', ''))
    out = (fill((ROOT / 'src/ce_header.js').read_text(encoding='utf-8'))
           + 'const KA_B=(document.currentScript&&document.currentScript.src)?new URL("./",document.currentScript.src).href:' + json.dumps(A.base) + ';\n'
           + 'const CSS=' + json.dumps(css, ensure_ascii=False) + '.split("%%B%%").join(KA_B);\n'
           + 'const HTML=' + json.dumps('\n' + markup + '\n', ensure_ascii=False) + '.split("%%B%%").join(KA_B);\n'
           + 'const FONTS=' + json.dumps(fonts) + ';\n'
           + 'function run(document,R){\n' + script + '\n}\n'
           + fill((ROOT / 'src/ce_footer.js').read_text(encoding='utf-8')))
    (D / f'{tag}.js').write_text(out, encoding='utf-8')
    (D / 'test-ce.html').write_text(f'<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><style>body{{margin:0;font-family:sans-serif}}</style></head><body><{tag}></{tag}><script src="{tag}.js"></script></body></html>\n', encoding='utf-8')
print('ok', {p.name: p.stat().st_size for p in D.iterdir() if p.is_file()})
