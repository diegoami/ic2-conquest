"""Deterministic public synthetic caller inputs; no execution at import."""
import struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'runs/experiments/navigation187'))
import core as C
ACTOR=2;ARMY=0x47c1ec+ACTOR*656
def fixture(context,blocked):
 r=C.fresh_map();C.put(r,0x4a0324,5)
 # Distinct, in-bounds generated city coordinates, away from the test corridor.
 for i in range(334):
  address=0x479590+i*34;x,y=260+i%50,100+i//50
  C.put(r,address+14,x);C.put(r,address+16,y);C.setcell(r,(x,y),20+C.short(r,address+18))
 for i in range(5):C.put(r,0x47c1ec+i*656+4,-1);C.put(r,0x47c1ec+i*656+6,0)
 target=(110,40) if context=='mercenary' else (120,40)
 for city,pos in [(0,target),(1,(200,100))]:
  address=0x479590+city*34
  C.put(r,address+14,pos[0]);C.put(r,address+16,pos[1]);C.put(r,address+18,1);C.setcell(r,pos,21)
 C.place_army(r,ACTOR,(100,40),1);C.put(r,ARMY+6,8)
 for i,pos in zip([0,1,3],[(101,39),(101,40),(101,41)]):
  C.place_army(r,i,pos if blocked else (50+i,20),1);C.put(r,0x47c1ec+i*656+6,0)
 C.put(r,0x474670+1172+0x444,0 if context=='garrison-capital' else 1)
 if context=='garrison-nearest':C.place_army(r,4,(200,100),1);C.put(r,0x47c1ec+4*656+6,0)
 # One eligible generated mercenary at the target city, none elsewhere.
 for i in range(50):C.put(r,0x49da10+i*12+8,-1)
 if context=='mercenary':
  for off,value in [(0,target[0]),(2,target[1]),(4,0),(6,7),(8,1000),(10,1)]:C.put(r,0x49da10+off,value)
  C.put(r,0x474670+1172+0x26+2,0)
 return bytes(r),target

def parent_fixture(context,blocked):
 raw,target=fixture(context,blocked);r=bytearray(raw)
 # The parent must reach these helpers naturally. No call/decision is stubbed.
 for n in range(16):
  for j in range(16):C.put(r,0x474670+n*1172+0x26+j*2,0)
 r[0x4a0b7c-C.ORIGIN]=0
 for i in range(334):C.put(r,0x479590+i*34+24,0)
 # One remote own stocked provider across the coordinate partition. The direct
 # line has a sea cell; no fleet exists, so the initial resupply request refuses
 # without spending moves. Garrison fallback can then be entered naturally.
 city=0x479590+2*34
 for off,value in [(14,230),(16,80),(18,1),(24,1000)]:C.put(r,city+off,value)
 C.setcell(r,(230,80),21)
 import model as M
 C.setcell(r,list(M.line((100,40),(230,80)))[30],0)
 C.put(r,ARMY+10,2000)
 troops=sum(C.short(r,ARMY+16+i*32+4) for i in range(20))
 full=10-min(5,troops//20000)
 if ((2000*troops)//10000)&65535<10:full-=1
 C.put(r,ARMY+6,full)
 if context=='mercenary':
  # A legal but unattractive hostile-city target opens the mercenary-run branch.
  city=0x479590+3*34
  for off,value in [(14,130),(16,40),(18,3),(20,3),(22,100),(26,100),(28,500)]:C.put(r,city+off,value)
  C.setcell(r,(130,40),23)
  C.put(r,0x474670+3*1172+0x444,4)
  for a,b in [(1,3),(3,1)]:C.put(r,0x474670+a*1172+0x26+b*2,3)
 return bytes(r),target
