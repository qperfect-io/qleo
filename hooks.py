# Copyright (c) 2025-2026 QPerfect. All Rights Reserved.
# Proprietary and confidential.

"""Rebrand engine names in the rendered pages.

The API reference is generated from the simulation engine's own docstrings,
which speak of Exaqt. Rewriting them upstream is not ours to do, so the
substitution happens here, on the rendered page HTML — before the search
index is built from it.

Only mixed/lower-case spellings are mapped, so the ``EXAQT_*`` environment
variables the engine actually reads keep their real names.

``_LITERALS`` shields real identifiers that merely happen to contain the
engine's name — a shipped file called ``libexaqt.so`` is not a brand
mention, and rewriting it would send readers looking for a file that does
not exist. They are swapped out for a sentinel before the brand rules run
and swapped back afterwards.

ponytail: post-render string swap, not a docstring fork. If the engine ever
grows brand-neutral docstrings, delete this file and the `hooks:` entry.
"""

_REPLACEMENTS = [
    ("mimiq-exaqt", "qleo"),
    ("exaqt-python", "qleo"),
    ("Exaqt", "Qleo"),
    ("exaqt", "qleo"),
]

# Names that must survive verbatim. Order does not matter; each is parked
# under a sentinel that contains no substring any rule above matches.
_LITERALS = [
    "libexaqt.so",
]


def on_page_content(html, page, config, files):
    for i, literal in enumerate(_LITERALS):
        html = html.replace(literal, f"\x00literal{i}\x00")
    for old, new in _REPLACEMENTS:
        html = html.replace(old, new)
    for i, literal in enumerate(_LITERALS):
        html = html.replace(f"\x00literal{i}\x00", literal)
    return html
