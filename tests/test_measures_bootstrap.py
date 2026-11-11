"""Bootstrap por pergunta (criado em 11/11/2026 com a camada de medidas)."""

from norvald_lab.measures.bootstrap import ClusteredBootstrap, quantile
from norvald_lab.measures.cluster_sums import ClusterSums
from norvald_lab.measures.statistic import Statistic


def _sums(values):
    sums = ClusterSums()
    for index, (num, den) in enumerate(values):
        sums.add(f"q{index:02d}", "num", num)
        sums.add(f"q{index:02d}", "den", den)
    return sums


STAT = {"taxa": Statistic.ratio("num", "den")}


def test_quantile_is_type_7():
    # posição (n−1)q = 3·0,25 = 0,75 → 1 + 0,75·(2 − 1) = 1,75
    assert quantile([1, 2, 3, 4], 0.25) == 1.75
    assert quantile([1, 2, 3, 4], 1.0) == 4
    assert quantile([5], 0.5) == 5


def test_same_seed_same_interval_and_seed_is_recorded():
    sums = _sums([(1, 2), (0, 2), (2, 2), (1, 1), (0, 3)])
    first = ClusteredBootstrap(reps=500, seed=7).run(sums, STAT)["taxa"]
    second = ClusteredBootstrap(reps=500, seed=7).run(sums, STAT)["taxa"]
    other = ClusteredBootstrap(reps=500, seed=8).run(sums, STAT)["taxa"]
    assert first == second
    assert ClusteredBootstrap(reps=10, seed=7).describe()["seed"] == 7
    # estimativa pontual = Σnum/Σden = 4/10, independe da seed
    assert first.estimate == other.estimate == 0.4
    assert first.n == 10 and first.n_clusters == 5 and first.valid_reps == 500


def test_different_seed_changes_draws():
    sums = _sums([(i % 3, 3) for i in range(30)])
    a = ClusteredBootstrap(reps=300, seed=1).run(sums, STAT)["taxa"]
    b = ClusteredBootstrap(reps=300, seed=2).run(sums, STAT)["taxa"]
    assert (a.low, a.high) != (b.low, b.high)


def test_constant_clusters_give_degenerate_interval():
    sums = _sums([(1, 2)] * 6)
    interval = ClusteredBootstrap(reps=200).run(sums, STAT)["taxa"]
    assert (interval.estimate, interval.low, interval.high) == (0.5, 0.5, 0.5)


def test_cache_of_draws_does_not_change_numbers():
    sums = _sums([(1, 2), (0, 2), (2, 2), (1, 1)])
    shared = ClusteredBootstrap(reps=300, seed=3)
    first = shared.run(sums, STAT)["taxa"]
    again = shared.run(sums, STAT)["taxa"]  # usa o sorteio guardado
    fresh = ClusteredBootstrap(reps=300, seed=3).run(sums, STAT)["taxa"]
    assert first == again == fresh


def test_strata_are_resampled_with_their_own_size():
    # 2 clusters no estrato "x" e 3 no "y": a fração de clusters "x" fica 2/5 em toda réplica.
    sums = ClusterSums()
    for index in range(5):
        stratum = "x" if index < 2 else "y"
        sums.add(f"q{index}", "x", float(stratum == "x"), stratum=stratum)
        sums.add(f"q{index}", "n", 1.0, stratum=stratum)
    interval = ClusteredBootstrap(reps=300).run(sums, {"fracao": Statistic.ratio("x", "n")})["fracao"]
    assert (interval.low, interval.high) == (0.4, 0.4)


def test_statistic_missing_in_some_replicates_is_counted():
    # Só q1 tem denominador; réplica sem q1 não tem taxa e fica fora do quantil.
    sums = ClusterSums()
    sums.add("q0", "num", 0.0)
    sums.add("q1", "num", 1.0)
    sums.add("q1", "den", 1.0)
    interval = ClusteredBootstrap(reps=400, seed=5).run(sums, STAT)["taxa"]
    assert 0 < interval.valid_reps < 400
    assert interval.low == interval.high == 1.0


def test_empty_sums_give_empty_interval():
    interval = ClusteredBootstrap(reps=10).run(ClusterSums(), STAT)["taxa"]
    assert interval.estimate is None and interval.n_clusters == 0
