import re


def contains_digit(word: str) -> bool:
    """Check if word contains any digit."""
    return any(char.isdigit() for char in word)


def is_acronym(word: str) -> bool:
    """Check if word is fully capitalized (length >= 2)."""
    return len(word) >= 2 and word.isupper()


def is_mixed_case(word: str) -> bool:
    """Check if word has mixed case (e.g., "SegWit").

    Returns True if word contains both uppercase and lowercase letters
    and is not just a normal capitalized word (first letter capital, rest lowercase).
    """
    if len(word) <= 1:
        return False

    # Normal capitalization: first char upper, rest lower (like "Scheme")
    if word[0].isupper() and word[1:].islower():
        return False

    # All lowercase or all uppercase
    if word.islower() or word.isupper():
        return False

    # If we get here, it's truly mixed case (like "SegWit")
    has_upper = any(char.isupper() for char in word)
    has_lower = any(char.islower() for char in word)
    return has_upper and has_lower


def contains_empty_parens(word: str) -> bool:
    """Check if word contains empty parentheses () like a function call."""
    return "()" in word


def is_proper_name(word: str) -> bool:
    """Check if word is a proper name (case-insensitive)."""
    PROPER_NAMES_LOWER = {
        "Bitcoin",
        "CoinJoin",
    }
    return word.lower() in PROPER_NAMES_LOWER


def is_small_word(word: str) -> bool:
    """Check if word is an article, conjunction, or preposition."""
    # fmt: off
    LOWERCASE_WORDS = {
        # Articles
        "a", "an", "the",
        
        # Coordinating conjunctions
        "and", "but", "for", "nor", "or", "so", "yet",
        
        # Prepositions (CMOS lowercases these regardless of length)
        "as", "at", "by", "for", "in", "of", "off", "on", "per", "to", "up", "via",
        
        # Additional common prepositions
        "about", "above", "across", "after", "against", "along", "among",
        "around", "before", "behind", "below", "beneath", "beside", "between",
        "beyond", "down", "during", "except", "from", "inside", "into", "like",
        "near", "onto", "out", "outside", "over", "past", "since", "through",
        "throughout", "till", "toward", "under", "underneath", "until", "upon",
        "vs", "with", "within", "without"
    }
    # fmt: on
    return word.lower() in LOWERCASE_WORDS


def apply_special_cases(text: str) -> str:
    """Apply special case transformations."""
    text = text.replace("([soft/hard]forks)", "([Soft/Hard]forks)")  # BIP 99
    text = text.replace('"Version" Message', '"version" Message')  # BIP 60
    text = text.replace("bitcoin: Uri", "bitcoin: uri")  # BIP 72

    return text


def titlecase(text: str, wrap: bool = True) -> str:
    """Convert text to title case, loosely based on Chicago Manual of Style

    Rules (here, a "part" is a part of a hyphenated/slashed word):
    - Preserve: First part of first word (lowercase is likely for a reason)
    - Always capitalize: last word, major words
    - Always lowercase: articles, coordinating conjunctions, prepositions
    - Preserve: Parts containing digits (like "v1+")
    - Preserve: Fully capitalized parts of length >= 2 (acronyms like "BIP")
    - Preserve: Mixed-case parts (like "SegWit", "Bech32m")
    - Preserve: Parts containing () (like "tr()", "musig()")
    - Hyphenated/slashed words: Capitalize first part, apply above rules to other parts

    Preserved parts are wrapped in {} for BibTeX, and are some proper names such
    as "Bitcoin" and "CoinJoin".

    Some special cases are applied after title casing.

    Args:
        text: Input string to convert.
        wrap: Whether to wrap preserved parts in {}.  Default is True.

    Returns:
        Title-cased string.
    """
    # Punctuation characters to strip when checking words
    punctuation = ".,!?    ;:\"'()[]{}"

    words = text.split()
    result = []

    for i, word in enumerate(words):
        # Split by hyphen or slash, capturing the separators
        # re.split with capturing group returns: [part, sep, part, sep, part]
        tokens = re.split(r"([-/])", word)

        # Separate parts and separators
        parts = tokens[::2]  # Every other element starting at 0
        separators = tokens[1::2]  # Every other element starting at 1

        is_multi_part = len(parts) > 1
        processed_parts = []

        for j, part in enumerate(parts):
            has_upper = any(char.isupper() for char in part)
            wrapped_part = f"{{{part}}}" if wrap and has_upper else part

            # Check for acronym in part
            if is_acronym(part):
                processed_parts.append(wrapped_part)
                continue

            # Check for empty parentheses in part
            if contains_empty_parens(part):
                processed_parts.append(wrapped_part)
                continue

            # Check for mixed case in part
            if is_mixed_case(part):
                processed_parts.append(wrapped_part)
                continue

            # Check for digits in part
            if contains_digit(part):
                processed_parts.append(wrapped_part)
                continue

            # Never modify the first part of the first word (but don't wrap)
            if i == 0 and j == 0:
                processed_parts.append(part)
                continue

            # Extract prefix/suffix punctuation to preserve it in output
            # Example: "hello," -> prefix='', clean_part='hello', suffix=','
            # Example: '"world"' -> prefix='"', clean_part='world', suffix='"'
            clean_part = part.strip(punctuation)
            prefix = part[: len(part) - len(part.lstrip(punctuation))]
            suffix = part[len(clean_part) + len(prefix) :]

            # Check for proper names (case-insensitive)
            part_is_proper_name = is_proper_name(clean_part)

            # Determine if this part should be capitalized
            is_last_word = i == len(words) - 1 and j == len(parts) - 1
            is_first_part_of_multi = is_multi_part and j == 0
            part_is_small_word = is_small_word(clean_part)

            if is_last_word or is_first_part_of_multi or not part_is_small_word:
                title_cased = prefix + clean_part.capitalize() + suffix
            else:
                title_cased = prefix + clean_part.lower() + suffix

            # Wrap if it's a proper name
            if part_is_proper_name:
                wrapped_title_cased = f"{{{title_cased}}}" if wrap else title_cased
                processed_parts.append(wrapped_title_cased)
            else:
                processed_parts.append(title_cased)

        # Reconstruct word by interleaving parts and separators
        reconstructed = []
        for idx, part in enumerate(processed_parts):
            reconstructed.append(part)
            if idx < len(separators):
                reconstructed.append(separators[idx])

        result.append("".join(reconstructed))

    result_text = " ".join(result)

    # Apply special cases
    result_text = apply_special_cases(result_text)

    return result_text


# Examples
if __name__ == "__main__":
    examples = [
        "a guide to python programming",
        "the quick brown fox jumps over the lazy dog",
        "gone with the wind",
        "to be or not to be",
        "to-be or not to-be",
        "learning python: from beginner to expert",
        "state-of-the-art technology",
        "they're writing a guide for developers",
        "introduction to REST API development",
        "using NASA data for ML applications",
        "understanding p2sh transactions in bitcoin",
        "sha256 and other hashing algorithms",
        "base64 encoding for beginners",
        "FORTRAN programming in the 1970s",
        "IPv4 vs IPv6 addressing",
        '"hello," she said',
        "developing apps for iPhone and android",
        "using PyTorch for machine learning",
        "P2WPKH-nested-in-P2SH addresses",
        "end-to-end encryption",
        "calling the print() function",
        "use getData() to fetch results",
        "parameters are (optional) here",
        "understanding ([soft/hard]forks) mechanisms",
        '"Version" Message handling in bitcoin',
        "bitcoin: uri scheme explained",
        "client/server architecture",
        "read/write operations",
        "input/output for the system",
        "address scheme for bitcoin",
        "Bitcoin and CoinJoin explained",
        "bitcoin versus BITCOIN discussion",
        "coinjoin privacy for bitcoin users",
    ]

    for example in examples:
        print(f"{example}")
        print(f"  → {titlecase(example)}")
        print()
