// Scalar probe of the real retained upstream helper. No copied formula.
// Build source pin b593c6e; helper blob verified identical at a5cfebe main.
using System.Text.Json;
using IC2.Engine.Economy;
using IC2.Engine.Model;
using IC2.Engine.Serialization;
var rules=GameDataRepository.Load(Path.Combine(args[0],"data")).RulesetById("classical-faithful")!;
var rows=new List<object>();
foreach(var file in args.Skip(2))
foreach(var c in JsonDocument.Parse(File.ReadAllText(file)).RootElement.EnumerateArray())
{
 int t=c.GetProperty("treasury").GetInt32(),p=c.GetProperty("purse").GetInt32();
 int provider=c.TryGetProperty("fleet_money",out var fm)?fm.GetInt32():50;
 int request=c.GetProperty("direction").GetInt32()*100;
 string kind=c.GetProperty("kind").GetString()!,via=c.GetProperty("provider").GetString()!;
 var n=new NationState("test","test","#000000","test",null,SeatControl.Human,null,t,800,0,0,20,0,0,0,t,0,ValueList<RecruitmentSlot>.Empty,false);
 int[] result;
 if(kind=="army"&&via=="fleet") {
  var r=TreasuryPurseTransfer.TransferBetweenPurses(provider,p,request,rules);
  result=[t,r.ToMoney,r.FromMoney];
 } else if(kind=="army") {
  var a=new ArmyState("a","test",101,45,8,70,p,0,2,null,ValueList<UnitSlot>.Empty);
  var r=TreasuryPurseTransfer.TransferWithArmy(n,a,request,rules);
  result=[r.Nation.Treasury,r.Army.Money,provider];
 } else {
  var f=new FleetState("f","test",101,46,8,30,100,p,0,null,null,null,0);
  var r=TreasuryPurseTransfer.TransferWithFleet(n,f,request,rules);
  result=[r.Nation.Treasury,r.Fleet.Money,provider];
 }
 var expected=c.GetProperty("expected").EnumerateArray().Select(x=>x.GetInt32()).ToArray();
 rows.Add(new{id=c.GetProperty("id").GetString(),native_after=result,original_prediction=expected,matches_prediction=result.SequenceEqual(expected),scope="actual helper; not CLI/UI provider routing"});
}
using var output=new FileStream(args[1],FileMode.CreateNew);
JsonSerializer.Serialize(output,rows,new JsonSerializerOptions{WriteIndented=true});
Console.WriteLine($"Native helper evaluated {rows.Count} predeclared cases");
