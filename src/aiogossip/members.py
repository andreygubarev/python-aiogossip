import asyncio
import logging
import sys

from . import config
from .concurrency import TaskManager
from .types_pb2 import Message

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler(sys.stdout))
if config.DEBUG:
    logger.setLevel(logging.DEBUG)  # pragma: no cover


class Members:
    SCHEDULER_INTERVAL = 5

    PING_INTERVAL = 15
    PING_TIMEOUT = 5

    def __init__(self, peer):
        self.peer = peer

        self.task_manager = TaskManager(loop=self.peer._loop)
        self.task_manager.create_task(self.scheduler())

        self.peer.response("keepalive:*")(self.pong)

    async def scheduler(self):
        while True:
            for node in self.peer.nodes:
                if node == self.peer.peer_id:
                    continue

                if node not in self.task_manager:
                    self.task_manager.create_task(self.ping(node), name=node)

            await asyncio.sleep(self.SCHEDULER_INTERVAL)

    async def ping(self, peer_id):
        while True:
            topic = "keepalive"
            message = Message()
            message.routing.snode = self.peer.peer_id
            message.routing.dnode = peer_id

            response = await self.peer.request(topic, message, peers=[peer_id], timeout=self.PING_TIMEOUT)
            responses = []
            async for r in response:
                responses.append(r)

            if len(responses):
                self.peer.gossip.topology.mark_reachable(peer_id)
                logger.debug(f"Node is reachable: {peer_id}")
            else:
                self.peer.gossip.topology.mark_unreachable(peer_id)
                logger.debug(f"Node is unreachable: {peer_id}")

            await asyncio.sleep(self.PING_INTERVAL)

    async def pong(self, message):
        return Message()

    async def close(self):
        await self.task_manager.close()

    def print_topology(self, *args, **kwargs):
        print("Topology:")
        print("---------")
        import json

        print(json.dumps(self.peer.gossip.topology.to_dict(), indent=4))
        print("---------")
