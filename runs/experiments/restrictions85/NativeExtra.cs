using IC2.Engine.Model;
using IC2.Engine.Serialization;
using IC2.Engine.Tests.Core;
using IC2.Engine.Tests.Armies;
using IC2.Engine.Armies.Commands;
using IC2.Engine.Naval.Commands;
using IC2.Engine.Recruitment.Commands;
using IC2.Slice.UI;
var rules=GameDataRepository.Load("data").Resolve("classical-mediterranean").Ruleset;
var dispatcher=ArmiesTestbed.DispatcherWithRuleset(rules);
var initial=CoreTestbed.InitialState();
var army=new ArmyState("a","north",3,2,7,70,30000,206,2,null,ValueList.Of(new UnitSlot(0,"light_infantry",10000,6,"A")));
var partner=army with { Id="b", X=4, SupplyTons=0 };
var unchanged=ArmyTransferModel.ForArmies(army,partner,rules);
var us=initial with { Armies=ValueList.Of(army,partner) };
var ur=dispatcher.Dispatch(us,new ArmyTransferCommand("north","a","b",ValueList<int>.Empty,0,0,ValueList<int>.Empty,0,0));
Console.WriteLine($"unchanged model={unchanged.ComposeOk()??"<none>"} rejected={ur.IsRejected} code={ur.Code} supply={ur.State.ArmyById("a")!.SupplyTons}/{ur.State.ArmyById("b")!.SupplyTons}");
foreach(var total in new[]{5000,5001,5499,5500}){
 var carrier=new FleetState("f","north",4,2,7,10,100,123,321,null,null,null,null);
 var aa=army with { Units=ValueList.Of(new UnitSlot(0,"light_infantry",total,6,"A")),SupplyTons=100 };
 var es=initial with { Armies=ValueList.Of(aa),Fleets=ValueList.Of(carrier) };
 var er=dispatcher.Dispatch(es,new EmbarkArmyCommand("north","a","f"));
 Console.WriteLine($"embark total={total} rejected={er.IsRejected} code={er.Code} carried={er.State.FleetById("f")!.CarriedArmyId??"<none>"}");
 aa=army with { X=4,AboardFleetId="f",CoveredTileCode=null,SupplyTons=100,Units=ValueList.Of(new UnitSlot(0,"light_infantry",4000,6,"A")) };
 var city=new CityState("port","Port",3,2,"north","north",90,330,0,100,100,0,ValueList<UnitSlot>.Empty);
 var hs=initial with { Armies=ValueList.Of(aa),Fleets=ValueList.Of(carrier with {CarriedArmyId="a"}),Cities=ValueList.Of(city),MercenaryPool=ValueList.Of(new MercenaryPoolSlot(0,3,2,1,"light_infantry",total-4000,6)) };
 var hr=dispatcher.Dispatch(hs,new HireMercenaryCommand("north","a",0));
 Console.WriteLine($"hire total={total} rejected={hr.IsRejected} code={hr.Code} troops={hr.State.ArmyById("a")!.TotalTroops}");
}
foreach(var money in new[]{950,1000,1100}){
 var donorFleet=new FleetState("from","north",3,2,7,10,100,200,0,null,null,null,null);
 var to=donorFleet with {Id="to",Y=3,Money=money,Ships=20};
 var fs=initial with {Fleets=ValueList.Of(donorFleet,to)};
 var fr=dispatcher.Dispatch(fs,new FleetToFleetTransferCommand("north","from","to",0,0,100));
 Console.WriteLine($"fleet-money receiver={money} rejected={fr.IsRejected} purses={fr.State.FleetById("from")!.Money}/{fr.State.FleetById("to")!.Money} treasuryDelta={fr.State.NationById("north")!.Treasury-fs.NationById("north")!.Treasury}");
}
var cf=new FleetState("f","north",4,2,7,30,100,100,100,null,null,"a",null);
var da=army with {X=4,AboardFleetId="f",CoveredTileCode=null};
var ds=initial with{Armies=ValueList.Of(da),Fleets=ValueList.Of(cf),Cities=ValueList.Of(new CityState("port","Port",3,2,"north","north",90,330,0,100,100,0,ValueList<UnitSlot>.Empty))};
var dr=dispatcher.Dispatch(ds,new DisbandArmyCommand("north","a"));
Console.WriteLine($"disband carried rejected={dr.IsRejected} code={dr.Code}");
