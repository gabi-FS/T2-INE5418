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
            self._node.neighbors[parent_id],
        )
    
    def wait_for_parent_response(self, parent_id: int) -> bool:
        """
        Returns:
            bool: True if the request was accepted, False otherwise.
        """
        message = self._device.receive_message(parent_id)
        if message:
            message_type, id = message.split(" ")
            if MessageType.PARENT_ACK_RESPONSE.value == message_type:
                print(f"Node {self._device.id} received parent ack response from {id}")
                self._device.neighbors.pop(parent_id).close()
                return True
            return False # Recebeu outra mensagem. O que poderia ser?
        return False
        
    def send_leader_announcement(self, child_id: int, leader_id: int) -> None:
        """Sends leader annoucement.

        Args:
            child_id (int): The child who will receive the leader id.
            leader_id (int): The leader id.
        """
        self._device.send_message_to_server(
            child_id,
            f"{MessageType.LEADER_ANNOUNCEMENT.value} {str(leader_id)}",
            self._node.neighbors[child_id]
        )
        
    def broadcast_leader_announcement(self, leader_id: int):
        """Broadcast leader annoucement for the children.

        Args:
            leader_id (int): _description_
        """
        for child_id in self._node.children:
            self.send_leader_announcement(child_id, leader_id)
            
        # TODO: esperar ack?

    def leader_election(self) -> int:
        """
        Performs the leader election algorithm.
        """
                
        while not self._node.done:
            if self._node.is_leaf: 
                # if the node is a leaf, send a request to its only neighbor
                neighbor_id = self._node.possible_parents_ids[0]
                self.send_parenting_request(neighbor_id)
                parent_response = self.wait_for_parent_response(neighbor_id)
                if parent_response:
                    self._node.set_done(True)

            else:
                # TODO: Teria como fazer uma espera não ocupada do able_to_request_parent?
                if self._node.able_to_request_parent: 
                    possible_parents_ids = self._node.possible_parents_ids
                    if len(possible_parents_ids) == 0:
                        print(self._node.id, "is leader")
                        self._node.set_leader(self._node.id)
                        self.broadcast_leader_announcement(self._node.id)
                        self._node.set_done(True)
                        self._device.server_should_finish()                               
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
        
        # Terminou seu papel. Esperar tudo terminar
        while not self._device.did_server_ended():
            continue #TODO: Remover espera ocupada
        
        return self._node.leader_id
                

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
            while not self._device.did_server_ended():
                data = client_socket.recv(1024) # LÍDER TRAVADO AQUI, PROVAVELMENTE
                if not data: 
                    break
                msg = data.decode()
                message_type, id = msg.split(" ")
                print(f"Node {self._device.id} info: {message_type}")
                
                if MessageType.CHILD_PARENTING_REQUEST.value == message_type:
                    self.handle_parenting_request(client_socket, int(id))
                elif MessageType.LEADER_ANNOUNCEMENT.value == message_type:
                    # TODO: enviar ack
                    self._node.set_leader(int(id))
                    self.broadcast_leader_announcement(int(id))
                    self._device.server_should_finish() 
                    
                print(f"Node {self._device.id} received data: {msg}")    
        except Exception as e:
            print(f"Node {self._device.id} error: {e}")
        finally:
            client_socket.close()
            print(f"Node {self._device.id} connection closed.")
