# bips2bib

Generate a BibTeX file from the [BIPs repository](https://github.com/bitcoin/bips) (Bitcoin Improvement Proposals).

### Usage

``` sh
uv run bips2bip /path/to/bips/repo -o bips.bib
```

BibLaTeX/biber is recommended but the good old BibTeX should also supported.

This tool uses some heuristics for title casing BIP titles
as well as for wrapping words such as "Bitcoin" in curly braces to prevent them being forced to lowercase by the bibliography style.
Please open an issue for any cases of failing heuristics.

### Just need the latest BibTeX file?

Grab the artifact from the latest (nightly) run of the [GitHub Actions workflow](https://github.com/real-or-random/bips2bib/actions/workflows/generate-bib.yml?query=branch%3Amain+is%3Asuccess).
