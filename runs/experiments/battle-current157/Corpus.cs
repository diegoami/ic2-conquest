// Unmodified upstream GoldenReplay/DrawComparison; no KnownFailures acceptance.
using System.Collections;
using System.Reflection;
using System.Text.Json;
using IC2.Engine.Tests.Battle.Tactical.GoldenMaster;

const BindingFlags F=BindingFlags.Static|BindingFlags.Instance|BindingFlags.Public|BindingFlags.NonPublic;
var assembly=typeof(SeriesReplayTests).Assembly;
Type T(string n)=>assembly.GetType("IC2.Engine.Tests.Battle.Tactical.GoldenMaster."+n,true)!;
object? Call(string t,string m,params object?[] a)=>T(t).GetMethods(F).Single(x=>x.Name==m&&x.GetParameters().Length==a.Length).Invoke(null,a);
object Get(object o,string p)=>o.GetType().GetProperty(p,F)!.GetValue(o)!;
if(args.Length>2&&args[2]=="--fixed-only")
{
    var names=(string[])T("GoldenData").GetField("FixedSeries",F)!.GetValue(null)!;
    var fixedRows=new List<object>();int bad=0;
    using var fixedLog=new StreamWriter(new FileStream(args[0],FileMode.CreateNew));
    foreach(var name in names)
    {
        try
        {
            var spec=Call("GoldenData","Named",name)!;var outcome=Call("GoldenReplay","Run",spec,true,null)!;
            var passed=(bool)Get(outcome,"Passed");if(!passed)bad++;
            var row=new{trial=name,passed,description=outcome.GetType().GetMethod("Describe",F)!.Invoke(outcome,[spec]),filesMatched=Get(outcome,"FilesMatched")};
            fixedRows.Add(row);fixedLog.WriteLine(JsonSerializer.Serialize(row));fixedLog.Flush();Console.WriteLine(name+" "+passed);
        }
        catch(Exception e){bad++;var row=new{trial=name,passed=false,error=e.GetBaseException().ToString()};fixedRows.Add(row);fixedLog.WriteLine(JsonSerializer.Serialize(row));fixedLog.Flush();}
    }
    using(var file=new FileStream(args[1],FileMode.CreateNew))JsonSerializer.Serialize(file,new{fixedCases=names.Length,passed=names.Length-bad,failed=bad,rows=fixedRows,scope="Unmodified strict GoldenReplay including fixed gate aliases; no registry exemptions"});
    return bad==0?0:1;
}
var trials=((IEnumerable)Call("SeriesCatalogue","HookedTrials")!).Cast<object>().ToArray();
if(trials.Length!=318) throw new Exception($"Expected pinned318 hooked trials, found {trials.Length}");
var rows=new List<object>();int failed=0,statePass=0,drawPass=0;
using var log=new StreamWriter(new FileStream(args[0],FileMode.CreateNew));
foreach(var trial in trials)
{
    var spec=Get(trial,"Series");var name=(string)Get(spec,"Name");
    try
    {
        var hook=Call("HookLog","Load",Get(trial,"HookLog"))!;
        var pair=hook.GetType().GetMethod("PairingError",F)!.Invoke(hook,[Get(trial,"Seed"),((IEnumerable)Get(spec,"Files")).Cast<object>().Count()]);
        if(pair is not null) throw new Exception("Fixture pairing: "+pair);
        var state=Call("GoldenReplay","Run",spec,true,null)!;
        var full=Call("GoldenReplay","Run",spec,false,null)!;
        var stateEqual=(bool)Get(state,"Passed");
        var structural=full.GetType().GetProperty("Structural",F)!.GetValue(full);
        var difference=Call("DrawComparison","First",Get(Get(full,"Draws"),"Draws"),hook);
        var drawsEqual=structural is null&&difference is null;
        if(stateEqual)statePass++;if(drawsEqual)drawPass++;
        if(!stateEqual||!drawsEqual)failed++;
        var row=new{trial=name,stateEqual,drawsEqual,
            stateDescription=state.GetType().GetMethod("Describe",F)!.Invoke(state,[spec]),
            structural,firstDrawDifference=difference,filesMatched=Get(state,"FilesMatched"),
            portDraws=((IEnumerable)Get(Get(full,"Draws"),"Draws")).Cast<object>().Count(),
            originalDraws=((IEnumerable)Get(hook,"Draws")).Cast<object>().Count()};
        rows.Add(row);log.WriteLine(JsonSerializer.Serialize(row));log.Flush();
        if(!stateEqual||!drawsEqual)Console.WriteLine(name+" DIFF "+JsonSerializer.Serialize(row));
    }
    catch(Exception e)
    {
        failed++;var row=new{trial=name,error=e.GetBaseException().ToString()};rows.Add(row);
        log.WriteLine(JsonSerializer.Serialize(row));log.Flush();Console.WriteLine(name+" ERROR "+e.GetBaseException().Message);
    }
}
using(var file=new FileStream(args[1],FileMode.CreateNew))JsonSerializer.Serialize(file,new{trials=trials.Length,statePass,drawPass,failed,rows,scope="Strict original GoldenReplay.Passed and ordered DrawComparison, no registry exemptions or fixture changes"});
Console.WriteLine($"{trials.Length} trials: state={statePass}, draws={drawPass}, failed={failed}");
return failed==0?0:1;
