"""
Controller module.
"""

from enum import Enum
from random import randint
from time import sleep

from .device import Device
from .node import Node, NodeInfo


class MessageType(Enum):
    """
    Defines the message types.
    """

    PARENT_REQUEST = "be_my_parent"
    PARENT_RESPONSE = "you_are_my_child"
    LEADER_ANNOUNCEMENT = "leader_announcement"
    ERROR = "error"
    LEADER_ANNOUNCEMENT_ACK = "leader_announcement_ack"


class Controller:

    """
    Defines a node of a graph.
    """

    _node: Node
    _device: Device

    def __init__(
        self,
        server_cfg: NodeInfo,
        client_cfg: NodeInfo,
        timeout: float = 120.0,
    ):
        self._device = Device(server_cfg, client_cfg, timeout)

    def start(self, neighbors_info: dict[int, NodeInfo], id: int):
        """
        Initializes the node by starting the server.

        Returns:
            None
        """
        self._node = Node(id, neighbors_info)
        self._device.start_device(id, self.handle_client)

    def send_parent_request(self, parent_id: int) -> bool:
        """
        Sends a request.

        Returns:
            bool: True if the request was accepted, False otherwise.
        """
        self._device.send_message_to_server(
            parent_id,
            f"{MessageType.PARENT_REQUEST.value} {str(self._device.id)}",
            self._node.neighbours[parent_id],
        )
        message = self._device.receive_message(parent_id)
        if message:
            info, id = message.split(" ")
            if info == MessageType.PARENT_RESPONSE.value:
                print(f"Node {self._device.id} received parent response from {id}")
                self._device.neighbors.pop(parent_id).close()
                return True
            else:
                return False
        else:
            return False

    def leader_election(self) -> None:
        """
        Performs the leader election algorithm.
        """
        while not self._node.done:
            if self._node.is_leaf:
                # if the node is a leaf, send a request to its only neighbour
                neighbour_id = self._node.neighbours_ids[0]
                if self.send_parent_request(neighbour_id):
                    self._node.set_done(True)

            else:
                neighbours_ids = self._node.neighbours_ids
                if self._node.able_to_request_parent:
                    if len(neighbours_ids) == 1:
                        # if it is not a leaf, find a neighbour that is not a
                        # child and send parent request
                        if self.send_parent_request(neighbours_ids[0]):
                            self._node.set_able_to_request_parent(False)
                            self._node.set_done(True)
                            break
                        else:
                            # if the request was not accepted, try again after some time
                            sleep_time = randint(1, 3000)
                            sleep(float(30 / sleep_time))

                elif len(neighbours_ids) > 0:
                    # if all neighbours are children, this node is the leader
                    self._node.set_leader(self._node.id)
                    # send message to all children

    def handle_parent_request(self, client_socket, client_id) -> None:
        """
        Handles the request received from a client.

        Args:
            client_socket (socket.socket): The socket object representing the client connection.
            client_id (int): The ID of the client.
        """

        print(self._node.neighbours_ids)
        print(self._node.is_leaf)

        if client_id in self._node.neighbours_ids and not self._node.is_leaf:
            print("accept parent request from", client_id)
            # add client as child and remove it from neighbours
            self._node.add_child(client_id)
            self._node.remove_neighbour(client_id)

            if len(self._node.neighbours_ids) == 1:
                self._node.set_able_to_request_parent(True)
            self._device.send_message_to_client(
                client_socket,
                f"{MessageType.PARENT_RESPONSE.value} {str(self._device.id)}",
            )
        else:
            print("reject parent request from", client_id)
            self._device.send_message_to_client(
                client_socket,
                f"{MessageType.ERROR.value} {str(self._device.id)}",
            )

    def handle_client(self, client_socket) -> None:
        """
        Handles the client connection and receives data from the client.

        Args:
            client_socket (socket): The socket object representing the client connection.
        """
        try:
            while True:
                data = client_socket.recv(1024)
                if not data:
                    break
                msg = data.decode()
                info, id = msg.split(" ")
                print(f"Node {self._device.id} info: {info}")
                if info == MessageType.PARENT_REQUEST.value:
                    print("entrou")
                    self.handle_parent_request(client_socket, int(id))
                print(f"Node {self._device.id} received data: {msg}")
        except Exception as e:
            print(f"Node {self._device.id} error: {e}")
        finally:
            client_socket.close()
            print(f"Node {self._device.id} connection closed.")
