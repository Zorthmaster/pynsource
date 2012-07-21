# blackboard

from graph import Graph
from layout_spring import GraphLayoutSpring

class LayoutBlackboard(object):
    def __init__(self, graph, umlwin):
        self.graph = graph
        self.umlwin = umlwin

    def stateofthespring(self):
        pass

    @property
    def kill_layout(self):
        if not self.outer_thread.CheckContinue():
            return True
        else:
            return False
    @kill_layout.setter
    def kill_layout(self, value):
      pass
          
    def LayoutMultipleChooseBest(self, numlayouts=3):
        """
        Blackboard
        Rerun layout several times, remembering each as a memento.  Then pick the best.

        Don't remember starting scale since we are going to change it anyway
        We could add mementos for a layout at the current scale - in which case
        
        Coordinate scaling runs 3.2 to max within ScaleUpMadly()
        Finish at the best scale as chosen by this algorithm
        """
        self.umlwin.AllToLayoutCoords()    # doesn't matter what scale the layout starts with
        layouter = GraphLayoutSpring(self.graph, gui=self)
        self.umlwin.snapshot_mgr.Clear()
        oriscale = self.umlwin.coordmapper.scale

        def ThinkAndAddSnapshot(res):
            num_line_line_crossings, num_node_node_overlaps, num_line_node_crossings = res

            # Calculate a layout score, lower the better?  Not used yet.
            score = 0
            bounds = self.graph.GetBounds()
            
            self.umlwin.snapshot_mgr.AddSnapshot(\
                layout_score=score,
                LL=num_line_line_crossings,
                NN=num_node_node_overlaps,
                LN=num_line_node_crossings,
                scale=self.umlwin.coordmapper.scale,
                bounds=bounds,
                bounds_area_simple=bounds[0]*bounds[1]/10000,
                graph_memento=self.graph.GetMementoOfPositions())

        # Generate several totally fresh layout variations
        for i in range(numlayouts):
            
            progress_val = i+1 # range is 1..n inclusive whereas for loop is 0..n-1 excluding n, so adjust by adding 1 for visual progress
            if not self.outer_thread.CheckContinue(statusmsg="Layout #%d of %d" % (progress_val, numlayouts), progress=progress_val):
                break
            
            # Do a layout
            self.outer_thread.Log("spring layout started")
            layouter.layout(keep_current_positions=False)
            self.outer_thread.Log("layout done")

            if not self.outer_thread.CheckContinue(logmsg="GetVitalStats"): break

            # Expand directly to the original scale, and calc vitals stats
            res = self.GetVitalStats(scale=oriscale, animate=False)
            ThinkAndAddSnapshot(res)
            
            if res[0] == 0 and res[2] <= 0:     # LL crossings solved and LN reasonable, so optimise and break - save time
                self.outer_thread.Log("LL crossings solved and LN reasonable, so optimise and break - save time")
                break

            if not self.outer_thread.CheckContinue(logmsg="ScaleUpMadly"): break

            # Expand progressively from small to large scale, and calc vitals stats
            # This can be SLOW
            res = self.ScaleUpMadly(strategy=":reduce post overlap removal LN crossings")
            ThinkAndAddSnapshot(res)
                
            if res[0] == 0 and res[2] <= 0:     # LL crossings solved and LN reasonable, so optimise and break - save time
                break
        
        #self.umlwin.snapshot_mgr.DumpSnapshots(label='Unsorted')
            
        """
        blackboard now sorting smarter because I have converted snapshots to
        dictionary format and thus can control which elements to sort by and
        whether to maximise or minimise any particular key in that snapshot
        dictionary.
        """
        def sortfunc(d):
            # this does the thinking!
          return (d['LL'], d['LN'], d['bounds_area_simple'], -d['scale'], d['NN_pre_OR'])        

        #self.umlwin.snapshot_mgr.Sort()
        self.umlwin.snapshot_mgr.Sort(sortfunc)  # this does the thinking!
        #self.umlwin.snapshot_mgr.Sort(lambda d: (d['scale'], -d['LL'], -d['LN']))   # pick biggest with most line crossings! - Ha ha          
        
        #self.umlwin.snapshot_mgr.DumpSnapshots('Sorted')
        
        self.umlwin.snapshot_mgr.Restore(0)


    def LayoutThenPickBestScale(self, strategy=None, scramble=False, animate_at_scale=None):
        """
        layout to untangle then scale up repeatedly till strategy met
        """
        self.umlwin.AllToLayoutCoords()  # doesn't matter what scale the layout starts with
        
        if animate_at_scale:
            self.umlwin.coordmapper.Recalibrate(scale=animate_at_scale) # Scale up just for watching purposes...
        
        layouter = GraphLayoutSpring(self.graph, gui=self.umlwin)  # TODO gui = controller - yuk
        layouter.layout(keep_current_positions=not scramble)

        self.ScaleUpMadly(strategy, animate=True)
        self.umlwin.stateofthenation()

    def Experiment1(self):
        """
        Disproves the potential theorem that there are no line crossings
        (in world coordinates) immediately after a layout.  There may be.
        
        Post layout, if there are LL crossings - this does not prove the graph
        is tangled. Scaling layout->world may have introduced these LL (or LL
        raw - ignoring nodes width/height) crossings.
        
        This experiment: Want to test if LL raw stays the same true for all
        scales. Turns out that it does not. And it may start at non zero too
        (depending on the graph and the scale at which you start this experiment
        at).

        We don't do any overlap removal here of course - cos this may
        introduce/remove LLs
        """
        MAX_SCALE = 1.4
        SCALE_STEP = 0.2
        SCALE_START = 3.2

        self.umlwin.AllToLayoutCoords()  # doesn't matter what scale the layout starts with
        layouter = GraphLayoutSpring(self.graph, gui=self.umlwin)  # TODO gui = controller - yuk
        layouter.layout(keep_current_positions=False)

        initial_num_line_line_crossings = len(self.graph.CountLineOverLineIntersections(ignore_nodes=True))  # node height/width ignored
        if initial_num_line_line_crossings > 0:
            print "Tangled", initial_num_line_line_crossings
        else:
            print "Not Tangled", initial_num_line_line_crossings
            
        self.umlwin.coordmapper.Recalibrate(scale=SCALE_START)
        for i in range(8):
            self.umlwin.coordmapper.Recalibrate(scale=self.umlwin.coordmapper.scale - SCALE_STEP)
            self.umlwin.AllToWorldCoords()
    
            self.umlwin.stateofthenation()
            
            # see how many INITIAL, PRE OVERLAP REMOVAL line-line crossings there are.
            num_line_line_crossings = len(self.graph.CountLineOverLineIntersections(ignore_nodes=True))
            print 'LL raw crossings', num_line_line_crossings
            if num_line_line_crossings <> initial_num_line_line_crossings:
                print "AXIOM FAILED !!!! ori LL raw %d --> post scale LL raw %d" % (initial_num_line_line_crossings, num_line_line_crossings)
        
        
            
    def LayoutLoopTillNoChange(self, maxtimes=10, scramble=True):
        """
        Relayout till nothing seems to move anymore in real world coordinates.
        Stay at same scale. DEFUNCT - integrated this algorithm into the lower
        level spring layout, operating there on layout coords - Spring Layout
        itself drops out early if nothing seems to be changing.
        """
        self.umlwin.AllToLayoutCoords()     # doesn't matter what scale the layout starts with
        memento1 = self.graph.GetMementoOfPositions()
        
        layouter = GraphLayoutSpring(self.graph, gui=self.umlwin)  # TODO gui = controller - yuk
        layouter.layout(keep_current_positions=not scramble)

        for i in range(1, maxtimes):
            self.umlwin.AllToWorldCoords()
            memento2 = self.graph.GetMementoOfPositions()
            
            if Graph.MementosEqual(memento1, memento2):
                print "Layout %d World Position Mementos Equal - break" % i
                break
            else:
                print "Layout %d World Positions in flux - keep trying" % i
                layouter.layout(keep_current_positions=True)

            layouter.layout(keep_current_positions=True)
            memento1 = memento2
        
        self.umlwin.AllToWorldCoords()
        self.umlwin.stage2() # does overlap removal and stateofthenation
        
    def ScaleUpMadly(self, strategy, animate=False):
        """
        No layout performed, assuming we are working off juicy post layout coords
        
        Leaves the scale at max level it got to - doesn't restore scale

        strategy = ":reduce pre overlap removal NN overlaps"
        strategy = ":reduce post overlap removal LN crossings"
        strategy = ":reduce post overlap removal LN and LL crossings":
        
        Operates repeatedly on the layout coords, so ignores anything you
        have done since, like world coord overlap removal.

        Running overlap removal at different scales can remove or introduce
        LL and LN crossings (but by definition, no NN overlaps ;-)
        
        After AllToWorldCoords() we are getting a picture of the pure layout
        result, scaled up
        
        Calling self.coordmapper.Recalibrate(scale) before AllToWorldCoords()
        simply expands or contracts the appearance of the world view nodes
        
        After AllToWorldCoords(), looking at pre NN overlap removal, layout
        result there will typically be
         -- LL some, act of translating to world introduces them.  More if the spring layout couldn't untangle itself.
         *- NN many, scaling up helps reduce (of course running overlap remover removes totally)
         -- LN many, scaling up helps reduce (running overlap remover may make it better or worse)
        
        After RemoveOverlaps()
         *- LL some
         -- NN == 0, unless algorithm failed
         *- LN some
         
         Note: * indicates the things we are looping and testing for. Mainly
         post overlap removal information - obviously since that is the 'look'
         that we are trying to make look nice, but we also look at pre overlap
         removal NN overlaps, which gives us some indication of how crowded we
         are and thus how far away from pure spring layout our graph will look
         after an overlap removal. We want to stay looking like the spring
         layout and not shove nodes all over the place. Possibly another way of
         guaging how much overlap removal has corrupted our look, would be to
         calc how much nodes have moved out of position after an overlap removal
         run - don't know.
        """
        ACCEPTABLE_NODE_NODE_PRE_REMOVAL = 3
        MAX_SCALE = 1.4
        SCALE_STEP = 0.2
        SCALE_START = 3.2
        
        self.umlwin.coordmapper.Recalibrate(scale=SCALE_START)
        for i in range(15):
            
            res = self.GetVitalStats(scale=self.umlwin.coordmapper.scale - SCALE_STEP, animate=animate)
            
            num_line_line_crossings, num_node_node_overlaps, num_line_node_crossings = res

            if not self.outer_thread.CheckContinue(logmsg="Scale test %d"%i):
                break
            
            if strategy == ":reduce pre overlap removal NN overlaps":
                if num_node_node_overlaps <= ACCEPTABLE_NODE_NODE_PRE_REMOVAL:
                    #print "Mad: Aborting expansion since num NN overlaps <= %d" % ACCEPTABLE_NODE_NODE_PRE_REMOVAL
                    break
            elif strategy == ":reduce post overlap removal LN crossings":
                if num_line_node_crossings == 0:
                    #print "Mad: Finished expansion since LN crossings == 0 :-)"
                    break
            elif strategy == ":reduce post overlap removal LN and LL crossings":
                if num_line_node_crossings == 0 and num_line_node_crossings == 0:
                    #print "Mad: Finished expansion since LN and LL crossings == 0 :-)"
                    break
            else:
                assert False, "Mad: unknown strategy"
    
            if self.umlwin.coordmapper.scale < MAX_SCALE:
                #print "Mad: Aborting expansion - gone too far.", self.umlwin.coordmapper.scale
                break
    
        if animate:
            self.umlwin.stateofthenation()
        
        return num_line_line_crossings, num_node_node_overlaps, num_line_node_crossings

    def GetVitalStats(self, scale, animate=False):
        """
        No layout performed, assuming we are working off juicy post layout coords
        Expand directly to the 'scale', and calc vitals stats
        Same as ScaleUpMadly except only one scale made
        NN Overlap Removal performed.
        """
        
        self.umlwin.coordmapper.Recalibrate(scale=scale)
        self.umlwin.AllToWorldCoords()

        if animate:
            self.umlwin.stateofthenation()
        
        """Pre Overlap Removal"""
        
        # The only thing of interest here pre node overlap removal are the
        # initial NN as this gives us some indication of how crowded we are and
        # how hard the node overlap removal algorithm has to work. If too much
        # overlap removal is done it detracts from the nice layout that was
        # worked out

        # count NN (pre overlap removal)
        num_node_node_overlaps = self.umlwin.overlap_remover.CountOverlaps()

        """Remove Node Overlaps"""
        self.umlwin.overlap_remover.RemoveOverlaps(watch_removals=False)

        """Post Overlap Removal"""

        # How many LN reduced (or perhaps increased) after expansion & post removing NN overlaps
        num_line_node_crossings = self.graph.CountLineOverNodeCrossings()['ALL']/2
        
        # How many LL reduced (or perhaps increased) after expansion & post removing NN overlaps
        num_line_line_crossings = len(self.graph.CountLineOverLineIntersections())

        #print "GetVitalStats: At scale %.1f NN_pre %d LN %d LL %d" % (self.umlwin.coordmapper.scale, num_node_node_overlaps, num_line_node_crossings, num_line_line_crossings)
    
        return num_line_line_crossings, num_node_node_overlaps, num_line_node_crossings

        