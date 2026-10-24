using System.Reflection;
using System.Text.Json;
using System.Security.Cryptography;
using IC2.Engine.Ai;
using IC2.Engine.Import;
using IC2.Engine.Model;
using IC2.Engine.Serialization;
using IC2.Engine.Movement.Commands;

var root=args[0];var source=args[1];var output=args[2];
if(File.Exists(output))throw new IOException("Existing output");
var repo=GameDataRepository.Load(Path.Combine(source,"data"));var resolved=repo.Resolve("classical-mediterranean");var rules=repo.RulesetById("classical-faithful")!;
var method=typeof(AiMilitaryPhase).GetMethod("ProposeFleetMarches",BindingFlags.Static|BindingFlags.NonPublic)!;
var rows=new List<object>();int checkedFields=0;
void Need(bool condition,string message){if(!condition)throw new InvalidDataException(message);checkedFields++;}
foreach(var folder in Directory.GetDirectories(root).Order(StringComparer.Ordinal))
{
 var raw=File.ReadAllBytes(Path.Combine(folder,"pre-move.SAV"));
 var state=OriginalSaveImporter.Import(raw,"fleet174",resolved.World,rules,resolved.Scenario,"fleet174","fleet174").Save.State;
 using var expected=JsonDocument.Parse(File.ReadAllText(Path.Combine(folder,"expected.json")));
 var original=expected.RootElement;var count=original.GetProperty("fleets").GetArrayLength();Need(state.Fleets.Count==count,"fleet count");
 foreach(var f in original.GetProperty("fleets").EnumerateArray())
 {
  int I(string n)=>f.GetProperty(n).GetInt32();var model=state.FleetById($"fleet-{I("id")}")!;Need(model is not null,"fleet lineage");
  Need(model!.Nation==resolved.World.Nations[I("owner")].Id,"fleet owner");
  Need(model.X==I("x")&&model.Y==I("y"),"fleet location");
  Need(model.Moves==I("moves")&&model.Ships==I("ships"),"fleet moves/ships");
  Need(model.SupplyTons==I("supplies")&&model.Money==I("money"),"fleet resources");
  Need(model.IsUnderConstruction==f.GetProperty("building").GetBoolean(),"construction");
  if(!model.IsUnderConstruction)Need(model.ConditionPercent==I("condition"),"condition");
 }
 var nations=original.GetProperty("nations").EnumerateArray().ToArray();
 for(int n=0;n<16;n++)for(int j=0;j<16;j++)if(n!=j)
  Need(state.Relations.Get(resolved.World.Nations[n].Id,resolved.World.Nations[j].Id)==nations[n].GetProperty("relations").GetProperty(nations[j].GetProperty("name").GetString()!).GetInt32(),"relation");
 var actor=state.FleetById("fleet-0")!;var proposals=new List<AiCandidate>();
 if(!actor.IsUnderConstruction&&actor.Moves>0)method.Invoke(null,new object[]{new AiView(state,rules,resolved.World,actor.Nation),actor,proposals});
 var fleetOffset=100958+BitConverter.ToInt16(raw,100956)*656+2;
 rows.Add(new{caseName=Path.GetFileName(folder),gate=true,
  originalStoredDestination=new[]{BitConverter.ToInt16(raw,fleetOffset+4),BitConverter.ToInt16(raw,fleetOffset+6)},
  nativeStateSha256=Convert.ToHexString(SHA256.HashData(JsonSerializer.SerializeToUtf8Bytes(state))).ToLowerInvariant(),
  proposals=proposals.Select(p=>new{p.Kind,p.Score,p.Rationale,commands=p.Commands.Select(c=>new{kind=c.Kind,body=JsonSerializer.SerializeToElement(c,c.GetType())}).ToArray()}).ToArray(),
  sourcePolicy="sailAtFleetBaseScore and distancePenaltyPerTile explicitly marked designed; proposals are not accepted actions"});
}
using(var f=new FileStream(output,FileMode.CreateNew))JsonSerializer.Serialize(f,new{cases=rows.Count,checkedFields,rows},new JsonSerializerOptions{WriteIndented=true});
Console.WriteLine(JsonSerializer.Serialize(new{cases=rows.Count,checkedFields}));
