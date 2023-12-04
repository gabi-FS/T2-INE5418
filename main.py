"""
Simple application that uses the election protocol IEEE 1394.
"""

import argparse
from os.path import join
from application import Application


parser = argparse.ArgumentParser(description="Launch a node")
parser.add_argument("id", type=int, help="The node id")

args = parser.parse_args()
node_id = args.id

application = Application(node_id, join("config", "network.json"), 1.0)
application.start()
