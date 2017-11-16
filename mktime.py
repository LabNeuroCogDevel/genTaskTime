#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import random, anytree, copy, pprint, itertools, functools, pprint, sys 
import EventNode, EventGrammar


def parse_events(astobj):
    if astobj == None: return
    events=EventGrammar.unlist_grammar(astobj['allevents'])
    # TODO: recursively expand subevents that are events in full
    return(events)

# subevent list is an elment of 'eventtypes'
# this builds a tree of them
# a=mkChild(EventNode.EventNode('root',dur=0),events[0]['eventtypes'])
    print("\n#### events")
def mkChild(parents,elist,verb=1):
    subevent_list=EventGrammar.unlist_grammar(copy.deepcopy(elist)) #tmp copy because we're poping off it
    if type(parents) != list:
        print('I dont think parents are a list, tye are %s; %s'%(type(parents),parents))
        parents=[parents]

    children=parents
    if type(subevent_list) != list: subevent_list = [ subevent_list ]
    if len(subevent_list)>0:
        children=[]
        if verb > 1: print("popping from: %s"%subevent_list)
        seitem=subevent_list.pop(0)
        # skip '*'
        if type(seitem) == str:
            print('skipping *')
            seitem=subevent_list.pop(0)

        if verb > 1: print("have: %s"%seitem)
        
        # if we only have 1 subevent, still need to treat it like a list
        # should check for 
        if type(seitem['subevent']) != list:
            if verb > 1: print('item not a list, coercing: %s'%seitem['subevent'])
            seitem['subevent']=[seitem['subevent']]
        
        these_subevets = EventGrammar.unlist_grammar(seitem['subevent'])
        for sube_info in these_subevets:
           if type(sube_info) == str:
               if verb > 1: print("\tskipping '")
               continue # skip ','

           if verb > 1: print("\tsube_info: %s"%sube_info)

           name=sube_info['subname']
           freq=sube_info['freq']
           if freq: freq=int(freq)
           for p in parents:
              if verb > 1: print("\t\tadding child %s to parent %s"%(name,p))
              children.append( EventNode.EventNode(name,parent=p,nrep=freq,dur=0) )

        # continue down the line
        #TODO: fix bad hack; break out of list
        if len(subevent_list) == 1 and str(subevent_list[0] == list):
            print("\tTODO: do not break recursive list")
            subevent_list=subevent_list[0]

        if verb > 1: print("\t\trecurse DOWN: %s"%subevent_list)
        children=mkChild(children,subevent_list,verb)

    return(children)
    

# for a ast list of events, build a tree
def events_to_tree(events,verb=1):
    last_leaves=None
    for event in events:
        if last_leaves == None:
            last_leaves = [ EventNode.EventNode(event['eventname'],dur=event['dur'],parent=None) ]
        else:
            last_leaves = [ EventNode.EventNode(event['eventname'],dur=event['dur'],parent=r) for r in last_leaves ]
                
        if event['eventtypes']:
            if verb > 1:
                print('making children for %s'%last_leaves)
                pprint.pprint(event['eventtypes'])
            last_leaves = mkChild(last_leaves,event['eventtypes'],verb)

    return(last_leaves)




## create a master node used calculate delays
# each node in the tree with the same name points to the same master node
def create_master_refs(root):
    # root requires no calculation -- there is only one (right!?)
    uniquenode = lambda n: '%s'%n.name # '%s %s'%(n.name,n.dur)
    masternodes = {}

    for n in (root, *root.descendants):
        nname = uniquenode(n)
        if not masternodes.get(nname):
          n.master_total_reps = 0
          masternodes[nname] = n
        n.master_node=masternodes.get(nname)
        n.master_node.master_total_reps+=n.total_reps
    return([ x for x in masternodes.values() ] )


def event_tree_to_list(last_leaves, n_rep_branches, min_iti):
    # tree to list
    triallist=[]
    for l in last_leaves:
        branch = l.parents
        fname=[]
        for i in range(l.nrep):
            thistrial=[]
            for n in branch:
                n=n.master_node
                if n.dur != 0:
                    if fname:
                        thistrial.append( {'fname':fname, 'dur': dur} )
                    fname=[]
                    dur=0
                fname.append(n.name)
                dur+=n.next_dur()
            if fname: thistrial.append( {'fname':fname, 'dur': dur} )
            thistrial.append( {'fname': None, 'dur': min_iti} )

            for i in range(l.total_reps * n_rep_branches): triallist.append(thistrial)
    return(triallist) 


def write_list_to_file(triallist,start_at_time,seed=None):
    # shuffle up the events, optionally with a provided seed
    if seed:
        random.Random(seed)
    random.shuffle(triallist)
    # initialize start time and dict to hold output file handles
    total_time=start_at_time
    write_to={}
    for tt in triallist:
        for  t in tt:
            if t['fname']:
                #iter_id = "%05d"%iter_i
                iter_id = "%018d"%seed
                fname="_".join( t['fname'])
                outname=os.path.join(iter_id,fname)
                if not write_to.get(outname):
                    #print('%s'%outname)
                    outdir=os.path.dirname(outname)
                    if not os.path.isdir( outdir ): os.mkdir(outdir)
                    write_to[outname] = open(outname,'w')
                #print('%s: %f (%f)'%(outname,total_time,t['dur']))
                write_to[outname].write("%.02f "%total_time)
            total_time+=t['dur']

    for v in write_to.values():
        v.write('\n')
        v.close()

# settings stores 'rundur' and maybe granularity and finish_with_left
# TODO: get finish_with_left and granularity from settings
def add_itis(triallist,settings,finish_with_left=0,start_at_time=0):
    #[ [{'fname': '', 'dur': '' }, ...], ... ]
    all_durs = [ o['dur'] for x in triallist for o in x ] 
    total_dur=functools.reduce(lambda x,y:x+y, all_durs)

    rundur=float(settings['rundur'])
    rundur=rundur - finish_with_left
    if total_dur  > (rundur - start_at_time):
        print("ERROR: total event time (%.2f) is greater than run time (%.2f)!"%(total_dur,rundur))
        sys.exit(1)
        #TODO: print info about finish_with_left + start_at_time and min_iti n_rep_branches
        rundur = total_dur # TODO, maybe die instead?
        

    ## calculate number of ITIs we need. make them and add to triallist
    # TODO:
    # - use specified granularity 
    granularity=.01
    n_iti = int( (rundur - total_dur ) / granularity )

    triallist += [ [ {'fname': None, 'dur': granularity} ] ] * n_iti
    return(triallist)

# update tree for the number of trials we have
# updates the nodes of tree
def fit_tree(last_leaves,ntrials):
    # how many times do we go down the tree?
    nperms=0
    for l in last_leaves:
        l.set_last()
        #print("leaf '%s' seen %d times"%(l,l.need_total))
        nperms+=l.need_total

    n_rep_branches=ntrials/nperms

    # check sanity
    if n_rep_branches < 1:
        print('WARNING: your expreiment has too few trials (%d) to accomidate all branches(%d)'%(ntrials,nperms))
        n_rep_branches=1
    elif n_rep_branches != int(n_rep_branches):
        print('WARNING: your expreiment will not be balanced\n\t' +
              '%d trials / %d event branches is not a whole number (%f);'%(ntrials,nperms,n_rep_branches, ))
              #'maybe try %f trials '%(ntrials,nperms,n_rep_branches, (int(n_rep_branches)*nperms) ))

    n_rep_branches=int(n_rep_branches)

    # each node should have the nrep sum of its children (x nreps of that node)
    # node.totalreps
    root=last_leaves[0].root

    # get how many time each node in the tree will be seen
    root.count_reps() 
    # different branches have nodes with the same name
    # link them all to one node so we can draw duration times from that one
    unique_nodes = create_master_refs(root)

    # set up delay distributions
    for u in unique_nodes:
        u.parse_dur(n_rep_branches)

    return( (n_rep_branches, nperms) )

def write_trials(last_leaves,settings,n_iterations=1000,verb=1):

    # settings
    ntrials=int( settings['ntrial'] )

    # update tree for the number of trials we have
    # updates the nodes of tree
    (n_rep_branches, nperms) = fit_tree(last_leaves,ntrials)

    # todo: min_iti, start_at_time from settings
    min_iti=1.5
    start_at_time=0

    triallist=event_tree_to_list(last_leaves, n_rep_branches, min_iti)
    triallist=add_itis(triallist,settings)
                

    print("making %d version of %d reps of (%d final branches, seen a total of %d times)"%
                     (n_iterations, n_rep_branches ,len(last_leaves),nperms ))

    # set file name to seed
    # int(math.log10(sys.maxsize)) -- 18 digits
    
    for iter_i in range(0,n_iterations):
        # set a seed
        seed = random.randrange(sys.maxsize)
        # start timer after or initial rest period
        write_list_to_file(triallist,start_at_time,seed)

        # TODO: run 3dDeconvolve

        # print a message very 100 trials
        if iter_i%100==0 and verb > 0:
            print('finished %d'%iter_i)
           


def string_to_many_files(expstr,n_iterations,n_terations=1000,verb=0):
    astobj = EventGrammar.parse(expstr)
    events = parse_events(astobj)
    # build a tree from events
    last_leaves = events_to_tree(events,verb)
    # write out files
    write_trials(last_leaves,astobj['settings'],n_iterations,verb)

def verbose_info(expstr,verb=99):

    print("### given")
    astobj = EventGrammar.parse(expstr)
    pprint.pprint(astobj,indent=2,width=20)

    print("\n### parsed events")
    events=parse_events(astobj)
    pprint.pprint(events,indent=2,width=20)

    print('\n# Building Tree')
    # build a tree from events
    last_leaves = events_to_tree(events)
    root = last_leaves[0].root

    print("\n### tree")
    print(anytree.RenderTree(root))

    print("\n### last leaves")
    print(last_leaves) 
    
if __name__ == '__main__':
    import os, sys, argparse
    getargs = argparse.ArgumentParser(description="Make timing files by building an event tree from a DSL description of task timing.")
    getargs.add_argument('timing_description',
                         type=str, help='quoted string' +
                         '\nlike: "<30/5> first=[2]; next=[1](2x Left, Right)"',nargs=1)
    getargs.add_argument('-i', dest='n_iterations', type=int,
                         help="Number of iterations",
                         nargs=1,default=1000)
    getargs.add_argument('-o', dest='outputdir', type=str, default='stims',
                         help="output directory (default='stims/')",
                         nargs=1)
    getargs.add_argument('-n','--dry', dest='show_only', action='store_const',
                         const=True, default=False,
                         help="Dry run. Show parsing of DSL only. Don't create files")
    getargs.add_argument('-v',dest='verbosity', default=[1], nargs=1, type=int,
                         help="Verbosity. 0=print nothing. 99=everything. (default=1)")

    args = getargs.parse_args()
    expstr = args.timing_description[0]
    #expstr='<1/1>vgs=[1.5]( Left,Right * Near,Far ~); dly=[4x 2,3x 4,2x 6];mgs=[1.5]'
    if args.show_only or args.verbosity[0] > 1:
       verbose_info(expstr,args.verbosity[0])

    if not args.show_only:
        # deal with where we are saving files
        if os.path.isfile(args.outputdir):
           print("outdir ('%s') is already a file. Thats not good!"%args.outputdir)
           sys.exit(1)
        if not os.path.isdir(args.outputdir):
            os.mkdir(args.outputdir)
        os.chdir(args.outputdir)

        # run
        string_to_many_files(expstr, args.n_iterations[0],args.verbosity[0])

        
