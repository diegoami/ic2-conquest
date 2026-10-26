using System.Text.Json;
using System.Text.Json.Nodes;
using IC2.Engine.Model;
using IC2.Engine.Serialization;
using IC2.Engine.Import;
using IC2.Engine.Core;
using IC2.Engine.Naval.Commands;
var repo=GameDataRepository.Load(Path.Combine(args[0],"data"));var resolved=repo.Resolve("classical-mediterranean");var rules=repo.RulesetById("classical-faithful")!;
var owners=resolved.World.Nations.Select((n,i)=>(n.Id,i)).ToDictionary(x=>x.Id,x=>x.i);
string[] types={"light_infantry","heavy_infantry","archers","light_cavalry","heavy_cavalry"};
object?[] Army(ArmyState a)=>new object?[]{a.Nation,a.X,a.Y,a.Moves,a.Morale,a.Money,a.SupplyTons,a.IsEmbarked,(object?)a.CoveredTileCode!,a.Units.Select(u=>new object[]{u.MercenaryLabel,Array.IndexOf(types,u.UnitTypeId),u.Troops,u.Quality,u.Name}).ToArray()};
object Shape(GameState s)=>new{
 armies=s.Armies.Select(Army).OrderBy(a=>JsonSerializer.Serialize(a),StringComparer.Ordinal).ToArray(),
 fleets=s.Fleets.Where(f=>!f.IsUnderConstruction).Select(f=>new object?[]{f.Nation,f.X,f.Y,f.Moves,f.Ships,f.ConditionPercent,f.Money,f.SupplyTons,f.CarriedArmyId is{}id&&s.ArmyById(id)is{}a?Army(a):null}).ToArray(),
 cities=s.Cities.Select(c=>new object[]{c.X,c.Y,owners[c.Owner],owners[c.Allegiance],c.Loyalty,c.SupplyTons,c.FortificationCode,c.PopulationThousands,c.MaxPopulationThousands,c.Tribute,c.Name}).ToArray(),
 nations=s.Nations.Select(n=>new object[]{n.Treasury,n.Wealth,n.Unity,n.MobilizedPercent,n.Control==SeatControl.Human}).ToArray()};
void Write(string path,object value){using var f=new FileStream(path,FileMode.CreateNew);JsonSerializer.Serialize(f,value,value.GetType(),new JsonSerializerOptions{WriteIndented=true});}
bool Equal(object a,JsonNode b)=>JsonNode.DeepEquals(JsonSerializer.SerializeToNode(a),b);
var specs=JsonNode.Parse(File.ReadAllText(args[2]))!.AsArray();Directory.CreateDirectory(args[3]);var results=new List<object>();
foreach(var node in specs){var spec=node!.AsObject();var id=spec["id"]!.GetValue<string>();
 if(spec.ContainsKey("helper_no_land")){results.Add(new{id,status="not compared: helper-only no-land entry"});continue;}
 var folder=Path.Combine(args[1],id);var input=File.ReadAllBytes(Path.Combine(folder,"before.SAV"));
 try{
 var state=OriginalSaveImporter.Import(input,id,resolved.World,rules,resolved.Scenario,"overflow","overflow").Save.State;
 var before=JsonNode.Parse(File.ReadAllText(Path.Combine(folder,"before-shape-v2.json")))!;if(!Equal(Shape(state),before))throw new Exception("complete input projection differs");
 var terrain=resolved.World.Terrain.Decode(resolved.World.Width,resolved.World.Height);var terrainChecks=0;
 foreach(var a in state.Armies.Where(a=>!a.IsEmbarked)){if(terrain[a.Y*resolved.World.Width+a.X]!=a.CoveredTileCode)throw new Exception("army covered terrain/world differs");terrainChecks++;}
 foreach(var f in state.Fleets.Where(f=>!f.IsUnderConstruction)){if(terrain[f.Y*resolved.World.Width+f.X]>1)throw new Exception("fleet is not on original world sea");terrainChecks++;}
 var d=new CommandDispatcher(SystemRegistry.FromEngineAssembly(),rules,resolved.World,NullEventSink.Instance);
 var aa=state.ArmyById("army-0")!;var ff=state.FleetById("fleet-0")!;
 var preCell=IC2.Engine.Armies.SplitPlacement.ArmyCellFor(state,resolved.World,aa);
 var boarded=aa with{X=ff.X,Y=ff.Y,Moves=0,CoveredTileCode=null,AboardFleetId=ff.Id};
 var diagnosticState=state with{Armies=ValueList.From(state.Armies.Select(a=>a.Id==aa.Id?boarded:a)),Fleets=ValueList.From(state.Fleets.Select(f=>f.Id==ff.Id?f with{Moves=0,CarriedArmyId=aa.Id}:f))};
 var postCell=IC2.Engine.Armies.SplitPlacement.ArmyCellFor(diagnosticState,resolved.World,boarded);
 var result=d.Dispatch(state,new EmbarkArmyCommand("carthage","army-0","fleet-0"));
 var expected=JsonNode.Parse(File.ReadAllText(Path.Combine(folder,"expected-shape-v2.json")))!;var got=JsonSerializer.SerializeToNode(Shape(result.State))!;
 var mismatch=new List<string>();foreach(var key in new[]{"armies","fleets","cities","nations"})if(!JsonNode.DeepEquals(got[key],expected[key]))mismatch.Add(key);
 var changed=!Equal(Shape(result.State),before);var natives= result.State.Armies.Where(a=>a.Nation=="carthage").ToArray();
 var row=new{id,status=spec.ContainsKey("not_gui_equivalent")?"non-equivalent helper/human command boundary":"conditional original mechanics vs native command",complete_input_projection_equal=true,placement_query_scope="diagnostic only: unchanged production helper, preboard versus staged postboard context",pre_placement=preCell is{}pp?new[]{pp.X,pp.Y}:null,post_placement=postCell is{}bp?new[]{bp.X,bp.Y}:null,terrain_checks=terrainChecks,accepted=result.IsAccepted,rejection=result.Code?.ToString(),state_changed=changed,full_state_unchanged=JsonSerializer.Serialize(state)==JsonSerializer.Serialize(result.State),projection_equal=mismatch.Count==0,mismatch_sections=mismatch,troops=natives.Sum(a=>a.TotalTroops),armies=natives.Where(a=>a.Id=="army-0"||a.Id=="army-1"||a.Id.StartsWith("army-0-overflow",StringComparison.Ordinal)).Select(a=>new{a.Id,a.X,a.Y,a.Moves,a.TotalTroops,a.Money,a.SupplyTons,a.AboardFleetId}).ToArray()};
 Write(Path.Combine(args[3],id+"-state.json"),result.State);Write(Path.Combine(args[3],id+"-projection.json"),got);results.Add(row);Write(Path.Combine(Path.GetDirectoryName(args[4])!,Path.GetFileNameWithoutExtension(args[4])+"_"+id+".json"),row);Console.WriteLine($"{id} accepted={result.IsAccepted} rejection={result.Code} mismatches={string.Join(',',mismatch)}");
 }catch(Exception e){Write(Path.Combine(args[3],id+"-failure.json"),new{type=e.GetType().Name,message=e.Message});throw;}
}
Write(args[4],results);
