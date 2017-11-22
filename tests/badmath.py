from genTaskTime.badmath import fit_dist, list_to_length_n


def test_list():
    ll = list_to_length_n([1, 2], 1, '')
    assert len(ll) == 1

    ll = list_to_length_n([1, 2], 2, '')
    assert len(ll) == 2

    ll = list_to_length_n([1, 2], 3, '')
    assert len(ll) == 3
    assert 1 in ll
    assert 2 in ll


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
