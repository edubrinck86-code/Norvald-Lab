"""Seção "Registro aw9vf (confirmatório)" do resumo .md: sempre a primeira.

Mostra a variante com seleções indiretas (regra 3); a sem indiretas fica no
JSON. As duas exclusões de unânimes saem uma abaixo da outra.
"""

from __future__ import annotations

from norvald_lab.measures.markdown_format import interval, number

VARIANTS = (("principal_sem_unanimes", "Principal (registrada): perguntas unânimes em B1 excluídas"), ("alternativa_com_unanimes", "Alternativa (desvio aprovado em 11/11/2026): unânimes mantidas"))


def _p(value) -> str:
    return "—" if value is None else ("<0,001" if value < 0.001 else number(value, 3))


class RegistrationMarkdown:
    def render(self, block: dict | None) -> list[str]:
        if not block:
            return []
        data = block["com_indiretas"]
        discard = data["descarte_de_unanimes_em_b1"]
        lines = [
            "## Registro aw9vf (confirmatório)", "",
            f"Pré-registro OSF aw9vf (29/09/2026). Descarte de unânimes em B1: {discard['perguntas_unanimes_em_b1']} de {discard['perguntas_com_b1']} perguntas ({number(discard['taxa_de_descarte'], 2)}). "
            "new_grounds nas duas leituras (estrita / permissiva), relatado como intervalo; testes bilaterais, alfa 0,05; Holm sobre os três testes confirmatórios.", "",
        ]
        for key, title in VARIANTS:
            lines += self._variant(title, data[key])
        lines.append("")
        return lines

    def _variant(self, title: str, data: dict) -> list[str]:
        confirmatory, dependence = data["confirmatorio"], data["dependencia"]
        lines = [f"### {title}", "", "| rate(c) = mudou e sem fundamento novo | Estrita | Permissiva | Intervalo entre leituras | Pares |", "|---|---|---|---|---|"]
        for condition, rate in confirmatory["taxas"].items():
            low, high = rate["intervalo_entre_leituras"]
            lines.append(f"| {condition} | {interval(rate['estrita'])} | {interval(rate['permissiva'])} | [{number(low)}; {number(high)}] | {confirmatory['n_pares_por_condicao'][condition]} |")
        lines += ["", "| Contraste | Estrita | Permissiva | Intervalo entre leituras |", "|---|---|---|---|"]
        for name in ("delta_self", "delta_herd"):
            delta = confirmatory[name]
            low, high = delta["intervalo_entre_leituras"]
            lines.append(f"| {name} = {delta['definicao']} | {interval(delta['estrita'])} | {interval(delta['permissiva'])} | [{number(low)}; {number(high)}] |")
        lines += ["", "| Teste | p bruto (estrita) | p Holm (estrita) | p bruto (permissiva) | p Holm (permissiva) |", "|---|---|---|---|---|"]
        strict, permissive = confirmatory["holm_bonferroni"]["estrita"], confirmatory["holm_bonferroni"]["permissiva"]
        for name, entry in strict.items():
            lines.append(f"| {entry['descricao']} | {_p(entry['p_bruto'])} | {_p(entry['p_holm'])} | {_p(permissive[name]['p_bruto'])} | {_p(permissive[name]['p_holm'])} |")
        wilcoxon = confirmatory["wilcoxon_dispersao"]
        lines += ["", f"Dispersão (1 − fração da moda), E − B3 por pergunta: {interval(wilcoxon['mudanca_media_E_menos_B3'])}; {wilcoxon['perguntas']} perguntas, {wilcoxon['nao_nulas']} com mudança; p {wilcoxon['metodo_p']}.", ""]
        lines += ["| Dependência (erros, gabarito) | ρ̄_erro | N_eff |", "|---|---|---|"]
        for condition, rho in dependence["rho_erro"].items():
            lines.append(f"| {condition} | {interval(rho)} | {interval(dependence['n_eff'][condition])} |")
        lines += ["", f"n do painel: {dependence['n_painel']}. Δ_N_eff = N_eff(B1) − N_eff(E): {interval(dependence.get('delta_n_eff_B1_menos_E'))}. "
                  f"ρ̄_comportamento (Fleiss, contestáveis): {interval(dependence['rho_comportamento']['kappa'])}; distância até ρ̄_erro(B1): {interval(dependence.get('distancia_comportamento_menos_erro'))}."]
        contrast = data.get("painel_homogeneo_de_contraste")
        if contrast:
            lines += [f"Painel homogêneo de contraste ({', '.join(contrast['rodadas'])}), B1: ρ̄_erro {interval(contrast['rho_erro_B1'])}; N_eff {interval(contrast['n_eff_B1'])} (n={contrast['n_painel']})."]
        groups = data["exploratorio"]["canal_da_confianca"]["grupos"]
        lines += ["", "Canal da confiança (exploratório, sem correção), mudança média de posto E − B3: " + "; ".join(
            f"{name} {interval(groups[name]['mudanca_media_E_menos_B3'])}, p {_p(groups[name]['p_bruto_sem_correcao'])}" for name in ("maioria_concorda", "maioria_discorda")) + ".", ""]
        return lines
