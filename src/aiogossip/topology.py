import collections
import random
import time

import networkx as nx

from .transport.address import parse_addr
from .types_pb2 import Message, Route

Node = collections.namedtuple("Node", ["node_id", "node_addr"])
Node.__str__ = lambda self: f"{self.node_id.decode()}@{self.node_addr}"
Node.__repr__ = lambda self: f"<Node: {self}>"


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
                "local": None,
                "lan": None,
                "wan": None,
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

        node["node_addrs"][node_addr_type] = node_addr

    def create_node_edge(self, node):
        if node.node_id == self.node_id:
            return

        self.create_node(node.node_id, node_addr=node.node_addr)
        self.g.add_edge(
            self.node_id,
            node.node_id,
            saddr=self.node_addr,
            daddr=node.node_addr,
        )

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

    @property
    def _node(self):
        return self.g.nodes[self.node_id]

    def update(self, routes):
        if len(routes) < 2:
            raise ValueError("Empty route")

        nodes = set()
        for r in routes:
            if r.node_id not in self.g:
                self.create_node(r.node_id)
                nodes.add(r.node_id)
            self.create_node_addr(r.node_id, r.daddr)

        def edge(src, dst):
            return {
                "saddr": parse_addr(src.daddr),
                "daddr": parse_addr(dst.daddr),
                "latency": abs(src.timestamp - dst.timestamp),
            }

        hops = ((routes[r], routes[r + 1]) for r in range(len(routes) - 1))
        for src, dst in hops:
            self.g.add_edge(src.node_id, dst.node_id, **edge(src, dst))
        self.g.add_edge(dst.node_id, src.node_id, **edge(dst, src))

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
            node_addrs = self.g.nodes[node_id]["node_addrs"]
            node_addrs = {k: str(v) for k, v in node_addrs.items()}
            nodes[node_id.decode()] = node_addrs
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
            msg.routing.routes.append(Route(node_id=self.topology.node_id))
            msg.routing.routes.append(Route(node_id=peer_id))
        elif msg.routing.routes[-1].node_id == self.topology.node_id:
            msg.routing.routes.append(Route(node_id=peer_id))

        if peer_addr.ip.is_loopback:
            peer_addr_type = "local"
        elif peer_addr.ip.is_private:
            peer_addr_type = "lan"
        elif peer_addr.ip.is_global:
            peer_addr_type = "wan"

        node_saddrs = self.topology._node["node_addrs"]
        node_saddr = (
            node_saddrs.get(peer_addr_type)
            or node_saddrs.get("wan")
            or node_saddrs.get("lan")
            or node_saddrs.get("local")
        )
        if not node_saddr:
            raise ValueError(f"Unknown address type {peer_addr}")

        msg.routing.routes[-1].daddr = f"{peer_addr[0]}:{peer_addr[1]}"
        msg.routing.routes[-2].saddr = f"{node_saddr.ip}:{node_saddr.port}"
        msg.routing.routes[-2].timestamp = int(time.time_ns())
        return msg

    def set_recv_route(self, message, peer_id, peer_addr):
        msg = Message()
        msg.CopyFrom(message)

        msg.routing.routes[-2].daddr = f"{peer_addr[0]}:{peer_addr[1]}"
        msg.routing.routes[-1].saddr = f"{self.topology.node_addr.ip}:{self.topology.node_addr.port}"
        msg.routing.routes[-1].timestamp = int(time.time_ns())
        return msg
