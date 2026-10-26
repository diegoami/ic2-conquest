"""Fresh original process per retained result. Read original saves, write NEW saves.
No original input or measurement overwritten; full evidence/hashes private.
"""
from run import *
CASES=[dict(id='change-regular-empty',batch='cd218-pilot-v1',case='carried-change-last-ok'),dict(id='change-merc-empty',batch='cd218-controls-v2',case='carried-change-merc-no-city'),dict(id='transfer-deleted',batch='cd218-controls-v2',case='carried-transfer-disband-ok')]
def execute(case,g,private,stem):
 r=json.load(open(DATA/(case['batch']+'_'+case['case']+'.json')))
 source=ART/('private-'+case['batch'])/r['after_save']
 g.open(source);state=observed(g);g.shot(private/(stem+'-loaded.png'));output=c.save(g,private,stem,'cold_saved')
 row=dict(case=case,turn=734,input_save=source.name,output_save=output.name,process_fresh=True,state=state,summary=dict(owner=state['armies']['0']['owner'],troops=state['armies']['0']['troops'],link=state['carrier']['army']))
 c.public_row(stem,row)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--version',required=True);q=p.parse_args();write_new(DATA/(q.version+'-matrix.json'),CASES)
 assert (drv.G/'Imperial Conquest 2.exe').read_bytes()==Path('/home/diego/ic2-work/build/Imperial Conquest 2.exe').read_bytes()
 for k,case in enumerate(CASES):c.session(q.version+f'-c{k:02d}',execute,[case])
