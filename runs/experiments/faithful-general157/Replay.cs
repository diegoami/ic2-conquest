// The actual compiled ComputerGeneral, without a diagnostic replacement controller.
using System.Text.Json;
using IC2.Engine.Battle.Tactical;
using IC2.Engine.Battle.Tactical.General;
using IC2.Engine.Model;
using IC2.Engine.Serialization;

var repository=GameDataRepository.Load(Path.Combine(args[1],"data"));
var context=TacticalContext.From(repository.RulesetById("classical-faithful")!);
using var doc=JsonDocument.Parse(File.ReadAllText(args[0]));var root=doc.RootElement;
var block=root.GetProperty("entry");
int N(JsonElement e,string name)=>e.GetProperty(name).GetInt32();
int[] Values(JsonElement e,string name)=>e.GetProperty(name).EnumerateArray().Select(x=>x.GetInt32()).ToArray();
string[] types=["li","hi","ar","lc","hc"];
var slots=ValueList.From(block.GetProperty("slots").EnumerateArray().Select(s=>new TacticalSlot(
    N(s,"x"),N(s,"y"),N(s,"merc"),Array.IndexOf(types,s.GetProperty("type").GetString()),
    N(s,"troops"),N(s,"quality"),N(s,"morale"),N(s,"state"),N(s,"ammo"),N(s,"target"),s.GetProperty("name").GetString()!)));
var claims=Values(root,"entry_claims");var flags=Values(root,"entry_flags");
var selectedProvided=root.TryGetProperty("entry_selected",out var selected);
var initial=new TacticalBattleState("original-attacker","original-defender",N(block,"x2"),N(block,"y1")!=0,
    N(block,"half_round"),false,slots,ValueList.From(Values(block,"grid")),ValueList.Of(false,true),
    ValueList.Of(flags[0]!=0,flags[1]!=0),ValueList.From(Enumerable.Range(0,40).Select(i=>claims.Count(c=>c==i))),
    selectedProvided?selected.GetInt32():-1,ValueList<TacticalEvent>.Empty);
var rng=new DelphiBattleDraws(root.GetProperty("entry_seed").GetUInt32());
var phases=new List<object>();
var general=new RecordedGeneral(new ComputerGeneral(),(s,kind)=>phases.Add(new{kind,s.Counter,s.SideToMove,s.IsOver,s.Slots,s.Grid,RandSeed=rng.RandSeed}));
var result=TacticalOrders.ComputerGeneralOn(initial,context,rng,general);
var output=new{label="production",result.Accepted,result.State.IsOver,result.State.Counter,RandSeed=rng.RandSeed,
    troops=new[]{result.State.Slots.Take(20).Sum(s=>s.Troops),result.State.Slots.Skip(20).Sum(s=>s.Troops)},
    result.State.Slots,result.State.Grid,phases,
    events=result.State.Log.Select(e=>new{type=e.GetType().Name,data=JsonSerializer.SerializeToElement(e,e.GetType())}).ToArray()};
using(var file=new FileStream(args[2],FileMode.CreateNew))
    JsonSerializer.Serialize(file,new{provenance="Actual compiled production ComputerGeneral; no diagnostic ordering controller",selectedProvided,initial,fullBattles=new[]{output}});
Console.WriteLine(JsonSerializer.Serialize(new{result.Accepted,result.State.IsOver,result.State.Counter,output.troops}));
return result.Accepted&&result.State.IsOver ? 0 : 1;

sealed class RecordedGeneral(ITacticalGeneral inner,Action<TacticalBattleState,string> record) : ITacticalGeneral
{
    public TacticalBattleState Place(TacticalBattleState state,TacticalContext context,IBattleDraws draws)
    {var s=inner.Place(state,context,draws);record(s,"placement");return s;}
    public TacticalBattleState Move(TacticalBattleState state,TacticalContext context,IBattleDraws draws)
    {var s=inner.Move(state,context,draws);record(s,"movement");return s;}
}
