// Replay individual native decision routines on actual original pre-call inputs.
// This is conditional routine comparison, not an autonomous whole-battle replay.
using System.Globalization;
using System.Text.Json;
using IC2.Engine.Battle.Tactical;
using IC2.Engine.Battle.Tactical.General;
using IC2.Engine.Model;
using IC2.Engine.Persistence;
using IC2.Engine.Serialization;
using System.Reflection;

CultureInfo.CurrentCulture = CultureInfo.InvariantCulture;
var repository = GameDataRepository.Load(Path.Combine(args[1], "data"));
var context = TacticalContext.From(repository.RulesetById("classical-faithful")!);
using var input = JsonDocument.Parse(File.ReadAllText(args[0]));
var records = input.RootElement.GetProperty("records").EnumerateArray().ToArray();
int N(JsonElement e, string name) => e.GetProperty(name).GetInt32();
int[] Array(JsonElement e, string name) => e.GetProperty(name).EnumerateArray()
    .Select(x => x.TryGetInt32(out var value) ? value : unchecked((int)x.GetUInt32())).ToArray();
TacticalBattleState State(JsonElement r)
{
    var slots = r.GetProperty("slots").EnumerateArray().Select(s => new TacticalSlot(
        N(s,"x"),N(s,"y"),N(s,"origin"),N(s,"type"),N(s,"troops"),N(s,"quality"),
        N(s,"morale"),N(s,"moves"),N(s,"shots"),N(s,"target"),s.GetProperty("name").GetString()!));
    var claims = Array(r, "actor_claim_targets");
    var flags = Array(r, "flags");
    return new TacticalBattleState("original-attacker", "original-defender", N(r,"side"), N(r,"counter") > 2,
        N(r,"counter"), false, ValueList.From(slots), ValueList.From(Array(r,"grid")),
        ValueList.Of(false,true), ValueList.Of(flags[0] != 0,flags[1] != 0),
        ValueList.From(Enumerable.Range(0,40).Select(i => claims.Count(c => c == i))),
        N(r,"selected"), ValueList<TacticalEvent>.Empty);
}
object[] Difference(TacticalBattleState state, JsonElement r)
{
    var expected = State(r);
    var rows = new List<object>();
    for(int i=0;i<40;i++) if(state.Slots[i] != expected.Slots[i])
        rows.Add(new {slot=i,original=expected.Slots[i],native=state.Slots[i]});
    for(int i=0;i<168;i++) if(state.Grid[i] != expected.Grid[i])
        rows.Add(new {cell=i,original=expected.Grid[i],native=state.Grid[i]});
    for(int i=0;i<40;i++) if(state.GeneralClaims[i] != expected.GeneralClaims[i])
        rows.Add(new {claim=i,original=expected.GeneralClaims[i],native=state.GeneralClaims[i]});
    return rows.ToArray();
}
var results = new List<object>();
const BindingFlags F = BindingFlags.Static | BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic;
var engine = typeof(ComputerGeneral).Assembly;
object? Call(string type, string method, params object?[] values) => engine.GetType("IC2.Engine.Battle.Tactical."+type,true)!
    .GetMethods(F).Single(m=>m.Name==method && m.GetParameters().Length==values.Length &&
        m.GetParameters().Select((p,i)=>values[i] is null || p.ParameterType.IsInstanceOfType(values[i])).All(x=>x)).Invoke(null,values);
TacticalBattleState Alternate(TacticalBattleState state, IBattleDraws draws, bool slotPassTwo, bool slotPassThree, IList<GeneralDecision> journal)
{
    var board=Call("TacticalBoard","Thaw",state,context,draws)!;
    TacticalBattleState Freeze() => (TacticalBattleState)board.GetType().GetMethod("Freeze",F)!.Invoke(board,null)!;
    IEnumerable<int> Order(bool slots)
    {
        var candidates = slots ? Enumerable.Range(state.SideToMove*20,20)
            : (IEnumerable<int>)Call("General.GeneralOrders","InOrder",board)!;
        foreach(var i in candidates)
        {
            var now=Freeze();
            if(now.IsOver) yield break;
            if(now.Slots[i].IsLive) yield return i;
        }
    }
    void PassTwo()
    {
        foreach(var actor in Order(slotPassTwo)) Call("General.GeneralPassTwo","ApplyUnit",board,actor,journal);
    }
    foreach(var actor in Order(false))
    {
        var target=(int)Call("General.GeneralTargeting","Apply",board,actor,journal)!;
        if(target>=0) Call("General.GeneralEngage","Apply",board,actor,target,journal);
    }
    PassTwo();
    foreach(var actor in Order(slotPassThree)) Call("General.GeneralPassThree","ThreatMoveUnit",board,actor,journal);
    PassTwo();
    foreach(var actor in Order(slotPassThree)) Call("General.GeneralPassThree","FlankUnit",board,actor,journal);
    PassTwo();
    return Freeze();
}
int previousEngage = -1;
for(int k=0;k<records.Length;k++)
{
    var r=records[k];
    if(r.GetProperty("site").GetString() != "0x43a160") continue;
    int actor=N(r,"eax") & 65535, target=N(r,"edx") & 65535;
    var earlier = records.Take(k).Where(x => N(x,"seq") > previousEngage &&
        x.GetProperty("site").GetString() == "0x439e08").ToArray();
    previousEngage = N(r,"seq");
    if(earlier.Length == 0) continue;
    var choiceInput=earlier[0];
    int decodedActor=Array(choiceInput,"stack_words")[1] >> 16 & 65535;
    if(decodedActor != actor) throw new Exception("Original target-choice actor stack mismatch");
    var choice=GeneralTargeting.Choose(State(choiceInput),actor,context);
    var stop=k+1;
    while(stop<records.Length && !new[]{"0x439e08","0x43a544"}.Contains(records[stop].GetProperty("site").GetString())) stop++;
    var walks=records.Skip(k+1).Take(stop-k-1).Where(x=>x.GetProperty("site").GetString()=="0x438d24")
        .Select(x=>new[]{N(x,"edx") & 65535,(int)(x.GetProperty("edx").GetUInt32()>>16)}).ToArray();
    var journal=new List<GeneralDecision>();
    var rng=new DelphiBattleDraws(r.GetProperty("seed_before").GetUInt32());
    var after=GeneralEngage.Engage(State(r),actor,target,context,rng,journal);
    var nativeWalks=journal.Where(d=>d.Step is GeneralStep.ApproachLine or GeneralStep.ApproachBox)
        .Select(d=>new[]{d.X,d.Y}).ToArray();
    var differences=stop<records.Length ? Difference(after,records[stop]) : null;
    results.Add(new {counter=N(r,"counter"),actor,originalSeq=N(r,"seq"),choiceSeq=N(choiceInput,"seq"),
        originalTarget=target,nativeTarget=choice.Target,targetEqual=target==choice.Target,
        choiceStateDifferences=Difference(choice.State,r),
        originalWalks=walks,nativeWalks,walksEqual=walks.Length==nativeWalks.Length && walks.Zip(nativeWalks).All(p=>p.First.SequenceEqual(p.Second)),
        afterDifferences=differences,flags=Array(r,"flags"),journal,
        nativeDrawState=rng.RandSeed,originalAfterSeed=stop<records.Length ? records[stop].GetProperty("seed_before").GetUInt32() : (uint?)null});
}
var movePhases = new List<object>();
var passTwo = new List<object>();
var alternatives = new List<object>();
var threatOrderProof = new List<object>();
foreach(var counter in records.Select(r=>N(r,"counter")).Distinct().Where(c=>c>2))
{
    var phase=records.Where(r=>N(r,"counter")==counter).ToArray();
    var beginnings=phase.Where(r=>r.GetProperty("site").GetString()=="0x439e08").ToArray();
    var endings=phase.Where(r=>r.GetProperty("site").GetString()=="0x4393ec").ToArray();
    if(beginnings.Length==0 || endings.Length!=1) continue;
    var first=beginnings[0];var last=endings[0];
    var pass3=phase.Single(x=>x.GetProperty("site").GetString()=="0x43abb4");
    var observedThreats=phase.Where(x=>x.GetProperty("site").GetString()=="0x43a718").ToArray();
    var proofDraws=new DelphiBattleDraws(pass3.GetProperty("seed_before").GetUInt32());
    var proofBoard=Call("TacticalBoard","Thaw",State(pass3),context,proofDraws)!;
    TacticalBattleState ProofState()=>(TacticalBattleState)proofBoard.GetType().GetMethod("Freeze",F)!.Invoke(proofBoard,null)!;
    int observedIndex=0;
    foreach(var actor in (IEnumerable<int>)Call("General.GeneralOrders","InOrder",proofBoard)!)
    {
        var state=ProofState();var unit=state.Slots[actor];
        if(unit.Moves<=0 || unit.Target>=0) continue;
        if(observedIndex>=observedThreats.Length) break;
        var observed=observedThreats[observedIndex++];var originalActor=N(observed,"eax") & 65535;
        var inputDifferences=Difference(state,observed);
        threatOrderProof.Add(new {counter,originalSeq=N(observed,"seq"),originalActor,nativeActor=actor,
            sameActor=actor==originalActor,sharedGameplayInput=inputDifferences.Length==0,inputDifferences});
        if(actor!=originalActor || inputDifferences.Length!=0) break;
        Call("General.GeneralPassThree","ThreatMoveUnit",proofBoard,actor,new List<GeneralDecision>());
    }
    var journal=new List<GeneralDecision>();
    var rng=new DelphiBattleDraws(first.GetProperty("seed_before").GetUInt32());
    var moved=new ComputerGeneral(journal).Move(State(first),context,rng);
    movePhases.Add(new {counter,startSeq=N(first,"seq"),endSeq=N(last,"seq"),
        differences=Difference(moved,last),journal,nativeDrawState=rng.RandSeed,
        originalDrawState=last.GetProperty("seed_before").GetUInt32()});
    foreach(var (label,p2,p3) in new[]{("slot-pass2-only",true,false),("slot-pass3-only",false,true),("slot-both-later-passes",true,true)})
    {
        var draws=new DelphiBattleDraws(first.GetProperty("seed_before").GetUInt32());
        var decisions=new List<GeneralDecision>();
        var altered=Alternate(State(first),draws,p2,p3,decisions);
        alternatives.Add(new {counter,label,differences=Difference(altered,last),journal=decisions,
            nativeDrawState=draws.RandSeed,originalDrawState=last.GetProperty("seed_before").GetUInt32()});
    }
    int passTwoIndex=0;
    for(int k=0;k<phase.Length;k++)
    {
        var r=phase[k];
        if(r.GetProperty("site").GetString()!="0x43a544") continue;
        // The middle pass-two entry has no exit marker before the flank.
        // Comparing it to the final entry would incorrectly include flank effects.
        if(passTwoIndex++ == 1) continue;
        var next=phase.Skip(k+1).FirstOrDefault(x=>new[]{"0x43a544","0x43abb4","0x4393ec"}.Contains(x.GetProperty("site").GetString()));
        if(next.ValueKind==JsonValueKind.Undefined) continue;
        var draws=new DelphiBattleDraws(r.GetProperty("seed_before").GetUInt32());
        var output=GeneralPassTwo.Run(State(r),context,draws);
        passTwo.Add(new {counter,seq=N(r,"seq"),endSeq=N(next,"seq"),differences=Difference(output,next),
            nativeDrawState=draws.RandSeed,originalDrawState=next.GetProperty("seed_before").GetUInt32()});
    }
}
var fullBattles=new List<object>();
if(args.Length>3)
{
    using var entry=JsonDocument.Parse(File.ReadAllText(args[3]));
    var root=entry.RootElement;var block=root.GetProperty("entry");
    string[] types=["li","hi","ar","lc","hc"];
    var slots=ValueList.From(block.GetProperty("slots").EnumerateArray().Select(s=>new TacticalSlot(
        N(s,"x"),N(s,"y"),N(s,"merc"),System.Array.IndexOf(types,s.GetProperty("type").GetString()),
        N(s,"troops"),N(s,"quality"),N(s,"morale"),N(s,"state"),N(s,"ammo"),N(s,"target"),s.GetProperty("name").GetString()!)));
    var actorClaims=Array(root,"entry_claims");var flags=Array(root,"entry_flags");
    var initial=new TacticalBattleState("original-attacker","original-defender",N(block,"x2"),N(block,"y1")!=0,
        N(block,"half_round"),false,slots,ValueList.From(Array(block,"grid")),ValueList.Of(false,true),
        ValueList.Of(flags[0]!=0,flags[1]!=0),ValueList.From(Enumerable.Range(0,40).Select(i=>actorClaims.Count(c=>c==i))),
        root.TryGetProperty("entry_selected",out var selected)?selected.GetInt32():-1,ValueList<TacticalEvent>.Empty);
    foreach(var (label,p2,p3) in new[]{("production",false,false),("slot-pass3-only",false,true),("slot-both-later-passes",true,true)})
    {
        var rng=new DelphiBattleDraws(root.GetProperty("entry_seed").GetUInt32());
        ITacticalGeneral general=label=="production" ? new ComputerGeneral()
            : new AlternativeGeneral((s,c,d)=>Alternate(s,d,p2,p3,new List<GeneralDecision>()));
        var phases=new List<object>();
        general=new RecordedGeneral(general,(s,kind)=>phases.Add(new{kind,s.Counter,s.SideToMove,s.Slots,s.Grid,RandSeed=rng.RandSeed}));
        var output=TacticalOrders.ComputerGeneralOn(initial,context,rng,general);
        fullBattles.Add(new {label,output.Accepted,output.State.IsOver,output.State.Counter,RandSeed=rng.RandSeed,
            troops=new[]{output.State.Slots.Take(20).Sum(s=>s.Troops),output.State.Slots.Skip(20).Sum(s=>s.Troops)},
            output.State.Slots,output.State.Grid,phases,events=output.State.Log.Select(e=>new{type=e.GetType().Name,data=JsonSerializer.SerializeToElement(e,e.GetType())}).ToArray()});
    }
}
using var f=new FileStream(args[2],FileMode.CreateNew);
JsonSerializer.Serialize(f,new {provenance="Unchanged native routines on independently observed original pre-call state; alternatives change harness iteration only, not production",results,movePhases,passTwo,alternatives,threatOrderProof,fullBattles},new JsonSerializerOptions{WriteIndented=true});
Console.WriteLine($"Compared {results.Count} original pass1 engagements");

sealed class AlternativeGeneral(Func<TacticalBattleState,TacticalContext,IBattleDraws,TacticalBattleState> move) : ITacticalGeneral
{
    public TacticalBattleState Place(TacticalBattleState state,TacticalContext context,IBattleDraws draws)=>new ComputerGeneral().Place(state,context,draws);
    public TacticalBattleState Move(TacticalBattleState state,TacticalContext context,IBattleDraws draws)=>move(state,context,draws);
}

sealed class RecordedGeneral(ITacticalGeneral inner,Action<TacticalBattleState,string> record) : ITacticalGeneral
{
    public TacticalBattleState Place(TacticalBattleState state,TacticalContext context,IBattleDraws draws)
    {
        var result=inner.Place(state,context,draws);record(result,"placement");return result;
    }
    public TacticalBattleState Move(TacticalBattleState state,TacticalContext context,IBattleDraws draws)
    {
        var result=inner.Move(state,context,draws);record(result,"movement");return result;
    }
}
