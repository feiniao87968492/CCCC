"""Safety contracts for isolated Q4 experimental policies."""
import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path[:0] = [str(HERE), str(ROOT / 'src'), str(ROOT / 'tests'),
               str(ROOT / 'simulator_automation')]


def implementation():
    assert importlib.util.find_spec('q4_ablation_policies') is not None, 'experimental policies missing'
    import q4_ablation_policies as policies
    return policies


def test_compact_cover_rejects_uncertified_radius_and_restores_baseline():
    p = implementation()
    import q4_cover
    original = q4_cover.cover_points('TRI25').copy()
    with p.cover_context(1900) as certificate:
        assert certificate['valid']
        assert certificate['hull_margin_m'] > 0
    np.testing.assert_array_equal(q4_cover.cover_points('TRI25'), original)
    with pytest.raises(ValueError):
        with p.cover_context(1750):
            pass
    np.testing.assert_array_equal(q4_cover.cover_points('TRI25'), original)


@pytest.mark.parametrize('variant', ['nearest', 'reuse', 'early160', 'full', 'probe_off',
                                   'early220', 'full_compact', 'every_stop'])
def test_outward_boundary_source_completes_without_truth_access(variant):
    p = implementation()
    from test_q4_regressions import NoisyGeomSim
    class APIOnly:
        def __init__(self, env):
            self._env = env
        @property
        def entered(self):
            return self._env.entered
        def enter(self):
            return self._env.enter()
        def exit(self):
            return self._env.exit()
        def measure(self, x, y, k):
            return self._env.measure(x, y, k)
        def clear(self, x, y, k):
            return self._env.clear(x, y, k)
    config = p.VARIANTS[variant]
    env = NoisyGeomSim([dict(k=1, g=np.array([1800., 0.]), r=1000.,
                            directional=True, psi=0.)], 42, 'endpoint')
    with p.cover_context(config.outer_radius):
        runner = p.make_runner(APIOnly(env), config)
        result = runner.run()
    assert result['failure'] is None, result
    assert result['K'] == 1 and result['all_certified']
    assert runner.state.channels[1].extra_measures <= 8
    assert result['T'] == pytest.approx(result['move_m']/5 + 5*result['n_measure']
                                        + sum(a[3] != b[3] for a,b in zip(
                                            [('measure',0,0,1)] + [e for e in env.calls if e[0]=='measure'],
                                            [e for e in env.calls if e[0]=='measure']))
                                        + 3*result['n_clear'] + 2*result['K'])


def test_all_off_is_exact_frozen_runner():
    p = implementation()
    from q4_runner import Q4Runner
    from test_q4_regressions import NoisyGeomSim, random_sources
    with p.cover_context(1950):
        runner = p.make_runner(NoisyGeomSim(random_sources(1000), 1000, 'endpoint'),
                               p.VARIANTS['baseline'])
        assert type(runner) is Q4Runner
        result = runner.run()
    import csv
    with (ROOT/'experiments/q4_efficiency/release_holdout100.csv').open() as f:
        expected = next(csv.DictReader(f))
    for key in ('T', 'T_over_K', 'move_m', 'n_measure', 'K'):
        assert result[key] == pytest.approx(float(expected[key]), abs=1e-8)


