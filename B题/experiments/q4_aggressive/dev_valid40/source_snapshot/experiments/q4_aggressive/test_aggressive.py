"""Behavioral acceptance for complete clearing, local costs and bounded callbacks."""
from pathlib import Path
from types import SimpleNamespace
import sys
import numpy as np
import pytest
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path[:0]=[str(HERE),str(ROOT/'tests'),str(ROOT/'experiments/q4_ablation')]
import q4_aggressive_policies as p
from test_q4_regressions import NoisyGeomSim
from run_ablation import ObservableAPI

def test_expected_optical_cost_counts_first_hits_and_uncovered_mass():
    cells=np.array([[0.,0.],[100.,0.]])
    points=np.array([[0.,0.],[100.,0.],[1000.,0.]])
    order,cost,full,reset=p.optical_plan(cells,points,[.5,.25,.25],np.zeros(2))
    assert order==[0,1] and not reset
    assert cost==pytest.approx(3+.5*23+2)
    assert full==pytest.approx(3+23+2)

def test_optical_order_can_choose_far_mass_first_and_keeps_all_cells():
    cells=np.array([[0.,0.],[40.,0.],[80.,0.]])
    order,cost,full,reset=p.optical_plan(cells,np.array([[80.,0.]]),[1.],np.zeros(2))
    assert order[0]==2 and sorted(order)==[0,1,2] and cost<full
    other=p.optical_plan(cells,np.array([[80.,0.]]),[1.],np.zeros(2),[[80.,0.]])
    assert sorted(other[0])==[0,1,2] and other[3]

def test_optical_executor_honors_order_and_finishes_when_belief_is_wrong():
    cells=np.array([[0.,0.],[40.,0.],[80.,0.]])
    with p.cover_context(1950):
        r=p.make_runner(ObservableAPI(NoisyGeomSim([],0)),p.VARIANTS['E1'])
        region={'center':np.array([40.,0.]),'rho':40.,'verts':np.array([[0.,-1.],[80.,-1.],[80.,1.],[0.,1.]])}
        r._optical_plan=lambda k,reg:(cells,p.optical_plan(cells,np.array([[80.,0.]]),[1.],r.state.pos))
        visits=[]
        r._try_clear_at=lambda k,q:visits.append(tuple(q)) is None and np.linalg.norm(q)<1e-7
        r._optical_fallback(1,region)
        assert visits[0]==(80.,0.) and visits[-1]==(0.,0.)
        assert len(visits)==3

def test_large_optical_cover_is_not_truncated(monkeypatch):
    cells=np.c_[np.arange(257)*30.,np.zeros(257)]
    calls=[]
    monkeypatch.setattr(p,'optical_cover_points',lambda v:cells)
    monkeypatch.setattr(p.base.LocalRunner,'_optical_fallback',lambda *a:calls.append('full_fallback'))
    with p.cover_context(1950):
        r=p.make_runner(ObservableAPI(NoisyGeomSim([],0)),p.VARIANTS['E1'])
        r._optical_fallback(1,{'verts':cells})
    assert calls==['full_fallback']

def test_early_e_threshold_uses_expected_rf_cost_and_certified_priority():
    with p.cover_context(1950):
        r=p.make_runner(ObservableAPI(NoisyGeomSim([],0)),p.VARIANTS['E1'])
        r.state.apply_measure(1,[0.,0.],'direction',45.)
        r.state.apply_measure(1,[2000.,0.],'direction',135.)
        r._optical_plan=lambda k,reg:(np.zeros((1,2)),([0],1e8,1e8,False))
        assert r._adaptive_task(1)[1]!='optical'
        r._optical_plan=lambda k,reg:(np.zeros((1,2)),([0],0.,1e8,False))
        assert r._adaptive_task(1)[1]=='optical'

def test_continuation_uses_predicted_radius_and_handles_coincident_points():
    q=np.zeros(2);pts=np.array([[100.,0.],[0.,0.]])
    costs=p.continuation_cost(pts,q,np.array([10.,80.]))
    assert costs[0]==pytest.approx(25.) and np.isfinite(costs).all()
    assert p.continuation_cost(pts[:1],q,np.array([100.]))[0]>costs[0]

def test_already_cleared_source_has_no_second_physical_clear():
    source=dict(k=1,g=np.array([10.,0.]),r=1200.,directional=False)
    with p.cover_context(1950):
        r=p.make_runner(ObservableAPI(NoisyGeomSim([source],0)),p.VARIANTS['N20'])
        r.measure(0,0,1);assert r.clear(10,0,1)
        count=len(r.log);assert r.clear(10,0,1) and r._try_clear_at(1,np.array([10.,0.]))
        assert len(r.log)==count and r.state.channels[1].status=='cleared'

def test_g_budget_shared_across_callbacks_and_resets_only_on_real_move():
    sources=[dict(k=k,g=np.array([400.,100.*k]),r=1500.,directional=False) for k in (1,2,3,4)]
    with p.cover_context(1950):
        r=p.make_runner(ObservableAPI(NoisyGeomSim(sources,0)),p.VARIANTS['G075'])
        for k in (1,2,3,4):r.measure(0,0,k)
        r.measure(200,0,20)
        r._g_admission=lambda q,k:dict(score=2.,gain=2.,rho=200.,probability=.9,charge=5+int(r.measure_channel!=k),parallax_sine=.8)
        before=r.n_measure;r._endpoint(r.state.pos.copy());r._endpoint(r.state.pos.copy())
        assert r.n_measure-before==3
        r.measure(200.5,0,20);before=r.n_measure;r._endpoint(r.state.pos.copy());assert r.n_measure==before
        r.measure(202,0,20);before=r.n_measure;r._endpoint(r.state.pos.copy());assert r.n_measure-before==3

def test_g_formula_uses_saved_travel_and_actual_switch():
    with p.cover_context(1950):
        r=p.make_runner(ObservableAPI(NoisyGeomSim([],0)),p.VARIANTS['G075'])
        r.state.apply_measure(1,[0.,0.],'direction',0.)
        r._region=lambda k:dict(rho=200.,center=np.array([400.,0.]))
        r._reception_belief=lambda k:SimpleNamespace(reception_probability=lambda q:.8,expected_gain=lambda q:1.)
        r.measure_channel=1;a=r._g_admission(np.array([200.,100.]),1)
        r.measure_channel=2;b=r._g_admission(np.array([200.,100.]),1)
        assert a['score']==pytest.approx(200*(1-np.exp(-1))/25)
        assert b['score']==pytest.approx(a['score']*5/6)

def test_n_failed_trial_and_negative_do_not_renew_permission():
    with p.cover_context(1950):
        r=p.make_runner(ObservableAPI(NoisyGeomSim([],0)),p.VARIANTS['N20'])
        r.state.apply_measure(1,[0.,0.],'direction',45.)
        r.state.apply_measure(1,[2000.,0.],'direction',135.)
        r.state.pos=np.array([1000.,1000.])
        r._reception_belief=lambda k:SimpleNamespace(points=r.state.pos[None,:],weights=np.ones((1,1,1)))
        r._endpoint(r.state.pos.copy());assert len(r._n_versions[1])==1
        r.state.apply_measure(1,[90.,40.],'no_signal',None)
        r._endpoint(r.state.pos.copy());assert len(r._n_versions[1])==1
        assert sum(e['op']=='endpoint_clear_attempt' for e in r.log)==1

@pytest.mark.parametrize('name',[n for n in p.VARIANTS if n not in ('baseline','LC','LPC','previous_best')])
def test_all_arms_finish_observation_only_boundary_scene(name):
    sources=[dict(k=1,g=np.array([1800.,0.]),r=1000.,directional=True,psi=0.),
             dict(k=3,g=np.array([350.,400.]),r=1100.,directional=True,psi=2.),
             dict(k=20,g=np.array([-900.,-450.]),r=1200.,directional=False,psi=0.)]
    with p.cover_context(1950):
        r=p.make_runner(ObservableAPI(NoisyGeomSim(sources,11,'endpoint')),p.VARIANTS[name]);result=r.run()
    assert result['failure'] is None and result['K']==3 and result['all_certified']
    assert all(ch.extra_measures<=8 for ch in r.state.channels.values())
    assert r.config.route=='tour' and r.config.outer_radius==1950
