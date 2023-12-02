"""
Device module.
"""

import socket
import threading
import lib.node as node


class Device:

    """
    Defines a device with a socket for communication.
    """

    _server_cfg: node.NodeInfo
    _client_cfg: node.NodeInfo
    _socket: socket.socket  # tipo socket
    _neighbors: dict[int, socket.socket]
    _timeout: float

    # neighbours: list of identifiers of other Nodes connected to this
    def __init__(
        self,
        server_cfg: node.NodeInfo,
        client_cfg: node.NodeInfo,
        timeout: float,
    ) -> None:
        self._server_cfg = server_cfg
        self._client_cfg = client_cfg
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._neighbors = {}
        self._timeout = timeout
        self._id = 0

    def start_device(self, id: int, handler):
        """
        Initializes the node by starting the server.

        Returns:
            None
        """
        self._id = id
        server_thread = threading.Thread(target=self.start_server, args=(handler,))
        server_thread.start()

    def start_server(self, handler):
        """
        Starts the server and listens for incoming connections.
        """
        self._socket.bind((self._server_cfg.host, self._server_cfg.port))
        self._socket.listen(10)
        print(
            f"Node {self._id} listening on {self._server_cfg.host}:{self._server_cfg.port}"
        )

        while True:
            client_socket, client_address = self._socket.accept()
            print(f"Node {self._id} accepted connection from {client_address}")
            handler(client_socket)
            # Handle client in a separate thread
            # client_thread = threading.Thread(target=handler, args=(client_socket,))
            # client_thread.start()

    def connect_to_node(self, neighbor_info: node.NodeInfo, neighbor_id: int):
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
            f"Node {self._id} connected to Node {neighbor_id} at {neighbor_info.host}:{neighbor_info.port}"
        )
        self._neighbors[neighbor_id] = neighbor_socket

    def send_message_to_server(self, neighbor_id, message, neighbor_info):
        """
        Sends a message to a neighbor socket.

        Args:
            neighbor_id (int): The ID of the neighbor node.
            message (str): The message to be sent.

        Returns:
            None
        """
        if neighbor_id not in self._neighbors:
            self.connect_to_node(neighbor_info, neighbor_id)
        try:
            neighbor_socket = self._neighbors[neighbor_id]
            neighbor_socket.sendall(message.encode("utf-8"))
            print(f"Node {self._id} sent message to {neighbor_id}: {message}")
        except Exception as e:
            print(f"Node {self._id} error: {e}")

    def send_message_to_client(self, neighbor_socket, message):
        """
        Sends a message to a neighbor client socket.

        Args:
            neighbor_socket (socket): The socket object of the neighbor.
            message (str): The message to be sent.

        Returns:
            None
        """
        try:
            neighbor_socket.sendall(message.encode("utf-8"))
            print(f"Node {self._id} sent message: {message}")
        except Exception as e:
            print(f"Node {self._id} error: {e}")

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
            message = data.decode("utf-8")

            print(f"Node {self._id} received message: {message}")

            return message
        except socket.timeout:
            print(
                f"Node {self._id} did not receive a message within the timeout period."
            )
            return None

    @property
    def cfg(self) -> node.NodeInfo:
        """
        Get the node configuration.

        Returns:
            node.NodeInfo: The node configuration.
        """
        return self._server_cfg

    @property
    def neighbors(self) -> dict[int, socket.socket]:
        """
        Get the node neighbors.

        Returns:
            dict[int, socket.socket]: The node neighbors.
        """
        return self._neighbors

    @property
    def id(self) -> int:
        """
        Get the node id.

        Returns:
            int: The node id.
        """
        return self._id
