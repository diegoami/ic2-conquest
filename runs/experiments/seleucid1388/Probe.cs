using System.Globalization;
using System.Text.Json;
using IC2.Engine.Ai;
using IC2.Engine.Model;
using IC2.Engine.Persistence;
using IC2.Engine.Presentation;
using IC2.Engine.Serialization;
using IC2.Engine.Strength;
using IC2.Engine.Movement;
using System.Reflection;

// Read-only diagnostics; all full campaign outputs must remain private.
CultureInfo.CurrentCulture = CultureInfo.InvariantCulture;
var repository = GameDataRepository.Load(Path.Combine(args[0], "data"));
var resolved = repository.Resolve("classical-mediterranean");
var rules = repository.RulesetById("classical-faithful")!;
var save = SaveManager.LoadFile(args[1], resolved.World, rules);
var output = args[2];
if (Directory.Exists(output)) throw new IOException("Existing output directory");
Directory.CreateDirectory(output);
void Write(string name, object value)
{
    using var f = new FileStream(Path.Combine(output, name), FileMode.CreateNew);
    JsonSerializer.Serialize(f, value, value.GetType(), new JsonSerializerOptions { WriteIndented = true });
}
var session = new GameSession(resolved.World, rules, resolved.Scenario, save);
var decisions = AiArmyTargetTree.NewDecisionLog();
try
{
    Write("before.json", session.State);
    var result = session.Submit("end");
    Write("after.json", session.State);
    Write("decisions.json", decisions);
    var movement=session.LastStrategicTimeline.Steps.First(s=>s.Routes.Any(r=>r.EntityId=="army-4"));
    Write("defender-command-before.json",movement.Before);
    var actor=movement.Before.ArmyById("army-4")!;
    var view=new AiView(movement.Before,rules,resolved.World,"seleucid");
    var strength=ArmyPower.Compute(actor.Units,actor.Morale,rules);
    Write("target-diagnostics.json",movement.Before.Armies.Where(t=>t.Nation=="ptolemaic").Select(t=>new{
        t.Id,t.X,t.Y,t.TotalTroops,t.Morale,
        strength=ArmyPower.Compute(t.Units,t.Morale,rules),actorStrength=strength,
        distance=AiView.Distance(actor.X,actor.Y,t.X,t.Y),
        reachable=AiArmyTargetTree.IsReachable(view,actor,t.X,t.Y)
    }).ToArray());
    var walker=typeof(AiArmyTargetTree).GetMethod("WalkTowards",BindingFlags.Static|BindingFlags.NonPublic)!;
    var terrain=resolved.World.Terrain.Decode(resolved.World.Width,resolved.World.Height);
    Write("conditional-walks.json",new[]{(207,95),(191,95),(189,104)}.Select(goal=>new{
        goal=new[]{goal.Item1,goal.Item2},
        walk=(MovementWalkResult?)walker.Invoke(null,new object[]{view,actor,goal.Item1,goal.Item2,terrain,actor.Moves})
    }).ToArray());
    Write("unlimited-walks.json",new[]{(207,95),(191,95)}.Select(goal=>new{
        goal=new[]{goal.Item1,goal.Item2},
        walk=(MovementWalkResult?)walker.Invoke(null,new object[]{view,actor,goal.Item1,goal.Item2,terrain,1000000})
    }).ToArray());
    Write("routes.json", session.LastStrategicTimeline.Steps.Select(s => new {
        s.StepId, s.Identity, s.Kind, beforeCalendar=s.Before.Calendar,
        s.Before.ActiveNationId, s.Routes,
        defenderBefore=s.Before.Armies.FirstOrDefault(a=>a.Id=="army-4"),
        defenderAfter=s.After.Armies.FirstOrDefault(a=>a.Id=="army-4")
    }).ToArray());
    Write("output.json", new { result.Lines, result.ShouldExit, result.Battles });
    Console.WriteLine(JsonSerializer.Serialize(new { complete=true,
        decisions=decisions.Count, steps=session.LastStrategicTimeline.Steps.Count,
        defender=session.State.Armies.Where(a=>a.Id=="army-4").Select(a=>new {a.X,a.Y,a.Moves,a.TotalTroops}) }));
}
finally { AiArmyTargetTree.ClearDecisionLog(); }
