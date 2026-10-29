using System.Text.Json;
using IC2.Engine.Import;
using IC2.Engine.Presentation;
using IC2.Engine.Serialization;

// #231 natural battle entry: import an original SAV, issue `attack-army` with tactical human battles, and write the
// opened battle's board before any order.
//   RemakeAdapter battleentry <remake-root> <start.SAV> <attacker-index> <target-index> <out.json> seed=<N>
public static class BattleEntry
{
    public static int Run(string[] args)
    {
        string root = args[0], start = args[1], outPath = args[4];
        int attacker = int.Parse(args[2]), target = int.Parse(args[3]);
        ulong seed = ulong.Parse(args.First(a => a.StartsWith("seed="))[5..]);
        if (File.Exists(outPath)) throw new IOException("Refusing existing output: " + outPath);
        var repo = GameDataRepository.Load(Path.Combine(root, "data"));
        var resolved = repo.Resolve("classical-mediterranean");
        var rules = repo.RulesetById("classical-faithful")!;
        var imported = OriginalSaveImporter.Import(File.ReadAllBytes(start), Path.GetFileName(start), resolved.World, rules,
            resolved.Scenario, "diff-entry", "diff-entry");
        var save = imported.Save with { State = imported.Save.State with { RandomSeed = seed } };
        var session = new GameSession(resolved.World, rules, resolved.Scenario, save) { HumanBattles = HumanBattleMode.Tactical };
        var a = session.State.Armies[attacker].Id;
        var t = session.State.Armies[target].Id;
        var r = session.Submit($"attack-army {a} {t}");
        var v = r.OpenBattleView;
        File.WriteAllText(outPath, JsonSerializer.Serialize(new
        {
            seed, command = $"attack-army {a} {t}", lines = r.Lines, opened = v != null,
            view = v == null ? null : new
            {
                v.AttackerArmyId, v.DefenderArmyId, v.SideToMove, v.Placed, v.Counter, v.ComputerControlled, v.ComputerGeneral,
                slots = v.Slots.Select((s, k) => new { k, s.X, s.Y, s.Type, s.Troops, s.Quality, s.Morale, s.Moves, s.Shots, s.Target }),
                grid = v.Grid,
            },
        }));
        return 0;
    }
}
