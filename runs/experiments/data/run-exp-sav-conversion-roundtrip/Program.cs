using System.Text.Json;
using IC2.Engine.Import;
using IC2.Engine.Model;
using IC2.Engine.Persistence;
using IC2.Engine.Presentation;
using IC2.Engine.Serialization;

// Experiment adapter only. Uses the pinned remake's public APIs without editing it.
// All destinations must be new. Native JSON and original SAV contents stay private.
var repo = GameDataRepository.Load(Path.Combine(args[1], "data"));
var resolved = repo.Resolve("classical-mediterranean");
var world = resolved.World;
var rules = repo.RulesetById("classical-faithful")!;
var scenario = resolved.Scenario;
void Emit(object value) => Console.WriteLine(JsonSerializer.Serialize(value));
void SaveNew(string path, SaveGame save)
{
    if (File.Exists(path)) throw new IOException("Refusing existing output: " + path);
    SaveManager.WriteFile(path, save);
}
SaveGame Wrap(GameState state, string id) => new(GameDataSchema.CurrentVersion, id, id,
    state.ScenarioId, state.WorldId, state.RulesetId, state);
object Summary(GameState s) => new { turn = s.Calendar.TurnIndex, calendar = s.Calendar,
    active = s.ActiveNationId, armies = s.Armies.Count, fleets = s.Fleets.Count,
    building = s.Fleets.Count(f => f.IsUnderConstruction), cargo = s.Armies.Count(a => a.AboardFleetId != null),
    recruits = s.Nations.Sum(n => n.RecruitmentSlots.Count), cities = s.Cities.Count,
    human = s.Nations.Where(n => n.Control == SeatControl.Human).Select(n => n.Id).ToArray() };

if (args[0] == "generate")
{
    string dir = args[2];
    Directory.CreateDirectory(dir);
    var session = new GameSession(world, rules, scenario, seedOverride: 7, humanSeatNationId: "rome");
    void Capture(string name)
    {
        string path = Path.Combine(dir, name + ".json");
        if (File.Exists(path)) throw new IOException("Refusing existing output: " + path);
        var output = session.Submit("save " + path);
        if (!File.Exists(path)) throw new Exception(string.Join("\n", output.Lines));
        Emit(new { kind = "snapshot", name, summary = Summary(session.State), output.Lines });
    }
    void Command(string command)
    {
        var result = session.Submit(command);
        Emit(new { kind = "command", command, result.Lines, result.ShouldExit, summary = Summary(session.State) });
        if (result.ShouldExit) throw new Exception("Session ended before experiment completed");
    }
    Capture("native-initial");
    Emit(new { kind = "inventory", ownCities = session.State.Cities.Where(c => c.Owner == "rome"),
        ownArmies = session.State.Armies.Where(a => a.Nation == "rome"),
        ownFleets = session.State.Fleets.Where(f => f.Nation == "rome") });
    Command("set-tax 25");
    Command("recruit-standing rome heavy_infantry 1000");
    Command("order-fleet neapolis 10 conversion-fleet");
    Capture("native-orders");
    for (int t = 1; t <= 24; t++)
    {
        Command("end");
        if (t is 6 or 12 or 24) Capture("native-progress-" + t);
    }
    var improved = repo.RulesetById("improved")!;
    var negative = new GameSession(world, improved, scenario, seedOverride: 7, humanSeatNationId: "rome");
    SaveNew(Path.Combine(dir, "negative-improved.json"), Wrap(negative.State, "negative-improved"));
    Emit(new { kind = "negative", name = "negative-improved", summary = Summary(negative.State) });
}
else if (args[0] == "cargo")
{
    // Explicit synthetic native-model test, not a claim of reaching it by play.
    var source = SaveManager.LoadFile(args[2], world, rules);
    var s = source.State;
    var army = s.Armies.First(a => a.Nation == "rome");
    var fleet = s.Fleets.First(f => !f.IsUnderConstruction && f.CarriedArmyId is null);
    var cargo = army with { X = fleet.X, Y = fleet.Y, CoveredTileCode = null, AboardFleetId = fleet.Id };
    var carrier = fleet with { Nation = army.Nation, CarriedArmyId = army.Id };
    var changed = s with { Armies = ValueList.From(s.Armies.Select(a => a.Id == army.Id ? cargo : a)),
        Fleets = ValueList.From(s.Fleets.Select(f => f.Id == fleet.Id ? carrier : f)) };
    SaveNew(args[3], Wrap(changed, "native-cargo-synthetic"));
    var loaded = SaveManager.LoadFile(args[3], world, rules);
    Emit(new { kind = "synthetic-native-cargo", summary = Summary(loaded.State),
        construction = "One native army embarked in an existing launched fleet; carrier reassigned to army owner, coordinates and reciprocal references set through public model records. Not a gameplay-derived snapshot." });
}
else if (args[0] == "import")
{
    var imported = OriginalSaveImporter.Import(File.ReadAllBytes(args[2]), Path.GetFileName(args[2]), world, rules, scenario, "converted", "converted");
    SaveNew(args[3], imported.Save);
    // A native serialization reload checks the importer output against actual load validation.
    var loaded = SaveManager.LoadFile(args[3], world, rules);
    var session = new GameSession(world, rules, scenario, loaded);
    var status = session.Submit("status mine");
    Emit(new { kind = "import", input = Path.GetFileName(args[2]), summary = Summary(loaded.State),
        reloadEqual = loaded.State == imported.Save.State, imported.Report, status.Lines });
    if (args.Length > 4)
    {
        var output = session.Submit("set-tax 27");
        if (session.State.NationById(session.State.ActiveNationId)!.TaxRatePercent != 27)
            throw new Exception("Returned native session rejected the tax continuation");
        SaveNew(args[4], Wrap(session.State, "returned-native-continuation"));
        Emit(new { kind = "returned-session-order", command = "set-tax 27", verified = true, output.Lines,
            summary = Summary(session.State) });
    }
}
else throw new ArgumentException("generate or import required");
