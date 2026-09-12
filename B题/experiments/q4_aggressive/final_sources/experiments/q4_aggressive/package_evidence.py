"""Bind final artifacts to valid batch snapshots without changing run manifests."""
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
VALID=['dev_valid40','dev_combinations40','primary_valid400']

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    baseline=ROOT/'experiments/q4_efficiency/release_holdout100.meta.json'
    frozen=json.loads(baseline.read_text(encoding='utf-8-sig'))
    mismatch=[name for name,digest in frozen['sha256'].items() if sha(ROOT/name)!=digest]
    assert not mismatch
    assert (HERE/'reviews/primary-validation.md').exists()
    for name in VALID:
        folder=HERE/name;completion=json.loads((folder/'completion.json').read_text())
        audit=json.loads((folder/'audit.json').read_text())
        assert completion['completed']==completion['expected'] and not completion['code_changed_during_run']
        assert audit['status']=='PASS' and audit['results_sha256']==sha(folder/'results.csv')
    own=[p for p in HERE.iterdir() if p.suffix in ('.py','.md')]
    own+=list((HERE/'reviews').glob('*.py'))+list((HERE/'reviews').glob('*.md'))
    dependencies=[ROOT/'experiments/q4_ablation/summarize.py',ROOT/'experiments/q4_local/audit_local.py',
                  ROOT/'experiments/q4_transfer/audit_transfer.py',ROOT/'memory.md',ROOT/'workflow.md',
                  ROOT/'decisions/decision-q4-aggressive-experiment.md',baseline,ROOT/'claims/baseline-q4.md']
    dependencies.append(ROOT/'docs/当前算法与消融状态.md')
    copies={}
    for path in own+dependencies:
        rel=path.relative_to(ROOT);dest=HERE/'final_sources'/rel
        dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(path.read_bytes())
        copies[str(rel)]=str(dest.relative_to(HERE))
    files=own+[HERE/'selection.json']+list((HERE/'reviews').glob('*.json'))
    for name in VALID:
        folder=HERE/name
        files += [p for p in folder.iterdir() if p.is_file()]
        files += [p for p in (folder/'source_snapshot').rglob('*') if p.is_file()]
    files += [p for p in (HERE/'final_sources').rglob('*') if p.is_file()]
    result=dict(generated_utc=datetime.now(timezone.utc).isoformat(),
        status='offline exploratory evidence; see independent primary review for qualifications',
        frozen_baseline_replaced=False,valid_batches=VALID,invalid_runs='invalid-runs.md',
        scope='Final reports and source copies; immutable start snapshots; every event bound by results.csv event_sha256 and full audit',
        frozen_verification=dict(anchor=str(baseline.relative_to(ROOT)),anchor_sha256=sha(baseline),
                                 files=len(frozen['sha256']),mismatches=mismatch),
        source_copy_map=copies,sha256={str(p.relative_to(HERE)):sha(p) for p in sorted(set(files))})
    (HERE/'evidence_manifest.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(bound_files=len(result['sha256']),frozen_files=len(frozen['sha256']),mismatches=mismatch)))

if __name__=='__main__':main()
