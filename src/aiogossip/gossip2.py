import math
import random
import uuid

from .mutex import mutex


class Gossip:
    FANOUT = 5

    def __init__(self, transport, peers, fanout=FANOUT):
        self.transport = transport
        self.peers = peers
        self._fanout = fanout

    @property
    def fanout(self):
        return min(self._fanout, len(self.peers))

    @property
    def fanout_cycles(self):
        if self.fanout == 0:
            return 0

        if self.fanout == 1:
            return 1

        return math.ceil(math.log(len(self.peers), self.fanout))

    async def send(self, message, peer):
        await self.transport.send(message, peer)

    async def gossip(self, message):
        if "gossip" in message["metadata"]:
            gossip_id = message["metadata"]["gossip"]
        else:
            gossip_id = message["metadata"]["gossip"] = uuid.uuid4().hex

        @mutex(gossip_id)
        async def multicast():
            if self.fanout == 0:
                return

            cycle = 0
            while cycle < self.fanout_cycles:
                fanout_peers = random.sample(self.peers, self.fanout)
                for fanout_peer in fanout_peers:
                    await self.send(message, fanout_peer)
                cycle += 1

        await multicast()

    async def recv(self):
        while True:
            message, peer = await self.transport.recv()
            message["metadata"]["sender"] = peer

            if "gossip" in message["metadata"]:
                await self.gossip(message)

            yield message
