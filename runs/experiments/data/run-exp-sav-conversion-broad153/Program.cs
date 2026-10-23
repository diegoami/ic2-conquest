using System.Text.Json;
using IC2.Engine.Import;
using IC2.Engine.Model;
using IC2.Engine.Persistence;
using IC2.Engine.Presentation;
using IC2.Engine.Serialization;

var repo = GameDataRepository.Load(Path.Combine(args[1], "data"));
var resolved = repo.Resolve("classical-mediterranean");
var world = resolved.World;
var rules = repo.RulesetById("classical-faithful")!;
var scenario = resolved.Scenario;
var terrain = world.Terrain.Decode(world.Width, world.Height);
void Emit(object value) => Console.WriteLine(JsonSerializer.Serialize(value));
SaveGame Wrap(GameState s, string id) => new(GameDataSchema.CurrentVersion, id, id, s.ScenarioId, s.WorldId, s.RulesetId, s);
void Write(string path, SaveGame save)
{
    if (File.Exists(path)) throw new IOException("Refusing existing destination " + path);
    SaveManager.WriteFile(path, save);
}
object Summary(GameState s) => new { turn=s.Calendar.TurnIndex, calendar=s.Calendar,
    active=s.ActiveNationId, human=s.Nations.Where(n=>n.Control==SeatControl.Human).Select(n=>n.Id),
    armies=s.Armies.Count, fleets=s.Fleets.Count, building=s.Fleets.Count(f=>f.IsUnderConstruction),
    cargo=s.Armies.Count(a=>a.IsEmbarked), recruits=s.Nations.Sum(n=>n.RecruitmentSlots.Count),
    eliminated=s.Nations.Where(n=>n.Eliminated).Select(n=>n.Id), pending=s.PendingOffer };
(object plan, string command) MoveOrTax(GameState s)
{
    for(int i=0;i<s.Armies.Count;i++)
    {
        var a=s.Armies[i];
        if(a.Nation!=s.ActiveNationId || a.IsEmbarked || a.Moves<4) continue;
        foreach(var (dx,dy) in new[]{(1,0),(0,1),(-1,0),(0,-1),(1,1),(-1,-1)})
        {
            int x=a.X+dx,y=a.Y+dy;
            if(x<0||y<0||x>=world.Width||y>=world.Height)continue;
            int code=terrain[y*world.Width+x];
            if(code<2||code>11)continue;
            if(s.Cities.Any(c=>c.X==x&&c.Y==y)||s.Armies.Any(b=>!b.IsEmbarked&&b.X==x&&b.Y==y)||s.Fleets.Any(f=>!f.IsUnderConstruction&&f.X==x&&f.Y==y))continue;
            return(new {kind="move",army=i,x,y},$"move army-{i} {x} {y}");
        }
    }
    return(new {kind="tax",value=17},"set-tax 17");
}
void Capture(string dir,string name,string category,string provenance,GameState s,object action,string command,ulong seed=7)
{
    Directory.CreateDirectory(dir);
    var path=Path.Combine(dir,name+".json");
    if(args[0].StartsWith("features-") && File.Exists(path))
    {
        Emit(new{kind="preserve-existing-source",name});return;
    }
    Write(path,Wrap(s,name));
    var loaded=SaveManager.LoadFile(path,world,rules);
    var record=new {name,category,provenance,nation=s.ActiveNationId,seed,originalAction=action,remakeCommand=command,
        summary=Summary(loaded.State)};
    File.AppendAllText(Path.Combine(dir,"manifest.jsonl"),JsonSerializer.Serialize(record)+"\n");
    Emit(record);
}

if(args[0]=="starts")
{
    for(int n=0;n<world.Nations.Count;n++)
    {
        ulong seed=n%2==0?7UL:11UL;
        var session=new GameSession(world,rules,scenario,seedOverride:seed,humanSeatNationId:world.Nations[n].Id);
        var (plan,command)=MoveOrTax(session.State);
        Capture(args[2],$"S{n:D2}-{world.Nations[n].Id}","nation-start","gameplay: first human seat after constructor prelude",session.State,plan,command,seed);
    }
}
else if(args[0]=="progress")
{
    foreach(var (nation,ticks,seed) in new[]{("rome",6,7UL),("carthage",12,11UL),("ptolemaic",18,7UL),("macedonia",24,11UL)})
    {
        var session=new GameSession(world,rules,scenario,seedOverride:seed,humanSeatNationId:nation);
        for(int t=0;t<ticks;t++)
        {
            var output=session.Submit("end");
            Emit(new {kind="progress-command",nation,t,output.Lines,output.ShouldExit});
            if(output.ShouldExit)break;
        }
        Capture(args[2],$"P{ticks:D2}-{nation}","progressed","gameplay: repeated public end command; no orders",session.State,
            new{kind="end-turn"},"end",seed);
    }
}
else if(args[0] is "features" or "features-extra" or "features-more" or "features-final")
{
    FeatureCases.Generate(world,rules,scenario,(name,origin,s,plan,command)=>Capture(args[2],name,"feature",origin,s,plan,command),Emit);
}
else if(args[0]=="open-battle")
{
    var initial=new GameSession(world,rules,scenario,seedOverride:7,humanSeatNationId:"rome").State;
    int enemy=Enumerable.Range(0,initial.Armies.Count).First(i=>initial.Armies[i].Nation=="gaul");
    var a=initial.Armies[0];
    var staged=initial with{Armies=initial.Armies.Replace(enemy,initial.Armies[enemy] with{X=a.X+1,Y=a.Y}),
        Relations=initial.Relations.WithRelation("rome","gaul",3)};
    var session=new GameSession(world,rules,scenario,Wrap(staged,"battle-input")){HumanBattles=HumanBattleMode.Tactical};
    var output=session.Submit($"attack-army {a.Id} {initial.Armies[enemy].Id}");
    if(session.OpenTacticalBattle is null)throw new Exception("Battle did not open: "+string.Join(";",output.Lines));
    if(File.Exists(args[2]))throw new IOException("Refusing existing battle save");
    var saved=session.Submit("save "+args[2]);
    Emit(new{kind="actual-open-battle-save",output.Lines,saved=saved.Lines,battleOpen=session.OpenTacticalBattle!=null});
}
else if(args[0]=="import")
{
    var imported=OriginalSaveImporter.Import(File.ReadAllBytes(args[2]),Path.GetFileName(args[2]),world,rules,scenario,"imported","imported");
    Write(args[3],imported.Save);
    var loaded=SaveManager.LoadFile(args[3],world,rules);
    var session=new GameSession(world,rules,scenario,loaded);
    Emit(new{kind="import",summary=Summary(loaded.State),reloadEqual=loaded.State==imported.Save.State,imported.Report,
        resumeSummary=Summary(session.State),status=session.Submit("status mine").Lines});
}
else if(args[0]=="action")
{
    var save=SaveManager.LoadFile(args[2],world,rules);
    var session=new GameSession(world,rules,scenario,save);
    string command=args[4];
    var output=session.Submit(command);
    Write(args[3],Wrap(session.State,"after-command"));
    Emit(new{kind="action",command,output.Lines,output.ShouldExit,changed=session.State!=save.State,
        before=Summary(save.State),after=Summary(session.State),battleOpen=session.OpenTacticalBattle!=null});
}
else throw new ArgumentException("Unknown mode");
