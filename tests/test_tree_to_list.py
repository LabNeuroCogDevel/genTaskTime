#!/usr/bin/env python3
import genTaskTime as gtt
import pytest
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
