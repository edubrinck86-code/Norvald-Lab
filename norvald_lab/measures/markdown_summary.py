"""Resumo curto, em português, do relatório JSON (fica ao lado dele, mesmo nome, .md).

Só a linha principal de cada medida; o detalhe (grupos, níveis por
condição, por modelo, por pergunta) fica no JSON.
"""

from __future__ import annotations

from typing import Any

from norvald_lab.measures.aw9vf.registration_markdown import RegistrationMarkdown
from norvald_lab.measures.markdown_format import interval as _interval, number as _number


def _get(data: Any, *path: str) -> Any:
    for key in path:
        if not isinstance(data, dict) or key not in data:
            return None
        data = data[key]
    return data


# letra → (descrição da linha principal, caminho até o intervalo dentro do resultado da variante)
PRIMARY = {
    "A": ("Δ_pares(ida à maioria)", ("resultado", "todas", "contrastes", "delta_pares")),
    "B": ("Δ_pares(unanimidade)", ("resultado", "unanimidade", "todas", "contrastes", "delta_pares")),
    "C": ("alteração em E: divididas − unânimes", ("divididas_menos_unanimes", "niveis", "E")),
    "D": ("entre modelos − dentro do modelo", ("resultado", "entre_menos_dentro")),
    "F": ("N_eff (erros em B1)", ("n_eff",)),
    "G": ("P(todos erram) ÷ Π taxas", ("resultado", "razao")),
    "H": ("Δ_pares(acerto)", ("resultado", "acerto", "todas", "contrastes", "delta_pares")),
    "I": ("Δ_pares(C→W)", ("resultado", "todas", "contrastes", "delta_pares")),
    "E": ("N_eff posições − N_eff erros", ("resultado", "dif_n_eff_posicoes_menos_erros_phi")),
}


def _variant(block: dict, name: str) -> dict:
    data = block.get(name, {})
    return block.get("com_indiretas", {}) if "igual_a" in data else data


def render_markdown(report: dict) -> str:
    lines = [f"# Medidas do Δ_herd — {', '.join(report['rodadas'])}", ""]
    boot = report["bootstrap"]
    table = report["tabela"]
    lines += [
        f"Gerado em {report['gerado_em']}. Bootstrap por pergunta, {boot['reps']} réplicas, seed {boot['seed']}, IC {int(boot['nivel'] * 100)}% percentil.",
        f"Tabela: {table['linhas']} linhas, {table['perguntas']} perguntas ({table['perguntas_com_gabarito']} com gabarito), {table['selecoes_indiretas']} seleções indiretas.",
        "",
        *RegistrationMarkdown().render(report.get("registro_aw9vf")),
        "## Tentativas e custo",
        f"Custo total: US$ {_number(report['tentativas_e_custo']['custo_total_usd'], 4)}.",
        "",
        "| Modelo | Observações | Falha na tentativa 1 | Sem posição no fim |",
        "|---|---|---|---|",
    ]
    for model, entry in report["tentativas_e_custo"]["por_modelo"].items():
        lines.append(f"| {model} | {entry['observacoes']} | {entry['falhas_tentativa_1']} ({_number(entry['taxa_falha_tentativa_1'], 2)}) | {entry['sem_posicao_final']} |")
    lines += ["", "## Critérios do bloco 1.2", "", "| | Medida | Com indiretas | Veredito | Sem indiretas | Veredito |", "|---|---|---|---|---|---|"]
    for letter, (label, path) in PRIMARY.items():
        block = report["criterios"].get(letter, {})
        with_, without = block.get("com_indiretas", {}), _variant(block, "sem_indiretas")
        lines.append(f"| {letter} | {label} | {_interval(_get(with_, *path))} | {with_.get('veredito')} | {_interval(_get(without, *path))} | {without.get('veredito')} |")
    j = _get(report, "criterios", "J", "com_indiretas", "por_condicao", "E") or {}
    lines += ["", f"J (exploratória): {j.get('mudancas', 0)} mudanças em E; excesso do 1º par da lista sobre o acaso: {_interval(_get(j, 'resultado', 'excesso_primeiro'))}.", ""]
    lines += ["## Hao et al. (a_0=B1, a_sr=B3, a_so=EP, a_r=E)", "", "| Subconjunto | Pares | Flip SR | Conformidade estrita | H−B só posição | H−B raciocínio |", "|---|---|---|---|---|---|"]
    hao = report["hao"]["com_indiretas"]
    for subset in ("todas", "discordancia"):
        lines.append(
            f"| {subset} | {hao['n_pares_agente_pergunta'][subset]} | {_interval(_get(hao, 'taxas_de_mudanca', subset, 'todos', 'sr'))} | "
            f"{_interval(_get(hao, 'conformidade_estrita', subset, 'taxa'))} | {_interval(_get(hao, 'dano_beneficio', subset, 'so_posicao_EP', 'H_menos_B'))} | "
            f"{_interval(_get(hao, 'dano_beneficio', subset, 'raciocinio_E', 'H_menos_B'))} |")
    check = report["conferencia_algebrica"]["com_indiretas"]
    lines += ["", "## Conferência algébrica", f"Δ_pares(acerto | estáveis em SR) = (W→C − C→W)/N: todas {'confere' if check['todas']['iguais'] else 'NÃO CONFERE'}, discordância {'confere' if check['discordancia']['iguais'] else 'NÃO CONFERE'}."]
    reasons = report["razoes"]["com_indiretas"]
    lines += ["", "## Mesma resposta, razões diferentes (exploratória)",
              f"Similaridade lexical ({reasons['similaridade']['metodo']}) entre concordantes, E − B1: {_interval(_get(reasons, 'resumo', 'similaridade_concordantes', 'contrastes', 'E_menos_B1'))}. Limiar provisório {_number(reasons['limiar_provisorio'], 2)}.", ""]
    return "\n".join(lines)
