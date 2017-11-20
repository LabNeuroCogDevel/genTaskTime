#!/usr/bin/env python3
from .EventGrammar import *
from .EventNode import *
from .generate import *
import os
import sys
import argparse


def main(*args):
    getargs = argparse.ArgumentParser(description="Make timing files by building an event tree from a DSL description of task timing.")
    getargs.add_argument('timing_description',
                         type=str, help='quoted string' +
                         'like: "<30/5> first=[2]; next=[1](2x Left, Right)"',
                         nargs=1)
    getargs.add_argument('-i', dest='n_iterations', type=int,
                         help="Number of iterations",
                         nargs=1, default=[1000])
    getargs.add_argument('-o', dest='outputdir', type=str, default=['stims'],
                         help="output directory (default='stims/')",
                         nargs=1)
    getargs.add_argument('-n', '--dry', dest='show_only', action='store_const',
                         const=True, default=False,
                         help="Dry run. Show parsing of DSL only. Don't create files")
    getargs.add_argument('-v', dest='verbosity', default=[1],
                         nargs=1, type=int,
                         help="Verbosity. 0=print nothing. 99=everything. (default=1)")

    if len(args) > 0:
        args = getargs.parse_args(args)
    else:
        args = getargs.parse_args()

    expstr = args.timing_description[0]

    if args.show_only or args.verbosity[0] > 1:
        verbose_info(expstr, args.verbosity[0])

    if not args.show_only:
        outdir = args.outputdir[0]
        # deal with where we are saving files
        if os.path.isfile(outdir):
            print("outdir ('%s') is already a file. Thats not good!" % outdir)
            sys.exit(1)
        if not os.path.isdir(outdir):
            os.mkdir(outdir)
        os.chdir(outdir)

        # run
        (triallist, settings) = str_to_triallist(expstr)
        write_trials(triallist, settings,
                     args.n_iterations[0], args.verbosity[0])


if __name__ == '__main__':
    main()

