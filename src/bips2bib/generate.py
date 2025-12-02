#!/usr/bin/env python3
import re
from pathlib import Path
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


def find_bip_files(bips_dir: Path) -> list[Path]:
    """Find BIP files in bips_dir.

    Args:
        bips_dir (Path): Directory to search.

    Returns:
        list[Path]: List of file paths.
    """
    bip_files: list[Path] = []
    for path in bips_dir.iterdir():
        if path.is_file() and re.match(r"^bip-\d+\.(mediawiki|md)$", path.name):
            bip_files.append(path)
    return bip_files


def extract_preamble(path: Path) -> Optional[list[str]]:
    """Extract the preamble lines from a BIP file.

    Args:
        path (Path): Path to the BIP file.

    Returns:
        Optional[list[str]]: List of preamble lines if found, else None.

    Raises:
        ValueError: If the file has an unsupported suffix.
    """
    with path.open() as f:
        content = f.read()
    if path.suffix == ".mediawiki":
        m = re.search(r"<pre>\s*(.*?)\s*</pre>", content, re.DOTALL)
    elif path.suffix == ".md":
        m = re.search(r"```(.*?)```", content, re.DOTALL)
    else:
        raise ValueError(f"File {path} has unsupported suffix")
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


def bib_entry(fields: dict[str, list[str]], fname: Path) -> Optional[tuple[int, str]]:
    """Create a BibTeX entry for the BIP.

    Args:
        fields (dict[str, list[str]]): Parsed preamble fields.
        fname (Path): Filename of the BIP.

    Returns:
        Optional[tuple[int, str]]: Tuple of bip_num and BibTeX entry string if data is sufficient, else None.
    """
    bip_num_str: str = fields.get("BIP", [""])[0]
    title: str = fields.get("Title", [""])[0]
    authors: str = fields.get("Author", [""])[0]
    year: str = fields.get("Created", [""])[0][:4]
    url: str = f"https://github.com/bitcoin/bips/blob/master/{fname.name}"

    if (
        not bip_num_str
        or not bip_num_str.isdigit()
        or not title
        or not authors
        or not year
    ):
        print(
            f"WARNING: Skipping {fname} due to insufficient data: "
            f"BIP={bip_num_str!r} Title={title!r} Author={authors!r} Year={year!r}"
        )
        return None

    bip_num: int = int(bip_num_str)
    lines: list[str] = [f"@techreport{{bip:{bip_num:04},"]
    if bip_num in BIP_ALIASES:
        lines.append(f"  ids          = {{bip:{escape_tex(BIP_ALIASES[bip_num])}}},")
    lines.append(f"  shorthand    = {{BIP{bip_num}}},")
    lines.append(f"  author       = {{{escape_tex(authors)}}},")
    lines.append(f"  title        = {{{escape_tex(title)}}},")
    lines.append(f"  year         = {{{escape_tex(year)}}},")
    lines.append(f"  url          = {{{escape_tex(url)}}},")
    lines.append(
        f"  type         = {{{escape_tex('Bitcoin Improvement Proposal (BIP)')}}},"
    )
    lines.append(f"  number       = {{{bip_num}}},")
    lines.append("}\n")
    entry: str = "\n".join(lines)
    return bip_num, entry


def generate_bib(bips_dir: Path, out_path: Path) -> None:
    """Generate .bib file from BIP preambles.

    Args:
        bips_dir (Path): Root directory of the bitcoin/bips repo.
        out_path (Path): Output .bib file path.

    Raises:
        RuntimeError: If there are no BIP files.
    """
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
    with out_path.open("w") as out:
        out.writelines(entry for _, entry in bib_entries)
    print(f"Wrote {len(bib_entries)} entries to {out_path}.")

