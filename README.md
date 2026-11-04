# mental-conditioning-lp

「働く心のコンディショナー」LP。`ka-site-kit` の構成（文章は `content/text.json`、レイアウトは `src/template.html`、画像は `assets/img/`）で管理し、更新は更新リスト＋2段階承認で行う。

- 予備の公開先：https://k-yoshida-spec.github.io/mental-conditioning-lp/（GitHub Pages、Source＝GitHub Actions）
- 本番の公開先：Cloudflare Pages（独自ドメイン設定後に site.json の production_url を更新）

---

## サイトキットについて

合同会社K&Aプロジェクトのサイト制作キット（テンプレートリポジトリ）。
A「安心・安全」ページ（`ka-anshin`）で作った仕組みを、どのページ・LPでも使えるようにしたもの。

**仕組み**：文章は `content/text.json`、レイアウトは `src/template.html`、画像は `assets/img/`。
更新は「更新リスト → 承認① → PR → 承認②（マージ）→ 自動公開」。承認①の無い変更は Actions が止める。

## 新しいサイト・LPの始め方

1. GitHub でこのリポジトリの「Use this template」→ 新しいリポジトリを作る（例 `lp-<名前>`）
2. `site.json` を書き換える（name・title・mode・tag・target・production_url）
   - `mode: "static"` … そのまま公開するページ（LP など）
   - `mode: "element"` … Wix などに埋め込むカスタムエレメント（`<tag>.js` を生成）
3. 既存の HTML があれば取り込む：`python3 tools/import_html.py <既存.html> --verify`（文章と埋め込み画像を分離。「元のHTMLと一致：True」を確認）
4. `python3 tools/build.py && python3 tools/check.py`
5. Cloudflare Pages に接続（Build command `python3 tools/build.py`、Output `dist`、Production branch `main`）
   - 独自ドメイン：Cloudflare の「Custom domains」に追加し、DNS（ak-analytics.jp は Wix で管理）に CNAME を1行追加
6. 予備の配信が要るなら `site.json` の `github_pages: true` と、GitHub の Settings → Pages → Source を「GitHub Actions」に

## ファイル

| パス | 役割 |
|---|---|
| `site.json` | サイトの設定（名前・方式・タグ・送付用の会社名と対象・画像の記号・公開先） |
| `src/template.html` | レイアウト。文章は `⟦キー⟧`、画像は `{{記号}}` |
| `content/text.json` | 文章。翻訳は `text.en.json` を追加して `--lang en` |
| `assets/img/` | 画像 |
| `src/ce_header.js` `src/ce_footer.js` | カスタムエレメントの外枠（mode=element） |
| `tools/build.py` | `dist/` を生成 |
| `tools/check.py` | 公開前チェック（1280px/390px、JSエラー、はみ出し、画像、カスタムエレメント） |
| `tools/import_html.py` | 既存HTMLの取り込み（最初に1回） |
| `tools/source_extract.py` `source_diff.py` | 更新資料（pptx/docx/xlsx/pdf/txt/md）の抽出と前回分との差分 |
| `tools/content_diff.py` | 「変更前→変更後」一覧 |
| `tools/update_list_export.py` | 更新リストのクライアント送付用 Word・Excel（修正依頼欄つき） |
| `tools/check_update_record.py` | 承認済み更新リストの有無を PR で検査 |
| `docs/RUNBOOK.md` | 更新の手順 |
| `docs/updates/` | 更新リストと承認の記録 |
