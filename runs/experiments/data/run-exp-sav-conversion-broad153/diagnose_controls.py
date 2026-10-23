"""One read-only UI setup to verify caption decoding and actual button geometry."""
import hashlib,json,subprocess
import live

name='control-diagnostic-v2';out=live.HERE/(name+'.json')
if out.exists():raise SystemExit('Existing diagnostic preserved')
g=live.IsolatedGame(exe='Imperial Conquest 2.exe',log=lambda s:None)
result={}
try:
    g.start();g.open(live.ART/'exports-v1/F11-recruit-li.SAV')
    g.open_recruit();cs=g.controls('Army recruits');c=g.control(cs,cls='TListBox',index=0)
    query=subprocess.run([live.WINE,str(live.ART/'runtime/list_items.exe'),'Army recruits',str(c['x'])],env=live.ENV,capture_output=True,text=True,check=True)
    result['recruit_controls']=cs;result['captions']=query.stdout;result['helper_diagnostic']=query.stderr
    assert '\tROME\n' in query.stdout or '\tRome\n' in query.stdout
    g.close_controls('Army recruits',cs)
    g.army_tool(0,'supply','Supply army');cs=g.controls('Supply army');result['supply_controls']=cs
    ok=g.control(cs,text='OK');g.click_control(ok,pause=.6);g.wait(lambda:not g.find_windows('^Supply army$'),10,'Supply army close')
    result['supply_control_close_passed']=True
    result['helper_sha256']=hashlib.sha256((live.ART/'runtime/list_items.exe').read_bytes()).hexdigest()
finally:
    g.kill()
    if live.display is not None:live.display.terminate();live.display.wait(timeout=10)
    with out.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print('Caption and control-close diagnostic passed')
