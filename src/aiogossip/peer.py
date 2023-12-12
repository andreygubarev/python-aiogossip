import asyncio
import signal
import uuid

from . import config
from .broker import Broker
from .concurrency import TaskManager
from .debug import debug
from .gossip import Gossip
from .members import Members
from .topology import Node
from .transport import Transport
from .transport.address import parse_addr
from .types_pb2 import Message


class Peer:
    def __init__(
        self,
        host="0.0.0.0",
        port=0,
        fanout=None,
        peer_id=None,
        loop: asyncio.AbstractEventLoop = None,
    ):
        self._loop = loop or asyncio.get_event_loop()

        if peer_id:
            self.peer_id = peer_id.encode()
        else:
            self.peer_id = uuid.uuid1().bytes

        self.transport = Transport((host, port), loop=self._loop)
        self.gossip = Gossip(self.transport, fanout=fanout, peer_id=self.peer_id)
        self.broker = Broker(self.gossip, loop=self._loop)

        self.task_manager = TaskManager(loop=self._loop)
        self.task_manager.create_task(self.broker.listen())

        self.members = Members(self)
        self._loop.add_signal_handler(signal.SIGHUP, self.members.print_topology)

    @property
    def node(self):
        return self.gossip.topology.node

    @property
    def nodes(self):
        return list(self.gossip.topology)

    @property
    def DSN(self):
        return "{}@{}:{}".format(self.node.node_id.decode(), *self.node.node_addr)

    async def _connect(self):
        await self.gossip.send_gossip_handshake()

    def connect(self, seeds=config.SEEDS):
        if not seeds:
            return

        nodes = []

        if isinstance(seeds, str):
            seeds = seeds.split(",")
            for seed in seeds:
                peer_id, addr = seed.split("@")
                addr = parse_addr(addr)
                nodes.append(Node(node_id=peer_id.encode(), node_addr=addr))
        elif isinstance(seeds, list):
            nodes = seeds

        for node in nodes:
            self.gossip.topology.create_node_edge(node)

        self.task_manager.create_task(self._connect())

    async def disconnect(self):
        await self.members.close()
        await self.broker.close()
        await self.task_manager.close()

    async def publish(self, topic, message, peers=None, syn=False):
        if not message.id:
            message.id = uuid.uuid4().bytes
        topic = topic.replace("{uuid}", uuid.uuid4().hex)

        if syn and (Message.Kind.SYN not in message.kind):
            message.kind.append(Message.Kind.SYN)
        return await self.broker.publish(topic, message, peer_ids=peers)

    def subscribe(self, topic):
        def decorator(func):
            return self.broker.subscribe(topic, func)

        return decorator

    async def request(self, topic, message, peers=None, timeout=5):
        if not message.id:
            message.id = uuid.uuid4().bytes
        message.kind.append(Message.Kind.REQ)

        topic = "request:{}:{}".format(topic, uuid.uuid4().hex)
        response = await self.publish(topic, message, peers=peers, syn=True)
        return response

    def response(self, topic):
        topic = "request:{}:*".format(topic)

        async def responder(message, result):
            result.id = message.id
            result.routing.snode = message.routing.dnode
            result.routing.dnode = message.routing.snode
            result.kind.append(Message.Kind.RES)
            await self.publish(message.topic, result, peers=[message.routing.snode], syn=False)

        def decorator(func):
            handler = self.broker.subscribe(topic, func)
            handler.hook(responder)
            return handler

        return decorator

    @debug
    def run_forever(self, main=None):  # pragma: no cover
        try:
            if main:
                main = self._loop.create_task(main())
            self._loop.run_forever()
        except KeyboardInterrupt:
            pass
        finally:
            if main:
                main.cancel()
                self._loop.run_until_complete(main)
            self._loop.run_until_complete(self.disconnect())
