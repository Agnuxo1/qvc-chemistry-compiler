#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: Apache-2.0
# Research-Project: reversible-ancilla-scheduling
# Research-Date: 2026-11-04
# Research-ORCID: https://orcid.org/0009-0001-1634-7063
# Attribution-Recorded-On: 2026-11-06
# Reuse: preserve applicable notices and cite the original author.

"""Experimento controlado: canjear profundidad (gratis) por qubits (caros).

HIPOTESIS (congelada antes de ejecutar)
H: en el modelo de coste de este concurso, serializar un acumulador de productos
   (computa - usa - descomputa de uno en uno) reduce el pico de qubits SIN
   aumentar el numero de Toffolis, y por tanto reduce el coste Q*C.

POR QUE IMPORTA
Las tres funciones de coste oficiales son Q*C, R(eps)*Q**2*T y lambda_eff*T*Q,
y **`reaction_depth` no aparece en ninguna**: la profundidad es gratis. Dos
medidas previas han cerrado las otras vias:
  - La reasignacion de indices no da nada: holgura 0 en el envio publico
    (invsqrt 63=63=63, quimica 126=126=126) y tambien en la referencia de
    Google (260=260=260), porque el CircuitBuilder de kickmix ya empaqueta
    optimo con alloc_qubits/free.
  - El canje de precision por recursos en invsqrt esta agotado:
    worst_error_over_tolerance = 0,9993 e identico en 4 salts (determinista).
Queda esta: que el ALGORITMO necesite menos qubits a la vez. Este experimento
mide si el modelo de coste premia de verdad ese canje, en un nucleo
representativo, antes de invertir en reconstruir invsqrt entero.

DISENO
Nucleo: acumular k productos AND de pares de bits en un registro objetivo, que
es la forma de los productos parciales de los multiplicadores de Horner que usa
el circuito Newton-Raphson de invsqrt.
  Variante PARALELO:    reserva k scratch, init_and los k, suma, del_and los k.
  Variante SERIALIZADO: por cada i: reserva 1, init_and, suma, del_and, libera.
Control: ambas variantes calculan LO MISMO; se comprueba que coinciden
simulando las dos con los mismos valores de entrada y comparando el objetivo.
Variables medidas: num_qubits (Q), num_toffoli_like (C), reaction_depth, coste Q*C.

Solo CPU. No toca nada fuera de su carpeta de salida.
"""

import json
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
SALIDA = os.path.join(AQUI, "resultado")

import kickmix as km  # noqa: E402

ANCHO = 16          # bits del acumulador
KS = [2, 4, 8, 16, 32]   # numero de productos parciales


def construir(k, ancho, serializado):
    """Acumula k productos AND en un objetivo. Devuelve (circuito, registros)."""
    b = km.CircuitBuilder()
    objetivo = b.create_quantum_register(ancho, "acc")
    a = b.create_quantum_register(k, "a")
    c = b.create_quantum_register(k, "c")

    if serializado:
        # Un solo scratch vivo a la vez: pico minimo, profundidad maxima.
        for i in range(k):
            s = b.alloc_qubits(1)
            b.init_and(a[i], c[i], s)
            b.iadd(s, target=objetivo)
            b.del_and(a[i], c[i], s)
            b.free(s)
    else:
        # Los k scratch vivos a la vez: pico maximo, profundidad minima.
        ss = [b.alloc_qubits(1) for _ in range(k)]
        for i in range(k):
            b.init_and(a[i], c[i], ss[i])
        for i in range(k):
            b.iadd(ss[i], target=objetivo)
        for i in range(k):
            b.del_and(a[i], c[i], ss[i])
        for s in ss:
            b.free(s)

    return b.finish_circuit(), (objetivo, a, c)


def leer(obj, nombre):
    """kickmix expone unos como propiedad y otros como metodo: vale para ambos."""
    a = getattr(obj, nombre)
    return a() if callable(a) else a


def medir(circuito):
    st = leer(circuito, "operation_statistics")
    Q = leer(circuito, "num_qubits")
    C = leer(st, "num_toffoli_like")
    return {"Q": Q, "C_toffoli_like": C,
            "reaction_depth": leer(circuito, "reaction_depth"),
            "instrucciones": leer(st, "num_instructions"),
            "coste_Q_por_C": Q * C}


def comprobar_equivalencia(k, ancho):
    """Control: las dos variantes deben dar el MISMO acumulador."""
    salidas = []
    for serializado in (False, True):
        circuito, (objetivo, a, c) = construir(k, ancho, serializado)
        sim = km.Simulator(batch_size=1)
        # Entradas deterministas, escritas antes de ejecutar el circuito:
        # a[i] = 1 siempre, c[i] = 1 solo en los pares, asi que el acumulador
        # debe acabar valiendo el numero de indices pares.
        # La firma es posicional: (index, shot_index, new_value).
        for i in range(k):
            sim.write_within_shot(a[i], 0, True)
            sim.write_within_shot(c[i], 0, i % 2 == 0)
        sim.do(circuito)
        bits = [bool(sim.read_within_shot(objetivo[j], 0))
                for j in range(ancho)]
        salidas.append(sum(1 << j for j, v in enumerate(bits) if v))
    esperado = sum(1 for i in range(k) if i % 2 == 0)
    return {"paralelo": salidas[0], "serializado": salidas[1],
            "esperado": esperado,
            "coinciden": salidas[0] == salidas[1],
            "correcto": salidas[0] == esperado and salidas[1] == esperado}


def main():
    os.makedirs(SALIDA, exist_ok=True)
    informe = {
        "hipotesis": ("Serializar el acumulador reduce el pico de qubits SIN aumentar los "
                      "Toffolis, y por tanto reduce el coste Q*C."),
        "por_que": ("reaction_depth no entra en ninguna de las 3 funciones de coste del "
                    "concurso: la profundidad es gratis. Las otras vias ya estan medidas y "
                    "cerradas (reasignacion de indices: holgura 0; precision: margen 0,07 %)."),
        "ancho_acumulador": ANCHO,
        "filas": [],
    }

    for k in KS:
        fila = {"k": k}
        for nombre, serializado in (("paralelo", False), ("serializado", True)):
            circuito, _ = construir(k, ANCHO, serializado)
            fila[nombre] = medir(circuito)
        p, s = fila["paralelo"], fila["serializado"]
        fila["ganancia"] = {
            "Q": "%d -> %d" % (p["Q"], s["Q"]),
            "C_igual": p["C_toffoli_like"] == s["C_toffoli_like"],
            "factor_coste": (p["coste_Q_por_C"] / s["coste_Q_por_C"]
                             if s["coste_Q_por_C"] else None),
            "profundidad": "%d -> %d" % (p["reaction_depth"], s["reaction_depth"]),
        }
        try:
            fila["control_equivalencia"] = comprobar_equivalencia(k, ANCHO)
        except Exception as e:
            fila["control_equivalencia"] = {"error": "%s: %s" % (type(e).__name__, e)}
        informe["filas"].append(fila)
        print("[prof] k=%-3d Q %s  C_igual=%s  factor_coste=%.3f" % (
            k, fila["ganancia"]["Q"], fila["ganancia"]["C_igual"],
            fila["ganancia"]["factor_coste"] or 0), flush=True)

    ok = [f for f in informe["filas"] if f["ganancia"]["C_igual"]
          and (f["ganancia"]["factor_coste"] or 0) > 1.0]
    informe["veredicto"] = {
        "hipotesis_confirmada": len(ok) == len(informe["filas"]),
        "filas_con_ganancia_sin_coste_en_toffolis": len(ok),
        "de": len(informe["filas"]),
        "lectura": ("Si se confirma, el canje profundidad->qubits es beneficio neto en este "
                    "modelo de coste, y reconstruir invsqrt serializando su aritmetica es la "
                    "linea correcta. Si no, hay que atacar el numero de Toffolis."),
    }

    with open(os.path.join(SALIDA, "profundidad.json"), "w", encoding="utf-8") as f:
        json.dump(informe, f, ensure_ascii=False, indent=2)

    print(json.dumps({"veredicto": informe["veredicto"],
                      "filas": [{"k": f["k"], **f["ganancia"],
                                 "control": f.get("control_equivalencia")}
                                for f in informe["filas"]]},
                     ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
