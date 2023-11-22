'''
Node module.
'''


class Node:

    '''
    Defines a node of a graph.
    '''

    _id: int
    _neighbours: list['Node']
    _done: bool
    _is_leaf: bool

    # neighbours: list of identifiers of other Nodes connected to this
    def __init__(self, id: int, neighbours: list['Node'], leaf: bool) -> None:
        self._id = id
        self._neighbours = neighbours
        self._done = False
        self._is_leaf = leaf
