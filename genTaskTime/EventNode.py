import anytree
import random
from .EventGrammar import unlist_grammar
from .badmath import (zeno_dichotomy, fit_dist, list_to_length_n,
                      rep_a_b_times, print_uniq_c)


def gen_dist(steps, freq, nsamples, dist, parseid="gen_dist"):
    """
    generate distirubtion
    """
    # if we have an int, make it a list
    if type(steps) == int:
        steps = [steps]

    # how many steps
    ndur = len(steps)

    # the warning message we want to send (if we need to)
    msg = ("WARNING: %s: num durations given (%d)" +
           "doesn't fit with number of events (%d) equally. " +
           "randomly picking") % (parseid, ndur, nsamples)

    if dist == 'g':
        if freq is not None and any([x != 1 for x in freq]):
            print("WARNING: asked for distribution, but provided frequences" +
                  "in duration! Disregarding freqs, generating geometric for" +
                  "%s nsamples" % nsamples)
        dist_array = zeno_dichotomy(nsamples)
        freq = fit_dist(len(steps), dist_array, nsamples)

    # elif dist == 'e':
    steps = rep_a_b_times(steps, freq)
    #print('%s: initial dur before resample: %s' % (parseid, steps))

    dur = list_to_length_n(steps, nsamples, msg)
    return(dur)


# what we need to store for each event entering our event tree
class EventNode(anytree.NodeMixin):

    def __init__(self,name,dur,parent=None,nrep=1,writeout=True,extra=None, verbose=1):
        if(nrep == None): nrep=1
        self.parent=parent
        self.name=name
        self.dur = dur #parse_dur(dur)
        self.nrep=nrep
        self.writeout=writeout
        self.last=False
        self.verbose=verbose
        #self.finalized = False
        self.extra=extra

    def __repr__(self):
        return (f"{self.name}@{self.nrep}reps" +
                f"[{getattr(self,'total_reps','NA')} total] " +
                f"({len(self.path)}up|{len(self.children)}down)")

    # count up and make list of parents to traverse
    def set_last(self):
        self.last = True
        self.need_total = 1  # TODO: should be self.nrep?
        p = self.parent
        self.parents = self.path
        # self.parents=[]
        while p:
            self.need_total *= float(p.nrep)
            # self.parents.append(p)
            p = p.parent
        return(self)

    # how many times is this node hit on it's children branches
    # N.B. still need to combine across branches
    def count_reps(node):
        totalreps = 0
        children = node.children
        for c in children:
            totalreps += c.count_reps()
        if node.nrep:
            if len(children) == 0:
                totalreps = float(node.nrep)
            else:
                totalreps *= float(node.nrep)
        if node.verbose > 1:
            print("count_reps (recursive): %d for all %d children of %s" %
                  (totalreps, len(children), node))
        node.total_reps = totalreps
        return(totalreps)

    def count_branch_reps(node):
        """
        how many total reps do we do of this branch
        cue=[1](2x A); end => 2
        cue=[1](3x B); end => 3
        """
        branch_reps = node.total_reps
        if not hasattr(node, 'branch_reps'):
            pn = node.parent
            while pn:
                branch_reps *= pn.nrep
                pn = pn.parent
            node.branch_reps = branch_reps
        return node.branch_reps

    # TODO: better handle distibutions
    # TODO: parse_dur every iteration
    def parse_dur(self, nperms):
        # ## how many durs do we need?
        # -- should probably stop if do not have total_reps
        nsamples = getattr(self, "master_total_reps",
                           getattr(self, "total_reps",
                                   getattr(self, "nrep", 0)))

        nsamples_perm = nsamples * nperms
        nsamples = round(nsamples_perm)
        if nsamples != nsamples_perm:
            print(f"WARNING: {self.name} ideal {nsamples_perm:.2f} samples but using {nsamples}")
            print("\tconsider adjusting e.g catch trial ratio or total number of trials")

        if self.verbose > 1:
            print('have %d samples to spread for %s' % (nsamples, self.dur))

        # get dist
        try:
            dist = self.dur['dist']
        except TypeError:
            dist = None
        # what is the distribution
        # None is uniform
        if dist is None or dist not in ['u', 'g']:
            dist = 'u'
            if self.verbose > 1:
                print('unknown distribution, using uniform')

        if type(self.dur) in [float, int, type(None)]:
            dur = [self.dur] * nsamples

        elif self.dur['dur']:
            dur = [float(self.dur['dur'])] * int(nsamples)

        elif self.dur['min']:
            # todo distribute for others (just uniform now)
            a = float(self.dur['min'])
            b = float(self.dur['max'])
            # TODO: round intv w.r.t granularity
            if dist == 'u':
                intv = (b-a)/(nsamples-1)
                dur = [a+i*intv for i in range(nsamples)]
            else:
                freqs = zeno_dichotomy(nsamples)
                intv = (b-a)/(len(freqs)-1)
                nums = [a+i*intv for i in range(len(freqs))]
                dur = gen_dist(nums, None, nsamples, dist, self.name)

        elif self.dur['steps']:
            steps = unlist_grammar(self.dur['steps'])
            nums = [float(x['num']) for x in steps]
            freqs = [x['freq'] if x['freq'] is not None else 1 for x in steps]
            dur = gen_dist(nums, freqs, nsamples, dist, self.name)
            if self.verbose > 10:
                print('have steps %s' % nums)
                print('into freqs %s' % freqs)
                print('total n %s' % nsamples)
                print('final durs %s' % dur)

        if self.verbose > 1:
            print("shuffling %s (%d/%d): %s" %
                  (self.name, len(dur), nsamples, dur))
            print_uniq_c(dur)

        random.shuffle(dur)
        dur = dur[0:nsamples]
        self.dur_dist = dur
        # self.dur_dist_avg = functools.reduce(lambda x, y: x+y, dur)/len(dur)
        if len(dur) == 0:
            print(f"WARNING: event {self.name} is never included (no durations)!")
            self.dur_dist_avg = 0
            return dur

        self.dur_dist_avg = sum(dur)/len(dur)
        return dur

    def next_dur(self):
        if len(self.dur_dist) == 0:
            print("WARNING: %s: no more durations to pick from. giving 0" %
                  self.name)
            return(0)
        else:
            dur = self.dur_dist.pop()
            if self.verbose > 10:
                print('%s: %s --> %.01f' % (self.name, self.dur_dist, dur))
            #if not self.picked: self.picked=0
            #self.picked+=1
            return(dur)
