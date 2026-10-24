using System.Text.Json;
using IC2.Engine.Battle.Tactical;
using IC2.Engine.Model;
using IC2.Engine.Serialization;

var context=TacticalContext.From(GameDataRepository.Load(Path.Combine(args[0],"data")).RulesetById("classical-faithful")!);
TacticalBattleState Setup(int type,int moves,int ammo,int enemyType,int troops,int side=0,bool general=true)
{
    var slots=Enumerable.Repeat(TacticalSlot.Empty,40).ToArray();var grid=Enumerable.Repeat(50,168).ToArray();
    int own=side*20,enemy=(1-side)*20;
    slots[own]=new(3,3,0,type,type==3?7000:15000,6,70,moves,ammo,-1,"Moving unit");
    slots[enemy]=new(4,3,0,enemyType,troops,6,70,2,0,-1,"Weak target");
    slots[enemy+1]=new(11,10,0,1,6000,6,70,2,0,-1,"Keeps battle live");
    foreach(var index in new[]{own,enemy,enemy+1})grid[slots[index].X*12+slots[index].Y]=(index/20)*20+slots[index].Type*3+1;
    return new("a","d",side,true,10,false,ValueList.From(slots),ValueList.From(grid),ValueList.Of(false,side==1),
        ValueList.Of(side==0&&general,side==1&&general),ValueList.From(Enumerable.Repeat(0,40)),-1,ValueList<TacticalEvent>.Empty);
}
var rows=new List<object>();int failed=0;
void Case(string name,TacticalBattleState initial,int actor,Func<TacticalBattleState,bool> expected)
{
    try
    {
        var rng=new DelphiBattleDraws(1);var result=TacticalMovement.MoveUnit(initial,actor,4,3,context,rng);
        var passed=expected(result);if(!passed)failed++;
        rows.Add(new{name,passed,mover=result.Slots[actor],result.IsOver,RandSeed=rng.RandSeed,
            shots=result.Log.OfType<TacticalShotEvent>().Count(),draws=result.Log.OfType<TacticalDrawEvent>().Select(x=>new{x.Bound,x.Value}).ToArray()});
    }
    catch(Exception e){failed++;rows.Add(new{name,passed=false,error=e.ToString()});}
}
Case("last move retains routed target",Setup(0,2,2,1,250),0,s=>s.Slots[20].Troops==0&&s.Slots[0].X==3&&s.Slots[0].Moves==1&&s.Slots[0].Target==20&&s.Log.OfType<TacticalShotEvent>().Count()==1);
Case("dead captured target is not shot again",Setup(3,6,9,2,150),0,s=>s.Slots[20].Troops==0&&s.Slots[0].X==4&&s.Slots[0].Moves==4&&s.Slots[0].Shots==8&&s.Log.OfType<TacticalShotEvent>().Count()==1);
Case("living adjacent target still engages",Setup(0,2,2,1,6000),0,s=>s.Slots[20].Troops>0&&s.Slots[0].X==3&&s.Slots[0].Moves==1&&s.Slots[0].Target==20&&s.Log.OfType<TacticalShotEvent>().Count()==1);
Case("human move does not become computer shooting",Setup(0,2,2,1,250,0,false),0,s=>s.Slots[0].X==3&&s.Slots[0].Moves==2&&!s.Log.OfType<TacticalShotEvent>().Any());
Case("defender capture lifetime is symmetric",Setup(0,2,2,1,250,1),20,s=>s.Slots[0].Troops==0&&s.Slots[20].X==3&&s.Slots[20].Moves==1&&s.Slots[20].Target==0&&s.Log.OfType<TacticalShotEvent>().Count()==1);
using(var file=new FileStream(args[1],FileMode.CreateNew))JsonSerializer.Serialize(file,new{passed=rows.Count-failed,failed,rows,scope="Synthetic native regressions from original instruction/control-flow contract; not new original synthetic game runs"},new JsonSerializerOptions{WriteIndented=true});
Console.WriteLine($"{rows.Count-failed}/{rows.Count} movement controls pass");
return failed==0?0:1;
