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

# configuração, ajustar
server_address = NodeAddress(server_data["host"], server_data["port"])
neighbors = {
    int(n["id"]): NodeAddress(n["host"], n["port"]) for n in this_node_data["neighbors"]
}

this_node = ElectionNode(this_node_data["id"], server_address, neighbors)


this_node.start_server()  # Requisitos

option = input(
    "1 para bloquear processo e aguardar eleição, 2 para iniciar a eleição: "
)
# Duas opções, e só um iniciaria... e em outro caso? poderia ser não bloqueante, mas acessar o resultado de algum objeto?
# Poderia acessar do this_node em algum momento, mas aí como saberia o fim da eleição? Ah, o que não espera não processa. Acho melhor processar nos fundos...
# Tipo uma thread de processar a eleição. Aí o wait esperaria por ela só. E ela só roda quando a do server sair
if option == "1":
    leader_id = this_node.wait_for_election()  # Bloqueante
elif option == "2":
    leader_id = this_node.start_the_election()  # Bloqueante tb

print("Finalizando o processo, id do líder é", leader_id)
