# genTaskTime
* Parses a domain specific language describing a rapid event related fmri task
* Create stimulus onset files.

Designed for optimizing task timing with `3dDeconvolve -nodata` as an alternative to `optseq`, `RSFgen`, and `make_random_timing.py`

See
* https://afni.nimh.nih.gov/pub/dist/HOWTO/howto/ht03_stim/html/stim_background.html
* http://andysbrainblog.blogspot.com/2012/06/design-efficiency.html


Jump to [Install](#Install) or command [grammar](#Grammar).

## Usage
```bash
# help
genTaskTime -h

# create 1 iteration of files like stims/$seed/{cue_A,cue_B,dly,end}.1D
genTaskTime -i 1 -o stims '<20/4> cue=[1.5](A,B); dly=[3x 3, 1x 6]; end=[1.5]'

# dryrun: see notes and tree
genTaskTime -n '<20/4> cue=[1.5](A,B); dly=[3x 3, 1x 6]; end=[1.5]'
```

### Example
for [lncdtask](github.com/LabNeuroCogDevel/lncdtask)'s `dollarreward`
```bash
genTaskTime -i 1 -o /tmp/gtt_test/ '<300/40> ring=[1.5](rew,neu){.333}; prep=[1.5]{.333}; dot=[1.5](left,right)'
```
creates timing for 28 full trials and 2 separate catch-trial types: 40*.333 of first ending after ring, and 40*.333*.333 of the second ending after prep.


`genTaskTime -n '<480/40> ring=[1.5](rew,neu){.333}; prep=[1.5]{.333}; dot=[1.5](left,right)'` (dry run) will show the event tree, like:
```
ring
├── rew
│   ├── __catch__1
│   └── prep
│       ├── __catch__2
│       └── dot
│           ├── left
│           └── right
└── neu
    ├── __catch__1
    └── prep
        ├── __catch__2
        └── dot
            ├── left
            └── right
```

The output timing 1D files, ready for AFNI's `3dDeconvolve -nodata`, look like
```
tree /tmp/gtt_test/
/tmp/gtt_test/
└── 8906532558624107687
    ├── dot_left.1D
    ├── dot_right.1D
    ├── prep.1D
    ├── ring_neu.1D
    └── ring_rew.1D
```

`8906532558624107687` is the random seed. Running again with that seed should produce the same timing.

An single 1D file has onset married to duration like `onset:dur`. All onsets are on a single line and space separated
```
cat /tmp/gtt_test/8906532558624107687/dot_left.1D
24.27:1.50 33.19:1.50 84.98:1.50 92.77:1.50 105.75:1.50 115.94:1.50 220.65:1.50 238.40:1.50 293.19:1.50 400.43:1.50 
```

## Grammar
```
<totaltime/number_trials> event_name=[duration]; 
<totaltime/number_trials> event_name=[duration]; another_event_that_follows_first=[duration2]
<totaltime/number_trials> event_name=[duration]( event_type1, event_type2 * mutation1, mutation2 )
<totaltime/number_trials> event_name=[duration](type1,type2){catch_ratio}; event2=[dur]
```

See [EventGrammer](genTaskTime/EventGrammar.py#L43) for the full EBNF-like specification (uses `tatSu`).


## Cookbook

Create `cue_A` and `cue_B` timing files with an onset (once each b/c total 2 trials) within a 20 second duration run.
```
<20/2> cue=[1.5](A, B)
```

Create a series of 3 events and repeat 10 times. The middle event `isi` has a duration pulled from a uniform distribution bound by 1.5 to 5, sorted randomly. (e.g. `3.06 1.89 2.67 4.22 4.61 1.50 2.28 3.44 5.00 3.83`)
```
<100/10> cue=[1.5]; isi=[1.5-5 u]; resp=[2]
```

Create 4 events `cue_Left_Near` to `cue_Right_Far` and repeat each 2 times (total of 8 trials)
```
<20/8> cue=[1.5](Left, Right * Near, Far)
```

Create stimulus onset timing files `start`  and `end`. `end` always follows 1.5s after `start`. The next `start` is at least 3s after the previous `end`
```
<20/1> start=[1.5]; end=[3]
```

Same as above but using catch trials such that a 1/3 of the time, trial only includes `start` and not `end`. 21 `start`s: 14 full `start`+`end` and 7 `start`-only.
```
<21/1> start=[1.5]{.333}; end=[3]
```

## Install
```bash
python3 -m pip install --user git+https://github.com/LabNeuroCogDevel/genTaskTime

# add pip python install scripts to path if not already there
which genTaskTime || { echo 'export PATH=$PATH:$HOME/.local/bin' >> ~/.bashrc && source ~/.bashrc }

# N.B.
# 1. OS X might have resource file ~/.zshrc instead of ~/.bashrc
# 2. Your python bin install PATH might be somewhere else. see:
#     python3 -m site --user-site
#     pip3 show genTaskTime --files
```

## TODO
As of 2024-02-01, there are still many features left to implement. See `git bug ls`


## Notes
This is very much not complete and very ugly

### Data structures and algorithms 
 1. The grammar is parsed into events `cue=[1](A,B); end`
 2. events are parsed into a tree where each event/stimulus is a node
   -  building the tree returns the last leaves of each unique branch
   - e.g `cue->a->end; cue->b->end;`
   - events without duration go into the parents names (later for output: `cue->a` will be file `cue_a`)
 4. the tree is fit for the number of trials we have (`fit_tree`)
   - nodes acquire the property `total_reps`
 5. we pull out "unique nodes" (by name only) by backtracking through the branches
   - calculate how many times the node will be seen (nrep)
   - distribute durations based on nrep
   - `cue`,`a`,`b`,`end`
 6. calculate the number and total duration of our events (+ min iti), add itis (with duration=stepdur) to consume remaining time
   - `n_rep_branch` is how many times we should run each branch (== `ntrials/n_perms`)
   - `n_perms` is number of branches with multipliers `1xA + 2xB == 3`
 7. shuffle for number of iterations specified (default 1000). and write out files in directories named after the random seed

