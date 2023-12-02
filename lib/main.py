import controller
import node

node1_server = node.NodeInfo("localhost", 5000)
node1 = controller.Controller(node1_server, node.NodeInfo("localhost", 5001))

node2_server = node.NodeInfo("localhost", 4000)
node2 = controller.Controller(node2_server, node.NodeInfo("localhost", 4001))

node3_server = node.NodeInfo("localhost", 3000)
node3 = controller.Controller(node3_server, node.NodeInfo("localhost", 3001))

node1.start({2: node2_server}, 1)
node2.start({1: node1_server, 3: node3_server}, 2)
node3.start({2: node2_server}, 3)

node1.leader_election()
node2.leader_election()
node3.leader_election()
