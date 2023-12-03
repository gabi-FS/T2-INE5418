"""
Module for the connection manager.
"""


from __future__ import annotations

from threading import Thread
from typing import TYPE_CHECKING

from lib.socket_manager import SocketManager

if TYPE_CHECKING:
    from lib_refactor.election_node import NodeAddress


class ConnectionManager():

    """
    Defines a connection manager.
    """

    _node_id: int
    _socket_manager: SocketManager
    _server_thread: Thread
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

    def start(self, handle_message) -> None:
        """
        Initializes the node by starting the server.
        """

        self._server_thread = Thread(target=self.start_server, args=(handle_message,))
        self._server_thread.start()

    def start_server(self, handle_message):
        """
        Starts the server and listens for incoming connections.
        """

        self._socket_manager.bind_server(self._server_address.address())
        self._socket_manager.listen(10)

        print(f"Node {self._node_id} listening on {self._server_address}")

        while not self._server_finished:
            client_address = self._socket_manager.accept()

            if client_address:
                print(f"Node {self._node_id} accepted connection from {client_address[0]}:{client_address[1]}")

                message, node_id = self._socket_manager.receive_from_client(client_address).split()

                node_id = int(node_id)

                print(f"Node {self._node_id} received message \"{message}\" from node {node_id}")

                self._socket_manager.bind_client_id_to_address(node_id, client_address)

                handle_message(node_id, message)

                self._socket_manager.close_connection_with_client(node_id)

                print(f"Connection closed with node {node_id}")

        print("Closing server")
        self._socket_manager.close_server_socket()

    def send_message_to_client(self, client_node_id: int, message: str) -> None:
        """
        Sends a message to a client.
        """

        try:
            self._socket_manager.send_to_client(client_node_id, message)
            print(f"Node {self._node_id} sent message: {message}")
        except Exception as exception:
            print(f"Node {self._node_id} error: {exception}")

    def send_message_to_server(self, server_id: int, message: str) -> None:
        """
        Sends a message to a neighbor socket.

        Args:
            neighbor_id (int): The ID of the neighbor node.
            message (str): The message to be sent.
        """

        # TODO: Resolver problema de conexão com o servidor
        # if not self._socket_manager.is_connected_to_server(server_id):
        self._socket_manager.connect_to_server(server_id, self._neighbors_addresses[server_id].address())

        try:
            self._socket_manager.send_to_server(server_id, message)
            print(f"Node {self._node_id} sent message to {server_id}: {message}")
        except Exception as exception:
            print(f"Node {self._node_id} error: {exception}")

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

    def close_connection_with_server(self, server_id: int) -> None:
        """
        Closes a connection using the server id.
        """

        self._socket_manager.close_connection_with_server(server_id)
