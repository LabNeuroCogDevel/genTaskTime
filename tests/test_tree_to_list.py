#!/usr/bin/env python3
import genTaskTime as gtt
import pytest
import pandas as pd
from helpers import dummydur


def test_easy():
    pytest.skip("dur issues")
    c = gtt.EventNode('cue', dur=dummydur(dur=1), nrep=1, verbose=99)
    a = gtt.EventNode('A', parent=c, dur=dummydur(), nrep=2)
    b = gtt.EventNode('B', parent=c, dur=dummydur(), nrep=1)
    e1 = gtt.EventNode('e', parent=a, dur=dummydur(dur=1), nrep=1)
    e2 = gtt.EventNode('e', parent=b, dur=dummydur(dur=1), nrep=1)
    last_leaves = [e1, e2]
    n = c.count_reps()

    gtt.fit_tree(last_leaves, n)
    gtt.event_tree_to_list(last_leaves, 1, 0)


def test_catch_triallist():
    s = "<60/24> cue=[1]{.333}; trg=[2]{.5}; end=[3]"
    ntrial = 24  # hard code to match above
    events = gtt.parse_events(gtt.parse(s))
    last_leaves = gtt.events_to_tree(events, 99)
    (n_rep_branches, nperms) = gtt.fit_tree(last_leaves, ntrial)
    gtt.fit_tree(last_leaves, ntrial)

    # also see gen_events()
    elist = gtt.event_tree_to_list(last_leaves, n_rep_branches, min_iti=0)
    # quick dumb counts
    cnt = {}
    for k in sorted([e['fname'][0] for nodereps in elist for e in nodereps]):
        cnt[k] = cnt.get(k,0) + 1
    assert cnt['cue'] == 24
    assert cnt['trg'] == 24*2/3     # 16
    assert cnt['end'] == 24*2/3*1/2 # 8


def test_triallist_to_df():
    # mocking output of event_tree_to_list
    # better to have tested add_iti(event_tree_to_list)
    # but will be easier to find breaking changes this way (?)
    triallist = [[{'fname': 'A',  'dur': 1},   # 0
                  {'fname': None, 'dur': 1},   #
                  {'fname': None, 'dur': 2},   # 3
                  {'fname': 'B',  'dur': 3}],  # 6
                 [{'fname': 'B',  'dur': 1},   # 10
                  {'fname': None, 'dur': 1},   # 11
                  {'fname': 'A',  'dur': 3}]]  # 14

    edf = gtt.triallist_to_df(triallist, 0)
    assert edf.shape[0] == 6  # iti collapsed
    assert edf['event'].to_list() == ['A', '__iti__', 'B', 'B', '__iti__', 'A']


def test_df_to_1D():
    edf = pd.DataFrame({'event': ['__iti__', 'A', 'A', 'B'],
                        'dur':   [        5,   5,   1,  1],
                        'onset': [        0,   5,  10, 11]})
    onsets_list = gtt.df_to_1D(edf, savedir=None)
    assert onsets_list['A.1D'] == ['5.00:5.00', '10.00:1.00']
    assert onsets_list['B.1D'] == ['11.00:1.00']
    assert onsets_list.get('__iti__.1D') is None
