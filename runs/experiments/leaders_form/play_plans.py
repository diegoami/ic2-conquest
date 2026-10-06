"""The expected action sequence of each play, derived from the PLAY DEFINITIONS (scenarios.py, parsed as source, never imported and never read from a recording): the claims audit compares every recording's verified steps
with it, so a step relabelled, dropped or invented in a record fails. The meaning of each runner helper is written here once, from play_lib.py (what steps it records):
 open_form        reset, menu open file, menu item New  (+ confirm <answer> when a game with a human is running)
 set_tick/ticks   tick <Nation> on|off          edit_text      name <Nation>        try_edit_disabled   greyed name box <Nation> refuses typing
 press_button     press <OK|Cancel>             press_key_close  key <Escape|Return>  tab_walk  tab walk  focus_checkbox_by_tab  tab to <Nation> tick box   key_toggle  space on tick <Nation>
 menu_probe       reset, menu open <word>, menu close <word>    after_ok  close start boxes (only when humans were ticked)
Also derives the seeds of the New Games (the seed of the play, changed by g.set_seed) and whether a game with a human was running when New Game was chosen."""
import ast, os, re

NATIONS = ['Rome', 'Carthage', 'Seleucid', 'Ptolemaic', 'Macedonia', 'Numidia', 'Gaul', 'Greece', 'Celtiberia', 'Illyria', 'Dacia', 'Bithynia', 'Galatia', 'Armenia', 'Media', 'Thracia']
IGNORED = {'record_form', 'snap_rec', 'capture', 'sleep', 'set_seed', 'form_wid', 'basename', 'keep_memory', 'game_state', 'sha', 'DriverError', 'dict', 'len', 'list', 'range', 'sorted', 'open', 'read'}

class Plan:
    def __init__(self): self.steps = []; self.seeds = []; self.confirms = 0; self.humans = set(); self.running = False; self.seed = None; self.forms_opened = 0; self.untouched = []; self.dirty = True

def _eval(node, consts):
    """a literal argument: numbers, strings, lists, list(range(n)), a module constant"""
    if isinstance(node, ast.Name) and node.id in consts: return consts[node.id]
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'list' and isinstance(node.args[0], ast.Call) and node.args[0].func.id == 'range':
        return list(range(*[_eval(a, consts) for a in node.args[0].args]))
    if isinstance(node, ast.List): return [_eval(e, consts) for e in node.elts]
    return ast.literal_eval(node)

def parse(scenarios_path):
    src = open(scenarios_path, encoding='utf-8').read(); tree = ast.parse(src)
    consts = {}; fns = {}; sc = {}
    for n in tree.body:
        if isinstance(n, ast.FunctionDef): fns[n.name] = n
        if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name):
            if n.targets[0].id == 'SC' and isinstance(n.value, ast.Dict):
                for k, v in zip(n.value.keys, n.value.values):
                    kw = {x.arg: x.value for x in v.keywords}
                    sc[ast.literal_eval(k)] = {'seed': ast.literal_eval(kw['seed']), 'fn': kw['fn'].id}
            else:
                try: consts[n.targets[0].id] = ast.literal_eval(n.value)
                except Exception: pass
    return fns, sc, consts

def plan_of(scenarios_path, play):
    fns, sc, consts = parse(scenarios_path)
    if play not in sc: raise KeyError('play %s is not defined in scenarios.py' % play)
    pl = Plan(); pl.seed = sc[play]['seed']; pl.seed0 = pl.seed
    def run_fn(name):
        for st in fns[name].body: stmt(st)
    def call(c):
        f = c.func
        nm = f.id if isinstance(f, ast.Name) else f.attr if isinstance(f, ast.Attribute) else None
        args = c.args; kws = {k.arg: k.value for k in c.keywords}
        if nm == 'record_form':                                                          # a form read straight after it opened, before any tick, edit, key or press: an UNTOUCHED (default) form, whatever label the scenario gives it
            if not pl.dirty: pl.untouched.append(_eval(args[2], consts))
            return
        if nm in ('set_tick', 'ticks', 'edit_text', 'try_edit_disabled', 'press_button', 'press_key_close', 'tab_walk', 'focus_checkbox_by_tab', 'key_toggle', 'menu_probe'): pl.dirty = True
        if nm == 'set_seed': pl.seed = _eval(args[0], consts); return
        if nm == 'open_form':
            answer = _eval(kws['answer'], consts) if 'answer' in kws else 'Yes'
            pl.steps += ['reset', 'menu open file', 'menu item New']
            if pl.running:
                pl.steps.append('confirm %s' % answer); pl.confirms += 1
                if answer != 'Yes': return
            pl.seeds.append(pl.seed); pl.humans = set(); pl.running = False; pl.forms_opened += 1; pl.dirty = False; return
        if nm == 'set_tick':
            n = _eval(args[1], consts); want = _eval(args[2], consts)
            pl.steps.append('tick %s %s' % (NATIONS[n], 'on' if want else 'off')); (pl.humans.add if want else pl.humans.discard)(n); return
        if nm == 'ticks':
            for n in _eval(args[1], consts): pl.steps.append('tick %s on' % NATIONS[n]); pl.humans.add(n)
            return
        if nm == 'edit_text': pl.steps.append('name %s' % NATIONS[_eval(args[1], consts)]); return
        if nm == 'try_edit_disabled': pl.steps.append('greyed name box %s refuses typing' % NATIONS[_eval(args[1], consts)]); return
        if nm == 'press_button':
            b = _eval(args[1], consts); pl.steps.append('press %s' % b); pl.running = bool(pl.humans) if b == 'OK' else False
            if b != 'OK': pl.humans = set()
            return
        if nm == 'press_key_close':
            k = _eval(args[1], consts); pl.steps.append('key %s' % k); pl.running = bool(pl.humans) if k == 'Return' else False
            if k != 'Return': pl.humans = set()
            return
        if nm == 'tab_walk': pl.steps.append('tab walk'); return
        if nm == 'focus_checkbox_by_tab': pl.steps.append('tab to %s tick box' % NATIONS[_eval(args[1], consts)]); return
        if nm == 'key_toggle': n = _eval(args[1], consts); pl.steps.append('space on tick %s' % NATIONS[n]); pl.humans ^= {n}; return
        if nm == 'menu_probe':
            w = _eval(args[4], consts); pl.steps += ['reset', 'menu open %s' % w, 'menu close %s' % w]; return
        if nm == 'after_ok':
            if _eval(args[3], consts): pl.steps.append('close start boxes')
            return
        if nm in fns and nm not in ('ticks',): run_fn(nm); return
    class V(ast.NodeVisitor):
        def visit_Call(self, c):
            for a in list(c.args) + [k.value for k in c.keywords]: self.visit(a)
            call(c)
    def stmt(st):
        if isinstance(st, (ast.If, ast.Raise, ast.Pass)): return                      # `if form_wid(g): raise ...` guards: no step
        V().visit(st)
    run_fn(sc[play]['fn'])
    return pl

def plays(scenarios_path): return sorted(parse(scenarios_path)[1])
