"""Medidas de Hao et al. (2026), §3 do protocolo (studies/herd/hao-2026-protocolo.md)."""

from norvald_lab.measures.hao.hao_flip_rates import HaoFlipRates
from norvald_lab.measures.hao.hao_harm_benefit import HaoHarmBenefit
from norvald_lab.measures.hao.hao_partition import HaoPartition
from norvald_lab.measures.hao.hao_strict_conformity import HaoStrictConformity
from norvald_lab.measures.hao.hao_transitions import HaoTransitions

HAO_MEASURES = (HaoPartition(), HaoFlipRates(), HaoStrictConformity(), HaoTransitions(), HaoHarmBenefit())
