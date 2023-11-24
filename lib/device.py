"""
Device module.
"""

import socket
import threading
import node


class Device:

    """
    Defines a device with a socket for communication.
    """

    _cfg: node.NodeInfo
    _socket: socket.socket  # tipo socket
    _neighbors: dict[int, socket.socket]
    _timeout: float

    # neighbours: list of identifiers of other Nodes connected to this
    def __init__(self, cfg: node.NodeInfo, timeout: float) -> None:
        self._cfg = cfg
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._neighbors = {}
        self._timeout = timeout

    def start_server(self):
        """
        Starts the server and listens for incoming connections.
        """
        self._socket.bind((self._cfg.host, self._cfg.port))
        self._socket.listen(10)
        print(f"Node {self._cfg.id} listening on {self._cfg.host}:{self._cfg.port}")

        while True:
            client_socket, client_address = self._socket.accept()
            print(f"Node {self._cfg.id} accepted connection from {client_address}")

            # Handle client in a separate thread
            client_thread = threading.Thread(
                target=self.handle_client, args=(client_socket,)
            )
            client_thread.start()

    def handle_client(self, client_socket):
        """
        Handles the client connection and receives data from the client.

        Args:
            client_socket (socket): The socket object representing the client connection.

        Returns:
            None
        """
        try:
            while True:
                data = client_socket.recv(1024)
                if not data:
                    break
                print(f"Node {self._cfg.id} received data: {data.decode('utf-8')}")
        except Exception as e:
            print(f"Node {self._cfg.id} error: {e}")
        finally:
            client_socket.close()
            print(f"Node {self._cfg.id} connection closed.")

    def connect_to_node(self, neighbor_info: node.NodeInfo):
        """
        Connects the current node to a neighbor node.

        Args:
            neighbor_info (node.node.NodeInfo): Information about the neighbor node, including host and port.

        Returns:
            None
        """
        neighbor_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        neighbor_socket.connect((neighbor_info.host, neighbor_info.port))
        print(
            f"Node {self._cfg.id} connected to Node at {neighbor_info.host}:{neighbor_info.host}"
        )
        self._neighbors[neighbor_info.id] = neighbor_socket

    def send_message(
        self, neighbor_id, message, neighbor_info=node.NodeInfo("a", 0, 0)
    ):
        """
        Sends a message to a neighbor socket.

        Args:
            neighbor_id (int): The ID of the neighbor node.
            message (str): The message to be sent.

        Returns:
            None
        """
        if neighbor_id not in self._neighbors:
            self.connect_to_node(neighbor_info)
        try:
            neighbor_socket = self._neighbors[neighbor_id]
            neighbor_socket.sendall(message.encode("utf-8"))
            print(f"Node {self._cfg.id} sent message: {message}")
        except Exception as e:
            print(f"Node {self._cfg.id} error: {e}")

    def receive_message(self, neighbor_id):
        """
        Receives a message from a neighbor socket.

        Args:
            neighbor_socket (socket): The socket object of the neighbor.

        Returns:
            str: The received message.
        """
        # Define the buffer size
        buffer_size = 1024

        neighbor_socket = self._neighbors[neighbor_id]

        # Set a timeout
        neighbor_socket.settimeout(self._timeout)

        try:
            # Receive the data
            data = neighbor_socket.recv(buffer_size)

            # Decode the data
            message = data.decode()

            print(f"Node {self._cfg.id} received message: {message}")

            return message
        except socket.timeout:
            print(
                f"Node {self._cfg.id} did not receive a message within the timeout period."
            )
            return None

    @property
    def cfg(self) -> node.NodeInfo:
        """
        Get the node configuration.

        Returns:
            node.NodeInfo: The node configuration.
        """
        return self._cfg

    @property
    def neighbors(self) -> dict[int, socket.socket]:
        """
        Get the node neighbors.

        Returns:
            dict[int, socket.socket]: The node neighbors.
        """
        return self._neighbors
