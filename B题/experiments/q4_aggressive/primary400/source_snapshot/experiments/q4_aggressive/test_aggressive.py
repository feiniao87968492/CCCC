"""Contract tests written before the aggressive policy implementation."""
from pathlib import Path
import sys
import numpy as np
import pytest

HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[1]
sys.path[:0]=[str(HERE),str(ROOT/'experiments/q4_local'),str(ROOT/'experiments/q4_transfer'),str(ROOT/'experiments/q4_ablation'),str(ROOT/'src'),str(ROOT/'simulator_automation')]

def policy():
    import q4_aggressive_policies as p
    return p

def test_family_registry_has_controls_and_all_six_families():
    p=policy(); names=set(p.VARIANTS)
    assert {'baseline','LC','LPC','previous_best'}.issubset(names)
    for family in ('E','B','G','R','H','N'):
        assert any(n.startswith(family) for n in names)

def test_optical_order_is_complete_and_never_empty_after_zero_mass():
    p=policy()
    cells=np.array([[0.,0.],[10.,0.],[20.,0.]])
    order,cost=p.expected_optical_order(cells,np.array([0.,0.,0.]),np.zeros(2),[])
    assert order==[0,1,2] and np.isfinite(cost) and cost>0
    assert sorted(order)==list(range(3))

def test_two_step_candidates_are_legal_and_finite():
    p=policy(); region={'center':np.zeros(2),'rho':100.,'verts':np.array([[-200.,-200.],[200.,-200.],[200.,200.],[-200.,200.]])}
    out=p.two_step_score(region,np.array([10.,0.]),np.zeros(2),np.array([50.,0.]),0.5)
    assert np.isfinite(out) and out>=0

def test_mass_trial_is_bounded_and_endpoint_state_guarded():
    p=policy(); assert p.FAMILY_CAPS['N']==2 and p.FAMILY_CAPS['H']==2
    assert p.endpoint_can_act('detected',False) and not p.endpoint_can_act('cleared',False)

def test_stale_endpoint_clear_is_idempotent():
    from types import SimpleNamespace
    p=policy()
    r=p.AggressiveRunner.__new__(p.AggressiveRunner)
    r.state=SimpleNamespace(channels={1:SimpleNamespace(status='cleared')})
    assert r._try_clear_at(1,np.zeros(2)) is True

@pytest.mark.parametrize('name',['E1','E2','B20','B60','G075','G15','R2','R4','H200','H400','N20','N50','ER','EN','ERN'])
def test_aggressive_arm_retains_local_route_and_radius(name):
    p=policy(); c=p.VARIANTS[name]
    assert c.route=='tour' and c.outer_radius==1950
