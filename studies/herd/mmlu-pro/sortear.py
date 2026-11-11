"""Sorteio do bloco MMLU-Pro do Δ_herd (11/11/2026).

Por que existe: Hao et al. (2026, arXiv 2606.00820) usam MMLU-Pro, mas guardam só
as perguntas em que os agentes discordaram, um filtro que depende do desfecho.
Aqui o sorteio é aleatório e estratificado por categoria, ANTES de qualquer
resposta, e as unânimes ficam (decisão do Eduardo: "concordância tem que entrar
também"). O recorte "só discordância" é calculado depois, para comparar com eles.

Como sorteia: dentro de cada categoria, ordena pelo sha256 de
"norvald-herd-mmlupro-v1|<question_id>". Sem gerador aleatório, então o
resultado não depende de versão de biblioteca. O piloto usa os 2 primeiros de
cada categoria; a coleta principal usa os seguintes, nunca os do piloto.

Fonte: TIGER-Lab/MMLU-Pro (licença MIT), split test, revisão
b189ec765aa7ed75c8acfea42df31fdae71f97be, arquivo
data/test-00000-of-00001.parquet, sha256
0e24a191921c2f453518a537a8b2117bd137e7714d4ef1565e9ba06c1ecb9ad8.

Uso: python sortear.py <caminho do parquet> <por categoria>
"""

import hashlib
import json
import sys
from pathlib import Path

import pyarrow.parquet as pq

SALT = "norvald-herd-mmlupro-v1"
PARQUET_SHA256 = "0e24a191921c2f453518a537a8b2117bd137e7714d4ef1565e9ba06c1ecb9ad8"
PILOT_PER_CATEGORY = 2
HERE = Path(__file__).resolve().parent


def rank_key(question_id):
    return hashlib.sha256(f"{SALT}|{question_id}".encode()).hexdigest()


def main(parquet_path, per_category):
    raw = Path(parquet_path).read_bytes()
    if hashlib.sha256(raw).hexdigest() != PARQUET_SHA256:
        raise SystemExit("O parquet não é a revisão registrada.")
    rows = pq.read_table(parquet_path).to_pylist()
    by_category = {}
    for row in rows:
        by_category.setdefault(row["category"], []).append(row)
    questions, answers = [], {}
    for category in sorted(by_category):
        ordered = sorted(by_category[category], key=lambda r: rank_key(r["question_id"]))
        for rank, row in enumerate(ordered[:per_category], start=1):
            qid = f"m{int(row['question_id']):05d}"
            letters = "abcdefghij"[: len(row["options"])]
            questions.append({
                "id": qid, "kind": "gabarito", "category": category, "rank_in_category": rank,
                "block": "piloto" if rank <= PILOT_PER_CATEGORY else "principal",
                "source_question_id": row["question_id"], "src": row["src"],
                "question": row["question"],
                "options": [{"id": f"option-{l}", "content": o} for l, o in zip(letters, row["options"])],
            })
            answers[qid] = f"option-{row['answer'].lower()}"
            assert row["answer"] == "ABCDEFGHIJ"[row["answer_index"]]
    meta = {"source": "TIGER-Lab/MMLU-Pro, test, rev b189ec7", "parquet_sha256": PARQUET_SHA256, "salt": SALT,
            "per_category": per_category, "pilot_per_category": PILOT_PER_CATEGORY}
    (HERE / "bank.json").write_text(json.dumps({"schema": "norvald.lab.herd.bank.v1", "language": "en", **meta, "questions": questions}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    (HERE / "answers.json").write_text(json.dumps({"schema": "norvald.lab.herd.answers.v1", "note": "Gabarito do MMLU-Pro; nunca entra no prompt.", **meta, "answers": answers}, indent=1) + "\n", encoding="utf-8")
    print(len(questions), "perguntas;", sum(q["block"] == "piloto" for q in questions), "no piloto")


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]))
