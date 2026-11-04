# 運用手順（サイトキット共通）

このリポジトリのサイトを、誰がいつやっても同じ結果で更新するための手順。詳しい経緯と実例は `k-yoshida-spec/ka-anshin` の `docs/RUNBOOK.md`。

## 1. 仕組み

```
更新資料 → Claude：差分・更新リスト（md＋送付用 Word・Excel）→ 承認①（クライアント／薫さん）
        → Claude：承認分だけ反映・PR → Actions：承認記録・ビルド・画面チェック → 承認②：マージ → 自動公開
```

- 公開先は `site.json` の `production_url`（Cloudflare Pages）。`github_pages: true` なら GitHub Pages にも予備公開。
- `mode: element` のときは `dist/<tag>.js` を Wix のカスタムエレメント（サーバーURL）に設定して使う。

## 2. 更新の手順（更新リスト＋2段階承認）

| 段階 | 誰 | やること |
|---|---|---|
| ① 資料を渡す | 依頼者 | PP・Word・Excel・PDF・テキスト・メモ・画像（フォルダ `PP/` か チャット） |
| ② 差分 | Claude | `source_extract.py` → `source_diff.py sources/last-<形式>.json`（前回分が無ければ今のサイトと直接突き合わせ） |
| ③ 更新リスト | Claude | `docs/updates/YYYYMMDD-<名前>.md`（雛形 TEMPLATE.md）＋ `update_list_export.py` で `送付用/` に Word・Excel |
| ④ **承認①** | クライアント／薫さん | 「全件承認」または修正依頼。記入済み Word・Excel でも可 → md の承認欄に記録 |
| ⑤ 反映・PR | Claude | 承認分だけ `content/text.json`／`src/template.html` を修正 → `build.py` → `content_diff.py` → PR |
| ⑥ **承認②** | 薫さん | PR をマージ（＝公開） |
| ⑦ 公開確認 | Claude | 公開先で新しい文言・画像を確認 |

判断のルール：意味の変更だけを載せる／置き場が合わない・不確かなものは「要確認」／承認後にリスト外の変更を足さない／1回の PR は1資料分／公開後の問題は Revert。

## 3. コマンド

```bash
T=$(tr -d ' \r\n' < ../ka-anshin/gh_token.txt); A="Authorization: Basic $(printf 'x-access-token:%s' "$T" | base64 -w0)"
git -c http.extraHeader="$A" fetch -q origin && git checkout -q -B update-YYYYMMDD origin/main
python3 tools/source_extract.py "PP/<資料>" /tmp/new.json && python3 tools/source_diff.py sources/last-<形式>.json /tmp/new.json
cp docs/updates/TEMPLATE.md docs/updates/YYYYMMDD-<名前>.md && python3 tools/update_list_export.py docs/updates/YYYYMMDD-<名前>.md
# 承認①を記入 → 反映
python3 tools/build.py && python3 tools/content_diff.py origin/main > /tmp/diff.md && cp /tmp/new.json sources/last-<形式>.json
git add content src sources docs && git commit -m "更新: <資料名>" && git -c http.extraHeader="$A" push -u origin update-YYYYMMDD
```

## 4. 障害時

| 症状 | 対応 |
|---|---|
| 更新後に表示が崩れた | 該当 PR の Revert（戻しも更新リスト＋承認①） |
| Cloudflare が止まった | element：Wix のサーバーURLを予備（GitHub Pages）へ／static：DNS の CNAME を予備へ |
| GitHub が止まった | 公開中のページは影響なし。更新のみ待つ |
