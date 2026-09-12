"""Protocol and completeness checks for the isolated paired Q3 experiment."""
import importlib
import sys
from pathlib import Path

import numpy as np
import pytest

EXP = Path(__file__).resolve().parents[1] / "experiments" / "q3_ablation"
sys.path.insert(0, str(EXP))


def modules():
    assert (EXP / "environment.py").exists(), "paired Q3 environment is missing"
    assert (EXP / "policies.py").exists(), "Q3 ablation policies are missing"
    return importlib.import_module("environment"), importlib.import_module("policies")


def test_receiver_channel_and_action_costs():
    env, _ = modules()
    sim = env.Q3Environment([dict(k=2, g=[100., 0.], r=1000.)], 0, "smooth")
    sim.enter()
    assert sim.measure(0, 0, 1)["virtual_time_s"] == 5
    assert sim.clear(0, 0, 2)["virtual_time_s"] == 8
    assert sim.measure(0, 0, 1)["virtual_time_s"] == 13
    assert sim.measure(0, 0, 2)["virtual_time_s"] == 19
    assert sim.clear(100, 0, 2)["virtual_time_s"] == 44
    assert sim.measure(100, 0, 2)["virtual_time_s"] == 49


@pytest.mark.parametrize("mode", ["smooth", "spatial", "endpoint"])
def test_noise_is_bounded_and_independent_of_action_order(mode):
    env, _ = modules()
    sources = [dict(k=2, g=[500., 50.], r=1000.)]
    a = env.Q3Environment(sources, 23, mode)
    b = env.Q3Environment(sources, 23, mode)
    a.enter()
    b.enter()
    b.measure(10, 10, 1)
    for x in [-100., 0., 200.]:
        ra = a.measure(x, 20, 2)
        rb = b.measure(x, 20, 2)
        assert ra["svd_deg"] == rb["svd_deg"]
        true = np.degrees(np.arctan2(30., 500. - x))
        err = (ra["svd_deg"] - true + 180) % 360 - 180
        assert abs(err) <= 1. + 1e-10


def test_compact_ring_analytic_and_dense_boundary_coverage():
    _, pol = modules()
    pts = pol.cover_points(1130.)
    bound = max(1130 / np.sqrt(3), np.sqrt(1800**2 + 1130**2
                - 2*1800*1130*np.cos(np.pi/6)))
    assert bound < 1000
    angles = np.linspace(0, 2*np.pi, 1081)
    targets = np.concatenate([r*np.c_[np.cos(angles), np.sin(angles)]
                              for r in np.linspace(0, 1800, 31)])
    assert np.linalg.norm(targets[:, None] - pts[None], axis=2).min(axis=1).max() < 1000


@pytest.mark.parametrize("variant", ["COMPACT", "J", "S", "O", "JS", "JO", "SO", "JSO", "JSO_ALLSCAN"])
def test_unknown_count_boundary_completion(variant):
    env, pol = modules()
    sources = [dict(k=1, g=[0., 0.], r=1000.),
               dict(k=20, g=[1800*np.cos(np.pi/6), 1800*np.sin(np.pi/6)], r=1000.)]
    sim = env.Q3Environment(sources, 5, "endpoint")
    runner = pol.make_runner(sim.client(), variant)
    result = runner.run()
    assert result["failure"] is None
    assert result["K"] == 2
    assert result["all_certified"]
    assert len(sim.cleared) == 2
    assert not hasattr(runner.robot, "sources")
    assert result["T"] == pytest.approx(sim.t)
    assert sim.t == pytest.approx(sim.move_m/5 + 5*sim.n_measure + sim.n_switch
                                 + 3*sim.n_clear + 2*len(sim.cleared))


def test_optimistic_failed_clear_retains_completion():
    env, pol = modules()
    sim = env.Q3Environment([dict(k=3, g=[900., 300.], r=1500.)], 11, "endpoint")
    runner = pol.make_runner(sim.client(), "O")
    result = runner.run()
    assert result["all_certified"] and result["K"] == 1
    assert not result["abandoned_channels"]


def test_absence_requires_each_compact_station_and_rejects_original_ring():
    env, pol = modules()
    sim = env.Q3Environment([], 1)
    runner = pol.make_runner(sim.client(), "COMPACT")
    runner.robot.enter()
    for p in pol.cover_points(1200):
        runner.measure(*p, 1)
    assert runner.state.channels[1].V == {0}
    assert runner.state.channels[1].status == "unseen"
    for p in pol.cover_points(1130)[:-1]:
        runner.measure(*p, 1)
        runner.measure(*p, 1)
    assert runner.state.channels[1].status == "unseen"
    runner.measure(*pol.cover_points(1130)[-1], 1)
    assert runner.state.channels[1].status == "certified_absent"


def test_baseline_is_actual_greedy_fast_and_no_truth_access_in_policy():
    import ast
    env, pol = modules()
    from q3_fast_mode import GreedyFastRunner
    original = pol.make_runner(env.Q3Environment([], 0).client(), "ORIGINAL")
    assert type(original) is GreedyFastRunner
    tree = ast.parse((EXP / "policies.py").read_text(encoding="utf-8"))
    assert not any(isinstance(node, ast.Attribute) and node.attr in
                   {"sources", "_sim", "cleared", "_noise"} for node in ast.walk(tree))
