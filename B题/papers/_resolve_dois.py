# --- Standard prelude ---
import sys, os, glob, json
_candidates = [
    os.path.expanduser("~/.claude/skills/semanticscholar-skill"),
    os.path.expanduser("~/.openclaw/skills/semanticscholar-skill"),
    *glob.glob(os.path.expanduser("~/.claude/plugins/**/semanticscholar-skill"), recursive=True),
    *glob.glob(os.path.expanduser("~/.codex/skills/semanticscholar-skill")),
    ".",
]
SKILL_DIR = next((p for p in _candidates if os.path.isfile(os.path.join(p, "s2.py"))), None)
if SKILL_DIR is None:
    raise RuntimeError("Cannot locate semanticscholar-skill (s2.py not found)")
sys.path.insert(0, SKILL_DIR)
from s2 import *
# --- end prelude ---

titles = [
    "Statistical theory of d.f. fixing",
    "Bearings-only target localization using total least squares",
    "Weighted intersections of bearing lines for AOA based localization",
    "Characterizing the Worst-Case Position Error in Bearing-Only Target Localization",
    "Optimality analysis of sensor-target localization geometries",
    "Optimal Sensor Placement for 3-D Angle-of-Arrival Target Localization",
    "UAV Path Planning for Passive Emitter Localization",
    "A survey on coverage path planning for robotics",
    "UAV-Based Efficient Joint Estimation of Directional Emitter Position and Transmission Orientation",
    "Cautious Greedy Strategy for Bearing-Only Active Localization",
    "Optimal Geometries for AOA Localization in the Bayesian Sense",
    "Multi-Stage RF Emitter Search and Geolocation With UAV A Cognitive Learning-Based Method",
    "Low-Complexity Three-Dimensional AOA-Cross Geometric Center Localization Algorithm",
    "Spatially Intelligent Patrol Routes for Concealed Emitter Localization",
    "Geolocation of RF Emitters Using a Low-Cost UAV-Based Approach",
    "CRLB-weighted intersection method for target localization using AOA measurements",
]

out = []
for t in titles:
    try:
        p = match_title(t)
    except Exception as e:
        print(f"FAIL\t{t}\t{e}")
        continue
    if not p:
        print(f"MISS\t{t}")
        continue
    ext = p.get("externalIds") or {}
    doi = ext.get("DOI")
    arxiv = ext.get("ArXiv")
    pmc = ext.get("PubMedCentral")
    oa = (p.get("openAccessPdf") or {}).get("url")
    rec = {
        "query": t,
        "title": p.get("title"),
        "year": p.get("year"),
        "paperId": p.get("paperId"),
        "doi": doi,
        "arxiv": arxiv,
        "pmc": pmc,
        "oa_pdf": oa,
        "venue": p.get("venue"),
        "citationCount": p.get("citationCount"),
    }
    out.append(rec)
    print(f"OK\t{p.get('year')}\tDOI={doi}\tARXIV={arxiv}\tPMC={pmc}\tOA={bool(oa)}\t{p.get('title')}")

dest = os.path.join(os.path.dirname(__file__), "_resolved.json")
with open(dest, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print("WROTE", dest)
