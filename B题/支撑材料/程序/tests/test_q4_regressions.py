"""Regression cases for the September 11 Q4 practice failures."""
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "simulator_automation"))
sys.path.insert(0, str(ROOT / "tests"))

from q4_runner import Q4Runner
from q4_practice import parse_n_from_ui
import q4_localize
from test_q4_geomsim import GeomSim


class NoisyGeomSim(GeomSim):
    """Bounded, coordinate-stable error; official measurement/switch accounting."""
    def __init__(self, sources, seed=0, error_mode="smooth"):
        super().__init__(sources)
        self.seed = seed
        self.error_mode = error_mode
        self.channel = 1

    def measure(self, x, y, k):
        response = super().measure(x, y, k)
        if k == self.channel:
            self.t -= 1.0
        self.channel = k
        response["virtual_time_s"] = self.t
        if response["measure_result"] == "direction":
            phase = np.sin(x * 0.071 + y * 0.037 + k * 1.7 + self.seed)
            error = phase if self.error_mode == "smooth" else (1.0 if phase >= 0 else -1.0)
            response["svd_deg"] = round((response["svd_deg"] + error) % 360, 2)
        return response


def random_sources(seed):
    rng = np.random.default_rng(seed)
    n = int(rng.integers(10, 17))
    channels = rng.choice(np.arange(1, 21), n, replace=False)
    sources = []
    for k in channels:
        a = rng.uniform(0, 2 * np.pi)
        radius = 1800 * np.sqrt(rng.uniform())
        sources.append(dict(k=int(k), g=radius * np.array([np.cos(a), np.sin(a)]),
                            r=rng.uniform(1000, 1500), directional=bool(rng.integers(2)),
                            psi=rng.uniform(0, 2 * np.pi)))
    return sources


def test_scan_finishes_channels_before_leaving_site():
    robot = NoisyGeomSim([dict(k=1, g=np.array([400., 0.]), r=1200, directional=False)])
    runner = Q4Runner(robot)
    runner.scan_at(np.zeros(2))
    assert len(robot.calls) == 20
    assert all(c[0] == "measure" and c[1:3] == (0., 0.) for c in robot.calls)


def test_fresh_bearing_can_clear_after_fast_budget_is_exhausted():
    robot = NoisyGeomSim([dict(k=1, g=np.array([400., 0.]), r=1200, directional=False)])
    runner = Q4Runner(robot)
    runner.measure(0, 0, 1)
    runner.measure(0, 300, 1)
    ch = runner.state.channels[1]
    ch.n_clear_try = 6
    ch.extra_measures = 8
    runner.measure(390, 30, 1)
    runner.process_pending()
    assert ch.cleared


def test_official_completion_dialog_parses_counts():
    text = "本次案例含干扰源13个，其中全向10个、定向3个。\n行为日志已保存。"
    assert parse_n_from_ui(text) == (13, 10, 3)


def test_official_summary_card_parses_split_uia_text_nodes():
    text = "\n\n".join("ControlType.Text||" + value for value in
                         ("本次演练测试干扰源数量", "共", "12", "个， 全向", "0", "个， 定向", "12", "个"))
    assert parse_n_from_ui(text) == (12, 0, 12)


def test_noisy_mixed_case_clears_and_certifies():
    sources = random_sources(0)
    runner = Q4Runner(NoisyGeomSim(sources, seed=0))
    summary = runner.run()
    assert summary["K"] == len(sources), summary
    assert summary["all_certified"], summary
    assert summary["failure"] is None, summary


def test_all_bearings_shrink_region_without_using_no_signal_as_a_hole():
    assert hasattr(q4_localize, "history_region")
    source = np.array([1100., 250.])
    history = []
    for site in (np.array([0., 0.]), np.array([700., 100.]), np.array([1100., 300.])):
        delta = source - site
        history.append(dict(pos=site, result="direction", svd=np.rad2deg(np.arctan2(*delta[::-1]))))
    two = q4_localize.history_region(history[:2])
    three = q4_localize.history_region(history)
    assert three["rho"] < two["rho"] / 4
    assert np.linalg.norm(source - three["center"]) <= three["rho"] + 1e-7
    with_shadow = q4_localize.history_region(history + [dict(pos=source, result="no_signal", svd=None)])
    np.testing.assert_allclose(with_shadow["verts"], three["verts"])


def test_optical_cover_contains_entire_thin_polygon():
    assert hasattr(q4_localize, "optical_cover_points")
    u = np.array([1., 1.]) / np.sqrt(2)
    v = np.array([-u[1], u[0]])
    verts = np.array([a * u + b * v for a, b in ((0, -10), (1500, -10), (1500, 10), (0, 10))])
    points = np.array(q4_localize.optical_cover_points(verts))
    assert len(points) < 180  # Align the cover to the thin region, not its huge XY bounding box.
    for a in np.linspace(0, 1500, 151):
        for b in np.linspace(-10, 10, 9):
            assert np.min(np.linalg.norm(points - (a * u + b * v), axis=1)) <= 20 + 1e-7


def test_clear_still_works_when_refinement_sites_are_in_rf_shadow():
    class ShadowSim(NoisyGeomSim):
        def measure(self, x, y, k):
            response = super().measure(x, y, k)
            if (x, y) != (0., 0.):
                response["measure_result"] = "no_signal"
                response.pop("svd_deg", None)
            return response
    robot = ShadowSim([dict(k=1, g=np.array([1230., 0.]), r=1500, directional=False)])
    runner = Q4Runner(robot)
    runner.measure(0, 0, 1)
    runner.process_pending()
    assert runner.state.channels[1].cleared
