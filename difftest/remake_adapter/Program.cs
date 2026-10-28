using System.Security.Cryptography;
using System.Text.RegularExpressions;
using System.Text.Json;
using IC2.Engine.Import;
using IC2.Engine.Persistence;
using IC2.Engine.Presentation;
using IC2.Engine.Serialization;

// Differential-testing adapter for the remake (#229). Uses the pinned remake's public APIs only.
//
//   RemakeAdapter <remake-root> <start.SAV | native-save> <template.SAV> <commands.txt> <out-dir> [tactical]
//
// Placeholders in a command line name records by their position in the original format, resolved against the
// session's state at that moment: {army:N} -> the id of state.Armies[N], {fleet:N} -> state.Fleets[N],
// {city:N} -> world.Cities[N] (the world lists the cities in the original's record order).
//
// Starts a session from an original SAV (imported) or a native save, submits each command line as the
// CLI would, and at each "#checkpoint <name>" line writes <name>.native (the native JSON save) and <name>.SAV (exported
// with the template's interface settings). One JSON line per event on stdout. Never overwrites a file.
string root = args[0], start = args[1], template = args[2], commands = args[3], outDir = args[4];
var mode = args.Length > 5 && args[5] == "tactical" ? HumanBattleMode.Tactical : HumanBattleMode.Instant;
Directory.CreateDirectory(outDir);
var repo = GameDataRepository.Load(Path.Combine(root, "data"));
var resolved = repo.Resolve("classical-mediterranean");
var world = resolved.World;
var rules = repo.RulesetById("classical-faithful")!;
var scenario = resolved.Scenario;
void Emit(object value) => Console.WriteLine(JsonSerializer.Serialize(value));
string Sha(string path) => Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(path))).ToLowerInvariant();
string Fresh(string path) => File.Exists(path) ? throw new IOException("Refusing existing output: " + path) : path;

GameSession session;
if (!start.EndsWith(".sav", StringComparison.OrdinalIgnoreCase))
{
    session = new GameSession(world, rules, scenario, SaveManager.LoadFile(start, world, rules)) { HumanBattles = mode };
    Emit(new { kind = "start", from = "native", path = start, sha256 = Sha(start) });
}
else
{
    var imported = OriginalSaveImporter.Import(File.ReadAllBytes(start), Path.GetFileName(start), world, rules, scenario,
        "diff-start", "diff-start");
    session = new GameSession(world, rules, scenario, imported.Save) { HumanBattles = mode };
    Emit(new { kind = "start", from = "original-sav", path = start, sha256 = Sha(start), report = imported.Report });
}

int step = 0;
foreach (var raw in File.ReadLines(commands))
{
    var line = raw.Trim();
    if (line.Length == 0) continue;
    if (line.StartsWith("#checkpoint "))
    {
        var name = line["#checkpoint ".Length..].Trim();
        var native = Fresh(Path.Combine(outDir, name + ".native"));
        var saved = session.Submit("save " + native);
        if (!File.Exists(native)) throw new Exception("native save failed: " + string.Join("\n", saved.Lines));
        var sav = Fresh(Path.Combine(outDir, name + ".SAV"));
        object export;
        try
        {
            var written = OriginalSaveExporter.ExportFile(session, template, sav);
            export = new { ok = true, sha256 = written.OutputSha256, written.ProfileId };
        }
        catch (OriginalSaveExportException ex)
        {
            export = new { ok = false, error = ex.Message, refusals = ex.Refusals.Select(r => $"{r.Code} {r.Field}: {r.Detail}") };
        }
        Emit(new { kind = "checkpoint", name, native, nativeSha256 = Sha(native), sav, export,
            turn = session.State.Calendar.TurnIndex, calendar = session.State.Calendar.ToString(),
            active = session.State.ActiveNationId });
        continue;
    }
    if (line.StartsWith('#')) continue;
    string resolvedLine;
    try { resolvedLine = Resolve(line); }
    catch (Exception ex)
    {
        Emit(new { kind = "command", step = step++, command = line, error = "unresolved: " + ex.Message });
        continue;
    }
    var result = session.Submit(resolvedLine);
    Emit(new { kind = "command", step = step++, command = line, resolved = resolvedLine, lines = result.Lines, exit = result.ShouldExit,
        turn = session.State.Calendar.TurnIndex, active = session.State.ActiveNationId });
    if (result.ShouldExit) break;
}
Emit(new { kind = "done", steps = step });

string Resolve(string line) => Regex.Replace(line, @"\{(army|fleet|city):(\d+)\}", m =>
{
    int i = int.Parse(m.Groups[2].Value);
    return m.Groups[1].Value switch
    {
        "army" => session.State.Armies[i].Id,
        "fleet" => session.State.Fleets[i].Id,
        _ => world.Cities[i].Id,
    };
});
