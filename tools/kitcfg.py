"""site.json の読み込み（全ツール共通）。"""
import json, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
CFG = json.loads((ROOT / 'site.json').read_text(encoding='utf-8'))
def content_path(lang='ja'):
    base = ROOT / CFG.get('content', 'content/text.json')
    alt = base.with_name(f'{base.stem}.{lang}{base.suffix}')
    return alt if alt.exists() else base
