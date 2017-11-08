#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import random, anytree, copy
import EventNode, EventGrammar


def parse_events(ast):
    if ast == None: return
    events=EventGrammar.unlist_grammar(ast['allevents'])
    # TODO: recursively expand subevents that are events in full
    return(events)

# subevent list is an elment of 'eventtypes'
# this builds a tree of them
# a=mkChild(EventNode.EventNode('root',dur=0),events[0]['eventtypes'])
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

def find_root(leaf):
    root = leaf
    while root.parent: root=root.parent
    return(root)
    
def write_trials(tree,settings):
   pass 



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

    ast = EventGrammar.parse(expstr)
    print("have")
    pprint.pprint(ast,indent=2,width=20)
    events=parse_events(ast)

    print("\n#### events")
    pprint.pprint(events,indent=2,width=20)
    print("\n#### calc tree")

    # build a tree from events
    last_leaves = events_to_tree(events)

    # set the terminal leaves, and count number of permutations
    nperms=0
    for l in last_leaves:
        l.set_last()
        nperms+=l.need_total

    # can we divide perms evenly into trials
    #settings
    
    # find root
    root=find_root(last_leaves[0])

    ## print some more stuff
    print("\n#### tree")
    print(anytree.RenderTree(root))
    print("\n#### last leaves")
    print(last_leaves) 
    print(nperms)
    write_trials(last_leaves,ast['settings'])
#for t in range(1,ast['settings']['ntrial']):
        
