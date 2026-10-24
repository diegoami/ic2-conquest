using System.Globalization;
using System.Text.Json;
using IC2.Engine.Ai;
using IC2.Engine.Import;
using IC2.Engine.Model;
using IC2.Engine.Persistence;
using IC2.Engine.Presentation;
using IC2.Engine.Serialization;

CultureInfo.CurrentCulture=CultureInfo.InvariantCulture;
var repo=GameDataRepository.Load(Path.Combine(args[1],"data"));
var resolved=repo.Resolve("classical-mediterranean");
var rules=repo.RulesetById("classical-faithful")!;
string[] types={"light_infantry","heavy_infantry","archers","light_cavalry","heavy_cavalry"};
string[] shortTypes={"li","hi","ar","lc","hc"};
GameState Import(string path)=>OriginalSaveImporter.Import(File.ReadAllBytes(path),path,resolved.World,rules,resolved.Scenario,"strategic171","strategic171").Save.State;
void Write(string path,object value)
{
    using var f=new FileStream(path,FileMode.CreateNew);
    JsonSerializer.Serialize(f,value,value.GetType(),new JsonSerializerOptions{WriteIndented=true});
}
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
int? CityIndex(CityState? city)=>city is null?null:resolved.World.Cities.ToList().FindIndex(c=>c.Id==city.Id);
int? ArmyIndex(ArmyState? army)=>army is null?null:int.Parse(army.Id[5..],CultureInfo.InvariantCulture);
if(args[0]=="decisions")
{
    var directory=args[2];var output=args[3];Need(!File.Exists(output),"existing output");
    var rows=new List<object>();
    foreach(var path in Directory.GetFiles(directory,"*.SAV").Order(StringComparer.Ordinal))
    {
        var stem=Path.GetFileNameWithoutExtension(path);var state=Import(path);
        using var expected=JsonDocument.Parse(File.ReadAllText(Path.ChangeExtension(path,"json")));
        int fields=Gate(state,expected.RootElement);
        var manifest=JsonDocument.Parse(File.ReadAllText(Path.Combine(directory,"manifest.json")));
        var spec=manifest.RootElement.EnumerateArray().Single(r=>Int(r,"snapshot")==int.Parse(stem));
        var actor=state.ArmyById($"army-{Int(spec,"army")}")!;
        var view=new AiView(state,rules,resolved.World,actor.Nation);
        bool atWar=state.Nations.Any(n=>n.Id!=actor.Nation&&view.IsAtWar(actor.Nation,n.Id));
        var city=AiArmyTargetTree.ScoreCityTarget(view,actor);
        var enemy=AiArmyTargetTree.ScoreArmyTarget(view,actor);
        var supply=AiArmyTargetTree.ScoreResupplyCity(view,actor,atWar);
        var decision=AiArmyTargetTree.DecideUnlogged(view,actor,atWar,out var detail);
        rows.Add(new{snapshot=int.Parse(stem),army=Int(spec,"army"),nation=actor.Nation,gate=true,checkedFields=fields,
            city=new{target=CityIndex(city.City),score=city.Score,distance=city.Distance,city.Skipped},
            enemy=new{target=ArmyIndex(enemy.Army),score=enemy.Score,distance=enemy.Distance,enemy.Skipped},
            resupply=new{target=CityIndex(supply.City),score=supply.Score,distance=supply.Distance},
            decision=new{kind=(int)decision.Selected,after=(int)decision.After,resolvedResupply=CityIndex(decision.Resupply?.City)},
            origin=new{actor.X,actor.Y,actor.Moves,actor.Morale,actor.Money,actor.SupplyTons,actor.TotalTroops}});
        manifest.Dispose();
    }
    using(var writer=new StreamWriter(new FileStream(output,FileMode.CreateNew)))
        foreach(var row in rows)writer.WriteLine(JsonSerializer.Serialize(row));
    Console.WriteLine(JsonSerializer.Serialize(new{complete=true,decisions=rows.Count,allImportGatesPassed=true}));
}
else if(args[0]=="end")
{
    var state=Import(args[2]) with{RandomSeed=1UL};var output=args[3];Need(!Directory.Exists(output),"existing output");Directory.CreateDirectory(output);
    var saved=new SaveGame(GameDataSchema.CurrentVersion,"strategic171","strategic171",state.ScenarioId,state.WorldId,state.RulesetId,state);
    var session=new GameSession(resolved.World,rules,resolved.Scenario,saved){HumanBattles=HumanBattleMode.Tactical};
    bool unobserved=args.Length>4&&args[4]=="unobserved";
    if(unobserved)session.DisableStrategicObservations();
    var decisions=unobserved?new List<AiArmyTargetTree.DecisionRecord>():AiArmyTargetTree.NewDecisionLog();
    try
    {
        Write(Path.Combine(output,"before.json"),session.State);
        var result=session.Submit("end");
        Write(Path.Combine(output,"after.json"),session.State);
        Write(Path.Combine(output,"decisions.json"),decisions);
        Write(Path.Combine(output,"routes.json"),session.LastStrategicTimeline.Steps.Select(s=>new{s.StepId,s.Identity,s.Kind,s.Before.ActiveNationId,s.Routes}).ToArray());
        Write(Path.Combine(output,"output.json"),new{result.Lines,result.ShouldExit,result.Battles,battleOpen=session.OpenTacticalBattle!=null});
        Console.WriteLine(JsonSerializer.Serialize(new{complete=true,decisions=decisions.Count,steps=session.LastStrategicTimeline.Steps.Count,battleOpen=session.OpenTacticalBattle!=null}));
    }
    finally{AiArmyTargetTree.ClearDecisionLog();}
}
else throw new ArgumentException("Unknown mode");
