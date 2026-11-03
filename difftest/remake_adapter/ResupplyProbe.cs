// The remake's resupply-city choice for one army on an imported original save (2026-11-03, Greece turn 21: the original's
// FUN_0044e670 picks the adjacent capital Antioch, the remake's march goes to Aradus).
//
//   RemakeAdapter resupplyprobe <remake-root> <start.SAV> <nation> <army-id>
//
// Prints, as JSON lines: every own city within 10 tiles with its stock, capital flag and the Faithful score; then
// ScoreResupplyCity, ResolveResupplyCity and Decide for the army (atWar as the military phase computes it). No turn is played.
using System.Text.Json;
using IC2.Engine.Ai;
using IC2.Engine.Serialization;
using IC2.Engine.Model;
using IC2.Engine.Import;
using IC2.Engine.Cities.Capture;

public static class ResupplyProbe
{
    public static int Run(string[] args)
    {
        string root = args[0], start = args[1], nation = args[2], armyId = args[3];
        var repo = GameDataRepository.Load(Path.Combine(root, "data"));
        var resolved = repo.Resolve("classical-mediterranean");
        var rules = repo.RulesetById("classical-faithful")!;
        var imported = OriginalSaveImporter.Import(File.ReadAllBytes(start), Path.GetFileName(start), resolved.World, rules,
            resolved.Scenario, "diff-resupplyprobe", "diff-resupplyprobe");
        var s = imported.Save.State;
        var view = new AiView(s, rules, resolved.World, nation);
        var army = s.ArmyById(armyId)!;
        var atWar = s.Nations.Any(n => n.Id != nation && view.IsAtWar(nation, n.Id));
        var strength = army.TotalTroops / rules.Ai.ResupplyStrengthTroopsDivisor;
        foreach (var c in s.Cities)
        {
            var d = AiView.Distance(army.X, army.Y, c.X, c.Y);
            if (c.Owner != nation || d > 10) continue;
            Console.WriteLine(JsonSerializer.Serialize(new { city = c.Id, c.X, c.Y, distance = d, c.SupplyTons, strength,
                capital = CapitalOwnership.IsAnyNationsCapital(s, c.Id) }));
        }
        var score = AiArmyTargetTree.ScoreResupplyCity(view, army, atWar);
        var resolvedCity = AiArmyTargetTree.ResolveResupplyCity(view, army, atWar);
        var decision = AiArmyTargetTree.Decide(view, army, atWar);
        Console.WriteLine(JsonSerializer.Serialize(new { army = army.Id, army.X, army.Y, army.Moves, army.SupplyTons, atWar,
            score = score.City?.Id, scoreValue = score.Score, resolve = resolvedCity.City?.Id,
            decision = decision.Selected.ToString(), decisionResupply = decision.Resupply?.City?.Id }));
        return 0;
    }
}
