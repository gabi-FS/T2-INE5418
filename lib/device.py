"""
Device module.
"""

from socket import AF_INET, SOCK_STREAM, socket, timeout
from threading import Thread

from .node import NodeInfo


class Device:

    """
    Defines a device with a socket for communication.
    """

    _server_cfg: NodeInfo
    _client_cfg: NodeInfo
    _socket: socket 
    _neighbors: dict[int, socket] # list of identifiers of other Nodes connected to this
    _timeout: float
    _end_server: bool

    def __init__(
        self,
        server_cfg: NodeInfo,
        client_cfg: NodeInfo,
        timeout: float,
    ) -> None:
        self._server_cfg = server_cfg
        self._client_cfg = client_cfg
        self._socket = socket(AF_INET, SOCK_STREAM)
        self._neighbors = {}
        self._timeout = timeout
        self._id = 0
        self._end_server = False

    def start_device(self, id: int, handler) -> None:
        """
        Initializes the node by starting the server.
        """
        self._id = id
        server_thread = Thread(target=self.start_server, args=(handler,))
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

        while not self._end_server:
            client_socket, client_address = self._socket.accept()
            print(f"Node {self._id} accepted connection from {client_address}")
            handler(client_socket)
        
        print("Finalizando server.")
        self._socket.close()
            
    def connect_to_node(self, neighbor_info: NodeInfo, neighbor_id: int) -> None:
        """
        Connects the current node to a neighbor node.

        Args:
            neighbor_info (NodeInfo): Information about the neighbor node, including host and port.
        """
        neighbor_socket = socket(AF_INET, SOCK_STREAM)
        neighbor_socket.connect((neighbor_info.host, neighbor_info.port))
        print(
            f"Node {self._id} connected to Node {neighbor_id} at {neighbor_info.host}:{neighbor_info.port}"
        )
        self._neighbors[neighbor_id] = neighbor_socket

    def send_message_to_server(self, neighbor_id, message, neighbor_info) -> None:
        """
        Sends a message to a neighbor socket.

        Args:
            neighbor_id (int): The ID of the neighbor node.
            message (str): The message to be sent.
        """
        if neighbor_id not in self._neighbors:
            self.connect_to_node(neighbor_info, neighbor_id)
        try:
            neighbor_socket = self._neighbors[neighbor_id]
            neighbor_socket.sendall(message.encode("utf-8"))
            print(f"Node {self._id} sent message to {neighbor_id}: {message}")
        except Exception as e:
            print(f"Node {self._id} error: {e}")

    def send_message_to_client(self, neighbor_socket, message) -> None:
        """
        Sends a message to a neighbor client socket.

        Args:
            neighbor_socket (socket): The socket object of the neighbor.
            message (str): The message to be sent.
        """
        try:
            neighbor_socket.sendall(message.encode("utf-8"))
            print(f"Node {self._id} sent message: {message}")
        except Exception as e:
            print(f"Node {self._id} error: {e}")

    def receive_message(self, neighbor_id) -> str:
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
        except timeout:
            print(
                f"Node {self._id} did not receive a message within the timeout period."
            )
            return None

    @property
    def cfg(self) -> NodeInfo:
        """
        Get the node configuration.

        Returns:
            NodeInfo: The node configuration.
        """
        return self._server_cfg

    @property
    def neighbors(self) -> dict[int, socket]:
        """
        Get the node neighbors.

        Returns:
            dict[int, socket]: The node neighbors.
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
    
    def did_server_ended(self) -> bool:
        return self._end_server
    
    def server_should_finish(self) -> None:
        self._end_server = True
