# Layout tests

import networkx as NX
import networkx.drawing.layout as lay
#import networkx.paths as P
import networkx.algorithms.dag as P
import random

G=NX.Graph()
G.add_node("hello",size=10)
G.add_node("there",size=10)
G.add_node("again",size=10)
G.add_node("please",weight=0.4,UTM=('13S',382871,3972649))
G.add_node("aa")
G.add_edge("hello", "there",weight=0.6)
G.add_edge("there", "again",weight=0.4)
G.add_edge("there", "please",weight=0.2)
G.add_edge("hello", "aa",weight=0.2)
print G.nodes()
print G.edges()
#print G.info()

print dir(lay)
res01 = lay.circular_layout(G)
print "res01", res01
print
res02 = lay.spring_layout(G)
print "res02", res02
print
print "sorted! "

#P.topological_sort(G)
#P.topological_sort_recursive(G)

nx = NX

"""
 ANDY NOTE: requires graphviz which doesn't come easy under windows
 
# Added from example http://networkx.lanl.gov/examples/drawing/atlas.html
print("graph has %d nodes with %d edges"\
	  %(nx.number_of_nodes(G),nx.number_of_edges(G)))
print(nx.number_connected_components(G),"connected components")

try:
	from networkx import graphviz_layout
except ImportError:
	raise ImportError("This example needs Graphviz and either PyGraphviz or Pydot")

import matplotlib.pyplot as plt
plt.figure(1,figsize=(8,8))
# layout graphs with positions using graphviz neato
pos=nx.graphviz_layout(G,prog="neato")
# color nodes the same in each connected subgraph
C=nx.connected_component_subgraphs(G)
for g in C:
	c=[random.random()]*nx.number_of_nodes(g) # random color...
	nx.draw(g,
		 pos,
		 node_size=40,
		 node_color=c,
		 vmin=0.0,
		 vmax=1.0,
		 with_labels=False
		 )
plt.savefig("andy.png",dpi=75)
"""


# From example weighted_graph.py
try:
    import matplotlib.pyplot as plt
except:
    raise
elarge=[(u,v) for (u,v,d) in G.edges(data=True) if d['weight'] >0.5]
esmall=[(u,v) for (u,v,d) in G.edges(data=True) if d['weight'] <=0.5]
pos=nx.spring_layout(G) # positions for all nodes
# nodes
#nx.draw_networkx_nodes(G,pos,node_size=700)
#nx.draw_networkx_nodes(G,pos,node_size=7000)
nx.draw_networkx_nodes(G,pos,node_size=2000)
# edges
nx.draw_networkx_edges(G,pos,edgelist=elarge,
                    width=6)
nx.draw_networkx_edges(G,pos,edgelist=esmall,
                    width=6,alpha=0.5,edge_color='b',style='dashed')
# labels
nx.draw_networkx_labels(G,pos,font_size=20,font_family='sans-serif')
plt.axis('off')
plt.savefig("weighted_graph.png") # save as png
plt.show() # display




#--------------------------


def calcMinMax(res):
    maxx = maxy = minx = miny = 0
    for k in res.keys():
        arr = res[k]
        x, y = arr[0], arr[1]
        if x > maxx:
            maxx = x
        if x < minx:
            minx = x
        if y > maxy:
            maxy = y
        if y < miny:
            miny = y
    print "x ranges from " + str(minx) + " to " + str(maxx)
    print "y ranges from " + str(miny) + " to " + str(maxy)
    
"""
G2=NX.Graph()
lastnode = None
for n in range(1,450):
    node1 = "N"+str(random.randint(1,5000))
    node2 = "T"+str(random.randint(1,5000))
    G2.add_node(node1)
    G2.add_node(node2)
    G2.add_edge(node1, node2)
    if lastnode:
        G2.add_edge(lastnode, node1)
    lastnode = node2
res1 = lay.circular_layout(G2)
print res1
print
res2 = lay.spring_layout(G2)
print res2
print

calcMinMax(res1)
print
calcMinMax(res2)

"""


def CollectY(res):
    ys = [ v[1] for v in res.values() ]

    # remove duplicates
    
    #from sets import Set
    #ys = list(Set(ys))    python 2.6 now has built in sets 
    ys = list(set(ys))

    ys.sort()
    ys.reverse()
    return ys
print CollectY(res02)

def CollectXsAtY(res, y):
    xs = [ v[0] for v in res.values() if v[1] == y ]
    xs.sort()
    return xs

def FindName(res, x, y):
    for (k,v) in res.iteritems():
        if v[0] == x and v[1] == y:
            return k
    return None

def InjectNodeNames(res, xs, y):
    xs2 = []
    for x in xs:
        node = FindName(res, x, y)
        xs2.append( (node, x) )
    return xs2
    
def SortRes(res):
    rez = []
    ys = CollectY(res)
    for y in ys:
        xs = CollectXsAtY(res, y)
        xs2 = InjectNodeNames(res, xs, y)
        rez.append( (y, xs2) )
    return rez

def ReMap(res, sizes):
    SPACING = 50
    nextx = 200
    nexty = 200
    newres = {}
    
    print "ReMap"
    myres = SortRes(res)
    for (y, xs) in myres:
        for (node, x) in xs:
            print node, x, y, "   => ",
            print nextx, nexty
            newres[node] = (nextx, nexty)
            nextx += sizes[node][0] + SPACING

        nexty += sizes[node][1] + SPACING # nexty should be set to max of largest y encountered in that row.
        nextx = 200
        # Or even make next y a bit smarter and alter it dynamically every time, knowing wheat was in the previous row
    
    return newres


print
print "SortRes02"
print SortRes(res02)
print


res55 = { 'A' : (0.0, 0.0),
          'B' : (0.1, 0.0),
          'C' : (-0.1, -0.15) }
sizes55 = { 'A' : (50, 50),
            'B' : (100, 100),
            'C' : (10, 10) }

import pprint
print "SortRes55"
pprint.pprint( SortRes(res55) )
print


coords55 = ReMap(res55, sizes55)
print
print coords55

sizes55 = {'wxPrintout': (106.0, 36.0), 'MyPrintout': (152.0, 227.0)}
res55 = {'wxPrintout': [ 0.71233445,  3.11540857], 'MyPrintout': [-0.58540195, -2.45158964]}
coords55 = ReMap(res55, sizes55)
print
print coords55

