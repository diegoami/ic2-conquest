"""Reads the g3_checks-*.jsonl logs of this folder and writes the tables the finding cites to analysis_g3.txt (next free version; never overwrites).
Every number in the finding comes from a log line named in the table; the news lines are recomputed from the logged buffers (the first Q1 logs'
`news_new` used an index comparison that fails once the 40-line buffer scrolls; `news_all` and `round_open.news` are complete)."""
import difflib, collections, glob, json, math, re, sys
from pathlib import Path
D = Path(__file__).resolve().parent
ROOT = D.parents[3]; sys.path.insert(0, str(ROOT))
from state import sav
sys.path.insert(0, str(D)); from versioned import write_new
OUT = []
def P(*a): OUT.append(" ".join(str(x) for x in a))
def logs(case): return sorted(D.glob(f"g3_checks-{case}-*.jsonl"))
def rows(f): return [json.loads(l) for l in open(f)]
def new_lines(before, after):
    b = [t for t in before if t != ""]; a = [t for t in after if t != ""]
    for s_ in range(len(b) + 1):
        k = len(b) - s_
        if b[s_:] == a[:k]: return a[k:]
    return a
def ch(c): return f"{c['name']} owner {c['before']['owner']}->{c['after']['owner']} alleg {c['before']['allegiance']} loyalty {c['before']['loyalty']}->{c['after']['loyalty']} fort {c['before']['fort']}->{c['after']['fort']} pop {c['before']['pop']}->{c['after']['pop']} maxpop {c['before']['max_pop']}->{c['after']['max_pop']} tribute {c['before']['tribute']}->{c['after']['tribute']}"
NAT = ["Rome","Carthage","Seleucid","Ptolemaic","Macedonia","Numidia","Gaul","Greece","Celtiberia","Illyria","Dacia","Bithynia","Galatia","Armenia","Media","Thracia"]

AN = {}
for _f in sorted(D.glob("autosave_news-*.jsonl")):
    for _l in open(_f):
        _o = json.loads(_l); AN[_o["kept"]] = _o["news"]
def after_news(r): return r.get("autosave_news") or AN.get(r.get("kept")) or r["news_all"]

def rounds(case):
    for f in logs(case):
        R = rows(f); prev_news = None
        for r in R:
            if r["step"] == "round_open": prev_news = r.get("saved_news") or sav.parse(Path(ROOT / "saves/run0-start-AUTO0720-seed12345.SAV").read_bytes())["news"]   # staged saves from the start save: its news list (the memory buffer read right after File>Open can still hold the previous game's lines)
            if r["step"] == "round_done":
                r["_news"] = new_lines(prev_news, after_news(r)) if prev_news else r.get("news_new"); prev_news = after_news(r)
                r["_file"] = f.name; yield r

def section_ab():
    P("== Q1 (a)(b): quarterly rebellion, staged week 11 ==")
    for r in rounds("Q1ab"):
        moved = [c for c in r["diff"]["cities"] if c["before"]["owner"] != c["after"]["owner"]]
        P(f"[{r['_file']}] {r['tag']} -> {r['cal']} kept={r['kept']}")
        for c in moved: P("   city:", ch(c))
        P("   news:", r["_news"])
        for n in r["diff"]["nations"]:
            if n["id"] == 0 or n["cities_gained"] or n["cities_lost"]:
                if True: P("   nation", n["name"], {k: v for k, v in n["changed"].items() if k in ("unity","treasury","wealth","tax_base","cities_count")}, "gained", n["cities_gained"], "lost", n["cities_lost"])
        if not moved: P("   (no city changed owner)")
    for f in logs("Q1ab"):
        for r in rows(f):
            if r["step"] == "prediction": P(f"[{f.name}] prediction {r['tag']}: city {r['city']} {r['name']} predicted {r['predicted']} observed owner {r['observed_owner']} loyalty {r['observed_loyalty']}")

def section_c():
    P("== Q1 (c): rebirth, Greece unity 0 (Q1c: Greece keeps its 21 cities; Q1c_dead: Greece eliminated, its cities given to Macedonia) ==")
    for r in [x for case in ("Q1c", "Q1c_dead") for x in rounds(case)]:
        P(f"[{r['_file']}] {r['tag']} -> {r['cal']} kept={r['kept']}")
        moved = [c for c in r["diff"]["cities"] if c["before"]["owner"] != c["after"]["owner"]]
        P("   cities moved:", len(moved)); [P("     ", ch(c)) for c in moved]
        P("   news (new):", r["_news"])
        for n in r["diff"]["nations"]:
            if n["name"] in ("Greece", "Rome") or n["cities_gained"] or n["cities_lost"]:
                P("   nation", n["name"], n["changed"], "rel changes", n["relations"], "gained", n["cities_gained"], "lost", n["cities_lost"])
        other = [c for c in r["diff"]["cities"] if c["before"]["owner"] == c["after"]["owner"] and c["before"]["loyalty"] != c["after"]["loyalty"] and abs(c["before"]["loyalty"] - c["after"]["loyalty"]) > 8]
        P("   cities not moved with loyalty change > 8:", [ch(c) for c in other])

def section_d():
    P("== Q1 (d): mercenary desertion, staged week 11 ==")
    for r in rounds("Q1d"):
        P(f"[{r['_file']}] {r['tag']} -> {r['cal']} kept={r['kept']}")
        for a in r["diff"]["armies"]:
            if a["id"] == 0:
                b, af = a["before"], a["after"]
                P("   army 0 before: moves", b[3], "supplies", b[4], "purse", b[5], "morale", b[6], "units", [(u[0], u[1], u[2], u[3], u[4]) for u in b[7]])
                P("   army 0 after : moves", af[3], "supplies", af[4], "purse", af[5], "morale", af[6], "units", [(u[0], u[1], u[2], u[3], u[4]) for u in af[7]])
        P("   news (new):", r["_news"])

def section_e():
    P("== Q1 (e): winter famine loyalty (Random(3)==0 -> loyalty -1 when stock is 0 after the round, season 3) ==")
    for f in logs("Q1e"):
        R = rows(f); tot = collections.Counter(); 
        for r in R:
            if r["step"] == "groups": P("groups:", {k: v for k, v in r.items() if k in ("n_test", "n_control")}, "test ids", r["test_stock0"], "control ids", r["control_full"])
            if r["step"] != "famine_round": continue
            for grp in ("test", "ctl", "other"):
                rs = [x for x in r["rows"] if x["group"] == grp]
                z = [x for x in rs if x["stock_after"] == 0 and x["owner_before"] >= 0]
                clean = [x for x in z if x["loy_after"] - x["loy_before"] in (0, -1)]
                dec = [x for x in clean if x["loy_after"] - x["loy_before"] == -1]
                nz = [x for x in rs if x["stock_after"] > 0]
                nzc = [x for x in nz if x["loy_after"] != x["loy_before"] and abs(x["loy_after"] - x["loy_before"]) <= 3]; nzbig = [(x['id'], x['loy_before'], x['loy_after']) for x in nz if abs(x["loy_after"] - x["loy_before"]) > 3]
                P(f"   round {r['round']} {grp}: cities {len(rs)}, stock 0 after {len(z)} (loyalty delta 0 or -1: {len(clean)}, of which -1: {len(dec)}); stock>0 {len(nz)} with a loyalty change of 1..3: {len(nzc)}, with a change > 3 (a capture or a defection, not famine): {nzbig}; other deltas among stock-0 cities: {[x['loy_after']-x['loy_before'] for x in z if x not in clean]}")
                tot[grp, "n"] += len(clean); tot[grp, "dec"] += len(dec); tot[grp, "nz"] += len(nz); tot[grp, "nzc"] += len(nzc)
        for grp in ("test", "ctl", "other"):
            n, d = tot[grp, "n"], tot[grp, "dec"]
            P(f"   TOTAL {grp}: stock-0 city-rounds (delta 0/-1) {n}, loyalty -1: {d} = {d / n:.3f}" if n else f"   TOTAL {grp}: no stock-0 city-rounds", f"; stock>0 city-rounds {tot[grp,'nz']}, with loyalty change {tot[grp,'nzc']}")

def section_f():
    P("== Q1 (f): AI nations at treasury -50,000, week 11 quarter round, same staged save opened again in one process ==")
    for f in logs("Q1f"):
        R = [r for r in rows(f)]
        stag = [r for r in R if r["step"] == "staged"]
        P(f"[{f.name}] staged: {stag[0]['dst'] if stag else None} ops {stag[0]['ops'] if stag else None}")
        trials = collections.Counter(); dep = collections.Counter(); per_round = []
        ud = []; un = []; tre_d = []; solv = collections.defaultdict(list)
        for r in R:
            if r["step"] != "round_done": continue
            deposed = [t.split(" depose")[0] for t in r["news_all"] if " depose their leader " in t]
            deposed = [x for x in set(deposed)]
            # news_all holds the whole buffer; restrict to lines new this round
        # recompute with the open snapshot
        prev = None
        for r in R:
            if r["step"] == "round_open": prev = r.get("saved_news") or sav.parse((ROOT / "saves/run0-start-AUTO0720-seed12345.SAV").read_bytes())["news"]; nat0 = r["nations"]
            if r["step"] != "round_done": continue
            new = new_lines(prev, after_news(r)); prev = after_news(r)
            deposed = sorted({t.split(" depose")[0] for t in new if " depose their leader " in t})
            changes = {n["name"]: n["changed"] for n in r["diff"]["nations"]}
            per_round.append((r["tag"], deposed))
            for nm, b in nat0.items():
                if nm == "Rome": continue
                debt = b["treasury"] <= -50000
                key = "debtor" if debt else ("solvent_u%d" % b["unity"])
                trials[key] += 1
                d = nm in deposed
                if d: dep[key] += 1
                c = changes.get(nm, {})
                (ud if d else un).append((key, nm, b["unity"], c.get("unity", (b["unity"], b["unity"]))[1], c.get("treasury", (b["treasury"], b["treasury"]))[1]))
        P("   per round deposed:", per_round)
        for k in sorted(trials): P(f"   {k}: trials {trials[k]}, deposed {dep[k]} = {dep[k] / trials[k]:.3f}  (1/9 = 0.111)")
        P("   (key, nation, unity before, unity after, treasury after) DEPOSED:", ud)
        # unity change summary
        def chg(lst, key): 
            v = [a[3] - a[2] for a in lst if a[0] == key]; return (len(v), min(v), max(v), sum(v) / len(v)) if v else None
        for key in sorted(trials): P(f"   unity change (n,min,max,mean) {key}: deposed {chg(ud, key)}; not deposed {chg(un, key)}")
        P("   treasury after, deposed:", sorted(collections.Counter(a[4] for a in ud).items()), " not deposed debtors:", sorted(collections.Counter(a[4] for a in un if a[0] == "debtor").items())[:12])


START = sav.load(ROOT / "saves/run0-start-AUTO0720-seed12345.SAV")
def tdiv(a, b): return int(a / b)

def section_q2():
    P("== Q2: quarter boundary, Rome (natural run Q2: six rounds from the start save; staged run Q2b: week-11 save, no AI capture first) ==")
    PRICE = {"li": 1, "hi": 2, "ar": 1, "lc": 3, "hc": 4}
    for case in ("Q2", "Q2b"):
        for f in logs(case):
            R = rows(f); sheets = {r["tag"]: r for r in R if r["step"] == "balance_sheet"}
            P(f"[{f.name}]")
            for r in R:
                if r["step"] == "balance_sheet":
                    rd = r["readings"]; m = r["memory"]
                    P(f"   sheet {r['tag']}: revenue OCR {[ (k, v['value']) for k, v in rd['revenue'].items()]} expenditure OCR {[(k, v['value']) for k, v in rd['expenditure'].items()]} balance(treasury) {rd['balance']['value']} debt limit {rd['debt_limit']['value']}; memory taxes {m['taxes']} tribute {m['tribute']} admin {m['administration']} fleet {m['fleet']} recruit {m['army_recruit']} regular {m['regular_units']} merc {m['mercenary_units']} ncities {m['ncities']} wealth {m['wealth']} tax_base {m['tax_base']} image {r['image']}")
                if r["step"] != "round_done": continue
                b, a = r["rome_before"], r["rome_after"]
                P(f"   round {r.get('round')} {r['tag']} -> {r['cal']} kept={r['kept']}: Rome treasury {b['treasury']}->{a['treasury']} ({a['treasury']-b['treasury']:+d}) unity {b['unity']}->{a['unity']} mobilization {b['mobilization']}->{a['mobilization']} wealth {b['wealth']}->{a['wealth']} tax_base {b['tax_base']}->{a['tax_base']} cities {b['cities_count']}->{a['cities_count']} tax {b['tax']}")
                P("      news:", [t for t in r["news_new"]] if r.get("news_new") else None)
                if r["cal"]["week"] == 1 and r["tag"].startswith(("q2b", "q2_round6")):
                    n = r["tag"].split("_")[-1] if r["tag"].startswith("q2b") else "round6"
                    pre = sheets.get(f"q2b_{n}_before") or sheets.get("before_round6"); post = sheets.get(f"q2b_{n}_after") or sheets.get("after_round6")
                    if pre and post:
                        pm, qm = pre["memory"], post["memory"]; prt = pre["readings"]["revenue"]["trade"]["value"]; pot = post["readings"]["revenue"]["trade"]["value"]
                        pre_bal = pm["taxes"] + pm["tribute"] + (prt or 0) - (pm["administration"] + pm["fleet"] + pm["army_recruit"] + pm["regular_units"] + pm["mercenary_units"])
                        post_bal = qm["taxes"] + qm["tribute"] + (pot or 0) - (qm["administration"] + qm["fleet"] + qm["army_recruit"] + qm["regular_units"] + qm["mercenary_units"])
                        P(f"      balance-sheet balance before tick {pre_bal:+d} (revenue - expenditure), after tick {post_bal:+d}; observed treasury change {a['treasury']-b['treasury']:+d}")
                    # formula from the after state
                    tb, tax, nc, w = a["tax_base"], a["tax"], a["cities_count"], a["wealth"]
                    P(f"      income terms from the after state: tax_base*tax/100 = {tdiv(tb*tax,100)}, tax_base/4 = {tdiv(tb,4)}, -7*cities = {-7*nc}, -wealth/20000 = {-tdiv(w,20000)}")
                    mob_new = max(0, b["mobilization"] - 3)
                    P(f"      mobilization: max(0, {b['mobilization']}-3) = {mob_new}, observed {a['mobilization']}")
                    P(f"      unity formula min(990, max(300, 25 - tax/2 + unity - mob'/5)) with unity before the nation loop unknown when cities changed hands; without events: {min(990, max(300, 25 - tax//2 + b['unity'] - mob_new//5))}, observed {a['unity']}")
                    # population per city (Rome's cities and all): formula check from the start save (Q2b only: staged unchanged)
                    if r["tag"].startswith("q2b"):
                        ok = bad = 0; bads = []
                        after_pop = {c["id"]: c["after"]["pop"] for c in r["diff"]["cities"]}
                        for c in START["cities"]:
                            o = c["owner"]
                            if o < 0 or o > 15: continue
                            nt = START["nations"][o]; tx, mb = nt["tax"], nt["mobilization"]
                            pop, mx = c["pop"], c["max_pop"]; exp = pop
                            if pop < mx:
                                d = mx - pop; s6 = d >> 2 if d >= 0 else -((-d) >> 2)
                                s6 = s6 - tdiv(s6 * tx, 0x78); i7 = s6 * mb; i4 = tdiv(i7, 300)
                                exp = min(pop + (s6 - i4) + 1, mx)
                            got = after_pop.get(c["id"], pop)
                            if exp == got: ok += 1
                            else: bad += 1; bads.append((c["name"], o, pop, mx, exp, got))
                        P(f"      per-city population, formula of FUN_00451b40 vs observed, all {ok+bad} cities: match {ok}, differ {bad}: {bads[:12]}")
                        rome = [(c["name"], c["pop"], after_pop.get(c["id"], c["pop"])) for c in START["cities"] if c["owner"] == 0]
                        P("      Rome's cities (name, pop before, pop after):", rome)

def section_q5():
    P("== Q5: rough sea ==")
    for f in logs("Q5"):
        R = rows(f)
        for r in R:
            if r["step"] == "fleet_move":
                P(f"[{f.name}] move {r['tag']}: target cell (100,47) before {r['before']['target_cell']}, fleet moves {r['before']['moves']} -> {r['moves_after']}, pos {r['pos_after']}, covered cell field after (fleet +24) {r['state_after'][1][48:52]}, info panel OCR: {r['info_ocr'][1] if r['info_ocr'] else None}, image {r['info_ocr'][0] if r['info_ocr'] else None}")
        lr = [r for r in R if r["step"] == "light_round"]
        if lr:
            import struct
            def fl(h): b = bytes.fromhex(h); x, y, _, _, own, cd, mv, su, mo, sh, co, ar, ce = struct.unpack("<13h", b[:26]); return dict(x=x, y=y, cond=co, ships=sh, cell=ce, moves=mv, supplies=su, owner=own)
            res = collections.defaultdict(list)
            for r in lr:
                kind = "rough" if "rough" in r["tag"] else "calm"
                b = fl(r["fleets_before"][2])
                aft = [fl(h) for h in r["fleets_after"]]
                a = next((x for x in aft if x["owner"] == 0 and (x["x"], x["y"]) == (b["x"], b["y"])), None)
                res[kind].append((r["tag"], r["save"], b["cond"], b["ships"], b["cell"], a["cond"] if a else None, a["ships"] if a else None, a["cell"] if a else None, [t for t in r["news_new"] if "fleet" in t.lower() or "storm" in t.lower()], r["rough_cells_after"], r["cal_before"]))
            for k, v in res.items():
                P(f"   {k}: trials {len(v)}")
                for x in v: P("     ", x)
                ds = [x[2] - x[5] for x in v if x[5] is not None]
                P(f"   {k}: condition drop per surviving trial {collections.Counter(ds)}, ships {collections.Counter((x[3], x[6]) for x in v)}")

def section_q6():
    P("== Q6: offers from a peace-only start (Rome at peace with all 15, spring week 1, one End turn per trial; the offer is rolled at Rome's next turn start, FUN_00452034) ==")
    cnt = collections.Counter(); per = []; by = collections.Counter(); mism = []
    name_ok = collections.Counter(); variants = collections.Counter(); name_bad = []
    for f in logs("Q6"):
        for r in rows(f):
            if r["step"] != "light_round": continue
            po = r.get("pending_offer"); txt = [t for t in r.get("texts", []) if "wants" in t or "alliance" in t or "form an" in t]
            has = bool(po and po["from"] >= 0)
            kind = {1: "trade", 2: "alliance"}.get(po["type"]) if has else "none"
            cnt[kind] += 1
            boxk = "none" if not txt else ("alliance" if re.search(r"form|alli|aliance", " ".join(txt)) else "trade")
            if boxk != kind: mism.append((r["tag"], kind, txt))
            # R9: proposer identity. OCR variants (e.g. 'liyia' for Illyria, 'ta' for 'to') are handled as follows: the word before 'wants' is
            # compared with the autosave's proposer name: exact (case-insensitive) = 'exact'; otherwise 'variant' only if the closest of the 16
            # nation names (difflib, cutoff 0.5) is that same proposer AND no other nation is as close; anything else is a disagreement.
            if has and txt:
                m = re.search(r"([A-Za-z]+)\s+wan", " ".join(txt)); w = m.group(1) if m else ""
                exp = NAT[po["from"]]
                if w.lower() == exp.lower(): name_ok["exact"] += 1
                else:
                    sc = sorted(((difflib.SequenceMatcher(None, w.lower(), n.lower()).ratio(), n) for n in NAT), reverse=True)
                    if sc[0][1] == exp and sc[0][0] > sc[1][0] and sc[0][0] >= 0.5: name_ok["variant"] += 1; variants[(w, exp)] += 1
                    else: name_bad.append((r["tag"], w, exp))
            elif has and not txt: name_bad.append((r["tag"], "(no box text)", NAT[po["from"]]))
            if has: by[(kind, NAT[po["from"]])] += 1
            if any(v == 3 for v in r["rome_rel_after"]): cnt["rome_at_war_at_turn_start"] += 1
            per.append((r["tag"], po, txt))
    n = len(per)
    P(f"   turn starts: {n}; offers: trade {cnt['trade']}, alliance {cnt['alliance']}, none {cnt['none']}; Rome at war with someone at the turn start in {cnt['rome_at_war_at_turn_start']} of them")
    P(f"   offer kind by proposer (the offer in the kept autosave's tail, +16/+17 words): {sorted(by.items())}")
    P(f"   box text (OCR) KIND (trade/alliance) against the autosave's pending offer: disagreements {len(mism)}: {mism}")
    P(f"   box text (OCR) PROPOSER NAME against the autosave's proposer: exact {name_ok['exact']}, OCR variant resolved to the same nation {name_ok['variant']} {dict(variants)}, disagreements {len(name_bad)}: {name_bad}")
    NEIGH = {"Carthage", "Gaul", "Illyria"}
    P(f"   alliance offers come from {sorted({k[1] for k in by if k[0]=='alliance'})}; trade offers from neighbours (Carthage, Gaul, Illyria): {sum(v for k, v in by.items() if k[0]=='trade' and k[1] in NEIGH)}; from other nations: {sum(v for k, v in by.items() if k[0]=='trade' and k[1] not in NEIGH)}")
    P(f"   expected from the roll if every neighbour pass: alliance {n * 3 / 16 / 3:.1f} (3 neighbours x 1/16 x 1/3 per turn start); upper bound for trade from the 12 non-neighbour AI nations: {n * 12 / 16 / 3:.1f}")
    for x in per:
        if x[1] and x[1]["from"] >= 0: P("   offer:", x)

def section_q3():
    P("== Q3: news order, 'destroys army of' vs the treaty block ==")
    for f in logs("Q3"):
        for r in rows(f):
            if r["step"] == "news_start": P(f"[{f.name}] news memory lines 27-31: {[ (i, r['lines'][i]) for i in range(27, 32)]}; destroys at {r['destroys']}, treaty header at {r['sues']}; image {r['root']}")
            if r["step"] == "information_window_ocr":
                o = r["ocr"]; P(f"[{f.name}] Information window ({r['image']}) OCR: 'destroys army of Ptolemaic' at char {o.find('destroys army of Ptolemaic')}, 'sues Seleucid for peace' at char {o.find('sues Seleucid')}")
    t = [l.split("\t") for l in open(D / "news_scan.txt")]
    P(f"   news_scan.txt: {len(t)} save files with both lines; treaty-block-first adjacent pairs: {sum('treaty FIRST' in x[-1] for x in t)}; destroys-first: {sum('destroys FIRST' in x[-1] for x in t)}")

if __name__ == "__main__":
    which = [a for a in sys.argv[1:] if not a.startswith("--")] or ["ab", "c", "d", "e", "f", "q2", "q3", "q5", "q6"]
    for w in which: globals()["section_" + w]()
    text = "\n".join(OUT) + "\n"
    if "--write" in sys.argv: print(write_new(D / "analysis_g3.txt", text).name)
    else: print(text[:30000])
