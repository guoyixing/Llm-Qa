from __future__ import annotations

import unittest

from tools.send_mail import MailError, SafeHtmlParser


class SafeHtmlParserTests(unittest.TestCase):
    def test_accepts_utf8_charset_meta(self) -> None:
        # Given
        html = '<html><head><meta charset="utf-8"></head><body>日报</body></html>'
        parser = SafeHtmlParser()

        # When
        parser.feed(html)
        parser.close()

        # Then
        self.assertEqual(parser.seen_structure, {"html", "body"})
        self.assertFalse(parser.open_structure)

    def test_rejects_other_meta_variants(self) -> None:
        # Given
        invalid_tags = (
            '<meta charset="utf-16">',
            '<meta charset="utf-8" content="extra">',
            '<meta http-equiv="refresh" content="0">',
        )

        # When / Then
        for tag in invalid_tags:
            with self.subTest(tag=tag):
                parser = SafeHtmlParser()
                with self.assertRaises(MailError) as caught:
                    parser.feed(f"<html><head>{tag}</head><body>日报</body></html>")
                self.assertEqual(caught.exception.code, "HTML内容不安全")


if __name__ == "__main__":
    unittest.main()
