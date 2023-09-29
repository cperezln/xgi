from collections import defaultdict
from collections.abc import Hashable, Iterable
from copy import copy, deepcopy
from itertools import count
from warnings import warn
import numpy as np
import math
from ..exception import IDNotFound, XGIError, frozen
from ..utils import IDDict, update_uid_counter
from .views import EdgeView, NodeView
from ..core.hypergraph import Hypergraph
from itertools import combinations
__all__ = ["nuHypergraph"]

class nuHypergraph(Hypergraph):
    # Got to take care of all the OOP params that should be implemented and so on.
    _node_dict_factory = IDDict
    _node_attr_dict_factory = IDDict
    _hyperedge_dict_factory = IDDict
    _hyperedge_attr_dict_factory = IDDict
    _hypergraph_attr_dict_factory = dict

    def __setstate__(self, state):
        """Function that allows unpickling of a hypergraph.

        Parameters
        ----------
        state
            The keys access the dictionary names the values are the
            dictionarys themselves from the Hypergraph class.

        Notes
        -----
        This allows the python multiprocessing module to be used.
        """
        self._edge_uid = state["_edge_uid"]
        self._hypergraph = state["_hypergraph"]
        self._node = state["_node"]
        self._node_attr = state["_node_attr"]
        self._edge = state["_edge"]
        self._edge_attr = state["_edge_attr"]
        self._nodeview = NodeView(self)
        self._edgeview = EdgeView(self)

    def __init__(self, uh):
        self._edge_uid = count()
        self._hypergraph = self._hypergraph_attr_dict_factory()
        self._node = self._node_dict_factory()
        self._node_attr = self._node_attr_dict_factory()
        self._edge = self._hyperedge_dict_factory()
        self._edge_attr = self._hyperedge_attr_dict_factory()

        self._nodeview = NodeView(self)
        """A :class:`~xgi.core.reportviews.NodeView` of the hypergraph."""

        self._edgeview = EdgeView(self)
        """An :class:`~xgi.core.reportviews.EdgeView` of the hypergraph."""

        self._num_nodes = len(uh.nodes)
        self._nodes = set(uh.nodes)
        self._ds = {tuple(k): 1 for k in uh.edges.members()}
    @property
    def nodes(self):
        """A :class:`NodeView` of this network."""
        return self._nodeview

    @property
    def edges(self):
        """An :class:`EdgeView` of this network."""
        return self._edgeview
    
    @property
    def ds(self):
        return self._ds
    
    @property
    def num_nodes(self):
        return self._num_nodes
    @property
    def nodes(self):
        return self._nodes
    
    def uniformize(self, m = None):
        N = self._num_nodes
        if not m:
            m = max([len(ind) for ind in list(self._ds.keys())])
        else:
            assert isinstance(m, int)
        if len(set(self._ds.keys())) != 1 or m <= max([len(ind) for ind in list(self._ds.keys())]):
            N+=1
        new_ds = dict()
        for hyperedge in self._ds:
            initial_len = len(hyperedge)
            edge = list(hyperedge)
    
            if len(edge) <= m:
                while len(edge) < m:
                    edge.append(N - 1)
                    if not N - 1 in self._nodes:
                        self._nodes.add(N - 1)
                        self._num_nodes += 1
                entry = np.math.factorial(initial_len)/np.math.factorial(len(edge))
                if tuple(edge) in new_ds:
                    new_ds[tuple(edge)] += entry
                else:
                    new_ds[tuple(edge)] = entry
            else:
                indcomb = combinations(edge, m)
                entry = 1/(np.math.factorial(m)*math.comb(len(edge), m))
                for indtuple in indcomb:
                    if indtuple in new_ds:
                        new_ds[indtuple] += entry
                    else:
                        new_ds[indtuple] = entry
        self._ds = new_ds
        
                