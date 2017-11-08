import tatsu 
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
          | subeventinfo ',' ~ subevent
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

def parse(timingdesc):
    return(tatsu.parse(GRAMMAR,timingdesc))
