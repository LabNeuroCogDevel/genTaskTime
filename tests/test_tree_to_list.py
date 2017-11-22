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
