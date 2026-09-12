"""Behavioral contracts for local Q4 experiments."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import sys
import numpy as np
import pytest

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path[:0]=[str(HERE),str(ROOT/'tests'),str(ROOT/'src'),str(ROOT/'simulator_automation'),
              str(ROOT/'experiments/q4_ablation')]

def module():
    assert importlib.util.find_spec('q4_local_policies') is not None,'local policies not implemented'
    import q4_local_policies
    return q4_local_policies


def test_mass_uses_spatial_weight_and_stays_inside_polygon():
    p=module()
    region=dict(center=np.zeros(2),rho=100.,verts=np.array([[-100.,-100.],[100.,-100.],[100.,100.],[-100.,100.]]))
    belief=SimpleNamespace(points=np.array([[50.,0.],[55.,0.],[60.,0.],[-50.,0.]]),weights=np.ones((4,1,1))/4)
    point,mass=p.mass_candidate(region,belief,[],np.zeros(2),[])
    assert mass==pytest.approx(.75)
    assert np.linalg.norm(point-[55.,0.])<=20
    assert p.inside_polygon(point,region['verts'])


def test_probe_budget_shared_across_same_stop_callbacks():
    p=module()
    from test_q4_regressions import NoisyGeomSim
    sources=[dict(k=k,g=np.array([400.,100.*k]),r=1500.,directional=False) for k in (1,2,3)]
    with p.cover_context(1950):
        runner=p.make_runner(NoisyGeomSim(sources,0),p.VARIANTS['P1'])
        for k in (1,2,3): runner.measure(0,0,k)
        runner.measure(200,0,20)
        runner._useful=lambda q,k:(.9,.8)
        runner._reception_belief=lambda k:SimpleNamespace(expected_gain=lambda q:1.)
        before=runner.n_measure
        runner._supplement(runner.state.pos.copy())
        runner._supplement(runner.state.pos.copy())
        assert runner.n_measure-before==1
        runner.measure(202,0,20)
        before=runner.n_measure
        runner._supplement(runner.state.pos.copy())
        runner._supplement(runner.state.pos.copy())
        assert runner.n_measure-before==1


@pytest.mark.parametrize('name',['L30','L90','P1','P2','F60','F120','C1','C15','M50','M75'])
def test_actual_executor_boundary_with_observation_only_api(name):
    p=module()
    from run_ablation import ObservableAPI
    from test_q4_regressions import NoisyGeomSim
    sources=[dict(k=1,g=np.array([1800.,0.]),r=1000.,directional=True,psi=0.),
             dict(k=3,g=np.array([350.,400.]),r=1100.,directional=True,psi=2.),
             dict(k=20,g=np.array([-900.,-450.]),r=1200.,directional=False,psi=0.)]
    with p.cover_context(1950):
        runner=p.make_runner(ObservableAPI(NoisyGeomSim(sources,11,'endpoint')),p.VARIANTS[name])
        result=runner.run()
    assert result['failure'] is None,result
    assert result['K']==3 and result['all_certified']
    assert all(ch.extra_measures<=8 for ch in runner.state.channels.values())
    assert runner.config.route=='tour' and runner.config.outer_radius==1950


def test_mass_failure_and_negative_history_do_not_reset_retry():
    p=module()
    from test_q4_regressions import NoisyGeomSim
    with p.cover_context(1950):
        runner=p.make_runner(NoisyGeomSim([],0),p.Config('test',mass_gate=.01))
        runner.state.apply_measure(1,[0.,0.],'direction',45.)
        runner.state.apply_measure(1,[2000.,0.],'direction',135.)
        q,kind=runner._adaptive_task(1)
        assert kind=='mass_clear'
        runner._do_v3_action(1,q,kind)
        assert runner.failed_clear_points[1]
        assert runner._adaptive_task(1)[1]!='mass_clear'
        runner.state.apply_measure(1,[90.,40.],'no_signal',None)
        assert runner._adaptive_task(1)[1]!='mass_clear'


def test_negative_initial_action_does_not_start_burst_and_optical_still_finishes():
    p=module()
    from test_q4_regressions import NoisyGeomSim
    class Shadow(NoisyGeomSim):
        def measure(self,x,y,k):
            r=super().measure(x,y,k)
            if (x,y)!=(0.,0.):
                r['measure_result']='no_signal';r.pop('svd_deg',None)
            return r
    with p.cover_context(1950):
        runner=p.make_runner(Shadow([dict(k=1,g=np.array([1230.,0.]),r=1500.,directional=False)],0),p.VARIANTS['F120'])
        runner.measure(0,0,1)
        runner._do_v3_action(1,np.array([80.,60.]),'measure')
        assert not [e for e in runner.log if e['op']=='local_burst_action']
        for _ in range(30):
            if runner.state.channels[1].cleared: break
            q,kind=runner._adaptive_task(1)
            if kind=='optical': runner._optical_fallback(1,runner._region(1))
            else: runner._do_v3_action(1,q,kind)
        assert runner.state.channels[1].cleared
        assert runner.state.channels[1].extra_measures==8


def test_failed_initial_clear_does_not_start_burst():
    p=module()
    from test_q4_regressions import NoisyGeomSim
    with p.cover_context(1950):
        runner=p.make_runner(NoisyGeomSim([],0),p.VARIANTS['F120'])
        runner.state.apply_measure(1,[0.,0.],'direction',45.)
        runner.state.apply_measure(1,[2000.,0.],'direction',135.)
        runner._do_v3_action(1,np.array([1000.,1000.]),'aggr_clear')
        assert runner.failed_clear_points[1]
        assert not [e for e in runner.log if e['op']=='local_burst_action']
