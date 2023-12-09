import collections
import random
import time

import networkx as nx

from .message_pb2 import Message, Route
from .transport.address import parse_addr

Node = collections.namedtuple("Node", ["node_id", "node_addr"])


class Topology:
    def __init__(self, node_id, node_addr):
        node_addr = parse_addr(node_addr)
        self.g = nx.DiGraph(node_id=node_id, node_addr=node_addr)
        self.create_node(node_id, node_addr=node_addr)

    def create_node(self, node_id, node_addr=None):
        self.g.add_node(node_id)

        node = self.g.nodes[node_id]
        if "node_id" not in node:
            node["node_id"] = node_id

        if "node_addrs" not in node:
            node["node_addrs"] = {
                "local": {},
                "lan": {},
                "wan": {},
            }

        if node_addr:
            self.create_node_addr(node_id, node_addr)

    def create_node_addr(self, node_id, node_addr):
        node = self.g.nodes[node_id]
        node_addr = parse_addr(node_addr)

        if node_addr.ip.is_loopback:
            node_addr_type = "local"
        elif node_addr.ip.is_private:
            node_addr_type = "lan"
        elif node_addr.ip.is_global:
            node_addr_type = "wan"
        else:
            raise ValueError(f"Unknown address type {node_addr}")

        node["node_addrs"][node_addr_type][node_addr] = True

    # Node #
    @property
    def node_id(self):
        return self.g.graph["node_id"]

    @property
    def node_addr(self):
        return self.g.graph["node_addr"]

    @property
    def node(self):
        return Node(self.node_id, self.node_addr)

    # Topology #
    def add(self, nodes):
        for node in nodes:
            if node.node_id == self.node_id:
                continue

            self.create_node(node.node_id, node_addr=node.node_addr)

            src = self.g.nodes[self.node_id]
            dst = self.g.nodes[node.node_id]
            self.g.add_edge(
                src["node_id"],
                dst["node_id"],
                saddr=parse_addr(src["node_addr"]),
                daddr=parse_addr(dst["node_addr"]),
            )

    def update(self, routes):
        if len(routes) < 2:
            raise ValueError("Empty route")

        nodes = set()
        for r in routes:
            if r.route_id not in self.g:
                self.create_node(r.route_id)
                nodes.add(r.route_id)
            self.create_node_addr(r.route_id, r.daddr)

        def edge(src, dst):
            return {
                "saddr": parse_addr(src.daddr),
                "daddr": parse_addr(dst.daddr),
                "latency": abs(src.timestamp - dst.timestamp),
            }

        hops = ((routes[r], routes[r + 1]) for r in range(len(routes) - 1))
        for src, dst in hops:
            self.g.add_edge(src.route_id, dst.route_id, **edge(src, dst))
        self.g.add_edge(dst.route_id, src.route_id, **edge(dst, src))

        return nodes

    def sample(self, k, ignore=None):
        nodes = [e[1] for e in self.g.out_edges(self.node_id)]
        if ignore:
            nodes = list(set(nodes) - set(ignore))
        k = min(k, len(nodes))
        return random.sample(nodes, k)

    def __len__(self):
        return len(self.g)

    def __iter__(self):
        return iter(self.g.nodes)

    def __contains__(self, node_id):
        return node_id in self.g

    def __getitem__(self, node_id):
        return self.g.nodes[node_id]

    def to_dict(self):
        nodes = {}
        for node_id in self.g.nodes:
            # addr = set()
            node_data = self.g.nodes[node_id]
            node_addr = list(node_data["node_addrs"])[0]
            addr = f"{node_addr.ip}:{node_addr.port}"
            nodes[node_id.decode()] = {
                "addresses": [addr],
                "reachable": self.g.nodes[node_id].get("reachable", False),
            }
        return nodes

    # Reachability #

    def mark_reachable(self, node_id):
        self.g.nodes[node_id]["reachable"] = True

    def mark_unreachable(self, node_id):
        self.g.nodes[node_id]["reachable"] = False

    # Addr #
    def get_next_peer(self, node_id):
        path = nx.shortest_path(self.g.to_undirected(), self.node_id, node_id)
        addr = self.g.edges[path[0], path[1]]["daddr"]
        return path[1], parse_addr(addr)


class Routing:
    def __init__(self, topology):
        self.topology = topology

    def set_send_route(self, message, peer_id, peer_addr):
        msg = Message()
        msg.CopyFrom(message)

        if not msg.routing.routes:
            msg.routing.routes.append(Route(route_id=self.topology.node_id))
            msg.routing.routes.append(Route(route_id=peer_id))
        elif msg.routing.routes[-1].route_id == self.topology.node_id:
            msg.routing.routes.append(Route(route_id=peer_id))

        msg.routing.routes[-1].daddr = f"{peer_addr[0]}:{peer_addr[1]}"
        msg.routing.routes[-2].saddr = f"{self.topology.node_addr.ip}:{self.topology.node_addr.port}"
        msg.routing.routes[-2].timestamp = int(time.time_ns())
        return msg

    def set_recv_route(self, message, peer_id, peer_addr):
        msg = Message()
        msg.CopyFrom(message)

        msg.routing.routes[-2].daddr = f"{peer_addr[0]}:{peer_addr[1]}"
        msg.routing.routes[-1].saddr = f"{self.topology.node_addr.ip}:{self.topology.node_addr.port}"
        msg.routing.routes[-1].timestamp = int(time.time_ns())
        return msg
