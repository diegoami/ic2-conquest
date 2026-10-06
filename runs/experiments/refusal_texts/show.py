import sys,re,sites
L=sites.load(); fn=sites.functions(L)
for n in sys.argv[1:]:
    v=fn[n]
    for i in range(v[0],v[-1]+1):
        if L[i].strip() and not re.match(r'\s*(undefined|short|int|uint|ushort|bool|char|byte|undefined\d) [\*\w]+( = [^;]*)?;$',L[i]): print('%d\t%s'%(i+1,L[i]))
