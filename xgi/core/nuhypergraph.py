from collections import defaultdict
from collections.abc import Hashable, Iterable
from copy import copy, deepcopy
from itertools import count
from warnings import warn

from ..exception import IDNotFound, XGIError, frozen
from ..utils import IDDict, update_uid_counter
from .views import EdgeView, NodeView

__all__ = ["nuHypergraph"]

class nuHypergraph():
    # Got to take care of all the OOP params that should be implemented and so on.
    __ds: dict()
    def __init__(self, uh):
        __ds: {list(k): 1 for k in uh.edges.members()}