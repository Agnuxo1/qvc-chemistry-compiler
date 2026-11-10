# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# Research-Project: QVC Chemistry Compiler - Google Verifiable Quantum Circuit Compilation (chemistry task)
# Research-Author: Francisco Angulo de Lafuente | ORCID https://orcid.org/0009-0001-1634-7063 | https://github.com/Agnuxo1
# Research-Date: 2026-10-29/2026-11-10 | Source: https://github.com/Agnuxo1/qvc-chemistry-compiler
# Open source (MIT OR Apache-2.0): keep this notice and credit the author in any copy or derivative work.
# Margin per task with the official formulas. Measured inputs: fases_inv.json and dqi_base.json.
import math, json
REF_I=2076774.233715282; REF_D=24439463583672.93
Q_I=62; TOF_I=1281.4557; NROT=41; TBASE=1.0; MARG=3.1762e-12
Q_D=892; T_D=395394.06; R_D=1.1912604648
CHEM=11.1976
def rot_t(n,m): return 0.56*math.log2(1/(math.pi*m/n))+5.3
def inv(Q=Q_I,tof=TOF_I,n=NROT,m=MARG):
    C=tof+(TBASE+n*rot_t(n,m))/4
    return Q*C,C
def dqi(Q=Q_D,T=T_D,R=R_D): return R*Q*Q*T
s0,c0=inv(); d0=dqi()
gm=lambda ri,rd,rc=CHEM:(ri*rd*rc)**(1/3)
print(f'invsqrt base: C {c0:.1f} score {s0:.0f} razon {REF_I/s0:.3f}; rotaciones {NROT*rot_t(NROT,MARG)/4:.1f} eq ({NROT*rot_t(NROT,MARG)/4/c0:.1%}); DQI base {d0:.4e} razon {REF_D/d0:.3f}; media {gm(REF_I/s0,REF_D/d0):.3f}')
print('--- invsqrt')
casos=[('-1 qubit',dict(Q=61)),('-2 qubits',dict(Q=60)),('-4 qubits',dict(Q=58)),('-25 Toffolis (equivale a 1 qubit)',dict(tof=TOF_I-25.4)),('-1 rotacion y 3 Toffolis de seleccion',dict(n=40,tof=TOF_I-3)),('-8 rotaciones y 30 Toffolis (fusion de pasadas)',dict(n=33,tof=TOF_I-30)),('margen x2',dict(m=2*MARG)),('-5 % filas ida y vuelta (-31)',dict(tof=TOF_I-31)),('-15 % tabla (-44)',dict(tof=TOF_I-44)),('paquete prudente: 61 q, -40 Toffolis',dict(Q=61,tof=TOF_I-40)),('paquete ambicioso: 60 q, -100 Toffolis, -4 rot',dict(Q=60,tof=TOF_I-100,n=37))]
for n,k in casos:
    s,c=inv(**k); r=REF_I/s
    print(f'{n:52s} C {c:7.1f} razon {r:6.2f} ({r/(REF_I/s0)-1:+.1%}) media {gm(r,REF_D/d0):.3f}')
print('--- DQI')
casos=[('-1 qubit',dict(Q=891)),('-4 qubits',dict(Q=888)),('-12 qubits',dict(Q=880)),('suelo absoluto 840 qubits',dict(Q=840)),('-1.000 Toffolis',dict(T=T_D-1000)),('vuelta de extract en coste de ida (-37,7k)',dict(T=T_D-37734)),('vuelta de synthesis en coste de ida (-8,8k)',dict(T=T_D-8817)),('ida = vuelta en las tres fases (-48,4k)',dict(T=T_D-48422)),('mitad de esa asimetria (-24k)',dict(T=T_D-24200)),('1 fallo por tirada (k=1)',dict(R=1.1967)),('paquete prudente: 890 q, -24k',dict(Q=890,T=T_D-24200)),('paquete ambicioso: 884 q, -48k',dict(Q=884,T=T_D-48422))]
for n,k in casos:
    r=REF_D/dqi(**k)
    print(f'{n:52s} razon {r:6.2f} ({r/(REF_D/d0)-1:+.1%}) media {gm(REF_I/s0,r):.3f}')
print('--- conjunto y lideres')
L=(29.30/24.94)**3
print('producto lideres',L)
for nombre,fi,fd in (('prudente',REF_I/inv(Q=61,tof=TOF_I-40)[0],REF_D/dqi(Q=890,T=T_D-24200)),('ambicioso',REF_I/inv(Q=60,tof=TOF_I-100,n=37)[0],REF_D/dqi(Q=884,T=T_D-48422))):
    p=(fi/(REF_I/s0))*(fd/(REF_D/d0))
    print(nombre,'invsqrt',round(fi,2),'dqi',round(fd,2),'factor conjunto',round(p,3),'media con quimica 11,20',round(gm(fi,fd),2),'con quimica 12,5',round(gm(fi,fd,12.5),2),'parte de 1,62 explicada',round(math.log(p)/math.log(L),3),'quimica necesaria para 29,30',round(29.30**3/(fi*fd),2))

# qvc-chemistry-compiler :: (c) 2026 Francisco Angulo de Lafuente :: ORCID 0009-0001-1634-7063 :: MIT :: cite the author when reusing
