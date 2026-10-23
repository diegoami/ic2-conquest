// Observable regression checks against the actual engine assembly, before/after.
using System.Reflection;
using System.Text.Json;
using IC2.Engine.Battle.Tactical;
using IC2.Engine.Battle.Tactical.General;
using IC2.Engine.Model;
using IC2.Engine.Serialization;

var repository=GameDataRepository.Load(Path.Combine(args[0],"data"));
var context=TacticalContext.From(repository.RulesetById("classical-faithful")!);
const BindingFlags F=BindingFlags.Static|BindingFlags.Instance|BindingFlags.Public|BindingFlags.NonPublic;
var assembly=typeof(ComputerGeneral).Assembly;
Type T(string name)=>assembly.GetType("IC2.Engine.Battle.Tactical."+name,true)!;
object Board(TacticalBattleState state)=>T("TacticalBoard").GetMethod("Thaw",F)!.Invoke(null,[state,context,new DelphiBattleDraws(7)])!;
IEnumerable<int> Order(object board,string method)=>(IEnumerable<int>)(T("General.GeneralOrders").GetMethod(method,F)
    ?? throw new MissingMethodException(method)).Invoke(null,[board])!;
TacticalSlot Unit(int type,int x,int y,int troops,int moves,int shots)=>new(x,y,0,type,troops,6,70,moves,shots,-1,"Synthetic");
TacticalBattleState State(IEnumerable<(int Index,TacticalSlot Unit)> units,int side=0)
{
    var slots=Enumerable.Repeat(TacticalSlot.Empty,40).ToArray();var grid=Enumerable.Repeat(50,168).ToArray();
    foreach(var (index,unit) in units)
    {
        slots[index]=unit;grid[unit.X*12+unit.Y]=(index/20)*20+unit.Type*3+1;
    }
    return new("attacker","defender",side,true,3,false,ValueList.From(slots),ValueList.From(grid),
        ValueList.Of(false,true),ValueList.Of(true,false),ValueList.From(Enumerable.Repeat(0,40)),-1,ValueList<TacticalEvent>.Empty);
}
void Require(bool condition,string message) {if(!condition)throw new Exception(message);}
var results=new List<object>();int failures=0;
void Check(string name,Func<object> test)
{
    try {results.Add(new{name,passed=true,evidence=test()});}
    catch(Exception e) {failures++;results.Add(new{name,passed=false,error=e.GetBaseException().Message});}
}
var mixed=State(Enumerable.Range(0,5).Select(i=>(i,Unit(new[]{0,1,2,4,3}[i],i+1,1,1000,1,1))));
Check("pass one retains type ordering",()=>
{
    var actual=Order(Board(mixed),"InOrder").ToArray();Require(actual.SequenceEqual(new[]{1,3,4,0,2}),"Pass one order changed");return actual;
});
Check("later passes use live slot order",()=>
{
    var actual=Order(Board(mixed),"InSlotOrder").ToArray();Require(actual.SequenceEqual(new[]{0,1,2,3,4}),"Later order differs");return actual;
});
Check("defender slot order stays on defender side",()=>
{
    var state=State(Enumerable.Range(0,5).Select(i=>(i+20,Unit(new[]{0,1,2,4,3}[i],i+1,9,1000,1,1))),1);
    var actual=Order(Board(state),"InSlotOrder").ToArray();Require(actual.SequenceEqual(new[]{20,21,22,23,24}),"Wrong side/slot order");return actual;
});
Check("slot enumeration rechecks liveness and battle end",()=>
{
    var board=Board(mixed);using var order=Order(board,"InSlotOrder").GetEnumerator();
    Require(order.MoveNext()&&order.Current==0,"First unit missing");
    var slots=(TacticalSlot[])board.GetType().GetProperty("Slots",F)!.GetValue(board)!;slots[1]=TacticalSlot.Empty;
    Require(order.MoveNext()&&order.Current==2,"Dead unit was yielded");
    board.GetType().GetProperty("IsOver",F)!.SetValue(board,true);
    Require(!order.MoveNext(),"Continued after battle ended");return new{yielded=new[]{0,2},stopped=true};
});
Check("actual threat pass visits slot zero before heavy infantry",()=>
{
    var state=State(new[]{(0,Unit(0,3,1,15000,1,7)),(1,Unit(1,7,1,6000,2,0)),(20,Unit(0,5,10,15000,1,7))});
    var journal=new List<GeneralDecision>();GeneralPassThree.ThreatMove(state,context,new DelphiBattleDraws(7),journal);
    var actors=journal.Select(x=>x.Slot).Distinct().ToArray();Require(actors.SequenceEqual(new[]{0,1}),"Threat pass still uses type order: "+string.Join(',',actors));return actors;
});
Check("actual second pass fires archer slot zero before light infantry",()=>
{
    var state=State(new[]{(0,Unit(2,4,5,3500,1,25)),(1,Unit(0,5,4,15000,1,7)),(20,Unit(1,5,5,6000,2,0))});
    var after=GeneralPassTwo.Run(state,context,new DelphiBattleDraws(7));
    var actors=after.Log.OfType<TacticalShotEvent>().Select(e=>e.Shooter).ToArray();
    Require(actors.Length>=2&&actors[0]==0&&actors[1]==1,"Shot order differs: "+string.Join(',',actors));return actors;
});
using(var file=new FileStream(args[1],FileMode.CreateNew))
    JsonSerializer.Serialize(file,new{failures,passed=results.Count-failures,results},new JsonSerializerOptions{WriteIndented=true});
Console.WriteLine($"{results.Count-failures}/{results.Count} regression checks pass");
return failures==0 ? 0 : 1;
