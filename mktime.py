#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import  tatsu, random, anytree, copy
import EventNode

# parse a string to design an experiment
# example:
#  <300/32> cue=[1.5]( Left, Right){0}; dly=[5-7e]; mgs=[1.5]
# annotation:
#  <total secons/number trials> event[duration range uniform, expidential ](types){catchratio}; next_ordered_event ...
# additionial notes:
#  * can nest events
#  * can specify permutations with '*'
#  * can specify duration range
#  * glm ignore '~' or '&'
#  * specify padding
#  * disconnect events with '|'
#  <300/32> cue=[1.5]( ( 3x Left, 2 x Right)*( 2 x Near, 3 x Far ~); dly=[.5,1.5,3] | mgs=( short=[.5],long=[1.5])

# two independent events
# <20/2> A=[1.5] | B=[1.5]
# written differently
# <20/2> event=[1.5](A, B)

# two dependent events (model cannot separate)
# <20/1> start=[1.5]; end=[1.5]
# now with catch trials
# <20/1> start=[1.5]{.3}; end=[1.5]

# with variable delay that we dont care to see timing files for
# <20/1> start=[1.5];dly=[1.5,3]~; end=[1.5]
# same thing but named
# <20/1> start=[1.5]; dly=(short=[1.5],long=[3]) ~; end=[1.5]
# and now with uneven distribution of short and long
# <20/1> start=[1.5]; dly=(3 x short=[1.5],2 x long=[3]) ~; end=[1.5]

# multipe cue types
# <60/4> cue=[1.5](Left,Right)
# but we want a near and far for each left and right
# <60/4> cue=[1.5]( (Left,Right) x (Near, Far) )
# we want near and far to be balenced for the presentation, but we dont care about separating it in the GLM
# <60/4> cue=[1.5]( (Left,Right) x (Near, Far ~) )

# <100/8> cue=[1.5]( (Left,Right) x (Near, Far ~) ) ; dly=[ 2,4,6 g] &; msgs=[1.5]



GRAMMAR = '''
# the input is settings and a list of events
start = settings:runsetting  allevents:eventlist $ ;

# information about constant constraints, run duration (seconds), number of trials and optional tr (seconds) and/or start+stop padding (seconds): 
# "<300/32>"
# "<300/32@2>"
# "<300/32@2 pad:12+20>"
# "<300/32 pad:12+20 iti:1.5-8>"
# "<300/32 iti:1.5-8>"
runsetting = '<'  rundur:num  '/' ntrial:num  ['@' tr:num ] [ 'pad:' startpad:num '+' stoppad:num  ] [ 'iti:' miniiti:num '-' maxiti:num ] '>'  ;

# sequential ';' events that build the tree
eventlist = 
          | event ';' ~ eventlist 
          | event '|' ~ eventlist 
          | event 
          ;

# full specification for an event: "cue=[1.5](L,R){0}"
event =  eventname:name  '='  [dur:duration] ['(' eventtypes:eventnamesx ')' ]  ['{' catchratio:num '}' ] [GLMignore:ignorechars] ;

# distributions: expodential, uniform, geometric
dist     = 
         | 'e' 
         | 'u'
         | 'g'
         ;

# [1.5] | [1.5-5] | [1.5-5 g] | [1.5,3,4.5] | [ 3 x 1.5, 2 x 3, 1 x 4.5 ]
duration = 
         | '['  dur:num  ']'
         | '['  min:num  '-' max:num [dist:dist]   ']'
         | '['  steps:numlist [dist:dist] ']'
         ;

# L,R * N,F  | (L,R) * (N,F) |  (L,R * N,F), A
eventnamesx = 
            | eventnames '*' ~ eventnamesx 
            | '(' eventnamesx ')'
            | '(' eventnames ')'
            | eventnames
            ;
# 2 x L, 3 x R ~&
eventnames = subevent:subevent [GLMignore:ignorechars];

# list of ways an event can be broken down: "2 x L, 3 x R"
subevent  = 
          | subeventinfo ',' ~ subeventinfo
          | subeventinfo
          ;

# maybe duration and an eventname: "2 x L"
subeventinfo  = [ freq:num 'x' ] subname:eventname;
          
# name or a full event: "L"| "[.4](N,F){.3}"
eventname = 
          | event
          | name 
          ;

# catch ratio
#catches = '{' catchratio:num  '}' ;

# ignore in timing (~), and ignore in tree (&)
ignorechars = 
            | '~'
            | '&'
            | '~&'
            ;

name = /\w+/ ;

numlist = 
        | numwithfreq ',' ~ numlist
        | numwithfreq
        ;

#e.g "2 x 3" | "3"
numwithfreq = [freq:num 'x' ] num:num;
 
# allow 5, 5.01, 0.4, .4
num = /\d+\.?\d*/ | /\.\d+/ ;

'''


def unlist_grammar(e):
    final=[]
    if type(e) == list: 
        for e2 in e:
           r=unlist_grammar(e2) 
           if r: final.extend( r )
    elif type(e) == str: return([])
    else:
      final.append(e)
    return(final)


def parse_tree(ast):
    events=unlist_grammar(ast['allevents'])
    # TODO: recursively expand subevents that are events in full
    return(events)

# subevent list is an elment of 'eventtypes'
# this builds a tree of them
# a=mkChild(EventNode.EventNode('root',dur=0),events[0]['eventtypes'])
def mkChild(parents,elist):
    subevent_list=copy.deepcopy(elist) #tmp copy because we're poping off it
    if type(parents) != list:
        print('I dont think parents are a list, tye are %s; %s'%(type(parents),parents))
        parents=[parents]

    children=parents
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
        
        for sube_info in seitem['subevent']:
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
#for t in range(1,ast['settings']['ntrial']):
    

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

    ast = tatsu.parse(GRAMMAR,expstr)
    print("have")
    pprint.pprint(ast,indent=2,width=20)
    events=parse_tree(ast)

    print("\n#### events")
    pprint.pprint(events,indent=2,width=20)
    print("\n#### calc tree")

    # build a tree from events
    last_leaves = events_to_tree(events)
    # find root
    root = last_leaves[0]
    while root.parent: root=root.parent

    ## print some more stuff
    print("\n#### tree")
    print(anytree.RenderTree(root))
    print("\n#### last leaves")
    for l in last_leaves:
        l.set_last()
    print(last_leaves) 
        
