"""Independent geometric and end-to-end contracts for Q4 transfer policies."""
import importlib.util
from pathlib import Path
import sys

import numpy as np
import pytest

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path[:0]=[str(HERE),str(ROOT/'src'),str(ROOT/'simulator_automation'),str(ROOT/'tests')]


def module():
    assert importlib.util.find_spec('q4_transfer_policies') is not None, 'Q4 transfer policies not implemented'
    import q4_transfer_policies as p
    return p


def test_ls_intersection_rejects_parallel_and_respects_region():
    p=module()
    history=[dict(pos=np.array([0.,0.]),svd=45.,result='direction'),
             dict(pos=np.array([200.,0.]),svd=135.,result='direction')]
    region=dict(verts=np.array([[95.,95.],[105.,95.],[105.,105.],[95.,105.]]))
    np.testing.assert_allclose(p.line_estimate(history,region),[100.,100.],atol=1e-7)
    history[1]['svd']=45.
    assert p.line_estimate(history,region) is None
    history[1]['svd']=120.
    assert p.line_estimate(history,region) is None


def test_certified_shortcut_covers_all_vertices():
    p=module()
    region=dict(center=np.array([300.,200.]),rho=10.,
                verts=np.array([[290.,200.],[300.,210.],[310.,200.],[300.,190.]]))
    q=p.short_clear_point(region,np.zeros(2))
    assert np.linalg.norm(q)<np.linalg.norm(region['center'])
    assert np.max(np.linalg.norm(region['verts']-q,axis=1))<20.


@pytest.mark.parametrize('name',['J','S','O','JSO','insert80','insert200','aligned',
                               'doptimal','bracket','optical2','optical4','short_clear',
                               'S_doptimal','SO_doptimal','S_dopt_short','JSO_compact_dopt'])
def test_boundary_and_failure_recovery_with_observation_only_api(name):
    p=module()
    from test_q4_regressions import NoisyGeomSim
    class Client:
        def __init__(self,env): self._env=env
        @property
        def entered(self): return self._env.entered
        def enter(self): return self._env.enter()
        def exit(self): return self._env.exit()
        def measure(self,*args): return self._env.measure(*args)
        def clear(self,*args): return self._env.clear(*args)
    sources=[dict(k=1,g=np.array([1800.,0.]),r=1000.,directional=True,psi=0.),
             dict(k=3,g=np.array([300.,400.]),r=1100.,directional=True,psi=2.),
             dict(k=20,g=np.array([-900.,-450.]),r=1200.,directional=False,psi=0.)]
    with p.cover_context(p.VARIANTS[name].outer_radius):
        runner=p.make_runner(Client(NoisyGeomSim(sources,7,'endpoint')),p.VARIANTS[name])
        r=runner.run()
    assert r['failure'] is None,r
    assert r['K']==3 and r['all_certified'],r
    assert all(ch.extra_measures<=8 for ch in runner.state.channels.values())
    assert r['T']>r['move_m']/5+5*r['n_measure']


def test_optimistic_clear_failure_forces_new_positive_before_retry():
    p=module()
    from test_q4_regressions import NoisyGeomSim
    with p.cover_context(1950):
        runner=p.make_runner(NoisyGeomSim([],0),p.VARIANTS['O'])
        runner.state.apply_measure(1,[0.,0.],'direction',45.)
        runner.state.apply_measure(1,[2000.,0.],'direction',135.)
        q,kind=runner._adaptive_task(1)
        assert kind=='aggr_clear'
        runner._do_v3_action(1,q,kind)
        assert runner.failed_clear_points[1]
        q2,kind2=runner._adaptive_task(1)
        assert kind2 in ('measure','optical')
        runner.state.apply_measure(1,[90.,40.],'no_signal',None)
        assert runner._adaptive_task(1)[1] in ('measure','optical')


def test_sparse_positive_history_keeps_certified_optical_fallback():
    p=module()
    from test_q4_regressions import NoisyGeomSim
    class Shadow(NoisyGeomSim):
        def measure(self,x,y,k):
            r=super().measure(x,y,k)
            if (x,y)!=(0.,0.):
                r['measure_result']='no_signal';r.pop('svd_deg',None)
            return r
    with p.cover_context(1950):
        runner=p.make_runner(Shadow([dict(k=1,g=np.array([1230.,0.]),r=1500.,directional=False)],0),p.VARIANTS['JSO'])
        runner.measure(0.,0.,1)
        # Exercise the actual V4 adaptive action path used in the experiment.
        for _ in range(30):
            if runner.state.channels[1].cleared:
                break
            q,kind=runner._adaptive_task(1)
            if kind=='optical':
                runner._optical_fallback(1,runner._region(1))
            else:
                runner._do_v3_action(1,q,kind)
        assert runner.state.channels[1].cleared
        assert runner.state.channels[1].extra_measures<=8
