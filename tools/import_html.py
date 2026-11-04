"""既存のHTMLをサイトキットに取り込む（最初に1回）。
  python3 tools/import_html.py <既存.html>
- 文章（日本語を含む部分）を content の JSON に出し、テンプレートでは ⟦キー⟧ に置き換える
- 埋め込み画像（data:image/…;base64）を assets/img/ に書き出し、テンプレートでは {{IMG_n}} に置き換えて site.json に登録
- 取り込み後に build.py で元のHTMLと同じものが出ることを確認する（--verify で自動確認）
"""
import re, json, sys, base64, hashlib, argparse
from kitcfg import ROOT, CFG
ap = argparse.ArgumentParser(); ap.add_argument('html'); ap.add_argument('--verify', action='store_true'); A = ap.parse_args()
t = open(A.html, encoding='utf-8').read(); orig = t

# 1) 画像
imgs = {}; ext = {'png': 'png', 'jpeg': 'jpg', 'jpg': 'jpg', 'webp': 'webp', 'gif': 'gif', 'svg+xml': 'svg'}
def img(m):
    kind, data = m.group(1), m.group(2)
    raw = base64.b64decode(data); h = hashlib.sha1(raw).hexdigest()[:8]
    key = next((k for k, v in imgs.items() if v[1] == h), None)
    if not key:
        key = f'IMG_{len(imgs) + 1}'; name = f'img-{len(imgs) + 1}-{h}.{ext.get(kind, "bin")}'
        (ROOT / 'assets/img').mkdir(parents=True, exist_ok=True); (ROOT / 'assets/img' / name).write_bytes(raw); imgs[key] = (name, h)
    return '{{' + key + '}}'
t = re.sub(r'data:image/([\w+.-]+);base64,([A-Za-z0-9+/=]+)', img, t)

# 2) 文章
JP = re.compile(r'[぀-ヿ㐀-鿿！-｠　-〿]')
SEG = re.compile(r'[^<>{}`"\'$\\\n]+')
keys, cnt = {}, {}
def context(pos):
    m = list(re.finditer(r"function (\w+)\(|const (\w+)\s*=|\{id:'([\w-]+)'|<section[^>]*?(?:id|class)=\"([\w-]+)|<(header|footer|nav|title)\b", t[max(0, pos - 30000):pos]))
    if not m: return 'page'
    return next(x for x in m[-1].groups() if x)
def proc(chunk, base):
    res = []; last = 0
    for m in SEG.finditer(chunk):
        s = m.group(0)
        if not JP.search(s): continue
        core = s.strip(' \t,:;')
        if not core or ';' in core or '=>' in core or '/[' in core or '&&' in core or core.startswith('//'): continue
        a = m.start() + s.index(core); b = a + len(core)
        if core not in keys:
            c = context(base + a); cnt[c] = cnt.get(c, 0) + 1; keys[core] = f'{c}.{cnt[c]:03d}'
        res.append(chunk[last:a]); res.append('⟦' + keys[core] + '⟧'); last = b
    res.append(chunk[last:]); return ''.join(res)
parts = re.split(r'(<style[^>]*>.*?</style>)', t, flags=re.S)   # CSS は対象外
t2 = ''.join(p if p.startswith('<style') else proc(p, sum(len(x) for x in parts[:i])) for i, p in enumerate(parts))
content = {v: k for k, v in keys.items()}
(ROOT / 'src').mkdir(exist_ok=True); (ROOT / 'src/template.html').write_text(t2, encoding='utf-8')
cp = ROOT / CFG.get('content', 'content/text.json'); cp.parent.mkdir(exist_ok=True)
cp.write_text(json.dumps(content, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
cfg = json.loads((ROOT / 'site.json').read_text(encoding='utf-8')); cfg['images'] = {k: v[0] for k, v in imgs.items()}
(ROOT / 'site.json').write_text(json.dumps(cfg, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
print(f'文章 {len(content)}項目、画像 {len(imgs)}枚を取り込み')

if A.verify:   # 文章と画像を戻すと元と同じになるか
    back = re.sub('⟦([^⟧]+)⟧', lambda m: content[m.group(1)], t2)
    restored = back
    for k, (name, h) in imgs.items():
        raw = (ROOT / 'assets/img' / name).read_bytes(); b64 = base64.b64encode(raw).decode()
        m = re.search(r'data:image/([\w+.-]+);base64,' + re.escape(b64[:60]), orig)
        restored = restored.replace('{{' + k + '}}', f'data:image/{m.group(1)};base64,{b64}')
    print('元のHTMLと一致：', restored == orig)
    sys.exit(0 if restored == orig else 1)
