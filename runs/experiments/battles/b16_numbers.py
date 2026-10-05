#!/usr/bin/env python3
"""B16 R1: the mechanical inventory of every number in findings/2026-10-05-battle-peace-offer.md, shared by the audit and by the map generator.

`inventory(text)` returns, per line of the finding, the normalised numeric tokens that the line states (digits, hex, and the number words two..nine), after
removing what is checked another way: (a) code spans that name a file or a cell (extension, `*`, `<`, `=`...): they are checked for existence in the data
(`b16_audit.py` claim `cited_files`), (b) ISO dates, (c) the numbering of a list at the line start, (d) markdown table lines (a table is recomputed cell by cell,
see `tables()`), (e) the heading lines.
`b16_number_map.json` maps each prose line (key: its first 70 characters) to {"claims": [claim ids], "exempt": {token: reason}}; the audit fails when a line with
tokens is not in the map, when a token is neither found among the checked values of the line's claims nor exempt with a reason, or when the map names a claim
that does not exist or does not match. `python3 runs/experiments/battles/b16_numbers.py` prints the skeleton of the map for the current finding."""
import json
import re
import sys
from pathlib import Path

FINDING = Path(__file__).resolve().parents[3] / "findings" / "2026-10-05-battle-peace-offer.md"
NUM = re.compile(r"(?<![\w#.\-/])(?:0x[0-9A-Fa-f]+|-?\d[\d,]*(?:\.\d+)?)(?![\w])")
WORDS = {"two": "2", "three": "3", "four": "4", "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9", "twice": "2"}
WORD = re.compile(r"\b(%s)\b" % "|".join(WORDS), re.I)
CODE = re.compile(r"`[^`]*`")
FILEISH_INNER = re.compile(r"\.(?:png|SAV|sav|csv|json|jsonl|md|py|gz|sha256|txt|log|exe|sh)\b|\*|<|=")


def drop_file_spans(line):
    """Remove the code spans that name a file or a cell (spans are paired left to right, so a closing backtick never opens a span)."""
    return CODE.sub(lambda m: " " if FILEISH_INNER.search(m.group(0)) else m.group(0), line)
DATE = re.compile(r"\d{4}-\d\d-\d\d")


LINT_NUM = re.compile(r"(?<![\w#])(?:0x[0-9A-Fa-f]+|\d[\d,]*(?:\.\d+)?)(?![\w])")
FILE_SPAN = re.compile(r"\.(?:png|SAV|sav|csv|json|jsonl|md|py|gz|sha256|txt|log|exe|sh)\b|\*")
CELL_SPAN = re.compile(r"^`(?:loss|win)\+[^`]*`$|^`(?:loss|win)\+")


def lint_tokens(line):
    """Numeric tokens of one skeleton line for the lint: every digit run or hex number not glued to a letter, underscore or digit (so `turn-4`, `..0x4A0B80`, `> 500` count),
    and the number words two..nine. Only code spans that NAME a file (an extension or a `*`) or a cell (`loss+...`, `win+...`) are set aside, never any other span."""
    s = CODE.sub(lambda m: " " if (FILE_SPAN.search(m.group(0)) or CELL_SPAN.search(m.group(0))) else m.group(0), line)
    s = DATE.sub(" ", s)
    s = re.sub(r"SHA-256|sha256", " ", s)
    s = re.sub(r"^\s*\d+\.\s", " ", s)                      # the numbering of a list
    return [norm(m.group(0)) for m in LINT_NUM.finditer(s)] + [WORDS[m.group(1).lower()] for m in WORD.finditer(s)]


def norm(tok):
    t = tok.replace(",", "").rstrip("%").lower()
    if t.startswith("0x"):
        return "0x" + t[2:].lstrip("0").lower() or "0x0"
    return t


def line_tokens(line, all_lines=False):
    """Normalised numeric tokens of one line. Table rows and headings are skipped unless `all_lines` (the skeleton lint reads them too)."""
    if not all_lines and (line.startswith("|") or line.startswith("#")):
        return []
    s = drop_file_spans(line)
    s = DATE.sub(" ", s)
    s = re.sub(r"^\s*\d+\.\s", " ", s)
    out = [norm(m.group(0)) for m in NUM.finditer(s)]
    out += [WORDS[m.group(1).lower()] for m in WORD.finditer(s)]
    return out


def line_key(line):
    return re.sub(r"\s+", " ", line.strip())[:70]


def inventory(text=None):
    text = text if text is not None else FINDING.read_text()
    inv = []
    for n, line in enumerate(text.split("\n"), 1):
        t = line_tokens(line)
        if t:
            inv.append({"line": n, "key": line_key(line), "tokens": sorted(set(t)), "count": len(t)})
    return inv


def tables(text=None):
    """Markdown tables of the finding as {title: {"header": [...], "rows": [[...], ...]}}, the title being the bold line before the table."""
    text = text if text is not None else FINDING.read_text()
    out, title, cur = {}, None, None
    for line in text.split("\n"):
        if line.startswith("|"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if cur is None:
                cur = {"header": cells, "rows": []}
                out[title] = cur
            elif not set("".join(cells)) <= set("-: "):
                cur["rows"].append(cells)
        else:
            cur = None
            if line.startswith("**") and line.strip():
                title = line.strip().strip("*")
    return out


if __name__ == "__main__":
    inv = inventory()
    print("%d prose lines with numbers, %d token occurrences, %d table lines" % (len(inv), sum(i["count"] for i in inv), sum(len(t["rows"]) for t in tables().values())))
    skel = {i["key"]: {"line": i["line"], "tokens": i["tokens"], "claims": [], "exempt": {}} for i in inv}
    print(json.dumps(skel, indent=1)[:200000])
