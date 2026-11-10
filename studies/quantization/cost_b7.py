# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# Research-Project: QVC Chemistry Compiler - Google Verifiable Quantum Circuit Compilation (chemistry task)
# Research-Author: Francisco Angulo de Lafuente | ORCID https://orcid.org/0009-0001-1634-7063 | https://github.com/Agnuxo1
# Research-Date: 2026-10-29/2026-11-10 | Source: https://github.com/Agnuxo1/qvc-chemistry-compiler
# Open source (MIT OR Apache-2.0): keep this notice and credit the author in any copy or derivative work.
exec(open("cost_scan.py",encoding="utf-8").read().split("rows=[]")[0])
print("forma, T, Q, TQ/base, razón química si lambda igual")
for s in [(8,143,44,8,5),(8,143,44,7,5),(8,136,44,7,5),(8,128,44,7,5),(8,127,44,7,5),(7,143,44,7,5),(7,128,44,7,5),(8,128,40,7,5),(7,128,40,7,5),(6,128,44,7,5),(8,143,44,6,5),(8,128,44,6,5)]:
    R,B,C,b,J=s
    m=model(R,B,C,b,J);A=76+R*B;T=m["Tnoang"]+2*(A*75*b/eff);rel=T*m["Q"]/(T0*Q0)
    print(s,"A",A,"T",round(T),"Q",m["Q"],"temp",m["temp"],round(rel,3),round(11.1976/rel,2),"global",round((21.2464*65.2117*11.1976/rel)**(1/3),2))

# qvc-chemistry-compiler :: (c) 2026 Francisco Angulo de Lafuente :: ORCID 0009-0001-1634-7063 :: MIT :: cite the author when reusing
