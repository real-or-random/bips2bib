from pathlib import Path

from bips2bib.generate import generate_bib

def app() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate a BibTeX file from the BIPs repository"
    )
    parser.add_argument("bips_dir", help="Root directory of the bitcoin/bips repo")
    default_output = "bips.bib"
    parser.add_argument(
        "-o", "--output", default=default_output, help="Output .bib file"
    )
    args = parser.parse_args()
    generate_bib(Path(args.bips_dir), Path(args.output))
