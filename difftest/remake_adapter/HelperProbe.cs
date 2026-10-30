using System.Text.Json;
using IC2.Engine.Ai;
using IC2.Engine.Import;
using IC2.Engine.Model;
using IC2.Engine.Serialization;

// Research #144 (remake #1640): the remake's GarrisonFallback and MercenaryRunDestination on the same synthetic states as
// runs/experiments/boundary144/controls.py (the original's FUN_0044ebe8 / FUN_0044e84c under emulation).
//
//   RemakeAdapter helperprobe <remake-root> <start.SAV> <out.jsonl> [layout=land]
//
// From the imported start: nation carthage, deciding army army-3; every other carthage army at (300,10); every city but
// the capital at (319,139); an empty mercenary pool. Each control then places the army, cities and offers as the original
// control does and calls the two public helpers directly (no turn is played). GarrisonFallback includes the retained #925
// reachable-fallback policy (FirstReachableCity / IsUsableDestination), so a null or a different city can be that policy
// rather than the literal ordering; the output says which helper answered.
public static class HelperProbe
{
    public static int Run(string[] args)
    {
        string root = args[0], start = args[1], outPath = args[2];
        var land = args.Contains("layout=land");   // controls.py --layout land: the free land strip, cities 3 (ties 2) away
        if (File.Exists(outPath)) throw new IOException("Refusing existing output: " + outPath);
        var repo = GameDataRepository.Load(Path.Combine(root, "data"));
        var resolved = repo.Resolve("classical-mediterranean");
        var rules = repo.RulesetById("classical-faithful")!;
        var imported = OriginalSaveImporter.Import(File.ReadAllBytes(start), Path.GetFileName(start), resolved.World, rules,
            resolved.Scenario, "diff-helperprobe", "diff-helperprobe");
        var s0 = imported.Save.State;
        const string nation = "carthage", armyId = "army-3";
        var capitalId = s0.NationById(nation)!.CapitalCityId!;
        var capital = s0.CityById(capitalId)!;
        s0 = s0 with
        {
            Armies = ValueList.From(s0.Armies.Select(a => a.Nation == nation && a.Id != armyId ? a with { X = 300, Y = 10 } : a)),
            Cities = ValueList.From(s0.Cities.Select(c => c.Id == capitalId ? c : c with { X = 319, Y = 139 })),
            MercenaryPool = ValueList<MercenaryPoolSlot>.Empty,
        };
        var cityIds = s0.Cities.Select(c => c.Id).ToList();
        using var output = new StreamWriter(outPath);

        GameState Army(GameState s, int x, int y) =>
            s with { Armies = ValueList.From(s.Armies.Select(a => a.Id == armyId ? a with { X = x, Y = y } : a)) };
        GameState City(GameState s, int record, int x, int y, string? owner = null) =>
            s with { Cities = ValueList.From(s.Cities.Select((c, i) => i == record ? c with { X = x, Y = y, Owner = owner ?? c.Owner } : c)) };
        GameState Other(GameState s, int x, int y)
        {
            var other = s.Armies.First(a => a.Nation == nation && a.Id != armyId).Id;
            return s with { Armies = ValueList.From(s.Armies.Select(a => a.Id == other ? a with { X = x, Y = y } : a)) };
        }
        GameState Offer(GameState s, int slot, int x, int y) =>
            s with { MercenaryPool = ValueList.From(s.MercenaryPool.Append(new MercenaryPoolSlot(slot, x, y, 0, "light_infantry", 100, 5))) };
        void Garrison(string control, GameState s)
        {
            var view = new AiView(s, rules, resolved.World, nation);
            var army = s.ArmyById(armyId)!;
            var got = AiArmyTargetTree.GarrisonFallback(view, army, s);
            output.WriteLine(JsonSerializer.Serialize(new { control, helper = "GarrisonFallback", army = new[] { army.X, army.Y },
                destination = got is { } g ? new[] { g.X, g.Y } : null }));
        }
        void Run(string control, GameState s)
        {
            var view = new AiView(s, rules, resolved.World, nation);
            var army = s.ArmyById(armyId)!;
            var got = AiArmyTargetTree.MercenaryRunDestination(view, army);
            output.WriteLine(JsonSerializer.Serialize(new { control, helper = "MercenaryRunDestination", army = new[] { army.X, army.Y },
                destination = got is null ? null : new[] { got.X, got.Y }, city = got?.Id }));
        }

        const int x = 40;                                   // the "nearest city" record of the original controls
        var gap = land ? 3 : 1;
        if (land)
        {
            s0 = s0 with { Cities = ValueList.From(s0.Cities.Select(c => c.Id == capitalId ? c with { X = 60, Y = 20 } : c)) };
            capital = s0.CityById(capitalId)!;
        }
        foreach (var d in new[] { 9, 10, 11 })
        {
            var s = Army(s0, capital.X + d, capital.Y);
            s = City(s, x, capital.X + d + gap, capital.Y);
            Garrison($"ebe8 capital distance {d}", s);
        }
        {
            var s = Army(s0, capital.X + (land ? 8 : 20), capital.Y);
            s = City(s, x, s.ArmyById(armyId)!.X + gap, capital.Y);
            s = s with { Nations = ValueList.From(s.Nations.Select(n => n.Id == nation ? n with { CapitalCityId = null } : n)) };
            Garrison("ebe8 capital index -1 (native: no capital)", s);
        }
        const int i = 1, j = 3;                              // olisipo (record 1) and ebora (record 3): ids order the other way
        var (ax, ay, a1, b1, cx, cy, ox, oy) = land ? (68, 20, (66, 20), (70, 20), 68, 31, 68, 30) : (61, 40, (60, 40), (62, 40), 61, 50, 61, 49);
        foreach (var (label, pi, pj) in new[] { ("as staged", a1, b1), ("positions swapped", b1, a1) })
        {
            var s = Army(s0, ax, ay);
            s = s with { Cities = ValueList.From(s.Cities.Select(c => c.Id == capitalId ? c with { X = cx, Y = cy } : c)) };
            s = Other(s, ox, oy);
            s = City(s, i, pi.Item1, pi.Item2);
            s = City(s, j, pj.Item1, pj.Item2);
            Garrison($"ebe8 tie, {label} ({cityIds[i]} record {i}, {cityIds[j]} record {j})", s);
        }

        var sa = Army(s0, 60, 70);
        foreach (var d in new[] { 19, 20, 21 })
        {
            var s = City(sa, 50, 60 + d, 70, nation);
            Run($"e84c single offer at {d}", Offer(s, 201, 60 + d, 70));
        }
        foreach (var (label, s19, s20) in new[] { ("19 in slot 201, 20 in slot 202", 201, 202), ("19 in slot 202, 20 in slot 201", 202, 201) })
        {
            var s = City(City(sa, 50, 79, 70, nation), 51, 40, 70, nation);
            var pool = new[] { (s19, 79), (s20, 40) }.OrderBy(t => t.Item1);
            foreach (var (slot, px) in pool) s = Offer(s, slot, px, 70);
            Run($"e84c pair 19 vs 20, {label}", s);
        }
        foreach (var (slotLabel, slotA, slotB) in new[] { ("A in slot 201, B in slot 202", 201, 202), ("A in slot 202, B in slot 201", 202, 201) })
            foreach (var (cityLabel, ca, cb) in new[] { ("A on record i", i, j), ("A on record j", j, i) })
            {
                var s = City(City(sa, ca, 65, 70, nation), cb, 55, 70, nation);
                foreach (var (slot, px) in new[] { (slotA, 65), (slotB, 55) }.OrderBy(t => t.Item1)) s = Offer(s, slot, px, 70);
                Run($"e84c tie at 5, {slotLabel}, {cityLabel}", s);
            }
        return 0;
    }
}
