using System.Text.Json;
using System.Text.RegularExpressions;
using IC2.Engine.Ai;
using IC2.Engine.Import;
using IC2.Engine.Model;
using IC2.Engine.Movement.Commands;
using IC2.Engine.Economy;
using IC2.Engine.Presentation;
using IC2.Engine.Serialization;

// AI march probe (follow-up of findings/2026-10-30-ai-march-continuation-missing-in-remake.md): how often does a remake
// AI march end short of its aimed point with moves left?
//
//   RemakeAdapter aiprobe <remake-root> <start.SAV> <turns> <out.jsonl> seed=<N> [decisions=<out2.jsonl>] [relations=<out3.json>] [ailog=<out4.txt>]
//
// decisions= (#138) also installs the remake's own target-tree log (AiArmyTargetTree.NewDecisionLog) and writes each
// DecisionRecord (kind, city and army targets, their scores and distances) as one JSON line, after the last turn.
//
// Plays <turns> End turns from an imported original save (the human seat gives no orders). Each AI seat's
// AiTurnDecided lines name the chosen marches ("... (x, y) with army-N: K tiles away"); right after that seat's turn
// the probe records the march's ArmyMoved event (from, to, moves spent). Events arrive once per round of seats, when
// some seats' armies are already refilled and others not, so the allowance is RECOMPUTED with the remake's own refill
// rule (SupplyMoraleRule.BaseMoves and the supply penalty, as EndTurnWarnings.RecomputedArmyMoves) from the army as
// it stands at the end of the round: an estimate where troops or supplies changed during the round. One JSON line per march.
public static class AiProbe
{
    static readonly Regex March = new(@"chose \[Military/(?<kind>[^\]]+)\] score \S+ of \S+ candidates -- (?<why>.*?) \((?<x>-?\d+), (?<y>-?\d+)\) with (?<army>\S+): (?<dist>\d+) tiles away");

    public static int Run(string[] args)
    {
        string root = args[0], start = args[1], outPath = args[3];
        int turns = int.Parse(args[2]);
        ulong seed = ulong.Parse(args.First(a => a.StartsWith("seed="))[5..]);
        if (File.Exists(outPath)) throw new IOException("Refusing existing output: " + outPath);
        var repo = GameDataRepository.Load(Path.Combine(root, "data"));
        var resolved = repo.Resolve("classical-mediterranean");
        var rules = repo.RulesetById("classical-faithful")!;
        var imported = OriginalSaveImporter.Import(File.ReadAllBytes(start), Path.GetFileName(start), resolved.World, rules,
            resolved.Scenario, "diff-aiprobe", "diff-aiprobe");
        var decisionsPath = args.FirstOrDefault(a => a.StartsWith("decisions="))?[10..];
        if (decisionsPath != null && File.Exists(decisionsPath)) throw new IOException("Refusing existing output: " + decisionsPath);
        var decisions = decisionsPath == null ? null : AiArmyTargetTree.NewDecisionLog();
        var save = imported.Save with { State = imported.Save.State with { RandomSeed = seed } };
        var session = new GameSession(resolved.World, rules, resolved.Scenario, save) { HumanBattles = HumanBattleMode.Instant };
        using var output = new StreamWriter(outPath);
        var aiLogPath = args.FirstOrDefault(a => a.StartsWith("ailog="))?[6..];
        if (aiLogPath != null && File.Exists(aiLogPath)) throw new IOException("Refusing existing output: " + aiLogPath);
        using var aiLog = aiLogPath == null ? null : new StreamWriter(aiLogPath);
        int turn = 0;
        session.EventsPublished += events =>
        {
            var moved = events.OfType<ArmyMoved>().GroupBy(m => m.ArmyId).ToDictionary(g => g.Key, g => g.ToList());
            foreach (var e in events.OfType<AiTurnDecided>())
            {
                foreach (var line in e.Lines) aiLog?.WriteLine(e.NationId + "\t" + line);
                foreach (var line in e.Lines)
                {
                    var m = March.Match(line);
                    if (!m.Success) continue;
                    var army = session.State.ArmyById(m.Groups["army"].Value);
                    int ax = int.Parse(m.Groups["x"].Value), ay = int.Parse(m.Groups["y"].Value);
                    var walks = moved.TryGetValue(m.Groups["army"].Value, out var w) ? w : new List<ArmyMoved>();
                    var walk = walks.FirstOrDefault();
                    output.WriteLine(JsonSerializer.Serialize(new
                    {
                        walks = walks.Count, from = walk == null ? null : new[] { walk.FromX, walk.FromY },
                        to = walk == null ? null : new[] { walk.ToX, walk.ToY }, spent = walk?.MovesSpent,
                        allowance = army == null ? (int?)null : Allowance(army, rules),
                        left = walk == null || army == null ? (int?)null : Allowance(army, rules) - walk.MovesSpent,
                        distAfterWalk = walk == null ? (int?)null : Math.Max(Math.Abs(walk.ToX - ax), Math.Abs(walk.ToY - ay)),
                        turn, nation = e.NationId, army = m.Groups["army"].Value, kind = m.Groups["kind"].Value,
                        why = m.Groups["why"].Value, aim = new[] { ax, ay }, distBefore = int.Parse(m.Groups["dist"].Value),
                        alive = army != null, pos = army == null ? null : new[] { army.X, army.Y },
                        movesAfter = army?.Moves, distAfter = army == null ? (int?)null : Math.Max(Math.Abs(army.X - ax), Math.Abs(army.Y - ay)),
                    }));
                }
            }
            output.Flush();
        };
        static int Allowance(ArmyState a, Ruleset r)
        {
            var troops = Math.Max(1, a.TotalTroops);
            var moves = SupplyMoraleRule.BaseMoves(troops, r);
            if ((long)a.SupplyTons * troops / r.Economy.SupplyPercentNumerator < r.Economy.SupplyMorale.DecayThresholdPercent)
                moves -= r.Economy.SupplyMorale.MovesPenaltyOnDecay;
            return moves;
        }
        for (turn = 1; turn <= turns; turn++)
        {
            var r = session.Submit("end");
            if (r.ShouldExit) break;
        }
        var relationsPath = args.FirstOrDefault(a => a.StartsWith("relations="))?[10..];
        if (relationsPath != null)
        {
            // The relation matrix after the last turn, {nation: {other: code}} (#aidecide: war ended or declared in the round).
            var rel = session.State.Relations;
            var m = rel.NationIds.ToDictionary(a => a, a => rel.NationIds.Where(b => b != a).ToDictionary(b => b, b => rel.Get(a, b)));
            using var fr = new FileStream(relationsPath, FileMode.CreateNew);
            JsonSerializer.Serialize(fr, m);
        }
        if (decisions != null)
        {
            using var d = new StreamWriter(decisionsPath!);
            foreach (var rec in decisions)
                d.WriteLine(JsonSerializer.Serialize(rec with { }, new JsonSerializerOptions { Converters = { new System.Text.Json.Serialization.JsonStringEnumConverter() } }));
            AiArmyTargetTree.ClearDecisionLog();
        }
        return 0;
    }
}
