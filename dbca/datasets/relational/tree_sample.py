import networkx as nx
from dbca.datasets.relational.relational_sample import RelationalSample, RelationalCompound
import itertools

def sample2graph(expr, heads, node_attr=None):
    g = nx.DiGraph()

    nodes = [(i, {node_attr: x}) if node_attr else i for i, x in enumerate(expr) if x not in '()']
    g.add_nodes_from(nodes)

    for i, h in enumerate(heads):
        if h == -1 or expr[i] in '()':
            continue
        direction = 'L' if i < h else 'R'
        g.add_edge(h, i, dir=direction)
    return g

class Node:
    def __init__(self, pos, sym):
        self.pos = pos
        self.sym = sym
        self.children = []

    def __repr__(self):
        return self.__repr__() 
    
    def __str__(self):
        raise NotImplementedError()
        
    def __hash__(self):
        return hash(self.__repr__())
    
    def __eq__(self, other):
        return (
            self.__class__ == other.__class__ and
            self.__hash__() == other.__hash__()
            )

    @property
    def sample_id(self) -> str:
        """
        Return the id of the sample containing this compound.
        """
        return self._sid

class TreeSample(RelationalSample):
    def __init__(self, expr, heads, node_attr=None, max_depth_compound=float('inf'), **kargs):
        g = sample2graph(expr, heads, node_attr)
        super().__init__(g, node_attr=node_attr, **kargs)
        nodes = [Node(i, x) for i, x in enumerate(expr)]
        for node, h in zip(nodes, heads):
            if node.sym in '()':
                continue
            if h == -1:
                root_node = node
            else:
                nodes[h].children.append(node)
        self.nodes = nodes
        self.root_node = root_node
        self.node_attr = node_attr
        self.max_depth_compound = max_depth_compound
    
    @property
    def compounds(self):
        if hasattr(self, "_compounds"):
            return self._compounds
        else:
            compounds = []

            def flatten(l_list):
                root_l = l_list[0][0][:]
                depth = 0
                for ch_l, d in l_list[1:]:
                    root_l.extend(ch_l) 
                    depth = max(d, depth)
                depth += 1
                return (root_l, depth)

            def find_compounds(root):
                if not root.children:
                    return [([root.pos], 1)] # subtree and depth
                children_compounds = [find_compounds(x) + [([], 0)] for x in root.children] # add an empty compounds
                root_compounds = list(itertools.product([([root.pos], 1)], *children_compounds))
                root_compounds = [flatten(x) for x in root_compounds]
                root_compounds = [x for x in root_compounds 
                        if len(x[0]) <= self.max_nodes_per_compound and x[1] <= self.max_depth_compound]
                compounds.extend([x[0] for x in root_compounds])
                return root_compounds
            
            find_compounds(self.root_node)
            compounds = [x for x in compounds if len(x) > 1]
            compounds = [RelationalCompound(self.G.subgraph(x), self.G, self.id, repr_attr=self.node_attr) for x in compounds]
            
            # otherwise we will double count subgraphs
            self._compounds = compounds
            for c in self._compounds:
                self.compounds_by_type[str(c)].append(c)
            return self._compounds
    


if __name__ == '__main__':
    expr = '(3+4)/1-3'
    heads = [2, 2, 5, 2, 2, 7, 5, -1, 7]
    ts = TreeSample(expr, heads, node_attr='sym', max_depth_compound=3)
    print(ts.compounds)
