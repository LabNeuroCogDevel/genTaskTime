from genTaskTime.badmath import fit_dist


def test_fit_dist():
    f = fit_dist(2, [4, 3], 21)
    assert len(f) == 2
    assert sum(f) == 21

    f = fit_dist(2, [4, 3], 7)
    assert len(f) == 2
    assert sum(f) == 7

    f = fit_dist(3, [4, 3], 7)
    assert len(f) == 3
    assert sum(f) == 7

    f = fit_dist(1, [4, 3], 7)
    assert len(f) == 1
    assert sum(f) == 7

    f = fit_dist(4, [4, 3], 21)
    assert len(f) == 4
    assert sum(f) == 21

    f = fit_dist(4, [4, 3], 4)
    assert len(f) == 4
    assert sum(f) == 4
