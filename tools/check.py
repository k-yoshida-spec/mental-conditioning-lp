"""公開前チェック（サイトキット共通）。問題があれば終了コード1。
  python3 tools/check.py      dist/ を 1280px と 390px で開き、JSエラー・横はみ出し・画像切れを検査。
  site.json の nav_selector があれば、そのボタンで切り替わる全ページを検査。mode=element ならカスタムエレメントも検査。
  スクリーンショットは shots/ へ。
"""
import asyncio, sys, threading, http.server, functools
from playwright.async_api import async_playwright
from kitcfg import ROOT, CFG
D = ROOT / 'dist'; S = ROOT / 'shots'; S.mkdir(exist_ok=True)
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Q, directory=str(D)))
threading.Thread(target=srv.serve_forever, daemon=True).start()
U = f'http://127.0.0.1:{srv.server_address[1]}/'
NAV = CFG.get('nav_selector') or ''
bad = []
BROKEN = '[...document.images].filter(i=>i.complete&&i.offsetParent&&!i.naturalWidth).map(i=>i.src.slice(-50))'
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for w in (1280, 390):
            pg = await b.new_page(viewport={'width': w, 'height': 900}); errs = []
            pg.on('pageerror', lambda e: errs.append(str(e)))
            for h in ('**/fonts.googleapis.com/**', '**/fonts.gstatic.com/**'): await pg.route(h, lambda r: r.abort())
            await pg.goto(U + 'index.html'); await pg.wait_for_timeout(1000)
            ids = await pg.eval_on_selector_all(NAV, 'e=>[...new Set(e.map(x=>x.dataset.go))]') if NAV else []
            for g in (ids or ['index']):
                if g != 'index':
                    await pg.evaluate("([s,g])=>[...document.querySelectorAll(s)].find(e=>e.dataset.go===g).click()", [NAV, g]); await pg.wait_for_timeout(400)
                ov = await pg.evaluate('document.documentElement.scrollWidth-innerWidth')
                if ov > 1: bad.append(f'{w}px {g}: 横にはみ出し {ov}px')
                br = await pg.evaluate(BROKEN)
                if br: bad.append(f'{w}px {g}: 画像が表示されない {br}')
                await pg.screenshot(path=str(S / f'{g}_{w}.png'), full_page=True)
            bad.extend(f'{w}px JSエラー: {e}' for e in errs); await pg.close()
        if CFG.get('mode') == 'element':
            tag = CFG['tag']
            pg = await b.new_page(viewport={'width': 1280, 'height': 900}); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
            await pg.goto(U + 'test-ce.html'); await pg.wait_for_timeout(1500)
            h = await pg.evaluate(f"parseInt(document.querySelector('{tag}').style.height)||0")
            if h < 200: bad.append(f'カスタムエレメントの高さが不足 {h}px')
            br = await pg.evaluate(f"[...document.querySelector('{tag}').shadowRoot.querySelectorAll('img')].filter(i=>i.complete&&i.offsetParent&&!i.naturalWidth).length")
            if br: bad.append(f'カスタムエレメント: 表示されない画像 {br}件')
            await pg.screenshot(path=str(S / 'element_1280.png'), full_page=True)
            bad.extend(f'カスタムエレメント JSエラー: {e}' for e in errs)
        await b.close()
asyncio.run(main())
print('\n'.join(bad) if bad else 'チェック合格'); sys.exit(1 if bad else 0)
