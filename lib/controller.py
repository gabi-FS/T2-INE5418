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

    CHILD_PARENTING_REQUEST = "be_my_parent"
    PARENT_ACK_RESPONSE = "you_are_my_child"
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

    def start(self, neighbors_info: dict[int, NodeInfo], id: int) -> None:
        """
        Initializes the node by starting the server.
        """
        self._node = Node(id, neighbors_info)
        self._device.start_device(id, self.handle_client)

    def send_parenting_request(self, parent_id: int) -> None:
        """
        Sends a request.
        """
        self._device.send_message_to_server(
            parent_id,
            f"{MessageType.CHILD_PARENTING_REQUEST.value} {str(self._device.id)}",
            self._node.neighbours[parent_id],
        )
    
    def wait_for_parent_response(self, parent_id: int) -> bool:
        """
        Returns:
            bool: True if the request was accepted, False otherwise.
        """
        message = self._device.receive_message(parent_id)
        if message:
            content, id = message.split(" ")
            if MessageType.PARENT_ACK_RESPONSE.value == content:
                print(f"Node {self._device.id} received parent ack response from {id}")
                self._device.neighbors.pop(parent_id).close()
                return True
            return False # Recebeu outra mensagem. O que poderia ser?
        return False
        

    def leader_election(self) -> None:
        """
        Performs the leader election algorithm.
        """
                
        while not self._node.done:
            if self._node.is_leaf: 
                # if the node is a leaf, send a request to its only neighbour
                neighbour_id = self._node.possible_parents_ids[0]
                self.send_parenting_request(neighbour_id)
                parent_response = self.wait_for_parent_response(neighbour_id)
                if parent_response:
                    self._node.set_done(True)

            else:
                # TODO: Teria como fazer uma espera não ocupada do able_to_request_parent?
                if self._node.able_to_request_parent: 
                    possible_parents_ids = self._node.possible_parents_ids
                    if len(possible_parents_ids) == 0:
                        self._node.set_leader(self._node.id)
                        print(self._node.id, "is leader")
                        # TODO: send message to all children
                        self._node.set_done(True)
                               
                    else: 
                        self.send_parenting_request(possible_parents_ids[0])
                        parent_response = self.wait_for_parent_response(possible_parents_ids[0])
                        if parent_response:
                            self._node.set_able_to_request_parent(False)
                            self._node.set_done(True)
                        else: # root contention?
                            # if the request was not accepted, try again after some time
                            sleep_time = randint(1, 3000)
                            sleep(float(30 / sleep_time))

                

    def handle_parenting_request(self, client_socket, client_id) -> None:
        """
        Handles the request received from a client.

        Args:
            client_socket (socket): The socket object representing the client connection.
            client_id (int): The ID of the client.
        """
        
        if client_id in self._node.possible_parents_ids and not self._node.is_leaf:
            print("Accept parenting request from", client_id)
            self._node.add_child(client_id)
            self._node.remove_possible_parent(client_id)
            
            if len(self._node.possible_parents_ids) == 1:
                self._node.set_able_to_request_parent(True)
                
            self._device.send_message_to_client(
                client_socket,
                f"{MessageType.PARENT_ACK_RESPONSE.value} {str(self._device.id)}",
            )
        else:
            # E se eu recebi uma requisição de alguém que eu já tinha mandado? Analisar sobre isso. "Sending request to..."
            print("Reject parent request from", client_id)
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
                content, id = msg.split(" ")
                print(f"Node {self._device.id} info: {content}")
                if MessageType.CHILD_PARENTING_REQUEST.value == content:
                    self.handle_parenting_request(client_socket, int(id))
                print(f"Node {self._device.id} received data: {msg}")    
        except Exception as e:
            print(f"Node {self._device.id} error: {e}")
        finally:
            client_socket.close()
            print(f"Node {self._device.id} connection closed.")
