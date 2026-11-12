"""Empresa fixa por modelo atrás do OpenRouter (criado em 11/11/2026).

Na 1ª tentativa da coleta confirmatória do Δ_herd, as cópias do Gemma do painel de
contraste foram servidas por KT e NextBit na mesma pergunta (observação do Eduardo).
"""

import json
from pathlib import Path

import pytest

from norvald_lab.herd.specs import blind_spec
from norvald_lab.vendor.norvald_execution.providers.openai_compatible_provider import _apply_routing, _check_routing

ROOT = Path(__file__).resolve().parents[1]


class _Req:
    def __init__(self, upstream):
        self.upstream_provider = upstream


def test_pinned_provider_goes_to_payload_without_fallback():
    payload = {}
    _apply_routing(payload, _Req("Crusoe"))
    assert payload["provider"] == {"order": ["Crusoe"], "allow_fallbacks": False}


def test_unpinned_request_keeps_free_routing():
    payload = {}
    _apply_routing(payload, _Req(None))
    assert "provider" not in payload


def test_answer_from_another_company_is_refused():
    with pytest.raises(RuntimeError, match="NextBit"):
        _check_routing(_Req("Crusoe"), "NextBit")
    _check_routing(_Req("Crusoe"), "crusoe")
    _check_routing(_Req(None), "NextBit")


def test_collection_panels_pin_every_participant():
    bank = json.loads((ROOT / "studies/herd/bank.en.json").read_text(encoding="utf-8"))
    for name in ("panel.json", "panel-contraste.json"):
        panel = json.loads((ROOT / "studies/herd" / name).read_text(encoding="utf-8"))
        spec = blind_spec(bank["questions"][0], panel, run_id="t", condition_id="B1")
        assert all(p.get("upstream_provider") for p in spec["participants"])
    contraste = json.loads((ROOT / "studies/herd/panel-contraste.json").read_text(encoding="utf-8"))
    assert {(s["model"], s["upstream_provider"]) for s in contraste["participants"]} == {("google/gemma-4-31b-it", "Crusoe")}


def test_spec_validation_accepts_the_pinned_provider():
    # A 1ª fumaça (11/11/2026, 21:17) foi bloqueada: "campos desconhecidos: upstream_provider".
    from norvald_lab.config import validate_spec
    bank = json.loads((ROOT / "studies/herd/bank.en.json").read_text(encoding="utf-8"))
    panel = json.loads((ROOT / "studies/herd/panel-contraste.json").read_text(encoding="utf-8"))
    spec = validate_spec(blind_spec(bank["questions"][0], panel, run_id="t", condition_id="B1"))
    assert spec["participants"][0]["upstream_provider"] == "Crusoe"
    bad = blind_spec(bank["questions"][0], panel, run_id="t", condition_id="B1")
    bad["participants"][0]["upstream_provider"] = " "
    with pytest.raises(ValueError, match="upstream_provider"):
        validate_spec(bad)
