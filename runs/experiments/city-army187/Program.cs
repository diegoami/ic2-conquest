using System.Text.Json;
using IC2.Engine.Ai;
using IC2.Engine.Core;
using IC2.Engine.Import;
using IC2.Engine.Model;
using IC2.Engine.Serialization;
using IC2.Engine.Cities.Capture;
var repo=GameDataRepository.Load(Path.Combine(args[0],"data"));var resolved=repo.Resolve("classical-mediterranean");var rules=repo.RulesetById("classical-faithful")!;
string[] types={"light_infantry","heavy_infantry","archers","light_cavalry","heavy_cavalry"};string[] shortTypes={"li","hi","ar","lc","hc"};
GameState Import(string path)=>OriginalSaveImporter.Import(File.ReadAllBytes(path),path,resolved.World,rules,resolved.Scenario,"private-city187","private-city187").Save.State;
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
var state=Import(Path.Combine(args[1],"before.SAV"));using var raw=JsonDocument.Parse(File.ReadAllText(Path.Combine(args[1],"before.json")));int checks=Gate(state,raw.RootElement);
var actor=state.ArmyById("army-4")!;var view=new AiView(state,rules,resolved.World,actor.Nation);bool atWar=state.Nations.Any(n=>view.IsAtWar(actor.Nation,n.Id));
var city=AiArmyTargetTree.ScoreCityTarget(view,actor);var enemy=AiArmyTargetTree.ScoreArmyTarget(view,actor);var supply=AiArmyTargetTree.ScoreResupplyCity(view,actor,atWar);
var decision=AiArmyTargetTree.DecideUnlogged(view,actor,atWar,out var detail);
int? Index(CityState? c)=>c is null?null:resolved.World.Cities.ToList().FindIndex(x=>x.Id==c.Id);
using var old=JsonDocument.Parse(File.ReadAllText(args[2]));var oldCity=old.RootElement.GetProperty("original_city");var oldArmy=old.RootElement.GetProperty("original_enemy");var originalCity=state.CityById(resolved.World.Cities[Int(oldCity,"target")].Id)!;var originalArmy=state.ArmyById("army-"+Int(oldArmy,"target"))!;
var supplied=new AiArmyTargetTree.CityTarget(originalCity,oldCity.GetProperty("score").GetInt64(),Int(oldCity,"distance"));var suppliedArmy=new AiArmyTargetTree.ArmyTarget(originalArmy,oldArmy.GetProperty("score").GetInt64(),Int(oldArmy,"distance"));
var fromOriginal=AiArmyTargetTree.DecideFromScores(rules.Ai,actor,supplied,suppliedArmy,supply);
var cityOnly=AiArmyTargetTree.DecideFromScores(rules.Ai,actor,supplied,enemy,supply);
var log=AiArmyTargetTree.NewDecisionLog();var proposals=new List<AiCandidate>();
try{AiMilitaryPhase.Propose(view,AiPersonalityProfile.For(state.NationById(actor.Nation)!,rules),new SplitMix64Rng(1),Array.Empty<string>(),proposals);}finally{AiArmyTargetTree.ClearDecisionLog();}
var military=log.Single(r=>r.ArmyId==actor.Id);var actorProposals=proposals.Where(p=>p.SubjectId==actor.Id).ToArray();
Write(Path.Combine(args[1],"native-proposals.json"),proposals);Write(Path.Combine(args[1],"native-decision-log.json"),log);
using var originalInputs=JsonDocument.Parse(File.ReadAllText(Path.Combine(args[1],"city-inputs.json")));var rows=new List<object>();int defenseMismatches=0;int filteredOriginalEligible=0;
foreach(var input in originalInputs.RootElement.EnumerateArray())
{
 int i=Int(input,"index");var c=state.CityById(resolved.World.Cities[i].Id)!;var defense=AiArmyTargetTree.CityDefense(c,rules,state);if(defense!=Int(input,"defense"))defenseMismatches++;
 bool reachable=AiArmyTargetTree.IsReachable(view,actor,c.X,c.Y);if(input.GetProperty("eligible").GetBoolean()&&!reachable)filteredOriginalEligible++;
 rows.Add(new{index=i,native_defense=defense,original_defense=Int(input,"defense"),reachable,original_eligible=input.GetProperty("eligible").GetBoolean()});
}
Write(Path.Combine(args[1],"native-city-components.json"),rows);
var result=new{source_pin="0c4944542d32d1e6d2d9982f78fdfcddaabaddea",input_identity_gate_passed=true,checked_fields=checks,original_city_reachable=AiArmyTargetTree.IsReachable(view,actor,originalCity.X,originalCity.Y),native_city=new{target=Index(city.City),city.Score,city.Distance,city.Skipped},native_enemy=new{target=enemy.Army is null?(int?)null:int.Parse(enemy.Army.Id[5..]),enemy.Score,enemy.Distance},native_branch=decision.Selected.ToString(),original_score_fed_branch=fromOriginal.Selected.ToString(),original_city_only_fed_branch=cityOnly.Selected.ToString(),military_phase_branch=military.Kind.ToString(),actor_proposal_kinds=actorProposals.Select(p=>p.Kind).ToArray(),assault_strength=AiArmyTargetTree.AssaultStrength(actor,rules,"archers"),city_defense_comparisons=rows.Count,city_defense_mismatches=defenseMismatches,original_eligible_native_unreachable=filteredOriginalEligible,region_assignment_count=rules.Ai.CityRegionById.Count,scope="same private imported boundary; no whole End turn or production change; diagnostic proposal RNG seed1, no native outcome parity"};
Write(args[3],result);Console.WriteLine("PASS private import/score/branch/proposal measurement; public output contains only scalar facts");
