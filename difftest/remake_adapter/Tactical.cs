using System.Text.Json;
using IC2.Data;
using IC2.Engine.Import;
using IC2.Engine.Model;
using IC2.Engine.Presentation;
using IC2.Engine.Serialization;

// Tactical mode of the differential adapter (#231). Uses the pinned remake's public APIs only.
//
//   RemakeAdapter tactical <remake-root> <strategic.SAV> <block.bin> <commands.txt> <out.jsonl> seed=<N>
//
// strategic.SAV is the staged save without its battle block (battle flag 0); block.bin is the block that followed
// its 55-byte trailer. The game is imported, the block imported onto it (OriginalBattleBlockImport, Computer general
// off on both sides), and the battle reopened as a saved one at a half-round start with the battle's draw stream
// at <N>. Each command line ("place s x y", "move s x y", "attack s e", "shoot s e", "clear s", "end") is applied
// with TacticalBattleSession, and the board is written after it.
public static class Tactical
{
    public static int Run(string[] args)
    {
        string root = args[0], strategic = args[1], blockPath = args[2], commands = args[3], outPath = args[4];
        ulong seed = ulong.Parse(args.First(a => a.StartsWith("seed="))[5..]);
        if (File.Exists(outPath)) throw new IOException("Refusing existing output: " + outPath);
        var repo = GameDataRepository.Load(Path.Combine(root, "data"));
        var resolved = repo.Resolve("classical-mediterranean");
        var rules = repo.RulesetById("classical-faithful")!;
        var imported = OriginalSaveImporter.Import(File.ReadAllBytes(strategic), Path.GetFileName(strategic), resolved.World, rules,
            resolved.Scenario, "diff-tactical", "diff-tactical");
        var game = imported.Save.State;
        var block = SaveBattleBlock.Parse(File.ReadAllBytes(blockPath));
        var state = OriginalBattleBlockImport.Import(block, game, new[] { false, false });
        var saved = new SavedTacticalBattle(state.AttackerArmyId, state.DefenderArmyId, state.SideToMove, state.Placed, state.Counter,
            ValueList.From(state.Slots.Select(s => new SavedTacticalSlot(s.X, s.Y, s.Origin, s.Type, s.Troops, s.Quality, s.Morale,
                s.Moves, s.Shots, s.Target, s.Name, s.RoutedTroops))),
            state.Grid, state.ComputerControlled, state.ComputerGeneral, state.GeneralClaims, state.Selected, seed, true);
        var session = TacticalBattleSession.Reopen(game, rules, saved, exactRestore: true);
        using var output = new StreamWriter(outPath);
        void Emit(object value) { output.WriteLine(JsonSerializer.Serialize(value)); output.Flush(); }
        object Board() => new
        {
            side = session.Battle.SideToMove, counter = session.Battle.Counter, placed = session.Battle.Placed,
            over = session.Battle.IsOver, selected = session.Battle.Selected,
            slots = session.Battle.Slots.Select((s, k) => new { k, s.X, s.Y, s.Type, s.Troops, s.Quality, s.Morale, s.Moves, s.Shots, s.Target }),
            grid = session.Battle.Grid,
        };
        Emit(new { kind = "start", seed, computerControlled = state.ComputerControlled, board = Board() });
        int step = 0;
        foreach (var raw in File.ReadLines(commands))
        {
            var p = raw.Trim().Split(' ', StringSplitOptions.RemoveEmptyEntries);
            if (p.Length == 0 || p[0].StartsWith('#')) continue;
            int I(int i) => int.Parse(p[i]);
            TacticalBattleOrderResult r = p[0] switch
            {
                "place" => session.Place(I(1), I(2), I(3)),
                "move" => session.Move(I(1), I(2), I(3)),
                "attack" => session.Attack(I(1), I(2)),
                "shoot" => session.Shoot(I(1), I(2)),
                "clear" => session.Clear(I(1)),
                "end" => session.EndHalfRound(),
                _ => new TacticalBattleOrderResult(false, new[] { "unknown command " + p[0] }),
            };
            Emit(new { kind = "command", step = step++, command = raw.Trim(), r.Accepted, r.Lines, board = Board() });
        }
        Emit(new { kind = "done", steps = step });
        return 0;
    }
}
