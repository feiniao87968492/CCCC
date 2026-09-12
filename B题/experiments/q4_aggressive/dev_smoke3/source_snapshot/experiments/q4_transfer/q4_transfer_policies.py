"""Incremental Q3 JSO transfer and independent Q4 solver-family ablations."""
from dataclasses import dataclass
from pathlib import Path
import sys

import numpy as np

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'simulator_automation'),str(ROOT/'experiments/q4_ablation')]
from q4_ablation_policies import (AblationRunner,Config as OldConfig,cover_context,
                                 VARIANTS as OLD_VARIANTS,make_runner as old_make_runner)
from q4_cover import cover_points
from q4_localize import legal_xy,optical_cover_points
from q4_policy import pending_batch_order,ROUTE_ADAPTIVE_V4,set_route_mode
from q4_runner import Q4Runner,MAX_MEASURE


@dataclass(frozen=True)
class Config(OldConfig):
    selective: bool=False
    optimistic: bool=False
    optimistic_rho: float=80.
    reception_gate: float=.7
    insert_cap: float=0.
    viewpoint: str='baseline'
    recovery: bool=False
    optical_cells: int=0
    shorten: bool=False


VARIANTS={
    'baseline':Config('baseline'),
    'previous_best':Config('previous_best',route='center',reuse=True,clear_rho=160,outer_radius=1900),
    'J':Config('J',route='center'),
    'S':Config('S',selective=True),
    'O':Config('O',optimistic=True),
    'JS':Config('JS',route='center',selective=True),
    'JO':Config('JO',route='center',optimistic=True),
    'SO':Config('SO',selective=True,optimistic=True),
    'JSO':Config('JSO',route='center',selective=True,optimistic=True),
    'insert80':Config('insert80',insert_cap=80),
    'insert200':Config('insert200',insert_cap=200),
    'insert400':Config('insert400',insert_cap=400),
    'aligned':Config('aligned',viewpoint='aligned'),
    'doptimal':Config('doptimal',viewpoint='doptimal'),
    'bracket':Config('bracket',recovery=True),
    'optical2':Config('optical2',optical_cells=2),
    'optical4':Config('optical4',optical_cells=4),
    'short_clear':Config('short_clear',shorten=True),
    'JSO_p50':Config('JSO_p50',route='center',selective=True,optimistic=True,reception_gate=.5),
    'JSO_p85':Config('JSO_p85',route='center',selective=True,optimistic=True,reception_gate=.85),
    'JSO_r120':Config('JSO_r120',route='center',selective=True,optimistic=True,optimistic_rho=120),
    'JSO_r160':Config('JSO_r160',route='center',selective=True,optimistic=True,optimistic_rho=160),
    'JSO_compact':Config('JSO_compact',route='center',selective=True,optimistic=True,outer_radius=1900),
    'JSO_outer1980':Config('JSO_outer1980',route='center',selective=True,optimistic=True,outer_radius=1980),
    'S_doptimal':Config('S_doptimal',selective=True,viewpoint='doptimal'),
    'SO_doptimal':Config('SO_doptimal',selective=True,optimistic=True,viewpoint='doptimal'),
    'S_dopt_short':Config('S_dopt_short',selective=True,viewpoint='doptimal',shorten=True),
    'JSO_compact_dopt':Config('JSO_compact_dopt',route='center',selective=True,optimistic=True,
                              outer_radius=1900,viewpoint='doptimal'),
}


def line_estimate(history,region):
    positive=[h for h in history if h['result']=='direction']
    if len(positive)<2:
        return None
    angles=np.deg2rad([h['svd'] for h in positive])
    normals=np.c_[-np.sin(angles),np.cos(angles)]
    if np.linalg.cond(normals)>30:
        return None
    rhs=np.array([n@h['pos'] for n,h in zip(normals,positive)])
    q=np.linalg.lstsq(normals,rhs,rcond=None)[0]
    if not legal_xy(q):
        return None
    v=np.asarray(region['verts']);edges=np.roll(v,-1,axis=0)-v;offset=q-v
    cross=edges[:,0]*offset[:,1]-edges[:,1]*offset[:,0]
    if not (np.all(cross>=-1e-7) or np.all(cross<=1e-7)):
        return None
    return q


def short_clear_point(region,pos):
    center=np.asarray(region['center']);v=np.asarray(region['verts'])
    slack=max(0.,20.-float(np.max(np.linalg.norm(v-center,axis=1)))-1e-5)
    toward=np.asarray(pos)-center;d=float(np.linalg.norm(toward))
    q=center+toward*min(1.,slack/max(d,1e-12))
    return q if legal_xy(q) and np.max(np.linalg.norm(v-q,axis=1))<20 else center


def make_runner(robot,config):
    set_route_mode(ROUTE_ADAPTIVE_V4)
    if config.name=='baseline':
        return Q4Runner(robot)
    if config.name=='previous_best':
        return old_make_runner(robot,OLD_VARIANTS['proxy_reuse_early_compact'])
    return TransferRunner(robot,config)


class TransferRunner(AblationRunner):
    def __init__(self,robot,config):
        super().__init__(robot,config)
        self._supplementing=False
        self._last_optimistic={}
        self._optimistic_count={k:0 for k in self.state.channels}
        self._estimate_cache={}
        self._optical_cache={}

    def _positive_version(self,k):
        return sum(h['result'] in ('direction','near') for h in self.state.channels[k].history)

    def _estimate(self,k):
        version=self._positive_version(k)
        cached=self._estimate_cache.get(k)
        if cached is None or cached[0]!=version:
            cached=(version,line_estimate(self.state.channels[k].history,self._region(k)))
            self._estimate_cache[k]=cached
        return cached[1]

    def _optimistic_available(self,k):
        return self._optimistic_count[k]<2 and self._last_optimistic.get(k)!=self._positive_version(k)

    def _adaptive_task(self,k):
        region=self._region(k)
        if self.config.optimistic:
            if region is None:
                raise RuntimeError('empty positive region')
            center=region['center'];rho=region['rho']
            tried=any(np.linalg.norm(center-q)<1e-7 for q in self.failed_clear_points[k])
            if rho<=20-1e-6 and not tried:
                q,kind=center,'cert_clear'
            else:
                estimate=self._estimate(k)
                if (estimate is not None and rho<=self.config.optimistic_rho
                    and self._optimistic_available(k)
                    and all(np.linalg.norm(estimate-p)>1. for p in self.failed_clear_points[k])):
                    q,kind=estimate,'aggr_clear'
                elif self.state.channels[k].extra_measures<MAX_MEASURE:
                    candidates=self._refinement_points(k,region)
                    q,kind=(candidates[0],'measure') if candidates else (center,'optical')
                else:
                    q,kind=center,'optical'
        else:
            q,kind=super()._adaptive_task(k)
        if self.config.optical_cells and kind=='measure' and region['rho']<=60:
            version=self._positive_version(k)
            cached=self._optical_cache.get(k)
            if cached is None or cached[0]!=version:
                cached=(version,optical_cover_points(region['verts']))
                self._optical_cache[k]=cached
            if len(cached[1])<=self.config.optical_cells:
                self._note(op='early_optical',k=k,cells=len(cached[1]),t=self.virtual_time)
                q,kind=region['center'],'optical'
        if self.config.shorten and kind=='cert_clear':
            q=short_clear_point(region,self.state.pos)
        return q,kind

    def _do_v3_action(self,k,q,kind):
        if self.config.optimistic and kind=='aggr_clear':
            if not self._optimistic_available(k):
                return
            self._last_optimistic[k]=self._positive_version(k)
            self._optimistic_count[k]+=1
            self._note(op='optimistic_attempt',k=k,positive_version=self._positive_version(k),
                       trial=self._optimistic_count[k],t=self.virtual_time)
        super()._do_v3_action(k,q,kind)
        if self.config.selective:
            self._supplement(self.state.pos.copy())

    def _useful(self,p,k):
        history=self.state.channels[k].history
        if any(np.linalg.norm(p-h['pos'])<=1 for h in history):
            return None
        region=self._region(k)
        if region is None or region['rho']<=40:
            return None
        if (self.config.optimistic and region['rho']<=self.config.optimistic_rho
            and self._estimate(k) is not None and self._optimistic_available(k)):
            return None
        center=region['center'];distance=float(np.linalg.norm(center-p))
        if distance>1100:
            return None
        bearings=[h for h in history if h['result']=='direction']
        if not bearings:
            return None
        vec=center-p;best=0.
        for h in bearings:
            old=center-h['pos']
            best=max(best,abs(float(vec[0]*old[1]-vec[1]*old[0]))/
                     max(float(np.linalg.norm(vec)*np.linalg.norm(old)),1e-9))
        if best<np.sin(np.deg2rad(12)) and distance>=.5*np.linalg.norm(center-bearings[-1]['pos']):
            return None
        probability=self._reception_belief(k).reception_probability(p)
        return (probability,best) if probability>=self.config.reception_gate else None

    def _supplement(self,p):
        if self._supplementing:
            return
        self._supplementing=True
        try:
            for k in list(self.state.pending_detected()):
                useful=self._useful(p,k)
                if useful is None:
                    continue
                self.n_probe+=1
                self._note(op='selective_probe',k=k,probability=useful[0],parallax_sine=useful[1],t=self.virtual_time)
                if self.measure(*p,k).get('measure_result')=='near':
                    self._try_clear_at(k,p)
        finally:
            self._supplementing=False

    def _probe_detected_at_v4(self,p):
        if self.config.selective:
            self._supplement(p)
        else:
            super()._probe_detected_at_v4(p)

    def _next_cover_xy(self):
        if self.config.viewpoint!='baseline':
            need=sorted(self._cover_need()-self.cover_visited)
            if need:
                pts=cover_points()
                return pts[min(need,key=lambda i:np.linalg.norm(pts[i]-self.state.pos))]
            return None
        return super()._next_cover_xy()

    def _recovery_pair(self,k,region):
        history=self.state.channels[k].history
        bearings=[h for h in history if h['result']=='direction']
        if not bearings or history[-1]['result']!='no_signal':
            return []
        last=bearings[-1];origin=np.asarray(last['pos']);a=np.deg2rad(last['svd'])
        axis=np.array([np.cos(a),np.sin(a)]);lateral=np.array([-axis[1],axis[0]])
        minimum=float(np.min((region['verts']-origin)@axis))
        if minimum<=30:
            return []
        along=min(80.,.4*minimum);across=.75*along
        pair=[origin+along*axis+sign*across*lateral for sign in (-1,1)]
        if not all(legal_xy(p) and np.max(np.dot(p-origin,p-origin)-
                       2*(region['verts']-origin)@(p-origin)) < -1e-6 for p in pair):
            return []
        fresh=[p for p in pair if all(np.linalg.norm(p-h['pos'])>1 for h in history)]
        fresh.sort(key=lambda p:np.linalg.norm(p-self.state.pos))
        return fresh

    def _refinement_points(self,k,region):
        points=super()._refinement_points(k,region)
        history=self.state.channels[k].history
        bearings=[h for h in history if h['result']=='direction']
        if self.config.viewpoint=='doptimal' and points:
            belief=self._reception_belief(k);samples=belief.points
            fisher=np.tile(np.eye(2)/(region['rho']+10)**2,(len(samples),1,1))
            scale=np.deg2rad(1.005)**2
            for h in bearings:
                v=samples-h['pos'];n=np.c_[-v[:,1],v[:,0]]/np.maximum((v*v).sum(axis=1)[:,None],25.)
                fisher+=n[:,:,None]*n[:,None,:]/scale
            before=np.linalg.det(fisher)
            next_cover=self._next_cover_xy()
            def score(p):
                v=samples-p;n=np.c_[-v[:,1],v[:,0]]/np.maximum((v*v).sum(axis=1)[:,None],25.)
                after=np.linalg.det(fisher+n[:,:,None]*n[:,None,:]/scale)
                weights=(belief.weights*belief._heard(p)).sum(axis=(1,2))
                gain=float(weights@(.5*np.log(after/before)))
                extra=float(np.linalg.norm(p-self.state.pos))
                if next_cover is not None:
                    extra+=float(np.linalg.norm(next_cover-p)-np.linalg.norm(next_cover-self.state.pos))
                return gain/(8+max(extra,0)/5)
            points=sorted(points,key=score,reverse=True)
        if self.config.recovery or (self.config.viewpoint!='baseline' and len(bearings)==1):
            pair=self._recovery_pair(k,region)
            if pair:
                points=pair+[p for p in points if all(np.linalg.norm(p-q)>1 for q in pair)]
        return points

    def _select(self,tasks,kinds):
        if self.config.insert_cap:
            covers=[(ident,p) for ident,p in tasks if ident[0]=='cover']
            if covers:
                order=pending_batch_order(self.state.pos,covers)
                cover_id=order[0];u=dict(covers)[cover_id]
                candidates=[]
                for ident,p in tasks:
                    if ident[0]!='source':
                        continue
                    extra=float(np.linalg.norm(p-self.state.pos)+np.linalg.norm(u-p)-np.linalg.norm(u-self.state.pos))
                    if extra<=self.config.insert_cap:
                        candidates.append((extra,0 if 'clear' in kinds[ident] else 1,ident))
                if candidates:
                    return min(candidates)[2]
                return cover_id
        return super()._select(tasks,kinds)
