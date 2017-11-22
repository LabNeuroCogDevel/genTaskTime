#!/usr/bin/env python3
import genTaskTime as gtt
from helpers import dummydur, cnt


def test_parse_dur():
    dur = dummydur(steps=[{'freq': None, 'num': 1},
                          {'freq': None, 'num': 2}])
    node = gtt.EventNode('test', dur, nrep=2)
    node.count_reps()
    node.master_total_reps = 2
    durs = node.parse_dur(1)
    dursi = [int(x) for x in sorted(durs)]
    assert set(dursi) == set([1, 2])
    dc = cnt(dursi)
    dc['1'] = 1
    dc['2'] = 1

    node.master_total_reps = 2
    durs = node.parse_dur(2)
    dursi = [int(x) for x in sorted(durs)]
    assert set(dursi) == set([1, 2])
    dc = cnt(dursi)
    dc['1'] = 2
    dc['2'] = 2


def test_parse_dur_many():
    dur = {'dist': 'u', 'dur': None, 'min': None, 'max': None,
           'steps': [{'freq': None, 'num': 1},
                     {'freq': None, 'num': 2},
                     {'freq': None, 'num': 4}]}
    node = gtt.EventNode('test', dur, nrep=3)
    node.count_reps()
    node.master_total_reps = 3
    durs = node.parse_dur(4)
    dursi = [int(x) for x in sorted(durs)]
    assert set(dursi) == set([1, 2, 4])
    dc = cnt(dursi)
    dc['1'] = 4
    dc['2'] = 4
    dc['4'] = 4


def test_parse_dur_freq():
    dur = {'dist': 'u', 'dur': None, 'min': None, 'max': None,
           'steps': [{'freq': 1, 'num': 1},
                     {'freq': 3, 'num': 2},
                     {'freq': 2, 'num': 4}]}
    node = gtt.EventNode('test', dur, nrep=6)
    node.count_reps()
    node.master_total_reps = 6
    durs = node.parse_dur(1)
    dursi = [int(x) for x in sorted(durs)]
    assert set(dursi) == set([1, 2, 4])
    dc = cnt(dursi)
    dc['1'] = 1
    dc['2'] = 3
    dc['4'] = 2


def test_dur_list():
    s = "<200/6> cue=[1, 2, 4 u]; end=[1]"
    (tl, settings) = gtt.str_to_triallist(s)

    # we have 2 of each our dirs 1 and 2
    durs = [t[0]['dur'] for t in tl if t[0].get('fname') == ['cue']]
    print(tl[0:4])
    print(durs)
    durgrps = cnt(durs)
    assert durgrps.get('1.0') == 2
    assert durgrps.get('2.0') == 2

    # and nothing else
    assert all([x in [1, 2, 4] for x in durs])
