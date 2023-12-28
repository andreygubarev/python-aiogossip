import dataclasses
import math

import typeguard

from .concurrency import mutex
from .endpoint import Endpoint
from .message import Message, update_recv_endpoints, update_send_endpoints
from .node import Node
from .topology import Topology
from .transport import Transport


class Gossip:
    @typeguard.typechecked
    def __init__(self, node: Node, transport: Transport, fanout: int = 5):
        """
        Initialize a Gossip instance.

        Args:
            node (Node): The local node.
            transport (Transport): The transport layer for communication.
            fanout (int, optional): The number of nodes to gossip with. Defaults to 5.
        """
        self.node = node
        self.transport = transport
        self._fanout = fanout

        self.topology = Topology()
        self.topology.add_node(node)

    async def close(self) -> None:
        """
        Close the Gossip instance by closing the transport layer.
        """
        self.transport.close()

    @property
    def fanout(self) -> int:
        """
        Returns the minimum value between the fanout and the length of the topology.

        Returns:
            int: The minimum value between the fanout and the length of the topology.
        """
        return min(self._fanout, len(self.topology))

    @property
    def cycles(self) -> int:
        """
        Calculate the number of cycles required for gossip dissemination.

        Returns:
            int: The number of cycles required.
        """
        if self.fanout == 0:
            return 0

        if self.fanout == 1:
            return 1

        return math.ceil(math.log(len(self.topology), self.fanout))

    @typeguard.typechecked
    async def send(self, message: Message, node: Node) -> Message:
        route = self.topology.get_shortest_route(self.node, node)

        # IMPORTANT: discovery
        message = update_send_endpoints(
            message,
            send=Endpoint(route.snode, src=route.saddr),
            recv=Endpoint(route.dnode, dst=route.daddr),
        )
        await self.transport.send(message, route.daddr)
        return message

    @typeguard.typechecked
    async def send_ack(self, message: Message, node: Node) -> Message:
        """
        Sends an ACK message to the specified node.

        Args:
            message (Message): The original message.
            node (Node): The destination node.

        Returns:
            Message: The ACK message sent.
        """
        if Message.Type.ACK in message.message_type:
            raise ValueError("Message type must not contain ACK")

        if Message.Type.SYN not in message.message_type:
            raise ValueError("Message type must contain SYN for ACK")

        message = dataclasses.replace(
            message,
            message_type={Message.Type.ACK},
            route_snode=message.route_dnode,
            route_dnode=message.route_snode,
        )
        return await self.send(message, node)

    @typeguard.typechecked
    async def send_handshake(self, node: Node) -> Message:
        """
        Sends HANDSHAKE/SYN message to the specified node.

        Args:
            node (Node): The destination node.

        Returns:
            Message: The SYN message sent.
        """
        message = Message(
            route_snode=self.node.node_id,
            route_dnode=node.node_id,
            message_type={Message.Type.HANDSHAKE, Message.Type.SYN},
        )
        return await self.send(message, node)

    @typeguard.typechecked
    async def send_gossip(self, message: Message) -> list[Message]:
        if Message.Type.GOSSIP not in message.message_type:  # pragma: no cover
            raise ValueError("Message type must contain GOSSIP")

        messages = set()
        gossip_ignore = set([self.node])
        gossip_ignore.update([ep.node for ep in message.route_endpoints])

        @mutex(self, message.message_id)
        async def multicast():
            cycle = 0
            while cycle < self.cycles:
                nodes = self.topology.get_random_successor_nodes(self.node, self.fanout, exclude_nodes=gossip_ignore)
                for node in nodes:
                    m = dataclasses.replace(message, route_dnode=node.node_id)
                    messages.add(await self.send(m, node))
                gossip_ignore.update([n for n in nodes])
                cycle += 1

        await multicast()
        return list(messages)

    @typeguard.typechecked
    async def recv(self) -> Message:
        while True:
            message, addr = await self.transport.recv()

            # IMPORTANT: discovery
            message = update_recv_endpoints(
                message,
                send=Endpoint(message.route_endpoints[-2].node, dst=addr),
                recv=Endpoint(message.route_endpoints[-1].node, src=self.transport.addr),
            )

            # IMPORTANT: handshake
            handshakes = {ep.node for ep in message.route_endpoints if ep.node not in self.topology}

            # IMPORTANT: discovery
            self.topology.update_routes(message.route_endpoints)

            # IMPORTANT: handshake
            for handshake in handshakes:
                await self.send_handshake(handshake)

            # IMPORTANT: forward
            if message.route_dnode != self.node.node_id:
                await self.send(message, self.topology.get_node(message.route_dnode))
                continue

            # IMPORTANT: syn/ack
            if Message.Type.ACK in message.message_type:
                yield message
                continue

            if Message.Type.SYN in message.message_type:
                await self.send_ack(message, self.topology.get_node(message.route_snode))

            # IMPORTANT: gossip
            if Message.Type.GOSSIP in message.message_type:
                await self.send_gossip(message)

            # IMPORTANT: handshake
            if Message.Type.HANDSHAKE in message.message_type:
                continue

            yield message
