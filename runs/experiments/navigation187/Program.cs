using System.Text.Json;
using IC2.Engine.Core;
using IC2.Engine.Import;
using IC2.Engine.Model;
using IC2.Engine.Serialization;
using IC2.Engine.Movement.Commands;
var repo=GameDataRepository.Load(Path.Combine(args[0],"data"));var ctx=repo.Resolve("classical-mediterranean");var rules=repo.RulesetById("classical-faithful")!;
var path=args[1];var state=OriginalSaveImporter.Import(File.ReadAllBytes(path),path,ctx.World,rules,ctx.Scenario,"private187","private187").Save.State;
using var source=JsonDocument.Parse(File.ReadAllText(args[2]));var raw=source.RootElement;var a=state.ArmyById("army-4")!;
if(a.X!=219||a.Y!=93||a.Moves!=7||a.TotalTroops!=78857)throw new Exception("private actor gate");
var army=raw.GetProperty("armies")[4];string[] types={"light_infantry","heavy_infantry","archers","light_cavalry","heavy_cavalry"};string[] abbreviations={"li","hi","ar","lc","hc"};
var units=army.GetProperty("units").EnumerateArray().ToArray();if(a.Units.Count!=units.Length)throw new Exception("private unit count");
for(int i=0;i<units.Length;i++)if(a.Units[i].Troops!=units[i].GetProperty("troops").GetInt32()||a.Units[i].Quality!=units[i].GetProperty("quality").GetInt32()||a.Units[i].UnitTypeId!=types[Array.IndexOf(abbreviations,units[i].GetProperty("type").GetString())])throw new Exception("private unit gate");
var map=raw.GetProperty("map").EnumerateArray().Select(x=>x.GetInt32()).ToArray();var terrain=ctx.World.Terrain.Decode(320,140);int mismatches=0;
var occupied=new HashSet<(int,int)>();foreach(var c in state.Cities)occupied.Add((c.X,c.Y));foreach(var x in state.Armies)if(!x.IsEmbarked&&x.CoveredTileCode is not null)occupied.Add((x.X,x.Y));foreach(var f in state.Fleets)if(!f.IsUnderConstruction)occupied.Add((f.X,f.Y));
for(int x=0;x<320;x++)for(int y=0;y<140;y++)
{
 int old=map[x*140+y],actual=terrain[y*320+x];if(old>=2&&old<=11&&old!=actual)mismatches++;
 if((old<2||old>11)!=(ctx.World.TileTypeByCode(actual)?.PassableByArmies!=true||occupied.Contains((x,y))))mismatches++;
}
if(mismatches!=0)throw new Exception("private terrain/occupancy gate");
var nations=raw.GetProperty("nations").EnumerateArray().ToArray();for(int n=0;n<16;n++)for(int j=0;j<16;j++)if(n!=j&&state.Relations.Get(ctx.World.Nations[n].Id,ctx.World.Nations[j].Id)!=nations[n].GetProperty("relations").GetProperty(nations[j].GetProperty("name").GetString()!).GetInt32())throw new Exception("private relation gate");
var result=new CommandDispatcher(SystemRegistry.FromEngineAssembly(),rules,ctx.World,NullEventSink.Instance).Dispatch(state,new MoveArmyCommand(a.Nation,a.Id,189,104));var after=result.State.ArmyById(a.Id)!;
if(!result.IsAccepted||after.X!=212||after.Y!=96||after.Moves!=0)throw new Exception("private conditioned movement result");
using(var f=new FileStream(args[3],FileMode.CreateNew))JsonSerializer.Serialize(f,new{owner_fields_published=false,actor_units_relations_gated=true,terrain_occupancy_mismatches=mismatches,supplied_waypoint=new[]{189,104},endpoint=new[]{after.X,after.Y},after.Moves,
 scope="conditioned low-level movement only; original model geodata separately verified; no native navigation/whole-turn equivalence claim"},new JsonSerializerOptions{WriteIndented=true});
Console.WriteLine("PASS private conditioned current-native walker; units/relations/map inputs match; no private hashes/full state emitted");
