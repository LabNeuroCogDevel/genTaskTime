#!/usr/bin/env python3

# -*- coding: utf-8 -*-
import anytree
import pprint
from .EventGrammar import unlist_grammar, parse, parse_settings
from .LastLeaves import LastLeaves, events_to_tree
import os.path
import copy
from .TrialList import shuffle_triallist, triallist_to_df, df_to_1D
# import itertools


def write_trials(last_leaves: LastLeaves, settings: dict, n_iterations=1000, verb=1) -> None:
    """
    Write n_interations folders (folder name = random seed).
    Must create a deep copy of LastLeaves struct before applying shuffle_trials
    """
    start_at_time = settings.get("startpad", 0)

    # set file name to seed
    # int(math.log10(sys.maxsize)) -- 18 digits
    for iter_i in range(0, n_iterations):
        # get a new trial list
        lastleaves_i = copy.copy(last_leaves)
        triallist = lastleaves_i.to_triallist(settings, verb)
        # shuffle with seed
        (triallist, seed) = shuffle_triallist(settings, triallist)
        # could not find a shuffle that worked!
        if triallist is None:
            continue

        # save to iteration specific directory
        savedir = "%018d" % seed
        os.makedirs(savedir, exist_ok=True)

        edf = triallist_to_df(triallist, start_at_time)
        edf.to_csv(
            os.path.join(savedir, "event_onset_duration.tsv"),
            sep="\t",
            index=False,
            float_format="%.3f",
        )

        # write out 1D timing files. likely for AFNI's '3dDeconvolve -nodata'
        df_to_1D(edf, savedir)

        # TODO: run 3dDeconvolve

        # print a message very 100 trials
        if iter_i % 100 == 0 and verb > 0:
            print("finished %d" % iter_i)


def parse_events(astobj):
    if astobj is None:
        return
    events = unlist_grammar(astobj['allevents'])
    # TODO: recursively expand subevents that are events in full
    return events


def str_to_last_leaves(expstr, verb=1):
    astobj = parse(expstr)
    events = parse_events(astobj)
    # build a tree from events
    last_leaves = events_to_tree(events, verb)
    # list events
    settings = parse_settings(astobj)
    return (last_leaves, settings)


# now only used for testing
def str_to_triallist(expstr, verb=1):
    (last_leaves, settings) = str_to_last_leaves(expstr)
    triallist = last_leaves.to_triallist(settings, verb)
    return (triallist, settings)


def verbose_info(expstr, verb=99):

    print("### given")
    astobj = parse(expstr)
    pprint.pprint(astobj, indent=2, width=20)

    print("\n### parsed events")
    events = parse_events(astobj)
    pprint.pprint(events, indent=2, width=20)

    print('\n# Building Tree')
    # build a tree from events
    last_leaves = events_to_tree(events)
    root = last_leaves[0].root

    print("\n### tree")
    print(anytree.RenderTree(root))

    print("\n### last leaves")
    print(last_leaves)
