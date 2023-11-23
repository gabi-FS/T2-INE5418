"""
Node module.
"""

import device
import threading
from enum import Enum


class MessageType(Enum):
    """
    Defines the message types.
    """

    PARENT_REQUEST = "parent_request"
    PARENT_RESPONSE = "parent_response"
    LEADER_ANNOUNCEMENT = "leader_announcement"
    LEADER_ANNOUNCEMENT_ACK = "leader_announcement_ack"


class Node:

    """
    Defines a node of a graph.
    """

    _id: int
    _neighbours: list[device.NodeInfo]
    _done: bool
    _is_leaf: bool
    _leader_id: int
    _device: device.Device
    _able_to_request_parent: bool

    # neighbours: list of identifiers of other Nodes connected to this
    def __init__(self, cfg: device.NodeInfo) -> None:
        self._id = cfg.id
        self._neighbours = []
        self._done = False
        self._is_leaf = False
        self._leader_id = -1
        self._device = device.Device(cfg)

    def is_leader(self):
        """
        Check if the current node is the leader.

        Returns:
            bool: True if the current node is the leader, False otherwise.
        """
        return self._leader_id == self._id

    def get_leader_id(self):
        """
        Get the leader id.

        Returns:
            int: The leader id.
        """
        return self._leader_id

    def init_node(self, neighbors_info: list[device.NodeInfo]):
        """
        Initializes the node by starting the server and connecting to neighbors.

        Returns:
            None
        """
        server_thread = threading.Thread(target=self._device.start_server)
        server_thread.start()

        for neighbor in neighbors_info:
            self._device.connect_to_node(neighbor)

        self._is_leaf = len(neighbors_info) == 1

    def leader_election(self):
        """
        Performs the leader election algorithm.

        Returns:
            None
        """
        if self._is_leaf:
            self.send_parent_request(self._neighbours[0].id)
        else:
            if self._able_to_request_parent:
                self.send_parent_request(self._neighbours[0].id)

    def send_parent_request(self, parent_id: int):
        """
        Sends a request.

        Returns:
            None
        """
        self._device.send_message(parent_id, MessageType.PARENT_REQUEST)
