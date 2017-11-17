#!/usr/bin/env python3
import genTaskTime as gtt


def test_cli_show(tmpdir):
    tmpdir.chdir()
    gtt.main('-n', '<10/1> cue=[1]')


def test_cli(tmpdir):
    tmpdir.chdir()
    gtt.main('-o', 'stims', '-i', '2', '<10/1> cue=[1]')
    iters = tmpdir.join('stims').listdir()
    assert len(iters) == 2
