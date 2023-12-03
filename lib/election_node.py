"""
Election algorithm definition
"""


from asyncio import sleep
from enum import Enum
from random import randint

from lib.connection_manager import ConnectionManager


class MessageType(Enum):
    """
    Defines the message types.
    """

    CHILD_PARENTING_REQUEST = "be_my_parent"
    PARENT_ACK_RESPONSE = "you_are_my_child"
    LEADER_ANNOUNCEMENT = "leader_announcement"
    ERROR = "error"
    LEADER_ANNOUNCEMENT_ACK = "leader_announcement_ack"


class NodeAddress():

    """
    Defines a neighbor node.

    This contains only the information a node in the network.
    """

    _host: str
    _port: int

    def __init__(self, host: str, port: int) -> None:
        self._host = host
        self._port = port

    def __str__(self) -> str:
        return f"{self._host}:{self._port}"

    def address(self) -> tuple[str, int]:
        """
        Returns the address of the node.
        """

        return (self._host, self._port)


class ElectionNode():

    """
    Defines a node that participates in the election algorithm.
    """

    _id: int
    _neighbors: dict[int, NodeAddress]  # id: NeighborNode
    _possible_parents_ids: list[int]
    _children_ids: list[int]
    _done: bool
    _able_to_request_parent: bool
    _is_leaf: bool
    _leader_id: int
    _is_leaf: bool
    _connection_manager: ConnectionManager

    def __init__(self,
                 id: int,
                 client_node_address: NodeAddress,
                 server_node_address: NodeAddress,
                 neighbors: dict[int, NodeAddress],
                 timeout: float = 120.0) -> None:
        self._id = id
        self._client_node_address = client_node_address
        self._server_node_address = server_node_address
        self._neighbors = neighbors
        self._leader_id = -1
        self._possible_parents_ids = list(neighbors.keys())
        self._children_ids = []
        self._done = False
        self._able_to_request_parent = False
        self._is_leaf = len(self._possible_parents_ids) == 1

        # Be careful, the neighbors are passed as a reference.
        self._connection_manager = ConnectionManager(self._id,
                                                     server_node_address,
                                                     client_node_address,
                                                     neighbors,
                                                     timeout)

        print(f"Node {self._id} is leaf: {self._is_leaf}")

    def start(self) -> None:
        """
        Starts the node.
        """

        self._connection_manager.start(self.handle_message)

    def add_child(self, child_id: int) -> None:
        """
        Adds a child to the node.

        Args:
            child_id (int): The ID of the child.
        """

        self._children_ids.append(child_id)

    def remove_possible_parent(self, parent_id: int) -> None:
        """
        Removes a possible parent from the node.

        Args:
            parent_id (int): The ID of the parent.
        """

        self._possible_parents_ids.remove(parent_id)

    def handle_message(self, node_id: int, message: str) -> None:
        """
        Handles the client connection and receives data from the client.
        """

        try:
            if MessageType.CHILD_PARENTING_REQUEST.value == message:
                self.handle_parenting_request(node_id)
            elif MessageType.LEADER_ANNOUNCEMENT.value == message:
                # TODO: enviar ack
                self._leader_id = node_id
                self.broadcast_leader_announcement(node_id)
                self._connection_manager.finish_server()
        except Exception as exception:
            print(f"Node {self._id} error: {exception}")

    def handle_parenting_request(self, client_node_id: int) -> None:
        """
        Handles the request received from a client.

        Args:
            client_socket (socket): The socket object representing the client connection.
            client_id (int): The ID of the client.
        """

        if client_node_id in self._possible_parents_ids and not self._is_leaf:
            print("Accept parenting request from", client_node_id)

            self.add_child(client_node_id)
            self.remove_possible_parent(client_node_id)

            if len(self._possible_parents_ids) == 1:
                self._able_to_request_parent = True

            self._connection_manager.send_message_to_client(client_node_id,
                                                            f"{MessageType.PARENT_ACK_RESPONSE.value} {str(self._id)}")
        else:
            # TODO: E se eu recebi uma requisição de alguém que eu já tinha mandado?
            # Analisar sobre isso. "Sending request to..."

            print("Reject parent request from", client_node_id)

            self._connection_manager.send_message_to_client(client_node_id,
                                                            f"{MessageType.ERROR.value} {str(self._id)}",)

    def broadcast_leader_announcement(self, leader_id: int) -> None:
        """Broadcast leader annoucement for the children.

        Args:
            leader_id (int): _description_
        """

        for child_id in self._children_ids:
            self.send_leader_announcement(child_id, leader_id)
            # TODO: esperar ack?

    def send_leader_announcement(self, child_id: int, leader_id: int) -> None:
        """Sends leader annoucement.

        Args:
            child_id (int): The child who will receive the leader id.
            leader_id (int): The leader id.
        """

        self._connection_manager.send_message_to_server(child_id,
                                                        f"{MessageType.LEADER_ANNOUNCEMENT.value} {str(leader_id)}")

    def leader_election(self) -> int:
        """
        Performs the leader election algorithm.
        """

        while not self._done:
            if self._is_leaf:  # if the node is a leaf, send a request to its only neighbor
                neighbor_id = self._possible_parents_ids[0]

                self.send_parenting_request(neighbor_id)

                parent_response = self.wait_for_parent_response(neighbor_id)

                if parent_response:
                    self._done = True
            else:
                # TODO: Teria como fazer uma espera não ocupada do able_to_request_parent?

                if self._able_to_request_parent:
                    possible_parents_ids = self._possible_parents_ids

                    if len(possible_parents_ids) == 0:
                        print(self._id, "is leader")
                        self._leader_id = self._id
                        self.broadcast_leader_announcement(self._id)
                        self._done = True
                        self._connection_manager.finish_server()
                    else:
                        self.send_parenting_request(possible_parents_ids[0])
                        parent_response = self.wait_for_parent_response(possible_parents_ids[0])

                        if parent_response:
                            self._able_to_request_parent = False
                            self._done = True
                        else:  # root contention?
                            # if the request was not accepted, try again after some time
                            sleep_time = randint(1, 3000)
                            sleep(float(30 / sleep_time))
        self._connection_manager.server_thread.join()

        return self._leader_id

    def send_parenting_request(self, parent_id: int) -> None:
        """
        Sends a request.
        """

        self._connection_manager.send_message_to_server(parent_id,
                                                        f"{MessageType.CHILD_PARENTING_REQUEST.value} {str(self._id)}")

    def wait_for_parent_response(self, parent_id: int) -> bool:
        """
        Returns:
            bool: True if the request was accepted, False otherwise.
        """

        message = self._connection_manager.receive_message_from_server(parent_id)

        if message:
            message_type, node_id = message.split()

            if MessageType.PARENT_ACK_RESPONSE.value == message_type:
                print(f"Node {self._id} received parent ack response from {node_id}")

                self._connection_manager.close_connection_with_server(parent_id)
                return True
        return False  # Recebeu outra mensagem. O que poderia ser?
