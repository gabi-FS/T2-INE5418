import json
import argparse
import lib.controller as controller
import lib.node as node
import time

parser = argparse.ArgumentParser(description="Launch a node")
parser.add_argument("name", type=str, help="The node name")

args = parser.parse_args()
name = args.name

JSON_NAME = "port_map.json"


def read_file(file_name):
    with open(file_name, "r") as file:
        return json.loads(file.read())


data = read_file(JSON_NAME)
this_node_data = data[name]
server_data = this_node_data["server"]
client_data = this_node_data["client"]
this_node = controller.Controller(
    node.NodeInfo(server_data["host"], server_data["port"]),
    node.NodeInfo(client_data["host"], client_data["port"]),
)

neighbours = {}
for n in this_node_data["neighbours"]:
    neighbours[int(n["id"])] = node.NodeInfo(n["host"], n["port"])

print(neighbours)

this_node.start(neighbours, this_node_data["id"])

print(data)
print(data[name])

time.sleep(30)
this_node.leader_election()
