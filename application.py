"""
Module for the application.
"""


from lib.election import ElectionProtocolManager


class Application():

    """
    Defines a simple application that uses an election protocol.
    """

    _election_protocol_manager: ElectionProtocolManager

    def __init__(self, node_id: int, node_host: str, node_port: int, neighbors: dict[int, tuple[str, int]]) -> None:
        self._election_protocol_manager = ElectionProtocolManager(node_id, node_host, node_port, neighbors)

    def start_server(self) -> None:
        """
        Starts the server.
        """

        self._election_protocol_manager.start_server()

    def wait_for_election(self) -> int:
        """
        Waits for an election.
        """

        return self._election_protocol_manager.wait_for_election()

    def start_election(self) -> None:
        """
        Starts an election.
        """

        self._election_protocol_manager.start_election()
