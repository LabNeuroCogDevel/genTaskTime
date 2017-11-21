# genTaskTime
* Parses a domain specific language describing a rapid event related fmri task
* Create stimulus onset files.

Designed for optimizing task timing with `3dDeconvolve -nodata` as an alternative to `optseq`, `RSFgen`, and `make_random_timing.py`

See
* https://afni.nimh.nih.gov/pub/dist/HOWTO/howto/ht03_stim/html/stim_background.html
* http://andysbrainblog.blogspot.com/2012/06/design-efficiency.html

## Install
```bash
pip3 install --user git+https://github.com/LabNeuroCogDevel/genTaskTime

# add pip python install scripts to path if not already there
which genTaskTime || { echo 'export PATH=$PATH:$HOME/.local/bin' >> ~/.bashrc && source ~/.bashrc }

# N.B. 
# - OS X might have resource file ~/.profile instead of ~/.bashrc
# - your install might be somewhere else. see:
#     python3 -m site --user-site
#     pip3 show genTaskTime --files
```
## Usage
```bash
genTaskTime -h
genTaskTime -i 1 -o stims '<20/4> cue=[1.5](A,B); dly=[3x 3, 1x 6]; end=[1.5]'
```

## Grammar
```
<totaltime/number_trials> event_name=[duration]; 
<totaltime/number_trials> event_name=[duration]; another_event_that_follows_first=[duration2]
<totaltime/number_trials> event_name=[duration]( event_type1, event_type2 * mutation1, mutation2 )
<totaltime/number_trials> event_name=[duration]( event_type1, event_type2 * mutation1, mutation2 )
```
## Cookbook

Create `cue_A` and `cue_B` timing files with an onset (once each b/c total 2 trials) within a 20 second duration run.
```
<20/2> cue=[1.5](A, B)
```

Create stimulus onset timing files `start`  and `end`. `end` always follows 1.5s after `start`. The next `start` is at least 3s after the previous `end`
```
<20/1> start=[1.5]; end=[3]
```

```
<60/4> cue=[1.5]( Left, Right x Near, Far )
```


TODO: uneven event subtypes, catch trials,  nested events

```
<20/1> start=[1.5](3x A, 2x B)
<20/1> start=[1.5]{.3}; end=[1.5]
<20/1> start=[1.5]; dly=(short=[1.5],long=[3]); end=[1.5]
```


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

