"""Seeded spawn adapter; uses the official verifier's public seed argument.

Scheduler pattern credited to manwithacat/verify_parallel.py, Apache-2.0.
An explicit seed makes logical shots and simulator seeds identical across
different circuit hashes. No sampling or scoring code is changed.
"""
from concurrent.futures import ProcessPoolExecutor
import multiprocessing as mp
import verify_parallel as vp


def worker(job):
    load_args,salt,seed,k,n=job
    module,circuit,spec=vp.load(*load_args)
    def run_share(fn,tasks,max_workers):
        raise vp._Collected([fn(task) for task in tasks[k::n]])
    module._run_parallel=run_share
    try:module.verify(circuit,spec,salt=salt,seed=seed,max_workers=n)
    except vp._Collected as collected:return collected.results
    raise RuntimeError('Verifier did not dispatch batches')


def verify_seeded_spawned(load_args,salt,seed,workers):
    with ProcessPoolExecutor(max_workers=workers,mp_context=mp.get_context('spawn')) as pool:
        shares=list(pool.map(worker,[(load_args,salt,seed,k,workers) for k in range(workers)]))
    module,circuit,spec=vp.load(*load_args)
    def gathered(fn,tasks,max_workers):
        assert sum(map(len,shares))==len(tasks)
        results=[None]*len(tasks)
        for k,share in enumerate(shares):results[k::workers]=share
        return results
    original=module._run_parallel;module._run_parallel=gathered
    try:return module.verify(circuit,spec,salt=salt,seed=seed,max_workers=workers)
    finally:module._run_parallel=original
