#!/usr/bin/env python3
# import pytest
import genTaskTime as gtt
from genTaskTime.EventGrammar import unlist_grammar
from genTaskTime.generate import mkChild
import pytest
from helpers import n_trials, sumdur, file_counts
import numpy as np
import anytree


def test_event_parse():
    """ pull out events. includes separator ';' or '|' """
    s = "<60/6> cue=[1]; end=[3]"
    astobj = gtt.parse(s)
    # ['cue' ';' 'end']
    assert len(astobj['allevents']) == 3

    events = gtt.parse("<60/6> cue=[1](A,B); end=[3]")['allevents']
    assert len(events) == 3

    events = gtt.parse("<60/6> cue=[1] | end=[3]")['allevents']
    assert len(events) == 3


def test_event_unlist():
    events = unlist_grammar(gtt.parse("<60/6> cue=[1]; end=[3]")['allevents'])
    assert len(events) == 2

    events = unlist_grammar(gtt.parse("<60/6> cue=[1](A,B); end=[3]")['allevents'])
    assert len(events) == 2


def test_mkChild():
    s = "<60/6> cue=[1](A,B); end=[3]"
    events = gtt.parse_events(gtt.parse(s))
    root = gtt.EventNode('root', dur=0)
    elist = events[0]['eventtypes']
    # events[0]['eventtypes']['subevent']
    #   ({'freq': None, 'subname': 'A'}, ',',
    #    {'freq': None, 'subname': 'B'})
    children = mkChild(root, elist, verb=99)
    len(children) == 2  # A and B
    assert children[0].parent == root
    assert children[1].parent == root
    assert children[0].root == root


def test_simple_tree():
    s = "<60/6> cue=[1]; end=[3]"
    # parse
    events = gtt.parse_events(gtt.parse(s))
    last_leaves = gtt.events_to_tree(events, 99)
    assert last_leaves[0].name == 'end'
    assert len(last_leaves) == 1


def test_catch_tree():
    s = "<60/6> cue=[1]{.3}; end=[3]"
    # parse
    events = gtt.parse_events(gtt.parse(s))
    last_leaves = gtt.events_to_tree(events, 99)
    # cue; cue->end
    assert len(last_leaves) == 2
    assert last_leaves[1].name == '__catch__1'


def test_tree_branch():
    s = "<60/6> cue=[1](A, B); end=[3]"
    astobj = gtt.parse(s)
    events = gtt.parse_events(astobj)
    last_leaves = gtt.events_to_tree(events, 99)
    # cue_A+end
    # cue_B+end
    assert len(last_leaves) == 2
    assert last_leaves[0].name == 'end'
    assert last_leaves[1].name == 'end'


def test_trial_uneven_branch_repcnt():
    s = "<60/6> cue=[1](A, 2x B); end=[3]"
    # parse
    astobj = gtt.parse(s)
    settings = gtt.parse_settings(astobj)
    events = gtt.parse_events(astobj)

    # build a tree from events
    last_leaves = gtt.events_to_tree(events, 99)
    # fit tree
    ntrial = settings['ntrial']
    (n_rep_branches, nperms) = gtt.fit_tree(last_leaves, ntrial)
    assert nperms == 3  # 1xA + 2xB == 3
    assert n_rep_branches == 2  # total_trials/(A + 2 B) => 6/3 => 2

    # 1x A
    assert last_leaves[0].count_branch_reps() == 1
    # 2x B
    assert last_leaves[1].count_branch_reps() == 2

    # get a list of all trials
    # triallist = gtt.event_tree_to_list(last_leaves, n_rep_branches,
    #                                    settings['miniti'])

def test_trial_uneven_branch_repcnt_catch():
    s = "<60/12> cue=[1](A, 2x B){.3}; end=[3]"
    # parse
    astobj = gtt.parse(s)
    settings = gtt.parse_settings(astobj)
    events = gtt.parse_events(astobj)

    # build a tree from events
    last_leaves = gtt.events_to_tree(events, 99)
    # fit tree
    ntrial = settings['ntrial']
    (n_rep_branches, nperms) = gtt.fit_tree(last_leaves, ntrial)
    print(last_leaves)
    assert nperms == 6  # 1xA + 2xB + .3*1 + .3*2
    assert n_rep_branches == 2  # total_trials/nperms 12/6

    branch_reps = [lf.count_branch_reps() for lf in last_leaves]
    # TODO: where does .7 come from!?
    # 1xA 2xB 1xA .3 (catch) 2xB .3 (catch)
    assert branch_reps == [.7*br for br in [1, 2, 0.3, 0.3*2]]

    # get a list of all trials
    # triallist = gtt.event_tree_to_list(last_leaves, n_rep_branches,
    #                                    settings['miniti'])


def test_2catch():
    s = "<60/12> cue=[1]{.3}; trg=[2]{.2}; end=[3]"
    events = gtt.parse_events(gtt.parse(s))
    last_leaves = gtt.events_to_tree(events, 99)
    assert len(last_leaves) == 3
    assert last_leaves[1].name == '__catch__1'

    assert last_leaves[2].name == '__catch__2'
    assert last_leaves[2].path[-2].name == 'trg'


def test_2catch_perms():
    s = "<60/12> cue=[1](A,B){.3}; trg=[2](C,D){.2}; end=[3]"
    events = gtt.parse_events(gtt.parse(s))
    last_leaves = gtt.events_to_tree(events, 99)
    assert len(last_leaves) == 10
    assert last_leaves[4].name == '__catch__1'
    assert last_leaves[4].path[-2].name == 'A'

    assert last_leaves[9].name == '__catch__2'
    assert last_leaves[9].path[-2].name == 'D'


def test_2catch_tree():
    s = "<60/12> cue=[1]{.3}; trg=[2]{.2}; end=[3]"
    ntrial = 12  # hard code to match above
    events = gtt.parse_events(gtt.parse(s))
    last_leaves = gtt.events_to_tree(events, 99)
    (n_rep_branches, nperms) = gtt.fit_tree(last_leaves, ntrial)
    print(anytree.RenderTree(last_leaves[0].root))
    assert nperms == 3  # cue+catch, cue+trg+catch, cue+trg+end


def test_trial_uneven_branch():
    s = "<60/6> cue=[1](A, 2x B); end=[3]"
    (triallist, settings) = gtt.str_to_triallist(s)

    fc = file_counts(triallist)
    assert fc['cue_A'] == 2
    assert fc['cue_B'] == 4
    assert fc['end'] == 6

    assert n_trials(triallist) == 6
    assert sumdur(triallist) == pytest.approx(60, .001)


def test_dur_foundation():
    steps = [1, 2]
    freq = [3, 4]
    reps = gtt.rep_a_b_times(steps, freq)
    finallist = gtt.list_to_length_n(reps, 14, 'msg')
    (vals, cnts) = np.unique(finallist, return_counts=True)
    assert all(vals == [1., 2.])
    assert all(cnts == [6., 8.])


def test_trial_uneven_dur():
    s = "<60/4 stepsize:1> cue=[3x 1, 1x 2]"
    (triallist, settings) = gtt.str_to_triallist(s)

    alldurs = [x[0]['dur'] for x in triallist if x[0]['fname'] is not None]
    (vals, cnts) = np.unique(alldurs, return_counts=True)
    assert all(vals == [1., 2.])
    assert all(cnts == [3., 1.])


def test_trial_uneven_dur_x2():
    s = "<60/8 stepsize:1> cue=[3x 1, 1x 2]"
    (triallist, settings) = gtt.str_to_triallist(s)

    alldurs = [x[0]['dur'] for x in triallist if x[0]['fname'] is not None]
    (vals, cnts) = np.unique(alldurs, return_counts=True)
    assert all(vals == [1., 2.])
    assert all(cnts == [6., 2.])

def test_trial_uneven_branch_rep_branches():
    s = "<600/12> cue=[1](A, 2x B, 3x C); end=[0]"
    (triallist, settings) = gtt.str_to_triallist(s)

    fc = file_counts(triallist)
    assert fc['cue_A'] == 2
    assert fc['cue_B'] == 4
    assert fc['cue_C'] == 6
    assert fc['end'] == 12

    assert n_trials(triallist) == 12
    assert sumdur(triallist) == pytest.approx(600, .001)


def test_trial_uneven_branch_complex():
    s = "<600/36> cue=[1](A, 2x B, 3x C * X, 2x Y); end=[0]"
    (triallist, settings) = gtt.str_to_triallist(s)

    fc = file_counts(triallist)
    assert fc['cue_A_X'] == 2
    assert fc['cue_B_X'] == 4
    assert fc['cue_C_X'] == 6

    assert fc['cue_A_Y'] == 4
    assert fc['cue_B_Y'] == 8
    assert fc['cue_C_Y'] == 12

    assert fc['end'] == 36

    assert n_trials(triallist) == 36
    assert sumdur(triallist) == pytest.approx(600, .001)
