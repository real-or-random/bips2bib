import unittest
from pathlib import Path

from bips2bib.generate import bib_entry, parse_preamble


class GenerateTests(unittest.TestCase):
    def test_bib_entry_supports_legacy_author_and_created_fields(self) -> None:
        fields = parse_preamble(
            [
                "BIP: 1",
                "Title: Legacy Example",
                "Author: Satoshi Nakamoto <satoshi@example.com>",
                "Created: 2008-08-18",
            ]
        )

        result = bib_entry(fields, Path("bip-0001.mediawiki"))

        self.assertIsNotNone(result)
        assert result is not None
        _, entry = result
        self.assertIn("author       = {Satoshi Nakamoto},", entry)
        self.assertIn("year         = {2008},", entry)

    def test_bib_entry_supports_current_authors_and_assigned_fields(self) -> None:
        fields = parse_preamble(
            [
                "BIP: 340",
                "Title: Schnorr Signatures for secp256k1",
                "Authors: Pieter Wuille <pieter.wuille@gmail.com>",
                "         Jonas Nick <jonas@example.com>",
                "Assigned: 2020-01-19",
            ]
        )

        result = bib_entry(fields, Path("bip-0340.mediawiki"))

        self.assertIsNotNone(result)
        assert result is not None
        _, entry = result
        self.assertIn("author       = {Pieter Wuille and Jonas Nick},", entry)
        self.assertIn("year         = {2020},", entry)


if __name__ == "__main__":
    unittest.main()
