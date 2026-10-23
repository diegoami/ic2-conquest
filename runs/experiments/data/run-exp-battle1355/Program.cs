using System.Globalization;
using System.Text.Json;
using System.Reflection;
using IC2.Engine.Battle.Tactical;
using IC2.Engine.Model;
using IC2.Engine.Persistence;
using IC2.Engine.Presentation;
using IC2.Engine.Serialization;

CultureInfo.CurrentCulture=CultureInfo.InvariantCulture;
var repository=GameDataRepository.Load(Path.Combine(args[1],"data"));
var resolved=repository.Resolve("classical-mediterranean");
var world=resolved.World;var rules=repository.RulesetById("classical-faithful")!;var scenario=resolved.Scenario;
var save=SaveManager.LoadFile(args[2],world,rules);
var outputDir=args[3];Directory.CreateDirectory(outputDir);
void Write(string name,object value)
{
 var path=Path.Combine(outputDir,name);
 using var f=new FileStream(path,FileMode.CreateNew);
 JsonSerializer.Serialize(f,value,value.GetType(),new JsonSerializerOptions{WriteIndented=true});
}
void SaveNew(string name,GameState state)
{
 var path=Path.Combine(outputDir,name);if(File.Exists(path))throw new IOException("Existing output");
 SaveManager.WriteFile(path,new SaveGame(GameDataSchema.CurrentVersion,name,name,state.ScenarioId,state.WorldId,state.RulesetId,state));
}
var session=new GameSession(world,rules,scenario,save){HumanBattles=HumanBattleMode.Tactical};
if(args[0]=="end")
{
 SaveNew("native-before-end.json",session.State);
 var result=session.Submit("end");
 SaveNew("native-after-end.json",session.State);
 Write("native-end-output.json",new{result.Lines,result.ShouldExit,result.Battles,battle=session.OpenTacticalBattle,frames=result.TacticalTimeline});
 Write("native-army-index.json",session.State.Armies.Select((a,i)=>new{index=i,army=a}).ToArray());
 Console.WriteLine(JsonSerializer.Serialize(new{completed=true,calendar=session.State.Calendar,active=session.State.ActiveNationId,battleOpen=session.OpenTacticalBattle!=null,
  armies=session.State.Armies.Where(a=>a.Nation is "ptolemaic" or "seleucid").Select(a=>new{a.Id,a.Nation,a.X,a.Y,a.Moves,a.Morale,troops=a.TotalTroops})}));
}
else if(args[0]=="attack")
{
 var result=session.Submit($"attack-army {args[4]} {args[5]}");
 Write("native-attack-output.json",new{result.Lines,result.ShouldExit,battle=session.OpenTacticalBattle,frames=result.TacticalTimeline});
 SaveNew("native-battle-entry-strategic.json",session.State);
 if(session.OpenTacticalBattle is null)throw new Exception("Requested battle did not open: "+string.Join(";",result.Lines));
 var controller=(TacticalBattleSession?)typeof(GameSession).GetField("_battle",BindingFlags.Instance|BindingFlags.NonPublic)!.GetValue(session);
 if(controller is null)throw new Exception("Read-only tactical trace seam unavailable");
 Write("native-initial-tactical-state.json",new{controller.Battle,controller.DrawState});
 var fought=session.Submit("battle general on");
 Write("native-general-output.json",new{fought.Lines,fought.ShouldExit,fought.EndedBattleReport,battle=session.OpenTacticalBattle,frames=fought.TacticalTimeline});
 SaveNew("native-after-battle.json",session.State);
 using(var trace=new StreamWriter(new FileStream(Path.Combine(outputDir,"native-events.jsonl"),FileMode.CreateNew)))
  foreach(var e in controller.Battle.Log)trace.WriteLine(JsonSerializer.Serialize(new{type=e.GetType().Name,data=JsonSerializer.SerializeToElement(e,e.GetType())}));
 Write("native-final-tactical-state.json",new{controller.Battle,controller.DrawState});
 Console.WriteLine(JsonSerializer.Serialize(new{completed=true,battleOpen=session.OpenTacticalBattle!=null,report=fought.EndedBattleReport is null?null:new{
  fought.EndedBattleReport.WinnerNationId,fought.EndedBattleReport.WinnerStartTotal,fought.EndedBattleReport.WinnerFinishTotal,fought.EndedBattleReport.LoserStartTotal},frames=fought.TacticalTimeline.Count}));
}
else throw new ArgumentException("end/attack");
