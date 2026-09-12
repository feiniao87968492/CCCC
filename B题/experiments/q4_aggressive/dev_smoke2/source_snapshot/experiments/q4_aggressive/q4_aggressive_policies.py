"""Aggressive ordinary-case local overlays; frozen Q4 geometry and route stay intact."""
from dataclasses import asdict, dataclass
from pathlib import Path
import sys
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'experiments/q4_local'),str(ROOT/'experiments/q4_transfer'),str(ROOT/'experiments/q4_ablation'),str(ROOT/'src'),str(ROOT/'simulator_automation')]
import q4_local_policies as base
from q4_runner import Q4Runner,MAX_MEASURE
from q4_localize import legal_xy,optical_cover_points
from q4_policy import set_route_mode,ROUTE_ADAPTIVE_V4

FAMILY_CAPS={'E':2,'B':2,'G':3,'R':4,'H':2,'N':2}

@dataclass(frozen=True)
class Config(base.Config):
    family:str=''
    level:float=0.
    e_ratio:float=0.
    b_radius:float=0.
    g_ratio:float=0.
    r_count:int=0
    h_rho:float=0.
    n_mass:float=0.

def _cfg(name,**kw):
    d=asdict(base.VARIANTS['LPC'])
    d.update(name=name,selective=False,stop_budget=0,local_penalty=30,optical_ratio=1.5)
    d.update(kw)
    return Config(**d)

VARIANTS={
    'baseline':base.VARIANTS['baseline'], 'LC':base.VARIANTS['LC'],
    'LPC':base.VARIANTS['LPC'], 'previous_best':base.VARIANTS['previous_best'],
    'E1':_cfg('E1',family='E',e_ratio=1.), 'E2':_cfg('E2',family='E',e_ratio=2.),
    'B20':_cfg('B20',family='B',b_radius=20.), 'B60':_cfg('B60',family='B',b_radius=60.),
    'G075':_cfg('G075',family='G',g_ratio=.75), 'G15':_cfg('G15',family='G',g_ratio=1.5),
    'R2':_cfg('R2',family='R',r_count=2), 'R4':_cfg('R4',family='R',r_count=4),
    'H200':_cfg('H200',family='H',h_rho=200.), 'H400':_cfg('H400',family='H',h_rho=400.),
    'N20':_cfg('N20',family='N',n_mass=.20), 'N50':_cfg('N50',family='N',n_mass=.50),
}

def inside(q,verts):
    v=np.asarray(verts); e=np.roll(v,-1,axis=0)-v; z=np.asarray(q)-v
    c=e[:,0]*z[:,1]-e[:,1]*z[:,0]
    return bool(np.all(c>=-1e-7) or np.all(c<=1e-7))

def expected_optical_order(cells,weights,pos,failed):
    cells=np.asarray(cells,dtype=float); w=np.asarray(weights,dtype=float).reshape(-1)
    if len(cells)==0:return [],0.
    if len(w)!=len(cells) or w.sum()<=1e-12:w=np.full(len(cells),1./len(cells))
    else:w=w/w.sum()
    remaining=list(range(len(cells))); order=[]; at=np.asarray(pos,dtype=float); cost=0.
    failed=np.asarray(failed,dtype=float).reshape(-1,2) if len(failed) else np.empty((0,2))
    while remaining:
        # Soft failed discs affect ordering but never remove a certified cell.
        scores=[]
        for j in remaining:
            d=float(np.linalg.norm(cells[j]-at)); c=d/5+3
            hit=(np.linalg.norm(cells-cells[j],axis=1)<=20.)
            benefit=float((w*hit).sum())+.05/len(cells)
            scores.append((-(benefit/(c+1e-9)),d,j))
        _,d,j=min(scores); cost+=d/5+3; order.append(j); at=cells[j];remaining.remove(j)
    return order,cost+2.

def two_step_score(region,q,pos,g,heard):
    q=np.asarray(q);pos=np.asarray(pos);g=np.asarray(g)
    r1=float(np.linalg.norm(g-q)); first=float(np.linalg.norm(q-pos))/5+6
    if r1<=20: cont=r1/5+5
    else:
        axis=(g-q)/max(r1,1e-12); lat=np.array([-axis[1],axis[0]])
        d=float(np.clip(r1,20,120)); vs=[g+d*lat,g-d*lat]
        legal_vs=[v for v in vs if legal_xy(v)]
        cont=min((float(np.linalg.norm(q-v)+np.linalg.norm(v-g))/5+11 for v in legal_vs),default=r1/5+89)
    return first+float(heard)*cont+78*(1-float(np.clip(heard,0,1)))

def endpoint_can_act(status,in_action):
    return status=='detected' and not in_action

class AggressiveRunner(base.LocalRunner):
    def __init__(self,robot,config):
        super().__init__(robot,config); self._g_used=0; self._g_guard=False
        self._n_versions={k:[] for k in self.state.channels}; self._in_optical=False
        self._e_cache={}; self._b_cache={}; self._h_used={k:[] for k in self.state.channels}

    def _try_clear_at(self,k,p):
        # Endpoint callbacks are post-action only. This guard makes a stale
        # caller harmless even if a future executor path invokes it twice.
        if self.state.channels[k].status in ('cleared','certified_absent'):
            return True
        return super()._try_clear_at(k,p)

    def _move_to(self,pos):
        if np.linalg.norm(np.asarray(pos)-self.state.pos)>1:self._g_used=0
        super()._move_to(pos)

    def _b_score(self,k,q,region):
        belief=self._reception_belief(k); masses=belief.weights.sum(axis=(1,2)); den=max(float(masses.sum()),1e-12)
        scores=[]
        for g,h in zip(belief.points,masses):
            heard=float((belief.weights*self._reception_belief(k)._heard(q)).sum())
            scores.append(float(h/den)*two_step_score(region,q,self.state.pos,g,heard))
        return float(np.sum(scores))+12*(1-float(self._reception_belief(k).reception_probability(q)))

    def _refinement_points(self,k,region):
        points=super()._refinement_points(k,region)
        if self.config.family!='B' or not points:return points
        belief=self._reception_belief(k); center=np.asarray(region['center']); out=[]
        candidates=points+ [center+np.array([dx,dy]) for dx,dy in ((self.config.b_radius,0),(-self.config.b_radius,0),(0,self.config.b_radius),(0,-self.config.b_radius))]
        hist=self.state.channels[k].history
        for q in candidates:
            if legal_xy(q) and inside(q,region['verts']) and all(np.linalg.norm(q-h['pos'])>1 for h in hist):
                out.append((self._b_score(k,q,region),q))
        if out:
            out.sort(key=lambda x:x[0]); self._b_cache[k]=(out[0][1],out[0][0]); return [q for _,q in out]
        return points

    def _optical_fallback(self,k,region):
        if self.config.family!='E' or len(optical_cover_points(region['verts']))>256:
            return super()._optical_fallback(k,region)
        cells=optical_cover_points(region['verts']); belief=self._reception_belief(k)
        w=belief.weights.sum(axis=(1,2)); order,cost=expected_optical_order(cells,w,self.state.pos,self.failed_clear_points[k])
        self._note(op='aggressive_optical_order',k=k,cells=len(cells),order=order,expected_cost=cost,t=self.virtual_time)
        self.n_optical_fallback+=1; remaining=list(order)
        self._in_optical=True
        try:
            while remaining:
                j=min(range(len(remaining)),key=lambda z:np.linalg.norm(cells[remaining[z]]-self.state.pos)); idx=remaining.pop(j)
                self._note(op='optical_cover_step',k=k,index=idx,count=len(cells),t=self.virtual_time)
                if self._try_clear_at(k,cells[idx]): return
        finally:self._in_optical=False
        raise RuntimeError(f'channel {k}: aggressive optical cover exhausted')

    def _adaptive_task(self,k):
        region=self._region(k)
        q,kind=super()._adaptive_task(k)
        if region is None:return q,kind
        if self.config.family=='R' and self.state.channels[k].extra_measures>=self.config.r_count:
            positives=sum(h['result']=='direction' for h in self.state.channels[k].history)
            if positives>=2 and region['rho']<=200 and kind not in ('cert_clear','optical'):
                self._note(op='aggressive_early_exit',k=k,count=self.state.channels[k].extra_measures,rho=region['rho'],t=self.virtual_time)
                return region['center'],'optical'
        if self.config.family=='H' and region['rho']<=self.config.h_rho:
            est=self._estimate(k); version=self._positive_version(k)
            if est is not None and version not in self._h_used[k] and len(self._h_used[k])<2 and all(np.linalg.norm(est-p)>1 for p in self.failed_clear_points[k]):
                return est,'h_clear'
        if self.config.family=='E' and region['rho']<=160 and len(optical_cover_points(region['verts']))<=48 and kind in ('measure','aggr_clear','mass_clear'):
            return region['center'],'optical'
        return q,kind

    def _g_useful(self,p,k):
        ch=self.state.channels[k]; region=self._region(k)
        if region is None or region['rho']<=40 or any(np.linalg.norm(p-h['pos'])<=1 for h in ch.history):return None
        bearings=[h for h in ch.history if h['result']=='direction']
        if not bearings:return None
        belief=self._reception_belief(k); prob=belief.reception_probability(p)
        if prob<.5:return None
        gain=belief.expected_gain(p); return gain/(5+(self.measure_channel!=k)) if gain>0 else None

    def _g_endpoint(self,p):
        if self.config.family!='G' or self._g_guard:return
        self._g_guard=True
        try:
            while self._g_used<3:
                choices=[]
                for k in list(self.state.pending_detected()):
                    score=self._g_useful(p,k)
                    if score is not None and score>=self.config.g_ratio:choices.append((-score,k))
                if not choices:break
                _,k=min(choices); self._g_used+=1
                self._note(op='aggressive_budget_probe',k=k,stop_used=self._g_used,ratio=self.config.g_ratio,t=self.virtual_time)
                self.n_probe+=1
                resp=self.measure(*p,k)
                if resp.get('measure_result')=='near' and self.state.channels[k].status=='detected':self._try_clear_at(k,p)
        finally:self._g_guard=False

    def _n_endpoint(self,p):
        if self.config.family!='N' or self._in_optical:return
        for k in list(self.state.pending_detected()):
            if not endpoint_can_act(self.state.channels[k].status,self._g_guard):continue
            region=self._region(k)
            if region is None or region['rho']>320 or self._positive_version(k) in self._n_versions[k]:continue
            belief=self._reception_belief(k); mass=float((np.linalg.norm(belief.points-p,axis=1)<=20)@belief.weights.sum(axis=(1,2)))
            if mass<self.config.n_mass or len(self._n_versions[k])>=2:continue
            self._n_versions[k].append(self._positive_version(k));self._note(op='aggressive_mass_attempt',k=k,mass=mass,positive_version=self._positive_version(k),trial=len(self._n_versions[k]),t=self.virtual_time)
            self._try_clear_at(k,p)
            if self.state.channels[k].status!='detected':continue

    def _do_v3_action(self,k,q,kind):
        if kind=='h_clear':
            v=self._positive_version(k); self._h_used[k].append(v)
            self._note(op='aggressive_h_attempt',k=k,positive_version=v,trial=len(self._h_used[k]),t=self.virtual_time)
            super()._do_v3_action(k,q,'aggr_clear')
        else:super()._do_v3_action(k,q,kind)
        if self.state.channels[k].status!='detected':return
        self._n_endpoint(self.state.pos.copy());self._g_endpoint(self.state.pos.copy())

    def scan_at(self,p,*,certificate_mode=False):
        super().scan_at(p,certificate_mode=certificate_mode)
        if not certificate_mode and not self._in_optical:
            self._n_endpoint(np.asarray(p,dtype=float)); self._g_endpoint(np.asarray(p,dtype=float))

def make_runner(robot,config):
    set_route_mode(ROUTE_ADAPTIVE_V4)
    if config.name=='baseline':return Q4Runner(robot)
    if config.name in ('LC','LPC','previous_best'):return base.make_runner(robot,config)
    return AggressiveRunner(robot,config)

cover_context=base.cover_context
