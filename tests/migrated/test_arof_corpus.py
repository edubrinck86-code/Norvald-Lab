from norvald_lab.application.arof.corpus import (
    fingerprint_library,
    same_library_corpus,
)
from norvald_lab.domain.evidence import Evidence


def test_library_fingerprint_independe_da_ordem_de_listagem():
    a = Evidence(
        id="a",
        kind="documento",
        reference="a.md",
        name="A",
        body="alpha",
    )
    b = Evidence(
        id="b",
        kind="documento",
        reference="b.md",
        name="B",
        body="beta",
    )

    first = fingerprint_library([a, b])
    second = fingerprint_library([b, a])

    assert first.fingerprint == second.fingerprint
    assert first.item_count == 2
    assert same_library_corpus(first, second)


def test_library_fingerprint_muda_com_conteudo_status_ou_metadata():
    base = Evidence(
        id="a",
        kind="documento",
        reference="a.md",
        name="A",
        body="alpha",
    )
    original = fingerprint_library([base])

    changed_body = Evidence.from_dict(base.to_dict())
    changed_body.body = "alpha alterado"
    assert not same_library_corpus(
        original,
        fingerprint_library([changed_body]),
    )

    changed_status = Evidence.from_dict(base.to_dict())
    changed_status.status = "archived"
    assert not same_library_corpus(
        original,
        fingerprint_library([changed_status]),
    )

    changed_metadata = Evidence.from_dict(base.to_dict())
    changed_metadata.metadata = {"semantic": {"x": 1}}
    assert not same_library_corpus(
        original,
        fingerprint_library([changed_metadata]),
    )


def test_frozen_library_nao_muda_quando_objeto_original_muda():
    from norvald_lab.application.arof.corpus import FrozenEvidenceLibrary

    original = Evidence(
        id="x",
        kind="documento",
        reference="x.md",
        body="antes",
    )
    frozen = FrozenEvidenceLibrary([original])
    original.body = "depois"

    assert frozen.get("x").body == "antes"

