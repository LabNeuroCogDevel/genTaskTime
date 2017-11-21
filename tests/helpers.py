#!/usr/bin/env python3
# ##### helping functions ##### #
import itertools


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
