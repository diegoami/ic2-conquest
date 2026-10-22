"""Case3 continuation after retained Python binding failure; no new turn/order."""
from remaining_cases import *

def resume():
 prefix='case3';case=3;c=CASES[case];n=c['nation']
 # Prior attempt completed normal close, fresh launch/open and scalar read.
 failed=dict(error="NameError: n was not defined in extracted finish_after_turn",stage='after fresh reopen scalar read, before new save',game_error=False,retained_action_logs=True)
 record('case3-continuation-failure-v1',failed)
 launchlog=json.loads((DATA/'case3-reopen-launch-v1.json').read_text());fresh=json.loads(launchlog['stdout'])['pid']
 w=rows(fresh,'case3-reopen-resume-windows-v1');main=top(w,'TPremierForm');sc=action(fresh,'snapshot','case3-reopen-resume-scalars-v1')
 endlog=json.loads((DATA/'case3-endturn-effect-v1.json').read_text());post=endlog['scalars']
 assert all(sc[k]==post[k] for k in ['current','tax','year','season','week','armies','fleets','offer_source'])
 capture(fresh,top(w,'TInformation'),'N3INF003.PNG','case3-reopen-info-capture-v1')
 reopened=save_as(fresh,main,'N3R68B2.SAV','case3-reopen-save-v1')
 a=(PRIVATE/'N3E68B2.SAV').read_bytes();b=(PRIVATE/'N3R68B2.SAV').read_bytes();assert a==b
 close(fresh,main,'case3-final-normal-close-v1','N3EX02.PNG')
 sh=hashlib.sha256((SOURCE/c['source']).read_bytes()).hexdigest();ch=hashlib.sha256((CAND/c['candidate']).read_bytes()).hexdigest();assert sh==c['source_sha'] and ch==c['candidate_sha']
 order=json.loads((DATA/'case3-order-effect-v1.json').read_text());ctx=json.loads((DATA/'case3-active-context-v1.json').read_text())
 result=dict(case=3,original_open_order_AND_endturn_newsave_normalclose_freshreopen_sequence='PASS observed',initial_pid=ctx['pid'],fresh_reopen_pid=fresh,order=order['queue_changes'],economy=order['economy'],endturn_commands_issued=1,original_endturn_confirmation=dict(observed='An army of yours needs supplies.',button='End turn',confirmations=1),postturn_scalars=post,fresh_reopen_scalars=sc,reopen_file=reopened,reopen_exact_postturn_byte_identity=True,reopen_only_geometry_changed_offsets=[],source_sha256=sh,candidate_sha256=ch,source_candidate_unchanged=True,final_active_original_processes=0,internal_callback_instruction_trace='UNVERIFIED',twelve_native_JSON_conversion_target='UNMET/separate',automation_failure_recovered=failed)
 record('case3-completion-v1',result);print(json.dumps(result))
if __name__=='__main__':resume()
