"""Assemble the four row tables (rows_g1.md, rows_g2.md, rows_g3.md, rows_ai.md) into one table with a Group column, and count rows by
class and severity. Writes combined_table.md and combined_counts.json (versioned). python3 assemble.py"""
import json, re
from collections import Counter
from pathlib import Path
D = Path(__file__).resolve().parent
GROUPS = [("g1", "Menus, windows, File/Game/Strategy/Nations/Help/keys"), ("g2", "Area map, unit map orders and dialogs"),
          ("g3", "Turn and quarter cycle, news, victory, defeat, end of game"), ("ai", "The AI over many turns")]
rows, counts = [], {}
for g, title in GROUPS:
    lines = (D / f"rows_{g}.md").read_text().splitlines()
    tab = [l for l in lines if l.startswith("| ") and not l.startswith("| Id") and not re.match(r"\|\s*-", l)]
    tab = tab[:next((i for i, l in enumerate(tab) if l.count("|") < 9), len(tab))]
    for l in tab:
        cells = [c.strip() for c in l.strip().strip("|").split("|")]
        if len(cells) < 8: continue
        cells = cells[:7] + [" | ".join(cells[7:])]
        rows.append((g, cells))
def norm_sev(s):
    s = s.lower()
    for k in ("breaks play", "blocks a normal game", "fidelity only", "cosmetic", "excluded"):
        if k in s: return k
    return "-" if s.strip() in ("-", "–", "") else s[:30]
def norm_cls(c):
    c = c.lower()
    for k in ("missing", "differs", "matches"):
        if k in c: return k
    return c[:20]
for g, _ in GROUPS:
    R = [c for gg, c in rows if gg == g]
    counts[g] = {"rows": len(R), "class": dict(Counter(norm_cls(c[4]) for c in R)), "severity": dict(Counter(norm_sev(c[5]) for c in R))}
counts["total"] = {"rows": len(rows), "class": dict(Counter(norm_cls(c[4]) for _, c in rows)), "severity": dict(Counter(norm_sev(c[5]) for _, c in rows))}
out = ["| Group | Id | Area | Original (evidence) | Remake v0.5.0 (evidence) | Class | Severity | Known | Notes |", "|---|---|---|---|---|---|---|---|---|"]
out += ["| " + g + " | " + " | ".join(c) + " |" for g, c in rows]
def new(name):
    p = D / name; k = 1
    while p.exists(): k += 1; p = D / (Path(name).stem + f".v{k}" + Path(name).suffix)
    return p
p1 = new("combined_table.md"); p1.write_text("\n".join(out) + "\n")
p2 = new("combined_counts.json"); p2.write_text(json.dumps(counts, indent=1))
print(p1.name, p2.name); print(json.dumps(counts, indent=1))
hi = [(g, c[0], c[1], c[5]) for g, c in rows if norm_sev(c[5]) in ("breaks play", "blocks a normal game")]
print("HIGH:", *hi, sep="\n  ")
odd = [(g, c[0], c[4], c[5]) for g, c in rows if norm_cls(c[4]) not in ("missing", "differs", "matches") or norm_sev(c[5]) not in ("breaks play", "blocks a normal game", "fidelity only", "cosmetic", "excluded", "-")]
print("UNUSUAL:", *odd, sep="\n  ")
