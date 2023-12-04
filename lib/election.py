"""
The Leader Election Protocol of IEEE 1394
"""


from lib.election_node import ElectionNode, NodeAddress


class ElectionProtocolManager():

    """
    Defines the interface of the election protocol.
    """

    _election_node: ElectionNode

    def __init__(self, node_id: int, node_host: str, node_port: int, neighbors: dict[int, tuple[str, int]]) -> None:
        node_address = NodeAddress(node_host, node_port)
        neighbors_addresses = {id: NodeAddress(host, port) for id, (host, port) in neighbors.items()}
        self._election_node = ElectionNode(node_id, node_address, neighbors_addresses)

    def start_server(self) -> None:
        """
        Starts the server.
        """

        self._election_node.start_server()

    def wait_for_election(self) -> int:
        """
        Waits for an election.
        """

        return self._election_node.wait_for_election()

    def start_election(self) -> None:
        """
        Starts an election.
        """

        self._election_node.start_the_election()
