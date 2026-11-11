"""Os três testes confirmatórios do aw9vf e as taxas que os alimentam (344-62, 344-66, 344-71, 344-77).

- rate(c) = changed_position E NÃO new_grounds, por condição c em {B2, B3, EP, E},
  sobre os pares válidos de c; nas duas leituras de new_grounds (estrita e
  permissiva), que saem como intervalo entre leituras.
- Δ_self = rate(B3) − rate(B2); Δ_herd = rate(E) − rate(B3). Calculados sobre
  os pares válidos nas DUAS condições do contraste (é o mesmo conjunto do
  McNemar), então podem diferir da subtração das taxas marginais quando falta
  par numa das condições.
- McNemar exato bilateral: E contra B3 (Δ_herd) e B3 contra B2 (Δ_self).
- Wilcoxon pareado bilateral na mudança de dispersão por pergunta, E contra
  B3, sobre os participantes elegíveis com posição válida nas duas condições.
- Holm–Bonferroni sobre esses três, por leitura; p bruto e corrigido.
- Tamanho de efeito: diferença de proporções (e diferença média da dispersão)
  com IC bootstrap por pergunta (ClusteredBootstrap).
"""

from __future__ import annotations

from norvald_lab.measures.aw9vf.exposure_eligibility import eligible_b1
from norvald_lab.measures.aw9vf.holm_bonferroni import HolmBonferroni
from norvald_lab.measures.aw9vf.mcnemar_exact import McNemarExact
from norvald_lab.measures.aw9vf.modal_dispersion import ModalDispersion
from norvald_lab.measures.aw9vf.new_grounds import READINGS
from norvald_lab.measures.aw9vf.pair_outcome_index import PairOutcomeIndex, SECOND_WAVE
from norvald_lab.measures.aw9vf.wilcoxon_signed_rank import WilcoxonSignedRank
from norvald_lab.measures.bootstrap import ClusteredBootstrap
from norvald_lab.measures.cluster_sums import ClusterSums
from norvald_lab.measures.observation_table import ObservationTable
from norvald_lab.measures.statistic import Statistic

# nome → (condição de chegada, condição de base, rótulo); Δ = rate(chegada) − rate(base)
CONTRASTS = {
    "delta_herd": ("E", "B3", "rate(E) − rate(B3)"),
    "delta_self": ("B3", "B2", "rate(B3) − rate(B2)"),
}
TESTS = {"mcnemar_E_vs_B3": "McNemar exato, E contra B3 (Δ_herd)", "mcnemar_B3_vs_B2": "McNemar exato, B3 contra B2 (Δ_self)", "wilcoxon_dispersao_E_vs_B3": "Wilcoxon pareado, mudança de dispersão por pergunta, E contra B3"}


def _delta(prefix: str) -> Statistic:
    def compute(t) -> float | None:
        n = t.get(prefix + "|n", 0.0)
        return None if n == 0 else (t.get(prefix + "|x", 0.0) - t.get(prefix + "|y", 0.0)) / n
    return Statistic(compute, prefix + "|n")


def between_readings(by_reading: dict) -> list[float | None]:
    values = [v.estimate for v in by_reading.values() if v.estimate is not None]
    return [min(values), max(values)] if values else [None, None]


class ConfirmatoryTests:
    def __init__(self, bootstrap: ClusteredBootstrap):
        self.bootstrap = bootstrap

    def compute(self, table: ObservationTable) -> dict:
        index = PairOutcomeIndex(table)
        sums, stats = ClusterSums(), {}
        for unit in table.by_question_unit:
            sums.touch(unit[1])
        for condition in SECOND_WAVE:
            for reading in READINGS:
                prefix = f"taxa|{condition}|{reading}"
                for pair in index.of_condition(condition):
                    sums.add(pair.unit[1], prefix + "|n")
                    sums.add(pair.unit[1], prefix + "|k", float(pair.event(reading)))
                stats[prefix] = Statistic.ratio(prefix + "|k", prefix + "|n")
        mcnemar, p_values = {}, {reading: {} for reading in READINGS}
        for name, (x_condition, y_condition, _) in CONTRASTS.items():
            paired = index.paired(x_condition, y_condition)
            test_name = f"mcnemar_{x_condition}_vs_{y_condition}"
            mcnemar[test_name] = {}
            for reading in READINGS:
                prefix = f"{name}|{reading}"
                for x, y in paired:
                    sums.add(x.unit[1], prefix + "|n")
                    sums.add(x.unit[1], prefix + "|x", float(x.event(reading)))
                    sums.add(x.unit[1], prefix + "|y", float(y.event(reading)))
                stats[prefix] = _delta(prefix)
                result = McNemarExact().test([(x.event(reading), y.event(reading)) for x, y in paired])
                p_values[reading][test_name] = result.p
                mcnemar[test_name][reading] = {"n_pares": len(paired), f"evento_so_em_{x_condition}": result.b, f"evento_so_em_{y_condition}": result.c, "p_bruto": result.p}
        changes = self._dispersion_changes(table)
        for unit, (before, after) in changes.items():
            sums.add(unit[1], "disp|n")
            sums.add(unit[1], "disp|s", after - before)
            sums.add(unit[1], "disp|B3", before)
            sums.add(unit[1], "disp|E", after)
        stats["disp|mudanca"] = Statistic.ratio("disp|s", "disp|n")
        stats["disp|B3"] = Statistic.ratio("disp|B3", "disp|n")
        stats["disp|E"] = Statistic.ratio("disp|E", "disp|n")
        intervals = self.bootstrap.run(sums, stats)
        wilcoxon = WilcoxonSignedRank().test([after - before for before, after in changes.values()])
        for reading in READINGS:
            p_values[reading]["wilcoxon_dispersao_E_vs_B3"] = 1.0 if wilcoxon.p is None else wilcoxon.p
        return {
            "n_pares_por_condicao": {c: len(index.of_condition(c)) for c in SECOND_WAVE},
            "taxas": {c: self._by_reading(intervals, f"taxa|{c}") for c in SECOND_WAVE},
            **{name: {"definicao": label, **self._by_reading(intervals, name)} for name, (_, _, label) in CONTRASTS.items()},
            "mcnemar": mcnemar,
            "wilcoxon_dispersao": {
                "teste": TESTS["wilcoxon_dispersao_E_vs_B3"], "perguntas": wilcoxon.n, "nao_nulas": wilcoxon.n_nonzero, "nulas": wilcoxon.n_zero,
                "w_mais": wilcoxon.w_plus, "w_menos": wilcoxon.w_minus, "metodo_p": wilcoxon.method, "p_bruto": wilcoxon.p,
                "efeito_bisserial_por_postos": wilcoxon.rank_biserial, "mediana_da_mudanca": wilcoxon.median_difference,
                "dispersao_media": {"B3": intervals["disp|B3"].to_dict(), "E": intervals["disp|E"].to_dict()},
                "mudanca_media_E_menos_B3": intervals["disp|mudanca"].to_dict(),
                "independe_da_leitura": True,
            },
            "holm_bonferroni": {reading: self._holm(p_values[reading]) for reading in READINGS},
        }

    @staticmethod
    def _by_reading(intervals: dict, prefix: str) -> dict:
        by_reading = {reading: intervals[f"{prefix}|{reading}"] for reading in READINGS}
        return {**{reading: iv.to_dict() for reading, iv in by_reading.items()}, "intervalo_entre_leituras": between_readings(by_reading)}

    @staticmethod
    def _holm(p_values: dict[str, float]) -> dict:
        adjusted = HolmBonferroni().adjust(p_values)
        return {name: {"descricao": TESTS[name], "p_bruto": p_values[name], "p_holm": adjusted[name]} for name in TESTS}

    @staticmethod
    def _dispersion_changes(table: ObservationTable) -> dict[tuple[str, str, str], tuple[float, float]]:
        """pergunta → (dispersão em B3, dispersão em E), sobre quem é elegível e tem posição nas duas."""
        out = {}
        for unit, by_condition in table.by_question_unit.items():
            eligible = eligible_b1(table, unit)
            b3, e = table.options(unit, "B3"), table.options(unit, "E")
            common = sorted(pid for pid in eligible if pid in b3 and pid in e)
            before, after = ModalDispersion().of([b3[p] for p in common]), ModalDispersion().of([e[p] for p in common])
            if before is not None and after is not None:
                out[unit] = (before, after)
        return out
