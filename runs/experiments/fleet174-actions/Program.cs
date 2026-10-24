using System.Text.Json;
using IC2.Engine.Ai;
using IC2.Engine.Core;
using IC2.Engine.Import;
using IC2.Engine.Model;
using IC2.Engine.Movement.Commands;
using IC2.Engine.Naval.Commands;
using IC2.Engine.Battle.Commands;
using IC2.Engine.Serialization;

var repo=GameDataRepository.Load(Path.Combine(args[0],"data"));var context=repo.Resolve("classical-mediterranean");var rules=repo.RulesetById("classical-faithful")!;
var artifactRoot=args[1];var output=args[2];if(File.Exists(output))throw new IOException("Existing result");
var original=JsonDocument.Parse(File.ReadAllText(args[3])).RootElement.EnumerateArray().ToDictionary(x=>x.GetProperty("case").GetString()!);
var rows=new List<object>();
var version=args.Length>4?args[4]:"v1";
using var journal=new StreamWriter(new FileStream(output+".jsonl",FileMode.CreateNew));
GameState Import(string path)=>OriginalSaveImporter.Import(File.ReadAllBytes(path),path,context.World,rules,context.Scenario,"actions174","actions174").Save.State;
object? Snapshot(GameState s)=>s.FleetById("fleet-0") is {} f?new{f.X,f.Y,f.Moves,f.Ships,f.Money,f.SupplyTons,f.CarriedArmyId,cargo=f.CarriedArmyId is {} id?s.ArmyById(id):null}:null;
void Write(string path,object value){using var f=new FileStream(path,FileMode.CreateNew);JsonSerializer.Serialize(f,value,value.GetType(),new JsonSerializerOptions{WriteIndented=true});}
foreach(var folder in Directory.GetDirectories(Path.Combine(artifactRoot,"original-v1")).Order(StringComparer.Ordinal))
{
 var name=Path.GetFileName(folder);var spec=original[name];var state=Import(Path.Combine(folder,"before.SAV"));
 using var expected=JsonDocument.Parse(File.ReadAllText(Path.Combine(folder,"before.json")));
 var old=expected.RootElement.GetProperty("fleets")[0];var actor=state.FleetById("fleet-0")!;
 if(actor.X!=old.GetProperty("x").GetInt32()||actor.Y!=old.GetProperty("y").GetInt32()||actor.Moves!=old.GetProperty("moves").GetInt32()||actor.Nation!="carthage")throw new InvalidDataException("actor gate");
 var dst=Path.Combine(artifactRoot,"native-"+version,name);if(Directory.Exists(dst))throw new IOException("Existing case output");Directory.CreateDirectory(dst);
 var registry=SystemRegistry.FromEngineAssembly();var dispatcher=new CommandDispatcher(registry,rules,context.World,NullEventSink.Instance);
 object? direct=null;var goal=spec.GetProperty("native_direct_goal");
 if(goal.ValueKind!=JsonValueKind.Null)
 {
  int x=goal[0].GetInt32(),y=goal[1].GetInt32();
  var result=dispatcher.Dispatch(state,new MoveFleetCommand(actor.Nation,actor.Id,x,y));
  Write(Path.Combine(dst,"direct-before.json"),state);Write(Path.Combine(dst,"direct-after.json"),result.State);
  direct=new{goal=new[]{x,y},result.IsAccepted,result.IsRejected,rejection=result.Rejection?.ToString(),before=Snapshot(state),after=Snapshot(result.State),events=result.Events.Select(e=>new{kind=e.GetType().Name,body=JsonSerializer.SerializeToElement(e,e.GetType())})};
 }
 // This is a full native AI seat run on the declared input, not a claim that
 // original F608 alone is the equivalent whole-seat phase.
 var initial=Import(Path.Combine(artifactRoot,"inputs-v1",name,"input.SAV"));
 var trace=new RecordingDispatch(dispatcher,dst);
 var outcome=AiTurn.Run(initial,rules,context.World,trace,new SplitMix64Rng(initial.RandomSeed),NullEventSink.Instance);
 Write(Path.Combine(dst,"ai-before.json"),initial);Write(Path.Combine(dst,"ai-after.json"),outcome.State);
 Write(Path.Combine(dst,"ai-log.json"),outcome.Log);
 var row=new{caseName=name,actor_input_gate=true,direct,
  ai=new{outcome.CommandsIssued,outcome.CommandsRejected,outcome.ProjectionMismatches,outcome.HitActionCap,
    initial=Snapshot(initial),terminal=Snapshot(outcome.State),commands=trace.Rows},
  phase_limit="native full seat vs original fleet phase differ; direct movement is conditioned on measured original pre-move state/goal; AiTurn uses declared SplitMix stream from imported root seed"};
 rows.Add(row);Write(Path.Combine(dst,"result.json"),row);journal.WriteLine(JsonSerializer.Serialize(row));journal.Flush();
 Console.WriteLine(JsonSerializer.Serialize(new{caseName=name,commands=outcome.CommandsIssued,rejected=outcome.CommandsRejected,fleetCommands=trace.FleetCommands}));
}
Write(output,rows);

sealed class RecordingDispatch:ICommandDispatch
{
 readonly ICommandDispatch inner;readonly string directory;public List<object> Rows{get;}=new();public int FleetCommands{get;private set;}
 public RecordingDispatch(ICommandDispatch d,string folder){inner=d;directory=folder;}
 public CommandResult Dispatch(GameState s,ICommand c)=>Dispatch(s,c,NullEventSink.Instance);
 public CommandResult Dispatch(GameState s,ICommand c,IEventSink e)
 {
  var result=inner.Dispatch(s,c,e);var f0=s.FleetById("fleet-0");var f1=result.State.FleetById("fleet-0");
  bool fleet=c is MoveFleetCommand or AttackFleetCommand;
  Rows.Add(new{index=Rows.Count,c.Kind,command=JsonSerializer.SerializeToElement(c,c.GetType()),result.IsAccepted,rejection=result.Rejection?.ToString(),fleet0_before=f0,fleet0_after=f1});
  if(fleet)
  {
   var prefix=Path.Combine(directory,$"accepted-fleet-{FleetCommands++:03}");
   using(var f=new FileStream(prefix+"-before.json",FileMode.CreateNew))JsonSerializer.Serialize(f,s);
   using(var f=new FileStream(prefix+"-after.json",FileMode.CreateNew))JsonSerializer.Serialize(f,result.State);
  }
  return result;
 }
}
