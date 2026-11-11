"""Prompt em inglês (spec `language: "en"`), criado em 11/11/2026.

O dono decidiu que a coleta do estudo seria em inglês, para o idioma não se
misturar com a capacidade medida. Até então tudo o que o Lab injetava no
prompt estava em português.
"""

import copy
import hashlib
import json
import re

import pytest

from norvald_lab.application.arof.outcome_extract import rows_from_raw
from norvald_lab.application.deliberation.round_prompt import TEXTS_PT, render_constitution_block, render_shared_instructions
from norvald_lab.application.deliberation.round_prompt_en import TEXTS_EN
from norvald_lab.cli import demo_spec, derive_spec
from norvald_lab.config import validate_spec
from norvald_lab.domain.deliberation.contribution import Contribution
from norvald_lab.runner import ExperimentRunner

# Palavras que só aparecem em português; "ção" cobre contribuição, execução etc.
MARCADORES_PT = ["Você", "Reconsidere", "Escolha", "escolha", "contribuição", "não", "ção", "Analista", "Opção", "Demonstração", "DEMONSTRAÇÃO", "Material fictício"]

# Calculados ANTES da mudança, sobre `demo_spec("snap")` (11/11/2026).
# tools=off e tools=corpus. Se mudarem, um spec antigo passou a gerar outro request.
ANTES = {
    "off": ("d07c36438956e0c95b6f9d9ff251a94996cb107a8e4439e8598a2e9efe364673", "598dc770485a17ca371d4b1963b13ea82dcc74f564550497d484d37cf4cac0b2"),
    "corpus": ("88693e66aaf201deea3619878156e576e9f39f9be644edd74a41009dbb248046", "6b81dec28ff03bdd8887ba62a6b275d99be453ea694a090622c64bd51a35c795"),
}


def english_spec(experiment_id):
    spec = demo_spec(experiment_id)
    spec["language"] = "en"
    spec["task"] = {"id": "demo-question", "objective": "Compare options A and B and state your position. Synthetic demonstration, no empirical value.", "instructions": "Declare a decision and selects for option-a or option-b."}
    for i, p in enumerate(spec["participants"], 1):
        p["name"], p["role"] = f"Analyst {i}", "Analyst"
    spec["documents"] = [{"id": "demo-text", "title": "Fictitious material", "text": "A prioritizes deadline. B prioritizes flexibility.", "source": "Synthetic demonstration"}]
    spec["working_context"] = {"items": [{"id": "option-a", "type": "option", "content": "Option A: deadline"}, {"id": "option-b", "type": "option", "content": "Option B: flexibility"}], "relations": []}
    return spec


def texts_of(prepared):
    out = []
    for raw in prepared.requests_json:
        request = json.loads(raw)
        out += [request["instructions"], request["shared_instructions"], request["wave_instructions"]]
    return out


def assert_no_portuguese(texts):
    for text in texts:
        for word in MARCADORES_PT:
            assert word not in text, f"{word!r} em texto que devia estar em inglês: ...{text[max(0, text.index(word) - 60):text.index(word) + 60]}..."


def test_en_prepared_requests_have_no_portuguese(tmp_path):
    runner = ExperimentRunner(tmp_path)
    for tools in ("off", "corpus"):
        spec = english_spec("en-" + tools)
        spec["condition"]["tools"] = tools
        prepared = runner.prepare(spec)
        texts = texts_of(prepared)
        assert len(texts) == 9
        assert_no_portuguese(texts)
        request = json.loads(prepared.requests_json[0])
        assert request["instructions"].startswith("You are Analyst 1, acting as Analyst.\n")
        assert request["wave_instructions"].startswith("COMPLETE WORKING CONTEXT:\n")
        assert "FROZEN CORPUS OF THIS EXPERIMENT:" in request["shared_instructions"]
        assert "LAB PROFILE:" in request["shared_instructions"]
        assert request["context"]["metadata"]["prompt_language"] == "en"


def test_en_shared_instructions_have_no_portuguese_in_any_round_or_option():
    for round_number in (1, 2, 3):
        for lib in (True, False):
            text = render_shared_instructions(round_number=round_number, has_library_tools=lib, language="en")
            assert_no_portuguese([text])
    assert_no_portuguese([render_constitution_block([type("C", (), {"name": "Rule", "reference": "r", "canonical_body": "Be brief.", "body": ""})()], language="en")])


def test_en_keeps_structure_markers_keys_and_types():
    assert set(TEXTS_EN) == set(TEXTS_PT)
    for round_number in (1, 2):
        for lib in (True, False):
            pt = render_shared_instructions(round_number=round_number, has_library_tools=lib)
            en = render_shared_instructions(round_number=round_number, has_library_tools=lib, language="en")
            assert len(pt.split("\n\n")) == len(en.split("\n\n"))  # mesma ordem e número de seções
            for marker in ("<<CONTRIBUTION>>", "<<END_CONTRIBUTION>>", '"local_id"', '"relation_type"', "decision", "selects", "derived_from", "evidence-<id>", "resolves", "supersedes", "scan_context", "retain_ids", "dimension_id"):
                assert pt.count(marker) == en.count(marker), marker
            # a lista de relações vem do grafo e é idêntica nos dois idiomas
            assert [l for l in pt.splitlines() if l.startswith("- ")] == [l for l in en.splitlines() if l.startswith("- ")]
    for key in TEXTS_PT:
        assert set(re.findall(r"\{\w+\}", TEXTS_PT[key])) == set(re.findall(r"\{\w+\}", TEXTS_EN[key])), key
        assert TEXTS_PT[key].count("<<") == TEXTS_EN[key].count("<<"), key


def test_unknown_language_is_refused_and_does_not_fall_back_to_portuguese():
    with pytest.raises(ValueError, match="language"):
        validate_spec(demo_spec("x") | {"language": "fr"})
    with pytest.raises(ValueError):
        render_shared_instructions(language="fr")


def test_spec_without_language_is_untouched_by_validation():
    spec = demo_spec("x")
    assert "language" not in validate_spec(spec)  # nada de setdefault: não muda a impressão digital
    assert validate_spec(demo_spec("x") | {"language": "pt-BR"})["language"] == "pt-BR"


@pytest.mark.parametrize("tools", ["off", "corpus"])
def test_spec_without_language_generates_exactly_the_requests_of_before(tmp_path, tools):
    runner = ExperimentRunner(tmp_path)
    spec = demo_spec("snap")
    spec["condition"]["tools"] = tools
    prepared = runner.prepare(spec)
    fingerprint, digest = ANTES[tools]
    assert prepared.condition_fingerprint == fingerprint
    assert hashlib.sha256("\n".join(prepared.requests_json).encode()).hexdigest() == digest
    assert "prompt_language" not in json.loads(prepared.requests_json[0])["context"]["metadata"]


def test_explicit_pt_br_generates_the_same_requests_as_no_field(tmp_path):
    runner = ExperimentRunner(tmp_path)
    plain = runner.prepare(demo_spec("snap"))
    explicit = runner.prepare(demo_spec("snap") | {"language": "pt-BR"})
    # A impressão digital da condição cobre o spec inteiro (que agora tem o campo), então é a
    # única coisa que difere; o que o modelo recebe é idêntico.
    def sem_digital(prepared):
        out = []
        for raw in prepared.requests_json:
            request = json.loads(raw)
            del request["context"]["metadata"]["condition_fingerprint"]
            out.append(request)
        return out

    assert sem_digital(explicit) == sem_digital(plain)
    assert "Você é Analista 1, atuando como Analista." in json.loads(plain.requests_json[0])["instructions"]


def test_parser_accepts_english_confidence():
    block = '{"knowledge":[{"local_id":"d1","type":"decision","content":"I pick A","confidence":"high"},{"local_id":"c1","type":"claim","content":"x","confidence":"low"},{"local_id":"i1","type":"inference","content":"y","confidence":"medium"}],"relations":[{"relation_type":"selects","source":"d1","target":"option-a"}]}'
    parsed = Contribution.parse("Prose.\n<<CONTRIBUTION>>\n" + block + "\n<<END_CONTRIBUTION>>", author_id="p1", round_number=1)
    assert [k.confidence for k in parsed.knowledge] == ["high", "low", "medium"]
    assert len(parsed.relations) == 1


@pytest.mark.asyncio
async def test_b1_to_e_cycle_in_english_runs_to_the_end_and_normalizes_confidence(tmp_path):
    runner = ExperimentRunner(tmp_path)
    original = english_spec("b1")
    spec = copy.deepcopy(original)
    result = await runner.run(runner.prepare(spec), monitor_capacity=False)
    assert result["status"] == "complete"
    exposed_spec = derive_spec(tmp_path, "b1", "e", "exposed")
    assert exposed_spec["language"] == "en"  # a condição derivada herda o idioma da origem
    prepared = runner.prepare(exposed_spec)
    assert_no_portuguese(texts_of(prepared))
    assert "Reconsider the task in light of the contributions available in the context." in json.loads(prepared.requests_json[0])["instructions"]
    result = await runner.run(prepared, monitor_capacity=False)
    assert result["status"] == "complete" and result["executed"] == 3
    paths = sorted((tmp_path / "experiments" / "e" / "raw").rglob("*.jsonl"))
    rows = rows_from_raw(paths, experiment_id="e")
    assert len(rows) == 3
    assert {row.confidence for row in rows} == {"média"}  # "medium" vira o valor canônico


@pytest.mark.asyncio
async def test_condition_derived_from_other_language_is_refused(tmp_path):
    runner = ExperimentRunner(tmp_path)
    await runner.run(runner.prepare(english_spec("b1")), monitor_capacity=False)
    spec = derive_spec(tmp_path, "b1", "e", "exposed")
    spec["language"] = "pt-BR"
    with pytest.raises(ValueError, match="diferem da origem"):
        runner.prepare(spec)
