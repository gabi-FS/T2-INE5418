"""
Module for the application.
"""

from random import randrange
from socket import AF_INET, SOCK_STREAM, socket
from threading import Thread, Lock
from time import sleep
from lib.election import ElectionProtocolManager
from lib.network import Network


class Application():

    """
    Defines a simple application that uses an election protocol.
    """

    _node_id: int
    _election_startup_time: float
    _leader_id: int
    _network: Network
    _election_protocol_manager: ElectionProtocolManager
    _server_socket: socket | None
    _client_socket: socket | None
    _server_thread: Thread | None
    _random_number_message: str
    _lock: Lock

    def __init__(self, node_id: int, network_file_path: str, election_startup_time: float) -> None:
        self._node_id = node_id
        self._leader_id = -1
        self._server_socket = None
        self._network = Network(network_file_path)
        self._server_thread = None
        self._client_socket = None
        self._random_number_message = ""
        self._lock = Lock()
        node_address = self._network.get_node_election_address(node_id)
        neighbors = self._network.get_election_neighbors(node_id)

        self._election_startup_time = election_startup_time
        self._election_protocol_manager = ElectionProtocolManager(node_id, node_address[0], node_address[1], neighbors)

    def start(self) -> None:
        """
        Starts the application.
        """

        self.elect_leader()

    def connect_to_leader(self) -> None:
        """
        Connects to the neighbors.
        """

        print(f"Conectando ao líder: {self._network.get_node_application_address(self._leader_id)}")

        self._client_socket = socket(AF_INET, SOCK_STREAM)
        self._client_socket.connect(self._network.get_node_application_address(self._leader_id))

        for _ in range(100):
            message = str(self._node_id)
            self._client_socket.sendall(message.encode("utf-8"))
            sleep(randrange(1, 10) / 20)

        self._client_socket.sendall("X".encode("utf-8"))
        self._client_socket.close()

    def start_server(self) -> None:
        """
        Starts the server.
        """

        self._server_socket = socket(AF_INET, SOCK_STREAM)
        self._server_socket.bind(self._network.get_node_application_address(self._node_id))
        self._server_socket.listen(10)

        remaining_neighbors = self._network.get_node_count() - 1

        threads = []

        while remaining_neighbors > 0:
            client_socket, client_address = self._server_socket.accept()

            print(f"Aceitou conexão de {client_address}")
            remaining_neighbors -= 1

            threads.append(Thread(target=self.handle_client, args=(client_socket,)))
            threads[-1].start()

        for thread in threads:
            thread.join()

        self._server_socket.close()

        print(f"\nO número aleatório capturado é {self._random_number_message}")

    def handle_client(self, client_socket: socket) -> None:
        """
        Handles a client.
        """

        while True:
            message = client_socket.recv(1024).decode("utf-8")

            if message == "X":
                break

            with self._lock:
                self._random_number_message += message
                print(f"{message} ", end="", flush=True)

        client_socket.close()

    def elect_leader(self) -> None:
        """
        Elects a leader.
        """

        self._election_protocol_manager.start_server(self._election_startup_time)

        if self._node_id == self._network.get_election_starter_id():
            self._leader_id = self._election_protocol_manager.start_election()
        else:
            self._leader_id = self._election_protocol_manager.wait_for_election()

        if self._leader_id == self._node_id:
            self.start_server()
        else:
            self.connect_to_leader()
