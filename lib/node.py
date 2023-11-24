"""
Node module.
"""

import threading


class NodeInfo:
    """
    Defines host and port for communication.
    """

    _host: str
    _port: int
    _id: int

    def __init__(self, host: str, port: int, id: int) -> None:
        self._host = host
        self._port = port
        self._id = id

    @property
    def host(self) -> str:
        """
        Get the host name.

        Returns:
        str: The host name.
        """
        return self._host

    @property
    def port(self) -> int:
        """
        Get the port number.

        Returns:
        int: The port number.
        """
        return self._port

    @property
    def id(self) -> int:
        """
        Get the id number.

        Returns:
        int: The id number.
        """
        return self._id


class Node:

    """
    Defines a node of a graph.
    """

    _id: int
    _neighbours: list[NodeInfo]
    _done: bool
    _is_leaf: bool
    _leader_id: int
    _able_to_request_parent: bool
    _children: list[int]

    # neighbours: list of identifiers of other Nodes connected to this
    def __init__(self, id: int, neighbors_info: list[NodeInfo]) -> None:
        self._id = id
        self._neighbours = neighbors_info
        self._done = False
        self._is_leaf = len(neighbors_info) == 1
        self._leader_id = -1
        self._able_to_request_parent = False
        self._children = []

    def is_leader(self):
        """
        Check if the current node is the leader.

        Returns:
            bool: True if the current node is the leader, False otherwise.
        """
        return self._leader_id == self._id

    @property
    def leader_id(self):
        """
        Get the leader id.

        Returns:
            int: The leader id.
        """
        return self._leader_id

    @property
    def is_leaf(self):
        """
        Check if the current node is a leaf.

        Returns:
            bool: True if the current node is a leaf, False otherwise.
        """
        return self._is_leaf

    @property
    def able_to_request_parent(self):
        """
        Check if the current node is able to request parent.

        Returns:
            bool: True if the current node is able to request parent, False otherwise.
        """
        return self._able_to_request_parent

    @property
    def children(self):
        """
        Get the children list.

        Returns:
            list[int]: The children list.
        """
        return self._children

    @property
    def neighbours(self):
        """
        Get the neighbours list.

        Returns:
            list[int]: The neighbours list.
        """
        return self._neighbours

    @property
    def id(self):
        """
        Get the id.

        Returns:
            int: The id.
        """
        return self._id

    def add_child(self, child_id: int):
        """
        Add a child to the children list.

        Args:
            child_id (int): The child id.

        Returns:
            None
        """
        self._children.append(child_id)

    def set_leader(self, leader_id: int):
        """
        Set the leader id.

        Args:
            leader_id (int): The leader id.

        Returns:
            None
        """
        self._leader_id = leader_id

    def set_able_to_request_parent(self, able_to_request_parent: bool):
        """
        Set the able_to_request_parent flag.

        Args:
            able_to_request_parent (bool): The able_to_request_parent flag.

        Returns:
            None
        """
        self._able_to_request_parent = able_to_request_parent

    def get_neighbor_by_id(self, neighbor_id: int) -> NodeInfo:
        """
        Get a neighbor by its id.

        Args:
            neighbor_id (int): The neighbor id.

        Returns:
            NodeInfo: The neighbor.
        """
        for neighbor in self._neighbours:
            if neighbor.id == neighbor_id:
                return neighbor
        return None
