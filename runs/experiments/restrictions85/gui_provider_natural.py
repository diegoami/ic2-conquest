"""GUI78: fixed classical coast/cities, vary fleet IDs/order and city stocks.
No city coordinates/terrain edits. Synthetic Roman army/fleets relocated onto
existing vacant land/sea, relations set to peace. See common evidence rules.
"""
from common import *
import argparse
CASES=[dict(id='natural-'+label,fleet_ids=fids,stocks=stocks) for label,fids,stocks in [('two-fleets',[2,5],[90,10]),('four-fleets',[2,5,0,1],[90,10]),('four-fleets-id-order-reversed',[5,2,1,0],[10,90])]]
def snap(g):
 s=snapshot(g);s['cities']={str(i):g.i16(0x479590+i*34+24) for i in [72,76]};s['all_fleets']={str(i):g.fleet_state(i) for i in [0,1,2,5]};return s

def execute(c,g,private,stem):
 b=new_bytes();a,f,n=offsets(b);army_units(b,0,[10000]);ox,oy=sav.i16(b,a),sav.i16(b,a+2);put(b,(ox*140+oy)*2,sav.i16(b,a+8));assert sav.i16(b,(94*140+77)*2) in range(2,12)
 put(b,a,94);put(b,a+2,77);put(b,a+8,sav.i16(b,(94*140+77)*2));put(b,(94*140+77)*2,200);put(b,a+10,0);put(b,a+12,100)
 # Clear old positions before staging any new fleet marker.
 for fid in c['fleet_ids']:
  off=f+fid*26;x,y=sav.i16(b,off),sav.i16(b,off+2);put(b,(x*140+y)*2,sav.i16(b,off+24))
 for k,(fid,(x,y)) in enumerate(zip(c['fleet_ids'],[(93,76),(93,77),(94,76),(95,76)])):
  off=f+fid*26;old=sav.i16(b,(x*140+y)*2);assert old in [0,1]
  put(b,off,x);put(b,off+2,y);put(b,off+8,0);put(b,off+14,100+20*k);put(b,off+16,200+20*k);put(b,off+24,old);put(b,(x*140+y)*2,300)
 for cid,stock in zip([72,76],c['stocks']):put(b,sav.CITY_OFF+cid*34+24,stock)
 put(b,n+0x26+2,0);put(b,n+1172+0x26,0)
 g.open(staged(b,private,stem));before=save(g,private,stem,'before');s0=snap(g);g.army_tool(0,'supply','Supply army');title='Supply army';cs=inspect(title);lst=g.control(cs,cls='TListBox');form=struct.unpack('<I',g.mem(0x45e71c,4))[0];events=[]
 for k in range(lst['count']):
  if k:lst=click_any_row(g,title,lst,k)
  fields=list(struct.unpack('<9h',g.mem(form+0x27e,18)));cs=inspect(title)
  events.append(dict(row=k,phase='selected',fields=fields,lists=list_rows(title),state=snap(g)))
  write_new(DATA/(stem+f'-selected-row{k}.json'),events[-1])
  if fields[5]<0 and fields[6]<0:
   events.append(dict(row=k,phase='invalid-provider-not-transferred'));continue
  ups=sorted([x for x in cs if x['cls']=='TUpDown' and x['visible']],key=lambda x:(x['y'],x['x']))
  arrow(g,title,ups[0],1)
  if fields[5]>=0:g.click_control(g.control(cs,text='Buy supplies'),pause=.4)
  events.append(dict(row=k,phase='transfer10',state=snap(g)))
  write_new(DATA/(stem+f'-transfer-row{k}.json'),events[-1])
 g.shot(private/(stem+'-dialog.png'));g.close_controls(title,cs);after=save(g,private,stem,'after');s1=snap(g)
 public_row(stem,dict(case=c,turn=734,before_save=before.name,after_save=after.name,before=s0,after=s1,events=events,summary=dict(rows=[e['lists'][0]['rows'] for e in events if 'lists'in e],fields=[e['fields'] for e in events if 'fields'in e],army_supply=s1['armies']['0']['supplies'],city_stocks=s1['cities'],fleet_stocks={k:v['supplies'] for k,v in s1['all_fleets'].items()})))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--version',required=True);p.add_argument('--cases',nargs='*');q=p.parse_args();session(q.version,execute,[c for c in CASES if not q.cases or c['id'] in q.cases])
