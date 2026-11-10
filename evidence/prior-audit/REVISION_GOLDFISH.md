# Revisión independiente de la entrega

Fecha: 10-11-2026. Método: adaptación acotada de [Elephant–Goldfish Model](https://github.com/google/elephant-goldfish-model), con un revisor `cog-goldfish` iniciado mediante `fork_turns=none`, sin heredar esta conversación. Una ronda, lentes crítico y deriva. No se declara convergencia de dos rondas ni una certificación EGM de cinco etapas. La exclusión de instrucciones generales del host no se ensayó por separado.

## Resultado

**Sin discrepancias demostradas dentro del alcance documental asignado.** El revisor leyó las dos lentes, la rúbrica, la entrega y los siete archivos de contexto enumerados debajo. No ejecutó generadores ni simulaciones; las pruebas de laboratorio se realizaron por el agente principal y se conservan por separado.

El revisor recalculó:

- Mejora sobre gengsr: 0,257030 %; sobre la base: 0,315069 %.
- Coste de química: 298.729.845,5264178.
- Margen hasta error_2=20 mHa: 0,021502892 mHa.
- Índice local de rendimiento A: 25,2098282614; control con fuentes: 2,2395660296.
- Volumen de los dos circuitos de referencia: 886.697.901 bytes.

También contrastó los 18 hashes de la prueba integrada con el manifiesto del control con fuentes y el SHA-256 del generador con su prueba. Todos coincidieron.

## Documentos de la revisión

Objetivo: `ENTREGA_CODEX.md`.

Contexto suministrado:

1. `RUBRICA_REVISION.md`.
2. `README.md`.
3. `THIRD_PARTY_NOTICES.md`.
4. `candidato-rendimiento-s37/MANIFIESTO.json`.
5. `candidato-con-fuentes-s37/MANIFIESTO.json`.
6. `resultados/full-source-generation-proof.json`.
7. `generar_tres_tareas.py`.

Lentes leídas: `critico.md` y `deriva.md`, de la adaptación local de cognición extendida.

## Observaciones

La revisión no abrió los ZIP, la receta, `reconstruir_quimica.py`, los recibos individuales de Windows/DQI/invsqrt/auxiliares, los datos y runtime externos, las reglas de Kaggle o el repositorio de James Day. No comprobó de forma independiente cada afirmación de esos materiales. La portabilidad Windows-Linux está sustentada por las pruebas ejecutadas del agente principal; la revisión contrastó parcialmente sus resúmenes y hashes.

No se detectaron hallazgos graves que resolver. La incorporación posterior de este informe y del estado factual del Guardián no altera las cifras, código generador o hashes de los dos ZIP revisados documentalmente.
