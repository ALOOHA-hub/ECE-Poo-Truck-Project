import unicodedata


def slugify(text: str) -> str:
    """Normalize unicode, strip accents, and convert non-alphanumeric chars to hyphens."""
    decomposed = unicodedata.normalize("NFKD", text)
    plain = decomposed.encode("ascii", "ignore").decode("ascii")
    result = ""
    for char in plain.lower():
        if char.isalnum():
            result += char
        elif not result.endswith("-"):
            result += "-"
    return result.strip("-")