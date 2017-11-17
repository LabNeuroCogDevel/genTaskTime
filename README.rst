genTaskTime
===========

-  Parses a domain specific language describing an event related fmri
   task
-  Create stimulus onset files.

Designed for optimizing task timing with ``3dDeconvolve -nodata`` as an
alternative to ``optseq`` and ``make_random_timing.py``

Usage
-----

::

    ./genTaskTime -h
    ./genTaskTime -i 1 -o stims '<20/4> cue=[1.5](A,B); dly=[3x 3, 1x 6]; end=[1.5]'

Grammar
-------

::

    <totaltime/number_trials> event_name=[duration]; 
    <totaltime/number_trials> event_name=[duration]; another_event_that_follows_first=[duration2]
    <totaltime/number_trials> event_name=[duration]( event_type1, event_type2 * mutation1, mutation2 )
    <totaltime/number_trials> event_name=[duration]( event_type1, event_type2 * mutation1, mutation2 )

Cookbook
--------

Create ``cue_A`` and ``cue_B`` timing files with an onset (once each b/c
total 2 trials) within a 20 second duration run.

::

    <20/2> cue=[1.5](A, B)

Create stimulus onset timing files ``start`` and ``end``. ``end`` always
follows 1.5s after ``start``. The next ``start`` is at least 3s after
the previous ``end``

::

    <20/1> start=[1.5]; end=[3]

::

    <60/4> cue=[1.5]( Left, Right x Near, Far )

TODO: uneven event subtypes, catch trials, nested events

::

    <20/1> start=[1.5](3x A, 2x B)
    <20/1> start=[1.5]{.3}; end=[1.5]
    <20/1> start=[1.5]; dly=(short=[1.5],long=[3]); end=[1.5]

Notes
-----

This is very much not complete and very ugly
