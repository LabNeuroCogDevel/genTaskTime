import anytree
import copy
import pprint
import re
from .EventNode import EventNode, create_master_refs
from .EventGrammar import unlist_grammar
from .TrialList import add_itis, TrialList


def rand_round(val, myrand=None):
    rand = myrand.random() if myrand else 0
    return int(val + rand)


class LastLeaves(list):
    """
    List containing pointers to EventNode elements.
    Each element is the last leaf node in a trials event tree.
    All leaves should share the same root.

    See events_to_tree for actual construction.
    """

    def __init__(self, *args: list[EventNode], **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)

    def root(self):
        if len(self) > 0:
            return self[0].root
        else:
            return None

    def __str__(self):
        return ", ".join([str(x) for x in self])

    def __repr__(self):
        "use anytree's render to see tree"
        if len(self) > 0:
            return str(anytree.RenderTree(self[0].root))
        else:
            return str(self)

    def event_tree_to_list(self, n_rep_branches, min_iti) -> TrialList:
        """
        Make a list of trials by
          making n_re_branches passes of the EventNode list (LastLeaves)

        cf. to_triallist (wraps this. uses settings, adds itis)

        Each trial is a list of event dicts with keys 'fname','dur', and 'type'
        type is either 'iti' or 'event'

        Expect node.set_last() already run on each of the leaves,
          so node.need_total is the necessary value.

        @param n_rep_branches  how many repeats f/all branches(ntrials/nperms)
                               calculated by fit_tree()
        """
        isverb = len(self) > 0 and self.root().verbose > 1
        if isverb:
            print(
                "event_tree_to_list: %d leaves, %d n_reps" % (len(self), n_rep_branches)
            )

        triallist = []
        for l in self:
            branch_nodes = l.parents

            n_total_branch_reps = n_rep_branches * l.need_total
            # l.need_total == l.count_branch_reps()

            # we have:
            #  n_rep_branches  -- total repeats (based on nperm)
            #  l.count_branch_reps() -- number of times this node on this branch
            #  l.nrep -- repeats from grammer (e.g. 2x )
            msg = (
                "working from %s, %d == %d total reps."
                + "we repeat everything %d times. total = %d"
            ) % (
                l,
                l.count_branch_reps(),
                l.need_total,
                n_rep_branches,
                n_total_branch_reps,
            )
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
                            thistrial.append(
                                {"fname": fname, "dur": dur, "type": "event"}
                            )
                        fname = []
                        dur = 0

                    # __catch__ trials are special
                    # timing should go into preceding child
                    # identified by name. TODO: catch property (or function) to node?
                    if not re.match(r"__catch__[0-9]+", n.name):
                        fname.append(n.name)
                    dur += n.next_dur()
                if fname:
                    thistrial.append({"fname": fname, "dur": dur, "type": "event"})
                if min_iti is not None and min_iti > 0:
                    thistrial.append({"fname": None, "dur": min_iti, "type": "iti"})

                triallist.append(thistrial)
                # for all the counts of of branch
                # for j in range(l.count_branch_reps() * n_rep_branches):
                #     triallist.append(thistrial)
        if l.root.verbose > 5:
            pprint.pprint(triallist)
        return triallist

    def fit_tree(self, ntrials: int, myrand=None) -> tuple[int, int]:
        """
        @param ntrials     total trials to fit into run
        @param myran       random seed, see MYRAND
        @returns           tuple (n_rep_branches, nperms)
          nperms         - total count need to represent all branches
                           normalized to nreps; accounts for uneven repeats
          n_rep_branches - how many repeats f/all branches(ntrials/nperms)
                           input for event_tree_to_list

        number of runs calculated relative to minimum node.nreps.
        which can be < 1 (catchratio)

        runs side effect functions to update node properties:
          * updates node.need_total (set_last)
          * update tree for the number of trials we have (count_reps)
          * duration distribution (parse_dur)
        """
        # how many times do we go down the tree?
        nperms = 0
        leaf_totals = [l.set_last().need_total for l in self]
        adj_factor = min(leaf_totals)
        adjusted_totals = [
            rand_round(lf.need_total / adj_factor, myrand) for lf in self
        ]
        nperms = sum(adjusted_totals)

        n_rep_branches = ntrials / nperms

        # check sanity
        if n_rep_branches < 1:
            print(
                "WARNING: your expreiment has too few trials"
                + ("(%d) to accomidate all branches(%d)" % (ntrials, nperms))
            )
            n_rep_branches = 1
        elif n_rep_branches != int(n_rep_branches):
            print(
                "WARNING: your expreiment will not be balanced\n\t"
                + f"{ntrials} trials / {nperms} event branches "
                + f"({len(self)} leaves)"
                + f"is not a whole number ({n_rep_branches});\n\t"
                + str(self)
            )
            # 'maybe try %f trials
            # '%(ntrials,nperms,n_rep_branches, (int(n_rep_branches)*nperms) ))

        n_rep_branches = int(n_rep_branches)

        # each node should have the nrep sum of its children (x nreps of that node)
        # node.totalreps
        root = self.root()

        # get how many time each node in the tree will be seen
        root.count_reps()
        # different branches have nodes with the same name
        # link them all to one node so we can draw duration times from that one
        unique_nodes = create_master_refs(root)

        # set up delay distributions
        for u in unique_nodes:
            u.parse_dur(n_rep_branches)

        return (n_rep_branches, nperms)

    def to_triallist(self, settings: dict, verb=1) -> TrialList:
        """
        Use settings to create list of trials
        wraps event_tree_to_list and add_itis
        """
        # settings
        ntrials = settings["ntrial"]

        # update tree for the number of trials we have
        # updates the nodes of tree
        (n_rep_branches, nperms) = self.fit_tree(ntrials)

        min_iti = settings["miniti"]

        triallist = self.event_tree_to_list(n_rep_branches, min_iti)
        triallist = add_itis(triallist, settings, verb)

        if verb > 0:
            print(
                "single run: %d reps of (%d final branches, seen a total of %d times)"
                % (n_rep_branches, len(self), nperms)
            )
        return triallist


def events_to_tree(events, verb=1) -> LastLeaves:
    # TODO: this should be the __init__ constructor for LastLeaves?
    """
    @param events 'allevents' AST from parse_events/unlist_grammar
    @param verb    verbosity (level > 1 prints extra/debug info)

    Generate list of EventNodes representing terminal tree leaves.
    Each leaf represents a the combination of events describing a single run.
    """
    last_leaves = None
    catch_count = 0
    for event in events:
        catchrat = float(event["catchratio"]) if event["catchratio"] else 0

        if last_leaves is None:
            parents = [None]
        else:
            parents = last_leaves

        last_leaves = [
            EventNode(
                event["eventname"],
                dur=event["dur"],
                parent=r,
                verbose=verb,
                # nrep=1-catchrat
            )
            for r in parents
            if (r is None or not r.last)
        ]

        if event["eventtypes"]:
            if verb > 1:
                print("making children for %s" % last_leaves)
                pprint.pprint(event["eventtypes"])
            last_leaves = mkChild(last_leaves, event["eventtypes"], verb)

        # add back catch (or any other last)
        # only if we aren't starting at root and there are some to add
        if parents[0]:
            term_leaves = [e for e in parents if e.last]
            if term_leaves:
                last_leaves += term_leaves

        # if catch trials, should end here
        # set_last() will set node.last = True
        if catchrat > 0:
            print(last_leaves)
            catch_count += 1
            catch_nodes = [
                EventNode(
                    f"__catch__{catch_count}",
                    dur=0,
                    nrep=catchrat,
                    parent=r,
                    verbose=verb,
                ).set_last()
                for r in last_leaves
                if not r.last
            ]

            if verb > 0:
                print(f'{event["name"]}: appending {len(catch_nodes)} catch nodes')
                print(catch_nodes)

            last_leaves += catch_nodes

    if len(last_leaves) > 0:
        last_leaves[0].root.verbose = verb

    return LastLeaves(last_leaves)


def mkChild(parents, elist, verb=1):
    """
    @param parents  list of EventNotes (or single root node)
    @param elist    list of events (likely from parse_events/unlist_grammar)

    Recursive function to populate leaves of tree
    """

    # make sure we're starting with a list
    # even if it's only one item
    if type(parents) not in [list, tuple]:
        print("mkChild: parent type=%s, expected list: %s" % (type(parents), parents))
        parents = [parents]

    # children will be added to parents
    children = parents

    # tmp copy because we're poping off it
    # and we need a list even if it's only one item
    subevent_list = unlist_grammar(copy.deepcopy(elist))
    if type(subevent_list) not in [list, tuple]:
        subevent_list = [subevent_list]

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
    if type(seitem["subevent"]) not in [list, tuple]:
        if verb > 1:
            print(f"mkChild: item type={type(seitem['subevent'])} not list/tuple")
            print("coercing: %s" % str(seitem["subevent"]))
        seitem["subevent"] = [seitem["subevent"]]

    these_subevets = unlist_grammar(seitem["subevent"])

    for sube_info in these_subevets:
        if type(sube_info) is str:
            if verb > 1:
                print(f"\tskipping {sube_info} (expect == ')")
            continue  # skip ','

        if verb > 1:
            print("\tsube_info: %s" % sube_info)

        name = sube_info["subname"]
        freq = sube_info["freq"]
        if freq:
            freq = int(freq)
        for p in parents:
            if verb > 1:
                print("\t\tadding child %s to parent %s" % (name, p))

            children.append(EventNode(name, parent=p, nrep=freq, dur=0, verbose=verb))

    # continue down the line
    # TODO: fix bad hack; break out of list
    if len(subevent_list) == 1 and str(subevent_list[0] == list):
        print("\tTODO: do not break recursive list")
        subevent_list = subevent_list[0]

    if verb > 1:
        print("\t\trecurse DOWN: %s" % subevent_list)

    children = mkChild(children, subevent_list, verb)

    return children
