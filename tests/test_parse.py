#!/usr/bin/env python3
import genTaskTime as gtt
import pytest
from helpers import n_trials, sumdur, file_counts


def test_settings_simple():
    s = "<10/1> cue=[2]"
    ast = gtt.parse(s)
    settings = gtt.parse_settings(ast)

    assert settings['ntrial'] == 1
    assert settings['rundur'] == 10


def test_settings_tr():
    s = "<10/1 @1> cue=[2]"
    ast = gtt.parse(s)
    settings = gtt.parse_settings(ast)

    assert settings['ntrial'] == 1
    assert settings['rundur'] == 10
    assert settings['tr'] == 1


def test_settings_stepsize():
    s = "<10/1 stepsize:1> cue=[2]"
    ast = gtt.parse(s)
    settings = gtt.parse_settings(ast)

    assert settings['ntrial'] == 1
    assert settings['rundur'] == 10
    assert settings['granularity'] == 1


def test_settings_itirange():
    s = "<10/1 iti:2.0-4.0> cue=[2]"
    ast = gtt.parse(s)
    settings = gtt.parse_settings(ast)

    assert settings['ntrial'] == 1
    assert settings['rundur'] == 10
    assert settings['miniti'] == 2.0
    assert settings['maxiti'] == 4.0


def test_settings_pad():
    s = "<10/1 pad:2+4> cue=[2]"
    ast = gtt.parse(s)
    settings = gtt.parse_settings(ast)

    assert settings['ntrial'] == 1
    assert settings['rundur'] == 10
    assert settings['startpad'] == 2.0
    assert settings['stoppad'] == 4.0


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


def test_glt1():
    s = "<10/1 glt:sum=cue+resp> cue=[2]; resp=[1]"
    ast = gtt.parse(s)
    settings = gtt.parse_settings(ast)

    assert settings['glts'][0]['formula'] == 'cue+resp'
    assert settings['glts'][0]['name'] == 'sum'


def test_glt2():
    s = "<10/1 glt:sum=cue+resp; glt:diff=resp-cue> cue=[2]; resp=[1]"
    ast = gtt.parse(s)
    settings = gtt.parse_settings(ast)

    assert settings['glts'][0]['formula'] == 'cue+resp'
    assert settings['glts'][1]['formula'] == 'resp-cue'


def test_decon_model():
    s = "<10/1 glt:diff=resp-cue> cue=[2]@GAM; resp=[1]"
    events = gtt.parse_events(gtt.parse(s))
    assert events[0]['model'] == 'GAM'
