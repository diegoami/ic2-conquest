"""Offline analysis of probe_cities.py's screenshots. Per word: inset-2 hash, colour count, colour classes. Per variant: is it a
fixed template (the pixels of each colour class are the same set for all 16 owners)? Roles are the classes of the template, named
by pixel count; per owner the colour on each role. Controls: real cities (screens 1 and 2) against the patched word's inset hash.
The 16 nation buttons of the main toolbar are also cropped (temples on coloured squares). python3 analyse_cities.py <out_dir>"""
import collections, hashlib, json, subprocess, sys
from pathlib import Path
out = Path(sys.argv[1])
NAMES = ['Rome', 'Carthage', 'Seleucid', 'Ptolemaic', 'Macedonia', 'Numidia', 'Gaul', 'Greece', 'Celtiberia', 'Illyria', 'Dacia',
         'Bithynia', 'Galatia', 'Armenia', 'Media', 'Thracia']
def px(png, inset=2):
    w = 32 - 2 * inset
    b = subprocess.run(["convert", str(png), "-crop", f"{w}x{w}+{inset}+{inset}", "+repage", "-depth", "8", "rgb:-"], capture_output=True, check=True).stdout
    return [b[i:i + 3].hex() for i in range(0, len(b), 3)]
res = json.loads((out / "probe_cities.json").read_text())
first = {}
for t in res["tiles"]:
    p = px(out / "tiles" / t["png"]); t["n_colours"] = len(set(p)); t["counts"] = collections.Counter(p).most_common()
    if t["repeat"] == 0:
        first[t["word"]] = (t, p)
res["repeats"] = [{"word": t["word"], "terrain": t["terrain_under"], "same_inset": t["sha_inset2"] == first[t["word"]][0]["sha_inset2"]}
                  for t in res["tiles"] if t["repeat"]]
summary = {}
for v in range(5):
    parts = {}
    for o in range(16):
        t, p = first[20 + o + 16 * v]
        cls = collections.defaultdict(list)
        for i, c in enumerate(p):
            cls[c].append(i)
        parts[o] = {c: frozenset(ix) for c, ix in cls.items()}
    ref = sorted(parts[0].values(), key=len, reverse=True)
    template = all(sorted(parts[o].values(), key=len, reverse=True) == ref for o in range(16))
    roles = {}
    for o in range(16):
        roles[NAMES[o]] = {f"role{k}_{len(s)}px": next(c for c, ix in parts[o].items() if ix == s) if template else None for k, s in enumerate(ref)}
    summary[f"v{v}"] = {"template": template, "role_sizes": [len(s) for s in ref], "n_colours": sorted({first[20 + o + 16 * v][0]["n_colours"] for o in range(16)}),
                        "distinct_hashes": len({first[20 + o + 16 * v][0]["sha_inset2"] for o in range(16)}), "roles": roles}
res["variants"] = summary
# controls: real cities against the patched copy of the same word
res["control_check"] = [{"tile": c["tile"], "word": c["word"], "same_as_patched": c["sha_inset2"] == first[c["word"]][0]["sha_inset2"]}
                        for c in res["controls"] if c["word"] in first]
res["control_check"] += [{"city": c["name"], "word": c["word"], "same_as_patched": c["sha_inset2"] == first[c["word"]][0]["sha_inset2"]}
                         for c in res["screen2"]["cities"] if c["word"] in first]
# the toolbar's 16 nation buttons (screen 1): find them as the 16 temple squares right of the "%" etc. buttons
tb = []
full = out / "cities_screen1.png"
for o in range(16):
    x0 = 229 + 24 * o
    p = out / "tiles" / f"toolbar_o{o:02d}.png"
    subprocess.run(["convert", str(full), "-crop", f"22x22+{x0}+{48}", "+repage", str(p)], check=True)
    c = collections.Counter(px(p, 0) if False else subprocess.run(["convert", str(p), "-depth", "8", "rgb:-"], capture_output=True, check=True).stdout[i:i + 3].hex()
                            for i in range(0, 22 * 22 * 3, 3))
    tb.append({"owner": o, "nation": NAMES[o], "top_colours": c.most_common(5)})
res["toolbar"] = tb
(out / "analyse_cities.json").write_text(json.dumps(res, indent=1, default=str))
for v, s in summary.items():
    print(v, "template", s["template"], "sizes", s["role_sizes"], "colours", s["n_colours"], "distinct", s["distinct_hashes"])
print("repeats all same:", all(r["same_inset"] for r in res["repeats"]), len(res["repeats"]))
print("controls:", res["control_check"])
for n in NAMES[:16]:
    print(n, {v: list(summary[v]["roles"][n].values()) for v in summary})
# compare: city roles (variant 0 order: background, outline role, fill role; v3 holds the same colours on reordered sizes) with the
# unit icons' A/B (research report 2026-10-09-owner-colours-by-band.md, ba103a0) and 2026-09-29's (outline, foreground)
import re
REP = Path("/home/diego/projects/imperial-conquest-2-research/docs/reports")
HEX = {"white": "ffffff", "black": "000000", "blue": "0000ff", "grey": "808080", "teal": "008080", "cyan": "00ffff", "olive": "808000",
       "purple": "800080", "maroon": "800000", "magenta": "ff00ff", "red": "ff0000", "yellow": "ffff00", "silver": "c0c0c0", "lime": "00ff00",
       "green": "008000", "navy": "000080"}
unit = {}
for line in (REP / "2026-10-09-owner-colours-by-band.md").read_text().splitlines():
    m = re.match(r"\| (\d+) \| (\w+) \| `#(\w+)`[^|]*\| `#(\w+)`[^|]*\| `#(\w+)`[^|]*\| ([\w ]+), ([\w ]+) \|", line)
    if m:
        unit[int(m.group(1))] = {"bg": m.group(3), "A": m.group(4), "B": m.group(5), "old_outline": HEX[m.group(6).strip()], "old_fg": HEX[m.group(7).strip()]}
cmp = []
for o in range(16):
    v0 = list(summary["v0"]["roles"][NAMES[o]].values())
    bg, outline, fill = v0
    same_all = all(set(summary[v]["roles"][NAMES[o]].values()) == set(v0) for v in summary)
    u = unit.get(o, {})
    cmp.append({"owner": o, "nation": NAMES[o], "city_bg": bg, "city_outline": outline, "city_fill": fill, "same_colours_all_variants": same_all,
                "unit_A": u.get("A"), "unit_B": u.get("B"), "old_outline": u.get("old_outline"), "old_fg": u.get("old_fg"),
                "eq_unit": (outline, fill) == (u.get("A"), u.get("B")), "eq_old": (outline, fill) == (u.get("old_outline"), u.get("old_fg"))})
res["comparison"] = cmp
(out / "analyse_cities.json").write_text(json.dumps(res, indent=1, default=str))
print("parsed unit rows", len(unit))
for c in cmp:
    print(c["nation"], c["city_bg"], c["city_outline"], c["city_fill"], "| unit", c["unit_A"], c["unit_B"], "| old", c["old_outline"], c["old_fg"],
          "| =unit", c["eq_unit"], "=old", c["eq_old"], "allvar", c["same_colours_all_variants"])
