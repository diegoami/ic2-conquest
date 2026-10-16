using System.Collections;
using System.Globalization;
using System.Reflection;
using System.Security.Cryptography;
using System.Text.Json;
using IC2.Data;
using IC2.Engine.Battle.Tactical;
using IC2.Engine.Tests.Battle.Tactical.GoldenMaster;

// Calls the unchanged production golden replay and comparisons. No gameplay emulation or expectations.
if (args.Length != 1 || Directory.Exists(args[0])) throw new ArgumentException("Supply a NEW output directory.");
var output = Path.GetFullPath(args[0]);
Directory.CreateDirectory(output);
var asm = typeof(SeriesReplayTests).Assembly;
const string prefix = "IC2.Engine.Tests.Battle.Tactical.GoldenMaster.";
var json = new JsonSerializerOptions { WriteIndented = true, PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseLower };
Type T(string name) => asm.GetType(prefix + name, true)!;
object? S(string type, string method, params object?[] a) => T(type).GetMethod(method, BindingFlags.Static | BindingFlags.Public | BindingFlags.NonPublic)!.Invoke(null, a);
object? G(object obj, string key) => obj.GetType().GetProperty(key)!.GetValue(obj);
object? M(object obj, string method, params object?[] a) => obj.GetType().GetMethod(method)!.Invoke(obj, a);
void Write(string name, object value)
{
    using var f = new FileStream(Path.Combine(output, name), FileMode.CreateNew);
    JsonSerializer.Serialize(f, value, json);
}
string Hash(string path) => Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(path))).ToLowerInvariant();
object ModelState(TacticalBattleState s) => new
{
    s.SideToMove, s.Counter, s.Placed, s.IsOver,
    nationComputer = s.ComputerControlled.ToArray(), generalFlags = s.ComputerGeneral.ToArray(),
    claimCounts = s.GeneralClaims.ToArray(), slots = s.Slots.ToArray(), grid = s.Grid.ToArray(),
};
object OriginalState(SaveBattleBlock s) => new
{
    s.AttackerArmy, s.DefenderArmy, s.Side, s.Placed, s.Counter,
    generalFlags = (object?)null, claims = (object?)null,
    missingRuntimeFields = "General flags and claims are not serialized in the original save.",
    slots = s.Slots.Select((u, i) => new { slot = i, u.X, u.Y, u.Origin, u.Type, u.Troops, u.Quality, u.Morale, u.Moves, u.Shots, u.Target, u.Name }).ToArray(),
    grid = s.Grid.ToArray(),
};
Dictionary<int, Actor> OriginalActors(List<OriginalRow> records)
{
    var map = new Dictionary<int, Actor>();
    var pendingMelee = new List<int>();
    int? meleeActor = null;
    Actor? shot = null;
    var index = 0;
    foreach (var r in records)
    {
        if (r.Kind == "marker" && r.Site == 0x43910c)
            shot = new Actor(unchecked((short)r.Eax), unchecked((short)r.Edx), "shooting; legacy marker does not identify general pass", "original shot-entry AX/DX");
        if (r.Kind == "random")
        {
            if (r.Site >= 0x4393ec && r.Site < 0x439968)
            {
                pendingMelee.Add(index);
                if (pendingMelee.Count > 4) throw new InvalidDataException("Unpaired original melee draws.");
            }
            if (r.Site >= 0x43910c && r.Site < 0x4393ec && shot is not null)
                map[index] = shot;
            index++;
        }
        if (r.Kind == "marker" && r.Site == 0x438fb0 && pendingMelee.Count == 4)
        {
            if (meleeActor is null) meleeActor = unchecked((short)r.Eax);
            else
            {
                var a = new Actor(meleeActor.Value, unchecked((short)r.Eax), "melee after general movement", "two original rout-entry AX arguments following the four exchange draws");
                if (a.Unit is < 0 or >= 40 || a.Target is < 0 or >= 40) throw new InvalidDataException("Invalid original melee actor/target.");
                foreach (var i in pendingMelee) map.Add(i, a);
                pendingMelee.Clear(); meleeActor = null;
            }
        }
    }
    if (pendingMelee.Count != 0) throw new InvalidDataException("Original melee group lacks both rout-entry arguments.");
    return map;
}
Dictionary<int, Actor> ModelActors(TacticalBattleState final, List<Draw> draws)
{
    var map = new Dictionary<int, Actor>();
    var last = new List<int>();
    var i = 0;
    foreach (var e in final.Log)
    {
        if (e is TacticalDrawEvent d)
        {
            if (i >= draws.Count || d.Bound != draws[i].Bound || d.Value != draws[i].Value)
                throw new InvalidDataException("State log is not a prefix of the authoritative model draw sequence.");
            last.Add(i++);
        }
        if (e is TacticalShotEvent shot)
        {
            if (last.Count < 2) throw new InvalidDataException("Missing model shot draws.");
            foreach (var n in last.TakeLast(2)) map[n] = new Actor(shot.Shooter, shot.Target, "shooting; detailed pass trace pending", "production TacticalShotEvent after its two draws");
        }
        if (e is TacticalMeleeEvent melee)
        {
            if (last.Count < 4) throw new InvalidDataException("Missing model melee draws.");
            foreach (var n in last.TakeLast(4)) map[n] = new Actor(melee.Attacker, melee.Defender, "melee after general movement", "production TacticalMeleeEvent after its four draws");
        }
    }
    return map;
}
List<OriginalRow> ReadOriginal(string path)
{
    uint U(string s) => unchecked((uint)long.Parse(s, CultureInfo.InvariantCulture));
    return File.ReadLines(path).Skip(1).Where(s => !string.IsNullOrWhiteSpace(s)).Select(s =>
    {
        var f = s.Split(',');
        if (f.Length != 13) throw new InvalidDataException("Unexpected original hook schema.");
        return new OriginalRow(int.Parse(f[0]), f[1], int.Parse(f[2].AsSpan(2), NumberStyles.HexNumber),
            U(f[3]), U(f[4]), U(f[5]), U(f[6]), U(f[7]), U(f[8]), int.Parse(f[9]), int.Parse(f[10]), int.Parse(f[11]), f[12]);
    }).ToList();
}
var trials = ((IEnumerable)S("SeriesCatalogue", "HookedTrials")!).Cast<object>().ToArray();
if (trials.Length != 318) throw new InvalidDataException($"Expected 318 trials, found {trials.Length}.");
var summaries = new List<object>();
var exact = 0; var blocksExact = 0; var drawsExact = 0;
foreach (var trial in trials)
{
    var spec = G(trial, "Series")!;
    var name = (string)G(spec, "Name")!;
    var files = ((IEnumerable<string>)G(spec, "Files")!).ToArray();
    var hookName = (string)G(trial, "HookLog")!;
    var hookPath = (string)S("BattleFixtures", "Path_", hookName)!;
    var log = S("HookLog", "Load", hookName)!;
    var pairing = M(log, "PairingError", G(trial, "Seed"), files.Length);
    if (pairing is not null) throw new InvalidDataException(name + ": " + pairing);
    var records = ReadOriginal(hookPath);
    var originalDraws = records.Where(r => r.Kind == "random").ToList();
    var originalActors = OriginalActors(records);
    var replay = S("GoldenReplay", "Run", spec, false, null)!;
    var check = S("GoldenReplay", "Run", spec, true, null)!;
    var recorded = G(replay, "Draws")!;
    var ds = G(recorded, "Draws")!;
    var draws = ((IEnumerable)ds).Cast<object>().Select(d => new Draw((int)G(d, "Bound")!, (int)G(d, "Value")!, (int)G(d, "Counter")!)).ToList();
    var drawDifference = (string?)S("DrawComparison", "First", ds, log);
    var final = (TacticalBattleState?)G(replay, "Final");
    var modelActors = final is null ? new() : ModelActors(final, draws);
    var result = G(replay, "Conclusion") is { } c ? G(c, "Result") : null;
    var originalPeace = originalDraws.FirstOrDefault(r => r.Site == 0x45951c);
    var peaceMatch = result is not null && (bool)G(result, "PeaceDrawn")! == (originalPeace is not null)
                     && (bool)G(result, "PeaceOffered")! == (originalPeace is not null && originalPeace.Result < 2);
    var passed = (bool)G(check, "Passed")!;
    var blocksPassed = (bool)G(check, "BlocksPassed")!;
    var allPassed = passed && drawDifference is null && peaceMatch;
    exact += allPassed ? 1 : 0; blocksExact += blocksPassed ? 1 : 0; drawsExact += drawDifference is null ? 1 : 0;
    var index = 0;
    while (index < draws.Count && index < originalDraws.Count && unchecked((uint)draws[index].Bound) == originalDraws[index].Eax && unchecked((uint)draws[index].Value) == originalDraws[index].Result) index++;
    if ((drawDifference is null) != (index == draws.Count && index == originalDraws.Count)) throw new InvalidDataException("Diagnostic disagrees with authoritative draw comparer.");
    var o = index < originalDraws.Count ? originalDraws[index] : null;
    var p = index < draws.Count ? draws[index] : null;
    object? first = drawDifference is null ? null : new
    {
        drawIndex = index, original = o, model = p,
        originalActor = originalActors.GetValueOrDefault(index), modelActor = modelActors.GetValueOrDefault(index),
        originalClaims = (object?)null,
        originalClaimsStatus = "Not in legacy hook/SAV; no invented runtime claim state.",
        sourceSite = o is null ? null : $"0x{o.Site:x}",
        originalBattleFile = o is not null && o.Counter > 0 && o.Counter <= files.Length ? files[o.Counter - 1] : null,
        originalHeaderSideWarning = "Legacy side is sampled at call; half-round End toggles it before melee. Actor side is obtained from actor slot.",
    };
    var summary = new
    {
        trial = name, seed = G(trial, "Seed"), start = G(spec, "Start"), hook = hookName,
        hookSha256 = Hash(hookPath), fileCount = files.Length, pairingError = pairing,
        exact = allPassed, blocksPassed, postAndConclusionPassed = passed, drawsMatch = drawDifference is null, peaceMatch,
        originalDrawCount = originalDraws.Count, modelDrawCount = draws.Count,
        blockDifference = passed ? null : M(check, "Describe", spec), drawDifference,
        structural = G(replay, "Structural"), firstDivergence = first,
    };
    summaries.Add(summary);
    Write(name + "-draws.json", draws.Select((d, n) => new { index = n, d.Bound, d.Value, d.Counter, actor = modelActors.GetValueOrDefault(n) }).ToArray());
    if (!allPassed)
    {
        var snapshots = ((IEnumerable<TacticalBattleState>)G(replay, "Snapshots")!).ToArray();
        var modelCounter = p?.Counter;
        var modelAt = snapshots.FirstOrDefault(s => s.Counter == modelCounter);
        var previous = snapshots.LastOrDefault(s => s.Counter < modelCounter);
        SaveBattleBlock? originalAt = o is not null && o.Counter > 0 && o.Counter <= files.Length
            ? (SaveBattleBlock)S("BattleFixtures", "Block", files[o.Counter - 1])! : null;
        Write(name + "-context.json", new
        {
            summary, modelSnapshotAfterMovement = modelAt is null ? null : ModelState(modelAt),
            modelPreviousSnapshot = previous is null ? null : ModelState(previous),
            originalSnapshotBeforeMelee = originalAt is null ? null : OriginalState(originalAt),
            timingNote = "Snapshots are after movement/before melee, not necessarily the instant of a shot or flank draw.",
        });
    }
    if (summaries.Count % 25 == 0) Console.WriteLine($"Captured {summaries.Count}/318; exact so far {exact}.");
}
Write("summary.json", new
{
    count = trials.Length, exact, blocksExact, drawsExact, residual = trials.Length - exact,
    assemblySha256 = Hash(asm.Location), productionReplay = "Unmodified GoldenReplay.Run at the pinned build revision",
    actorEvidence = "Original shot-entry AX/DX; original melee actor/target from the subsequent two rout-entry AX words; model typed action events. Legacy general pass/claims not invented.",
    rows = summaries,
});
Console.WriteLine($"Done: {trials.Length} trials, {exact} exact, {trials.Length - exact} residual; blocks {blocksExact}, draws {drawsExact}.");

record Draw(int Bound, int Value, int Counter);
record Actor(int Unit, int Target, string Pass, string Evidence);
record OriginalRow(int Seq, string Kind, int Site, uint Eax, uint Edx, uint Ecx, uint SeedBefore, uint SeedAfter, uint Result, int Counter, int Side, int Flag, string Ebp);
