"""
The Leader Election Protocol of IEEE 1394
"""

from time import sleep

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

    def start_server(self, startup_time: float) -> None:
        """
        Starts the node server and start the accept of other requests in another thread.
        """

        self._election_node.start_server()
        sleep(startup_time)

    def wait_for_election(self) -> int:
        """
        Block the process until the leader election ends, returning it's result.
        """

        return self._election_node.wait_for_election()

    def start_election(self, block_until_result=True) -> int:
        """
        Starts the election process, broadcasting to other nodes.

        Args:
            block_until_result (bool): if True, will wait for the result of the election and return it. If false, returns -1, and the result can be obtained from the ElectionNode class in nondeterministic time.
        """

        return self._election_node.start_the_election(block_until_result)
