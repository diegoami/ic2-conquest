"""Original Wine control timing, immutable lab snapshots and Random traces.

Never deletes a save. Each mode starts a private process; old BATTLEnn files
are moved aside before this lab series. Originals are used as read-only inputs.
"""
from types import SimpleNamespace
from probe_common import *
from state import battle_block as BB,hook_log
import general_hook
H=general_hook.H
INPUT=ART/'original-inputs/gate2_a_BATTLE02.SAV'
PLAIN='Imperial Conquest 2 lab s1.exe'
HOOK='Imperial Conquest 2 oct16 generalhook.exe'


def build():
    source=drv.G/PLAIN
    b=bytearray(source.read_bytes())
    lab=SimpleNamespace(BATTLE_START_CALL=0x45c1ae,SEED_CAVE=0x564400,TBATTLE_START=0x436fb4)
    info=H.apply(b,1,lab)
    destination=drv.G/HOOK
    if destination.exists():assert destination.read_bytes()==b
    else:
        with destination.open('xb') as out:out.write(b)
    kept=keep(destination,f'general-observer-{STAMP}.exe')
    log('general_hook_build',source=PLAIN,source_sha256=sha(source),output=kept.name,
        output_sha256=sha(destination),info=info,markers=[(name,hex(va)) for name,va,_ in H.MARKERS],
        reserved_word='general_attacker | general_defender<<8 | end<<16 | interrupted<<24')


def record(g,mode,label):
    flags=list(g.mem(0x45e6a4,4))
    state=g.battle_state() if g.in_battle() else None
    log('general_state',mode=mode,label=label,flags=flags,
        active_nation=g.i16(0x45e6aa),active_slots=g.i16(0x45e6ae),
        battle=state,seed=struct.unpack('<I',g.mem(drv.RAND_SEED,4))[0],
        claims=list(struct.unpack('<40h',g.mem(0x45e6b0,80))),
        titles=[w[1] for w in g.find_windows(' v ')])


def preserve_series(g,mode):
    for p in sorted(drv.G.glob('BATTLE*.SAV')):
        copy=keep(p,f'gen_{mode}-{STAMP}-{p.name}')
        block=BB.block_of_save(copy.read_bytes())
        log('general_boundary',mode=mode,file=copy.name,sha256=sha(copy),turn=sav.load(copy)['turn'],battle=block)


def read_hook(g,mode):
    control,recs=hook_log.read_process(g.mem)
    log('general_trace',mode=mode,control=control,records=recs,
        chain_breaks=hook_log.chain_check(recs),source=INPUT.name)
    assert control['magic_ok'] and not control['overflow'] and not control['reentered']


def click_general(g):
    window=g.find_windows(' v ')[0]
    drv.sh('xdotool','windowraise',str(window[0]),check=False)
    drv.sh('xdotool','windowfocus',str(window[0]),check=False)
    g.click(g.battle_x.get('computer',drv.BATTLE_TOOLS['computer']),drv.BATTLE_TOOLBAR_Y,pause=2)


def open_battle(g,source):
    # Game.open waits for strategic map windows, which are hidden during a
    # resumed battle. Use the same proven file dialog, then wait for the battle.
    target=drv.G/source.name
    if target.exists() and target.read_bytes()!=source.read_bytes():g.move_aside([target])
    if not target.exists():shutil.copy2(source,target)
    g.open_file_dialog(target.name)
    g.wait(lambda:g.in_battle() and g.find_windows(' v '),60,'resumed battle window')
    time.sleep(2)


if __name__=='__main__':
    build()
    for mode in sys.argv[1:]:
        src=INPUT
        if mode=='ai_control':
            def edit(b):
                b[stage._nation(b,0)+0x490]=0
                b[stage._nation(b,6)+0x490]=1
                return {'Rome_human':0,'Gaul_human':1,'battle_and_strategic_units_unchanged':True}
            src=staged(INPUT,'gen_ai_control',edit)
        g=PrivateGame(exe=PLAIN if mode=='plain_off' else HOOK,
                      log=lambda line:log('driver',mode=mode,message=line))
        try:
            g.move_aside(sorted(drv.G.glob('BATTLE*.SAV')))
            g.start()
            open_battle(g,src)
            record(g,mode,'fresh_process_after_resume')
            if mode=='interrupt_on':
                info=g.find_windows('^Information$')[0]
                x=info[2]+info[4]//2;y=info[3]+info[5]//2
                # The original polls WM_LBUTTONDOWN on the Information window
                # to relinquish human-side general control. Queue that click
                # immediately after General on, without writing game memory.
                drv.sh('xdotool','mousemove',str(g.battle_x.get('computer',drv.BATTLE_TOOLS['computer'])),
                       str(drv.BATTLE_TOOLBAR_Y),'click','1','mousemove',str(x),str(y),'click','1')
                time.sleep(2)
                record(g,mode,'after_general_then_information_click')
                if g.in_battle() and not g.find_windows('Battle ended'):
                    click_general(g)
                    record(g,mode,'after_general_reenabled')
            elif mode in ('human_on','reload_on'):
                click_general(g)
                record(g,mode,'after_general_on')
                # General-driven movement remains user-stepped by End turn.
                if g.in_battle() and not g.find_windows('Battle ended'):
                    mark=g.battle_progress_mark()
                    g.end_turn_proven(lambda:g.click(g.battle_x.get('end_turn',drv.BATTLE_TOOLS['end_turn']),drv.BATTLE_TOOLBAR_Y,pause=2))
                    record(g,mode,'after_one_end_turn')
                if mode=='reload_on':
                    for _ in range(40):
                        if not g.in_battle() or g.find_windows('Battle ended'):break
                        g.end_turn_proven(lambda:g.click(g.battle_x.get('end_turn',drv.BATTLE_TOOLS['end_turn']),drv.BATTLE_TOOLBAR_Y,pause=1))
                    g.wait(lambda:g.find_windows('Battle ended'),30,'battle result before same-process reload')
                    cs=g.controls('Battle ended')
                    g.click_control(g.control(cs,text='OK'),pause=2)
                    if g.find_windows('^Offer of peace$'):g.answer_battle_peace(False)
                    g.dismiss_popups()
                    record(g,mode,'finished_battle_before_reload')
                    open_battle(g,INPUT)
                    record(g,mode,'same_process_reload_after_general')
                    # Preserve this setup's moves in the lab boundary save,
                    # then observe the next setup with cleared general flags.
                    g.end_turn_proven(lambda:g.click(g.battle_x.get('end_turn',drv.BATTLE_TOOLS['end_turn']),drv.BATTLE_TOOLBAR_Y,pause=2))
                    record(g,mode,'same_process_reload_after_end_turn')
            elif mode in ('human_off','plain_off'):
                g.end_turn_proven(lambda:g.click(g.battle_x.get('end_turn',drv.BATTLE_TOOLS['end_turn']),drv.BATTLE_TOOLBAR_Y,pause=2))
                record(g,mode,'after_one_end_turn')
            if mode!='plain_off':read_hook(g,mode)
            preserve_series(g,mode)
            # Lab boundary files are the saved evidence. Do not open a strategic
            # File menu while the battle owns the UI (Escape can alter a battle).
        except BaseException as exc:
            log('failure',mode=mode,exception=repr(exc),windows=g.find_windows() if g.pid else [])
            # Retain any boundary files even if a UI step fails.
            if g.pid:preserve_series(g,mode+'-failed')
            raise
        finally:g.kill()
