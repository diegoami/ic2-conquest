"""Extract the UnitMap form's TImageList bitmaps from the original exe, read-only (ic2-research request for the player, 2026-10-09:
why Numidia's unit icons use grey where its cities use teal). Reuses the TPF0 parser of runs/experiments/feature_inventory/extract_forms.py,
with binary properties kept as bytes. Each TImageList 'Bitmap' blob is written raw (<list>.bin) and its header described.
python3 extract_imagelists.py <exe> <out_dir>"""
import hashlib, json, re, struct, sys
from pathlib import Path
R = Path("/home/diego/projects/ic2-conquest")
sys.path.insert(0, str(R / "runs/experiments/feature_inventory"))
import extract_forms as EF
_orig = EF.value
def value(r):
    if r.d[r.p] == 10:
        r.p += 1
        n = r.i(4, "<I"); v = bytes(r.d[r.p:r.p + n]); r.p += n
        return {"bytes": v}
    return _orig(r)
EF.value = value
exe, out = Path(sys.argv[1]), Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
d = exe.read_bytes()
res = {"exe": exe.name, "exe_sha256": hashlib.sha256(d).hexdigest(), "lists": []}
for m in re.finditer(rb"TPF0", d):
    s = m.start()
    if d[s + 4] == 0 or d[s + 5:s + 6] != b"T":
        continue
    try:
        o = EF.obj(EF.P(d, s + 4))
    except Exception:
        continue
    def walk(n, form):
        if n["class"] == "TImageList" and isinstance(n["props"].get("Bitmap"), dict):
            blob = n["props"]["Bitmap"]["bytes"]
            name = f"{form}_{n['name']}"
            (out / f"{name}.bin").write_bytes(blob)
            res["lists"].append({"form": form, "name": n["name"], "props": {k: v for k, v in n["props"].items() if k != "Bitmap"},
                                 "size": len(blob), "sha256": hashlib.sha256(blob).hexdigest(), "head_hex": blob[:64].hex()})
        for c in n["children"]:
            walk(c, form)
    walk(o, o["class"])
(out / "imagelists.json").write_text(json.dumps(res, indent=1, default=str))
for l in res["lists"]:
    print(l["form"], l["name"], l["size"], l["head_hex"][:96])
