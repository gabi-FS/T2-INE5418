import socket
import threading

# ideias iniciais, não sei se faz sentido


class NodeInfo:
    """
    Defines host and port for communication.
    """

    _host: str
    _port: int
    _id: int

    def __init__(self, host: str, port: int, id: int) -> None:
        self._host = host
        self._port = port
        self._id = id

    @property
    def host(self) -> str:
        """
        Get the host name.

        Returns:
        str: The host name.
        """
        return self._host

    @property
    def port(self) -> int:
        """
        Get the port number.

        Returns:
        int: The port number.
        """
        return self._port

    @property
    def id(self) -> int:
        """
        Get the id number.

        Returns:
        int: The id number.
        """
        return self._id


class Device:

    """
    Defines a device with a socket for communication.
    """

    _cfg: NodeInfo
    _socket: socket.socket  # tipo socket
    _neighbors: list[socket.socket]

    # neighbours: list of identifiers of other Nodes connected to this
    def __init__(self, cfg) -> None:
        self._cfg = cfg
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._neighbours = []

    def start_server(self):
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

    def connect_to_node(self, neighbor_host, neighbor_port):
        neighbor_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        neighbor_socket.connect((neighbor_host, neighbor_port))
        print(
            f"Node {self._cfg.id} connected to Node at {neighbor_host}:{neighbor_port}"
        )
        self._neighbors.append(neighbor_socket)

    def send_message(self, neighbor_socket, message):
        try:
            neighbor_socket.sendall(message.encode("utf-8"))
            print(f"Node {self._cfg.id} sent message: {message}")
        except Exception as e:
            print(f"Node {self._cfg.id} error: {e}")
