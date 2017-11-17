#!/usr/bin/env python3
import genTaskTime as gtt
import pytest
import itertools


def test_settings_simple():
    s = "<10/1> cue=[2]"
    ast = gtt.parse(s)
    settings = gtt.parse_settings(ast)

    assert settings['ntrial'] == 1
    assert settings['rundur'] == 10


def test_simple_event():
    s = "<10/1> cue=[2]"
    ast = gtt.parse(s)
    events = gtt.parse_events(ast)
    assert events[0]['eventname'] == 'cue'
    assert events[0]['dur']['dur'] == '2'


def test_trial_simple():
    s = "<10/1> cue=[2]"
    (triallist, settings) = gtt.str_to_triallist(s)
    # first and only event is trial 0, event 0
    cue = triallist[0][0]
    # should be what we asked for
    assert cue['dur'] == 2
    assert cue['fname'] == ['cue']
    # 1 trial in 10seconds of runtime
    assert n_trials(triallist) == 1
    assert sumdur(triallist) == pytest.approx(10, .001)


def test_trial_seq():
    s = "<10/1> cue=[2]; end=[3]"
    (triallist, settings) = gtt.str_to_triallist(s)

    trial = triallist[0]
    cue = trial[0]
    assert cue['dur'] == 2
    end = trial[1]
    assert end['dur'] == 3
    assert n_trials(triallist) == 1
    assert sumdur(triallist) == pytest.approx(10, .001)


def test_trial_branch():
    s = "<20/2> cue=[1](A, B); end=[3]"
    (triallist, settings) = gtt.str_to_triallist(s)

    assert n_trials(triallist) == 2
    assert sumdur(triallist) == pytest.approx(20, .001)

    for trial in triallist[0:2]:
        cue = trial[0]
        assert cue['dur'] == 1
        end = trial[1]
        assert end['dur'] == 3


def test_trial_branch_threetimes():
    s = "<60/6> cue=[1](A, B); end=[3]"
    (triallist, settings) = gtt.str_to_triallist(s)

    assert n_trials(triallist) == 6
    assert sumdur(triallist) == pytest.approx(60, .001)

    fc = file_counts(triallist)
    assert fc['cue_A'] == 3
    assert fc['cue_B'] == 3
    assert fc['end'] == 6

    # check each of the 6 has a cue and an end that are expected dur
    for trial in triallist[0:6]:
        cue = trial[0]
        assert cue['dur'] == 1
        end = trial[1]
        assert end['dur'] == 3

    assert triallist[6][0]['fname'] is None


def test_trial_branch_fork():
    s = "<60/4> cue=[1](A, B * D, E); end=[3]"
    (triallist, settings) = gtt.str_to_triallist(s)

    assert n_trials(triallist) == 4
    assert sumdur(triallist) == pytest.approx(60, .001)

    fc = file_counts(triallist)
    for names in ['cue_A_D', 'cue_B_D', 'cue_A_E', 'cue_B_E']:
        assert fc[names] == 1
    assert fc['end'] == 4

# ##### helping functions ##### #


# count trials that have outname
def n_trials(tl):
    n = 0
    for t in tl:
        if len(t) > 1 or not t[0].get('fname') is None:
            n += 1
        else:
            continue
    return(n)


def sumdur(tl):
    s = 0
    for t in tl:
        if type(t) == dict:
            s += t['dur']
        else:
            s += sumdur(t)
    return(s)


def allfiles(tl):
    n = []
    for t in tl:
        if type(t) == dict:
            if not t.get('fname') is None:
                n += ['_'.join(t['fname'])]
        else:
            n += allfiles(t)
    return(n)


def file_counts(tl):
    fnames = allfiles(tl)
    i = itertools.groupby(sorted(fnames))
    d = {x: len(list(y)) for x, y in i}
    return(d)
