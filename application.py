"""
Module for the application.
"""

from lib.election import ElectionProtocolManager
from network import Network


class Application():

    """
    Defines a simple application that uses an election protocol.
    """

    _node_id: int
    _election_startup_time: float
    _network: Network
    _election_protocol_manager: ElectionProtocolManager
    _is_leader: bool

    def __init__(self, node_id: int, network_file_path: str, election_startup_time: float) -> None:
        self._node_id = node_id
        self._network = Network(network_file_path)
        node_address = self._network.get_node_election_address(node_id)
        neighbors = self._network.get_election_neighbors(node_id)

        self._election_startup_time = election_startup_time
        self._election_protocol_manager = ElectionProtocolManager(node_id, node_address[0], node_address[1], neighbors)
        self._is_leader = False

    def start(self) -> None:
        """
        Starts the application.
        """

        self.connect_to_neighbors()
        self.elect_leader()

    def connect_to_neighbors(self) -> None:
        """
        Connects to the neighbors.
        """

    def elect_leader(self) -> None:
        """
        Elects a leader.
        """

        self._election_protocol_manager.start_server(self._election_startup_time)

        if self._node_id == self._network.get_election_starter_id():
            self._election_protocol_manager.start_election()
        else:
            self._is_leader = self._node_id == self._election_protocol_manager.wait_for_election()
