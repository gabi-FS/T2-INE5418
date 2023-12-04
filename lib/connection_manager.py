"""
Module for the connection manager.
"""


from __future__ import annotations

from threading import Thread
from time import sleep
from typing import TYPE_CHECKING

from lib.socket_manager import SocketManager

if TYPE_CHECKING:
    from lib.election_node import NodeAddress


start_election_message = "start_election"  # Mover daqui dps?


class ConnectionManager():

    """
    Defines a connection manager.
    """

    _node_id: int
    _socket_manager: SocketManager
    _server_address: NodeAddress
    _neighbors_addresses: dict[int, NodeAddress]
    _server_finished: bool
    _server_thread: Thread | None

    def __init__(self,
                 node_id: int,
                 server_address: NodeAddress,
                 neighbors_addresses: dict[int, NodeAddress],
                 timeout: float) -> None:
        self._node_id = node_id
        self._server_address = server_address
        self._socket_manager = SocketManager(timeout)
        self._neighbors_addresses = neighbors_addresses
        self._server_finished = False
        self._server_thread = None
        self._waiting_for_election = True

    @property
    def server_finished(self) -> bool:
        """
        Returns whether the server has finished.
        """

        return self._server_finished

    @property
    def server_thread(self) -> Thread | None:
        """
        Returns the server thread.
        """

        return self._server_thread

    def finish_server(self) -> None:
        """
        Finishes the server.
        """

        self._server_finished = True

    def start_server(self, handle_message):
        """
        Starts the server and listens for incoming connections.
        """

        self._socket_manager.bind_server(self._server_address.get_address())
        self._socket_manager.listen(10)

        print(f"Node {self._node_id} listening on {self._server_address}")
        self._server_thread = Thread(target=self.wait_for_election, args=(handle_message,))
        self._server_thread.start()

    def start_leader_election(self, handle_message):
        # Dúvida: e se dois começarem ao mesmo tempo?

        self._waiting_for_election = False
        not_connected_neighbors = list(self._neighbors_addresses.keys())
        for neighbour_id in not_connected_neighbors:
            address = self._neighbors_addresses[neighbour_id].get_address()
            self._socket_manager.connect_to_server(neighbour_id, address)
            self.send_message_to_server(neighbour_id, f"{start_election_message} {self._node_id}")
            server_thread = Thread(target=self.handle_server_thread, args=(neighbour_id, handle_message))
            server_thread.start()

        # Iniciar eleição aqui? Ou depois dos acks?

    def wait_for_election(self, handle_message):
        print("Tá esperando eleição, vai entrar no accept")
        while self._waiting_for_election:
            not_connected_neighbours = list(self._neighbors_addresses.keys())
            client_address = self._socket_manager.accept()

            if client_address:
                print(f"Node {self._node_id} accepted connection from {client_address[0]}:{client_address[1]}")

                message, client_node_id = self._socket_manager.receive_from_client_by_address(client_address).split()

                client_node_id = int(client_node_id)

                print(f"Node {self._node_id} received message \"{message}\" from node {client_node_id}")

                if start_election_message == message:
                    self._waiting_for_election = False

                    not_connected_neighbours.remove(client_node_id)
                    self._socket_manager.bind_client_id_to_address(client_node_id, client_address)

                    # Fazer broadcast; -> Para os vizinhos! E criar conexões com cada um deles. Seria necessário esperar acks se já conecta antes de enviar msg?
                    for neighbour_id in not_connected_neighbours:
                        address = self._neighbors_addresses[neighbour_id].get_address()
                        self._socket_manager.connect_to_server(neighbour_id, address)
                        self.send_message_to_server(neighbour_id, f"{start_election_message} {self._node_id}")
                        server_thread = Thread(target=self.handle_server_thread, args=(neighbour_id, handle_message))
                        server_thread.start()

                    print(f"Inicializando thread do cliente {client_node_id}")
                    client_thread = Thread(target=self.handle_client_thread, args=(client_node_id, handle_message))
                    client_thread.start()

        # print("Closing server") não iria usar essa socket p mais nada, ent faz sentido já finalizar ela pra mim
        # self._socket_manager.close_server_socket()

    def handle_client_thread(self, client_id: int, handle_message) -> None:
        print(f"Node {self._node_id} handling client thread {client_id}, server {self._server_finished}")
        while not self._server_finished:
            print(f"Node {self._node_id} waiting for message from {client_id}")
            message, _ = self._socket_manager.receive_from_client_by_id(client_id).split()
            handle_message(client_id, message)

    def handle_server_thread(self, server_id: int, handle_message) -> None:
        print(f"Node {self._node_id} handling server thread {server_id}, server {self._server_finished}")
        while not self._server_finished:
            print(f"Node {self._node_id} waiting for message from {server_id}")
            message, _ = self._socket_manager.receive_from_server(server_id).split()
            handle_message(server_id, message)

    def send_message_to_client(self, client_node_id: int, message: str) -> None:
        """
        Sends a message to a client.
        """

        try:
            self._socket_manager.send_to_client(client_node_id, message)
            print(f"Node {self._node_id} sent message: {message} to {client_node_id}")
        except Exception as exception:
            print(f"Node {self._node_id} error: {exception}")

    def send_message_to_server(self, server_id: int, message: str) -> bool:
        """
        Sends a message to a neighbor socket.

        Args:
            neighbor_id (int): The ID of the neighbor node.
            message (str): The message to be sent.
        """
        # Sempre estaria conectado nesse ponto...
        try:
            error = self._socket_manager.send_to_server(server_id, message)
            if not error: print(f"Node {self._node_id} sent message to {server_id}: {message}")
            return error
        except Exception as exception:
            print(f"Node {self._node_id} error: {exception}")
            return True

    def receive_message_from_server(self, server_id: int) -> str | None:
        """
        Receives a message from a server.

        Args:
            server_id (int): The ID of the server.

        Returns:
            str: The message received.
        """

        message = self._socket_manager.receive_from_server(server_id)

        if message is not None:
            print(f"Node {self._node_id} received message: {message}")
        else:
            print(f"Node {self._node_id} did not receive a message within the timeout period.")

        return message

    # Pra que essa função é usada?
    def close_connection_with_server(self, server_id: int) -> None:
        """
        Closes a connection using the server id.
        """

        self._socket_manager.close_connection_with_server(server_id)

    def close_client_sockets(self) -> None:
        self._socket_manager.close_client_sockets()
