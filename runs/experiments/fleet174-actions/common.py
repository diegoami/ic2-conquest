"""Pinned original CPU/projector helpers. No original game helper is replaced."""
import hashlib,struct,sys
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT));from state import sav
RAM_BASE=0x45e000;RAM_SIZE=0x43000
BASE=ROOT/'artifacts/run-exp-fleet-actions174';DATA=ROOT/'runs/experiments/data/run-exp-fleet-actions174'
OLD=ROOT/'artifacts/run-exp-strategic-fleet/controls-v1'
EXE=Path('/home/diego/ic2-work/build/Imperial Conquest 2.exe').read_bytes()
assert hashlib.sha256(EXE).hexdigest()=='9d753d5de78801f2368d06125cc87f296b92f671b686c39fd6ac149838ebba31'
pe=struct.unpack_from('<I',EXE,0x3c)[0];n,opt=struct.unpack_from('<H',EXE,pe+6)[0],struct.unpack_from('<H',EXE,pe+20)[0];SECTIONS=[]
for k in range(n):
 o=pe+24+opt+40*k;vs,va,rs,rp=struct.unpack_from('<4I',EXE,o+8);SECTIONS.append((0x400000+va,rp,rs))
TEMPLATE=next((ROOT/'artifacts/run-exp-strategic-fidelity/original/N-rome-hook-v1').glob('*-before.SAV')).read_bytes();PARSED=sav.parse(TEMPLATE)
def read(ram,address,size):return ram[address-RAM_BASE:address-RAM_BASE+size]
def short(ram,address):return struct.unpack('<h',read(ram,address,2))[0]
def put(ram,address,value):struct.pack_into('<h',ram,address-RAM_BASE,value)
def xy(ram,address):return list(struct.unpack('<2h',read(ram,address,4)))
def cell(ram,x,y):return short(ram,0x45e870+2*(x*140+y))
def project(ram):
 na,nf=short(ram,0x4a0324),short(ram,0x4a0326)
 b=read(ram,0x45e870,89600)+read(ram,0x479590,11356)+struct.pack('<h',na)+read(ram,0x47c1ec,na*656)
 b+=struct.pack('<h',nf)+read(ram,0x49c26c,nf*26)+read(ram,0x474670,18752)+read(ram,0x49da10,600)
 news=100958+len(PARSED['armies'])*656+2+len(PARSED['fleets'])*26+18752+600
 tail=bytearray(TEMPLATE[PARSED['tail_off']:PARSED['tail_off']+55])
 for off,address in [(36,0x4a0320),(38,0x4a0322),(40,0x4a0330),(42,0x4a0332),(44,0x4a032e)]:struct.pack_into('<h',tail,off,short(ram,address))
 tail[54]=0
 return b+TEMPLATE[news:PARSED['tail_off']]+tail
def machine(ram):
 u=Uc(UC_ARCH_X86,UC_MODE_32);u.mem_map(0x400000,0x300000);u.mem_map(0x800000,0x10000)
 for va,rp,rs in SECTIONS:
  if rs:u.mem_write(va,EXE[rp:rp+rs])
 u.mem_write(RAM_BASE,bytes(ram));return u
