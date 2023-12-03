import argparse
import json
import time

from lib.election_node import ElectionNode, NodeAddress

parser = argparse.ArgumentParser(description="Launch a node")
parser.add_argument("name", type=str, help="The node name")

args = parser.parse_args()
name = args.name

JSON_NAME = "port_map.json"


def read_file(file_name):
    with open(file_name, "r", encoding="utf-8") as file:
        return json.loads(file.read())


data = read_file(JSON_NAME)
this_node_data = data[name]
server_data = this_node_data["server"]

server_address = NodeAddress(server_data["host"], server_data["port"])
neighbors = {int(n["id"]): NodeAddress(n["host"], n["port"]) for n in this_node_data["neighbors"]}

this_node = ElectionNode(this_node_data["id"],
                         server_address,
                         neighbors)

print(neighbors)

this_node.start()

time.sleep(10)
leader_id = this_node.leader_election()

print("Finalizando o processo, id do líder é", leader_id)
