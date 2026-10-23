using IC2.Engine.Model;
using IC2.Engine.Presentation;
using IC2.Engine.Serialization;

static class FeatureCases
{
    public static void Generate(World w,Ruleset r,Scenario scenario,
        Action<string,string,GameState,object,string> capture,Action<object> emit)
    {
        var session=new GameSession(w,r,scenario,seedOverride:7,humanSeatNationId:"rome");
        var b=session.State;
        var terrain=w.Terrain.Decode(w.Width,w.Height);
        int num=0;
        void C(string label,GameState s,object plan,string command,string origin="synthetic native-model setup") =>
            capture($"F{num++:D2}-{label}",origin,s,plan,command);
        GameState Army(GameState s,int index,ArmyState a)=>s with{Armies=s.Armies.Replace(index,a)};
        GameState Nation(GameState s,int index,NationState n)=>s with{Nations=s.Nations.Replace(index,n)};
        int Index(string nation)=>Enumerable.Range(0,w.Nations.Count).Single(i=>w.Nations[i].Id==nation);
        var a=b.Armies[0];
        var rome=b.Nations[0];
        var arretium=b.Cities.Single(c=>c.Id=="arretium");
        var antium=b.Cities.Single(c=>c.Id=="antium");
        int second=Enumerable.Range(1,b.Armies.Count-1).First(i=>b.Armies[i].Nation=="rome");
        var adjacent=Army(b,second,b.Armies[second] with{X=a.X+1,Y=a.Y,Moves=8});
        C("army-split",b,new{kind="split-army",army=0,units=new[]{0}},"split-army army-0 broad-split 0","gameplay-derived initial state");
        C("army-join",adjacent,new{kind="join-armies",army=0},$"join-armies army-0 army-{second}");
        C("army-transfer",adjacent,new{kind="transfer-units",army=0,unit=0},$"army-transfer army-0 army-{second} units=0");
        var named=Army(b,0,a with{Units=a.Units.Replace(0,a.Units[0] with{Name="ABCDEFGHIJKLMNOPQRSTUVW"})});
        C("unit-name23",named,new{kind="rename-unit",army=0,unit=0,text="BROAD_153"},"rename-unit army-0 0 BROAD_153");
        C("unit-split",b,new{kind="split-unit",army=0,unit=0,hundreds=0},$"split-unit army-0 0 {a.Units[0].Troops/2}","gameplay-derived initial state");
        var joinunits=Army(b,0,a with{Units=a.Units.Replace(1,a.Units[1] with{Troops=2000}).Replace(2,a.Units[2] with{Troops=2000})});
        C("unit-join",joinunits,new{kind="join-units",army=0,units=new[]{1,2}},"join-units army-0 1 2");
        C("army-disband",b,new{kind="disband-army",army=0},"disband-army army-0","gameplay-derived initial state");
        var low=Army(b,0,a with{SupplyTons=0});
        C("army-supply",low,new{kind="supply",army=0,tons=10,money_100s=0},$"buy army-0 {arretium.Id} 10");
        C("army-money",b,new{kind="supply",army=0,tons=0,money_100s=1},"transfer-money army-0 100","gameplay-derived initial state");
        // One controlled offer at the adjacent city; all other offers there removed.
        var merc=new MercenaryPoolSlot(0,arretium.X,arretium.Y,1,"light_infantry",2000,7);
        var pool=b.MercenaryPool.Where(m=>m.SlotIndex!=0 && (m.X!=arretium.X||m.Y!=arretium.Y)).Append(merc).OrderBy(m=>m.SlotIndex);
        var hire=Army(b with{MercenaryPool=ValueList.From(pool)},0,a with{Money=1000});
        C("mercenary-hire",hire,new{kind="mercenary",army=0,row=0},"hire-mercenary army-0 0");
        var alias=Army(b,0,a with{Units=a.Units.Replace(0,a.Units[0] with{MercenaryLabel=7,Name="Mercenary unit (label 7)"})});
        C("mercenary-alias",alias,new{kind="tax",value=18},"set-tax 18");
        // Every original unit type gets a real recruitment command after conversion.
        foreach(var (id,shortName) in new[]{("light_infantry","li"),("heavy_infantry","hi"),("archers","ar"),("light_cavalry","lc"),("heavy_cavalry","hc")})
        {
            var recruit=Nation(b,0,rome with{RecruitmentSlots=ValueList<RecruitmentSlot>.Empty});
            C("recruit-"+shortName,recruit,new{kind="recruit",city="Rome",type=shortName,thousands=1},$"recruit-standing rome {id} 1000");
        }
        var ready=Nation(b,0,rome with{RecruitmentSlots=ValueList.Of(new RecruitmentSlot("rome","heavy_infantry",1000,18))});
        C("mobilize-quality4",ready,new{kind="mobilize",city="Rome",units=new[]{0}},"mobilize 0 broad-mobilized");
        C("recruit-disband",ready,new{kind="disband-slot",city="Rome",unit=0},"disband-slot 0");
        var capped=Nation(b,0,rome with{RecruitmentSlots=ValueList.From(Enumerable.Range(0,40).Select(_=>new RecruitmentSlot("rome","light_infantry",100,0)))});
        C("recruit-cap40",capped,new{kind="recruit",city="Rome",type="hi",thousands=1,expect_unchanged=true},"recruit-standing rome heavy_infantry 1000");
        // Native carrier staged at the previously exercised Antium port geometry.
        int fx=101,fy=46,ax=101,ay=45;
        if(terrain[fy*w.Width+fx]!=0 || terrain[ay*w.Width+ax]<2)throw new Exception("Port terrain changed");
        var fleet=b.Fleets[0] with{Nation="rome",X=fx,Y=fy,Moves=25,Ships=60,ConditionPercent=90,
            Money=100,SupplyTons=0,ConstructionTicksRemaining=null,BuildCityId=null,CarriedArmyId=null,CoveredTileCode=0};
        var port=b with{Fleets=b.Fleets.Replace(0,fleet),Armies=b.Armies.Replace(0,a with{X=ax,Y=ay,Moves=8})};
        C("fleet-repair",port,new{kind="repair-fleet",fleet=0,points=3},"repair-fleet fleet-0 3");
        C("fleet-supply",port,new{kind="supply-fleet",fleet=0,tons=100},$"buy-fleet-supply fleet-0 {antium.Id} 100");
        C("fleet-split",port,new{kind="split-fleet",fleet=0,ships=10},"split-fleet fleet-0 broad-fleet 10");
        int nx=100,ny=46;
        if(terrain[ny*w.Width+nx]!=0)throw new Exception("Adjacent port sea changed");
        var pair=port with{Fleets=ValueList.From(port.Fleets.Append(fleet with{Id="broad-partner",X=nx,Y=ny,Ships=20}))};
        int partner=pair.Fleets.Count-1;
        C("fleet-join",pair,new{kind="join-fleets",fleet=0},$"join-fleets fleet-0 fleet-{partner}");
        C("fleet-transfer",pair,new{kind="transfer-ships",fleet=0,ships=5},$"fleet-transfer fleet-0 fleet-{partner} 5 0 0");
        var over=pair with{Fleets=pair.Fleets.Replace(partner,pair.Fleets[partner] with{Ships=41})};
        C("fleet-cap101",over,new{kind="join-fleets",fleet=0,expect_unchanged=true},$"join-fleets fleet-0 fleet-{partner}");
        C("fleet-scuttle",port,new{kind="scuttle",fleet=0},"scuttle-fleet fleet-0");
        C("fleet-move",port,new{kind="move-fleet",fleet=0,x=nx,y=ny},$"move-fleet fleet-0 {nx} {ny}");
        C("embark",port,new{kind="embark",army=0,fleet=0},"embark-army army-0 fleet-0");
        var cargo=port with{Armies=port.Armies.Replace(0,port.Armies[0] with{X=fx,Y=fy,AboardFleetId=fleet.Id,CoveredTileCode=null}),
            Fleets=port.Fleets.Replace(0,fleet with{CarriedArmyId=a.Id})};
        C("disembark",cargo,new{kind="disembark",army=0,fleet=0,x=ax,y=ay},$"disembark-army army-0 {ax} {ay}");
        C("fleet-build",b,new{kind="build-fleet",ships=10},"order-fleet neapolis 10 broad-built","gameplay-derived initial state; original chooses its own free port");
        var war=b with{Relations=b.Relations.WithRelation("rome","media",0)};
        C("declare-war",war,new{kind="relation",nation=Index("media"),relation="war"},"declare-war media");
        var trade=b with{Relations=b.Relations.WithRelation("rome","numidia",0)};
        C("trade",trade,new{kind="relation",nation=Index("numidia"),relation="trade"},"propose-trade numidia");
        var offer=trade with{PendingOffer=new PendingDiplomaticOffer("numidia",1)};
        C("pending-offer",offer,new{kind="observe",load_offer_nation=Index("numidia"),load_offer_value=1},"accept-offer");
        var fortCity=b.Cities.First(c=>c.Owner=="rome"&&c.FortificationCode<90&&!b.Armies.Any(x=>Math.Abs(x.X-c.X)<=1&&Math.Abs(x.Y-c.Y)<=1&&x.Nation!="rome"));
        C("fortification",b,new{kind="fortify",city=fortCity.Name,x=fortCity.X,y=fortCity.Y,points=1},$"order-city {fortCity.Id} fortify 1","gameplay-derived initial state");
        var debt=Nation(b,0,rome with{Treasury=-500,TaxRatePercent=40});
        C("debt-tax40",debt,new{kind="tax",value=0},"set-tax 0");
        var quality=Army(b,0,a with{Units=a.Units.Replace(0,a.Units[0] with{Quality=4}).Replace(1,a.Units[1] with{Quality=9})});
        C("quality4-and9",quality,new{kind="move",army=0,x=a.X+1,y=a.Y},$"move army-0 {a.X+1} {a.Y}");
        // Elimination/conqueror state is representable, but importer1351 may lose history.
        int dead=Index("media");
        var eliminated=b with{Cities=ValueList.From(b.Cities.Select(c=>c.Owner=="media"?c with{Owner="rome"}:c)),
            Armies=ValueList.From(b.Armies.Where(x=>x.Nation!="media")),Fleets=ValueList.From(b.Fleets.Where(x=>x.Nation!="media")),
            Nations=b.Nations.Replace(dead,b.Nations[dead] with{CapitalCityId=null,Unity=0,Eliminated=true,ConqueredBy="rome"})};
        C("eliminated-conqueror",eliminated,new{kind="tax",value=18},"set-tax 18");
        var hotScenario=scenario with{Seats=ValueList.From(scenario.Seats.Select(s=>s with{Control=s.Nation is "rome" or "carthage"?SeatControl.Human:SeatControl.Ai}))};
        var hot=new GameSession(w,r,hotScenario,seedOverride:11);
        C("hotseat",hot.State,new{kind="end-turn"},"end","gameplay: two human seats in constructor");
        var winter=b with{Calendar=b.Calendar with{SeasonIndex=3,Week=11},RoughSeaCells=ValueList.Of(new RoughSeaCell(fx,fy))};
        C("winter-roughsea",winter,new{kind="tax",value=18},"set-tax 18");
        var enemyFleet=fleet with{Id=b.Fleets[1].Id,Nation="carthage",X=nx,Y=ny,Ships=20,ConditionPercent=80};
        var naval=port with{Fleets=port.Fleets.Replace(1,enemyFleet),Relations=port.Relations.WithRelation("rome","carthage",3)};
        C("naval-combat",naval,new{kind="attack-fleet",fleet=0,enemy=1},"attack-fleet fleet-0 fleet-1");
        var target=b.Cities.First(c=>c.Owner=="gaul");
        var near=(from dx in new[]{-1,0,1} from dy in new[]{-1,0,1}
            let x=target.X+dx let y=target.Y+dy
            where x>=0&&y>=0&&x<w.Width&&y<w.Height&&terrain[y*w.Width+x]>=2&&terrain[y*w.Width+x]<=11
            where !b.Cities.Any(c=>c.X==x&&c.Y==y)&&!b.Armies.Any(z=>z.X==x&&z.Y==y)
            select (x,y)).First();
        var siege=Army(b,0,a with{X=near.x,Y=near.y,Moves=8});
        siege=siege with{Relations=siege.Relations.WithRelation("rome","gaul",3),
            Cities=ValueList.From(siege.Cities.Select(c=>c.Id==target.Id?c with{FortificationCode=0,Loyalty=15}:c))};
        C("siege-capture",siege,new{kind="siege",army=0,x=target.X,y=target.Y},$"besiege-city army-0 {target.Id}");
        // A genuine instant field battle in the remake; export its aftermath.
        int enemy=Enumerable.Range(0,b.Armies.Count).First(i=>b.Armies[i].Nation=="gaul");
        var battle=Army(b,enemy,b.Armies[enemy] with{X=a.X+1,Y=a.Y});
        battle=battle with{Relations=battle.Relations.WithRelation("rome","gaul",3)};
        var battleSave=new SaveGame(GameDataSchema.CurrentVersion,"battle-input","battle-input",battle.ScenarioId,battle.WorldId,battle.RulesetId,battle);
        var fought=new GameSession(w,r,scenario,battleSave);
        var battleOutput=fought.Submit($"attack-army {a.Id} {battle.Armies[enemy].Id}");
        emit(new{kind="native-field-battle",battleOutput.Lines,battleOutput.Battles});
        if(fought.HasPendingPeaceOffers)emit(new{kind="decline-native-treaty",output=fought.Submit("peace-no").Lines});
        C("field-battle-aftermath",fought.State,new{kind="end-turn"},"end","public native battle command from labelled synthetic adjacent armies; pending treaty declined");
        var alliance=b with{Relations=b.Relations.WithRelation("rome","numidia",1)};
        C("alliance",alliance,new{kind="relation",nation=Index("numidia"),relation="ally"},"propose-alliance numidia");
        var peace=b with{Relations=b.Relations.WithRelation("rome","numidia",3)};
        C("peace",peace,new{kind="relation",nation=Index("numidia"),relation="peace"},"make-peace numidia");
        var weather=port with{Calendar=port.Calendar with{SeasonIndex=3,Week=11},RoughSeaCells=ValueList.Of(new RoughSeaCell(fx,fy))};
        C("winter-rough-fleet",weather,new{kind="end-turn"},"end");
        C("regular-unit-disband",b,new{kind="disband-regular",army=0,unit=0},"disband-unit army-0 0","gameplay-derived initial state");
        var foreign=low with{Cities=ValueList.From(low.Cities.Select(c=>c.Id==arretium.Id?c with{Owner="carthage"}:c)),
            Relations=low.Relations.WithRelation("rome","carthage",0),Armies=low.Armies.Replace(0,low.Armies[0] with{Money=1000})};
        C("foreign-city-supply",foreign,new{kind="supply",army=0,tons=10,money_100s=0},$"buy army-0 {arretium.Id} 10");
        C("fleet-money",port,new{kind="supply-fleet",fleet=0,tons=0,money=100},"transfer-money fleet-0 100");
        var hugeUnits=ValueList.From(Enumerable.Range(0,10).Select(i=>a.Units[i%a.Units.Count] with{Troops=10000,Name="Cap"+i}));
        C("army100000",Army(b,0,a with{Units=hugeUnits}),new{kind="split-army",army=0,units=new[]{0}},"split-army army-0 cap-split 0");
        var twenty=adjacent with{Armies=adjacent.Armies.Replace(0,a with{Units=ValueList.From(Enumerable.Range(0,11).Select(i=>a.Units[0] with{Troops=1000,Name="A"+i}))})
            .Replace(second,adjacent.Armies[second] with{Units=ValueList.From(Enumerable.Range(0,10).Select(i=>a.Units[0] with{Troops=1000,Name="B"+i}))})};
        C("army-unit-cap21",twenty,new{kind="join-armies",army=0,expect_unchanged=true},$"join-armies army-0 army-{second}");
        var hundred=pair with{Fleets=pair.Fleets.Replace(partner,pair.Fleets[partner] with{Ships=40})};
        C("fleet100",hundred,new{kind="join-fleets",fleet=0},$"join-fleets fleet-0 fleet-{partner}");
        C("unit-split-hi5000",b,new{kind="split-unit",army=0,unit=1,hundreds=0},"split-unit army-0 1 2500","gameplay-derived initial state; HI5000 exceeds original2400 minimum; separate from LI4800 refusal");
        var calm=b.Relations;
        foreach(var n in w.Nations)
        {
            if(n.Id!="rome")calm=calm.WithRelation("rome",n.Id,0);
            if(n.Id!="numidia")calm=calm.WithRelation("numidia",n.Id,0);
        }
        var calmAlliance=b with{Relations=calm.WithRelation("rome","numidia",1)};
        C("alliance-peacetime",calmAlliance,new{kind="relation",nation=Index("numidia"),relation="ally"},"propose-alliance numidia");
        var breakTrade=b with{Relations=b.Relations.WithRelation("rome","numidia",1)};
        C("peace-from-trade",breakTrade,new{kind="relation",nation=Index("numidia"),relation="peace"},"make-peace numidia");
        emit(new{kind="feature-generation-complete",count=num});
    }
}

static class ExperimentListExtensions
{
    public static ValueList<T> Replace<T>(this ValueList<T> items,int index,T value) =>
        ValueList.From(items.Select((item,i)=>i==index?value:item));
}
