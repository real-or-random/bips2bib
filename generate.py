#!/usr/bin/env python3
import re
import os
from typing import Optional

BIP_ALIASES: dict[int, str] = {
    32: "hdwallets",
    173: "bech32",
    324: "v2transport",
    327: "musig",
    340: "schnorr",
    341: "taproot",
    342: "tapscript",
    350: "bech32m",
    349: "internalkey",
}

ESCAPE_CHARS: dict[str, str] = {
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
    "\\": r"\textbackslash{}",
}


def escape_tex(s: str) -> str:
    """Escape special TeX characters in a string.

    Args:
        s (str): Input string.

    Returns:
        str: Escaped TeX string.
    """
    return "".join(ESCAPE_CHARS.get(c, c) for c in s)


def find_bip_files(bips_dir: str) -> list[str]:
    """Find BIP files in bips_dir.

    Args:
        bips_dir (str): Directory to search.

    Returns:
        list[str]: List of file paths.
    """
    bip_files: list[str] = []
    try:
        for fname in os.listdir(bips_dir):
            if re.match(r"^bip-\d+\.(mediawiki|md)$", fname):
                bip_files.append(os.path.join(bips_dir, fname))
    except Exception as e:
        raise SystemExit(f"ERROR: Failed to list files in {bips_dir!r}: {e}")
    return bip_files


def extract_preamble(path: str) -> Optional[list[str]]:
    """Extract the preamble lines from a BIP file.

    Args:
        path (str): Path to the BIP file.

    Returns:
        Optional[list[str]]: List of preamble lines if found, else None.
    """
    with open(path, encoding="utf-8") as f:
        content = f.read()
    if path.endswith(".mediawiki"):
        m = re.search(r"<pre>\s*(.*?)\s*</pre>", content, re.DOTALL)
    else:
        m = re.search(r"```(.*?)```", content, re.DOTALL)
    if not m:
        return None
    lines = m.group(1).splitlines()
    return [line.rstrip() for line in lines if line.strip()]


def parse_preamble(lines: list[str]) -> dict[str, list[str]]:
    """Parse preamble fields into a dict, handling multiline values.

    Args:
        lines (list[str]): List of preamble lines.

    Returns:
        dict[str, list[str]]: Parsed fields as dictionary.
    """
    fields: dict[str, list[str]] = {}
    key: Optional[str] = None
    for line in lines:
        m = re.match(r"^\s*([A-Za-z0-9\-]+):\s*(.*)$", line)
        if m:
            key = m.group(1)
            value = m.group(2).strip()
            assert key is not None
            fields[key] = [value] if value else []
        elif key is not None:
            fields[key].append(line.strip())
    for k, v in fields.items():
        if k == "Author":
            fields[k] = [" and ".join([strip_email(a) for a in v if a])]
        else:
            fields[k] = [" ".join([x for x in v if x])]
    return fields


def strip_email(author: str) -> str:
    """Remove email from author string.

    Args:
        author (str): Author string, possibly containing email.

    Returns:
        str: Author name without email.
    """
    return re.sub(r"<[^>]+>", "", author).strip()


def bib_entry(fields: dict[str, list[str]], fname: str) -> Optional[tuple[int, str]]:
    """Create a BibTeX entry for the BIP.

    Args:
        fields (dict[str, list[str]]): Parsed preamble fields.
        fname (str): Filename of the BIP.

    Returns:
        Optional[tuple[int, str]]: Tuple of bip_num and BibTeX entry string if data is sufficient, else None.
    """
    bip_num_str: str = fields.get("BIP", [""])[0]
    title: str = fields.get("Title", [""])[0]
    authors: str = fields.get("Author", [""])[0]
    year: str = fields.get("Created", [""])[0][:4]
    url: str = f"https://github.com/bitcoin/bips/blob/master/{os.path.basename(fname)}"

    if (
        not bip_num_str
        or not bip_num_str.isdigit()
        or not title
        or not authors
        or not year
    ):
        print(
            f"WARNING: Insufficient data for BibTeX entry in {fname}: "
            f"BIP={bip_num_str!r} Title={title!r} Author={authors!r} Year={year!r}"
        )
        return None

    bip_num: int = int(bip_num_str)
    lines: list[str] = [f"@manual{{bip:{bip_num},"]
    if bip_num in BIP_ALIASES:
        lines.append(f"  ids          = {{bip:{escape_tex(BIP_ALIASES[bip_num])}}},")
    lines.append(f"  shorthand    = {{BIP{bip_num}}},")
    lines.append(f"  author       = {{{escape_tex(authors)}}},")
    lines.append(f"  title        = {{{escape_tex(title)}}},")
    lines.append(f"  year         = {{{escape_tex(year)}}},")
    lines.append(f"  url          = {{{escape_tex(url)}}},")
    lines.append(
        f"  series       = {{{escape_tex('Bitcoin Improvement Proposal (BIP)')}}},"
    )
    lines.append(f"  number       = {{{bip_num}}},")
    lines.append("}\n")
    entry: str = "\n".join(lines)
    return bip_num, entry


def generate_bib(bips_dir: str, out_path: str) -> None:
    """Generate .bib file from BIP preambles.

    Args:
        bips_dir (str): Root directory of the bitcoin/bips repo.
        out_path (str): Output .bib file path.

    Raises:
        RuntimeError: If bips_dir does not exist or is not a directory, or if no
            BIP files are found.
    """
    if not os.path.isdir(bips_dir):
        raise RuntimeError(f"{bips_dir!r} does not exist or is not a directory.")
    bip_files = find_bip_files(bips_dir)
    if not bip_files:
        raise RuntimeError(f'No BIP files found in directory "{bips_dir}"')
    bib_entries: list[tuple[int, str]] = []
    for fpath in bip_files:
        lines = extract_preamble(fpath)
        if not lines:
            continue
        fields = parse_preamble(lines)
        result = bib_entry(fields, fpath)
        if result:
            bib_entries.append(result)
    bib_entries.sort(key=lambda x: x[0])
    with open(out_path, "w", encoding="utf-8") as out:
        out.writelines(entry for _, entry in bib_entries)
    print(f"Wrote {len(bib_entries)} entries to {out_path}.")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Parse BIP preambles and generate a .bib file."
    )
    parser.add_argument("bips_dir", help="Root directory of the bitcoin/bips repo")
    default_output = "bips.bib"
    parser.add_argument(
        "-o", "--output", default=default_output, help="Output .bib file"
    )
    args = parser.parse_args()
    generate_bib(args.bips_dir, args.output)
