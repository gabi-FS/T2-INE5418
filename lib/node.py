class Node:
    # neighbours: list of identifiers of other Nodes connected to this
    def __init__(self, id, neighbours, leaf) -> None:
        self.id = id
        self.neighbours = neighbours
        self.done = False
        self.is_leaf = leaf
