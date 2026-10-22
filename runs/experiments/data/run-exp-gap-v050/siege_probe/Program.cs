// The remake v0.5.0's AI siege gate, recomputed offline with the engine's own functions (research's suggestion, 2026-10-09).
// For every save of an idle-Rome game: every AI army (not aboard a fleet, with troops) adjacent (AttackLegality.AreAdjacent) to a city
// of a nation it is at war with (AiView.IsAtWar). For each such pair, the same quantities ProposeSieges computes
// (AiMilitaryPhase.cs:281-371): AttackLegality.IsLegal(besiege); SiegeStrength.Attacker; CompleteDefenderStrength.Compute;
// AiView.RatioPermille; AiView.RequiredAttackRatioPermille(AiPersonalityProfile.For(nation).AggressionPermille). The defender is computed
// twice: with the city's real fortification, and with its fortification code frozen at its value in the turn-10 save (if the city
// existed then with the same owner; else the real one). One JSON line per pair to stdout.
// Usage: SiegeProbe <data dir> <save glob prefix> <first turn> <last turn>
using System.Text.Json;
using IC2.Engine.Ai;
using IC2.Engine.Battle.Commands;
using IC2.Engine.Cities.Capture;
using IC2.Engine.Model;
using IC2.Engine.Persistence;
using IC2.Engine.Serialization;
using IC2.Engine.Strength;

var repo = GameDataRepository.Load(args[0]);
string prefix = args[1]; int first = int.Parse(args[2]), last = int.Parse(args[3]);
SaveGame Load(int t)
{
    var path = $"{prefix}{t:000}.sav";
    var sum = SaveManager.PeekSummaryFile(path);
    return SaveManager.LoadFile(path, repo.WorldById(sum.WorldId)!, repo.RulesetById(sum.RulesetId)!);
}
var s10 = Load(10).State;
var fort10 = s10.Cities.ToDictionary(c => c.Id, c => (c.Owner, c.FortificationCode));
for (int t = first; t <= last; t++)
{
    var save = Load(t);
    var st = save.State;
    var ruleset = repo.RulesetById(save.RulesetId)!;
    var world = repo.WorldById(save.WorldId)!;
    var archer = BattleCommandRuleset.ArcherUnitTypeIdIn(ruleset)!;
    var fortId = BattleCommandRuleset.FortificationOrderIdIn(ruleset)!;
    var fortify = ruleset.CityOrders.Orders.First(o => o.Id == fortId);
    foreach (var army in st.Armies)
    {
        var nation = st.NationById(army.Nation);
        if (nation is null || army.Nation == "rome" || army.AboardFleetId is not null || !army.Units.Any(u => u.Troops > 0)) continue;
        var view = new AiView(st, ruleset, world, army.Nation);
        var required = AiView.RequiredAttackRatioPermille(AiPersonalityProfile.For(nation, ruleset).AggressionPermille, ruleset);
        var attacker = SiegeStrength.Attacker(army.Units, army.Morale, ruleset, archer);
        foreach (var city in st.Cities)
        {
            if (city.Owner is null || city.Owner == army.Nation || !view.IsAtWar(army.Nation, city.Owner)) continue;
            if (!AttackLegality.AreAdjacent(army.X, army.Y, city.X, city.Y)) continue;
            var owner = st.NationById(city.Owner)!;
            bool cap = CapitalOwnership.IsAnyNationsCapital(st, city.Id), alleg = city.Owner != city.Allegiance;
            bool legal = AttackLegality.IsLegal(st, ruleset, new BesiegeCityCommand(army.Nation, army.Id, city.Id));
            var defReal = CompleteDefenderStrength.Compute(city, fortify, cap, alleg, owner, ruleset);
            var f10 = fort10.TryGetValue(city.Id, out var v) && v.Owner == city.Owner ? v.FortificationCode : city.FortificationCode;
            var defFrozen = CompleteDefenderStrength.Compute(city with { FortificationCode = f10 }, fortify, cap, alleg, owner, ruleset);
            var rReal = AiView.RatioPermille(attacker, defReal, ruleset);
            var rFrozen = AiView.RatioPermille(attacker, defFrozen, ruleset);
            Console.WriteLine(JsonSerializer.Serialize(new
            {
                turn = t, nation = army.Nation, army = army.Id, troops = army.Units.Sum(u => u.Troops), morale = army.Morale, city = city.Id, owner = city.Owner,
                legal, attacker, fort = city.FortificationCode, fort_t10 = f10, def_real = defReal, def_frozen = defFrozen,
                ratio_real = rReal, ratio_frozen = rFrozen, required, pass_real = rReal >= required, pass_frozen = rFrozen >= required
            }));
        }
    }
}
