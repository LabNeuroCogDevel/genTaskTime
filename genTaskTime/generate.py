#!/usr/bin/env python3

# -*- coding: utf-8 -*-
import random
import anytree
import copy
import functools
import pprint
import sys
import os
from .EventNode import EventNode
from .EventGrammar import unlist_grammar, parse, parse_settings
from .badmath import print_uniq_c
# import itertools
import numpy as np
MYRAND = random.Random(random.randrange(sys.maxsize))


def parse_events(astobj):
    if astobj is None:
        return
    events = unlist_grammar(astobj['allevents'])
    # TODO: recursively expand subevents that are events in full
    return(events)

# subevent list is an elment of 'eventtypes'
# this builds a tree of them
# a=mkChild(EventNode('root',dur=0),events[0]['eventtypes'])
    print("\n#### events")


def mkChild(parents, elist, verb=1):
    """
    @param parents  list of EventNotes (or single root node)
    @param elist    list of events (likely from parse_events/unlist_grammar)
    """

    # make sure we're starting with a list
    # even if it's only one item
    if type(parents) not in [list, tuple]:
        print('mkChild: parent type=%s, expected list: %s' %
              (type(parents), parents))
        parents = [parents]

    # children will be added to parents
    children = parents

    # tmp copy because we're poping off it
    # and we need a list even if it's only one item
    subevent_list = unlist_grammar(copy.deepcopy(elist))
    if type(subevent_list) not in [list, tuple]:
        subevent_list = [subevent_list]

    # TODO: look at catchratio?
    # catch trials are special case like having children

    # no more children to process
    # end recursive calls
    if len(subevent_list) == 0:
        return children

    children = []
    if verb > 1:
        print("popping from: %s" % subevent_list)
    seitem = subevent_list.pop(0)

    # skip '*'
    if type(seitem) is str:
        print(f"mkChild: skipping str '{seitem}' (expect '*')")
        seitem = subevent_list.pop(0)

    if verb > 1:
        print("mkChild on %s" % seitem)

    # if we only have 1 subevent, still need to treat it like a list
    if type(seitem['subevent']) not in [list, tuple]:
        if verb > 1:
            print(f"mkChild: item type={type(seitem['subevent'])} not list/tuple")
            print('coercing: %s' % str(seitem['subevent']))
        seitem['subevent'] = [seitem['subevent']]

    these_subevets = unlist_grammar(seitem['subevent'])

    for sube_info in these_subevets:
        if type(sube_info) is str:
            if verb > 1:
                print(f"\tskipping {sube_info} (expect == ')")
            continue  # skip ','

        if verb > 1:
            print("\tsube_info: %s" % sube_info)

        name = sube_info['subname']
        freq = sube_info['freq']
        if freq:
            freq = int(freq)
        for p in parents:
            if verb > 1:
                print("\t\tadding child %s to parent %s" % (name, p))
            children.append(EventNode(name, parent=p,
                            nrep=freq, dur=0, verbose=verb))

    # continue down the line
    # TODO: fix bad hack; break out of list
    if len(subevent_list) == 1 and str(subevent_list[0] == list):
        print("\tTODO: do not break recursive list")
        subevent_list = subevent_list[0]

    if verb > 1:
        print("\t\trecurse DOWN: %s" % subevent_list)
    children = mkChild(children, subevent_list, verb)

    return children


# for a ast list of events, build a tree
def events_to_tree(events, verb=1):
    """
    Generate list of EventNodes representing terminal tree leaves.
    Each leaf represents a the combination of events describing a single run.

    Input from parse_events (unlist_grammar of 'allevents' from AST).
    20240131: change in representation? updated libaries fails many tests
    """
    last_leaves = None
    for event in events:
        catchrat = float(event['catchratio']) if event['catchratio'] else 0

        if last_leaves is None:
            parents = [None]
        else:
            parents = last_leaves

        last_leaves = [EventNode(event['eventname'],
                                 dur=event['dur'],
                                 parent=r,
                                 verbose=verb,
                                 nrep=1-catchrat)
                       for r in parents
                       if (r is None or not r.last)]

        # add back catch (or any other last)
        # only if we aren't starting at root and there are some to add
        if parents[0]:
            term_leaves = [e for e in parents if e.last]
            if term_leaves:
                last_leaves += term_leaves

        if event['eventtypes']:
            if verb > 1:
                print('making children for %s' % last_leaves)
                pprint.pprint(event['eventtypes'])
            last_leaves = mkChild(last_leaves, event['eventtypes'], verb)

        # if catch trials should end here
        if catchrat > 0 :
            print(last_leaves)
            catch_nodes = [EventNode('__catch__',
                           dur=0, nrep=catchrat, parent=r,
                           verbose=verb).set_last()
                           for r in last_leaves]

            if verb > 0:
                print(f'{event["name"]}: appending {len(catch_nodes)} catch nodes')
                print(catch_nodes)

            last_leaves += catch_nodes

    if len(last_leaves) > 0:
        last_leaves[0].root.verbose = verb

    return last_leaves


# return a unique string for a node
# currently just use that nodes name
def uniquenode(n):
    return('%s' % n.name)  # '%s %s'%(n.name,n.dur)


def create_master_refs(root):
    """
     create a master node used calculate delays
    each node in the tree with the same name points to the same master node
    """
    # root requires no calculation -- there is only one (right!?)
    masternodes = {}

    for n in (root, *root.descendants):
        nname = uniquenode(n)
        if not masternodes.get(nname):
            n.master_total_reps = 0
            masternodes[nname] = n
        n.master_node = masternodes.get(nname)
        # this is wrong
        #   n.master_node.master_total_reps += n.total_reps
        # total_reps is "total on that branch".
        #  at root == nperms
        #  at leaf might it is == nrep

        # should be sum of leaf nodes need_total
        n.master_node.master_total_reps += n.count_branch_reps()
    return([x for x in masternodes.values()])


def event_tree_to_list(last_leaves, n_rep_branches, min_iti):
    isverb = last_leaves[0].root.verbose > 1
    if isverb:
        print('event_tree_to_list: %d leaves, %d n_reps' %
              (len(last_leaves), n_rep_branches))
    # tree to list
    triallist = []
    for l in last_leaves:
        branch_nodes = l.parents

        n_total_branch_reps = n_rep_branches * l.need_total
        # l.need_total == l.count_branch_reps()

        # we have:
        #  n_rep_branches  -- total repeats (based on nperm)
        #  l.count_branch_reps() -- number of times this node on this branch
        #  l.nrep -- repeats from grammer (e.g. 2x )
        msg = ("working from %s, %d == %d total reps." +
               "we repeat everything %d times. total = %d") % (
               l, l.count_branch_reps(),
               l.need_total, n_rep_branches,
               n_total_branch_reps)
        if l.root.verbose > 1:
            print(msg)

        for branch_rep_i in range(round(n_total_branch_reps)):
            thistrial = []
            fname = []
            dur = 0
            for n in branch_nodes:
                n = n.master_node
                if n.dur != 0:
                    if fname:
                        thistrial.append({'fname': fname,
                                          'dur': dur,
                                          'type': 'event'})
                    fname = []
                    dur = 0
                fname.append(n.name)
                dur += n.next_dur()
            if fname:
                thistrial.append({'fname': fname, 'dur': dur, 'type': 'event'})
            if min_iti is not None and min_iti > 0:
                thistrial.append({'fname': None,
                                  'dur': min_iti,
                                  'type': 'iti'})

            triallist.append(thistrial)
            # for all the counts of of branch
            # for j in range(l.count_branch_reps() * n_rep_branches):
            #     triallist.append(thistrial)
    if l.root.verbose > 5:
        pprint.pprint(triallist)
    return(triallist)


def iti_list(triallist):
    """
    @param triallist
    returns list of iti durations
    """
    itis = []
    iti_dur = 0
    if triallist is None:
        print("WARNING: generating iti list on empty trial list")
        return(itis)
    for x in triallist:
        if x[0]['type'] == 'event' and iti_dur > 0:
            itis.append(iti_dur)
            iti_dur = 0
        for xx in x:
            if xx['type'] == 'iti':
                iti_dur += xx['dur']
    if iti_dur > 0:
        itis.append(iti_dur)
    return(itis)


def _shuffle_triallist(triallist, myrand=MYRAND, noitifirst=False):
    """
    shuffle the list, optionally keeping the first item first
    works inplace on triallist
    """
    myrand.shuffle(triallist)
    # do we want an iti as first?
    if noitifirst:
        cnt = 1
        warnevery = 50
        while triallist[0][0]['type'] == 'iti':
            myrand.shuffle(triallist)
            if(cnt % warnevery == 0):
                mgs = "WARNING: shuffle event list: %d iterations without " +\
                      "finiding a no-iti first version"
                print(mgs % cnt)


def shuffle_triallist(settings, tl, seed=None, maxiterations=5000):
    triallist = copy.copy(tl)
    # set the seed
    if seed is None:
        seed = random.randrange(sys.maxsize)
    myrand = random.Random(seed)

    # initial shuffle, reproducable with given seed
    noitifirst = settings['iti_never_first']
    _shuffle_triallist(triallist, myrand, noitifirst)

    # reshuffle while too many itis in a row
    inum = 1
    warnevery = 50
    while max(iti_list(triallist)) > settings['maxiti']:
        _shuffle_triallist(triallist, myrand, noitifirst)
        inum += 1
        if(inum % warnevery == 0):
            mgs = "WARNING: shuffle event list with seed %d has gone " +\
                  "%d iterations without matching critera (maxiti: %f)"
            print(mgs % (seed, warnevery, settings['maxiti']))
        if(inum >= maxiterations):
            print("ERROR: want %d interations and never found a match!" %
                  maxiterations)
            return((None, seed))

    # give back the shuffle and the seed used
    return((triallist, seed))


def write_list_to_file(triallist, seed, start_at_time, writedur=True):
    # initialize start time and dict to hold output file handles
    total_time = start_at_time
    write_to = {}
    for tt in triallist:
        for t in tt:
            # if we have a fname,
            # we want to write this event (stimulus) onset to a file
            if t['fname']:
                # name should be unique to this iteration.
                #    iter_id = "%05d"%iter_i
                # lets use the seed instead, so we can get back to it
                iter_id = "%018d" % seed
                fname = "_".join(t['fname'])
                fname = fname + '.1D'
                outname = os.path.join(iter_id, fname)

                # if we have not stored this name yet
                # we should open it and store the handle
                if not write_to.get(outname):
                    # print('%s'%outname)
                    outdir = os.path.dirname(outname)
                    if not os.path.isdir(outdir):
                        os.mkdir(outdir)
                    write_to[outname] = open(outname, 'w')

                # write onset time of this stimulus/event
                # optionally put the duration in there too
                # like: (onset:dur) e.g 30:1.5
                if writedur:
                    onsetstr = "%.02f:%.02f " % (total_time, t['dur'])
                else:
                    onsetstr = "%.02f " % total_time

                # finally write it
                write_to[outname].write(onsetstr)

            # increment total time
            total_time += t['dur']

    # add new lines to the end of all the files and close the handle
    for v in write_to.values():
        v.write('\n')
        v.close()


# settings stores 'rundur' and maybe granularity and finish_with_left
def add_itis(triallist, settings, verb=1):
    # [ [{'fname': '', 'dur': '' }, ...], ... ]
    # previously computed like
    # all_durs = [o['dur'] for x in triallist for o in x]
    # task_dur = functools.reduce(lambda x, y: x + y, all_durs)
    each_event_dur = [sum([o['dur'] for o in x]) for x in triallist]
    avgtaskdur = np.mean(each_event_dur)
    if verb > 1:
        print_uniq_c(each_event_dur)
    task_dur = sum(each_event_dur)

    allocated_time = float(settings['rundur'])
    rundur = allocated_time - settings['stoppad'] - settings['startpad']
    iti_time = rundur - task_dur
    if iti_time < 0:
        print("ERROR: total event time (%.2f) does not fit in avalible run time (%.2f) (avg trial dur = %.2f == %.2f) !" %
              (task_dur, rundur, task_dur/settings['ntrial'], avgtaskdur))
        print("\tYou want %(ntrial)d trials in %(rundur)f time with min iti %(miniti)f and padding %(startpad)f+%(stoppad)f" % settings)
        pprint.pprint(np.unique(sorted(each_event_dur)))
        if verb > 1:
            print('trial x event list:')
            pprint.pprint(triallist)
        sys.exit(1)

        # TODO: maybe return None. exitings a bit extreme for a module!
        #  or maybe just adjust?
        rundur = task_dur

    # can fill enough space given the specified maxiti?
    # we take miniti*ntrials out of iti_time becaue they are
    # already included in task time
    just_task_time = iti_time - (settings['miniti'] * settings['ntrial'])
    max_all_itis = settings['maxiti'] * settings['ntrial']
    if just_task_time > max_all_itis:
        msg = "ERROR: total event time (%.2f in %.2f) requires more iti " + \
              "than max (%.2f * %d trials) can provided!"
        print(mgs % (task_dur, rundur, settings['maxiti'], settings['ntrial']))
        sys.exit(1)

    # # calculate number of ITIs (in addition to miniti) we need.
    # make them and add to triallist
    n_iti = int((rundur - task_dur)/settings['granularity'])
    triallist += [[{'fname': None,
                    'dur': settings['granularity'],
                    'type': 'iti'}]] * n_iti

    return(triallist)

def rand_round(val, myrand=None):
    rand = myrand.random() if myrand else 0
    return int(val + rand)


def fit_tree(last_leaves, ntrials, myrand=MYRAND):
    """
    update tree for the number of trials we have
    updates the nodes of tree
    """
    # how many times do we go down the tree?
    nperms = 0
    leaf_totals = [l.set_last().need_total for l in last_leaves]
    adj_factor = min(leaf_totals)
    adjusted_totals = [rand_round(lf.need_total/adj_factor, myrand)
                       for lf in last_leaves]
    nperms = sum(adjusted_totals)

    n_rep_branches = ntrials/nperms

    # check sanity
    if n_rep_branches < 1:
        print('WARNING: your expreiment has too few trials' +
              ('(%d) to accomidate all branches(%d)' % (ntrials, nperms)))
        n_rep_branches = 1
    elif n_rep_branches != int(n_rep_branches):
        print(('WARNING: your expreiment will not be balanced\n\t' +
               '%d trials / %d event branches is not a whole number'
               '(%f);') % (ntrials, nperms, n_rep_branches))
        # 'maybe try %f trials
        # '%(ntrials,nperms,n_rep_branches, (int(n_rep_branches)*nperms) ))

    n_rep_branches = int(n_rep_branches)

    # each node should have the nrep sum of its children (x nreps of that node)
    # node.totalreps
    root = last_leaves[0].root

    # get how many time each node in the tree will be seen
    root.count_reps()
    # different branches have nodes with the same name
    # link them all to one node so we can draw duration times from that one
    unique_nodes = create_master_refs(root)

    # set up delay distributions
    for u in unique_nodes:
        u.parse_dur(n_rep_branches)

    return (n_rep_branches, nperms)


def gen_events(last_leaves, settings, verb=1):
    # settings
    ntrials = settings['ntrial']

    # update tree for the number of trials we have
    # updates the nodes of tree
    (n_rep_branches, nperms) = fit_tree(last_leaves, ntrials)

    min_iti = settings['miniti']

    triallist = event_tree_to_list(last_leaves, n_rep_branches, min_iti)
    triallist = add_itis(triallist, settings, verb)

    if verb > 0:
        print("single run: %d reps of (%d final branches, seen a total of %d times)" %
            (n_rep_branches, len(last_leaves), nperms))
    return(triallist)


def write_trials(last_leaves, settings, n_iterations=1000, verb=1):
    start_at_time = settings['startpad']

    # set file name to seed
    # int(math.log10(sys.maxsize)) -- 18 digits
    for iter_i in range(0, n_iterations):
        # get a new trial list
        triallist = gen_events(copy.copy(last_leaves), settings, verb)
        # shuffle with seed
        (triallist, seed) = shuffle_triallist(settings, triallist)
        # could not find a shuffle that worked!
        if triallist is None:
            continue
        # start timer after or initial rest period
        write_list_to_file(triallist, seed, start_at_time)

        # TODO: run 3dDeconvolve

        # print a message very 100 trials
        if iter_i % 100 == 0 and verb > 0:
            print('finished %d' % iter_i)


def str_to_last_leaves(expstr, verb=1):
    astobj = parse(expstr)
    events = parse_events(astobj)
    # build a tree from events
    last_leaves = events_to_tree(events, verb)
    # list events
    settings = parse_settings(astobj)
    return((last_leaves, settings))


# now only used for testing
def str_to_triallist(expstr, verb=1):
    (last_leaves, settings) = str_to_last_leaves(expstr)
    triallist = gen_events(last_leaves, settings, verb)
    return((triallist, settings))


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
