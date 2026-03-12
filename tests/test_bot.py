import json
import pathlib
import unittest

import bot


class BotTest(unittest.TestCase):
    def setUp(self):
        bot.QUEUE_PATH.write_text("[]\n", encoding="utf-8")
        bot.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        for md_file in bot.OUTPUT_DIR.glob("*.md"):
            md_file.unlink()

    def test_create_draft_writes_markdown_and_queue(self):
        draft = bot.create_draft(
            theme="雨の東京と記憶の改ざん",
            tone="しっとり不穏",
            target_length=800,
            publish_at="2026-03-20T08:00:00+09:00",
            style="mystery",
            structure="3-act",
            ending_type="twist",
            include_keywords=["赤い傘", "ノイズ"],
            seed=42,
        )

        md_path = pathlib.Path(bot.ROOT / draft.markdown_path)
        self.assertTrue(md_path.exists())
        self.assertGreaterEqual(draft.quality_score, 60)

        queue = json.loads(bot.QUEUE_PATH.read_text(encoding="utf-8"))
        self.assertEqual(len(queue), 1)
        self.assertEqual(queue[0]["title"], draft.title)
        self.assertEqual(queue[0]["status"], "draft")
        self.assertEqual(queue[0]["keywords"], ["赤い傘", "ノイズ"])

    def test_parse_keywords(self):
        self.assertEqual(bot.parse_keywords("駅, 記憶,  "), ["駅", "記憶"])
        self.assertEqual(bot.parse_keywords(""), [])


if __name__ == "__main__":
    unittest.main()
