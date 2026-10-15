"""
anonymise.py — remove personal details from messages before we store or share them.

WHAT IT DOES
Reads a CSV of messages, replaces private details in the `text` column
with placeholder tags, and writes a new, cleaned CSV.

    0244123456          ->  <PHONE>
    +233 24 412 3456    ->  <PHONE>
    7123456789012       ->  <LONG_NUMBER>   (transaction IDs, account numbers)
    someone@gmail.com   ->  <EMAIL>
    https://bit.ly/xyz  ->  <URL>
    from KWAME ASANTE   ->  from <NAME>

WHY PLACEHOLDERS INSTEAD OF DELETING?
Because "this message contains a phone number" is itself useful to the
model. Scams very often say "send to 0XX...". We keep the fact that a
number was there, but throw away the actual number.

LIMITATION (be honest about this in the report)
Names are only caught in the common MoMo alert pattern ("from NAME IN CAPS").
A name in the middle of a casual message will slip through, so always
skim the cleaned file before sharing it.

Run:  python src/anonymise.py <input.csv> <output.csv>
"""

import re
import sys

import pandas as pd

# Each rule is (pattern, replacement). Order matters: emails and URLs
# contain digits, so we replace them before we look for numbers.
RULES = [
    # Email addresses
    (re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.]+\b"), "<EMAIL>"),
    # Web links (with or without http)
    (re.compile(r"\b(?:https?://|www\.)\S+|\b[\w-]+\.(?:com|ly|gh|net|org|io|me)/\S*", re.IGNORECASE), "<URL>"),
    # Ghana phone numbers: 0XX XXX XXXX or +233 XX XXX XXXX, with optional spaces or dashes
    (re.compile(r"(?:\+?233|\b0)[\s-]?\d{2}[\s-]?\d{3}[\s-]?\d{4}\b"), "<PHONE>"),
    # Any other run of 8 or more digits (transaction IDs, account numbers)
    (re.compile(r"\b\d{8,}\b"), "<LONG_NUMBER>"),
    # Full names (2 to 4 words) in CAPITALS after from/to/name, as in real MoMo alerts.
    # Requiring at least two words stops it from hiding company names like "to ECG".
    (re.compile(r"\b(from|to|name:?)\s+([A-Z][A-Z'-]+(?:\s+[A-Z][A-Z'-]+){1,3})\b"), r"\1 <NAME>"),
]


def anonymise_text(text: str) -> str:
    """Apply every rule, in order, to one message."""
    if not isinstance(text, str):
        return text
    for pattern, replacement in RULES:
        text = pattern.sub(replacement, text)
    return text


def main(in_path: str, out_path: str) -> None:
    df = pd.read_csv(in_path, dtype=str, keep_default_na=False)
    if "text" not in df.columns:
        sys.exit("The input CSV needs a 'text' column. See docs/LABELLING_GUIDE.md.")

    before = df["text"].copy()
    df["text"] = df["text"].map(anonymise_text)
    changed = (before != df["text"]).sum()

    df.to_csv(out_path, index=False)
    print(f"Cleaned {len(df)} messages ({changed} had personal details removed) -> {out_path}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("Usage: python src/anonymise.py <input.csv> <output.csv>")
    main(sys.argv[1], sys.argv[2])
