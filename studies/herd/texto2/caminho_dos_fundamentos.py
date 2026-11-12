"""EXPLORATÓRIO (fora do registro): ρ̄_caminho — os modelos chegam pelo mesmo caminho?

Pergunta do Eduardo (12/11/2026): "a questão não é se acertou ou não, é como
chegaram". Para cada pergunta com gabarito, condição e par de modelos:
sobreposição (Jaccard) das palavras de conteúdo dos fundamentos declarados no
CONTRIBUTION. Fundamento = conteúdo das unidades de conhecimento (a decisão
incluída, porque quase sempre é nela que a justificativa vem), menos as palavras
da pergunta e das opções: assim, repetir o enunciado ou a opção escolhida não
conta como caminho comum. Separado por: acerto em comum, erro em comum (mesma
opção errada) e opções diferentes.

Limite: sobreposição lexical não é raciocínio igual. Leitura humana de amostra
acompanha (texto 2, §4). O raciocínio interno não entra: os pares não o veem.
Uso: .venv/bin/python studies/herd/texto2/caminho_dos_fundamentos.py
"""

import glob
import json
import re
import sys
from collections import defaultdict
from itertools import combinations
from pathlib import Path
from statistics import mean

from norvald_lab.infrastructure.arof.dataset_store import arof_data_root

STUDY = Path(__file__).resolve().parents[1]
STOP = set("the a an of to and or in is are be by for on that this it as with at from not no its their they which was were has have had can will would should could than then so but if into also only more most other such any all each one two because does do".split())
CONDITIONS = {"B1": "b1", "E": "e"}


def words(text):
    return {w for w in re.findall(r"[a-zà-ú0-9]+", text.lower()) if len(w) > 2 and w not in STOP}


def contribution(content):
    m = re.search(r"<<CONTRIBUTION>>(.*?)<<END_CONTRIBUTION>>", content or "", re.S)
    try:
        return json.loads(m.group(1)) if m else None
    except ValueError:
        return None


def read(bank, answers, prefix, condition):
    out = {}
    for q in bank:
        key = answers.get(q["id"])
        if not key:
            continue
        files = glob.glob(str(arof_data_root() / "experiments" / f"{prefix}-{q['id']}-{CONDITIONS[condition]}" / "raw" / "r0001" / "observations.jsonl"))
        if not files:
            continue
        noise = words(q["question"]) | set().union(*(words(o["content"]) for o in q["options"]))
        by_model = {}
        for line in open(files[0]):
            r = json.loads(line)
            if r["attempt_outcome"] != "returned" or not r.get("result"):
                continue
            c = contribution(r["result"].get("content"))
            if not c:
                continue
            picks = [x["target"] for x in c.get("relations", []) if x.get("relation_type") == "selects" and str(x.get("target", "")).startswith("option-")]
            if not picks:
                continue
            text = " ".join(str(k.get("content", "")) for k in c.get("knowledge", []))
            extra = sum(k.get("type") != "decision" for k in c.get("knowledge", []))
            by_model[r["requested_model"]] = {"option": picks[0], "words": words(text) - noise, "extra_units": extra}
        out[q["id"]] = (key, by_model)
    return out


def summarize(data):
    groups = defaultdict(list)
    for key, by_model in data.values():
        for a, b in combinations(sorted(by_model), 2):
            x, y = by_model[a], by_model[b]
            union = x["words"] | y["words"]
            if not union:
                continue
            j = len(x["words"] & y["words"]) / len(union)
            g = "acerto_em_comum" if x["option"] == y["option"] == key else "erro_em_comum" if x["option"] == y["option"] else "opcoes_diferentes"
            groups[g].append(j)
    units = [m["extra_units"] > 0 for _, bm in data.values() for m in bm.values()]
    return {
        **{g: {"pares": len(v), "jaccard_medio": round(mean(v), 3)} for g, v in sorted(groups.items())},
        "respostas_com_fundamento_alem_da_decisao": round(sum(units) / len(units), 3) if units else None,
    }


def main():
    blocks = (("mmlu", STUDY / "mmlu-pro" / "bank.json", STUDY / "mmlu-pro" / "answers.json", "conf2-mmlu"), ("banco", STUDY / "bank.en.json", STUDY / "answers.json", "conf2-banco"))
    result = {}
    for name, bank_path, answers_path, prefix in blocks:
        bank = json.load(open(bank_path))["questions"]
        answers = json.load(open(answers_path))["answers"]
        for condition in CONDITIONS:
            result[f"{name}|{condition}"] = summarize(read(bank, answers, prefix, condition))
    json.dump(result, sys.stdout, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
