"""Observation-only aggressive local experiments with complete optical fallback."""
from dataclasses import asdict, dataclass
from pathlib import Path
import sys
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'experiments/q4_local'),str(ROOT/'experiments/q4_transfer'),
              str(ROOT/'experiments/q4_ablation'),str(ROOT/'src'),str(ROOT/'simulator_automation')]
import q4_local_policies as base
from q4_runner import Q4Runner
from q4_localize import legal_xy,optical_cover_points
from q4_policy import set_route_mode,ROUTE_ADAPTIVE_V4

@dataclass(frozen=True)
class Config(base.Config):
    e_ratio:float=0.
    b_radius:float=0.
    g_ratio:float=0.
    r_count:int=0
    h_rho:float=0.
    n_mass:float=0.

def config(name,**kw):
    d=asdict(base.VARIANTS['LC']);d.update(name=name,**kw)
    if kw.get('e_ratio'):d['optical_ratio']=0.
    if kw.get('h_rho'):d.update(optimistic=True,optimistic_rho=kw['h_rho'])
    return Config(**d)

VARIANTS={name:base.VARIANTS[name] for name in ('baseline','LC','LPC','previous_best')}
VARIANTS.update({
    'E1':config('E1',e_ratio=1.),'E2':config('E2',e_ratio=2.),
    'B20':config('B20',b_radius=20),'B60':config('B60',b_radius=60),
    'G075':config('G075',g_ratio=.75),'G15':config('G15',g_ratio=1.5),
    'R2':config('R2',r_count=2),'R4':config('R4',r_count=4),
    'H200':config('H200',h_rho=200),'H400':config('H400',h_rho=400),
    'N20':config('N20',n_mass=.20),'N50':config('N50',n_mass=.50),
})

def optical_plan(cells,points,weights,pos,failed=()):
    """Return ALL original cell indices and a first-hit expected-cost proxy."""
    cells=np.asarray(cells,dtype=float).reshape(-1,2)
    points=np.asarray(points,dtype=float).reshape(-1,2)
    w=np.asarray(weights,dtype=float).copy()
    if len(w)!=len(points) or not len(w):raise ValueError('one weight per spatial sample required')
    for p in failed:w[np.linalg.norm(points-p,axis=1)<=20]=0.
    reset=bool(w.sum()<=1e-12)
    w=np.full(len(w),1/len(w)) if reset else w/w.sum()
    hit=np.linalg.norm(cells[:,None,:]-points[None,:,:],axis=2)<=20
    uncovered=np.ones(len(points),dtype=bool);remaining=list(range(len(cells)))
    order=[];at=np.asarray(pos,dtype=float);expected=0.;full=0.
    while remaining:
        def score(j):
            distance=float(np.linalg.norm(cells[j]-at))
            benefit=float(w[uncovered & hit[j]].sum())+.05/max(len(cells),1)
            return -benefit/(3+distance/5),distance,j
        _,_,j=min(score(j) for j in remaining)
        order.append(j);remaining.remove(j)
        if any(np.linalg.norm(cells[j]-f)<1e-7 for f in failed):continue
        charge=float(np.linalg.norm(cells[j]-at))/5+3
        full+=charge;expected+=charge*float(w[uncovered].sum())
        uncovered &= ~hit[j];at=cells[j]
    return order,expected+2,full+2,reset

def continuation_cost(points,q,predicted):
    points=np.asarray(points);q=np.asarray(q);predicted=np.asarray(predicted)
    vec=points-q;distance=np.linalg.norm(vec,axis=1)
    axis=np.divide(vec,distance[:,None],out=np.tile([1.,0.],(len(vec),1)),where=distance[:,None]>1e-12)
    lateral=np.c_[-axis[:,1],axis[:,0]];offset=np.clip(predicted,20,120)[:,None]*lateral
    values=[]
    for v in (points+offset,points-offset):
        c=(np.linalg.norm(v-q,axis=1)+np.linalg.norm(v-points,axis=1))/5+11
        c=np.where(np.array([legal_xy(p) for p in v]),c,np.inf);values.append(c)
    second=np.minimum(*values);second=np.where(np.isfinite(second),second,distance/5+89)
    return np.where(predicted<=20,distance/5+5,second)

class AggressiveRunner(base.LocalRunner):
    def __init__(self,robot,cfg):
        super().__init__(robot,cfg)
        self._g_used=0;self._endpoint_busy=False
        self._n_versions={k:[] for k in self.state.channels};self._b_scores={}

    def _try_clear_at(self,k,p):
        if self.state.channels[k].status=='cleared':return True
        if self.state.channels[k].status=='certified_absent':return False
        return super()._try_clear_at(k,p)

    def clear(self,x,y,k):
        if self.state.channels[k].status=='cleared':return True
        if self.state.channels[k].status=='certified_absent':return False
        return super().clear(x,y,k)

    def _move_to(self,pos):
        if np.linalg.norm(np.asarray(pos)-self.state.pos)>1:self._g_used=0
        super()._move_to(pos)

    def _score_b(self,k,q,region):
        b=self._reception_belief(k);vec=b.points-q;distance=np.linalg.norm(vec,axis=1)
        sine=np.zeros(len(distance))
        for h in self.state.channels[k].history:
            if h['result']!='direction':continue
            old=b.points-h['pos']
            sine=np.maximum(sine,np.abs(old[:,0]*vec[:,1]-old[:,1]*vec[:,0])/
                            np.maximum(distance*np.linalg.norm(old,axis=1),1e-9))
        predicted=2*np.tan(np.deg2rad(1.005))*distance/np.maximum(sine,.015)
        heard=(b.weights*b._heard(q)).sum(axis=(1,2));prob=float(heard.sum())
        continuation=float(heard@continuation_cost(b.points,q,predicted))
        first=float(np.linalg.norm(q-self.state.pos))/5+6;negative=78*(1-prob)
        return dict(score=first+continuation+negative,first=first,continuation=continuation,
                    no_reception_cost=negative,probability=prob)

    def _refinement_points(self,k,region):
        points=super()._refinement_points(k,region)
        if not self.config.b_radius:return points
        b=self._reception_belief(k);centers=[b.weights.sum(axis=(1,2))@b.points]
        estimate=base.line_estimate(self.state.channels[k].history,region)
        if estimate is not None:centers.append(estimate)
        radius=self.config.b_radius
        for center in centers:
            points.extend([center,*(center+radius*np.asarray(v) for v in ((1,0),(-1,0),(0,1),(0,-1)))])
        hist=self.state.channels[k].history;fresh=[]
        for q in points:
            if legal_xy(q) and all(np.linalg.norm(q-h['pos'])>1 for h in hist) and all(np.linalg.norm(q-p)>1e-8 for p in fresh):fresh.append(q)
        scores={tuple(q):self._score_b(k,q,region) for q in fresh}
        fresh.sort(key=lambda q:scores[tuple(q)]['score'])
        bearings=[h for h in hist if h['result']=='direction'];pair=[]
        if len(bearings)==1 and hist[-1]['result']=='no_signal':
            pair=self._recovery_pair(k,region)
            if pair:fresh=pair+[q for q in fresh if all(np.linalg.norm(q-p)>1 for p in pair)]
        self._b_scores[k]=(scores,pair)
        return fresh

    def _optical_plan(self,k,region):
        version=self._positive_version(k);cached=self._local_cells.get(k)
        if cached is None or cached[0]!=version:
            cached=(version,optical_cover_points(region['verts']));self._local_cells[k]=cached
        cells=cached[1];b=self._reception_belief(k)
        return cells,optical_plan(cells,b.points,b.weights.sum(axis=(1,2)),self.state.pos,self.failed_clear_points[k])

    def _adaptive_task(self,k):
        q,kind=super()._adaptive_task(k);r=self._region(k)
        if kind=='cert_clear':return q,kind
        if self.config.e_ratio and r['rho']<=160 and kind!='optical':
            version=self._positive_version(k);cache=self._local_cells.get(k)
            if cache is None or cache[0]!=version:
                cache=(version,optical_cover_points(r['verts']));self._local_cells[k]=cache
            if len(cache[1])<=48:
                probe,pk=self._rf_or_optical(k,r)
                if pk=='optical':return r['center'],'optical'
                cells,(_,expected,full,reset)=self._optical_plan(k,r)
                rf=float(np.linalg.norm(probe-self.state.pos)+np.linalg.norm(probe-r['center']))/5+11
                if expected<=self.config.e_ratio*rf:
                    self._note(op='expected_optical_choice',k=k,cells=len(cells),rho=r['rho'],
                               expected_cost=expected,full_cost=full,rf_cost=rf,ratio=self.config.e_ratio,
                               reset_weights=reset,t=self.virtual_time)
                    q,kind=r['center'],'optical'
        ch=self.state.channels[k]
        if (self.config.r_count and kind!='optical' and ch.extra_measures>=self.config.r_count and
            sum(h['result']=='direction' for h in ch.history)>=2 and r['rho']<=200):
            self._note(op='early_exit_choice',k=k,dedicated=ch.extra_measures,
                       positive_bearings=sum(h['result']=='direction' for h in ch.history),rho=r['rho'],t=self.virtual_time)
            q,kind=r['center'],'optical'
        return q,kind

    def _optical_fallback(self,k,region):
        if not self.config.e_ratio:return super()._optical_fallback(k,region)
        cells=optical_cover_points(region['verts'])
        if len(cells)>256:return super()._optical_fallback(k,region)
        cells,(order,expected,full,reset)=self._optical_plan(k,region)
        self.n_optical_fallback+=1
        self._note(op='optical_cover',k=k,count=len(cells),rho=region['rho'],t=self.virtual_time)
        self._note(op='expected_optical_execution',k=k,cells=np.asarray(cells).tolist(),order=order,
                   expected_cost=expected,full_cost=full,reset_weights=reset,t=self.virtual_time)
        for index in order:
            if self._try_clear_at(k,cells[index]):return
        raise RuntimeError(f'channel {k}: complete optical cover exhausted')

    def _g_admission(self,p,k):
        hist=self.state.channels[k].history;r=self._region(k)
        if r is None or r['rho']<=40 or any(np.linalg.norm(p-h['pos'])<=1 for h in hist):return None
        center=r['center'];distance=float(np.linalg.norm(center-p))
        bearings=[h for h in hist if h['result']=='direction']
        if not bearings or distance>1100:return None
        vec=center-p;best=0.
        for h in bearings:
            old=center-h['pos'];best=max(best,abs(float(vec[0]*old[1]-vec[1]*old[0]))/max(float(np.linalg.norm(vec)*np.linalg.norm(old)),1e-9))
        if best<np.sin(np.deg2rad(12)) and distance>=.5*np.linalg.norm(center-bearings[-1]['pos']):return None
        b=self._reception_belief(k);prob=b.reception_probability(p)
        if prob<.5:return None
        gain=b.expected_gain(p);charge=5+int(self.measure_channel!=k)
        score=r['rho']*(1-np.exp(-gain))/(5*charge)
        return dict(score=float(score),gain=float(gain),rho=float(r['rho']),probability=prob,charge=charge,parallax_sine=best)

    def _endpoint(self,p):
        if self._endpoint_busy:return
        self._endpoint_busy=True
        try:
            if self.config.n_mass:
                for k in list(self.state.pending_detected()):
                    ch=self.state.channels[k];hist=ch.history;v=self._positive_version(k)
                    if ch.status!='detected' or len(self._n_versions[k])>=2 or v in self._n_versions[k]:continue
                    if sum(h['result']=='direction' for h in hist)<2 or any(np.linalg.norm(p-f)<=1 for f in self.failed_clear_points[k]):continue
                    r=self._region(k)
                    if r['rho']>320:continue
                    b=self._reception_belief(k);mass=float((np.linalg.norm(b.points-p,axis=1)<=20)@b.weights.sum(axis=(1,2)))
                    if mass<self.config.n_mass:continue
                    self._n_versions[k].append(v)
                    self._note(op='endpoint_clear_attempt',k=k,x=float(p[0]),y=float(p[1]),mass=mass,
                               positive_version=v,trial=len(self._n_versions[k]),t=self.virtual_time)
                    self._try_clear_at(k,p)
            if self.config.g_ratio:
                while self._g_used<3:
                    options=[]
                    for k in list(self.state.pending_detected()):
                        val=self._g_admission(p,k)
                        if val is None:continue
                        self._note(op='g_opportunity',k=k,threshold=self.config.g_ratio,**val,t=self.virtual_time)
                        if val['score']>=self.config.g_ratio:options.append((-val['score'],k,val))
                    if not options:break
                    _,k,val=min(options,key=lambda x:(x[0],x[1]))
                    self._g_used+=1;self.n_probe+=1
                    self._note(op='value_probe',k=k,stop_id=self._stop_id,used=self._g_used,**val,t=self.virtual_time)
                    if self.measure(*p,k).get('measure_result')=='near' and self.state.channels[k].status=='detected':self._try_clear_at(k,p)
        finally:self._endpoint_busy=False

    def _do_v3_action(self,k,q,kind):
        if self.state.channels[k].status!='detected':return
        if self.config.b_radius and kind=='measure':
            scores,pair=self._b_scores.get(k,({},[]));val=scores.get(tuple(q))
            self._note(op='two_step_probe',k=k,x=float(q[0]),y=float(q[1]),score_terms=val,
                       recovery=any(np.linalg.norm(q-p)<=1e-7 for p in pair),t=self.virtual_time)
        if self.config.h_rho and kind=='aggr_clear':
            self._note(op='wide_optimistic_attempt',k=k,rho=self._region(k)['rho'],limit=self.config.h_rho,t=self.virtual_time)
        super()._do_v3_action(k,q,kind)
        self._endpoint(self.state.pos.copy())

    def scan_at(self,p,*,certificate_mode=False):
        super().scan_at(p,certificate_mode=certificate_mode)
        self._endpoint(self.state.pos.copy())

    def _probe_detected_at_v4(self,p):
        if self.config.g_ratio:self._endpoint(np.asarray(p))
        else:super()._probe_detected_at_v4(p)

def make_runner(robot,cfg):
    set_route_mode(ROUTE_ADAPTIVE_V4)
    if cfg.name in ('baseline','LC','LPC','previous_best'):return base.make_runner(robot,cfg)
    return AggressiveRunner(robot,cfg)

cover_context=base.cover_context
