import anytree, functools

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

    # TODO: handle distibutions
    def parse_dur(self,dur):
        if type(dur) in [float, int, type(None)]:
          self.dur=dur
          return
        elif dur['dur']:
          self.dur=dur['dur']
        elif dur['min']:
          self.dur=[ float(dur['min']),float(dur['max']) ]
          # todo distribute
        elif dur['steps']:
          steps=unlist_grammar( dur['steps'] )
          # todo, distribute
          self.dur= functools.reduce(lambda x,y: x+y, [  [float(x['num'])]*int(x['freq']) for x in steps] ) 
        

    def __init__(self,name,dur,parent=None,nrep=1,writeout=True,isfree=False,extra=None):
        if(nrep == None): nrep=1
        self.parent=parent
        self.name=name
        self.parse_dur(dur)
        self.nrep=nrep
        self.writeout=writeout
        self.isfree=isfree
        self.last=False
        self.extra=extra

    def __repr__(self):
        return("%s=[%s] x %s (%dd %dc)"%(self.name,self.dur,self.nrep,len(self.path),len(self.children)) )

    # count up and make list of parents to traverse
    def set_last(self):
        self.last=True
        self.need_total=1
        p=self.parent
        self.parents=self.path
        #self.parents=[]
        while p:
            self.need_total*=p.nrep
            #self.parents.append(p)
            p=p.parent
        return(self)

    def set_free(self,ntrials):
        self.isfree=isfree
        self.nrep=0 # don't count in tree
        self.need_total=ntrials
        # TODO: better dur handling
        self.origdur= [self.dur] * self.need_total
        random.shuffle(self.origdur)
        return(self)

            
    def next_dur(self):
        if not self.isfree:
            return(self.dur)
        else:
            return(self.orgdur.pop)
