"""Gera o banco da tese 4: cada clássico do conf2-mmlu e a sua versão sorteada.

O clássico é copiado do bank.json do MMLU-Pro (enunciado, opções e gabarito
originais). O sorteado sai do molde: parâmetros sorteados com seed registrada,
gabarito calculado e dez opções (o gabarito, os erros típicos e vizinhos
numéricos para completar), embaralhadas pela mesma seed.
Uso: python3 gerador.py SAIDA_DIR [seed]
"""

import json
import os
import random
import sys

from moldes import MOLDES

AQUI = os.path.dirname(os.path.abspath(__file__))
BANCO = os.path.join(AQUI, "..", "..", "herd", "mmlu-pro")
LETRAS = "abcdefghij"
VIZINHOS = [0.5, 0.75, 0.8, 0.9, 1.1, 1.15, 1.25, 1.5, 2.0, 0.6, 1.4, 0.7, 1.3]


def sortear(molde, rnd):
    v = {}
    for nome, (lo, hi, casas) in molde.faixas.items():
        x = rnd.uniform(lo, hi)
        v[nome] = round(x, casas) if casas >= 0 else round(x, casas)
        if casas <= 0:
            v[nome] = float(int(v[nome]))
    texto = {nome: rnd.choice(lista) for nome, lista in molde.nomes.items()}
    return v, texto


def opcoes(molde, v, rnd):
    certo = molde.resposta(v)
    vistos, lista = set(), []

    def poe(x):
        s = molde.formato.format(x)
        if s not in vistos and x == x and abs(x) != float("inf"):
            vistos.add(s); lista.append(s)
            return True
        return False

    poe(certo)
    for erro in molde.erros:
        try:
            poe(erro(v))
        except (ZeroDivisionError, ValueError):
            pass
    for k in VIZINHOS:
        if len(lista) >= 10:
            break
        poe(certo * k)
    chave = lista[0]
    rnd.shuffle(lista)
    return lista, lista.index(chave)


def gerar(seed=20261115):
    rnd = random.Random(seed)
    banco = {q["id"]: q for q in json.load(open(os.path.join(BANCO, "bank.json")))["questions"]}
    gab = json.load(open(os.path.join(BANCO, "answers.json")))["answers"]
    perguntas, chaves = [], {}
    for m in MOLDES:
        c = banco[m.classico_id]
        perguntas.append({"id": f"c-{m.classico_id}", "kind": "gabarito", "category": m.area, "versao": "classico",
                          "par": m.classico_id, "question": c["question"], "options": c["options"]})
        chaves[f"c-{m.classico_id}"] = gab[m.classico_id]
        v, texto = sortear(m, rnd)
        ops, i = opcoes(m, v, rnd)
        sid = f"s-{m.classico_id}"
        perguntas.append({"id": sid, "kind": "gabarito", "category": m.area, "versao": "sorteado", "par": m.classico_id,
                          "parametros": v, "question": m.enunciado.format(**v, **texto),
                          "options": [{"id": f"option-{LETRAS[j]}", "content": o} for j, o in enumerate(ops)]})
        chaves[sid] = f"option-{LETRAS[i]}"
    return {"schema": "sombra.bank.v1", "seed": seed, "questions": perguntas}, {"answers": chaves}


if __name__ == "__main__":
    saida = sys.argv[1]
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else 20261115
    os.makedirs(saida, exist_ok=True)
    banco, chaves = gerar(seed)
    json.dump(banco, open(os.path.join(saida, "bank.json"), "w"), ensure_ascii=False, indent=1)
    json.dump(chaves, open(os.path.join(saida, "answers.json"), "w"), ensure_ascii=False, indent=1)
    print(len(banco["questions"]), "perguntas")
