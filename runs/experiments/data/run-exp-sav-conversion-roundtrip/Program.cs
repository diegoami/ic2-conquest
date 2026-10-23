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
}
else throw new ArgumentException("generate or import required");
