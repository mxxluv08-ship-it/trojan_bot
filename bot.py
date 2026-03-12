#!/usr/bin/env python3
from __future__ import annotations

import argparse
import dataclasses
import datetime as dt
import json
import pathlib
import random
import re
import textwrap
import uuid

ROOT = pathlib.Path(__file__).parent
QUEUE_PATH = ROOT / "data" / "post_queue.json"
OUTPUT_DIR = ROOT / "output"


@dataclasses.dataclass
class StoryDraft:
    id: str
    title: str
    theme: str
    tone: str
    style: str
    structure: str
    body: str
    tags: list[str]
    quality_score: int
    created_at: str
    publish_at: str | None
    markdown_path: str


@dataclasses.dataclass(frozen=True)
class StoryBlueprint:
    opener: str
    middle: str
    climax: str
    ending: str


STYLE_PRESETS: dict[str, dict[str, list[str] | str]] = {
    "moody": {
        "title_suffix": "の向こう側",
        "mood_words": ["湿度", "静寂", "残響", "気配"],
        "hook": "一行目で異変を置く",
    },
    "warm": {
        "title_suffix": "に灯る朝",
        "mood_words": ["ぬくもり", "呼吸", "光", "微笑み"],
        "hook": "一行目で小さな希望を置く",
    },
    "mystery": {
        "title_suffix": "の未解決ファイル",
        "mood_words": ["証拠", "矛盾", "痕跡", "視線"],
        "hook": "一行目で矛盾した事実を置く",
    },
}

STRUCTURE_PRESETS: dict[str, list[str]] = {
    "3-act": ["opener", "middle", "climax", "ending"],
    "kishotenketsu": ["opener", "middle", "turn", "ending"],
}


class LocalStoryGenerator:
    """投稿向けに調整可能なローカル短編ジェネレーター。"""

    def generate(
        self,
        *,
        theme: str,
        tone: str,
        target_length: int,
        style: str,
        structure: str,
        ending_type: str,
        include_keywords: list[str],
        seed: int | None,
    ) -> tuple[str, str, list[str], int]:
        if style not in STYLE_PRESETS:
            raise ValueError(f"unknown style: {style}")
        if structure not in STRUCTURE_PRESETS:
            raise ValueError(f"unknown structure: {structure}")

        rng = random.Random(seed)
        title = self._build_title(theme, style)
        blueprint = self._build_blueprint(theme, tone, style, ending_type, include_keywords, rng)
        paragraphs = self._assemble_paragraphs(blueprint, structure)
        paragraphs = self._expand_to_length(paragraphs, theme, tone, target_length, style)
        body = "\n\n".join(paragraphs)
        tags = ["AI小説", "短編", "note", style]
        quality = self._score_story(title=title, body=body, include_keywords=include_keywords)
        return title, body, tags, quality

    def _build_title(self, theme: str, style: str) -> str:
        seed = theme.strip().split("と")[0]
        suffix = str(STYLE_PRESETS[style]["title_suffix"])
        return f"{seed}{suffix}"

    def _build_blueprint(
        self,
        theme: str,
        tone: str,
        style: str,
        ending_type: str,
        include_keywords: list[str],
        rng: random.Random,
    ) -> StoryBlueprint:
        mood_word = rng.choice(list(STYLE_PRESETS[style]["mood_words"]))
        keyword_sentence = ""
        if include_keywords:
            keyword_sentence = "重要な断片は、" + "、".join(include_keywords) + "だった。"

        opener = (
            f"その夜、{theme}をめぐる噂は、見えないインクみたいに街へにじんだ。"
            f"私は{tone}声で、最初の違和感——{mood_word}だけが残る沈黙——を記録した。"
        )
        middle = (
            "古いメモ帳のページをめくるたび、昨日まで無かった行が増えていく。"
            "消したはずの名前が、罫線の上で何度も呼吸していた。"
            f"{keyword_sentence}"
        )
        climax = (
            "終電後のホームで監視カメラ映像を止めると、私の背後にだけ影が遅れて現れた。"
            "影は口を開かないまま、次に失う記憶の順番を指で示した。"
        )
        ending = self._ending_sentence(ending_type)
        return StoryBlueprint(opener=opener, middle=middle, climax=climax, ending=ending)

    def _ending_sentence(self, ending_type: str) -> str:
        options = {
            "twist": "朝になって届いた未送信メールの差出人は、今日の私自身だった。",
            "hope": "私はメモ帳を閉じ、失った頁の代わりに新しい一行を書いた。",
            "open": "列車の風がページをめくり、答えのない最終行だけが残った。",
        }
        return options.get(ending_type, options["open"])

    def _assemble_paragraphs(self, blueprint: StoryBlueprint, structure: str) -> list[str]:
        if structure == "3-act":
            return [blueprint.opener, blueprint.middle, blueprint.climax, blueprint.ending]

        turn = (
            "その瞬間、駅の案内表示は行き先を失い、"
            "代わりに私の名前を一文字ずつ流しはじめた。"
        )
        return [blueprint.opener, blueprint.middle, turn, blueprint.ending]

    def _expand_to_length(
        self,
        paragraphs: list[str],
        theme: str,
        tone: str,
        target_length: int,
        style: str,
    ) -> list[str]:
        if len("\n\n".join(paragraphs)) >= target_length:
            return paragraphs

        hook = str(STYLE_PRESETS[style]["hook"])
        filler = (
            f"{hook}を意識して書き直すたび、{theme}の輪郭だけがくっきりしていく。"
            f"それでも{tone}手触りは消えず、物語は私より先に次の頁へ進んだ。"
        )

        while len("\n\n".join(paragraphs)) < target_length:
            paragraphs.insert(-1, filler)
        return paragraphs

    def _score_story(self, title: str, body: str, include_keywords: list[str]) -> int:
        score = 0
        score += 25 if 10 <= len(title) <= 28 else 10
        score += 25 if 700 <= len(body) <= 1800 else 15

        keyword_hits = sum(1 for kw in include_keywords if kw in body)
        if include_keywords:
            score += int(30 * (keyword_hits / len(include_keywords)))
        else:
            score += 20

        paragraph_count = body.count("\n\n") + 1
        score += 20 if 4 <= paragraph_count <= 8 else 10
        return min(score, 100)


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9ぁ-んァ-ン一-龥]+", "-", text)
    return text.strip("-")[:40] or "story"


def ensure_paths() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    QUEUE_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not QUEUE_PATH.exists():
        QUEUE_PATH.write_text("[]\n", encoding="utf-8")


def load_queue() -> list[dict]:
    ensure_paths()
    return json.loads(QUEUE_PATH.read_text(encoding="utf-8"))


def save_queue(items: list[dict]) -> None:
    QUEUE_PATH.write_text(json.dumps(items, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build_markdown(draft: StoryDraft) -> str:
    tags = " ".join(f"#{t}" for t in draft.tags)
    return textwrap.dedent(
        f"""\
        # {draft.title}

        {draft.body}

        ---
        {tags}

        _quality_score: {draft.quality_score}_
        _generated_at: {draft.created_at}_
        """
    )


def create_draft(
    *,
    theme: str,
    tone: str,
    target_length: int,
    publish_at: str | None,
    style: str,
    structure: str,
    ending_type: str,
    include_keywords: list[str],
    seed: int | None,
) -> StoryDraft:
    generator = LocalStoryGenerator()
    title, body, tags, quality = generator.generate(
        theme=theme,
        tone=tone,
        target_length=target_length,
        style=style,
        structure=structure,
        ending_type=ending_type,
        include_keywords=include_keywords,
        seed=seed,
    )

    now = dt.datetime.now(dt.timezone.utc).astimezone()
    date_prefix = now.strftime("%Y%m%d")
    slug = slugify(title)
    filename = f"{date_prefix}_{slug}.md"
    md_path = OUTPUT_DIR / filename

    draft = StoryDraft(
        id=str(uuid.uuid4()),
        title=title,
        theme=theme,
        tone=tone,
        style=style,
        structure=structure,
        body=body,
        tags=tags,
        quality_score=quality,
        created_at=now.isoformat(),
        publish_at=publish_at,
        markdown_path=str(md_path.relative_to(ROOT)),
    )

    md_path.write_text(build_markdown(draft), encoding="utf-8")

    queue = load_queue()
    queue.append(dataclasses.asdict(draft) | {"status": "draft", "keywords": include_keywords})
    save_queue(queue)

    return draft


def parse_keywords(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [item.strip() for item in raw.split(",") if item.strip()]


def cmd_create(args: argparse.Namespace) -> int:
    draft = create_draft(
        theme=args.theme,
        tone=args.tone,
        target_length=args.target_length,
        publish_at=args.publish_at,
        style=args.style,
        structure=args.structure,
        ending_type=args.ending,
        include_keywords=parse_keywords(args.keywords),
        seed=args.seed,
    )
    print(f"created: {draft.markdown_path}")
    print(f"title: {draft.title}")
    print(f"quality_score: {draft.quality_score}")
    print(f"queue: {QUEUE_PATH.relative_to(ROOT)}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="note AI短編ボット（試作）")
    sub = parser.add_subparsers(dest="command", required=True)

    create = sub.add_parser("create", help="短編下書きを生成して投稿キューへ追加")
    create.add_argument("--theme", required=True, help="作品テーマ")
    create.add_argument("--tone", default="静かで余韻がある", help="文体・トーン")
    create.add_argument("--target-length", type=int, default=1200, help="目標文字数")
    create.add_argument("--publish-at", default=None, help="公開予定日時 (ISO8601)")
    create.add_argument("--style", choices=sorted(STYLE_PRESETS.keys()), default="moody", help="作風プリセット")
    create.add_argument("--structure", choices=sorted(STRUCTURE_PRESETS.keys()), default="3-act", help="構成プリセット")
    create.add_argument("--ending", choices=["twist", "hope", "open"], default="twist", help="結末タイプ")
    create.add_argument("--keywords", default="", help="必須キーワード（カンマ区切り）")
    create.add_argument("--seed", type=int, default=None, help="生成の乱数シード（再現性用）")
    create.set_defaults(func=cmd_create)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
