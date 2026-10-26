"""GUI81: initial selection, queues/list-order controls, real recruitment."""
from common import *
import argparse
CASES=[dict(id=label,queues=queues,reorder=reorder) for label,queues,reorder in [('no-queue',[],True),('capital-only',[(85,2000)],True),('noncapital-only',[(80,2000)],True),('two-unequal',[(80,2000),(85,2000),(85,2000)],True),('two-tied',[(80,2000),(85,2000)],True),('two-tied-slots-reversed',[(85,2000),(80,2000)],True)]]
def execute(c,g,private,stem):
 b=new_bytes();a,f,n=offsets(b);b[n+0x2e4:n+0x424]=bytes(320)
 # Qualification and city list place a noncapital before the capital, varying queue order separately.
 put(b,sav.CITY_OFF+80*34+26,78)
 ids=sav.parse(b)['nations'][0]['city_list'];ids=[80]+[i for i in ids if i!=80]
 for j,cid in enumerate(ids):put(b,n+0x48+j*2,cid)
 for k,(cid,num) in enumerate(c['queues']):struct.pack_into('<4h',b,n+0x2e4+8*k,24,0,num,cid)
 put(b,n+0x442,0)
 g.open(staged(b,private,stem));before=save(g,private,stem,'before')
 title='Recruit unit';g.tool('recruit');g.wait(lambda:g.find_windows('^Recruit unit$'),8,'Recruit unit');time.sleep(.5);cs=inspect(title)
 form=None
 # Form-global pointer located in TPremierForm_RecruitUnit at45b2xx via source; visible list is primary observation.
 opened=list_rows(title);g.shot(private/(stem+'-open.png'))
 write_new(private/(stem+'-controls.json'),cs)
 g.close_controls(title,cs)
 g.tool('recruit');g.wait(lambda:g.find_windows('^Recruit unit$'),8,'Recruit unit');reopened=list_rows(title);cs=inspect(title)
 manual_reopen=None
 cities=next((x for x in sorted(reopened,key=lambda x:x['y']) if x['rows'] and x['y']<200),None)
 if cities and cities['count']>1:
  citylist=next(x for x in cs if x['cls']=='TListBox' and x['x']==cities['x'] and x['y']==cities['y'])
  g.click_list_row(citylist,0 if cities['selected']!=0 else 1,pause=.3)
  g.close_controls(title,cs);g.tool('recruit');g.wait(lambda:g.find_windows('^Recruit unit$'),8,'Recruit unit')
  manual_reopen=list_rows(title);cs=inspect(title)
 # Choose LI through existing controls; source default minimum kept (no Max policy changes).
 buttons=[x for x in cs if x['cls']=='TButton'];li=next((x for x in buttons if 'Light infantry' in x['text'] or 'Lit inf' in x['text']),None)
 if li:g.click_control(li,pause=.3)
 recruit=next((x for x in cs if x['text'] in ['Recruit unit','Create unit']),None)
 if recruit:g.click_control(recruit,pause=.6);boxes=g.dismiss_popups()
 else:boxes=['runner: recruitment button unresolved; no recruitment attempted']
 afterclick=list_rows(title);g.close_controls(title,inspect(title));after=save(g,private,stem,'after')
 s0=sav.load(before);s1=sav.load(after)
 public_row(stem,dict(case=c,turn=734,before_save=before.name,after_save=after.name,opened=opened,reopened=reopened,afterclick=afterclick,manual_reopen=manual_reopen,boxes=boxes,queues_before=s0['nations'][0]['recruit_slots'],queues_after=s1['nations'][0]['recruit_slots'],summary=dict(opened=opened,reopened=reopened,boxes=boxes)))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--version',required=True);p.add_argument('--cases',nargs='*');q=p.parse_args();session(q.version,execute,[c for c in CASES if not q.cases or c['id'] in q.cases])
