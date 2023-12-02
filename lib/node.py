"""
Node module.
"""


class NodeInfo:
    """
    Defines host and port for communication.
    """

    _host: str
    _port: int

    def __init__(self, host: str, port: int) -> None:
        self._host = host
        self._port = port

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


class Node:

    """
    Defines a node of a graph.
    """

    _id: int
    _neighbours: dict[int, NodeInfo]  # id: NodeInfo
    _possible_parents_ids: list[int]
    _children_ids: list[int]
    _done: bool
    _able_to_request_parent: bool
    _is_leaf: bool
    _leader_id: int

    def __init__(self, id: int, neighbours_info: dict[int, NodeInfo]) -> None:
        self._id = id
        self._neighbours = neighbours_info
        self._possible_parents_ids = list(neighbours_info.keys())
        self._children_ids = []
        self._done = False
        self._able_to_request_parent = False
        self._is_leaf = len(self._possible_parents_ids) == 1
        self._leader_id = -1
        
        print(f"Node {self._id} is leaf: {self._is_leaf}")

    def is_leader(self) -> bool:
        """
        Check if the current node is the leader.

        Returns:
            bool: True if the current node is the leader, False otherwise.
        """
        return self._leader_id == self._id

    @property
    def leader_id(self) -> int:
        """
        Get the leader id.

        Returns:
            int: The leader id.
        """
        return self._leader_id

    @property
    def is_leaf(self) -> bool:
        """
        Check if the current node is a leaf.

        Returns:
            bool: True if the current node is a leaf, False otherwise.
        """
        return self._is_leaf

    @property
    def able_to_request_parent(self) -> bool:
        """
        Check if the current node is able to request parent.

        Returns:
            bool: True if the current node is able to request parent, False otherwise.
        """
        return self._able_to_request_parent

    @property
    def children(self) -> list[int]:
        """
        Get the children list.

        Returns:
            list[int]: The children list.
        """
        return self._children_ids

    @property
    def neighbours(self) -> list[int]:
        """
        Get the neighbours list.

        Returns:
            list[int]: The neighbours list.
        """
        return self._neighbours

    @property
    def id(self) -> int:
        """
        Get the id.

        Returns:
            int: The id.
        """
        return self._id

    @property
    def possible_parents_ids(self):
        return self._possible_parents_ids

    @property
    def done(self):
        return self._done

    def add_child(self, child_id: int) -> None:
        """
        Add a child to the children list.

        Args:
            child_id (int): The child id.
        """
        self._children_ids.append(child_id)

    def set_leader(self, leader_id: int) -> None:
        """
        Set the leader id.

        Args:
            leader_id (int): The leader id.
        """
        self._leader_id = leader_id

    def set_able_to_request_parent(self, able_to_request_parent: bool) -> None:
        """
        Set the able_to_request_parent flag.

        Args:
            able_to_request_parent (bool): The able_to_request_parent flag.
        """
        self._able_to_request_parent = able_to_request_parent

    def set_done(self, done: bool) -> None:
        """
        Set the done flag.

        Args:
            done (bool): The done flag.
        """
        self._done = done

    def remove_possible_parent(self, neighbour_id: int) -> None:
        """
        Remove a neighbour from the possible parents list.

        Args:
            neighbour_id (int): The neighbour id.
        """
        self._possible_parents_ids.remove(neighbour_id)
