import anytree, functools, math, random

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

# what we need to store for each event entering our event tree
class EventNode(anytree.NodeMixin):


    def __init__(self,name,dur,parent=None,nrep=1,writeout=True,extra=None):
        if(nrep == None): nrep=1
        self.parent=parent
        self.name=name
        self.dur = dur #parse_dur(dur)
        self.nrep=nrep
        self.writeout=writeout
        self.last=False
        #self.finalized = False
        self.extra=extra

    def __repr__(self):
        return("%s=%s (%dd|%dc)"%(self.name,self.nrep,len(self.path),len(self.children)) )

    # count up and make list of parents to traverse
    def set_last(self):
        self.last=True
        self.need_total=1
        p=self.parent
        self.parents=self.path
        #self.parents=[]
        while p:
            self.need_total*=int(p.nrep)
            #self.parents.append(p)
            p=p.parent
        return(self)

    # how many times is this node hit on it's children branches
    # N.B. still need to combine across branches
    def count_reps(node):
        totalreps=0
        children=node.children
        for c in children: totalreps+= c.count_reps()
        if node.nrep: 
            if len(children)==0: totalreps=int(node.nrep)
            else: totalreps*=int(node.nrep )
        #print("%d for all %d children of %s"%(totalreps,len(children),node))
        node.total_reps=totalreps
        return(totalreps)
        

    # TODO: handle distibutions
    def parse_dur(self,nperms):
        ## how many durs do we need?
        # -- should probably stop if do not have total_reps
        nsamples= getattr(self, "master_total_reps", \
                           getattr(self,"total_reps",\
                                    getattr(self,"nrep",0) ) )

        nsamples*=nperms

        if type(self.dur) in [float, int, type(None)]:
          dur=[self.dur] * nsamples
        elif self.dur['dur']:
          dur= [ float(self.dur['dur']) ] * int(nsamples)

        elif self.dur['min']:
          # todo distribute for others (just uniform now)
          a=float(self.dur['min'])
          b=float(self.dur['max'])
          intv=(b-a)/(nsamples-1)
          dur=[ a+i*intv for i in range(nsamples)  ]

        elif self.dur['steps']:
          steps=unlist_grammar( self.dur['steps'] )
          # todo, distribute
          dur = functools.reduce(lambda x,y: x+y, [  [float(x['num'])]*int(x['freq']) for x in steps] ) 
          ndur=len(dur)
          if ndur > nsamples:
              print("WARNING: %s: you have more durations (%d) than trials (%d). randomly truncating"%(self.name,ndur,nsamples))
          # fit what was given into what we have
          if ndur < nsamples:
              times_more = math.floor(nsamples/ndur)
              add_more   = ndur%nsamples
              origdur = dur
              dur = origdur + (origdur * (times_more-1))
              random.shuffle(origdur)
              if add_more > 0:
                 print("WARNING: %s: num durations given (%d) doesn't fit with number of events (%d) equally. randomly picking"%(self.name,ndur,nsamples))
                 dur= dur + origdur[0:add_more]
              else:
                 dur= dur + origdur
            
        random.shuffle(dur)
        dur=dur[0:nsamples]
        self.dur_dist = dur
        self.dur_dist_avg = functools.reduce(lambda x,y:x+y,dur)/len(dur)
        return(dur)
            
    def next_dur(self):
        if len(self.dur_dist)==0:
            print("WARNING: %s: no more durations to pick from. giving 0"%self.name)
            return(0)
        else:
            #if not self.picked: self.picked=0
            #self.picked+=1
            return(self.dur_dist.pop())



