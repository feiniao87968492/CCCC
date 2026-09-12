"""Offline Q3 API model. Hidden truth is never passed to policy methods."""
from __future__ import annotations

import hashlib
import math
import time

import numpy as np


class ObservationClient:
    __slots__ = ("__enter", "__measure", "__clear", "__exit", "entered")

    def __init__(self, sim):
        self.__enter, self.__measure = sim.enter, sim.measure
        self.__clear, self.__exit = sim.clear, sim.exit
        self.entered = False

    def enter(self):
        response = self.__enter()
        self.entered = True
        return response

    def measure(self, x, y, k):
        return self.__measure(x, y, k)

    def clear(self, x, y, k):
        return self.__clear(x, y, k)

    def exit(self):
        self.entered = False
        return self.__exit()


class Q3Environment:
    def __init__(self, sources, seed: int, error_mode: str = "smooth"):
        if error_mode not in ("smooth", "spatial", "endpoint"):
            raise ValueError(error_mode)
        self.sources = {int(s["k"]): {"g": np.asarray(s["g"], float).copy(),
                                      "r": float(s["r"])} for s in sources}
        self.seed, self.error_mode = int(seed), error_mode
        self.t = self.move_m = 0.0
        self.pos = np.zeros(2)
        self.channel = 1
        self.n_measure = self.n_clear = self.n_switch = 0
        self.cleared = set()
        self.events = []
        self.entered = False
        self.deadline = float("inf")

    def client(self):
        return ObservationClient(self)

    def enter(self):
        self.entered = True
        self.deadline = time.perf_counter() + 1200
        return {"accepted": True, "virtual_time_s": self.t,
                "remaining_real_duration_s": 1200.0}

    def exit(self):
        self.entered = False
        return {"accepted": True, "virtual_time_s": self.t}

    def _noise(self, k, p):
        if self.error_mode == "smooth":
            return math.sin(.0123*p[0] + .0179*p[1] + 1.73*k + .191*self.seed)
        key = f"{self.seed}:{k}:{float(p[0]).hex()}:{float(p[1]).hex()}"
        u = int.from_bytes(hashlib.sha256(key.encode()).digest()[:8], "big") / 2**64
        return (1.0 if u >= .5 else -1.0) if self.error_mode == "endpoint" else 2*u-1

    def _move(self, p, k):
        if not self.entered:
            raise RuntimeError("client has not entered")
        if not 1 <= int(k) <= 20 or not np.all(np.isfinite(p)) or np.max(np.abs(p)) > 2e6:
            raise ValueError("illegal action")
        if self.t > 360000 or time.perf_counter() >= self.deadline or len(self.events) >= 20000:
            raise TimeoutError("offline action/time budget")
        d = float(np.linalg.norm(p - self.pos))
        self.move_m += d
        self.t += d/5
        self.pos = p

    def measure(self, x, y, k):
        p, k = np.array([float(x), float(y)]), int(k)
        self._move(p, k)
        switch = int(k != self.channel)
        self.n_switch += switch
        self.channel = k
        self.n_measure += 1
        self.t += 5 + switch
        source = self.sources.get(k)
        result, bearing = "no_signal", None
        if source is not None and k not in self.cleared:
            vec = source["g"] - p
            d = float(np.linalg.norm(vec))
            if d <= source["r"]:
                result = "near" if d <= 5 else "direction"
                if result == "direction":
                    true = math.degrees(math.atan2(vec[1], vec[0]))
                    lo = math.ceil((true-1)*100 - 1e-10)/100
                    hi = math.floor((true+1)*100 + 1e-10)/100
                    bearing = min(hi, max(lo, round(true+self._noise(k, p), 2))) % 360
        response = {"accepted": True, "virtual_time_s": self.t, "measure_result": result}
        if bearing is not None:
            response["svd_deg"] = bearing
        self.events.append({"op": "measure", "k": k, "x": float(x), "y": float(y),
                            "result": result, "svd": bearing, "t": self.t})
        return response

    def clear(self, x, y, k):
        p, k = np.array([float(x), float(y)]), int(k)
        self._move(p, k)
        self.n_clear += 1
        source = self.sources.get(k)
        ok = source is not None and k not in self.cleared and np.linalg.norm(p-source["g"]) <= 20
        self.t += 3 + 2*int(ok)
        if ok:
            self.cleared.add(k)
        self.events.append({"op": "clear", "k": k, "x": float(x), "y": float(y),
                            "ok": bool(ok), "t": self.t})
        return {"accepted": True, "virtual_time_s": self.t,
                "clear_result": "success" if ok else "no_target_in_range"}
