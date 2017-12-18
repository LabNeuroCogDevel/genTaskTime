#!/usr/bin/env python3
import genTaskTime as gtt
import pprint
import helpers
import numpy as np


# shuffle was causing issues
def test_dont_drop():
    s = "<358/24 stepsize:.5 iti:1.5-2.5 iti_never_first> " + \
        "cue=[2];" + \
        "vgs=[2](NearLeft,NearRight,Left,Right * Indoor, Outdoor,None); " + \
        "dly=[15x 6, 7x 8, 2x 10]; mgs=[2]"
    (tl, settings) = gtt.str_to_triallist(s, verb=0)
    (ts1, sd) = gtt.shuffle_triallist(settings, tl, 1)
    pprint.pprint(ts1)
    itis = gtt.iti_list(ts1)
    elist = [x for x in tl if x[0]['type'] != 'iti']
    #  --- before shuffle is correct ---
    # iti distribution
    assert np.max(itis) <= 2.5
    assert np.min(itis) >= 1.5
    # total time
    tltotal = helpers.sumdur(tl)
    assert abs(tltotal - 358) <= .5
    # 24 permutations of tasks
    assert len(elist) == 24
    # --- after shuffle ---
    # and we have that many tries (by iti count)
    assert helpers.n_trials(ts1) == 24
    pprint.pprint(ts1)
    # we should be within our stepsize of itis
    total = helpers.sumdur(ts1)
    assert abs(total - 358) <= .5
    assert len(itis) == 24


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
