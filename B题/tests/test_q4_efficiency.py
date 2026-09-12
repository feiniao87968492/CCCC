"""Continuous discovery, bounded routing, and observation-only adaptive probes."""
import sys
from itertools import permutations
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "simulator_automation"), str(ROOT / "tests")]
import q4_cover
import q4_policy
from q4_runner import Q4Runner
from test_q4_regressions import NoisyGeomSim


def test_tri25_has_a_continuous_discovery_certificate():
    assert hasattr(q4_cover, "COVER_TRI25"), "37-point discovery can be replaced with a certified 25-point cover"
    from q4_certificate import discovery_certificate
    pts = q4_cover.cover_points("TRI25")
    assert len(pts) == 25
    cert = discovery_certificate(pts)
    assert cert["valid"], cert
    assert cert["max_distance_m"] < 950
    assert cert["hull_margin_m"] > 0
    assert sorted(q4_cover.cover_route("TRI25")) == list(range(25))
    assert np.linalg.norm(pts[q4_cover.cover_route("TRI25")[0]]) == 0


def test_discovery_certificate_rejects_missing_boundary_sector():
    assert hasattr(q4_cover, "COVER_TRI25")
    from q4_certificate import discovery_certificate
    pts = q4_cover.cover_points("TRI25")
    assert not discovery_certificate(pts[pts[:, 0] < 1700])["valid"]


def test_tri25_covers_boundary_headings_and_sites():
    assert hasattr(q4_cover, "COVER_TRI25")
    pts = q4_cover.cover_points("TRI25")
    angles = np.arange(720) * 2 * np.pi / 720
    sites = np.concatenate((1800 * np.column_stack((np.cos(angles), np.sin(angles))),
                            pts[np.linalg.norm(pts, axis=1) <= 1800]))
    # Sorted bearings have no gap >= pi: every open RF half-plane has a witness.
    for g in sites:
        vec = pts - g
        dist = np.linalg.norm(vec, axis=1)
        vec = vec[(dist < 1000) & (dist > 1e-8)]
        bearing = np.sort(np.arctan2(vec[:, 1], vec[:, 0]))
        assert np.max(np.diff(np.r_[bearing, bearing[0] + 2 * np.pi])) < np.pi - 1e-8


def test_small_batch_route_matches_exact_optimum():
    rng = np.random.default_rng(4)
    pts = rng.uniform(-1000, 1000, (10, 2))
    dist = np.linalg.norm(pts[:, None] - pts[None, :], axis=2)
    result = q4_policy.pending_batch_order(pts[0], list(enumerate(pts[1:9], 1)), pts[9])
    assert sorted(result) == list(range(1, 9))
    path = [0] + result + [9]
    actual = sum(dist[a, b] for a, b in zip(path, path[1:]))
    optimum = min(sum(dist[a, b] for a, b in zip((0,) + p, p + (9,)))
                  for p in permutations(range(1, 9)))
    assert actual == pytest.approx(optimum, abs=1e-8)


def test_count_certificate_stops_the_rest_of_the_current_sweep():
    runner = Q4Runner(NoisyGeomSim([dict(k=16, g=np.array([400., 0.]), r=1200., directional=False)]))
    for k in range(1, 16):
        runner.state.channels[k].status = "cleared"
        runner.state.channels[k].ever_detected = True
    runner.scan_at(np.zeros(2))
    assert [call[3] for call in runner.robot.calls] == [16]


def test_shadow_history_changes_probe_ranking_without_changing_the_certificate():
    assert hasattr(q4_policy, "ROUTE_ADAPTIVE_V4")
    from q4_adaptive import ReceptionBelief
    region = dict(center=np.array([800., 0.]), rho=2.,
                  verts=np.array([[799., -1.], [801., -1.], [801., 1.], [799., 1.]]))
    history = [dict(pos=np.array([0., 0.]), result="direction", svd=0.),
               dict(pos=np.array([1000., 0.]), result="no_signal", svd=None)]
    belief = ReceptionBelief(region, history)
    assert belief.reception_probability([700., 0.]) > .95
    assert belief.reception_probability([1050., 0.]) < .05
    np.testing.assert_array_equal(region["center"], [800., 0.])


def test_adaptive_refinement_never_repeats_a_measurement_site():
    assert hasattr(q4_policy, "ROUTE_ADAPTIVE_V4")
    from q4_adaptive import ranked_refinement_points
    from q4_localize import history_region
    history = [dict(pos=np.array([0., 0.]), result="direction", svd=0.),
               dict(pos=np.array([700., 180.]), result="no_signal", svd=None)]
    points = ranked_refinement_points(history_region(history), history, np.array([700., 180.]))
    assert points
    assert all(np.linalg.norm(p - h["pos"]) > 1 for p in points for h in history)


def test_adaptive_keeps_optical_fallback_in_complete_rf_shadow():
    assert hasattr(q4_policy, "ROUTE_ADAPTIVE_V4")
    class ShadowSim(NoisyGeomSim):
        def measure(self, x, y, k):
            response = super().measure(x, y, k)
            if (x, y) != (0., 0.):
                response["measure_result"] = "no_signal"
                response.pop("svd_deg", None)
            return response
    runner = Q4Runner(ShadowSim([dict(k=1, g=np.array([1230., 0.]), r=1500., directional=False)]))
    runner.route_mode = q4_policy.ROUTE_ADAPTIVE_V4
    runner.measure(0., 0., 1)
    runner.process_pending()
    assert runner.state.channels[1].cleared
    assert runner.state.channels[1].extra_measures <= 8


def test_close_outward_source_uses_short_baseline_before_crossing_it():
    assert hasattr(q4_policy, "ROUTE_ADAPTIVE_V4")
    robot = NoisyGeomSim([dict(k=1, g=np.array([1800., 0.]), r=1000.,
                              directional=True, psi=0.)], 42, "endpoint")
    runner = Q4Runner(robot)
    runner.route_mode = q4_policy.ROUTE_ADAPTIVE_V4
    runner.measure(1950., 0., 1)
    runner.process_pending()
    assert runner.state.channels[1].cleared
    assert runner.n_optical_fallback == 0
    assert runner.n_measure <= 5


def test_first_detection_index_tracks_actual_cover_visits():
    old_cover = q4_cover.current_cover_mode()
    try:
        q4_cover.set_cover_mode("TRI25")
        point = q4_cover.cover_points()[19]
        robot = NoisyGeomSim([dict(k=1, g=.9 * point, r=1000., directional=False)])
        runner = Q4Runner(robot)
        runner.scan_at(np.zeros(2))
        runner.scan_at(point)
        assert runner.first_detect_index[1] == 1
    finally:
        q4_cover.set_cover_mode(old_cover)
