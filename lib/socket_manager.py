"""
The socket manager is used to manage both the server and client sockets.
"""

import select
from atexit import register
from socket import AF_INET, SOCK_STREAM, socket, timeout


class SocketManager():

    """
    Defines a socket manager.

    This is a container that has a client and a server socket, they are created and freed together.
    """

    _server_socket: socket
    _client_sockets: dict[int, socket]
    _connected_clients: dict[tuple[str, int], socket]
    _connected_clients_addresses: dict[int, tuple[str, int]]
    _timeout: float

    def __init__(self, timeout: float) -> None:
        self._server_socket = socket(AF_INET, SOCK_STREAM)
        self._client_sockets = {}
        self._connected_clients = {}
        self._connected_clients_addresses = {}
        self._timeout = timeout

        # self._server_socket.setblocking(False)

        # Register the close_sockets method to be called when the program ends.
        # The sockets can also be closed at any moment.
        register(self.close_sockets)

    def bind_server(self, address: tuple[str, int]) -> None:
        """
        Binds the server socket to the given host and port.
        """

        self._server_socket.bind(address)

    def listen(self, backlog: int) -> None:
        """
        Starts listening for connections.
        """

        self._server_socket.listen(backlog)

    def accept(self) -> tuple[str, int] | None:
        """
        Accepts a connection and returns the client address.
        """

        readable, _, _ = select.select([self._server_socket], [], [], 1)  # Timeout de 1 segundo
        if self._server_socket in readable:
            client_socket, client_address = self._server_socket.accept()
            self._connected_clients[client_address] = client_socket

            print(f"Aceitou conexão de {client_address}")

            return client_address

    def is_connected_to_server(self, server_id: int) -> bool:
        """
        Returns whether the client is connected to the server.
        """

        return server_id in self._client_sockets

    def bind_client_id_to_address(self, id: int, address: tuple[str, int]) -> None:
        """
        Binds a client id to an address.
        """

        self._connected_clients_addresses[id] = address

    def connect_to_server(self, server_id, address: tuple[str, int]) -> None:
        """
        Connects to a server as a client.
        """

        self._client_sockets[server_id] = socket(AF_INET, SOCK_STREAM)
        self._client_sockets[server_id].connect(address)
        print("enviou conexao")

    def send_to_client(self, client_id: int, message: str) -> None:
        """
        Sends a message to a client using the client id.
        """

        try:
            self._connected_clients[self._connected_clients_addresses[client_id]].sendall(message.encode("utf-8"))
        except Exception as exception:
            print(f"Socket error: {exception}")

    def send_to_server(self, server_id: int, message: str) -> bool:
        """
        Sends a message to a server using the server id.
        """

        try:
            self._client_sockets[server_id].sendall(message.encode("utf-8"))
            return False
        except Exception as exception:
            print(f"Socket error: {exception}")
            return True

    def receive_from_client_by_address(self, address: tuple[str, int]) -> str:
        """
        Receives a message from a client using the client address.
        """

        try:
            message = self._connected_clients[address].recv(1024).decode("utf-8")
        except Exception as exception:
            print(f"Socket error: {exception}")
            message = ""

        return message

    def receive_from_client_by_id(self, client_id: int) -> str:
        """
        Receives a message from a client using the client id.
        """

        try:
            message = self._connected_clients[self._connected_clients_addresses[client_id]].recv(1024).decode("utf-8")
        except Exception as exception:
            print(f"Socket error: {exception}")
            message = ""

        return message

    def receive_from_server(self, server_id: int) -> str | None:
        """
        Receives a message from a server using the server id.
        """

        client_socket = self._client_sockets[server_id]
        client_socket.settimeout(self._timeout)

        try:
            message = client_socket.recv(1024).decode("utf-8")

            return message
        except timeout:
            return None

    def close_connection_with_client(self, client_id: int) -> None:
        """
        Closes a connection using the client id.
        """

        self._connected_clients[self._connected_clients_addresses[client_id]].close()
        self._connected_clients.pop(self._connected_clients_addresses[client_id])
        self._connected_clients_addresses.pop(client_id)

    def close_connection_with_server(self, server_id: int) -> None:
        """
        Closes a connection using the server id.
        """

        self._client_sockets[server_id].close()
        self._client_sockets.pop(server_id)

    def close_server_socket(self) -> None:
        """
        Closes the server socket.
        """

        for client_socket in self._connected_clients.values():
            client_socket.close()

        self._server_socket.close()

    def close_client_sockets(self) -> None:
        """
        Closes the client sockets.
        """

        for client_socket in self._client_sockets.values():
            client_socket.close()

    def close_sockets(self) -> None:
        """
        Closes both the server and client sockets.
        """

        self.close_server_socket()
        self.close_client_sockets()
