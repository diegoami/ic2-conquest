using System.Collections;
using System.Reflection;
using System.Text.Json;
using IC2.Engine.Battle.Tactical;
using IC2.Engine.Battle.Tactical.General;
using IC2.Engine.Model;
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
 var firstBlockIndex=index;var drawMode=Environment.GetEnvironmentVariable("IC2_OBSERVE_FIRST_DRAW")=="1";
 if(drawMode && residual[name].GetProperty("first_divergence").ValueKind!=JsonValueKind.Null) {
  var counter=residual[name].GetProperty("first_divergence").GetProperty("model").GetProperty("counter").GetInt32();index=Array.FindIndex(snapshots,s=>s.Counter==counter);
 }
 if(index<=0) throw new Exception("Need pre-first-phase state for "+name);
 if(rows.Count==0) {
 var baseState=snapshots[index-1];var ctx=(TacticalContext)G(full,"Context");
 var units=Enumerable.Repeat(TacticalSlot.Empty,40).ToArray();
 units[0]=new(5,5,0,1,3000,5,70,1,0,-1,"actor");units[20]=new(5,6,0,0,4000,1,50,0,0,-1,"weakLI");units[21]=new(6,5,0,1,2000,9,90,0,0,-1,"strongHI");
 var synthetic=baseState with {SideToMove=0,IsOver=false,Slots=new ValueList<TacticalSlot>(units),GeneralClaims=new ValueList<int>(new int[40])};
 var pass2=GeneralPassTwo.Run(synthetic,ctx,new DelphiBattleDraws(1));if(pass2.Slots[0].Target!=21) throw new Exception("Unexpected port weighted repro");
 units[0]=units[0] with {Type=0};for(var k=0;k<4;k++) units[20+k]=new(5+k,6,0,0,new[]{3000,2000,2000,1000}[k],1,100,0,0,-1,"tie");
 synthetic=synthetic with {Slots=new ValueList<TacticalSlot>(units)};
 var order=GeneralPassThree.ThreatOrder(synthetic,0,ctx);if(!order.SequenceEqual(new[]{23,22,21,20})) throw new Exception("Unexpected port sort repro");
 units=Enumerable.Repeat(TacticalSlot.Empty,40).ToArray();units[0]=new(5,5,0,0,3000,1,100,1,0,-1,"actor");units[20]=new(5,6,0,2,3000,1,100,0,1,-1,"archer");units[21]=new(6,6,0,0,1000,1,100,0,0,-1,"LI");
 synthetic=synthetic with {Slots=new ValueList<TacticalSlot>(units)};var archerOrder=GeneralPassThree.ThreatOrder(synthetic,0,ctx);if(archerOrder[0]!=20) throw new Exception("Unexpected port archer-subject repro");
 units=Enumerable.Repeat(TacticalSlot.Empty,40).ToArray();units[0]=new(5,5,0,1,3000,5,70,2,0,-1,"actor");
 var positions=new[]{(8,6),(9,6),(8,5),(9,5)};for(var k=0;k<4;k++)units[20+k]=new(positions[k].Item1,positions[k].Item2,0,0,1000,5,70,0,0,-1,"enemy");
 synthetic=synthetic with {Slots=new ValueList<TacticalSlot>(units),Grid=new ValueList<int>(Enumerable.Repeat(50,168)),Counter=20};
 var flankState=GeneralPassThree.Flank(synthetic,ctx,new DelphiBattleDraws(1));var flankDestination=new[]{flankState.Slots[0].X,flankState.Slots[0].Y};if(!flankDestination.SequenceEqual(new[]{3,7}))throw new Exception("Unexpected port flank equal-Y repro");
 using var f=new FileStream(Path.Combine(args[1],"model-repros.json"),FileMode.CreateNew);JsonSerializer.Serialize(f,new {weightedPass2Target=pass2.Slots[0].Target,sortOrder=order,archerSubjectOrder=archerOrder,flankDestination,matrix=Enumerable.Range(0,5).SelectMany(a=>Enumerable.Range(0,5).Select(b=>ctx.Matrix(a,b))).ToArray()},jopt);
}
var previous=snapshots[index-1];var expected=snapshots[index];var context=(TacticalContext)G(full,"Context");
 var rng=new DelphiBattleDraws((uint)G(trial,"Seed"));
 var prefix=previous.Log.OfType<TacticalDrawEvent>().ToArray();
 foreach(var d in prefix) if(rng.Random(d.Bound)!=d.Value) throw new Exception("RNG prefix mismatch");
 var draws=new ObserverDraws(rng);var state=TacticalHalfRound.End(previous,context,draws);
 state=(TacticalBattleState)S("GoldenReplay","EnableRecordedHumanGeneral",state)!;
 var reference=new ComputerGeneral().Move(state,context,new DelphiBattleDraws(rng.RandSeed));
 var board=Call("TacticalBoard","Thaw",state,context,draws)!;
 var journal=new List<GeneralDecision>();var stages=new List<object>();
 object View()=>new {slots=((TacticalSlot[])G(board,"Slots")).ToArray(),claims=((int[])G(board,"GeneralClaims")).ToArray(),grid=((int[])G(board,"Grid")).ToArray()};
 IEnumerable<int> Order()=>((IEnumerable<int>)Call("General.GeneralOrders","InOrder",board)!);
 draws.Snapshot=()=>new {draws.Stage,draws.Actor,decision=journal.LastOrDefault(),state=View()};
 void Stage(string label,string type,string method) {
  draws.Stage=label;var start=journal.Count;var before=View();var units=new List<object>();
  foreach(var slot in Order()) { draws.Actor=slot;var ub=View();var js=journal.Count;var frozen=(TacticalBattleState)board.GetType().GetMethod("Freeze",F)!.Invoke(board,null)!;var threatOrder=label=="pass3-threat" ? GeneralPassThree.ThreatOrder(frozen,slot,context).ToArray():null; Call(type,method,board,slot,journal); units.Add(new {slot,before=ub,after=View(),threatOrder,decisions=journal.Skip(js).ToArray()}); }
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
 var result=new {trial=name,counter=observed.Counter,firstBlockIndex,observedSnapshotIndex=index,selectionMode=drawMode?"first-model-draw-divergence":"first-state-divergence",validatedEntireStateAndLog=true,originalRuntimeClaimsAndPass=(object?)null,initial=state,stages,draws=draws.Rows};
 using(var f=new FileStream(Path.Combine(args[1],name+".json"),FileMode.CreateNew)) JsonSerializer.Serialize(f,result,jopt);
 rows.Add(new {trial=name,counter=observed.Counter,validated=true,decisions=journal.Count});
 Console.WriteLine(name+" validated");
}
using(var f=new FileStream(Path.Combine(args[1],"summary.json"),FileMode.CreateNew)) JsonSerializer.Serialize(f,rows,jopt);
sealed class ObserverDraws(DelphiBattleDraws rng):IBattleDraws {
 public string Stage="previous-melee-and-setup";public int Actor=-1;public Func<object>? Snapshot;public List<object> Rows=new();
 public int Random(int n) {var before=Snapshot?.Invoke();var value=rng.Random(n);Rows.Add(new {bound=n,value,stage=Stage,actor=Actor,before});return value;}
}
