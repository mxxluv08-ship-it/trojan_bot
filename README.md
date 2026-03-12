# note AI短編小説 自動投稿ボット（試作）

`作ってみて` に応えるための、最小実装プロトタイプです。  
このリポジトリは **短編生成 → Markdown下書き化 → 投稿キュー登録** までを自動化します。

> 注意: noteへの直接投稿APIは公開状況や規約確認が必要です。この試作では安全に、
> まず「下書き生成 + 投稿キュー」までを確実に回せる構成にしています。

## できること

- テーマ・文体・文字数を指定して短編を生成（ローカル生成）
- **作風プリセット**（`moody` / `warm` / `mystery`）を切り替え
- **構成プリセット**（`3-act` / `kishotenketsu`）を切り替え
- **結末タイプ**（`twist` / `hope` / `open`）を指定
- キーワード必須挿入（`--keywords`）
- `quality_score` を算出して下書き品質を可視化
- `output/` に note貼り付け用Markdownを保存
- `data/post_queue.json` に投稿予定として自動登録

## セットアップ

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 使い方

```bash
python3 bot.py create \
  --theme "雨の東京と記憶の改ざん" \
  --tone "しっとり、少し不穏" \
  --style mystery \
  --structure 3-act \
  --ending twist \
  --keywords "赤い傘,ノイズ,終電" \
  --target-length 1200 \
  --publish-at "2026-03-20T08:00:00+09:00" \
  --seed 42
```

実行後:

- `output/YYYYMMDD_slug.md` が作成される
- `data/post_queue.json` にエントリが追加される
- CLIに `quality_score` が表示される

## 「もっと突き詰める」運用アイデア

- `--style` と `--ending` を曜日で固定し、読者に期待値を作る
- `--keywords` に前話の固有名詞を渡して連載感を強化
- `quality_score` がしきい値未満（例: 75未満）なら人間レビューへ回す

## 次にやる拡張

1. LLM API接続（OpenAIなど）
2. `quality_score` に読了率/反応データを反映
3. note投稿アダプタ（規約順守・公式手段優先）
4. 人間承認UI（Slack/Discordボタン）

