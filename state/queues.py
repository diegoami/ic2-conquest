import struct, sys
def dat_queues(d):
    out=[]
    for n in range(16):
        r=0x1B100+n*0x41F
        name=d[r:r+11].split(b'\0')[0].decode('latin1')
        q=[struct.unpack_from('<4h',d,r+0x2C9+8*s) for s in range(40)]
        out.append((name,q))
    return out
def sav_queues(b):
    MAP,CITY=89600,11356
    na=struct.unpack_from('<H',b,MAP+CITY)[0]; f=MAP+CITY+2+na*656
    nf=struct.unpack_from('<H',b,f)[0]; nat=f+2+nf*26
    out=[]
    for n in range(16):
        r=nat+n*1172
        name=b[r:r+11].split(b'\0')[0].decode('latin1')
        q=[struct.unpack_from('<4h',b,r+0x2E4+8*s) for s in range(40)]
        out.append((name,q))
    return out
def live(q): return [(i,s) for i,s in enumerate(q) if s[2]>0]
if __name__=='__main__':
    for path in sys.argv[1:]:
        data=open(path,'rb').read()
        qs=dat_queues(data) if path.lower().endswith('.dat') else sav_queues(data)
        print('==',path.split('/')[-1])
        for n,(name,q) in enumerate(qs):
            L=live(q); print(f"{n:2} {name:12} slots={len(L):2} troops={sum(s[2] for i,s in L):6}", ' '.join(f"[{i}]st{s[0]}/ty{s[1]}/{s[2]}/c{s[3]}" for i,s in L))
