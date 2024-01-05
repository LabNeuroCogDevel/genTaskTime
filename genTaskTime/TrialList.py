"""
TrialList is the event tree (LastLeaves) iterated over to build a list of trials.
A trials is a list of event dictionaries.
 [ [{'fname': 'A', 'onset': 0, 'dur': 1.5, 'type': 'event'}, ...],
   ...]


To fill time, inter trial intervals (trials with event types=='iti') are shuffled in.
 [ [{'fname': 'A', 'onset': 0, 'dur': 1.5, 'type': 'event'}, ...],
   [{'type': 'iti', dur=0.1]],
   [{'type': 'iti', dur=0.1]],
   ...]

"""

import pandas as pd
import numpy as np
import pprint
import random
import sys
import os
import copy
from .badmath import print_uniq_c


MYRAND = random.Random(random.randrange(sys.maxsize))
TrialList = list[list[dict]]


def triallist_to_df(triallist: TrialList, start_at_time: float) -> pd.DataFrame:
    """
    @param triallist      list of event lists: LastLeaves.to_triallist + add_itis()
    @param start_at_time  initial onset time of first event
    @return dataframe row per event, including __iti__ time.
            columns: fname, onset, dur
    """
    events = []
    total_time = start_at_time
    for tt in triallist:
        for t in tt:
            # fname is a list like ['cue','left'] or None for iti
            # iti's are repeated based on iti resolution. collapse into one
            name = "_".join(t["fname"]) if t["fname"] else "__iti__"
            if (
                name == "__iti__"
                and len(events) > 0
                and events[-1]["event"] == "__iti__"
            ):
                events[-1]["dur"] += t["dur"]
            else:
                events.append({"event": name, "onset": total_time, "dur": t["dur"]})
            total_time += t["dur"]
    return pd.DataFrame(events)


def df_to_1D(
    event_df: pd.DataFrame, savedir: os.PathLike | None, writedur=True
) -> dict[os.path, list[str]]:
    """
    Writes onsets to per event 1D (AFNI timing) file, unless savedir is None.
    Always returns fname-keyed dict with list of onsets.
    event onsets and optionally married durations on one space separated le line.

    @param event_df dataframe with row per event. cols: event, onset, dur
    @param savedir  where to save all 1D files like event.1D (None to disable write)
    @param writedur included duration married to onset (like 'onset:dur')
    @return
    """
    # initialize dict to hold output file handles.
    # key   - output file handle
    # value - list of "onset:duration" to write to file
    write_to: dict[os.path, list[str]] = {}

    # NB. 20240202 dataframe uses 3 decimal places (milliseconds)
    #              reducing to 2 for 1D files
    for _, event in event_df.iterrows():
        # dont need 1D file for ITI
        # maybe want to add 'no_1D' column to output of triallist_to_df
        # instead of matching on name?
        if event["event"] == "__iti__":
            continue

        if writedur:
            onsetstr = "%.02f:%.02f" % (event["onset"], event["dur"])
        else:
            onsetstr = "%.02f" % event["onset"]

        outname = os.path.join(savedir if savedir else "", event["event"] + ".1D")
        if not write_to.get(outname):
            write_to[outname] = []
        write_to[outname].append(onsetstr)

    # no savedir, no write
    if savedir is None:
        return write_to

    # finished building across all events.
    # can now write onset collection to each file
    for out1D, onsets in write_to.items():
        # maybe event name has path separator?
        # if not, could just mkdirs(savedir) outside loop instead
        os.makedirs(os.path.dirname(out1D), exist_ok=True)
        fh_1D = open(out1D, "w")
        fh_1D.write(" ".join(onsets) + "\n")
        fh_1D.close()

    return write_to


def add_itis(triallist: TrialList, settings: dict, verb=1) -> TrialList:
    """
    fill remaining time with inter trial interval events

    output is the input trial list plus
    as many iti events @ specified granularity that we can fit

    from settings, need 'rundur' 'ntrials', 'granularity', and start/stop padding

    Also see add_itis, _shuffle_triallist, iti_list
    """
    # [ [{'fname': '', 'dur': '' }, ...], ... ]
    # previously computed like
    # all_durs = [o['dur'] for x in triallist for o in x]
    # task_dur = functools.reduce(lambda x, y: x + y, all_durs)
    each_event_dur = [sum([o["dur"] for o in x]) for x in triallist]
    avgtaskdur = np.mean(each_event_dur)
    if verb > 1:
        print_uniq_c(each_event_dur)
    task_dur = sum(each_event_dur)

    allocated_time = float(settings["rundur"])
    rundur = allocated_time - settings.get("stoppad", 0) - settings.get("startpad", 0)
    iti_time = rundur - task_dur
    if iti_time < 0:
        print(
            "ERROR: total event time (%.2f) does not fit in avalible run time (%.2f) (avg trial dur = %.2f == %.2f) !"
            % (task_dur, rundur, task_dur / settings["ntrial"], avgtaskdur)
        )
        print(
            "\tYou want %(ntrial)d trials in %(rundur)f time with min iti %(miniti)f and padding %(startpad)f+%(stoppad)f"
            % settings
        )
        pprint.pprint(np.unique(sorted(each_event_dur)))
        if verb > 1:
            print("trial x event list:")
            pprint.pprint(triallist)
        sys.exit(1)

        # TODO: maybe return None. exitings a bit extreme for a module!
        #  or maybe just adjust?
        rundur = task_dur

    # can fill enough space given the specified maxiti?
    # we take miniti*ntrials out of iti_time becaue they are
    # already included in task time
    just_task_time = iti_time - (settings["miniti"] * settings["ntrial"])
    max_all_itis = settings["maxiti"] * settings["ntrial"]
    if just_task_time > max_all_itis:
        msg = (
            "ERROR: total event time (%.2f in %.2f) requires more iti "
            + "than max (%.2f * %d trials) can provided!"
        )
        print(msg % (task_dur, rundur, settings["maxiti"], settings["ntrial"]))
        sys.exit(1)

    # # calculate number of ITIs (in addition to miniti) we need.
    # make them and add to triallist
    n_iti = int((rundur - task_dur) / settings["granularity"])
    triallist += [
        [{"fname": None, "dur": settings["granularity"], "type": "iti"}]
    ] * n_iti

    return triallist


def _shuffle_triallist(triallist: TrialList, myrand=MYRAND, noitifirst=False) -> None:
    """
    shuffle the list, optionally ensuring outcome does not start with an ITI event type
    works inplace on triallist
    """
    myrand.shuffle(triallist)
    # do we want an iti as first?
    if noitifirst:
        cnt = 1
        warnevery = 50
        while triallist[0][0]["type"] == "iti":
            myrand.shuffle(triallist)
            if cnt % warnevery == 0:
                mgs = (
                    "WARNING: shuffle event list: %d iterations without "
                    + "finiding a no-iti first version"
                )
                print(mgs % cnt)


def shuffle_triallist(
    settings: dict, tl: TrialList, seed=None, maxiterations=5000
) -> tuple[TrialList | None, int]:
    """
    shuffle trial list until the longest ITI is below the max from iti_list()
    """
    triallist = copy.copy(tl)
    # set the seed
    if seed is None:
        seed = random.randrange(sys.maxsize)
    myrand = random.Random(seed)

    # initial shuffle, reproducable with given seed
    noitifirst = settings["iti_never_first"]
    _shuffle_triallist(triallist, myrand, noitifirst)

    # reshuffle while too many itis in a row
    inum = 1
    warnevery = 50
    while max(iti_list(triallist)) > settings["maxiti"]:
        _shuffle_triallist(triallist, myrand, noitifirst)
        inum += 1
        if inum % warnevery == 0:
            mgs = (
                "WARNING: shuffle event list with seed %d has gone "
                + "%d iterations without matching critera (maxiti: %f)"
            )
            print(mgs % (seed, warnevery, settings["maxiti"]))
        if inum >= maxiterations:
            print("ERROR: want %d interations and never found a match!" % maxiterations)
            return (None, seed)

    # give back the shuffle and the seed used
    return (triallist, seed)


def iti_list(triallist: TrialList | None) -> list[float]:
    """
    @param triallist likely with many itis all with settings['granularity'] duration shuffled in. see add_itis(), _shuffle_triallist()
    returns list of collapsed (sum) iti durations between events
    """
    itis = []
    iti_dur = 0
    if triallist is None:
        print("WARNING: generating iti list on empty trial list")
        return itis

    for x in triallist:
        # hit a real (non-iti) event, collect this iti
        if x[0]["type"] == "event" and iti_dur > 0:
            itis.append(iti_dur)
            iti_dur = 0
        for xx in x:
            if xx["type"] == "iti":
                iti_dur += xx["dur"]
    if iti_dur > 0:
        itis.append(iti_dur)
    return itis
