from typing import List, Set, Tuple, Iterable
import networkx as nx
from collections import defaultdict
from itertools import product, combinations

from dbca.base import Compound
from dbca.sample import Sample

class RelationalCompound(Compound):
    """
    Compound representation for RelationalSample. 
    # TODO Currently supporting linear sub-graphs, need some graph to string 
    # linearization for more general sub-graphs.
    """
    def __init__(self, sub_graph: nx.DiGraph, sample_graph: nx.DiGraph = None, 
                 sid: str = None, repr_attr=None):
        super(RelationalCompound, self).__init__(sub_graph, sample_graph, sid)
        self.G = sub_graph
        self.sample_G = sample_graph if sample_graph else sub_graph

        # create unique ordering for atoms
        # TODO: current repr of compound do not distinguish left and right arcs.
        sorted_atoms = list(nx.algorithms.dag.lexicographical_topological_sort(self.G))
        if repr_attr:
            attributes = nx.get_node_attributes(self.G, repr_attr)
            sorted_atoms = [attributes[x] for x in sorted_atoms]
        self._repr = "_".join(sorted_atoms)
        
    def __repr__(self):
        return self._repr
    
    def __str__(self):
        return self._repr
    
    def __hash__(self):
        return hash(self.__repr__())
    
    def __eq__(self, other):
        return (
            self.__class__ == other.__class__ and
            self.__hash__() == other.__hash__()
            )
    
    @classmethod
    def from_edges(cls, edges: Iterable[Tuple[str, str]]):
        g = nx.DiGraph()
        g.add_edges_from(edges)
        return cls(g)
        
        

        

class RelationalSample(Sample):
    """
    Toy sample type, graph representing relations between unique entities.
    """
    def __init__(self, graph: nx.DiGraph, name: str = "", max_nodes_per_compound=float('inf'), node_attr=None):
        super(RelationalSample, self).__init__(graph, name)
        self.G = graph
        self.compounds_by_type = defaultdict(list)
        self.max_nodes_per_compound = max_nodes_per_compound
        self.node_attr = node_attr
        
        
    @property
    def atoms(self) -> List[str]:
        """
        Return list of atoms. 
        Assuming atoms are simply strings.

        """
        if self.node_attr:
            return list(nx.get_node_attributes(self.G, self.node_attr).values())
        else:
            return list(self.G.nodes())
    
    
    @property
    def compounds(self) -> List[str]:
        if hasattr(self, "_compounds"):
            return self._compounds
        else:
            self._compounds = []

            # # we define compounds as connected induced subgraphs.
            # max_nodes = min(self.max_nodes_per_compound, len(self.G.nodes()))
            # for r in range(2, max_nodes+1):
            #     for SG in (self.G.subgraph(s) for s in combinations(self.G, r)):
            #         if (nx.is_weakly_connected(SG)):
            #             new_compound = RelationalCompound(SG, self.G, self.id, self.node_attr)
            #             self._compounds.append(new_compound)

            # we define compounds as linear sub-graphs (paths) of any length.
            for a1, a2 in product(self.G.nodes(), self.G.nodes()):
                new_compounds = [RelationalCompound(self.G.edge_subgraph(p), self.G, self.id, self.node_attr) 
                                 for p in list(nx.all_simple_edge_paths(self.G, source=a1, target=a2)) 
                                    if p and len(p) + 1 <= self.max_nodes_per_compound]
                self._compounds += new_compounds
            
            # otherwise we will double count subgraphs
            self._compounds = set(self._compounds)
            for c in self._compounds:
                self.compounds_by_type[str(c)].append(c)
            return self._compounds
        
        
    def get_occurrences(self, compound_type: str) -> Iterable[Compound]:
        """
        Return all occurences of compounds of type `compound_type`.

        """
        return self.compounds_by_type[compound_type]
    
    def compounds_types(self) -> List[str]:
        return list(self.compounds_by_type.keys())
    
                
                
            
        
        
    
    