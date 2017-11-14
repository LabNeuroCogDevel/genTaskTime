#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import random, anytree, copy, pprint, itertools, functools
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
def mkChild(parents,elist):
    subevent_list=EventGrammar.unlist_grammar(copy.deepcopy(elist)) #tmp copy because we're poping off it
    if type(parents) != list:
        print('I dont think parents are a list, tye are %s; %s'%(type(parents),parents))
        parents=[parents]

    children=parents
    if type(subevent_list) != list: subevent_list = [ subevent_list ]
    if len(subevent_list)>0:
        children=[]
        print("popping from: %s"%subevent_list)
        seitem=subevent_list.pop(0)
        # skip '*'
        if type(seitem) == str:
            print('skipping *')
            seitem=subevent_list.pop(0)

        print("have: %s"%seitem)
        
        # if we only have 1 subevent, still need to treat it like a list
        # should check for 
        if type(seitem['subevent']) != list:
            print('item not a list, coercing: %s'%seitem['subevent'])
            seitem['subevent']=[seitem['subevent']]
        
        these_subevets = EventGrammar.unlist_grammar(seitem['subevent'])
        for sube_info in these_subevets:
           if type(sube_info) == str:
               print("\tskipping '")
               continue # skip ','

           print("\tsube_info: %s"%sube_info)

           name=sube_info['subname']
           freq=sube_info['freq']
           for p in parents:
              print("\t\tadding child %s to parent %s"%(name,p))
              children.append( EventNode.EventNode(name,parent=p,nrep=freq,dur=0) )

        # continue down the line
        #TODO: fix bad hack; break out of list
        if len(subevent_list) == 1 and str(subevent_list[0] == list):
            print("\tTODO: do not break recursive list")
            subevent_list=subevent_list[0]

        print("\t\trecurse DOWN: %s"%subevent_list)
        children=mkChild(children,subevent_list)

    return(children)
    

# for a ast list of events, build a tree
def events_to_tree(events):
    last_leaves=None
    for event in events:
        if last_leaves == None:
            last_leaves = [ EventNode.EventNode(event['eventname'],dur=event['dur'],parent=None) ]
        else:
            last_leaves = [ EventNode.EventNode(event['eventname'],dur=event['dur'],parent=r) for r in last_leaves ]
                
        if event['eventtypes']:
            print('making children for %s'%last_leaves)
            pprint.pprint(event['eventtypes'])
            last_leaves = mkChild(last_leaves,event['eventtypes'])

    return(last_leaves)

# set reference for nodes that should be doing their own calculation
def free_nodes(root):
    pass

# dont need this
def find_terminal_leaves(node):
   ends=[]
   if len(node.children)==0 or node.children == None:
       print(node)
       return([node])
   for c in node.children:
      ends += find_terminal_leaves(c) 
   return(ends)


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
    
def write_trials(last_leaves,settings):
    # settings
    ntrials=int( settings['ntrial'] )

    # how many times do we go down the tree?
    nperms=0
    for l in last_leaves:
        l.set_last()
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

    # todo: add min iti from settings
    min_iti=1.5

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

                
    #[ [{'fname': '', 'dur': '' }, ...], ... ]
    all_durs = [ o['dur'] for x in triallist for o in x ] 
    total_dur=functools.reduce(lambda x,y:x+y, all_durs)
    # TODO: add min ITI

    rundur=float(settings['rundur'])
    if total_dur > rundur:
        print("ERROR: total event time (%.2f) is greater than run time (%.2f)!"%(total_dur,rundur))
        rundur = total_dur # TODO, maybe die instead?
        

    # TODO:
    # - use specified granularity 
    # - remove start/end times from count
    granularity=.01
    n_iti = int( (rundur - total_dur ) / granularity )

    triallist += [ [ {'fname': None, 'dur': granularity} ] ] * n_iti

    random.shuffle(triallist)
    total_time=0
    for tt in triallist:
        for  t in tt:
            if t['fname']:
                outname="_".join(t['fname'])
                print('%s: %f (%f)'%(outname,total_time,t['dur']))
            total_time+=t['dur']

    print('stop')
           
    

    # calc final dur of leaves

    ## sequence: [{name:,dur:, treepath: }] of iti/rest + events (with min iti added)
    # todo tr lock by setting gran to tr and rounding durations
    # can we divide perms evenly into trials

    # for each last_leaf, 
    #  for each path
    #    use node to lookup masternodes, call get_dur
    #    build sequence, add min iti to seq dur
    #    track total time 
 
    # fill the renaming time with {iti: , dur: gran}
    
    # dont do it this way
    #for t in range(1,ast['settings']['ntrial']):



if __name__ == '__main__':
    import pprint,sys
    if len(sys.argv)>1: 
        expstr=sys.argv[1]
    else:
        #ast = tatsu.parse(GRAMMAR,'<300/32> cue=[1.5]( Left, Right){0}; dly=[5-7e]; mgs=[1.5]')
        #ast = tatsu.parse(GRAMMAR,'<300/32> cue=[1.5]( 2 x Left, 1 x Right){0}; dly=[5-7e]; mgs=[1.5]')
        #expstr='<300/32> cue=[1.5]( 3 x LeftCue=[.5](Short, Long) , Right){0}; dly=[5-7e]; mgs=[1.5]'
        #expstr='<300/32> vgs=[1.5]( (Left,Right) * (Near, Far &) ); dly=[2,4,6g]; mgs=[1.5]'
        expstr='<1/1>vgs=[1.5]( Left,Right * Near,Far ~); dly=[4x 2,3x 4,2x 6];mgs=[1.5]'

    astobj = EventGrammar.parse(expstr)
    print("have")
    pprint.pprint(astobj,indent=2,width=20)
    events=parse_events(astobj)

    pprint.pprint(events,indent=2,width=20)
    print("\n#### calc tree")

    # build a tree from events
    last_leaves = events_to_tree(events)
    # kludgyhack: event_to_tree does some weird things. rather than fix it, lets work around it
    root = last_leaves[0].root
    #find_terminal_leaves = 

    # set the terminal leaves, and count number of permutations



    ## print some more stuff
    print("\n#### tree")
    print(anytree.RenderTree(root))
    print("\n#### last leaves")
    print(last_leaves) 
    write_trials(last_leaves,astobj['settings'])

        
