#!/usr/bin/env python3
import genTaskTime as gtt
import pprint


# when we have to use all max, dont use something more than max
def test_shuffle_maxiti():
    s = "<24/4 iti:2-4 stepsize:2 iti_never_first> cue=[2](A,B)"
    (tl, settings) = gtt.str_to_triallist(s, verb=0)
    (ts1, sd) = gtt.shuffle_triallist(settings, tl, 1)
    itis = gtt.iti_list(ts1)
    print(itis)
    pprint.pprint(ts1)
    assert all([abs(x - 4) < 10e-4 for x in itis])


def test_shuffle_seed():
    """
    run shuffle 3 times on 8 things with a bunch of itis
    if output is the same for all 3 seed seems to work
    should also not match with a different seed
    """
    s = "<24/8 stepsize:.5> cue=[1](A,B)"
    (tl, settings) = gtt.str_to_triallist(s, verb=0)
    (ts1, sd) = gtt.shuffle_triallist(settings, tl, 1)
    (ts2, sd) = gtt.shuffle_triallist(settings, tl, 1)
    (ts3, sd) = gtt.shuffle_triallist(settings, tl, 1)
    (ts4, sd) = gtt.shuffle_triallist(settings, tl, 4000)
    assert ts1 == ts2
    assert ts1 == ts3
    pprint.pprint(ts4)
    assert ts1 != ts4
