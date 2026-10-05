"""Ports of the game's number formatting and of the End of Game text selection, written from the tracked code extract
(code_extract_end_of_game.txt: FUN_00448e74, FUN_00448f18, FUN_004028c4, THumanFalls_InitializeForm). The thresholds are READ from the extract by
`constants()` (nothing is typed in as an expectation); the strings are taken from the extract's literals."""
import re, os, struct
from paths import DATA

from common import latest
EXTRACT = latest(os.path.join(DATA, 'code_extract_end_of_game.txt'))        # the newest version of the tracked extract (older ones are kept)

def extract_lines(path=EXTRACT):
    """{ghidra line number: text} of the tracked code extract."""
    d = {}
    for l in open(path, encoding='utf-8'):
        m = re.match(r'(\d+)\t(.*)$', l.rstrip('\n'))
        if m: d[int(m.group(1))] = m.group(2)
    return d

def e74(v):
    """FUN_00448e74 (:47544): 13 spaces, digits from index 3 with a comma before every group of three, a '-' at index 1 for a negative value."""
    s = [' '] * 13
    if v < 0: s[1] = '-'
    d = str(abs(v)); i = 3
    for k, ch in enumerate(d, 1):
        s[i] = ch; i += 1
        if (len(d) - k) % 3 == 0 and k < len(d): s[i] = ','; i += 1
    return ''.join(s)

def f18(v):
    """FUN_00448f18 (:47581): e74 with the trailing spaces cut."""
    return e74(v).rstrip(' ')

def window_texts(nation, leader, year, pop_start, cities_start, money_start, pop_now, cities_now, money_now, conqueror_name, conquered_by, unity):
    """The eleven label captions of THumanFalls_InitializeForm (:56353) as the code builds them, from the nation fields it reads."""
    t = {'lbl_result1': 'The game is over for %s the leader of %s.' % (leader, nation)}
    if cities_now < 0x14e:
        if year == 0xfa: t['lbl_result2'] = 'You have reached the end of your allotted 20 years.'
        elif conquered_by < 0:
            t['lbl_result2'] = ('Your unpopularity has forced the army to overthrow you.' if unity < 400
                                else 'Your army have deposed you because they have not been paid.')
        else: t['lbl_result2'] = 'Your nation has been conquerred by %s.' % conqueror_name
    else: t['lbl_result2'] = 'You have conquerred the Mediterranean, a unique achievement.'
    mid = ('%d years ' % (0x10e - year)) if year < 0x10d else ' short time '
    t['lbl_changes'] = 'Your %sin power in %s produced these changes.' % (mid, nation)
    t['lbl_nat1'] = '%s in 270 BC.' % nation
    t['lbl_pop1'] = 'Population' + f18(pop_start)
    t['lbl_cities1'] = 'Cities   %d' % cities_start
    t['lbl_money1'] = 'Treasury ' + f18(money_start) + ' talents'
    t['lbl_nat2'] = '%s in %d BC.' % (nation, year)
    t['lbl_pop2'] = 'Population' + e74(pop_now)
    t['lbl_cities2'] = 'Cities   %d' % cities_now
    t['lbl_money2'] = 'Treasury ' + f18(money_now) + ' talents'
    return t

def norm(s):
    return ' '.join(s.split())

# ---- the save fields the window reads (offsets in the nation record; docs/sav-layout-notes.md, confirmed by the memory reads of the experiment) ----
NATION_FIELDS = {'wealth': (0x430, 'i'), 'wealth_start': (0x434, 'i'), 'treasury': (0x438, 'i'), 'treasury_start': (0x43C, 'i'), 'unity': (0x440, 'h'),
                 'cities': (0x446, 'h'), 'cities_start': (0x448, 'h'), 'conquered_by': (0x44E, 'h'), 'human': (0x490, 'B')}

def nation0(b):
    """Offset of nation record 0 in a save (the army table, then the fleet table, then the 16 nation records: state/sav.py)."""
    from state import sav as SAV
    na = SAV.i16(b, SAV.ARMY_OFF); off_f = SAV.ARMY_OFF + 2 + na * SAV.ARMY_LEN; nf = SAV.i16(b, off_f)
    return off_f + 2 + nf * SAV.FLEET_LEN

def nation_fields(save_bytes, n):
    """The window's inputs for nation n read raw from a save, plus names, the calendar and the human flags."""
    from state import sav as SAV
    t = SAV.parse(bytes(save_bytes)); n0 = nation0(save_bytes)
    cs = lambda m, o, ln: save_bytes[n0 + m * SAV.NATION_LEN + o:n0 + m * SAV.NATION_LEN + o + ln].split(b'\0')[0].decode('latin1')
    d = {k: struct.unpack_from('<' + f, save_bytes, n0 + n * SAV.NATION_LEN + o)[0] for k, (o, f) in NATION_FIELDS.items()}
    d['name'] = cs(n, 0, 11); d['leader'] = cs(n, 0x0B, 27)
    d['year'] = t['year_bc']; d['week'] = t['week']; d['season'] = t['season']; d['current_nation'] = t['current_nation']
    d['humans'] = [m for m in range(16) if save_bytes[n0 + m * SAV.NATION_LEN + 0x490]]
    d['names'] = [cs(m, 0, 11) for m in range(16)]
    return d
