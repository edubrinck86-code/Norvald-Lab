"""Camada de medidas do Δ_herd (criada em 11/11/2026).

Por quê: a coleta do Δ_herd precisava das medidas definidas e testadas antes
do registro no OSF, e o Eduardo pediu medir também do jeito de Hao et al.
(2026). As duas famílias de medidas leem a mesma tabela de observações
(`ObservationTable`) e nada mais: o carregador é o único lugar que abre o RAW.

- `criteria/`: as medidas A–J do bloco 1.2 (studies/herd/criterios-1.2.md).
- `hao/`: as medidas do §3 do protocolo de Hao et al. (studies/herd/hao-2026-protocolo.md).
- `reasons/`: "mesma resposta, razões diferentes" (exploratória).

Documentação de cada fórmula: docs/estudo/herd-medidas.md.
"""
