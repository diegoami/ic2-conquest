"""One SAV -> the JSON snapshot this experiment analyses: nations (tax/unity/treasury/wealth + the +0x26 relation
shorts), armies (money, position, unit slots with merc labels), the 50-slot mercenary pool, the date. Everything
sav.py already parses is reused; only the relations are read here, at nation record +0x26 (16 shorts, 3 = war;
the offset cosmetic_gaps/stage_neutral.py proved on the byte level)."""
import json, struct, sys
sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
sys.path.insert(0, __import__('os').path.join(__import__('os').path.dirname(__import__('os').path.abspath(__file__)), '..', '..', '..'))
from paths import DATA
import state.sav as SAV
from state.sav import ARMY_OFF, ARMY_LEN, FLEET_LEN, NATION_LEN, NATIONS


def nation_offset(b):
    """Offset of the 16 nation records in a save (same walk as SAV.parse)."""
    na = struct.unpack_from('<h', b, ARMY_OFF)[0]
    o = ARMY_OFF + 2 + na * ARMY_LEN
    nf = struct.unpack_from('<h', b, o)[0]
    return o + 2 + nf * FLEET_LEN


def snapshot(b, path=''):
    s = SAV.parse(b)
    no = nation_offset(b)
    for n in s['nations']:
        rel = list(struct.unpack_from('<16h', b, no + n['id'] * NATION_LEN + 0x26))
        n['relations'] = rel
        n['wars'] = sorted(NATIONS[i] for i, r in enumerate(rel) if r == 3)
    return {
        'save': path,
        'turn': s['turn'], 'date': s['date'], 'week': s['week'], 'season': s['season'], 'year_bc': s['year_bc'],
        'current': NATIONS[s['current_nation']],
        'nations': [{k: n[k] for k in ('id', 'name', 'alive', 'tax', 'unity', 'treasury', 'wealth',
                                       'cities_count', 'capital', 'wars')} for n in s['nations']],
        'armies': [{'id': a['id'], 'owner': NATIONS[a['owner']] if a['owner'] >= 0 else None,
                    'x': a['x'], 'y': a['y'], 'moves': a['moves'], 'money': a['money'],
                    'supplies': a['supplies'], 'morale': a['morale'], 'troops': a['troops'],
                    'units': a['units']} for a in s['armies'] if a['owner'] >= 0],
        'mercenaries': s['mercenaries'],
        'news': s['news'][-12:],
    }


if __name__ == '__main__':
    for p in sys.argv[1:]:
        print(json.dumps(snapshot(open(p, 'rb').read(), p.split('/')[-1]), indent=1)[:2000])
