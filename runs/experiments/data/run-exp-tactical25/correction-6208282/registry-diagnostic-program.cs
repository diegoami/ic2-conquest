using System.Collections;
using System.Reflection;
using System.Text.Json;
using IC2.Engine.Tests.Battle.Tactical.GoldenMaster;

// Diagnostic only: invokes the existing replay and comparers, without altering any expectations.
var assembly = typeof(SeriesReplayTests).Assembly;
const string prefix = "IC2.Engine.Tests.Battle.Tactical.GoldenMaster.";
Type T(string name) => assembly.GetType(prefix + name, true)!;
object? S(string type, string method, params object?[] args) => T(type).GetMethod(method, BindingFlags.Static | BindingFlags.Public | BindingFlags.NonPublic)!.Invoke(null, args);
object? G(object obj, string name) => obj.GetType().GetProperty(name)!.GetValue(obj);
object? M(object obj, string method, params object?[] args) => obj.GetType().GetMethod(method)!.Invoke(obj,args);
object Spec(string name) => name.EndsWith("_r5_hook", StringComparison.Ordinal) ? G(S("GoldenData","Trial",name)!,"Series")! : S("GoldenData","Named",name)!;
var replayCache = new Dictionary<string,object>();
object Replay(string name, bool blocks)
{
 var key=name+":"+blocks;
 if(replayCache.TryGetValue(key,out var old))return old;
 var spec=Spec(name);
 var result=S("GoldenReplay","Run",spec,blocks,null)!;
 replayCache.Add(key,result);return result;
}
string? Blocks(string name, bool complete)
{
 var r=Replay(name,true);
 return (bool)G(r,complete?"Passed":"BlocksPassed")! ? null : (string)M(r,"Describe",Spec(name))!;
}
string? Draws(string name)
{
 var trial=S("GoldenData","Trial",name)!;
 var log=S("HookLog","Load",G(trial,"HookLog"))!;
 var r=Replay(name,false);
 if(G(r,"Structural") is string error)throw new Exception(error);
 var diff=(string?)S("DrawComparison","First",G(G(r,"Draws")!,"Draws"),log);
 return diff is null?null:name+": "+diff;
}
string? Peace(string name)
{
 var trial=S("GoldenData","Trial",name)!;
 var log=S("HookLog","Load",G(trial,"HookLog"))!;
 var original=G(log,"PeaceDraw");
 var r=Replay(name,false);
 var conclusion=G(r,"Conclusion")??throw new Exception("No conclusion: "+name);
 var result=G(conclusion,"Result")!;
 var drawn=(bool)G(result,"PeaceDrawn")!;
 var offered=(bool)G(result,"PeaceOffered")!;
 if(drawn!=(original is not null))return $"{name}: the log {(original is null?"has no":"has a")} record at the peace site, the port {(drawn?"drew":"did not draw")} it";
 if(original is null)return offered?$"{name}: no draw, yet the treaty was offered":null;
 var all=(IList)G(G(r,"Draws")!,"Draws")!;var last=all[all.Count-1]!;
 var bound=(int)G(last,"Bound")!;var value=(int)G(last,"Value")!;var expected=(uint)G(original,"Result")!;
 if(bound!=5||unchecked((uint)value)!=expected)return $"{name}: the port's peace draw is Random({bound}) = {value}, the log's is Random(5) = {expected}";
 if(offered!=(expected<2))return $"{name}: peace offered: port {offered}, original {expected<2}";
 return null;
}
var source="tests/IC2.Engine.Tests/Battle/Tactical/GoldenMaster/KnownFailures.json";
var entries=JsonDocument.Parse(File.ReadAllText(source)).RootElement;
var resumeSpec=S("SeriesCatalogue","Resume05")!;
var startName=G(resumeSpec,"Start")!;
var resumeBlock=S("BattleFixtures","Block",startName)!;
var imported=S("BattleFixtures","Import",startName)!;
var resumeGame=G(G(imported,"Save")!,"State")!;
var original=typeof(IC2.Engine.Import.OriginalBattleBlockImport).GetMethod("Import")!.Invoke(null,new object[]{resumeBlock,resumeGame,new[]{false,false}})!;
var roundTrip=(Delegate)S("ResumeTests","ThroughACloneSave",resumeSpec)!;
var clone=roundTrip.DynamicInvoke(resumeBlock,resumeGame)!;
if(!original.Equals(clone))throw new Exception("Clone roundtrip input differs from plain resume; cannot share diagnosis.");
Console.WriteLine("Clone roundtrip initial state equals explicit fresh-process import.");
var output=new List<object>();
foreach(var row in entries.EnumerateArray())
{
 var id=row.GetProperty("Case").GetString()!;var parts=id.Split(':',2);var method=parts[0];var name=parts.Length==2?parts[1]:"";
 string? actual;
 switch(method)
 {
  case "The_hooked_series_replays_exactly":case "The_recorded_series_replays_exactly":case "The_crafted_battle_replays_from_its_slots":actual=Blocks(name,true);break;
  case "Stale_or_doubled_cells_are_not_repaired":actual=Blocks(name,false);break;
  case "The_port_draws_what_the_original_drew":actual=Draws(name);break;
  case "The_port_draws_the_peace_roll_when_the_original_did":actual=Peace(name);break;
  case "The_resume_gives_the_ten_files_the_original_wrote":
  case "No_resumed_file_equals_the_uninterrupted_tail":
  case "The_resume_through_a_clone_save_gives_the_same_ten_files":
    actual=Blocks("resume05_gate2_a_r1",false);break;
  default:continue; // C2/c4's complete pass is verified through its actual test body.
 }
 output.Add(new { Case=id,Old=row.GetProperty("FirstDifference").GetString(),Current=actual,Issue=row.GetProperty("Issue").GetInt32() });
}
using(var file=new FileStream(args[0],FileMode.CreateNew))JsonSerializer.Serialize(file,output,new JsonSerializerOptions{WriteIndented=true});
Console.WriteLine($"Wrote {output.Count} raw comparisons; {replayCache.Count} production replay calls.");
