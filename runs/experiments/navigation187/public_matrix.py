"""Generate portable semantic fixtures, not original raw RAM or full traces."""
import json
from pathlib import Path
DATA=Path(__file__).resolve().parents[3]/'runs/experiments/data/run-exp-navigation187'
fixtures=[
 dict(name='same-geographic-clear',default_cell=2,origin=[230,80],target=[240,90],patches=[],own_fleets=[],expected_eligible=True,expected_direct=True),
 dict(name='same-geographic-blocked',default_cell=2,origin=[230,80],target=[240,90],patches=[[235,85,0]],own_fleets=[],expected_eligible=True,expected_direct=False,expected_intermediate=[221,94]),
 dict(name='land-marker-does-not-block-line',default_cell=2,origin=[230,80],target=[240,90],patches=[[235,85,203]],expected_direct=True),
 dict(name='final-medium-not-tested',default_cell=2,origin=[230,80],target=[240,90],patches=[[240,90,0]],expected_direct=True),
 dict(name='cross-geographic-physically-clear',default_cell=2,origin=[100,40],target=[230,90],patches=[],own_fleets=[],expected_eligible=False,expected_direct=True),
 dict(name='cross-geographic-own-building-counts',default_cell=2,origin=[100,40],target=[230,90],patches=[],own_fleets=[dict(launched=False)],expected_eligible=True),
 dict(name='route-primary-beats-hub',group=1,candidates=[26,33],target_side_node=31,expected_node=26),
 dict(name='route-tie-first-candidate',group=1,candidates=[31,33],target_side_node=32,expected_node=31),
 dict(name='route-hub-fallback',group=1,candidates=[26,39],target_side_node=36,expected_node=39),
 dict(name='no-node-no-local-ray',default_cell=0,land_rectangles=[[229,231,79,81],[239,241,89,91]],origin=[230,80],target=[240,90],expected_eligible=True,expected_direct=False,expected_intermediate=None),
 dict(name='ferry-adjacent',origin=[100,40],target=[230,90],fleet=dict(owner='self',launched=True,moves=25,cargo=None,position=[101,40]),expected='embarked; both moves0, no waypoint'),
 dict(name='ferry-distant',origin=[98,40],target=[230,90],fleet=dict(owner='self',launched=True,moves=25,cargo=None,position=[105,40]),expected_army_approach=[100,40],expected_fleet_stored=[101,40]),
 dict(name='final-hostile-army-contact',origin=[100,40],target=[101,40],remaining_moves=8,relation=3,expected_dispatch='0044AEE4'),
 dict(name='final-hostile-army-no-budget',origin=[100,40],target=[101,40],remaining_moves=0,relation=3,expected_dispatch=None),
 dict(name='direct-blocked-wrapper-ABI',origin=[100,40],target=[110,40],friendly_blockers=[[101,39],[101,40],[101,41]],remaining_moves=8,
  expected_with_negative_inherited_guard=dict(position=[100,40],moves=8),expected_with_nonnegative_guard=dict(position=[100,41],moves=0),
  scope='Do not guess universal initialization; actual F31Ccaller context is separately proved nonnegative.')]
with (DATA/'public-test-matrix-v1.json').open('x') as f:json.dump(dict(fixtures=fixtures,coordinates='X,Y; inclusive land rectangles in these portable fixtures',
 ferry_geometry='land left throughX100, sea strip101..159, land right from160; actor/fleet markers consistent',
 use='Main regression inputs; semantic fixture descriptions, not complete original save images or accepted native AI claims'),f,indent=2)
print('Published15portable semantic regression fixtures')
