// Conditional public-kernel replay on independently observed original inputs.
using System.Text.Json;
using IC2.Engine.Battle.Tactical;
using IC2.Engine.Model;
using IC2.Engine.Serialization;

using var source=JsonDocument.Parse(File.ReadAllText(args[0]));
var records=source.RootElement.GetProperty("records").EnumerateArray().ToDictionary(r=>r.GetProperty("seq").GetInt32());
var context=TacticalContext.From(GameDataRepository.Load(Path.Combine(args[2],"data")).RulesetById("classical-faithful")!);
int N(JsonElement e,string k)=>e.GetProperty(k).GetInt32();
int[] A(JsonElement e,string k)=>e.GetProperty(k).EnumerateArray().Select(v=>v.GetInt32()).ToArray();
TacticalBattleState State(JsonElement r)
{
    var slots=r.GetProperty("slots").EnumerateArray().Select(s=>new TacticalSlot(N(s,"x"),N(s,"y"),N(s,"origin"),N(s,"type"),N(s,"troops"),N(s,"quality"),N(s,"morale"),N(s,"moves"),N(s,"shots"),N(s,"target"),s.GetProperty("name").GetString()!));
    var claims=A(r,"actor_claim_targets");var flags=A(r,"flags");
    return new("attacker","defender",N(r,"side"),true,N(r,"counter"),false,ValueList.From(slots),ValueList.From(A(r,"grid")),
        ValueList.Of(false,true),ValueList.Of(flags[0]!=0,flags[1]!=0),ValueList.From(Enumerable.Range(0,40).Select(i=>claims.Count(c=>c==i))),N(r,"selected"),ValueList<TacticalEvent>.Empty);
}
object[] Diff(TacticalBattleState a,TacticalBattleState b)
{
    var rows=new List<object>();
    for(int i=0;i<40;i++) if(a.Slots[i]!=b.Slots[i]) rows.Add(new{slot=i,original=b.Slots[i],native=a.Slots[i]});
    for(int i=0;i<168;i++) if(a.Grid[i]!=b.Grid[i]) rows.Add(new{cell=i,original=b.Grid[i],native=a.Grid[i]});
    for(int i=0;i<40;i++) if(a.GeneralClaims[i]!=b.GeneralClaims[i]) rows.Add(new{claim=i,original=b.GeneralClaims[i],native=a.GeneralClaims[i]});
    return rows.ToArray();
}
var output=new List<object>();
foreach(var line in File.ReadLines(args[1]))
{
    using var doc=JsonDocument.Parse(line);var action=doc.RootElement;
    if(action.GetProperty("kind").GetString()!="walk")continue;
    var begin=records[N(action,"begin_seq")];var end=records[N(action,"end_seq")];
    var before=State(begin);var expected=State(end);int actor=N(action,"actor");var goal=A(action,"goal");
    var rng=new DelphiBattleDraws(begin.GetProperty("seed_before").GetUInt32());var observations=new List<object>();
    context.Observer=(s,e,b)=>
    {
        if(before.Counter==10&&actor==24) observations.Add(new{kind=e?.GetType().Name,boundary=b?.Kind,RandSeed=rng.RandSeed,
            s.Counter,s.SideToMove,s.Slots,s.Grid,s.GeneralClaims,s.Selected,s.ComputerControlled,s.ComputerGeneral});
    };
    var after=TacticalMovement.MoveUnit(before,actor,goal[0],goal[1],context,rng);
    output.Add(new{counter=before.Counter,actor,beginSeq=N(action,"begin_seq"),endSeq=N(action,"end_seq"),goal,
        differences=Diff(after,expected),rngEqual=rng.RandSeed==end.GetProperty("seed_before").GetUInt32(),
        originalActor=expected.Slots[actor],nativeActor=after.Slots[actor],
        events=after.Log.Select(e=>new{type=e.GetType().Name,data=JsonSerializer.SerializeToElement(e,e.GetType())}).ToArray(),observations});
}
using(var file=new FileStream(args[3],FileMode.CreateNew)) JsonSerializer.Serialize(file,new{provenance="Unchanged public MoveUnit on each exact observed original Walk input and goal; this is conditional replay",rows=output});
Console.WriteLine($"Replayed {output.Count} independently observed Walk calls");
