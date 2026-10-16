using System.Collections;
using System.Reflection;
using System.Text.Json;
using IC2.Engine.Battle.Tactical;
using IC2.Engine.Battle.Tactical.General;
using IC2.Engine.Tests.Battle.Tactical.GoldenMaster;
if(args.Length!=2 || Directory.Exists(args[1])) throw new ArgumentException("summary input and NEW output directory required");
Directory.CreateDirectory(args[1]);
var jopt=new JsonSerializerOptions {WriteIndented=true,PropertyNamingPolicy=JsonNamingPolicy.SnakeCaseLower};
var tests=typeof(SeriesReplayTests).Assembly;var engine=typeof(ComputerGeneral).Assembly;
const BindingFlags F=BindingFlags.Public|BindingFlags.NonPublic|BindingFlags.Static|BindingFlags.Instance;
Type T(string n)=>tests.GetType("IC2.Engine.Tests.Battle.Tactical.GoldenMaster."+n,true)!;
object? S(string t,string m,params object?[] a)=>T(t).GetMethod(m,F)!.Invoke(null,a);
object G(object o,string n)=>o.GetType().GetProperty(n,F)!.GetValue(o)!;
Type E(string n)=>engine.GetType("IC2.Engine.Battle.Tactical."+n,true)!;
object? Call(string t,string m,params object?[] a) {
 var method=E(t).GetMethods(F).Single(x=>x.Name==m && x.GetParameters().Length==a.Length && x.GetParameters().Select((p,i)=>a[i]==null||p.ParameterType.IsInstanceOfType(a[i])).All(x=>x));
 return method.Invoke(null,a);
}
var summary=JsonDocument.Parse(File.ReadAllText(args[0]));
var residual=summary.RootElement.GetProperty("rows").EnumerateArray().Where(r=>!r.GetProperty("exact").GetBoolean()).ToDictionary(r=>r.GetProperty("trial").GetString()!);
var rows=new List<object>();
foreach(var trial in ((IEnumerable)S("SeriesCatalogue","HookedTrials")!).Cast<object>()) {
 var spec=G(trial,"Series");var name=(string)G(spec,"Name");if(!residual.ContainsKey(name)) continue;
 var strict=S("GoldenReplay","Run",spec,true,null)!;var full=S("GoldenReplay","Run",spec,false,null)!;
 var snapshots=((IEnumerable<TacticalBattleState>)G(full,"Snapshots")).ToArray();
 var first=G(strict,"FirstBlockDifference");var index=(int)first.GetType().GetField("Item1")!.GetValue(first)!;
 if(index==0) throw new Exception("Need pre-first-phase state for "+name);
 var previous=snapshots[index-1];var expected=snapshots[index];var context=(TacticalContext)G(full,"Context");
 var rng=new DelphiBattleDraws((uint)G(trial,"Seed"));
 var prefix=previous.Log.OfType<TacticalDrawEvent>().ToArray();
 foreach(var d in prefix) if(rng.Random(d.Bound)!=d.Value) throw new Exception("RNG prefix mismatch");
 var draws=new ObserverDraws(rng);var state=TacticalHalfRound.End(previous,context,draws);
 state=(TacticalBattleState)S("GoldenReplay","EnableRecordedHumanGeneral",state)!;
 var reference=new ComputerGeneral().Move(state,context,new DelphiBattleDraws(rng.RandSeed));
 var board=Call("TacticalBoard","Thaw",state,context,draws)!;
 var journal=new List<GeneralDecision>();var stages=new List<object>();
 object View()=>new {slots=((TacticalSlot[])G(board,"Slots")).ToArray(),claims=((int[])G(board,"GeneralClaims")).ToArray()};
 IEnumerable<int> Order()=>((IEnumerable<int>)Call("General.GeneralOrders","InOrder",board)!);
 draws.Snapshot=()=>new {draws.Stage,draws.Actor,decision=journal.LastOrDefault(),state=View()};
 void Stage(string label,string type,string method) {
  draws.Stage=label;var start=journal.Count;var before=View();var units=new List<object>();
  foreach(var slot in Order()) { draws.Actor=slot;var ub=View();var js=journal.Count; Call(type,method,board,slot,journal); units.Add(new {slot,before=ub,after=View(),decisions=journal.Skip(js).ToArray()}); }
  stages.Add(new {stage=label,before,after=View(),decisions=journal.Skip(start).ToArray(),units});
 }
 draws.Stage="pass1";var b1=View();
 foreach(var slot in Order()) {draws.Actor=slot;var target=(int)Call("General.GeneralTargeting","Apply",board,slot,journal)!;if(target>=0) Call("General.GeneralEngage","Apply",board,slot,target,journal);}
 stages.Add(new {stage="pass1",before=b1,after=View(),decisions=journal.ToArray()});
 Stage("pass2","General.GeneralPassTwo","ApplyUnit");
 Stage("pass3-threat","General.GeneralPassThree","ThreatMoveUnit");
 Stage("pass3-pass2","General.GeneralPassTwo","ApplyUnit");
 Stage("pass3-flank","General.GeneralPassThree","FlankUnit");
 Stage("pass3-final-pass2","General.GeneralPassTwo","ApplyUnit");
 var observed=(TacticalBattleState)board.GetType().GetMethod("Freeze",F)!.Invoke(board,null)!;
 if(observed!=reference || observed!=expected) throw new Exception("Observer final state/log differs from production snapshot: "+name);
 var result=new {trial=name,counter=observed.Counter,firstBlockIndex=index,validatedEntireStateAndLog=true,originalRuntimeClaimsAndPass=(object?)null,initial=state,stages,draws=draws.Rows};
 using(var f=new FileStream(Path.Combine(args[1],name+".json"),FileMode.CreateNew)) JsonSerializer.Serialize(f,result,jopt);
 rows.Add(new {trial=name,counter=observed.Counter,validated=true,decisions=journal.Count});
 Console.WriteLine(name+" validated");
}
using(var f=new FileStream(Path.Combine(args[1],"summary.json"),FileMode.CreateNew)) JsonSerializer.Serialize(f,rows,jopt);
sealed class ObserverDraws(DelphiBattleDraws rng):IBattleDraws {
 public string Stage="previous-melee-and-setup";public int Actor=-1;public Func<object>? Snapshot;public List<object> Rows=new();
 public int Random(int n) {var before=Snapshot?.Invoke();var value=rng.Random(n);Rows.Add(new {bound=n,value,stage=Stage,actor=Actor,before});return value;}
}
