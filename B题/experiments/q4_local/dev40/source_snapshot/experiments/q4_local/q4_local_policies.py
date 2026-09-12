"""Local actions on the unchanged TRI25/V4 global scheduling rule."""
from dataclasses import dataclass,asdict
from pathlib import Path
import sys
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'experiments/q4_transfer'),str(ROOT/'experiments/q4_ablation')]
from q4_transfer_policies import (Config as ParentConfig,TransferRunner,VARIANTS as TRANSFER,
                                  make_runner as transfer_runner,cover_context,line_estimate)
from q4_localize import legal_xy,optical_cover_points
from q4_runner import Q4Runner,MAX_MEASURE
from q4_policy import set_route_mode,ROUTE_ADAPTIVE_V4


@dataclass(frozen=True)
class Config(ParentConfig):
    local_penalty:float=0.
    stop_budget:int=0
    burst_radius:float=0.
    optical_ratio:float=0.
    mass_gate:float=0.


VARIANTS={
    'baseline':Config('baseline'),
    'previous_best':Config(**dict(asdict(TRANSFER['JSO_compact_dopt']),name='previous_best')),
    'S_all':Config('S_all',selective=True),
    'L30':Config('L30',local_penalty=30),
    'L90':Config('L90',local_penalty=90),
    'P1':Config('P1',selective=True,stop_budget=1),
    'P2':Config('P2',selective=True,stop_budget=2),
    'F60':Config('F60',burst_radius=60),
    'F120':Config('F120',burst_radius=120),
    'C1':Config('C1',optical_ratio=1.),
    'C15':Config('C15',optical_ratio=1.5),
    'M50':Config('M50',mass_gate=.50),
    'M75':Config('M75',mass_gate=.75),
}


def inside_polygon(q,verts):
    v=np.asarray(verts);edges=np.roll(v,-1,axis=0)-v;offset=np.asarray(q)-v
    cross=edges[:,0]*offset[:,1]-edges[:,1]*offset[:,0]
    return bool(np.all(cross>=-1e-7) or np.all(cross<=1e-7))


def mass_candidate(region,belief,history,pos,failed):
    candidates=[region['center'],*belief.points]
    estimate=line_estimate(history,region)
    if estimate is not None: candidates.append(estimate)
    candidates=[np.asarray(q) for q in candidates if legal_xy(q) and inside_polygon(q,region['verts'])
                and all(np.linalg.norm(q-f)>1 for f in failed)]
    if not candidates: return None,0.
    points=np.asarray(candidates);weights=belief.weights.sum(axis=(1,2))
    masses=(np.linalg.norm(points[:,None]-belief.points[None,:],axis=2)<=20)@weights
    i=min(range(len(points)),key=lambda i:(-float(masses[i]),float(np.linalg.norm(points[i]-pos))))
    return points[i],float(masses[i])


def make_runner(robot,config):
    set_route_mode(ROUTE_ADAPTIVE_V4)
    if config.name=='baseline': return Q4Runner(robot)
    if config.name=='previous_best': return transfer_runner(robot,TRANSFER['JSO_compact_dopt'])
    if config.name=='S_all': return transfer_runner(robot,TRANSFER['S'])
    return LocalRunner(robot,config)


class LocalRunner(TransferRunner):
    def __init__(self,robot,config):
        super().__init__(robot,config)
        self._stop_id=0;self._stop_used=0
        self._mass_versions={k:[] for k in self.state.channels}
        self._burst_id=0
        self._local_cells={}

    def _move_to(self,pos):
        # Reset only on an accepted operation whose individual movement exceeds1m.
        if np.linalg.norm(np.asarray(pos)-self.state.pos)>1:
            self._stop_id+=1;self._stop_used=0
        super()._move_to(pos)

    def _refinement_points(self,k,region):
        points=super()._refinement_points(k,region)
        if not self.config.local_penalty or not points: return points
        history=self.state.channels[k].history
        belief=self._reception_belief(k)
        spatial=belief.weights.sum(axis=(1,2))
        bearings=[h for h in history if h['result']=='direction']
        def score(q):
            vec=belief.points-q;dist=np.linalg.norm(vec,axis=1);sine=np.zeros(len(dist))
            for h in bearings:
                old=belief.points-h['pos']
                sine=np.maximum(sine,np.abs(old[:,0]*vec[:,1]-old[:,1]*vec[:,0])/
                                np.maximum(dist*np.linalg.norm(old,axis=1),1e-9))
            predicted=2*np.tan(np.deg2rad(1.005))*dist/np.maximum(sine,.015)
            heard=(belief.weights*belief._heard(q)).sum(axis=(1,2))
            finish=float(heard@np.clip((40-predicted)/20,0,1))
            return (float(np.linalg.norm(q-self.state.pos))/5+float(spatial@dist)/5+6+
                    self.config.local_penalty*(1-finish)+12*(1-float(heard.sum())))
        points.sort(key=score)
        if len(bearings)==1 and history[-1]['result']=='no_signal':
            pair=self._recovery_pair(k,region)
            if pair: points=pair+[q for q in points if all(np.linalg.norm(q-p)>1 for p in pair)]
        return points

    def _supplement(self,p):
        if not self.config.stop_budget: return super()._supplement(p)
        if self._supplementing or self._stop_used>=self.config.stop_budget: return
        self._supplementing=True
        try:
            while self._stop_used<self.config.stop_budget:
                candidates=[]
                for k in self.state.pending_detected():
                    useful=self._useful(p,k)
                    if useful is None: continue
                    score=self._reception_belief(k).expected_gain(p)/(5+(self.measure_channel!=k))
                    candidates.append((-score,k,useful))
                if not candidates: break
                _,k,useful=min(candidates)
                self._stop_used+=1;self.n_probe+=1
                self._note(op='budget_probe',k=k,stop_id=self._stop_id,used=self._stop_used,
                           cap=self.config.stop_budget,t=self.virtual_time)
                self._note(op='selective_probe',k=k,probability=useful[0],parallax_sine=useful[1],t=self.virtual_time)
                if self.measure(*p,k).get('measure_result')=='near': self._try_clear_at(k,p)
        finally:
            self._supplementing=False

    def _mass_available(self,k):
        return len(self._mass_versions[k])<2 and self._positive_version(k) not in self._mass_versions[k]

    def _mass_choice(self,k,region):
        # Belief is cached by full history in the parent. Recompute candidate ties
        # using current position and failed points; negatives can alter mass.
        return mass_candidate(region,self._reception_belief(k),self.state.channels[k].history,
                              self.state.pos,self.failed_clear_points[k])

    def _rf_or_optical(self,k,region):
        if self.state.channels[k].extra_measures<MAX_MEASURE:
            points=self._refinement_points(k,region)
            if points: return points[0],'measure'
        return region['center'],'optical'

    def _adaptive_task(self,k):
        region=self._region(k)
        q,kind=super()._adaptive_task(k)
        if self.config.mass_gate and kind!='cert_clear':
            if region['rho']<=160 and self._mass_available(k):
                candidate,mass=self._mass_choice(k,region)
                if candidate is not None and mass>=self.config.mass_gate:
                    q,kind=candidate,'mass_clear'
                else: q,kind=self._rf_or_optical(k,region)
            else: q,kind=self._rf_or_optical(k,region)
        if (self.config.optical_ratio and kind in ('measure','aggr_clear','mass_clear')
            and region['rho']<=80):
            probe,probe_kind=(q,kind) if kind=='measure' else self._rf_or_optical(k,region)
            if probe_kind=='optical': return region['center'],'optical'
            version=self._positive_version(k)
            cached=self._local_cells.get(k)
            if cached is None or cached[0]!=version:
                cached=(version,optical_cover_points(region['verts']));self._local_cells[k]=cached
            cells=cached[1]
            if len(cells)<=12:
                pos=self.state.pos.copy();remaining=list(cells);distance=0.
                while remaining:
                    index=min(range(len(remaining)),key=lambda i:np.linalg.norm(remaining[i]-pos))
                    nxt=remaining.pop(index);distance+=float(np.linalg.norm(nxt-pos));pos=nxt
                optical_cost=distance/5+3*len(cells)+2
                rf_cost=float(np.linalg.norm(probe-self.state.pos)+np.linalg.norm(probe-region['center']))/5+11
                if optical_cost<=self.config.optical_ratio*rf_cost:
                    self._note(op='local_optical_choice',k=k,cells=len(cells),optical_cost=optical_cost,
                               rf_cost=rf_cost,ratio=self.config.optical_ratio,t=self.virtual_time)
                    q,kind=region['center'],'optical'
        return q,kind

    def _execute_one(self,k,q,kind):
        before=len(self.log)
        if kind=='mass_clear':
            assert self._mass_available(k)
            version=self._positive_version(k);self._mass_versions[k].append(version)
            belief=self._reception_belief(k)
            mass=float((np.linalg.norm(belief.points-q,axis=1)<=20)@belief.weights.sum(axis=(1,2)))
            assert mass>=self.config.mass_gate-1e-12
            self._note(op='mass_attempt',k=k,x=float(q[0]),y=float(q[1]),mass=mass,
                       positive_version=version,trial=len(self._mass_versions[k]),t=self.virtual_time)
            kind='aggr_clear'
        assert kind not in ('optical','reuse')
        super()._do_v3_action(k,q,kind)
        actual=[e for e in self.log[before:] if e.get('k')==k and e['op'] in ('measure','clear')]
        if not actual: return 'no_operation'
        if any(e['op']=='measure' and e['result']=='no_signal' for e in actual): return 'no_signal'
        if any(e['op']=='clear' and not e['ok'] for e in actual): return 'failed_clear'
        return 'positive_or_cleared'

    def _do_v3_action(self,k,q,kind):
        outcome=self._execute_one(k,q,kind)
        if not self.config.burst_radius or outcome!='positive_or_cleared': return
        if self.state.channels[k].status!='detected': return
        self._burst_id+=1;burst_id=self._burst_id
        self._note(op='local_burst_start',k=k,burst_id=burst_id,t=self.virtual_time)
        reason='cap'
        for index in (1,2):
            if self.state.channels[k].status!='detected': reason='cleared';break
            next_q,next_kind=self._adaptive_task(k)
            distance=float(np.linalg.norm(next_q-self.state.pos))
            if next_kind=='optical': reason='optical_to_scheduler';break
            if distance>self.config.burst_radius: reason='distance';break
            self._note(op='local_burst_action',k=k,burst_id=burst_id,index=index,kind=next_kind,
                       distance=distance,cap=self.config.burst_radius,t=self.virtual_time)
            outcome=self._execute_one(k,next_q,next_kind)
            if outcome!='positive_or_cleared': reason=outcome;break
        self._note(op='local_burst_end',k=k,burst_id=burst_id,reason=reason,t=self.virtual_time)
