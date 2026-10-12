"""Print a compact summary of the round_done / prediction / error lines of a g3_checks log (reading helper)."""
import json,sys
for l in open(sys.argv[1]):
    r=json.loads(l)
    if r["step"] in("round_done","prediction","error","done"):
        print(r["step"],r.get("tag"),r.get("cal"),"NEWS",r.get("news_new"),"TXT",r.get("texts"), "CITIES",[ (c["name"],c["before"]["owner"],c["after"]["owner"],c["before"]["loyalty"],c["after"]["loyalty"]) for c in r.get("diff",{}).get("cities",[]) if c["before"]["owner"]!=c["after"]["owner"] or abs(c["before"]["loyalty"]-c["after"]["loyalty"])>5] , r.get("predicted"), r.get("observed_owner"), r.get("error"), r.get("game_over"))
