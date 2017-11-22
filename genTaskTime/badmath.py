#!/usr/bin/env python3
# ## bad math
import random
import math
import functools


# when mod is zero, make max of base
def mod_no_zero(a, b, zero=None):
    if zero is None:
        zero = b
    r = a % b
    if r == 0:
        r = zero
    return(r)


def fit_dist(nelm, freq, nsamples):
    """
    adjust freq list such that
      sum(freq) == nsamples
      len(freq) == nelm
    does not do a good job preserving geometic distribution
    """
    nsamples_in_freq = sum(freq)
    if nelm > nsamples_in_freq:
        print("WARNING: fitting distribution wih more elements than sum of" +
              " frequencies. This will get weird")

    # if we have fewer elements than we do
    # frequencies to assign to them:
    #  pop off the lowest freq
    #  and add it to the next lowest
    # -- be careful not to add so many to the last
    #    that it outnumbers the next to last
    while nelm < len(freq):
        lastf = freq.pop()

        # push value to next lowest
        # if last is too high
        idx = len(freq) - 1
        cmpval = 9e9
        if idx > 0:
            cmpval = freq[idx-1]
        # while we can, find find element of freq that is smalllest
        while idx > 0 and freq[idx] >= cmpval:
            idx -= 1
            cmpval = freq[idx-1]
        freq[idx] += lastf

    # if we have more elements than we do
    # frequencies to assign to them:
    # add a freq of 1 to the end.
    # remove from the largest and work down
    i = 0
    while nelm > len(freq):
        freq[i] -= 1
        freq.append(1)
        i = (i + 1) % len(freq)

    # if we want nsamples but freq doesn't sum to that number
    # we need to do some fiddling

    # if we have too many frequences, bump them
    i = 0
    while nsamples_in_freq > nsamples:
        # while we are not all ones but our current index is 1
        # move to a different index
        while freq[i] == 1 and nsamples_in_freq <= len(freq):
            i = (i + 1) % len(freq)

        freq[i] -= 1
        i = (i + 1) % len(freq)
        nsamples_in_freq = sum(freq)

    # if we have too few frequences, increase them
    while nsamples_in_freq < nsamples:
        freq[i] += 1
        i = (i + 1) % len(freq)
        nsamples_in_freq = sum(freq)

    return(freq)


def zeno_dichotomy(n):
    """
    geom distriubtion by halving each next step
    (similiar to Zeno's dichotomy paradox)
    """
    n = int(n)
    if n <= 1:
        return([1])
    else:
        n = int(n/2)
        return [n] + zeno_dichotomy(n)


def list_to_length_n(inlist, nsamples, msg):
    n = len(inlist)
    times_more = math.floor(nsamples/n)
    add_more = nsamples % n
    orig = inlist
    out = inlist * times_more

    # we'll need to add at least one more (maybe truncatd) set of inlist
    # if we are mod==0, it should be full, set add_more to the full length
    if add_more != 0:
        random.shuffle(orig)
        out += orig[0:add_more]

    # print('%d * %d (+ %d)' % (n, times_more, add_more))
    return(out)


def reduce_sum(v):
    return(functools.reduce(lambda x, y: x + y, v))


def rep_a_b_times(a, b):
    if len(a) != len(b):
        raise ValueError("a and b have different lengths!")

    listoflist = [[a[i]]*int(b[i]) for i in range(len(a))]
    r = reduce_sum(listoflist)
    return(r)
