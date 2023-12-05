"""
Module for the network specification.
"""

from json import load


class Network():

    """
    Defines a network graph.
    """

    _nodes: dict[int, tuple[str, int, int]]
    _connections: dict[int, list[int]]

    def __init__(self, network_file_path: str) -> None:
        with open(network_file_path, "r", encoding="utf-8") as network_file:
            network = load(network_file)

        self._nodes = {}
        for node_id, data in network["nodes"].items():
            self._nodes[int(node_id)] = (data["host"], data["election_port"], data["application_port"])

        self._connections = {int(node_id): neighbors for node_id, neighbors in network["connections"].items()}

    def get_node_count(self) -> int:
        """
        Returns the number of nodes.
        """

        return len(self._nodes)

    def get_node_election_address(self, node_id: int) -> tuple[str, int]:
        """
        Returns the address of a node.
        """

        return self._nodes[node_id][:2]

    def get_node_application_address(self, node_id: int) -> tuple[str, int]:
        """
        Returns the address of a node.
        """

        return (self._nodes[node_id][0], self._nodes[node_id][2])

    def get_election_neighbors(self, node_id: int) -> dict[int, tuple[str, int]]:
        """
        Returns the neighbors of a node.
        """

        return {neighbor_id: self._nodes[neighbor_id][:2] for neighbor_id in self._connections[node_id]}

    def get_application_neighbors(self, node_id: int) -> dict[int, tuple[str, int]]:
        """
        Returns the neighbors of a node.
        """

        result = {}

        for neighbor_id in self._connections[node_id]:
            result[neighbor_id] = (self._nodes[neighbor_id][0], self._nodes[neighbor_id][2])

        return result

    def get_election_starter_id(self) -> int:
        """
        Returns the id of the node that starts the election.
        """

        return min(self._nodes.keys())
