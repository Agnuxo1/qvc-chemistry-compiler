# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# Research-Project: QVC Chemistry Compiler - Google Verifiable Quantum Circuit Compilation (chemistry task)
# Research-Author: Francisco Angulo de Lafuente | ORCID https://orcid.org/0009-0001-1634-7063 | https://github.com/Agnuxo1
# Research-Date: 2026-10-29/2026-11-10 | Source: https://github.com/Agnuxo1/qvc-chemistry-compiler
# Open source (MIT OR Apache-2.0): keep this notice and credit the author in any copy or derivative work.
"""Simulador propio de kickmix (.kmx) por lotes de bits con enteros de Python.

Reproduce la semántica del artículo oficial (sección II): puertas clásicas reversibles, fases diagonales,
HMR (X-basis: bit aleatorio, fase (-1)^{q·b}, q<-0), R (q<-0, signo aleatorio si q=1), bits clásicos,
condiciones por puerta (if b) y pila de condiciones (valor capturado al hacer PUSH).
HMR sobrescribe el bit (comprobado con kickmix en pruebas/t_hmr*.kmx).

Además registra, para cada puerta Toffoli-like (CCX, CCZ, CSWAP) en orden, cuántos disparos:
  nm  = la ejecutan (condición clásica verdadera)
  act = la puerta cambia algo (CCX: a&b; CSWAP: c&(a!=b); CCZ: a&b&c)
  c1, c2 = control 1 / control 2 a 1 (para detectar controles constantes)
  eq  = disparos con c1 == c2 (para detectar controles iguales)

Ediciones: dict ordinal_toffoli -> acción ('del' borra la puerta; 'cx1' la cambia por CX(b,t) suponiendo a=1;
'cx2' por CX(a,t); 'x' por X(t)).
"""
from __future__ import annotations
import os as _os
_HOME = _os.environ.get("QVC_HOME") or _os.path.abspath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "..")).replace("\\", "/")
import random, sys, time
import numpy as np

TOFF = ('CCX', 'CCZ', 'CSWAP')


def run(kmx_path, syn_bits, mask_bits, exp_phase, nshots, seed=0, edits=None, record=True,
        reg_info=None, progress=False, rare=0, seg=0):
    """syn_bits: lista de 840 enteros (bit s = disparo s); mask_bits: lista de 49140 enteros;
    exp_phase: entero con la fase esperada. Devuelve dict con fallos, Toffolis medios y actividad."""
    rnd = random.Random(seed)
    ALL = (1 << nshots) - 1
    edits = edits or {}
    nq, nb = 892, 101370
    qs = [0] * nq
    bs = [0] * nb
    P = 0
    syn_q = []; mask_b = []
    # registros: se leen de la cabecera del propio archivo
    regs_q = {}; regs_b = {}
    stack = []  # máscaras de condición
    cur = ALL
    tof_total = 0
    rec = []  # (nm, act, c1, c2, eq, hi, lo)
    rare_sets = {}
    ti = -1
    t0 = time.time()
    pend_q = []; pend_b = []
    pc = 0
    acc = [0] * nq; seg_rows = []; live = [False] * nq; live_max = [0]; nlive = [0]
    def touch(q):
        if not live[q]: live[q] = True; nlive[0] += 1
        if nlive[0] > live_max[0]: live_max[0] = nlive[0]
    with open(kmx_path) as f:
        for l in f:
            pc += 1
            if seg and pc % seg == 0:
                seg_rows.append([x.bit_count() for x in acc] + [live_max[0], nlive[0]])
                acc = qs[:]; live_max[0] = nlive[0]
            if progress and pc % 5000000 == 0:
                print('  linea', pc, round(time.time() - t0, 1), 's', flush=True)
            p = l.split()
            op = p[0]
            if op == 'CX':
                t_ = int(p[2][1:])
                if len(p) == 3:
                    if cur == ALL:
                        qs[t_] ^= qs[int(p[1][1:])]
                    else:
                        qs[t_] ^= qs[int(p[1][1:])] & cur
                else:
                    m = cur & bs[int(p[4][1:])]
                    qs[t_] ^= qs[int(p[1][1:])] & m
                if seg: acc[t_] |= qs[t_]; touch(t_); touch(int(p[1][1:]))
                continue
            if op == 'BIT_INVERT':
                m = cur if len(p) == 2 else cur & bs[int(p[3][1:])]
                bs[int(p[1][1:])] ^= m
                continue
            if op == 'APPEND_TO_REGISTER':
                if p[1][0] == 'q': pend_q.append(int(p[1][1:]))
                else: pend_b.append(int(p[1][1:]))
                continue
            if op == 'REGISTER':
                name = p[2].strip('"')
                if pend_q: regs_q[name] = pend_q
                if pend_b: regs_b[name] = pend_b
                pend_q = []; pend_b = []
                continue
            if op == 'INFO_TAG':
                if not syn_q and regs_q:
                    # primera instrucción tras la cabecera: cargar entradas
                    for i in range(70):
                        for k, qq in enumerate(regs_q[f'S{i}']):
                            qs[qq] = syn_bits[i * 12 + k]
                            syn_q.append(qq)
                    for j in range(4095):
                        for k, bb in enumerate(regs_b[f'E{j}']):
                            bs[bb] = mask_bits[j * 12 + k]
                            mask_b.append(bb)
                continue
            # resto de operaciones: condición
            if 'if' in p:
                k = p.index('if')
                m = cur
                for x in p[k + 1:]: m &= bs[int(x[1:])]
                args = p[1:k]
            else:
                m = cur; args = p[1:]
            if seg and op not in ('HMR', 'R', 'BIT_STORE0', 'BIT_STORE1', 'NEG', 'PUSH_CONDITION', 'POP_CONDITION'):
                for x in args:
                    if x[0] == 'q': touch(int(x[1:]))
            if op in TOFF:
                ti += 1
                rare_now = rare
                if seg:
                    for x in args: acc[int(x[1:])] |= qs[int(x[1:])]
                a = int(args[0][1:]); b = int(args[1][1:]); c = int(args[2][1:])
                qa = qs[a] & m; qb = qs[b] & m
                if op == 'CCX':
                    actv = qa & qb
                    if record:
                        rec.append((m.bit_count(), actv.bit_count(), qa.bit_count(), qb.bit_count(),
                                    (~(qa ^ qb) & m).bit_count(), actv.bit_length(), (actv & -actv).bit_length()))
                        if rare_now and 0 < rec[-1][1] <= rare_now: rare_sets[ti] = bits_idx(actv)
                    e = edits.get(ti)
                    if e is None:
                        qs[c] ^= actv
                    elif e == 'del':
                        pass
                    elif e == 'cx1':
                        qs[c] ^= qb
                    elif e == 'cx2':
                        qs[c] ^= qa
                    elif e == 'x':
                        qs[c] ^= m
                    else:
                        raise ValueError(e)
                    if e is None: tof_total += m.bit_count()
                elif op == 'CCZ':
                    actv = qa & qb & qs[c]
                    if record:
                        rec.append((m.bit_count(), actv.bit_count(), qa.bit_count(), qb.bit_count(),
                                    (~(qa ^ qb) & m).bit_count(), actv.bit_length(), (actv & -actv).bit_length()))
                        if rare_now and 0 < rec[-1][1] <= rare_now: rare_sets[ti] = bits_idx(actv)
                    e = edits.get(ti)
                    if e is None:
                        P ^= actv; tof_total += m.bit_count()
                    elif e == 'del':
                        pass
                    elif e == 'cx1':  # CZ(b,c)
                        P ^= qb & qs[c]
                    elif e == 'cx2':
                        P ^= qa & qs[c]
                    else:
                        raise ValueError(e)
                else:  # CSWAP c a b : args[0] control
                    d = (qs[b] ^ qs[c]) & qa
                    if record:
                        rec.append((m.bit_count(), d.bit_count(), qa.bit_count(), ((qs[b] ^ qs[c]) & m).bit_count(), 0,
                                    d.bit_length(), (d & -d).bit_length()))
                        if rare_now and 0 < rec[-1][1] <= rare_now: rare_sets[ti] = bits_idx(d)
                    e = edits.get(ti)
                    if e is None:
                        qs[b] ^= d; qs[c] ^= d; tof_total += m.bit_count()
                    elif e == 'del':
                        pass
                    elif e == 'cx1':  # control siempre 1: SWAP
                        d = (qs[b] ^ qs[c]) & m; qs[b] ^= d; qs[c] ^= d
                    else:
                        raise ValueError(e)
                if seg:
                    for x in args: acc[int(x[1:])] |= qs[int(x[1:])]
                continue
            if op == 'CZ':
                P ^= qs[int(args[0][1:])] & qs[int(args[1][1:])] & m
            elif op == 'SWAP':
                a = int(args[0][1:]); b = int(args[1][1:])
                d = (qs[a] ^ qs[b]) & m; qs[a] ^= d; qs[b] ^= d
                if seg: acc[a] |= qs[a]; acc[b] |= qs[b]
            elif op == 'X':
                qs[int(args[0][1:])] ^= m
                if seg: acc[int(args[0][1:])] |= qs[int(args[0][1:])]
            elif op == 'Z':
                P ^= qs[int(args[0][1:])] & m
            elif op == 'HMR':
                q = int(args[0][1:]); b = int(args[1][1:])
                r = rnd.getrandbits(nshots)
                P ^= qs[q] & r & m
                qs[q] &= ~m
                bs[b] = (bs[b] & ~m) | (r & m)
                if seg and live[q]: live[q] = False; nlive[0] -= 1
            elif op == 'R':
                q = int(args[0][1:])
                r = rnd.getrandbits(nshots)
                P ^= qs[q] & r & m
                qs[q] &= ~m
                if seg and live[q]: live[q] = False; nlive[0] -= 1
            elif op == 'BIT_STORE0':
                bs[int(args[0][1:])] &= ~m
            elif op == 'BIT_STORE1':
                bs[int(args[0][1:])] |= m
            elif op == 'NEG':
                P ^= m
            elif op == 'PUSH_CONDITION':
                stack.append(cur); cur = m
            elif op == 'POP_CONDITION':
                cur = stack.pop()
            else:
                raise ValueError('op desconocida: ' + l)
    # comprobaciones finales
    bad_val = 0
    synset = set(syn_q)
    for i, qq in enumerate(syn_q):
        bad_val |= qs[qq] ^ syn_bits[i]
    for qq in range(nq):
        if qq not in synset: bad_val |= qs[qq]
    bad_ph = (P ^ exp_phase) & ~bad_val & ALL
    out = dict(value_errors=bad_val.bit_count(), phase_errors=bad_ph.bit_count(),
               toffoli_mean=tof_total / nshots, seconds=time.time() - t0, n=nshots,
               bad_val=bad_val, bad_ph=bad_ph)
    if record:
        out['rec'] = np.array(rec, dtype=np.int64)
    out['rare_sets'] = rare_sets
    if seg: out['seg_rows'] = np.array(seg_rows, dtype=np.int64)
    return out


def bits_idx(x):
    out = []
    while x:
        lb = x & -x
        out.append(lb.bit_length() - 1)
        x ^= lb
    return out


def make_shots(nshots, seed):
    """Disparos con la distribución oficial (sample_shots del verificador) y un generador propio."""
    sys.path.insert(0, (_os.environ.get("DFTHC_DATA", _HOME + "/data") + "/verifiers"))
    sys.path.insert(0, (_HOME + "/compiler/env"))
    try:
        from dqi import verify_submission_dqi as v
    except ImportError:
        import verify_submission_dqi as v
    import kickmix as km
    spec = v.ProblemSpecDQI.benchmark_instance(num_shots=nshots)
    tables = v.FieldTables(km.GF2Field(12))
    rng = np.random.default_rng(seed)
    syn, mbuc, ph = v.sample_shots(spec, tables, rng, nshots)
    return syn, mbuc.astype(np.uint16), ph


def make_shots_by_weight(per_weight, seed, weights=range(36)):
    """per_weight disparos de cada peso, en orden creciente de peso. Devuelve también el peso de cada disparo."""
    sys.path.insert(0, (_os.environ.get("DFTHC_DATA", _HOME + "/data") + "/verifiers"))
    sys.path.insert(0, (_HOME + "/compiler/env"))
    try:
        from dqi import verify_submission_dqi as v
    except ImportError:
        import verify_submission_dqi as v
    import kickmix as km
    spec = v.ProblemSpecDQI.benchmark_instance(num_shots=per_weight)
    tables = v.FieldTables(km.GF2Field(12))
    rng = np.random.default_rng(seed)
    S, M, P, W = [], [], [], []
    for t in weights:
        wp = np.zeros(36); wp[t] = 1.0
        a, b, c = v.sample_shots(spec, tables, rng, per_weight, wp)
        S.append(a); M.append(b); P.append(c); W.append(np.full(per_weight, t))
    return np.concatenate(S), np.concatenate(M), np.concatenate(P), np.concatenate(W)


def pack(syn, mbuc, ph):
    """(N,70),(N,4095),(N,) -> listas de enteros bit-paralelos."""
    N = len(ph)
    def col_ints(vals, width):
        bits = ((vals[:, :, None] >> np.arange(width)) & 1).astype(np.uint8)  # N, R, w
        bits = bits.reshape(N, -1)  # N, R*w
        packed = np.packbits(bits, axis=0, bitorder='little')  # ceil(N/8), R*w
        return [int.from_bytes(packed[:, j].tobytes(), 'little') for j in range(packed.shape[1])]
    s = col_ints(syn, 12)
    mk = []
    for j0 in range(0, mbuc.shape[1], 64):
        mk.extend(col_ints(mbuc[:, j0:j0 + 64].astype(np.int64), 12))
    pb = np.packbits(ph.astype(np.uint8), bitorder='little')
    return s, mk, int.from_bytes(pb.tobytes(), 'little')


if __name__ == '__main__':
    import argparse, json, pickle
    ap = argparse.ArgumentParser()
    ap.add_argument('kmx'); ap.add_argument('--n', type=int, default=4096); ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--out', default=None); ap.add_argument('--edits', default=None)
    ap.add_argument('--seg', type=int, default=0, help='tramos de L líneas para ocupación por qubit')
    ap.add_argument('--rare', type=int, default=0, help='guardar disparos activos de puertas con act <= rare')
    ap.add_argument('--por-peso', type=int, default=0, help='disparos por peso 0..35, ordenados (sustituye a --n)')
    a = ap.parse_args()
    t = time.time()
    if a.por_peso:
        syn, mbuc, ph, W = make_shots_by_weight(a.por_peso, a.seed)
        a.n = len(ph)
        if a.out: np.save(a.out + '_pesos.npy', W)
    else:
        syn, mbuc, ph = make_shots(a.n, a.seed)
    s, mk, pe = pack(syn, mbuc, ph)
    print('disparos listos', round(time.time() - t, 1), flush=True)
    edits = None
    if a.edits:
        edits = {int(k): v for k, v in json.load(open(a.edits)).items()}
    r = run(a.kmx, s, mk, pe, a.n, seed=a.seed + 7777, edits=edits, progress=True, rare=a.rare, seg=a.seg)
    wt = (syn != 0).sum(1)
    print(json.dumps({k: v for k, v in r.items() if k not in ('rec', 'bad_val', 'bad_ph', 'rare_sets', 'seg_rows')}), flush=True)
    if a.out:
        np.save(a.out, r['rec'])
        if a.seg: np.save(a.out + '_seg.npy', r['seg_rows'])
        bad = r['bad_val'] | r['bad_ph']
        idx = [i for i in range(a.n) if (bad >> i) & 1]
        json.dump(dict(summary={k: v for k, v in r.items() if k not in ('rec', 'bad_val', 'bad_ph', 'rare_sets', 'seg_rows')}, bad_idx=idx,
                       rare_sets={str(k): v for k, v in r['rare_sets'].items()}, syn_nz=[int(x) for x in wt[idx]]),
                  open(a.out + '.json', 'w'))

# qvc-chemistry-compiler :: (c) 2026 Francisco Angulo de Lafuente :: ORCID 0009-0001-1634-7063 :: MIT :: cite the author when reusing
