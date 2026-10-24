using System.Text.Json;
using IC2.Engine.Ai;
using IC2.Engine.Core;
using IC2.Engine.Diplomacy;
using IC2.Engine.Import;
using IC2.Engine.Model;
using IC2.Engine.Serialization;
var repo=GameDataRepository.Load(Path.Combine(args[0],"data"));var resolved=repo.Resolve("classical-mediterranean");var rules=repo.RulesetById("classical-faithful")!;
string[] types={"light_infantry","heavy_infantry","archers","light_cavalry","heavy_cavalry"};string[] shortTypes={"li","hi","ar","lc","hc"};
GameState Import(string path)=>OriginalSaveImporter.Import(File.ReadAllBytes(path),path,resolved.World,rules,resolved.Scenario,"tracks","tracks").Save.State;
void Write(string path,object value){using var f=new FileStream(path,FileMode.CreateNew);JsonSerializer.Serialize(f,value,value.GetType(),new JsonSerializerOptions{WriteIndented=true});}
int Int(JsonElement e,string n)=>e.GetProperty(n).GetInt32();
void Need(bool condition,string message){if(!condition)throw new InvalidDataException(message);}
int Gate(GameState state,JsonElement original)
{
    int checkedFields=0;
    void Equal(bool condition,string name){Need(condition,name);checkedFields++;}
    foreach(var a in original.GetProperty("armies").EnumerateArray())
    {
        if(Int(a,"owner")<0||Int(a,"troops")<=0)continue;
        var id=Int(a,"id");var actual=state.ArmyById($"army-{id}")??throw new InvalidDataException("missing raw army lineage "+id);
        Equal(actual.Nation==resolved.World.Nations[Int(a,"owner")].Id,"army owner");
        Equal(actual.X==Int(a,"x")&&actual.Y==Int(a,"y"),"army position");
        Equal(actual.Moves==Int(a,"moves")&&actual.Morale==Int(a,"morale"),"army moves/morale");
        Equal(actual.Money==Int(a,"money")&&actual.SupplyTons==Int(a,"supplies"),"army resources");
        Equal(actual.CoveredTileCode== (Int(a,"cell")==-1?null:Int(a,"cell")),"covered cell");
        var units=a.GetProperty("units").EnumerateArray().ToArray();Equal(actual.Units.Count==units.Length,"unit count");
        for(int i=0;i<units.Length;i++)
        {
            var u=units[i];var au=actual.Units[i];
            Equal(au.UnitTypeId==types[Array.IndexOf(shortTypes,u.GetProperty("type").GetString())],"unit order/type");
            Equal(au.Troops==Int(u,"troops")&&au.Quality==Int(u,"quality")&&au.MercenaryLabel==Int(u,"merc"),"unit troop/quality/label");
            Equal(au.Name==u.GetProperty("name").GetString(),"unit name");
        }
    }
    foreach(var c in original.GetProperty("cities").EnumerateArray())
    {
        var actual=state.CityById(resolved.World.Cities[Int(c,"id")].Id)!;
        Equal(actual.X==Int(c,"x")&&actual.Y==Int(c,"y"),"city position");
        Equal(actual.Owner==resolved.World.Nations[Int(c,"owner")].Id&&actual.Allegiance==resolved.World.Nations[Int(c,"allegiance")].Id,"city owner/allegiance");
        Equal(actual.SupplyTons==Int(c,"supplies")&&actual.Loyalty==Int(c,"loyalty"),"city supply/loyalty");
        Equal(actual.FortificationCode==Int(c,"fort")+100*Int(c,"fort_pending"),"fortification");
        Equal(actual.PopulationThousands==Int(c,"pop")&&actual.MaxPopulationThousands==Int(c,"max_pop")&&actual.Tribute==Int(c,"tribute"),"city population/tribute");
    }
    foreach(var f in original.GetProperty("fleets").EnumerateArray())
    {
        if(Int(f,"owner")<0||Int(f,"ships")<=0)continue;
        var actual=state.FleetById($"fleet-{Int(f,"id")}")??throw new InvalidDataException("missing fleet lineage");
        Equal(actual.Nation==resolved.World.Nations[Int(f,"owner")].Id,"fleet owner");
        Equal(actual.X==Int(f,"x")&&actual.Y==Int(f,"y"),"fleet position");
        Equal(actual.Ships==Int(f,"ships")&&actual.Moves==Int(f,"moves"),"fleet ships/moves");
        Equal(actual.Money==Int(f,"money")&&actual.SupplyTons==Int(f,"supplies"),"fleet resources");
        var building=f.GetProperty("building").GetBoolean();Equal(actual.IsUnderConstruction==building,"fleet construction");
        if(building)Equal(actual.ConstructionTicksRemaining==Int(f,"countdown"),"construction countdown");
        else Equal(actual.ConditionPercent==Int(f,"condition"),"fleet condition");
        var carrier=Int(f,"army");Equal(actual.CarriedArmyId==(carrier<0?null:$"army-{carrier}"),"fleet cargo");
    }
    var nations=original.GetProperty("nations").EnumerateArray().ToArray();
    for(int i=0;i<nations.Length;i++)
    {
        var n=nations[i];var actual=state.NationById(resolved.World.Nations[i].Id)!;
        var cap=Int(n,"capital");Equal(actual.CapitalCityId==(cap<0?null:resolved.World.Cities[cap].Id),"capital");
        Equal((actual.Control==SeatControl.Human)==n.GetProperty("human").GetBoolean(),"controller");
        Equal(actual.Treasury==Int(n,"treasury")&&actual.Unity==Int(n,"unity")&&actual.Wealth==Int(n,"wealth"),"nation resources");
        Equal(actual.TaxBase==Int(n,"tax_base")&&actual.TaxRatePercent==Int(n,"tax")&&actual.MobilizedPercent==Int(n,"mobilization"),"nation tax/mobilization");
        var recruits=n.GetProperty("recruit_slots").EnumerateArray().ToArray();Equal(actual.RecruitmentSlots.Count==recruits.Length,"recruit count");
        for(int k=0;k<recruits.Length;k++)
        {
            var r=recruits[k];var ar=actual.RecruitmentSlots[k];
            Equal(ar.TargetCityId==resolved.World.Cities[Int(r,"city")].Id,"recruit city/order");
            Equal(ar.UnitTypeId==types[Array.IndexOf(shortTypes,r.GetProperty("type").GetString())]&&ar.Troops==Int(r,"troops")&&ar.StateCode==Int(r,"state"),"recruit type/troops/state");
        }
        for(int j=0;j<nations.Length;j++)if(i!=j)
            Equal(state.Relations.Get(actual.Id,resolved.World.Nations[j].Id)==n.GetProperty("relations").GetProperty(nations[j].GetProperty("name").GetString()!).GetInt32(),"relation");
    }
    Equal(state.ActiveNationId==resolved.World.Nations[Int(original,"current_nation")].Id,"active seat");
    return checkedFields;
}
object EconomyState(GameState s,string n)
{
 var a=s.NationById(n)!;
 string[] Sorted(IEnumerable<object> values)=>values.Select(v=>JsonSerializer.Serialize(v,v.GetType())).Order(StringComparer.Ordinal).ToArray();
 return new{a.Treasury,a.MobilizedPercent,a.TaxRatePercent,a.Unity,a.Wealth,
 queue=a.RecruitmentSlots.Select(q=>new{q.TargetCityId,q.UnitTypeId,q.Troops,q.StateCode}).ToArray(),
 armies=Sorted(s.Armies.Where(x=>x.Nation==n).Select(x=>(object)new{x.X,x.Y,x.Moves,x.Morale,x.Money,x.SupplyTons,x.IsEmbarked,units=x.Units.Select(u=>new{u.UnitTypeId,u.Troops,u.Quality,u.MercenaryLabel}).ToArray()})),
 fleets=Sorted(s.Fleets.Where(x=>x.Nation==n).Select(x=>(object)new{x.X,x.Y,x.Moves,x.Ships,x.Money,x.SupplyTons,x.ConditionPercent,x.ConstructionTicksRemaining,cargo=x.CarriedArmyId is not null}))};
}
var ledger=JsonDocument.Parse(File.ReadAllText(args[2])).RootElement.EnumerateArray().ToDictionary(r=>r.GetProperty("index").GetInt32());
Directory.CreateDirectory(args[3]);var rows=new List<object>();
foreach(var folder in Directory.GetDirectories(args[1]).Order(StringComparer.Ordinal))
{
 var name=Path.GetFileName(folder);var original=ledger[int.Parse(name.Split('-')[0])];var phase=original.GetProperty("phase").GetString()!;if(phase=="fleet")continue;
 var state=Import(Path.Combine(folder,"before.SAV"));using var raw=JsonDocument.Parse(File.ReadAllText(Path.Combine(folder,"before.json")));int checks=Gate(state,raw.RootElement);
 var n=resolved.World.Nations[original.GetProperty("nation").GetInt32()].Id;
 if(phase=="economy")
 {
  var expected=Import(Path.Combine(folder,"expected.SAV"));var rng=new RecordedRng(original.GetProperty("draws"));var log=new List<string>();var dispatch=new CommandDispatcher(SystemRegistry.FromEngineAssembly(),rules,resolved.World,NullEventSink.Instance);
  try
  {
   var result=AiFaithfulEconomy.Run(state,rules,resolved.World,dispatch,NullEventSink.Instance,rng,n,log);
   var actual=EconomyState(result.State,n);var want=EconomyState(expected,n);
   var row=new{caseName=name,phase,nation=n,input_checks=checks,complete=true,result.Issued,result.Rejected,draws_consumed=rng.Used,original_draws=rng.Count,own=AiFaithfulEconomy.Own(state,rules,n),threat=AiFaithfulEconomy.Threat(state,rules,n),original_power=original.GetProperty("power"),all_draws_consumed=rng.Used==rng.Count,economy_projection_equal=JsonSerializer.Serialize(actual)==JsonSerializer.Serialize(want),actual,expected=want,log};
   Write(Path.Combine(args[3],name+"-after.json"),result.State);Write(Path.Combine(args[3],name+"-result.json"),row);rows.Add(row);
  }
  catch(Exception e){var row=new{caseName=name,phase,nation=n,input_checks=checks,complete=false,error=e.ToString(),draws_consumed=rng.Used,original_draws=rng.Count,log};Write(Path.Combine(args[3],name+"-result.json"),row);rows.Add(row);}
 }
 else
 {
  var row=new{caseName=name,phase,nation=n,input_checks=checks,original_facts=original.GetProperty("original_facts"),busy=AiOwnDiplomacyRule.IsBusy(state,rules,n),power=AiOwnDiplomacyRule.Power(state.NationById(n)!,rules),war_target=AiOwnDiplomacyRule.BestWarTarget(state,rules,resolved.World,n),alliance_partner=AiOwnDiplomacyRule.FindAlliancePartner(state,rules,resolved.World,n),trade_candidates=AiOwnDiplomacyRule.EligibleTradePartners(state,rules,n),swap=AiOwnDiplomacyRule.FindTradeSwap(state,rules,n)};
  Write(Path.Combine(args[3],name+"-result.json"),row);rows.Add(row);
 }
}
Write(args[4],rows);Console.WriteLine($"Preserved {rows.Count} native phase comparisons; recorded RNG fails closed on missing/bound mismatch");
sealed class RecordedRng:IRng
{
 readonly (int bound,int value)[] rows;public int Used{get;private set;}public int Count=>rows.Length;public ulong Seed=>1;public ulong State=>(ulong)Used;
 public RecordedRng(JsonElement e){rows=e.EnumerateArray().Select(r=>(r.GetProperty("bound").GetInt32(),r.GetProperty("result").GetInt32())).ToArray();}
 public int NextInt(int b){if(Used>=rows.Length||rows[Used].bound!=b)throw new InvalidDataException($"Original draw mismatch at {Used}: native bound {b}, original {(Used<rows.Length?rows[Used].bound:-1)}");return rows[Used++].value;}
 public int NextInt(int a,int b)=>a+NextInt(b-a);public bool NextChance(int n,int d)=>NextInt(d)<n;
 public ulong NextUInt64()=>throw new InvalidDataException("Unmatched raw draw");public IRng ForStream(string name)=>this;
}
