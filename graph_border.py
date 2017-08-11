class GraphBorder():
    r"""
    Object represent a induced subtree of a graph and the surrounding of this subtree.
    The data structure also catch up a bit of the evolution of the tree over time.

    ATTRIBUTES:
        vertex_status: Dictionnary that store the state of each vertices with options.
        The status of a vertex v is of the form:
            - ("s",d) if v is in the subtree with degree d in the subtree;
            - ("b",None) if v is not in the subtree and is adjacent to exactly one
              vertex of the subtree;
            - ("r",i) if v rejected of the subtree. If i==v the vertex was voluntary rejected
              from a potential subtree by the users. Otherwise it indicates that the addition
              of the vertex v to the subtree will form a cycle since vertex i was add to
              the subtree.
            - ("a",None) if v can eventually be add to the subtree but his addition will
              created a disconnected subgraph in the actual state (i.e v is not on the border
              of the subtree)

        parent: Dictionnary that store the parent of a leaf or a border element or a
        leaf in the tree. The parent of a border element is the vertex in the tree it is
        connected to. The parent of a tree vertex is the tree vertex it was connected to
        (when a border vertex become a leaf the parent don't change)

        graph: The graph used to induced the subtree

        num_leaf: The number of leaves of the subtree. Note that with this class a tree with only
        one vertex is consider to have one leaf but the function subtree_num_leaf makes
        the correction.

        subtree_size: The number of vertices in the subtree

        num_rejected: The number of vertices that are rejected

        user_intervention_stack: Stack of the subtree vertices in the order of which the user
        explicitly specify the state (by addition or rejection). Last vertex the user acts on
        is on top.

        num_leaf_creator: The last number of leaf creator. A leaf creator is a vertex with
        status "b" that is connected to an inner vertex of the subtree.
    """

    def __init__(self, G):
        r"""
        Constructor of the graph border. Initialize the state of all vertices
        to ("a", None)
        """
        self.vertex_status=dict()
        self.parent=dict()
        self.graph=G
        self.num_leaf=0
        self.subtree_size=0
        self.num_rejected=0
        self.user_intervention_stack=[]
        self.num_leaf_creator=0
        for v in G.vertex_iterator():
            self.vertex_status[v]=("a", None)
            self.parent[v]=None

    def vertex_to_add(self):
        r"""
        Return a vertex of the graph that can extend the current solution into a tree.
        Return any vertex if the subtree is empty.
        Return None if the current solution can't be extend.
        """
        if self.subtree_size==0:
            #The subtree is empty, any non rejected vertex can be add
            for v in self.vertex_status:
                if self.vertex_status[v][0]=="a":
                    return v
        else:
            #The subtree is unempty, a vertex of the border must be add
            for v in self.vertex_status:
                if self.vertex_status[v][0]=="b":
                    return v
        return None

    def vertex_border_size(self,v):
        r"""
        For a vertex v, count the number of border vertices that are 
        connected to v.
        """
        size=0
        for u in self.graph.neighbor_iterator(v):
            if self.vertex_status[u][0]=="b":
                size+=1
        return size

    def add_to_subtree(self,v):
        r"""
        Add a vertex of the border to the current solution or initiate a solution
        with a first vertex.

        INPUTS:
            v - A vertex of the border or if the subtree is empty any available vertex
        """
        assert self.vertex_status[v][0]=="b" or self.subtree_size==0
        for u in self.graph.neighbor_iterator(v):
            (state,info)=self.vertex_status[u]
            if state=="a":
                self.vertex_status[u]=("b",None)
                self.parent[u]=v
            elif state=="s":
                self.vertex_status[u]=(state,info+1)
                if info==1:
                    self.num_leaf-=1
            elif state=="b":
                self.num_rejected+=1
                self.vertex_status[u]=("r",v)
                if self.vertex_status[self.parent[u]][1]>1: #u was a leaf creator
                    self.num_leaf_creator-=1
            #If the vertices is already rejected we do nothing

        if self.subtree_size>0: #The vertex extend a current solution
            self.vertex_status[v]=("s",1)
            parent=self.parent[v]
            if self.vertex_status[parent][1]==2:
                #The addition create a new inner vertex parent
                #num_leaf_creator must be update
                self.num_leaf_creator+=self.vertex_border_size(parent)
            elif self.vertex_status[parent][1]>2:
                #The added vertex was a leaf creator
                self.num_leaf_creator-=1
        else: #The vertex is the first vertex to be set to "s"
            self.vertex_status[v]=("s",0)
        self.num_leaf+=1
        self.subtree_size+=1
        self.user_intervention_stack.append(v)

    def _remove_last_addition(self,v):
        r"""
        Removes the last inserted vertex v to the subtree.
        """
        for u in self.graph.neighbor_iterator(v):
            (state,info)=self.vertex_status[u]
            #Impossible that state=="a"
            if state=="b":
                self.vertex_status[u]=("a", None)
            elif state=="s":
                self.vertex_status[u]=(state,info-1)
                if info==2:
                    self.num_leaf+=1
            #At this point the state must be "r"
            elif info==v:
                #u was reject by addition of v
                self.vertex_status[u]=("b",None)
                if self.vertex_status[self.parent[u]][1]>1:
                    #u is now a leaf creator
                    self.num_leaf_creator+=1
                self.num_rejected-=1

        self.subtree_size-=1
        self.num_leaf-=1
        if self.subtree_size>0: #The subtree is not empty
            parent_v=self.parent[v]
            self.vertex_status[v]=("b",None)
            if self.vertex_status[parent_v][1]==1:
                #parent_v just became a leaf
                self.num_leaf_creator-=self.vertex_border_size(parent_v)-1
            elif self.vertex_status[parent_v][1]>1:
                #parent_v still a inner vertex and v become a leaf creator
                self.num_leaf_creator+=1
        else: #We remove the last vertex from the subtree
            self.vertex_status[v]=("a",None)

    def reject_vertex(self,v):
        r"""
        Sets a vertex that is not in the solution to rejected.
        When a vertex v has been rejected using this method,
        his value in vertex_status is set to ("r",v)
        """
        assert self.vertex_status[v][0]=="b" or self.subtree_size==0
        if self.subtree_size!=0:
            #The element we reject is on the border
            if self.vertex_status[self.parent[v]][1]>1:
                #v was a leaf creator
                self.num_leaf_creator-=1
        self.vertex_status[v]=("r",v)
        self.num_rejected+=1
        self.user_intervention_stack.append(v)

    def _unreject_last_manual_rejection(self,v):
        r"""
        Cancel the last manual rejection. Vertex v must be te last rejected vertex.
        """
        self.num_rejected-=1
        if self.subtree_size==0:
            self.vertex_status[v]=("a",None)
        else:
            self.vertex_status[v]=("b",None)
            if self.vertex_status[self.parent[v]][1]>1:
                #v is a leaf creator
                self.num_leaf_creator+=1

    def undo_last_user_action(self):
        r"""
        Undo the last user intervention which is either and addition to the subtree
        or a rejection.
        """
        v=self.user_intervention_stack.pop()
        if self.vertex_status[v][0]=="s":
            self._remove_last_addition(v)
        else:
            self._unreject_last_manual_rejection(v)

    def subtree_num_leaf(self):
        r"""
        Return the number of leaf in the subtree
        """
        if self.subtree_size==1:
            return 0
        else:
            return self.num_leaf

    def leaf_potential(self,i):
        r"""
        Evaluate a maximal potential number of leaf for a subtree of i
        vertices build from the current subtree

        The size of the tree must be bigger than the current tree size.
        """
        assert i>=self.subtree_size, "The size of the tree is not big enough"
        assert i<=self.graph.num_verts(), "The size is too big"
        if i<=self.subtree_size+self.num_leaf_creator:
            return self.num_leaf+i-self.subtree_size
        else:
            return self.num_leaf+i-self.subtree_size-1

    def plot(self):
        r"""
        Plot a graph representation of the graph bordrer with following convention for
        node colors:
            green: The node is in the subtre
            yellow: The vertex is on the border
            red: The vertex is rejected by an other vertex
            black:The vertex is rejected by the user
            blue: If the vertex is available

        The vertex of the induced subtree are in green
        """
        vertex_color={"blue": [], "yellow": [], "black": [], "red": [], "green": []} 
        for v in self.graph.vertex_iterator():
            (state,info)=self.vertex_status[v]
            if state=="a":
                vertex_color["blue"].append(v)
            elif state=="b":
                vertex_color["yellow"].append(v)
            elif state=="s":
                vertex_color["green"].append(v)
            else: #state is "r"
                if info==v:
                    vertex_color["black"].append(v)
                else:
                    vertex_color["red"].append(v)
        
        tree_edge=[]
        for (u,v,label) in self.graph.edge_iterator():
            if self.vertex_status[v][0]=="s"==self.vertex_status[u][0]:
                tree_edge.append((u,v))

        return self.graph.plot(vertex_colors=vertex_color, edge_colors={"green": tree_edge})

    def __repr__(self):
        return "subtree_size: %s, num_leaf: %s, num_rejected: %s, num_leaf_creator: %s" %(self.subtree_size,self.num_leaf, self.num_rejected, self.num_leaf_creator)
