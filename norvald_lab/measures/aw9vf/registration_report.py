"""Monta o bloco "Registro aw9vf (confirmatório)" do relatório de medidas.

Duas variantes de exclusão, lado a lado (344-79 item 1):
- `principal_sem_unanimes`: pergunta unânime em B1 fora da análise (registrado);
- `alternativa_com_unanimes`: perguntas unânimes mantidas (desvio aprovado
  em 11/11/2026).
A taxa de descarte sai como resultado.

O filtro de unânimes vale só para o confirmatório e o exploratório (o critério
A, criterios-1.2 regra 1). O ρ̄_erro, o N_eff e o contraste usam sempre TODAS
as perguntas com gabarito, como o registro define ("on ground-truth items",
gbx5m). Até 12/11/2026 o filtro também caía no ρ̄ da principal (desvio D7):
tirar as unânimes tira justamente os acertos e erros em comum, e o ρ̄ caía. A regra 3 (seleção indireta) é
variante de fora, tratada por quem chama (`MeasuresReport._variants`).
"""

from __future__ import annotations

from norvald_lab.measures.aw9vf.confidence_channel import ConfidenceChannel
from norvald_lab.measures.aw9vf.confirmatory_tests import ConfirmatoryTests
from norvald_lab.measures.aw9vf.dependence import Dependence
from norvald_lab.measures.aw9vf.literal_collision import LiteralCollision
from norvald_lab.measures.aw9vf.missingness import Missingness
from norvald_lab.measures.aw9vf.pair_asymmetry import PairAsymmetry
from norvald_lab.measures.aw9vf.unanimous_filter import UnanimousFilter
from norvald_lab.measures.bootstrap import ClusteredBootstrap
from norvald_lab.measures.observation_table import ObservationTable

SOURCE = "pré-registro OSF aw9vf (29/09/2026), respostas 344-62, 344-66, 344-71, 344-75, 344-77, 344-79, 344-81, 344-83"


class RegistrationReport:
    def __init__(self, bootstrap: ClusteredBootstrap):
        self.bootstrap = bootstrap

    @staticmethod
    def header() -> dict:
        return {
            "fonte": SOURCE,
            "leituras_de_new_grounds": {
                "estrita": "fundamento que aponta para a contribuição de outro participante NÃO conta como novo",
                "permissiva": "conta como novo",
                "relatorio": "intervalo entre as duas leituras; a estrita é a nomeada no registro",
            },
            "regra_dos_fundamentos": "alvo de relação derived_from/evidenced_by/documents aceita pelo validador; ver docs/estudo/herd-medidas.md §8",
        }

    def build(self, table: ObservationTable, contrast_table: ObservationTable | None = None) -> dict:
        unanimous = UnanimousFilter()
        # ρ̄ e contraste: tabela inteira, nas duas variantes (D7).
        dependence = Dependence(self.bootstrap).compute(table)
        contrast = None if contrast_table is None else self._contrast(contrast_table)
        return {
            "descarte_de_unanimes_em_b1": unanimous.discard_rate(table),
            "principal_sem_unanimes": self._analysis(unanimous.without_unanimous(table), dependence, contrast),
            "alternativa_com_unanimes": self._analysis(table, dependence, contrast),
        }

    def _analysis(self, table: ObservationTable, dependence: dict, contrast: dict | None) -> dict:
        return {
            "confirmatorio": ConfirmatoryTests(self.bootstrap).compute(table),
            "dependencia": dependence,
            "painel_homogeneo_de_contraste": contrast,
            "exploratorio": {
                "canal_da_confianca": ConfidenceChannel(self.bootstrap).compute(table),
                "assimetria_por_par_de_modelos": PairAsymmetry().compute(table),
                "colisao_literal": LiteralCollision().compute(table),
            },
            "ausencia": Missingness().compute(table),
        }

    def _contrast(self, table: ObservationTable) -> dict:
        """ρ̄_erro e N_eff em B1 do painel homogêneo (344-83 item 2), n = tamanho daquele painel."""
        full = Dependence(self.bootstrap).compute(table, conditions=("B1",), behaviour=False)
        return {
            "rodadas": list(table.runs), "n_painel": full["n_painel"], "perguntas_com_gabarito": full["perguntas_com_gabarito"],
            "rho_erro_B1": full["rho_erro"]["B1"], "n_eff_B1": full["n_eff"]["B1"],
            "pares_sem_correlacao_definida": full["pares_sem_correlacao_definida"]["B1"],
        }
