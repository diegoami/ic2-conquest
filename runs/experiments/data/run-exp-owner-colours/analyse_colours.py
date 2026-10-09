"""Offline analysis of colours_screen.png (probe_colours.py): 8-bit RGB hashes of each 32x32 tile, whole and inset by 2 px
(the dotted tile edges depend on the neighbours), the background colour (pixel (3,3)), and the earlier Rome tiles of
run-exp-army-marker-icon for comparison. python3 analyse_colours.py <out_dir>"""
import collections, hashlib, json, subprocess, sys
from pathlib import Path
out = Path(sys.argv[1]); R = Path("/home/diego/projects/ic2-conquest")
def rgb(png, inset=0):
    a = ["convert", str(png)] + (["-crop", f"{32 - 2 * inset}x{32 - 2 * inset}+{inset}+{inset}", "+repage"] if inset else []) + ["-depth", "8", "rgb:-"]
    return subprocess.run(a, capture_output=True, check=True).stdout
def info(png):
    b = rgb(png); i = 3 * (3 * 32 + 3)
    return {"sha": hashlib.sha256(b).hexdigest()[:16], "sha_inset2": hashlib.sha256(rgb(png, 2)).hexdigest()[:16], "bg": b[i:i + 3].hex()}
res = json.loads((out / "probe_colours.json").read_text())
res["control"].update(info(out / "tiles/control_rome_army_200.png"))
for t in res["tiles"]:
    t.update(info(out / "tiles" / t["png"]))
earlier = {n: info(R / f"artifacts/run-exp-army-marker-icon/{n}_tile.png") for n in ("w200_t24999", "w216_t25000", "w232_t50000")}
res["earlier_rome"] = earlier
first = {t["word"]: t for t in res["tiles"] if t["repeat"] == 0}
res["repeats"] = [{"word": t["word"], "terrain_under": [first[t["word"]]["terrain_under"], t["terrain_under"]],
                   "same_inset": t["sha_inset2"] == first[t["word"]]["sha_inset2"], "same_full": t["sha"] == first[t["word"]]["sha"]}
                  for t in res["tiles"] if t["repeat"]]
by_owner = collections.defaultdict(set); by_shape = collections.defaultdict(set)
for t in res["tiles"]:
    if t["repeat"] == 0:
        by_owner[t["owner"]].add(t["bg"])
        by_shape[(t["kind"], t["band"])].add(t["sha_inset2"])
res["bg_per_owner"] = {o: sorted(v) for o, v in sorted(by_owner.items())}
res["distinct_bg"] = len({next(iter(v)) for v in by_owner.values() if len(v) == 1})
res["distinct_sha_per_kind_band"] = {f"{k}_{b}": len(v) for (k, b), v in sorted(by_shape.items())}
res["distinct_sha_all"] = len({t["sha_inset2"] for t in res["tiles"] if t["repeat"] == 0})
(out / "analyse_colours.json").write_text(json.dumps(res, indent=1, default=str))
print("control", res["control"]["sha_inset2"], "earlier", {k: v["sha_inset2"] for k, v in earlier.items()})
print("repeats", res["repeats"]); print("bg", res["bg_per_owner"]); print("distinct bg", res["distinct_bg"])
print("per kind/band", res["distinct_sha_per_kind_band"], "all", res["distinct_sha_all"])
# owner colours: the two most frequent colours of each tile's inset (background, then the figure's main colour)
def top_colours(png):
    b = rgb(png, 2); c = collections.Counter(b[i:i + 3].hex() for i in range(0, len(b), 3))
    return [k for k, _ in c.most_common(3)]
per_owner = collections.defaultdict(list)
for t in res["tiles"]:
    if t["repeat"] == 0:
        t["top_colours"] = top_colours(out / "tiles" / t["png"])
        per_owner[t["owner"]].append((t["kind"], t["band"], t["top_colours"]))
res["owner_colours"] = {}
for o, v in sorted(per_owner.items()):
    bgs = {c[0] for _, _, c in v}
    res["owner_colours"][o] = {"background": sorted(bgs), "tiles": v}
(out / "analyse_colours.json").write_text(json.dumps(res, indent=1, default=str))
for o, d in res["owner_colours"].items():
    print(o, "bg", d["background"], "| second colours", sorted({c[1] for _, _, c in d["tiles"]}))
print("distinct backgrounds", len({tuple(d["background"]) for d in res["owner_colours"].values()}))
