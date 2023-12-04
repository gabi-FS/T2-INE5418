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
    _waiting_for_election: bool
    _connection_types: dict[int, str] # str: client | server

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
        self._connection_types = {}

    @property
    def server_finished(self) -> bool:
        """ Returns whether the server has finished."""
        return self._server_finished

    @property
    def server_thread(self) -> Thread | None:
        """Returns the server thread."""
        return self._server_thread

    def finish_server(self) -> None:
        """Finishes the server."""
        self._server_finished = True

    def start_server(self, handle_message):
        """Starts the server and listens for incoming connections."""
        
        self._socket_manager.bind_server(self._server_address.get_address())
        self._socket_manager.listen(10)

        print(f"Node {self._node_id} listening on {self._server_address}")
        self._server_thread = Thread(target=self.wait_for_election, args=(handle_message,))
        self._server_thread.start()

    def start_leader_election(self, handle_message):
        # TODO: Dúvida: e se dois começarem ao mesmo tempo?
        self._waiting_for_election = False
        self.broadcast_start_election(list(self._neighbors_addresses.keys()), handle_message)

    def wait_for_election(self, handle_message):
        print("Vai entrar no while do accept não bloqueante em wait_for_election.")
        while self._waiting_for_election:
            not_connected_neighbors = list(self._neighbors_addresses.keys())
            client_address = self._socket_manager.accept()

            if client_address:
                print(f"Node {self._node_id} accepted connection from {client_address[0]}:{client_address[1]}")

                message, client_node_id = self._socket_manager.receive_from_client_by_address(client_address).split()
                client_node_id = int(client_node_id)

                print(f"Node {self._node_id} received message \"{message}\" from node {client_node_id}")

                if start_election_message == message:
                    self._waiting_for_election = False

                    not_connected_neighbors.remove(client_node_id)
                    self._socket_manager.bind_client_id_to_address(client_node_id, client_address)

                    # Seria necessário esperar acks se já conecta antes de enviar msg?
                    self.broadcast_start_election(not_connected_neighbors, handle_message)

                    print(f"Inicializando thread do cliente {client_node_id}")
                    self._connection_types[client_node_id] = "client"
                    client_thread = Thread(target=self.handle_connection_thread, args=(client_node_id, handle_message))
                    client_thread.start()
    
    def broadcast_start_election(self, not_connected_neighbors: list[int], handle_message):
        for neighbour_id in not_connected_neighbors:
            address = self._neighbors_addresses[neighbour_id].get_address()
            self._socket_manager.connect_to_server(neighbour_id, address)
            self._connection_types[neighbour_id] = "server"
            self.send_message(neighbour_id, f"{start_election_message} {self._node_id}")
            connection_thread = Thread(target=self.handle_connection_thread, args=(neighbour_id, handle_message))
            connection_thread.start()
        
    def handle_connection_thread(self, connection_id: int, handle_message) -> None:
        print(f"Node {self._node_id} handling connection thread {connection_id}, server {self._server_finished}")
        while not self._server_finished:
            try:
                print(f"Node {self._node_id} waiting for message from {connection_id}")
                connection_type = self._connection_types[connection_id]
                if connection_type == "client":
                    message, node_message = self._socket_manager.receive_from_client_by_id(connection_id).split()
                elif connection_type == "server":
                    message, node_message = self._socket_manager.receive_from_server(connection_id).split()
                    
                handle_message(connection_id, message, int(node_message))
            except OSError:
                print(f"socket {connection_id} pode ter finalizado")
                break
            except ValueError:   
                # Veio uma mensagem nula ou incorreta e daí deu valueError. melhor tratamento?
                print(f"socket {connection_id} pode ter finalizado")
                break
            
    def send_message(self, node_id: int, message: str):
        """Sends a message, identifying if it's for a client socket or a server socket.

        Args:
            node_id (int): The ID of the neighbor node to send.
            message (str): The message.
        """
        try:
            connection_type = self._connection_types[node_id]
            if connection_type == "client":
                self._socket_manager.send_to_client(node_id, message)
            elif connection_type == "server":
                self._socket_manager.send_to_server(node_id, message)

            print(f"Node {self._node_id} sent message: {message} to {node_id} via ", connection_type)
        except Exception as exception:
            print(f"Node {self._node_id} error: {exception}")

    def close_all_sockets(self) -> None:
        self._socket_manager.close_sockets()
