"""Independent replay and paired deltas against ORIGINAL."""
from __future__ import annotations
import csv, json
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
rows = list(csv.DictReader((HERE/"evaluation/rows.csv").open(encoding="utf-8-sig")))
for r in rows:
    for k in ("T", "T_over_K", "move_m", "n_measure", "failed_clear", "n_switch"):
        r[k] = float(r[k]) if r[k] not in ("", "None") else np.nan
    r["full_success"] = r["full_success"].lower() == "true"
base = {(r["scene_id"]): r for r in rows if r["variant"] == "ORIGINAL"}
out=[]
for v in sorted(set(r["variant"] for r in rows)):
    if v == "ORIGINAL": continue
    rr=[r for r in rows if r["variant"]==v]
    d={k: np.array([r[k]-base[r["scene_id"]][k] for r in rr]) for k in ("T","T_over_K","move_m","n_measure","failed_clear","n_switch")}
    out.append(dict(variant=v, paired_mean_delta_T=float(np.mean(d["T"])),
                    paired_mean_delta_T_over_K=float(np.mean(d["T_over_K"])),
                    paired_mean_delta_walking_time=float(np.mean(d["move_m"])/5),
                    paired_mean_delta_measurements=float(np.mean(d["n_measure"])),
                    paired_mean_delta_failed_clear=float(np.mean(d["failed_clear"])),
                    paired_win_rate_T=float(np.mean(d["T"]<0)),
                    paired_win_rate_measure=float(np.mean(d["n_measure"]<0)),
                    p95_delta_T=float(np.quantile(d["T"],.95)),
                    full_scenes=sum(r["full_success"] for r in rr), scenes=len(rr)))
(HERE/"evaluation/paired_deltas.json").write_text(json.dumps(out,indent=2),encoding="utf-8")
with (HERE/"evaluation/paired_deltas.csv").open("w",newline="",encoding="utf-8-sig") as f:
    w=csv.DictWriter(f,fieldnames=list(out[0]));w.writeheader();w.writerows(out)
print(json.dumps(out,indent=2))
