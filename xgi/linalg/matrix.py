import numpy as np
from scipy.sparse import csr_matrix

__all__ = [
    "incidence_matrix",
    "adjacency_matrix",
    "intersection_profile",
    "laplacian",
    "clique_motif_matrix",
]


def incidence_matrix(
    H, order=None, sparse=True, index=False, weight=lambda node, edge, H: 1
):
    """
    A function to generate a weighted incidence matrix from a Hypergraph object,
    where the rows correspond to nodes and the columns correspond to edges.

    Parameters
    ----------
    H: Hypergraph object
        The hypergraph of interest
    order: int, optional
        Order of interactions to use. If None (default), all orders are used. If int,
        must be >= 1.
    sparse: bool, default: True
        Specifies whether the output matrix is a scipy sparse matrix or a numpy matrix
    index: bool, default: False
        Specifies whether to output dictionaries mapping the node and edge IDs to indices
    weight: lambda function, default=lambda function outputting 1
        A function specifying the weight, given a node and edge

    Returns
    -------
    I: numpy.ndarray or scipy csr_matrix
        The incidence matrix, has dimension (n_nodes, n_edges)
    rowdict: dict
        The dictionary mapping indices to node IDs, if index is True
    coldict: dict
        The dictionary mapping indices to edge IDs, if index is True

    Examples
    --------
        >>> import xgi
        >>> N = 100
        >>> ps = [0.1, 0.01]
        >>> H = xgi.random_hypergraph(N, ps)
        >>> I = xgi.incidence_matrix(H)

    """
    edge_ids = H.edges
    if order is not None:
        edge_ids = [id_ for id_, edge in H._edge.items() if len(edge) == order + 1]
    if not edge_ids:
        return (np.array([]), {}, {}) if index else np.array([])

    node_ids = H.nodes
    num_edges = len(edge_ids)
    num_nodes = len(node_ids)

    node_dict = dict(zip(node_ids, range(num_nodes)))
    edge_dict = dict(zip(edge_ids, range(num_edges)))

    if node_dict and edge_dict:

        if index:
            rowdict = {v: k for k, v in node_dict.items()}
            coldict = {v: k for k, v in edge_dict.items()}

        if sparse:
            # Create csr sparse matrix
            rows = []
            cols = []
            data = []
            for node in node_ids:
                memberships = H.nodes.memberships(node)
                # keep only those with right order
                memberships = [i for i in memberships if i in edge_ids]
                if len(memberships) > 0:
                    for edge in memberships:
                        data.append(weight(node, edge, H))
                        rows.append(node_dict[node])
                        cols.append(edge_dict[edge])
                else:  # include disconnected nodes
                    for edge in edge_ids:
                        data.append(0)
                        rows.append(node_dict[node])
                        cols.append(edge_dict[edge])
            I = csr_matrix((data, (rows, cols)))
        else:
            # Create an np.matrix
            I = np.zeros((num_nodes, num_edges), dtype=int)
            for edge in edge_ids:
                members = H.edges.members(edge)
                for node in members:
                    I[node_dict[node], edge_dict[edge]] = weight(node, edge, H)
        if index:
            return I, rowdict, coldict
        else:
            return I
    else:
        if index:
            return np.array([]), {}, {}
        else:
            return np.array([])


def adjacency_matrix(H, order=None, s=1, weighted=False, index=False):
    """
    A function to generate an adjacency matrix (N,N) from a Hypergraph object.

    Parameters
    ----------
    H: Hypergraph object
        The hypergraph of interest
    order: int, optional
        Order of interactions to use. If None (default), all orders are used. If int,
        must be >= 1.
    s: int, default: 1
        Specifies the number of overlapping edges to be considered connected.
    index: bool, default: False
        Specifies whether to output disctionaries mapping the node IDs to indices

    Returns
    -------
    if index is True:
        return A, rowdict
    else:
        return A

    Examples
    --------
        >>> import xgi
        >>> n = 1000
        >>> ps = [0.01, 0.001]
        >>> H = xgi.random_hypergraph(n, ps)
        >>> A = xgi.adjacency_matrix(H)

    """
    I, rowdict, coldict = incidence_matrix(H, index=True, order=order)

    if I.shape == (0,):
        if not rowdict:
            A = np.array([])
        if not coldict:
            A = np.zeros((H.num_nodes, H.num_nodes))
        return (A, {}) if index else A

    A = I.dot(I.T)
    A.setdiag(0)

    if not weighted:
        A = (A >= s) * 1
    else:
        A[A < s] = 0

    if index:
        return A, rowdict
    else:
        return A


def intersection_profile(H, order=None, index=False):
    """
    A function to generate an intersection profile from a Hypergraph object.

    Parameters
    ----------
    H: Hypergraph object
        The hypergraph of interest
    order: int, optional
        Order of interactions to use. If None (default), all orders are used. If int,
        must be >= 1.
    index: bool, default: False
        Specifies whether to output dictionaries mapping the edge IDs to indices

    Returns
    -------
    if index is True:
        return P, rowdict, coldict
    else:
        return P

    Examples
    --------
        >>> import xgi
        >>> N = 100
        >>> ps = [0.1, 0.01]
        >>> H = xgi.random_hypergraph(N, ps)
        >>> P = xgi.intersection_profile(H)
    """

    if index:
        I, _, coldict = incidence_matrix(H, order=order, index=True)
    else:
        I = incidence_matrix(H, order=order, index=False)

    P = I.T.dot(I)

    if index:
        return P, coldict
    else:
        return P


def _degree(H, order=None, index=False):
    """Returns the degree of each node as an array

    Parameters
    ----------
    H: Hypergraph object
        The hypergraph of interest
    order: int, optional
        Order of interactions to use. If None (default), all orders are used. If int,
        must be >= 1.
    index: bool, default: False
        Specifies whether to output disctionaries mapping the node and edge IDs to indices

    Returns
    -------
    if index is True:
        return K, rowdict
    else:
        return K
    """

    if index:
        I, rowdict, _ = incidence_matrix(H, index=True, order=order)
    else:
        I = incidence_matrix(H, index=False, order=order)

    if I.shape == (0,):
        return np.array([])

    K = np.sum(I, axis=1)
    return (K, rowdict) if index else K


def laplacian(H, order=1, rescale_per_node=False, index=False):

    """Laplacian matrix of order d, see [1]_.

    Parameters
    ----------
    HG : horss.HyperGraph
        Hypergraph
    order : int
        Order of interactions to consider. If order=1 (default),
        returns the usual graph Laplacian
    index: bool, default: False
        Specifies whether to output disctionaries mapping the node and edge IDs to indices

    Returns
    -------
    L_d : numpy array
        Array of dim (N, N)
    if index is True:
        return rowdict
    References
    ----------
    .. [1] Lucas, M., Cencetti, G., & Battiston, F. (2020).
        Multiorder Laplacian for synchronization in higher-order networks.
        Physical Review Research, 2(3), 033410.

    """
    A, row_dict = adjacency_matrix(H, order=order, weighted=True, index=True)
    if A.shape == (0,):
        return (np.array([]), {}) if index else np.array([])

    K = _degree(H, order=order, index=False)

    L = order * np.diag(np.ravel(K)) - A  # ravel needed to convert sparse matrix
    L = np.asarray(L)

    if rescale_per_node:
        L = L / order

    if index:
        return L, row_dict
    else:
        return L


def clique_motif_matrix(H, index=False):
    """
    A function to generate a weighted clique motif matrix
    from a Hypergraph object.

    Parameters
    ----------
    H: Hypergraph object
        The hypergraph of interest
    index: bool, default: False
        Specifies whether to output dictionaries
        mapping the node and edge IDs to indices

    Returns
    -------
    if index is True:
        return W, rowdict, coldict
    else:
        return W

    References
    ----------
    "Higher-order organization of complex networks"
    by Austin Benson, David Gleich, and Jure Leskovic
    https://doi.org/10.1126/science.aad9029

    Examples
    --------
        >>> import xgi
        >>> N = 100
        >>> ps = [0.1, 0.01]
        >>> H = xgi.random_hypergraph(N, ps)
        >>> W = xgi.clique_motif_matrix(H)
    """
    if index:
        I, rowdict, _ = incidence_matrix(H, index=True)
    else:
        I = incidence_matrix(H, index=False)

    if I.shape == (0,):
        return (np.array([]), rowdict) if index else np.array([])

    W = I.dot(I.T)
    W.setdiag(0)
    W.eliminate_zeros()

    if index:
        return W, rowdict
    else:
        return W
