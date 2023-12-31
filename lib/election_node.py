"""
Election algorithm definition
"""


from enum import Enum
from random import randint
from threading import Condition, Lock, Semaphore, Thread
from time import sleep

from lib.connection_manager import ConnectionManager


class MessageType(Enum):
    """
    Defines the message types.
    """

    CHILD_PARENTING_REQUEST = "be_my_parent"
    PARENT_ACK_RESPONSE = "you_are_my_child"
    PARENT_REJECT_MESSAGE = "you_are_not_my_child"
    LEADER_ANNOUNCEMENT = "leader_announcement"
    ERROR = "error"
    LEADER_ANNOUNCEMENT_ACK = "leader_announcement_ack"


class NodeAddress:

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

    def get_address(self) -> tuple[str, int]:
        """
        Returns the address of the node.
        """

        return (self._host, self._port)


class ElectionNode:

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
    _election_thread: Thread | None

    def __init__(
        self,
        id: int,
        server_node_address: NodeAddress,
        neighbors: dict[int, NodeAddress],
        timeout: float = 120.0,
    ) -> None:
        self._id = id
        self._neighbors = neighbors
        self._possible_parents_ids = list(neighbors.keys())
        self._children_ids = []
        self._done = False
        self._is_leaf = len(self._possible_parents_ids) == 1

        # Be careful, the neighbors are passed as a reference.
        self._connection_manager = ConnectionManager(
            self._id, server_node_address, neighbors, timeout
        )
        self._parent_response = None
        self._is_waiting_for = (False, None)
        self._leader_id = -1

        self._leader_mutex = Lock()
        self._leader_condition = Condition(self._leader_mutex)

        self._able_to_request_parent_sem = Semaphore(0)
        self._parent_response_sem = Semaphore(0)
        self._send_parent_response_sem = Semaphore(0)
        self._possible_parents_ids_mutex = Lock()
        self._is_waiting_for_mutex = Lock()

        self._election_thread = None

        print(f"Node {self._id} is leaf: {self._is_leaf}")

    # public lib methods

    def start_server(self) -> None:
        """
        Starts the node server and start the accept of other requests in another thread.
        """

        self._connection_manager.start_server(self.handle_message)
        self._election_thread = Thread(target=self.process_leader_election)
        self._election_thread.start()

    def wait_for_election(self) -> int:
        """
        Block the process until the leader election ends, returning it's result.
        """
        self._election_thread.join()
        return self._leader_id

    def start_the_election(self, block_until_result=True) -> int:
        """
        Starts the election process, broadcasting to other nodes.

        Args:
            block_until_result (bool): if True, will wait for the result of the election and return it. If false, returns -1, and the result can be obtained from the ElectionNode class in nondeterministic time.
        """
        self._connection_manager.start_leader_election(self.handle_message)

        if block_until_result:
            return self.wait_for_election()
        else:
            return -1

    # non public lib methods

    def process_leader_election(self):
        """
        Wait for the end of the process of waiting for leader election, and then starts it.
        """

        self._connection_manager.server_thread.join()
        self.leader_election()
        self._connection_manager.close_all_sockets()

    def leader_election(self) -> None:
        """
        Performs the leader election algorithm, setting the leader_id attribute and finish only when election ends.
        """
        print("Entrou na eleição")

        if self._is_leaf:
            self._able_to_request_parent_sem.release()

        while not self._done:
            self._able_to_request_parent_sem.acquire()

            while True:  # While em caso de root contention
                self._possible_parents_ids_mutex.acquire()
                if len(self._possible_parents_ids) == 0:
                    self._possible_parents_ids_mutex.release()
                    print(self._id, "is leader")
                    self._leader_id = self._id
                    # waiting to send response to children
                    self._send_parent_response_sem.acquire()
                    print(self._id, "broadcasting leader announcement")
                    self.broadcast_leader_announcement(self._id)
                    self._done = True
                    self._connection_manager.finish_server()
                    break

                self._possible_parents_ids_mutex.release()

                self.send_parenting_request(self._possible_parents_ids[0])
                with self._is_waiting_for_mutex:
                    self._is_waiting_for = (
                        True,
                        self._possible_parents_ids[0],
                    )

                print("enviou request, vai esperar resposta")
                self._parent_response_sem.acquire()

                if self._parent_response:
                    self._done = True
                    break

                # root contention? -> if the request was not accepted, try again after some time
                print("try again after some time")
                sleep_time = randint(1, 3000)
                sleep(float(30 / sleep_time))

        if self._id != self._leader_id:
            print(
                "### Nodo finalizado, entra em estado de espera por anuncio do líder."
            )
            with self._leader_mutex:
                self._leader_condition.wait()
        else:
            print("### Nodo finalizado, é o líder!")

    def handle_message(self, node_id: int, message: str, node_message: int) -> None:
        """
        Handles the connection and receives data from a neighbor node.
        """

        print(f"Mensagem recebida do nó {node_id}: {message}")

        try:
            match message:
                case MessageType.CHILD_PARENTING_REQUEST.value:
                    self.handle_parenting_request(node_id)
                    print(
                        "Sent parent ack to ",
                        node_id,
                        " possible parents: ",
                        self._possible_parents_ids,
                    )
                    self._possible_parents_ids_mutex.acquire()
                    if len(self._possible_parents_ids) == 0:
                        self._possible_parents_ids_mutex.release()
                        print("releasing leader sem", node_id)
                        self._send_parent_response_sem.release()
                    else:
                        self._possible_parents_ids_mutex.release()
                case MessageType.LEADER_ANNOUNCEMENT.value:
                    # TODO: enviar ack?
                    with self._leader_mutex:
                        self._leader_id = node_message
                        self.broadcast_leader_announcement(node_message)
                        self._leader_condition.notify()
                        self._connection_manager.finish_server()  # Vai fazer não receber mais mensagens.
                case MessageType.PARENT_ACK_RESPONSE.value:
                    self._parent_response = True
                    self._parent_response_sem.release()
                    print(
                        f"Node {self._id} received parent ack response from {node_id}"
                    )
                case MessageType.PARENT_REJECT_MESSAGE.value:
                    self._parent_response = False
                    self._parent_response_sem.release()
                case MessageType.ERROR.value:  # TODO: especificar msg de erro pra rejeição?
                    self._parent_response = False
                    self._parent_response_sem.release()
                case _:
                    print(f"Node {self._id} received unknown message from {node_id}")

        except Exception as exception:
            print(f"Node {self._id} error: {exception}")

    def handle_parenting_request(self, node_id: int) -> None:
        """
        Handles the parenting request received from a node.

        Args:
            client_socket (socket): The socket object representing the client connection.
            node_id (int): The ID of the node.
        """

        print(f"Parenting request from {node_id}")

        with self._is_waiting_for_mutex:
            # print("entrou no mutex", self._is_waiting_for)
            concurrency = self._is_waiting_for[0] and node_id == self._is_waiting_for[1]

        # print(concurrency)
        if (
            not concurrency
            and node_id in self._possible_parents_ids
        ):
            print("Accept parenting request from", node_id)

            self.add_child(node_id)
            self.remove_possible_parent(node_id)

            self._possible_parents_ids_mutex.acquire()
            if len(self._possible_parents_ids) <= 1:
                self._possible_parents_ids_mutex.release()
                self._able_to_request_parent_sem.release()
            else:
                self._possible_parents_ids_mutex.release()

            self._connection_manager.send_message(
                node_id, f"{MessageType.PARENT_ACK_RESPONSE.value} {str(self._id)}"
            )

        else:
            if concurrency:
                self._parent_response = False
                with self._is_waiting_for_mutex:
                    self._is_waiting_for = (False, None)

                self._parent_response_sem.release()

            print("Reject parent request from", node_id)

            self._connection_manager.send_message(
                node_id, f"{MessageType.ERROR.value} {str(self._id)}"
            )

    def broadcast_leader_announcement(self, leader_id: int) -> None:
        """Broadcast leader annoucement for the children.

        Args:
            leader_id (int): The id of the winner node.
        """

        for child_id in self._children_ids:
            self._connection_manager.send_message(
                child_id, f"{MessageType.LEADER_ANNOUNCEMENT.value} {str(leader_id)}"
            )

    def send_parenting_request(self, parent_id: int) -> None:
        """
        Sends a parenting request.
        """

        self._connection_manager.send_message(
            parent_id, f"{MessageType.CHILD_PARENTING_REQUEST.value} {str(self._id)}"
        )

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
